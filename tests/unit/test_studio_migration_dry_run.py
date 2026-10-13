"""IMP-101 real-SQLite migration dry-run and restart-safety tests."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from agent.db.schema import SCHEMA
from agent.studio.migration_dry_run import (
    MigrationDryRunIdentityConflict,
    MigrationDryRunRunner,
    MigrationDryRunSourceError,
)


_FIXTURE_SQL = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "legacy_migration_sample.sql"
)
_RAW_SENTINELS = (
    "IMP101_STORY_SENTINEL_NEVER_PERSIST",
    "IMP101_CHARACTER_PROMPT_SENTINEL_NEVER_PERSIST",
    "IMP101_SCENE_PROMPT_SENTINEL_NEVER_PERSIST",
    "IMP101_IMAGE_PROMPT_SENTINEL_NEVER_PERSIST",
    "IMP101_NARRATION_SENTINEL_NEVER_PERSIST",
    "IMP101_REQUEST_PROMPT_SENTINEL_NEVER_PERSIST",
)


def _create_legacy_db(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript(SCHEMA)
        connection.executescript(_FIXTURE_SQL.read_text(encoding="utf-8"))
        connection.commit()
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mapping_rows(path: Path) -> list[tuple[str, str, str, str]]:
    connection = sqlite3.connect(path)
    try:
        return connection.execute(
            """
            SELECT logical_id, version_id, payload_json, provenance_json
            FROM studio_semantic_version
            WHERE logical_id LIKE 'legacy-import-mapping:%'
            ORDER BY logical_id, version_id
            """
        ).fetchall()
    finally:
        connection.close()


@pytest.mark.asyncio
async def test_real_sqlite_dry_run_is_redacted_restart_safe_and_idempotent(tmp_path: Path):
    source = tmp_path / "legacy-source.db"
    output = tmp_path / "migration-output"
    _create_legacy_db(source)
    source_before = _sha256_file(source)

    runner = MigrationDryRunRunner()
    partial = await runner.run(source, output, max_records_per_invocation=2)

    assert partial.status == "RUNNING"
    assert partial.acceptance_pass is False
    assert partial.completed_records == 2
    assert partial.remaining_records == partial.total_records - 2
    assert (output / "manifest.json").is_file()
    assert (output / "report.json").is_file()
    assert (output / "canonical-staging.db").is_file()

    # Simulate a crash after the canonical mapping transaction committed but
    # before its manifest checkpoint was appended. Exact replay must be safe.
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lost_checkpoint = manifest["records"].pop()
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    assert lost_checkpoint["source_key_sha256"] not in {
        item["source_key_sha256"] for item in manifest["records"]
    }

    completed = await runner.run(source, output)

    assert completed.status == "COMPLETE"
    assert completed.acceptance_pass is True
    assert completed.remaining_records == 0
    assert completed.completed_records == completed.total_records
    assert completed.source_fingerprint.startswith("sha256:")
    assert completed.source_foreign_key_violations == 0
    assert completed.staging_db_sha256 == _sha256_file(output / "canonical-staging.db")
    assert completed.disposition_counts["SEED_ONLY"] == 1
    assert completed.disposition_counts["DELEGATE_EXISTING_ADAPTER"] == 1
    assert completed.disposition_counts["NOT_PROVABLE"] >= 2
    assert completed.disposition_counts["LINEAGE_ONLY"] >= 1
    assert "COMPATIBILITY_MAPPED" not in completed.disposition_counts
    assert completed.finding_counts["PROJECT_STORY_SEED_ONLY"] == 1
    assert completed.finding_counts["PROMPT_PROSE_DERIVATIVE_ONLY"] >= 1
    assert completed.finding_counts["EXPLICIT_TARGET_PROOF_REQUIRED"] >= 1
    assert completed.mapping_counts_by_table["project"] >= 1
    assert completed.mapping_counts_by_table["scene"] >= 1
    assert completed.mapping_counts_by_kind["PROJECT"] == 1
    assert completed.mapping_counts_by_kind["MEDIA"] >= 1
    assert {item.table for item in completed.context_only_tables} >= {
        "video",
        "project_character",
        "material",
    }

    # The report/manifest are privacy-safe: row text and prompts are only hashed.
    for artifact in (output / "manifest.json", output / "report.json"):
        content = artifact.read_text(encoding="utf-8")
        for sentinel in _RAW_SENTINELS:
            assert sentinel not in content

    mappings = _mapping_rows(output / "canonical-staging.db")
    assert len(mappings) == completed.completed_records
    for _, _, payload_json, provenance_json in mappings:
        for sentinel in _RAW_SENTINELS:
            assert sentinel not in payload_json
            assert sentinel not in provenance_json

    # IMP-080 remains the authority boundary: the dry run creates mapping
    # evidence only, never StoryCore/Shot/Scene semantic truth.
    connection = sqlite3.connect(output / "canonical-staging.db")
    try:
        logical_ids = {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT logical_id FROM studio_semantic_version"
            )
        }
        assert all(item.startswith("legacy-import-mapping:") for item in logical_ids)
        assert connection.execute(
            "SELECT COUNT(*) FROM studio_semantic_version WHERE logical_id LIKE 'story-core:%'"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM studio_semantic_version WHERE logical_id LIKE 'scene-dramatic-beat:%'"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM studio_semantic_version WHERE logical_id LIKE 'full-shot-spec:%'"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM studio_semantic_version WHERE logical_id LIKE 'shot-ir:%'"
        ).fetchone()[0] == 0
    finally:
        connection.close()

    # A completed replay verifies the durable manifest and returns the same
    # report; it does not create duplicate mapping versions.
    db_hash_before_replay = _sha256_file(output / "canonical-staging.db")
    replay = await runner.run(source, output)
    assert replay == completed
    assert _sha256_file(output / "canonical-staging.db") == db_hash_before_replay
    assert len(_mapping_rows(output / "canonical-staging.db")) == completed.completed_records
    assert _sha256_file(source) == source_before


@pytest.mark.asyncio
async def test_resume_rejects_changed_source_snapshot_without_mixing_runs(tmp_path: Path):
    source = tmp_path / "legacy-source.db"
    output = tmp_path / "migration-output"
    _create_legacy_db(source)

    runner = MigrationDryRunRunner()
    partial = await runner.run(source, output, max_records_per_invocation=1)
    assert partial.status == "RUNNING"
    before_count = len(_mapping_rows(output / "canonical-staging.db"))

    connection = sqlite3.connect(source)
    try:
        connection.execute(
            "UPDATE project SET story=? WHERE id=?",
            ("Changed source snapshot; must not mix runs", "legacy-project-101"),
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(MigrationDryRunIdentityConflict, match="source_fingerprint"):
        await runner.run(source, output)

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "RUNNING"
    assert len(manifest["records"]) == 1
    assert len(_mapping_rows(output / "canonical-staging.db")) == before_count


@pytest.mark.asyncio
async def test_non_flowkit_sqlite_source_fails_closed_before_creating_output(tmp_path: Path):
    source = tmp_path / "unrelated.db"
    connection = sqlite3.connect(source)
    try:
        connection.execute("CREATE TABLE unrelated (id TEXT PRIMARY KEY)")
        connection.commit()
    finally:
        connection.close()

    output = tmp_path / "migration-output"
    with pytest.raises(MigrationDryRunSourceError, match="missing required table"):
        await MigrationDryRunRunner().run(source, output)
    assert not output.exists()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tamper", "expected_message"),
    [
        ("missing_checkpoint", "completed manifest checkpoint set"),
        ("missing_and_recounted", "total_records"),
        ("duplicate_checkpoint", "duplicate source record checkpoints"),
    ],
)
async def test_completed_manifest_rejects_incomplete_or_duplicate_checkpoints(
    tmp_path: Path,
    tamper: str,
    expected_message: str,
):
    source = tmp_path / "legacy-source.db"
    output = tmp_path / "migration-output"
    _create_legacy_db(source)
    runner = MigrationDryRunRunner()
    completed = await runner.run(source, output)
    assert completed.status == "COMPLETE"

    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if tamper == "missing_checkpoint":
        manifest["records"].pop()
    elif tamper == "missing_and_recounted":
        manifest["records"].pop()
        manifest["total_records"] = len(manifest["records"])
    else:
        manifest["records"][-1] = dict(manifest["records"][0])
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    # Avoid a stale report mismatch masking the manifest validation under test.
    (output / "report.json").unlink()

    with pytest.raises(MigrationDryRunIdentityConflict, match=expected_message):
        await runner.run(source, output)


@pytest.mark.asyncio
async def test_completed_manifest_rejects_mapping_source_key_rebinding(tmp_path: Path):
    source = tmp_path / "legacy-source.db"
    output = tmp_path / "migration-output"
    _create_legacy_db(source)
    runner = MigrationDryRunRunner()
    completed = await runner.run(source, output)
    assert completed.status == "COMPLETE"

    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    first_key = manifest["records"][0]["source_key_sha256"]
    second_key = manifest["records"][1]["source_key_sha256"]
    manifest["records"][0]["source_key_sha256"] = second_key
    manifest["records"][1]["source_key_sha256"] = first_key
    manifest["records"].sort(key=lambda item: item["source_key_sha256"])
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "report.json").unlink()

    with pytest.raises(
        MigrationDryRunIdentityConflict,
        match="source identity does not match manifest checkpoint",
    ):
        await runner.run(source, output)


@pytest.mark.asyncio
async def test_completed_manifest_rejects_tampered_foreign_key_summary(tmp_path: Path):
    source = tmp_path / "legacy-source.db"
    output = tmp_path / "migration-output"
    _create_legacy_db(source)

    connection = sqlite3.connect(source)
    try:
        connection.execute("PRAGMA foreign_keys=OFF")
        video_id = connection.execute("SELECT id FROM video LIMIT 1").fetchone()[0]
        connection.execute(
            "UPDATE video SET project_id=? WHERE id=?",
            ("missing-project-for-integrity-test", video_id),
        )
        connection.commit()
    finally:
        connection.close()

    runner = MigrationDryRunRunner()
    completed = await runner.run(source, output)
    assert completed.status == "COMPLETE"
    assert completed.source_foreign_key_violations > 0
    assert completed.acceptance_pass is False

    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_foreign_key_violations"] = 0
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "report.json").unlink()

    with pytest.raises(
        MigrationDryRunIdentityConflict,
        match="source_foreign_key_violations",
    ):
        await runner.run(source, output)
