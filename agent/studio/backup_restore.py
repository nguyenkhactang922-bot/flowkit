"""IMP-082 verified backup, staged restore, and migration safety orchestration.

The persistence migration table remains schema authority and IMP-055 artifact
materialization evidence remains byte-lineage authority.  This module only
coordinates consistent backup publication and staged restore.  It never edits
an active project during restore and never reports a partial copy as success.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from .persistence import DEFAULT_MIGRATIONS, FOUNDATION_SCHEMA_VERSION, ensure_schema_compatibility
from .primitives import LogicalId


_MIGRATION_TABLE = "studio_schema_migration"
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_MANIFEST_NAME = "backup-manifest.json"
_RESTORE_MARKER = "restore-stage.json"
_DB_RELATIVE_PATH = "database/studio.db"


class BackupRestoreError(RuntimeError):
    """Base IMP-082 backup/restore error."""


class BackupRestoreBlocked(BackupRestoreError):
    """Raised when schema/identity/safety policy forbids the requested action."""


class BackupIntegrityError(BackupRestoreError):
    """Raised when DB/manifest/artifact bytes cannot be trusted."""


class BackupIdentityConflict(BackupRestoreError):
    """Raised when an existing backup/stage identity conflicts with the request."""


class BackupVerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"


class RestoreStageStatus(str, Enum):
    STAGED = "STAGED"


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _token(value: str, label: str) -> str:
    value = _trimmed(value, label)
    if not _TOKEN_RE.fullmatch(value):
        raise ValueError(f"{label} contains unsafe characters")
    return value


def _relative_path(value: str, label: str) -> str:
    value = _trimmed(value, label).replace("\\", "/")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) in {"", "."}:
        raise ValueError(f"{label} must be a safe relative path")
    return str(path)


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _canonical_hash(payload: dict[str, Any]) -> str:
    data = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return _sha256_bytes(data)


def _safe_join(root: Path, relative: str) -> Path:
    normalized = _relative_path(relative, "relative_path")
    resolved_root = root.resolve()
    candidate = (resolved_root / Path(normalized)).resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise BackupIntegrityError("manifest path escapes the authorized root")
    return candidate


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    data = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


class MigrationHistoryEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: int = Field(ge=1)
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _trimmed(value, "migration name")


class ArtifactBackupEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_id: LogicalId
    generation_job_id: LogicalId
    artifact_event_id: str
    relative_path: str
    content_sha256: str
    byte_count: int = Field(ge=0)
    media_type: str

    @field_validator("artifact_event_id", "media_type")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        return _relative_path(value, "relative_path")

    @field_validator("content_sha256")
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if not _HASH_RE.fullmatch(value):
            raise ValueError("content_sha256 must be sha256:<64 lowercase hex>")
        return value


class BackupManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    backup_id: str
    project_id: LogicalId
    project_revision: str
    schema_version: int = Field(ge=0)
    migration_history: tuple[MigrationHistoryEntry, ...] = ()
    created_at: AwareDatetime
    application_version: str
    db_snapshot_relative_path: str = _DB_RELATIVE_PATH
    db_snapshot_sha256: str
    db_snapshot_byte_count: int = Field(ge=0)
    artifacts: tuple[ArtifactBackupEntry, ...] = ()
    verification_status: BackupVerificationStatus = BackupVerificationStatus.VERIFIED
    manifest_sha256: str

    @field_validator("backup_id")
    @classmethod
    def validate_backup_id(cls, value: str) -> str:
        return _token(value, "backup_id")

    @field_validator("project_revision", "application_version")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("db_snapshot_relative_path")
    @classmethod
    def validate_db_path(cls, value: str) -> str:
        return _relative_path(value, "db_snapshot_relative_path")

    @field_validator("db_snapshot_sha256", "manifest_sha256")
    @classmethod
    def validate_hash(cls, value: str, info) -> str:
        if not _HASH_RE.fullmatch(value):
            raise ValueError(f"{info.field_name} must be sha256:<64 lowercase hex>")
        return value

    @model_validator(mode="after")
    def validate_manifest(self) -> "BackupManifest":
        versions = [item.version for item in self.migration_history]
        if versions != list(range(1, self.schema_version + 1)):
            raise ValueError("migration_history must be contiguous and end at schema_version")
        paths = [item.relative_path for item in self.artifacts]
        if len(paths) != len(set(paths)):
            raise ValueError("artifact manifest paths must be unique")
        if paths != sorted(paths):
            raise ValueError("artifact manifest entries must be path-sorted")
        if self.manifest_sha256 != _canonical_hash(self.unsigned_payload()):
            raise ValueError("manifest_sha256 does not match canonical manifest payload")
        return self

    def unsigned_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"manifest_sha256"})


class RestoreStageManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    backup_id: str
    source_manifest_sha256: str
    staged_schema_version: int = Field(ge=0)
    staged_db_sha256: str
    staged_db_byte_count: int = Field(ge=0)
    created_at: AwareDatetime
    status: RestoreStageStatus = RestoreStageStatus.STAGED
    manifest_sha256: str

    @field_validator("backup_id")
    @classmethod
    def validate_backup_id(cls, value: str) -> str:
        return _token(value, "backup_id")

    @field_validator("source_manifest_sha256", "staged_db_sha256", "manifest_sha256")
    @classmethod
    def validate_hash(cls, value: str, info) -> str:
        if not _HASH_RE.fullmatch(value):
            raise ValueError(f"{info.field_name} must be sha256:<64 lowercase hex>")
        return value

    @model_validator(mode="after")
    def validate_manifest(self) -> "RestoreStageManifest":
        if self.manifest_sha256 != _canonical_hash(self.unsigned_payload()):
            raise ValueError("restore stage manifest hash mismatch")
        return self

    def unsigned_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"manifest_sha256"})


class BackupRestoreService:
    """Verified backup and staged-restore coordinator.

    Restore deliberately has no active-project destination argument.  Promotion
    into an active project is a later, explicit lifecycle action outside IMP-082.
    """

    def __init__(
        self,
        *,
        db_path: str | Path,
        artifact_root: str | Path,
        supported_schema_version: int = FOUNDATION_SCHEMA_VERSION,
    ) -> None:
        self.db_path = Path(db_path)
        self.artifact_root = Path(artifact_root)
        self.supported_schema_version = supported_schema_version

    async def create_backup(
        self,
        *,
        backup_root: str | Path,
        backup_id: str,
        project_id: LogicalId,
        project_revision: str,
        application_version: str,
        created_at: datetime,
    ) -> BackupManifest:
        backup_id = _token(backup_id, "backup_id")
        _trimmed(project_revision, "project_revision")
        _trimmed(application_version, "application_version")
        if created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if not self.db_path.is_file():
            raise BackupRestoreBlocked("project database does not exist")

        source_schema, source_history = await asyncio.to_thread(
            self._inspect_schema_sync,
            self.db_path,
        )
        root = Path(backup_root)
        if root.exists() and (root.is_symlink() or not root.is_dir()):
            raise BackupIntegrityError("backup_root must be a safe directory")
        root.mkdir(parents=True, exist_ok=True)
        final_dir = root / backup_id
        partial_dir = root / f".{backup_id}.partial"

        if final_dir.exists():
            manifest = await self.verify_backup(final_dir)
            if (
                manifest.backup_id != backup_id
                or manifest.project_id != project_id
                or manifest.project_revision != project_revision
                or manifest.application_version != application_version
            ):
                raise BackupIdentityConflict("existing backup identity conflicts with request")
            return manifest
        if partial_dir.exists():
            if partial_dir.is_symlink() or not partial_dir.is_dir():
                raise BackupIntegrityError("partial backup path is not a safe directory")
            await asyncio.to_thread(shutil.rmtree, partial_dir)

        db_copy = partial_dir / _DB_RELATIVE_PATH
        artifacts_copy = partial_dir / "artifacts"
        db_copy.parent.mkdir(parents=True, exist_ok=True)
        artifacts_copy.mkdir(parents=True, exist_ok=True)

        await asyncio.to_thread(self._sqlite_backup_sync, self.db_path, db_copy)
        await asyncio.to_thread(self._assert_integrity_sync, db_copy)
        snapshot_schema, snapshot_history = await asyncio.to_thread(
            self._inspect_schema_sync,
            db_copy,
        )
        if snapshot_schema != source_schema or snapshot_history != source_history:
            raise BackupIntegrityError("schema history changed while creating DB snapshot")

        required = await asyncio.to_thread(self._required_artifacts_sync, db_copy)
        copied: list[ArtifactBackupEntry] = []
        for entry in required:
            source = _safe_join(self.artifact_root, entry.relative_path)
            if source.is_symlink() or not source.is_file():
                raise BackupIntegrityError(
                    f"required artifact is missing or unsafe: {entry.relative_path}"
                )
            if source.stat().st_size != entry.byte_count or _sha256_file(source) != entry.content_sha256:
                raise BackupIntegrityError(
                    f"required artifact no longer matches canonical evidence: {entry.relative_path}"
                )
            destination = _safe_join(artifacts_copy, entry.relative_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(shutil.copyfile, source, destination)
            if destination.stat().st_size != entry.byte_count or _sha256_file(destination) != entry.content_sha256:
                raise BackupIntegrityError(f"artifact backup verification failed: {entry.relative_path}")
            copied.append(entry)

        base: dict[str, Any] = {
            "backup_id": backup_id,
            "project_id": project_id,
            "project_revision": project_revision,
            "schema_version": snapshot_schema,
            "migration_history": snapshot_history,
            "created_at": created_at,
            "application_version": application_version,
            "db_snapshot_relative_path": _DB_RELATIVE_PATH,
            "db_snapshot_sha256": _sha256_file(db_copy),
            "db_snapshot_byte_count": db_copy.stat().st_size,
            "artifacts": tuple(sorted(copied, key=lambda item: item.relative_path)),
            "verification_status": BackupVerificationStatus.VERIFIED,
        }
        json_base = BackupManifest.model_construct(
            **base,
            manifest_sha256="sha256:" + "0" * 64,
        ).model_dump(mode="json", exclude={"manifest_sha256"})
        manifest = BackupManifest(**base, manifest_sha256=_canonical_hash(json_base))
        _atomic_write_json(partial_dir / _MANIFEST_NAME, manifest.model_dump(mode="json"))
        await self.verify_backup(partial_dir)
        partial_dir.rename(final_dir)
        return await self.verify_backup(final_dir)

    async def verify_backup(self, backup_dir: str | Path) -> BackupManifest:
        root = Path(backup_dir)
        if root.is_symlink() or not root.is_dir():
            raise BackupIntegrityError("backup directory is missing or unsafe")
        manifest_path = root / _MANIFEST_NAME
        if not manifest_path.is_file() or manifest_path.is_symlink():
            raise BackupIntegrityError("backup manifest is missing or unsafe")
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = BackupManifest.model_validate(raw)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise BackupIntegrityError("backup manifest is unreadable or invalid") from exc

        db_path = _safe_join(root, manifest.db_snapshot_relative_path)
        if db_path.is_symlink() or not db_path.is_file():
            raise BackupIntegrityError("backup DB snapshot is missing or unsafe")
        if db_path.stat().st_size != manifest.db_snapshot_byte_count:
            raise BackupIntegrityError("backup DB byte count does not match manifest")
        if _sha256_file(db_path) != manifest.db_snapshot_sha256:
            raise BackupIntegrityError("backup DB hash does not match manifest")
        await asyncio.to_thread(self._assert_integrity_sync, db_path)
        schema, history = await asyncio.to_thread(self._inspect_schema_sync, db_path)
        if schema != manifest.schema_version or history != manifest.migration_history:
            raise BackupIntegrityError("backup schema history does not match manifest")

        required = await asyncio.to_thread(self._required_artifacts_sync, db_path)
        if required != manifest.artifacts:
            raise BackupIntegrityError("backup artifact manifest does not match canonical DB evidence")
        artifacts_root = root / "artifacts"
        for entry in manifest.artifacts:
            path = _safe_join(artifacts_root, entry.relative_path)
            if path.is_symlink() or not path.is_file():
                raise BackupIntegrityError(f"backup artifact is missing or unsafe: {entry.relative_path}")
            if path.stat().st_size != entry.byte_count or _sha256_file(path) != entry.content_sha256:
                raise BackupIntegrityError(f"backup artifact hash mismatch: {entry.relative_path}")
        return manifest

    async def stage_restore(
        self,
        *,
        backup_dir: str | Path,
        staging_root: str | Path,
        created_at: datetime,
    ) -> RestoreStageManifest:
        if created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        source = Path(backup_dir)
        manifest = await self.verify_backup(source)
        root = Path(staging_root)
        if root.exists() and (root.is_symlink() or not root.is_dir()):
            raise BackupIntegrityError("staging_root must be a safe directory")
        root.mkdir(parents=True, exist_ok=True)
        final_dir = root / f"{manifest.backup_id}.staged"
        partial_dir = root / f".{manifest.backup_id}.restore-partial"

        if final_dir.exists():
            return await self._verify_staged_restore(final_dir, manifest)
        if partial_dir.exists():
            if partial_dir.is_symlink() or not partial_dir.is_dir():
                raise BackupIntegrityError("partial restore path is not a safe directory")
            await asyncio.to_thread(shutil.rmtree, partial_dir)

        staged_db = partial_dir / _DB_RELATIVE_PATH
        staged_artifacts = partial_dir / "artifacts"
        staged_db.parent.mkdir(parents=True, exist_ok=True)
        staged_artifacts.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(
            shutil.copyfile,
            _safe_join(source, manifest.db_snapshot_relative_path),
            staged_db,
        )
        for entry in manifest.artifacts:
            source_artifact = _safe_join(source / "artifacts", entry.relative_path)
            destination = _safe_join(staged_artifacts, entry.relative_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(shutil.copyfile, source_artifact, destination)

        await ensure_schema_compatibility(
            staged_db,
            supported_version=self.supported_schema_version,
        )
        await asyncio.to_thread(self._assert_integrity_sync, staged_db)
        staged_schema, _ = await asyncio.to_thread(self._inspect_schema_sync, staged_db)
        for entry in manifest.artifacts:
            path = _safe_join(staged_artifacts, entry.relative_path)
            if path.stat().st_size != entry.byte_count or _sha256_file(path) != entry.content_sha256:
                raise BackupIntegrityError(
                    f"staged restore artifact verification failed: {entry.relative_path}"
                )

        base: dict[str, Any] = {
            "backup_id": manifest.backup_id,
            "source_manifest_sha256": manifest.manifest_sha256,
            "staged_schema_version": staged_schema,
            "staged_db_sha256": _sha256_file(staged_db),
            "staged_db_byte_count": staged_db.stat().st_size,
            "created_at": created_at,
            "status": RestoreStageStatus.STAGED,
        }
        json_base = RestoreStageManifest.model_construct(
            **base,
            manifest_sha256="sha256:" + "0" * 64,
        ).model_dump(mode="json", exclude={"manifest_sha256"})
        stage_manifest = RestoreStageManifest(**base, manifest_sha256=_canonical_hash(json_base))
        _atomic_write_json(partial_dir / _RESTORE_MARKER, stage_manifest.model_dump(mode="json"))
        await self._verify_staged_restore(partial_dir, manifest)
        partial_dir.rename(final_dir)
        return await self._verify_staged_restore(final_dir, manifest)

    async def _verify_staged_restore(
        self,
        stage_dir: Path,
        source_manifest: BackupManifest,
    ) -> RestoreStageManifest:
        if stage_dir.is_symlink() or not stage_dir.is_dir():
            raise BackupIntegrityError("staged restore directory is missing or unsafe")
        marker = stage_dir / _RESTORE_MARKER
        if not marker.is_file() or marker.is_symlink():
            raise BackupIntegrityError("staged restore marker is missing or unsafe")
        try:
            value = RestoreStageManifest.model_validate_json(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise BackupIntegrityError("staged restore marker is invalid") from exc
        if (
            value.backup_id != source_manifest.backup_id
            or value.source_manifest_sha256 != source_manifest.manifest_sha256
        ):
            raise BackupIdentityConflict("existing staged restore belongs to different backup evidence")
        db_path = _safe_join(stage_dir, _DB_RELATIVE_PATH)
        if not db_path.is_file() or db_path.is_symlink():
            raise BackupIntegrityError("staged restore DB is missing or unsafe")
        if db_path.stat().st_size != value.staged_db_byte_count:
            raise BackupIntegrityError("staged restore DB size changed after verification")
        if _sha256_file(db_path) != value.staged_db_sha256:
            raise BackupIntegrityError("staged restore DB hash changed after verification")
        await asyncio.to_thread(self._assert_integrity_sync, db_path)
        schema, _ = await asyncio.to_thread(self._inspect_schema_sync, db_path)
        if schema != value.staged_schema_version or schema != self.supported_schema_version:
            raise BackupIntegrityError("staged restore schema is not current/verified")
        artifacts_root = stage_dir / "artifacts"
        for entry in source_manifest.artifacts:
            path = _safe_join(artifacts_root, entry.relative_path)
            if not path.is_file() or path.is_symlink():
                raise BackupIntegrityError(f"staged restore artifact missing: {entry.relative_path}")
            if path.stat().st_size != entry.byte_count or _sha256_file(path) != entry.content_sha256:
                raise BackupIntegrityError(f"staged restore artifact hash mismatch: {entry.relative_path}")
        return value

    def _inspect_schema_sync(
        self,
        db_path: Path,
    ) -> tuple[int, tuple[MigrationHistoryEntry, ...]]:
        connection = sqlite3.connect(str(db_path))
        try:
            connection.execute("PRAGMA query_only=ON")
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (_MIGRATION_TABLE,),
            ).fetchone()
            if exists is None:
                raise BackupRestoreBlocked("canonical schema migration history is missing")
            rows = connection.execute(
                f"SELECT version, name FROM {_MIGRATION_TABLE} ORDER BY version"
            ).fetchall()
        finally:
            connection.close()

        history = tuple(MigrationHistoryEntry(version=int(row[0]), name=str(row[1])) for row in rows)
        versions = [item.version for item in history]
        if versions != list(range(1, (max(versions) if versions else 0) + 1)):
            raise BackupRestoreBlocked("schema migration history is non-contiguous")
        latest = max(versions, default=0)
        if latest > self.supported_schema_version:
            raise BackupRestoreBlocked(
                f"database schema version {latest} is newer than supported version {self.supported_schema_version}"
            )
        known = {item.version: item.name for item in DEFAULT_MIGRATIONS}
        for item in history:
            if known.get(item.version) != item.name:
                raise BackupRestoreBlocked(
                    f"migration identity mismatch at version {item.version}: {item.name!r}"
                )
        return latest, history

    @staticmethod
    def _assert_integrity_sync(db_path: Path) -> None:
        connection = sqlite3.connect(str(db_path))
        try:
            rows = connection.execute("PRAGMA integrity_check").fetchall()
        finally:
            connection.close()
        if rows != [("ok",)]:
            raise BackupIntegrityError(f"SQLite integrity_check failed: {rows!r}")

    @staticmethod
    def _sqlite_backup_sync(source: Path, destination: Path) -> None:
        source_connection = sqlite3.connect(str(source))
        destination_connection = sqlite3.connect(str(destination))
        try:
            source_connection.execute("PRAGMA query_only=ON")
            source_connection.backup(destination_connection)
            destination_connection.commit()
        finally:
            destination_connection.close()
            source_connection.close()

    @staticmethod
    def _required_artifacts_sync(db_path: Path) -> tuple[ArtifactBackupEntry, ...]:
        connection = sqlite3.connect(str(db_path))
        try:
            tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            required_tables = {
                "studio_generation_artifact_event",
                "studio_generation_job",
            }
            if not required_tables.issubset(tables):
                return ()
            rows = connection.execute(
                """
                SELECT
                    e.artifact_id,
                    e.generation_job_id,
                    e.artifact_event_id,
                    e.final_relative_path,
                    e.content_sha256,
                    e.byte_count,
                    e.media_type,
                    e.attempt,
                    e.created_at
                FROM studio_generation_artifact_event AS e
                JOIN studio_generation_job AS j
                  ON j.generation_job_id=e.generation_job_id
                WHERE e.event_kind='MATERIALIZE_VALID'
                  AND j.artifact_state='READY'
                ORDER BY e.generation_job_id, e.attempt DESC, e.created_at DESC, e.artifact_event_id DESC
                """
            ).fetchall()
        finally:
            connection.close()

        latest_by_job: dict[str, ArtifactBackupEntry] = {}
        for row in rows:
            job_id = str(row[1])
            if job_id in latest_by_job:
                continue
            if row[3] is None or row[4] is None or row[5] is None or row[6] is None:
                raise BackupIntegrityError(
                    f"READY artifact evidence is incomplete for GenerationJob {job_id}"
                )
            latest_by_job[job_id] = ArtifactBackupEntry(
                artifact_id=LogicalId(str(row[0])),
                generation_job_id=LogicalId(job_id),
                artifact_event_id=str(row[2]),
                relative_path=str(row[3]),
                content_sha256=str(row[4]),
                byte_count=int(row[5]),
                media_type=str(row[6]),
            )
        return tuple(sorted(latest_by_job.values(), key=lambda item: item.relative_path))
