"""IMP-082 verified backup, staged restore, and migration safety tests."""

from __future__ import annotations

import json

import aiosqlite
import pytest

from agent.studio import (
    BackupIdentityConflict,
    BackupIntegrityError,
    BackupRestoreBlocked,
    BackupRestoreService,
    BackupVerificationStatus,
    FOUNDATION_SCHEMA_VERSION,
    LogicalId,
    RestoreStageStatus,
)
from agent.studio.persistence import DEFAULT_MIGRATIONS, Migration, SQLiteWriteOwner, ensure_schema_compatibility
from tests.unit.test_studio_artifact_lifecycle import _fixture as _artifact_fixture
from tests.unit.test_studio_artifact_lifecycle import _ready
from tests.unit.test_studio_directing import NOW


async def _verified_artifact_backup(tmp_path, *, backup_id: str = "backup-imp082"):
    active = tmp_path / "active"
    writer, _, job, artifact_service = await _artifact_fixture(active)
    await _ready(artifact_service, job, data=b"imp082-canonical-artifact")
    service = BackupRestoreService(
        db_path=writer.db_path,
        artifact_root=active / "artifacts",
    )
    manifest = await service.create_backup(
        backup_root=tmp_path / "backups",
        backup_id=backup_id,
        project_id=job.project_id,
        project_revision="project-revision-17",
        application_version="flowkit-test-v1",
        created_at=NOW,
    )
    return writer, job, artifact_service, service, manifest


