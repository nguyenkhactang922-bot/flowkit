"""Immutable semantic-version repository primitives for canonical Studio domains."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import AwareDatetime, BaseModel, ConfigDict

from .persistence import (
    CASConflict,
    PersistenceError,
    SQLiteReadRepository,
    SQLiteWriteOwner,
)
from .primitives import (
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    VersionId,
    VersionRef,
)


class VersionRepositoryError(PersistenceError):
    """Base error for semantic version repository operations."""


class VersionNotFound(VersionRepositoryError):
    """Raised when an exact logical/version record does not exist."""


class CurrentPointerNotFound(VersionRepositoryError):
    """Raised when a logical identity has no current pointer."""


class ContentHashMismatch(VersionRepositoryError):
    """Raised when supplied semantic metadata hash does not match payload bytes."""


class StoredSemanticVersion(BaseModel):
    """One immutable semantic realization with persisted provenance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    payload: dict[str, Any]


class CurrentVersionPointer(BaseModel):
    """Mutable coordination pointer/status, separate from immutable content."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    logical_id: LogicalId
    version_id: VersionId
    status: LifecycleState
    revision: int
    updated_at: AwareDatetime


class SupersessionRecord(BaseModel):
    """Durable history that links an older version to its successor."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    predecessor: VersionRef
    successor: VersionRef
    reason: str
    provenance: Provenance
    created_at: AwareDatetime


def _canonical_payload_json(payload: dict[str, Any]) -> str:
    try:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("semantic payload must be canonical JSON data") from exc


def _payload_hash(payload_json: str) -> str:
    digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _materialize_metadata(
    metadata: SemanticRecordMetadata,
    payload_json: str,
) -> SemanticRecordMetadata:
    actual_hash = _payload_hash(payload_json)
    if metadata.content_hash is not None and metadata.content_hash != actual_hash:
        raise ContentHashMismatch(
            f"semantic payload hash mismatch: expected {metadata.content_hash}, "
            f"actual {actual_hash}"
        )
    if metadata.content_hash == actual_hash:
        return metadata
    return metadata.model_copy(update={"content_hash": actual_hash})


