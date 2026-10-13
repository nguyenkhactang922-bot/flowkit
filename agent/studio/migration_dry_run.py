"""IMP-101 restart-safe, read-only-source migration dry run.

The runner persists only IMP-080 mapping evidence into a separate canonical
staging database. Legacy project/story/prompt/media data is read in memory,
hashed, classified, and never copied as canonical creative truth.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field

from .legacy_import import (
    LegacyImportAntiCorruptionService,
    LegacyImportDisposition,
    LegacyImportRequest,
    LegacySourceEvidence,
    LegacySourceKind,
)
from .persistence import FOUNDATION_SCHEMA_VERSION, SQLiteWriteOwner
from .primitives import LogicalId, VersionId, VersionRef


_RULE_VERSION = "legacy-import-v1"
_TARGET_SCHEMA_VERSION = f"studio-schema-v{FOUNDATION_SCHEMA_VERSION}"
_MAPPING_KIND_BY_TABLE: dict[str, LegacySourceKind] = {
    "project": LegacySourceKind.PROJECT,
    "character": LegacySourceKind.ENTITY,
    "scene": LegacySourceKind.OPERATIONAL_SCENE,
    "request": LegacySourceKind.REQUEST,
}
_REQUIRED_TABLES = frozenset({"project", "video", "scene"})
_MANIFEST_NAME = "manifest.json"
_REPORT_NAME = "report.json"
_STAGING_DB_NAME = "canonical-staging.db"


class MigrationDryRunError(RuntimeError):
    """Base error for the IMP-101 dry-run boundary."""


class MigrationDryRunSourceError(MigrationDryRunError):
    """Raised when a legacy SQLite source cannot be safely inspected."""


class MigrationDryRunIdentityConflict(MigrationDryRunError):
    """Raised when a resume target no longer matches its recorded identity."""


class MigrationDryRunSourceChanged(MigrationDryRunError):
    """Raised when the source changes during a migration dry run."""


class MigrationDryRunRecordSummary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_key_sha256: str
    source_kind: str
    source_table: str
    mapping_id: str
    version_id: str
    payload_sha256: str
    disposition: str
    finding_codes: tuple[str, ...] = ()
    has_story_text: bool = False
    has_prompt_prose: bool = False
    has_media_lineage: bool = False
    has_chain_lineage: bool = False


class MigrationDryRunContextTable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    table: str
    row_count: int = Field(ge=0)
    table_sha256: str
    reason: str


class MigrationDryRunReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: int = 1
    run_id: str
    status: str
    acceptance_pass: bool
    source_fingerprint: str
    source_schema_version: str
    target_schema_version: str
    rule_version: str
    created_at: str
    completed_at: str | None = None
    source_integrity_check: str
    source_foreign_key_violations: int = Field(ge=0)
    table_counts: dict[str, int]
    table_sha256: dict[str, str]
    context_only_tables: tuple[MigrationDryRunContextTable, ...]
    total_records: int = Field(ge=0)
    completed_records: int = Field(ge=0)
    remaining_records: int = Field(ge=0)
    disposition_counts: dict[str, int]
    finding_counts: dict[str, int]
    mapping_counts_by_kind: dict[str, int]
    mapping_counts_by_table: dict[str, int]
    records: tuple[MigrationDryRunRecordSummary, ...]
    staging_database: str = _STAGING_DB_NAME
    staging_db_sha256: str | None = None


@dataclass(frozen=True)
class _SourceRecord:
    source_kind: LegacySourceKind
    source_table: str
    source_id: str
    payload: dict[str, Any]
    source_key_sha256: str


@dataclass(frozen=True)
class _SourceSnapshot:
    source_fingerprint: str
    source_schema_version: str
    table_counts: dict[str, int]
    table_sha256: dict[str, str]
    context_only_tables: tuple[MigrationDryRunContextTable, ...]
    records: tuple[_SourceRecord, ...]
    foreign_key_violations: int
    integrity_check: str


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"$blob_sha256": _sha256(value), "length": len(value)}
    if isinstance(value, float) and not math.isfinite(value):
        return {"$float": repr(value)}
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _source_key_sha256(
    source_kind: LegacySourceKind,
    source_table: str,
    source_id: str,
) -> str:
    material = _canonical_json(
        {
            "source_kind": source_kind.value,
            "source_table": source_table,
            "source_id": source_id,
        }
    ).encode("utf-8")
    return "sha256:" + _sha256(material)


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return True


def _is_media_field(field_name: str) -> bool:
    lowered = field_name.lower()
    return (
        lowered == "media_id"
        or lowered.endswith("_media_id")
        or lowered.endswith("_url")
    )


def _context_reason(table: str) -> str:
    reasons = {
        "video": (
            "Legacy Video is an execution container; IMP-080 has no accepted "
            "canonical Film/Scene adapter for this row type."
        ),
        "project_character": (
            "Legacy project/entity association requires an explicit Entity "
            "adapter; the association is retained as context, not inferred truth."
        ),
        "material": (
            "Legacy material/style configuration has no accepted IMP-080 "
            "mapping target and is retained as context only."
        ),
    }
    return reasons.get(
        table,
        "No accepted IMP-080 source-kind adapter exists for this table; "
        "the row is fingerprinted and reported as context-only, not silently imported.",
    )


def _open_source_read_only(path: Path) -> sqlite3.Connection:
    try:
        resolved = path.expanduser().resolve(strict=True)
    except OSError as exc:
        raise MigrationDryRunSourceError("legacy source database does not exist") from exc
    if not resolved.is_file():
        raise MigrationDryRunSourceError("legacy source database path is not a file")
    uri = resolved.as_uri() + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        return connection
    except sqlite3.Error as exc:
        raise MigrationDryRunSourceError(
            f"cannot open legacy source database read-only: {type(exc).__name__}"
        ) from exc


def _scan_source(path: Path, *, collect_records: bool) -> _SourceSnapshot:
    connection = _open_source_read_only(path)
    try:
        integrity_rows = connection.execute("PRAGMA integrity_check").fetchall()
        if len(integrity_rows) != 1 or str(integrity_rows[0][0]).lower() != "ok":
            raise MigrationDryRunSourceError("legacy source failed SQLite integrity_check")
        foreign_key_violations = len(
            connection.execute("PRAGMA foreign_key_check").fetchall()
        )

        schema_rows = connection.execute(
            """
            SELECT type, name, tbl_name, COALESCE(sql, '')
            FROM sqlite_master
            WHERE type IN ('table', 'index', 'view', 'trigger')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY type, name
            """
        ).fetchall()
        schema_payload = [
            {
                "type": str(row[0]),
                "name": str(row[1]),
                "table": str(row[2]),
                "sql": str(row[3]),
            }
            for row in schema_rows
        ]
        schema_sha256 = _sha256(_canonical_json(schema_payload).encode("utf-8"))

        table_names = tuple(
            str(row[0])
            for row in connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        )
        missing = sorted(_REQUIRED_TABLES.difference(table_names))
        if missing:
            raise MigrationDryRunSourceError(
                "legacy source is missing required table(s): " + ", ".join(missing)
            )

        table_counts: dict[str, int] = {}
        table_hashes: dict[str, str] = {}
        records: list[_SourceRecord] = []

        for table in table_names:
            quoted_table = _quote_identifier(table)
            columns = connection.execute(
                f"PRAGMA table_info({quoted_table})"
            ).fetchall()
            primary_key_columns = [
                str(row[1])
                for row in sorted(columns, key=lambda item: int(item[5]))
                if int(row[5]) > 0
            ]
            order_by = (
                ", ".join(_quote_identifier(name) for name in primary_key_columns)
                if primary_key_columns
                else "rowid"
            )
            cursor = connection.execute(
                f"SELECT * FROM {quoted_table} ORDER BY {order_by}"
            )
            table_digest = hashlib.sha256()
            row_count = 0
            while True:
                batch = cursor.fetchmany(256)
                if not batch:
                    break
                for sqlite_row in batch:
                    row = _json_safe(dict(sqlite_row))
                    encoded = _canonical_json(row).encode("utf-8")
                    table_digest.update(len(encoded).to_bytes(8, "big"))
                    table_digest.update(encoded)
                    row_count += 1

                    kind = _MAPPING_KIND_BY_TABLE.get(table)
                    if collect_records and kind is not None:
                        if "id" not in row or not _is_present(row.get("id")):
                            raise MigrationDryRunSourceError(
                                f"mapped legacy table {table!r} has a row without a stable id"
                            )
                        source_id = str(row["id"])
                        records.append(
                            _SourceRecord(
                                source_kind=kind,
                                source_table=table,
                                source_id=source_id,
                                payload=row,
                                source_key_sha256=_source_key_sha256(
                                    kind, table, source_id
                                ),
                            )
                        )

                    if collect_records:
                        owner_id = str(row.get("id") or _sha256(encoded)[:24])
                        for field_name, field_value in sorted(row.items()):
                            if not _is_media_field(field_name) or not _is_present(field_value):
                                continue
                            media_source_id = f"{table}:{owner_id}:{field_name}"
                            media_payload = {
                                "owner_table": table,
                                "owner_id": owner_id,
                                field_name: field_value,
                            }
                            records.append(
                                _SourceRecord(
                                    source_kind=LegacySourceKind.MEDIA,
                                    source_table=table,
                                    source_id=media_source_id,
                                    payload=media_payload,
                                    source_key_sha256=_source_key_sha256(
                                        LegacySourceKind.MEDIA,
                                        table,
                                        media_source_id,
                                    ),
                                )
                            )
            table_counts[table] = row_count
            table_hashes[table] = table_digest.hexdigest()

        if len({record.source_key_sha256 for record in records}) != len(records):
            raise MigrationDryRunSourceError(
                "legacy source contains duplicate mapping identities"
            )

        fingerprint_payload = {
            "schema_sha256": schema_sha256,
            "tables": [
                {
                    "name": name,
                    "row_count": table_counts[name],
                    "table_sha256": table_hashes[name],
                }
                for name in sorted(table_counts)
            ],
            "foreign_key_violations": foreign_key_violations,
        }
        source_fingerprint = _sha256(
            _canonical_json(fingerprint_payload).encode("utf-8")
        )
        context_tables = tuple(
            MigrationDryRunContextTable(
                table=table,
                row_count=table_counts[table],
                table_sha256=table_hashes[table],
                reason=_context_reason(table),
            )
            for table in sorted(table_counts)
            if table not in _MAPPING_KIND_BY_TABLE
        )
        records.sort(key=lambda record: record.source_key_sha256)
        return _SourceSnapshot(
            source_fingerprint="sha256:" + source_fingerprint,
            source_schema_version="legacy-schema-" + schema_sha256[:16],
            table_counts=table_counts,
            table_sha256=table_hashes,
            context_only_tables=context_tables,
            records=tuple(records),
            foreign_key_violations=foreign_key_violations,
            integrity_check="ok",
        )
    except sqlite3.Error as exc:
        raise MigrationDryRunSourceError(
            f"cannot inspect legacy source database: {type(exc).__name__}"
        ) from exc
    finally:
        connection.rollback()
        connection.close()


def _make_run_id(source_fingerprint: str) -> str:
    material = _canonical_json(
        {
            "source_fingerprint": source_fingerprint,
            "target_schema_version": _TARGET_SCHEMA_VERSION,
            "rule_version": _RULE_VERSION,
        }
    ).encode("utf-8")
    return "imp101-" + _sha256(material)[:24]


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    encoded = json.dumps(
        payload,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    ) + "\n"
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MigrationDryRunIdentityConflict(
            "existing migration manifest is unreadable; refusing to overwrite it"
        ) from exc
    if not isinstance(value, dict) or value.get("format_version") != 1:
        raise MigrationDryRunIdentityConflict(
            "existing migration manifest has an unsupported format"
        )
    if not isinstance(value.get("records"), list):
        raise MigrationDryRunIdentityConflict(
            "existing migration manifest has no valid record checkpoint list"
        )
    return value


def _validate_manifest_identity(
    manifest: dict[str, Any],
    snapshot: _SourceSnapshot,
    run_id: str,
) -> None:
    expected = {
        "source_fingerprint": snapshot.source_fingerprint,
        "source_schema_version": snapshot.source_schema_version,
        "run_id": run_id,
        "target_schema_version": _TARGET_SCHEMA_VERSION,
        "rule_version": _RULE_VERSION,
        "source_integrity_check": snapshot.integrity_check,
        "source_foreign_key_violations": snapshot.foreign_key_violations,
        "table_counts": snapshot.table_counts,
        "table_sha256": snapshot.table_sha256,
        "context_only_tables": [
            item.model_dump(mode="json") for item in snapshot.context_only_tables
        ],
        "total_records": len(snapshot.records),
    }
    for key, expected_value in expected.items():
        if manifest.get(key) != expected_value:
            raise MigrationDryRunIdentityConflict(
                f"resume identity mismatch for {key}; refusing to mix source snapshots"
            )

    source_keys = {record.source_key_sha256 for record in snapshot.records}
    checkpoint_keys: set[str] = set()
    for summary in manifest["records"]:
        if not isinstance(summary, dict):
            raise MigrationDryRunIdentityConflict(
                "manifest contains a malformed record checkpoint"
            )
        key = summary.get("source_key_sha256")
        if not isinstance(key, str) or key not in source_keys:
            raise MigrationDryRunIdentityConflict(
                "manifest checkpoint refers to a record outside the current source snapshot"
            )
        if key in checkpoint_keys:
            raise MigrationDryRunIdentityConflict(
                "manifest contains duplicate source record checkpoints"
            )
        checkpoint_keys.add(key)

    if manifest.get("status") == "COMPLETE" and checkpoint_keys != source_keys:
        raise MigrationDryRunIdentityConflict(
            "completed manifest checkpoint set does not cover the current source snapshot"
        )


def _request_for_record(
    record: _SourceRecord,
    *,
    run_id: str,
    snapshot: _SourceSnapshot,
    recorded_at: datetime,
) -> LegacyImportRequest:
    source = LegacySourceEvidence.from_legacy(
        record.payload,
        source_kind=record.source_kind,
        source_table=record.source_table,
        source_id=record.source_id,
        source_schema_version=snapshot.source_schema_version,
    )
    version_material = _canonical_json(
        {
            "run_id": run_id,
            "source_key_sha256": record.source_key_sha256,
            "payload_sha256": source.payload_sha256,
            "rule_version": _RULE_VERSION,
        }
    ).encode("utf-8")
    version_id = VersionId("legacy-" + _sha256(version_material)[:24])
    evidence_refs = (
        "imp101:source:" + snapshot.source_fingerprint,
        "imp101:table:" + record.source_table + ":" + snapshot.table_sha256[record.source_table],
    )
    return LegacyImportRequest(
        migration_run_id=run_id,
        target_schema_version=_TARGET_SCHEMA_VERSION,
        record_version_id=version_id,
        source=source,
        canonical_project_id=None,
        explicit_target_refs=(),
        generation_job_id=None,
        generation_job_revision=None,
        actor_ref="studio:imp101-migration-dry-run",
        reason="dry-run classification only; no source mutation or creative inference",
        recorded_at=recorded_at,
        correlation_id="imp101:" + run_id,
        evidence_refs=evidence_refs,
        rule_version=_RULE_VERSION,
    )


def _summary_from_artifact(
    artifact: Any,
    source_key_sha256: str,
) -> MigrationDryRunRecordSummary:
    value = artifact.value
    actual_source_key_sha256 = _source_key_sha256(
        value.source.source_kind,
        value.source.source_table,
        value.source.source_id,
    )
    if actual_source_key_sha256 != source_key_sha256:
        raise MigrationDryRunIdentityConflict(
            "persisted mapping source identity does not match manifest checkpoint"
        )
    if value.target_refs or value.generation_job_id is not None:
        raise MigrationDryRunIdentityConflict(
            "dry-run classifier produced a canonical target without explicit proof"
        )
    return MigrationDryRunRecordSummary(
        source_key_sha256=source_key_sha256,
        source_kind=value.source.source_kind.value,
        source_table=value.source.source_table,
        mapping_id=value.mapping_id.root,
        version_id=value.version_id.root,
        payload_sha256=value.source.payload_sha256,
        disposition=value.disposition.value,
        finding_codes=tuple(finding.code.value for finding in value.findings),
        has_story_text=value.source.has_story_text,
        has_prompt_prose=value.source.has_prompt_prose,
        has_media_lineage=value.source.has_media_lineage,
        has_chain_lineage=value.source.has_chain_lineage,
    )


def _report_from_manifest(manifest: dict[str, Any]) -> MigrationDryRunReport:
    records = tuple(
        MigrationDryRunRecordSummary.model_validate(record)
        for record in manifest["records"]
    )
    disposition_counts = dict(sorted(Counter(record.disposition for record in records).items()))
    mapping_counts_by_kind = dict(sorted(Counter(record.source_kind for record in records).items()))
    mapping_counts_by_table = dict(sorted(Counter(record.source_table for record in records).items()))
    finding_counter: Counter[str] = Counter()
    for record in records:
        finding_counter.update(record.finding_codes)
    total_records = int(manifest["total_records"])
    completed_records = len(records)
    status = str(manifest["status"])
    acceptance_pass = (
        status == "COMPLETE"
        and manifest["source_integrity_check"] == "ok"
        and int(manifest["source_foreign_key_violations"]) == 0
        and completed_records == total_records
    )
    return MigrationDryRunReport(
        run_id=manifest["run_id"],
        status=status,
        acceptance_pass=acceptance_pass,
        source_fingerprint=manifest["source_fingerprint"],
        source_schema_version=manifest["source_schema_version"],
        target_schema_version=manifest["target_schema_version"],
        rule_version=manifest["rule_version"],
        created_at=manifest["created_at"],
        completed_at=manifest.get("completed_at"),
        source_integrity_check=manifest["source_integrity_check"],
        source_foreign_key_violations=int(manifest["source_foreign_key_violations"]),
        table_counts=manifest["table_counts"],
        table_sha256=manifest["table_sha256"],
        context_only_tables=tuple(
            MigrationDryRunContextTable.model_validate(item)
            for item in manifest["context_only_tables"]
        ),
        total_records=total_records,
        completed_records=completed_records,
        remaining_records=max(0, total_records - completed_records),
        disposition_counts=disposition_counts,
        finding_counts=dict(sorted(finding_counter.items())),
        mapping_counts_by_kind=mapping_counts_by_kind,
        mapping_counts_by_table=mapping_counts_by_table,
        records=records,
        staging_db_sha256=manifest.get("staging_db_sha256"),
    )


def _write_report(path: Path, report: MigrationDryRunReport) -> None:
    _atomic_write_json(path, report.model_dump(mode="json"))


def _validate_existing_report(path: Path, expected: MigrationDryRunReport) -> None:
    if not path.exists():
        _write_report(path, expected)
        return
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MigrationDryRunIdentityConflict(
            "existing migration report is unreadable; refusing to overwrite it"
        ) from exc
    if existing != expected.model_dump(mode="json"):
        raise MigrationDryRunIdentityConflict(
            "existing completed report differs from the durable manifest"
        )


def _checkpoint_staging_database(path: Path) -> None:
    connection = sqlite3.connect(str(path), timeout=10.0)
    try:
        mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower()
        if mode == "wal":
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
    finally:
        connection.close()


def _recorded_at_from_manifest(manifest: dict[str, Any]) -> datetime:
    value = str(manifest["created_at"])
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise MigrationDryRunIdentityConflict(
            "manifest created_at must be timezone-aware for deterministic replay"
        )
    return parsed


class MigrationDryRunRunner:
    """Read-only legacy source scanner with resumable canonical mapping evidence."""

    async def run(
        self,
        source_db_path: str | Path,
        output_dir: str | Path,
        *,
        max_records_per_invocation: int | None = None,
    ) -> MigrationDryRunReport:
        if max_records_per_invocation is not None and max_records_per_invocation < 1:
            raise ValueError("max_records_per_invocation must be >= 1")

        try:
            source_path = Path(source_db_path).expanduser().resolve(strict=True)
        except OSError as exc:
            raise MigrationDryRunSourceError(
                "legacy source database does not exist"
            ) from exc
        output_path = Path(output_dir).expanduser().resolve()
        if not source_path.is_file():
            raise MigrationDryRunSourceError("legacy source database path is not a file")
        try:
            if source_path.is_relative_to(output_path):
                raise MigrationDryRunSourceError(
                    "output directory must not contain the read-only source database"
                )
        except AttributeError:
            if str(source_path).lower().startswith(str(output_path).lower() + os.sep):
                raise MigrationDryRunSourceError(
                    "output directory must not contain the read-only source database"
                )

        staging_path = output_path / _STAGING_DB_NAME
        if staging_path.resolve() == source_path:
            raise MigrationDryRunSourceError(
                "source database and canonical staging database must be different files"
            )
        manifest_path = output_path / _MANIFEST_NAME
        report_path = output_path / _REPORT_NAME
        snapshot = _scan_source(source_path, collect_records=True)
        run_id = _make_run_id(snapshot.source_fingerprint)
        output_path.mkdir(parents=True, exist_ok=True)

        if manifest_path.exists():
            manifest = _load_manifest(manifest_path)
            _validate_manifest_identity(manifest, snapshot, run_id)
            if manifest.get("status") not in {"RUNNING", "COMPLETE"}:
                raise MigrationDryRunIdentityConflict(
                    "existing migration manifest is not resumable"
                )
            if not staging_path.exists():
                if manifest["records"] or manifest.get("status") == "COMPLETE":
                    raise MigrationDryRunIdentityConflict(
                        "staging database is missing while manifest claims persisted records"
                    )
        else:
            if staging_path.exists() or report_path.exists():
                raise MigrationDryRunIdentityConflict(
                    "staging database/report exists without a manifest; refusing to adopt it"
                )
            created_at = datetime.now(timezone.utc).isoformat()
            manifest = {
                "format_version": 1,
                "run_id": run_id,
                "status": "RUNNING",
                "source_fingerprint": snapshot.source_fingerprint,
                "source_schema_version": snapshot.source_schema_version,
                "target_schema_version": _TARGET_SCHEMA_VERSION,
                "rule_version": _RULE_VERSION,
                "created_at": created_at,
                "completed_at": None,
                "source_integrity_check": snapshot.integrity_check,
                "source_foreign_key_violations": snapshot.foreign_key_violations,
                "table_counts": snapshot.table_counts,
                "table_sha256": snapshot.table_sha256,
                "context_only_tables": [
                    item.model_dump(mode="json") for item in snapshot.context_only_tables
                ],
                "total_records": len(snapshot.records),
                "records": [],
                "staging_db_sha256": None,
            }
            _atomic_write_json(manifest_path, manifest)

        if manifest["status"] == "COMPLETE":
            if not staging_path.is_file():
                raise MigrationDryRunIdentityConflict(
                    "completed staging database is missing"
                )
            recorded_hash = manifest.get("staging_db_sha256")
            if not recorded_hash or _sha256_file(staging_path) != recorded_hash:
                raise MigrationDryRunIdentityConflict(
                    "completed staging database hash differs from its manifest"
                )
            verifier = LegacyImportAntiCorruptionService(SQLiteWriteOwner(staging_path))
            await self._verify_completed_records(verifier, manifest, snapshot, allow_missing=False)
            report = _report_from_manifest(manifest)
            _validate_existing_report(report_path, report)
            return report

        if staging_path.exists() is False and manifest["records"]:
            raise MigrationDryRunIdentityConflict(
                "staging database disappeared while resumable record checkpoints exist"
            )

        recorded_at = _recorded_at_from_manifest(manifest)
        writer = SQLiteWriteOwner(staging_path)
        service = LegacyImportAntiCorruptionService(writer)
        await writer.start()
        try:
            manifest = await self._verify_completed_records(
                service, manifest, snapshot, allow_missing=True
            )
            _atomic_write_json(manifest_path, manifest)
            completed_keys = {
                str(item["source_key_sha256"]) for item in manifest["records"]
            }
            processed_this_invocation = 0
            for record in snapshot.records:
                if record.source_key_sha256 in completed_keys:
                    continue
                if (
                    max_records_per_invocation is not None
                    and processed_this_invocation >= max_records_per_invocation
                ):
                    break
                request = _request_for_record(
                    record,
                    run_id=run_id,
                    snapshot=snapshot,
                    recorded_at=recorded_at,
                )
                assessment = await service.assess(request)
                summary = _summary_from_artifact(
                    assessment.artifact,
                    record.source_key_sha256,
                )
                if summary.payload_sha256 != request.source.payload_sha256:
                    raise MigrationDryRunIdentityConflict(
                        "persisted mapping payload digest differs from the source snapshot"
                    )
                manifest["records"].append(summary.model_dump(mode="json"))
                manifest["records"].sort(key=lambda item: item["source_key_sha256"])
                completed_keys.add(record.source_key_sha256)
                processed_this_invocation += 1
                _atomic_write_json(manifest_path, manifest)
        finally:
            await writer.close()

        _checkpoint_staging_database(staging_path)
        final_snapshot = _scan_source(source_path, collect_records=False)
        if final_snapshot.source_fingerprint != snapshot.source_fingerprint:
            raise MigrationDryRunSourceChanged(
                "legacy source changed during the dry run; partial evidence is retained but not finalized"
            )

        is_complete = len(manifest["records"]) == len(snapshot.records)
        manifest["status"] = "COMPLETE" if is_complete else "RUNNING"
        if is_complete:
            manifest["completed_at"] = manifest.get("completed_at") or datetime.now(
                timezone.utc
            ).isoformat()
        else:
            manifest["completed_at"] = None
        manifest["staging_db_sha256"] = _sha256_file(staging_path)
        _atomic_write_json(manifest_path, manifest)
        report = _report_from_manifest(manifest)
        _write_report(report_path, report)
        return report

    async def _verify_completed_records(
        self,
        service: LegacyImportAntiCorruptionService,
        manifest: dict[str, Any],
        snapshot: _SourceSnapshot,
        *,
        allow_missing: bool,
    ) -> dict[str, Any]:
        source_by_key = {record.source_key_sha256: record for record in snapshot.records}
        kept: list[dict[str, Any]] = []
        changed = False
        for summary in manifest["records"]:
            key = str(summary.get("source_key_sha256", ""))
            if key not in source_by_key:
                raise MigrationDryRunIdentityConflict(
                    "manifest checkpoint refers to a record outside the current source snapshot"
                )
            ref = VersionRef(
                logical_id=LogicalId(str(summary["mapping_id"])),
                version_id=VersionId(str(summary["version_id"])),
            )
            artifact = await service.get_mapping(ref)
            if artifact is None:
                if not allow_missing:
                    raise MigrationDryRunIdentityConflict(
                        "completed manifest record is missing from the staging database"
                    )
                changed = True
                continue
            observed = _summary_from_artifact(artifact, key).model_dump(mode="json")
            if observed != summary:
                raise MigrationDryRunIdentityConflict(
                    "persisted mapping differs from the durable resume checkpoint"
                )
            kept.append(summary)
        if changed:
            manifest["records"] = kept
            manifest["status"] = "RUNNING"
            manifest["completed_at"] = None
        return manifest


def _cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a read-only-source, restart-safe IMP-101 migration dry run."
    )
    parser.add_argument("--source-db", required=True, help="Path to the legacy SQLite DB (opened read-only).")
    parser.add_argument("--output-dir", required=True, help="Isolated directory for the staging DB and evidence.")
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Optional checkpoint budget for one invocation; resume by running the same command again.",
    )
    return parser


async def _run_cli(args: argparse.Namespace) -> int:
    report = await MigrationDryRunRunner().run(
        args.source_db,
        args.output_dir,
        max_records_per_invocation=args.max_records,
    )
    print(
        json.dumps(
            {
                "run_id": report.run_id,
                "status": report.status,
                "acceptance_pass": report.acceptance_pass,
                "source_fingerprint": report.source_fingerprint,
                "total_records": report.total_records,
                "completed_records": report.completed_records,
                "remaining_records": report.remaining_records,
                "disposition_counts": report.disposition_counts,
                "finding_counts": report.finding_counts,
                "mapping_counts_by_kind": report.mapping_counts_by_kind,
                "mapping_counts_by_table": report.mapping_counts_by_table,
                "staging_database": report.staging_database,
                "staging_db_sha256": report.staging_db_sha256,
            },
            sort_keys=True,
            indent=2,
        )
    )
    return 0 if report.status == "COMPLETE" and report.acceptance_pass else 2


def main() -> int:
    args = _cli_parser().parse_args()
    try:
        return asyncio.run(_run_cli(args))
    except MigrationDryRunError as exc:
        print(f"{type(exc).__name__}: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