@pytest.mark.asyncio
async def test_verified_backup_binds_db_schema_and_ready_artifact_and_replays_idempotently(tmp_path):
    writer, job, _, service, manifest = await _verified_artifact_backup(tmp_path)
    try:
        assert manifest.verification_status is BackupVerificationStatus.VERIFIED
        assert manifest.schema_version == FOUNDATION_SCHEMA_VERSION
        assert [item.version for item in manifest.migration_history] == list(
            range(1, FOUNDATION_SCHEMA_VERSION + 1)
        )
        assert len(manifest.artifacts) == 1
        assert manifest.artifacts[0].generation_job_id == job.generation_job_id
        backup_dir = tmp_path / "backups" / manifest.backup_id
        assert await service.verify_backup(backup_dir) == manifest

        replay = await service.create_backup(
            backup_root=tmp_path / "backups",
            backup_id=manifest.backup_id,
            project_id=job.project_id,
            project_revision="project-revision-17",
            application_version="flowkit-test-v1",
            created_at=NOW,
        )
        assert replay == manifest
        assert not (tmp_path / "backups" / f".{manifest.backup_id}.partial").exists()

        with pytest.raises(BackupIdentityConflict, match="identity conflicts"):
            await service.create_backup(
                backup_root=tmp_path / "backups",
                backup_id=manifest.backup_id,
                project_id=job.project_id,
                project_revision="different-project-revision",
                application_version="flowkit-test-v1",
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_missing_required_artifact_never_publishes_successful_backup(tmp_path):
    active = tmp_path / "active"
    writer, _, job, artifact_service = await _artifact_fixture(active)
    try:
        _, paths, _, _ = await _ready(
            artifact_service,
            job,
            data=b"imp082-required-artifact",
        )
        artifact_service.absolute_path(paths.final_relative_path).unlink()
        service = BackupRestoreService(
            db_path=writer.db_path,
            artifact_root=active / "artifacts",
        )
        with pytest.raises(BackupIntegrityError, match="required artifact"):
            await service.create_backup(
                backup_root=tmp_path / "backups",
                backup_id="backup-missing-artifact",
                project_id=job.project_id,
                project_revision="rev-missing",
                application_version="flowkit-test-v1",
                created_at=NOW,
            )
        assert not (tmp_path / "backups" / "backup-missing-artifact").exists()
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_artifact_hash_tamper_invalidates_existing_backup(tmp_path):
    writer, _, _, service, manifest = await _verified_artifact_backup(
        tmp_path,
        backup_id="backup-tamper-artifact",
    )
    try:
        backup_dir = tmp_path / "backups" / manifest.backup_id
        artifact = backup_dir / "artifacts" / manifest.artifacts[0].relative_path
        artifact.write_bytes(b"tampered-backup-artifact")
        with pytest.raises(BackupIntegrityError, match="artifact hash mismatch"):
            await service.verify_backup(backup_dir)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_manifest_tamper_is_rejected_before_restore(tmp_path):
    writer, _, _, service, manifest = await _verified_artifact_backup(
        tmp_path,
        backup_id="backup-tamper-manifest",
    )
    try:
        backup_dir = tmp_path / "backups" / manifest.backup_id
        manifest_path = backup_dir / "backup-manifest.json"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["project_revision"] = "forged-revision"
        manifest_path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(BackupIntegrityError, match="manifest"):
            await service.stage_restore(
                backup_dir=backup_dir,
                staging_root=tmp_path / "restore",
                created_at=NOW,
            )
        assert not (tmp_path / "restore" / f"{manifest.backup_id}.staged").exists()
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_newer_schema_is_blocked_without_publishing_backup(tmp_path):
    db_path = tmp_path / "future.db"
    await ensure_schema_compatibility(db_path)
    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute(
            "INSERT INTO studio_schema_migration(version,name) VALUES (?,?)",
            (FOUNDATION_SCHEMA_VERSION + 1, "future-schema"),
        )
        await db.commit()

    service = BackupRestoreService(db_path=db_path, artifact_root=tmp_path / "artifacts")
    with pytest.raises(BackupRestoreBlocked, match="newer than supported"):
        await service.create_backup(
            backup_root=tmp_path / "backups",
            backup_id="backup-future-schema",
            project_id=LogicalId("project:future"),
            project_revision="future-revision",
            application_version="older-app",
            created_at=NOW,
        )
    assert not (tmp_path / "backups" / "backup-future-schema").exists()


@pytest.mark.asyncio
async def test_staged_restore_migrates_copy_only_and_leaves_active_older_schema_untouched(tmp_path):
    active_db = tmp_path / "active-v8.db"
    assert await ensure_schema_compatibility(
        active_db,
        supported_version=8,
        migrations=DEFAULT_MIGRATIONS[:8],
    ) == 8
    service = BackupRestoreService(db_path=active_db, artifact_root=tmp_path / "artifacts")
    manifest = await service.create_backup(
        backup_root=tmp_path / "backups",
        backup_id="backup-v8",
        project_id=LogicalId("project:restore"),
        project_revision="legacy-revision",
        application_version="app-v8",
        created_at=NOW,
    )
    assert manifest.schema_version == 8

    staged = await service.stage_restore(
        backup_dir=tmp_path / "backups" / manifest.backup_id,
        staging_root=tmp_path / "restore-staging",
        created_at=NOW,
    )
    assert staged.status is RestoreStageStatus.STAGED
    assert staged.staged_schema_version == FOUNDATION_SCHEMA_VERSION

    async with aiosqlite.connect(str(active_db)) as db:
        active_latest = (
            await (await db.execute("SELECT MAX(version) FROM studio_schema_migration")).fetchone()
        )[0]
    staged_db = tmp_path / "restore-staging" / "backup-v8.staged" / "database" / "studio.db"
    async with aiosqlite.connect(str(staged_db)) as db:
        staged_latest = (
            await (await db.execute("SELECT MAX(version) FROM studio_schema_migration")).fetchone()
        )[0]
    assert active_latest == 8
    assert staged_latest == FOUNDATION_SCHEMA_VERSION


@pytest.mark.asyncio
async def test_interrupted_migration_rolls_back_and_resume_is_deterministic(tmp_path):
    db_path = tmp_path / "migration.db"
    broken = (
        Migration(
            1,
            "base",
            statements=("CREATE TABLE base_row(id INTEGER PRIMARY KEY)",),
        ),
        Migration(
            2,
            "transform",
            statements=(
                "CREATE TABLE transformed(id INTEGER PRIMARY KEY)",
                "THIS IS NOT VALID SQL",
            ),
        ),
    )
    with pytest.raises(aiosqlite.OperationalError):
        await ensure_schema_compatibility(
            db_path,
            supported_version=2,
            migrations=broken,
        )

    async with aiosqlite.connect(str(db_path)) as db:
        rows = await (
            await db.execute("SELECT version,name FROM studio_schema_migration ORDER BY version")
        ).fetchall()
        transformed = await (
            await db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='transformed'"
            )
        ).fetchone()
    assert rows == [(1, "base")]
    assert transformed is None

    repaired = (
        broken[0],
        Migration(
            2,
            "transform",
            statements=(
                "CREATE TABLE transformed(id INTEGER PRIMARY KEY)",
                "INSERT INTO transformed(id) VALUES (1)",
            ),
        ),
    )
    assert await ensure_schema_compatibility(
        db_path,
        supported_version=2,
        migrations=repaired,
    ) == 2
    async with aiosqlite.connect(str(db_path)) as db:
        rows = await (
            await db.execute("SELECT version,name FROM studio_schema_migration ORDER BY version")
        ).fetchall()
        count = (await (await db.execute("SELECT COUNT(*) FROM transformed")).fetchone())[0]
    assert rows == [(1, "base"), (2, "transform")]
    assert count == 1