def _utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class VersionRepository:
    """Repository for immutable versions + mutable current-pointer coordination."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.reader = SQLiteReadRepository(writer.db_path)

    async def create_initial(
        self,
        *,
        metadata: SemanticRecordMetadata,
        payload: dict[str, Any],
        status: LifecycleState = LifecycleState.DRAFT,
    ) -> StoredSemanticVersion:
        if metadata.predecessor is not None:
            raise ValueError("initial semantic version must not declare a predecessor")

        prepared, payload_json = self._prepare(metadata, payload)

        async def command(tx):
            await self._insert_version(tx, prepared, payload_json)
            await tx.execute(
                """
                INSERT INTO studio_current_pointer (
                    logical_id, version_id, lifecycle_status, revision, updated_at
                ) VALUES (?, ?, ?, 0, ?)
                """,
                (
                    prepared.logical_id.root,
                    prepared.version_id.root,
                    status.value,
                    _utc_now_text(),
                ),
            )

        await self.writer.execute(command)
        return StoredSemanticVersion(metadata=prepared, payload=payload)

    async def create_successor(
        self,
        *,
        metadata: SemanticRecordMetadata,
        payload: dict[str, Any],
        supersession_reason: str | None = None,
    ) -> StoredSemanticVersion:
        if metadata.predecessor is None:
            raise ValueError("successor semantic version requires predecessor")
        if metadata.predecessor.logical_id != metadata.logical_id:
            raise ValueError("successor predecessor must share logical ID")

        reason = supersession_reason or metadata.provenance.reason
        if not reason or reason != reason.strip():
            raise ValueError("supersession reason must be non-empty and trimmed")

        prepared, payload_json = self._prepare(metadata, payload)
        predecessor = prepared.predecessor
        assert predecessor is not None

        async def command(tx):
            exists = await tx.fetchone(
                """
                SELECT 1
                FROM studio_semantic_version
                WHERE logical_id=? AND version_id=?
                """,
                (prepared.logical_id.root, predecessor.version_id.root),
            )
            if exists is None:
                raise VersionNotFound(
                    f"predecessor not found: {prepared.logical_id.root}/"
                    f"{predecessor.version_id.root}"
                )

            await self._insert_version(tx, prepared, payload_json)
            await tx.execute(
                """
                INSERT INTO studio_supersession (
                    logical_id,
                    predecessor_version_id,
                    successor_version_id,
                    reason,
                    provenance_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    prepared.logical_id.root,
                    predecessor.version_id.root,
                    prepared.version_id.root,
                    reason,
                    prepared.provenance.model_dump_json(),
                    prepared.created_at.isoformat(),
                ),
            )

        await self.writer.execute(command)
        return StoredSemanticVersion(metadata=prepared, payload=payload)

    async def update_current(
        self,
        *,
        logical_id: LogicalId,
        version_id: VersionId,
        status: LifecycleState,
        expected_revision: int,
    ) -> CurrentVersionPointer:
        updated_at = _utc_now_text()

        async def command(tx):
            target = await tx.fetchone(
                """
                SELECT 1
                FROM studio_semantic_version
                WHERE logical_id=? AND version_id=?
                """,
                (logical_id.root, version_id.root),
            )
            if target is None:
                raise VersionNotFound(
                    f"version not found: {logical_id.root}/{version_id.root}"
                )

            await tx.cas_update(
                table="studio_current_pointer",
                pk_column="logical_id",
                pk_value=logical_id.root,
                expected_revision=expected_revision,
                changes={
                    "version_id": version_id.root,
                    "lifecycle_status": status.value,
                    "updated_at": updated_at,
                },
            )
            row = await tx.fetchone(
                """
                SELECT logical_id, version_id, lifecycle_status, revision, updated_at
                FROM studio_current_pointer
                WHERE logical_id=?
                """,
                (logical_id.root,),
            )
            if row is None:
                raise CurrentPointerNotFound(logical_id.root)
            return self._pointer_from_row(row)

        return await self.writer.execute(command)

    async def get_version(self, ref: VersionRef) -> StoredSemanticVersion | None:
        row = await self.reader.fetchone(
            """
            SELECT
                logical_id,
                version_id,
                payload_json,
                content_hash,
                provenance_json,
                created_at,
                predecessor_version_id
            FROM studio_semantic_version
            WHERE logical_id=? AND version_id=?
            """,
            (ref.logical_id.root, ref.version_id.root),
        )
        if row is None:
            return None
        return self._version_from_row(row)

    async def get_current(
        self,
        logical_id: LogicalId,
    ) -> CurrentVersionPointer | None:
        row = await self.reader.fetchone(
            """
            SELECT logical_id, version_id, lifecycle_status, revision, updated_at
            FROM studio_current_pointer
            WHERE logical_id=?
            """,
            (logical_id.root,),
        )
        if row is None:
            return None
        return self._pointer_from_row(row)

    async def list_supersession_history(
        self,
        logical_id: LogicalId,
    ) -> list[SupersessionRecord]:
        rows = await self.reader.fetchall(
            """
            SELECT
                logical_id,
                predecessor_version_id,
                successor_version_id,
                reason,
                provenance_json,
                created_at
            FROM studio_supersession
            WHERE logical_id=?
            ORDER BY created_at, predecessor_version_id, successor_version_id
            """,
            (logical_id.root,),
        )
        result: list[SupersessionRecord] = []
        for row in rows:
            provenance = Provenance.model_validate_json(row["provenance_json"])
            result.append(
                SupersessionRecord(
                    predecessor=VersionRef(
                        logical_id=LogicalId(row["logical_id"]),
                        version_id=VersionId(row["predecessor_version_id"]),
                    ),
                    successor=VersionRef(
                        logical_id=LogicalId(row["logical_id"]),
                        version_id=VersionId(row["successor_version_id"]),
                    ),
                    reason=row["reason"],
                    provenance=provenance,
                    created_at=row["created_at"],
                )
            )
        return result

    def _prepare(
        self,
        metadata: SemanticRecordMetadata,
        payload: dict[str, Any],
    ) -> tuple[SemanticRecordMetadata, str]:
        payload_json = _canonical_payload_json(payload)
        return _materialize_metadata(metadata, payload_json), payload_json

    async def _insert_version(
        self,
        tx,
        metadata: SemanticRecordMetadata,
        payload_json: str,
    ) -> None:
        predecessor_version_id = (
            metadata.predecessor.version_id.root
            if metadata.predecessor is not None
            else None
        )
        await tx.execute(
            """
            INSERT INTO studio_semantic_version (
                logical_id,
                version_id,
                payload_json,
                content_hash,
                provenance_json,
                created_at,
                predecessor_version_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metadata.logical_id.root,
                metadata.version_id.root,
                payload_json,
                metadata.content_hash,
                metadata.provenance.model_dump_json(),
                metadata.created_at.isoformat(),
                predecessor_version_id,
            ),
        )

    @staticmethod
    def _version_from_row(row) -> StoredSemanticVersion:
        logical_id = LogicalId(row["logical_id"])
        predecessor = (
            VersionRef(
                logical_id=logical_id,
                version_id=VersionId(row["predecessor_version_id"]),
            )
            if row["predecessor_version_id"] is not None
            else None
        )
        metadata = SemanticRecordMetadata(
            logical_id=logical_id,
            version_id=VersionId(row["version_id"]),
            provenance=Provenance.model_validate_json(row["provenance_json"]),
            created_at=row["created_at"],
            predecessor=predecessor,
            content_hash=row["content_hash"],
        )
        return StoredSemanticVersion(
            metadata=metadata,
            payload=json.loads(row["payload_json"]),
        )

    @staticmethod
    def _pointer_from_row(row) -> CurrentVersionPointer:
        return CurrentVersionPointer(
            logical_id=LogicalId(row["logical_id"]),
            version_id=VersionId(row["version_id"]),
            status=LifecycleState(row["lifecycle_status"]),
            revision=int(row["revision"]),
            updated_at=row["updated_at"],
        )