@pytest.mark.asyncio
async def test_retry_discards_stale_partial_backup_and_publishes_verified_result(tmp_path):
    active = tmp_path / "active"
    writer, _, job, artifact_service = await _artifact_fixture(active)
    try:
        await _ready(artifact_service, job, data=b"imp082-retry-artifact")
        backup_root = tmp_path / "backups"
        partial = backup_root / ".backup-retry.partial"
        partial.mkdir(parents=True)
        (partial / "garbage.txt").write_text("interrupted prior attempt", encoding="utf-8")
        service = BackupRestoreService(
            db_path=writer.db_path,
            artifact_root=active / "artifacts",
        )
        manifest = await service.create_backup(
            backup_root=backup_root,
            backup_id="backup-retry",
            project_id=job.project_id,
            project_revision="rev-retry",
            application_version="flowkit-test-v1",
            created_at=NOW,
        )
        assert manifest.verification_status is BackupVerificationStatus.VERIFIED
        assert (backup_root / "backup-retry" / "backup-manifest.json").is_file()
        assert not partial.exists()
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_backup_rejects_database_without_canonical_migration_history(tmp_path):
    db_path = tmp_path / "unversioned.db"
    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute("CREATE TABLE legacy_only(id INTEGER PRIMARY KEY)")
        await db.commit()
    service = BackupRestoreService(db_path=db_path, artifact_root=tmp_path / "artifacts")
    with pytest.raises(BackupRestoreBlocked, match="migration history is missing"):
        await service.create_backup(
            backup_root=tmp_path / "backups",
            backup_id="backup-unversioned",
            project_id=LogicalId("project:unversioned"),
            project_revision="legacy-revision",
            application_version="flowkit-test-v1",
            created_at=NOW,
        )
    assert not (tmp_path / "backups" / "backup-unversioned").exists()


@pytest.mark.asyncio
async def test_backup_id_is_windows_filesystem_safe(tmp_path):
    db_path = tmp_path / "studio.db"
    await ensure_schema_compatibility(db_path)
    service = BackupRestoreService(db_path=db_path, artifact_root=tmp_path / "artifacts")
    with pytest.raises(ValueError, match="unsafe characters"):
        await service.create_backup(
            backup_root=tmp_path / "backups",
            backup_id="backup:invalid-on-windows",
            project_id=LogicalId("project:safe-id"),
            project_revision="revision-1",
            application_version="flowkit-test-v1",
            created_at=NOW,
        )
