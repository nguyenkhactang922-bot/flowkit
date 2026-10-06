"""IMP-055 artifact byte lifecycle, immutable evidence, and startup reconciliation.

GenerationJob.artifact_state remains the sole mutable lifecycle authority.  This
module owns filesystem materialization plus immutable artifact identity and
append-only byte/reconciliation evidence.  It never owns creative approval.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .generation_job import (
    ArtifactState,
    CreativeState,
    GenerationJob,
    GenerationJobAxis,
    GenerationJobRepository,
    GuardFact,
    TransitionGuardEvidence,
    TransitionOwner,
)
from .persistence import SQLiteReadRepository, SQLiteWriteOwner
from .primitives import LogicalId


_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_EXT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,15}$")
_MEDIA_RE = re.compile(r"^[a-z0-9][a-z0-9.+-]*/[a-z0-9][a-z0-9.+-]*$")


class ArtifactLifecycleError(RuntimeError):
    """Base IMP-055 artifact lifecycle error."""


class ArtifactIdentityConflict(ArtifactLifecycleError):
    """Raised when a deterministic artifact/event identity conflicts."""


class ArtifactIntegrityError(ArtifactLifecycleError):
    """Raised when bytes/path/hash integrity cannot be trusted."""


class ArtifactLifecycleBlocked(ArtifactLifecycleError):
    """Raised when a request violates the canonical artifact transition contract."""


class ArtifactEventKind(str, Enum):
    BEGIN_MATERIALIZE = "BEGIN_MATERIALIZE"
    STAGING_BYTES_WRITTEN = "STAGING_BYTES_WRITTEN"
    FINAL_BYTES_WRITTEN = "FINAL_BYTES_WRITTEN"
    MATERIALIZE_VALID = "MATERIALIZE_VALID"
    INPUT_BECAME_STALE = "INPUT_BECAME_STALE"
    INTEGRITY_FAILED = "INTEGRITY_FAILED"
    LINEAGE_UNTRUSTED = "LINEAGE_UNTRUSTED"
    FILE_MISSING = "FILE_MISSING"
    ARCHIVE = "ARCHIVE"
    RECOVER_BYTES = "RECOVER_BYTES"
    DISCOVER_ORPHAN = "DISCOVER_ORPHAN"


class ReconcileClassification(str, Enum):
    NO_ACTION = "NO_ACTION"
    STAGING_PRESENT = "STAGING_PRESENT"
    STAGING_INCOMPLETE = "STAGING_INCOMPLETE"
    RECOVERED_READY = "RECOVERED_READY"
    STALE_RESULT = "STALE_RESULT"
    MISSING = "MISSING"
    CORRUPT = "CORRUPT"
    QUARANTINED_ORPHAN = "QUARANTINED_ORPHAN"


def artifact_logical_id(job_id: LogicalId) -> LogicalId:
    digest = hashlib.sha256(job_id.root.encode("utf-8")).hexdigest()[:32]
    return LogicalId(f"generation-artifact:{digest}")


def artifact_storage_key(job_id: LogicalId) -> str:
    return hashlib.sha256(job_id.root.encode("utf-8")).hexdigest()


def derive_artifact_event_id(
    artifact_id: LogicalId,
    attempt: int,
    event_kind: ArtifactEventKind,
) -> str:
    raw = f"{artifact_id.root}|{attempt}|{event_kind.value}".encode("utf-8")
    return "artifact-event:" + hashlib.sha256(raw).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _trimmed(value: str, label: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{label} must be non-empty")
    return value


def _relative_path(value: str, label: str) -> str:
    value = value.replace("\\", "/").strip()
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must be a safe relative path")
    return str(path)


class ArtifactIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_id: LogicalId
    generation_job_id: LogicalId
    storage_key: str
    actor_ref: str
    reason: str
    correlation_id: str
    created_at: datetime

    @field_validator("storage_key", "actor_ref", "reason", "correlation_id")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_identity(self) -> "ArtifactIdentity":
        if self.artifact_id != artifact_logical_id(self.generation_job_id):
            raise ValueError("artifact_id must be deterministic from GenerationJob identity")
        if self.storage_key != artifact_storage_key(self.generation_job_id):
            raise ValueError("storage_key must be deterministic from GenerationJob identity")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        return self


class ArtifactEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_event_id: str
    artifact_id: LogicalId
    generation_job_id: LogicalId
    attempt: int = Field(ge=1)
    event_kind: ArtifactEventKind
    job_revision_observed: int = Field(ge=0)
    expected_input_fingerprint: str
    observed_input_fingerprint: str | None = None
    staging_relative_path: str | None = None
    final_relative_path: str | None = None
    content_sha256: str | None = None
    byte_count: int | None = Field(default=None, ge=0)
    media_type: str | None = None
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    actor_ref: str
    reason: str
    correlation_id: str
    created_at: datetime

    @field_validator("expected_input_fingerprint", "observed_input_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str | None) -> str | None:
        if value is not None and not _HASH_RE.fullmatch(value):
            raise ValueError("fingerprints must be sha256:<64 lowercase hex>")
        return value

    @field_validator("content_sha256")
    @classmethod
    def validate_hash(cls, value: str | None) -> str | None:
        if value is not None and not _HASH_RE.fullmatch(value):
            raise ValueError("content_sha256 must be sha256:<64 lowercase hex>")
        return value

    @field_validator("staging_relative_path", "final_relative_path")
    @classmethod
    def validate_paths(cls, value: str | None, info) -> str | None:
        return None if value is None else _relative_path(value, info.field_name)

    @field_validator("media_type")
    @classmethod
    def validate_media_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower()
        if not _MEDIA_RE.fullmatch(value):
            raise ValueError("media_type must be a normalized MIME type")
        return value

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_trimmed(value, "evidence_ref") for value in values)
        if len(normalized) != len(set(normalized)):
            raise ValueError("evidence_refs must be unique")
        return normalized

    @field_validator("actor_ref", "reason", "correlation_id")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_identity(self) -> "ArtifactEvent":
        expected_id = derive_artifact_event_id(self.artifact_id, self.attempt, self.event_kind)
        if self.artifact_event_id != expected_id:
            raise ValueError("artifact_event_id must be deterministic")
        if self.artifact_id != artifact_logical_id(self.generation_job_id):
            raise ValueError("artifact_id/job identity mismatch")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.byte_count is not None and self.content_sha256 is None:
            raise ValueError("byte_count requires content_sha256")
        return self


class ArtifactPaths(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    staging_relative_path: str
    final_relative_path: str

    @field_validator("staging_relative_path", "final_relative_path")
    @classmethod
    def validate_path(cls, value: str, info) -> str:
        return _relative_path(value, info.field_name)


class ReconcileFinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    generation_job_id: LogicalId
    artifact_id: LogicalId
    classification: ReconcileClassification
    message: str
    resulting_artifact_state: ArtifactState

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        return _trimmed(value, "message")


class ArtifactEvidenceRepository:
    """Immutable identity + append-only artifact evidence; no lifecycle status store."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.reader = SQLiteReadRepository(writer.db_path)

    async def get_identity_for_job(self, job_id: LogicalId) -> ArtifactIdentity | None:
        row = await self.reader.fetchone(
            "SELECT * FROM studio_generation_artifact_identity WHERE generation_job_id=?",
            (job_id.root,),
        )
        return None if row is None else self._identity_from_row(row)

    async def ensure_identity(self, identity: ArtifactIdentity) -> ArtifactIdentity:
        async def command(tx):
            existing = await tx.fetchone(
                "SELECT * FROM studio_generation_artifact_identity WHERE generation_job_id=?",
                (identity.generation_job_id.root,),
            )
            if existing is not None:
                stored = self._identity_from_row(existing)
                # The identity is deterministic from GenerationJob. Audit-envelope fields
                # describe the first creation and must not make safe retries conflict.
                if (
                    stored.artifact_id != identity.artifact_id
                    or stored.generation_job_id != identity.generation_job_id
                    or stored.storage_key != identity.storage_key
                ):
                    raise ArtifactIdentityConflict(
                        "artifact identity already exists with different deterministic identity"
                    )
                return stored
            await tx.execute(
                """
                INSERT INTO studio_generation_artifact_identity (
                    artifact_id,generation_job_id,storage_key,actor_ref,reason,
                    correlation_id,created_at
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    identity.artifact_id.root,
                    identity.generation_job_id.root,
                    identity.storage_key,
                    identity.actor_ref,
                    identity.reason,
                    identity.correlation_id,
                    identity.created_at.isoformat(),
                ),
            )
            return identity

        return await self.writer.execute(command)

    async def get_event(
        self,
        artifact_id: LogicalId,
        attempt: int,
        event_kind: ArtifactEventKind,
    ) -> ArtifactEvent | None:
        row = await self.reader.fetchone(
            """
            SELECT * FROM studio_generation_artifact_event
            WHERE artifact_id=? AND attempt=? AND event_kind=?
            """,
            (artifact_id.root, attempt, event_kind.value),
        )
        return None if row is None else self._event_from_row(row)

    async def list_events_for_job(self, job_id: LogicalId) -> list[ArtifactEvent]:
        rows = await self.reader.fetchall(
            """
            SELECT * FROM studio_generation_artifact_event
            WHERE generation_job_id=? ORDER BY attempt,created_at,artifact_event_id
            """,
            (job_id.root,),
        )
        return [self._event_from_row(row) for row in rows]

    async def append_event(self, event: ArtifactEvent) -> ArtifactEvent:
        async def command(tx):
            existing = await tx.fetchone(
                "SELECT * FROM studio_generation_artifact_event WHERE artifact_event_id=?",
                (event.artifact_event_id,),
            )
            if existing is not None:
                stored = self._event_from_row(existing)
                if not self._same_event_semantics(stored, event):
                    raise ArtifactIdentityConflict(
                        "artifact event identity already exists with different immutable evidence"
                    )
                return stored
            await tx.execute(
                """
                INSERT INTO studio_generation_artifact_event (
                    artifact_event_id,artifact_id,generation_job_id,attempt,event_kind,
                    job_revision_observed,expected_input_fingerprint,observed_input_fingerprint,
                    staging_relative_path,final_relative_path,content_sha256,byte_count,media_type,
                    evidence_json,actor_ref,reason,correlation_id,created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    event.artifact_event_id,
                    event.artifact_id.root,
                    event.generation_job_id.root,
                    event.attempt,
                    event.event_kind.value,
                    event.job_revision_observed,
                    event.expected_input_fingerprint,
                    event.observed_input_fingerprint,
                    event.staging_relative_path,
                    event.final_relative_path,
                    event.content_sha256,
                    event.byte_count,
                    event.media_type,
                    json.dumps({"evidence_refs": list(event.evidence_refs)}, sort_keys=True, separators=(",", ":")),
                    event.actor_ref,
                    event.reason,
                    event.correlation_id,
                    event.created_at.isoformat(),
                ),
            )
            return event

        return await self.writer.execute(command)

    @staticmethod
    def _same_event_semantics(left: ArtifactEvent, right: ArtifactEvent) -> bool:
        # Retry/reconciliation calls may have a different audit envelope. The first
        # append remains durable; idempotency is decided by the materialization fact.
        excluded = {"evidence_refs", "actor_ref", "reason", "correlation_id", "created_at"}
        return left.model_dump(exclude=excluded) == right.model_dump(exclude=excluded)

    @staticmethod
    def _identity_from_row(row) -> ArtifactIdentity:
        return ArtifactIdentity(
            artifact_id=LogicalId(str(row["artifact_id"])),
            generation_job_id=LogicalId(str(row["generation_job_id"])),
            storage_key=str(row["storage_key"]),
            actor_ref=str(row["actor_ref"]),
            reason=str(row["reason"]),
            correlation_id=str(row["correlation_id"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )

    @staticmethod
    def _event_from_row(row) -> ArtifactEvent:
        evidence = json.loads(str(row["evidence_json"]))
        return ArtifactEvent(
            artifact_event_id=str(row["artifact_event_id"]),
            artifact_id=LogicalId(str(row["artifact_id"])),
            generation_job_id=LogicalId(str(row["generation_job_id"])),
            attempt=int(row["attempt"]),
            event_kind=ArtifactEventKind(str(row["event_kind"])),
            job_revision_observed=int(row["job_revision_observed"]),
            expected_input_fingerprint=str(row["expected_input_fingerprint"]),
            observed_input_fingerprint=None if row["observed_input_fingerprint"] is None else str(row["observed_input_fingerprint"]),
            staging_relative_path=None if row["staging_relative_path"] is None else str(row["staging_relative_path"]),
            final_relative_path=None if row["final_relative_path"] is None else str(row["final_relative_path"]),
            content_sha256=None if row["content_sha256"] is None else str(row["content_sha256"]),
            byte_count=None if row["byte_count"] is None else int(row["byte_count"]),
            media_type=None if row["media_type"] is None else str(row["media_type"]),
            evidence_refs=tuple(str(value) for value in evidence["evidence_refs"]),
            actor_ref=str(row["actor_ref"]),
            reason=str(row["reason"]),
            correlation_id=str(row["correlation_id"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )


class ArtifactLifecycleService:
    """Filesystem side-effect coordinator over the existing GenerationJob artifact axis."""

    def __init__(self, writer: SQLiteWriteOwner, artifact_root: Path) -> None:
        self.writer = writer
        self.jobs = GenerationJobRepository(writer)
        self.evidence = ArtifactEvidenceRepository(writer)
        self.artifact_root = Path(artifact_root)

    def paths_for(self, identity: ArtifactIdentity, attempt: int, extension: str) -> ArtifactPaths:
        extension = extension.strip().lower().lstrip(".")
        if not _EXT_RE.fullmatch(extension):
            raise ArtifactLifecycleBlocked("extension must be a safe normalized extension")
        suffix = f"attempt-{attempt:04d}.{extension}"
        return ArtifactPaths(
            staging_relative_path=f".staging/{identity.storage_key}/attempt-{attempt:04d}.partial",
            final_relative_path=f"objects/{identity.storage_key}/{suffix}",
        )

    def absolute_path(self, relative_path: str) -> Path:
        relative = _relative_path(relative_path, "relative_path")
        root = self.artifact_root.resolve()
        path = (root / Path(relative)).resolve()
        if root != path and root not in path.parents:
            raise ArtifactLifecycleBlocked("artifact path escapes artifact root")
        return path

    async def begin_materialization(
        self,
        *,
        job_id: LogicalId,
        attempt: int,
        extension: str,
        media_type: str,
        guard_evidence: TransitionGuardEvidence,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> tuple[ArtifactIdentity, ArtifactPaths, GenerationJob]:
        job = await self._require_job(job_id)
        identity = await self._ensure_identity(job, actor_ref, reason, correlation_id, recorded_at)
        paths = self.paths_for(identity, attempt, extension)
        event = self._event(
            identity=identity,
            job=job,
            attempt=attempt,
            kind=ArtifactEventKind.BEGIN_MATERIALIZE,
            recorded_at=recorded_at,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            evidence_refs=evidence_refs,
            paths=paths,
            media_type=media_type,
        )
        existing = await self.evidence.get_event(identity.artifact_id, attempt, ArtifactEventKind.BEGIN_MATERIALIZE)
        if existing is None:
            await self.evidence.append_event(event)
        else:
            if (
                existing.generation_job_id != job_id
                or existing.expected_input_fingerprint != job.expected_input_fingerprint
                or existing.staging_relative_path != paths.staging_relative_path
                or existing.final_relative_path != paths.final_relative_path
                or existing.media_type != event.media_type
            ):
                raise ArtifactIdentityConflict("begin materialization replay conflicts with immutable evidence")
            event = existing

        current = await self._require_job(job_id)
        if current.artifact_state is ArtifactState.NONE:
            result = await self.jobs.transition(
                job_id=job_id,
                axis=GenerationJobAxis.ARTIFACT,
                command="BEGIN_MATERIALIZE",
                owner=TransitionOwner.ARTIFACT_STORE,
                guard_evidence=guard_evidence,
                expected_revision=current.revision,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                recorded_at=recorded_at,
            )
            current = result.job
        elif current.artifact_state is not ArtifactState.STAGING:
            raise ArtifactLifecycleBlocked(
                f"begin materialization requires artifact NONE/STAGING, got {current.artifact_state.value}"
            )
        return identity, paths, current

    async def write_staging_bytes(
        self,
        *,
        job_id: LogicalId,
        attempt: int,
        data: bytes,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> ArtifactEvent:
        if not data:
            raise ArtifactIntegrityError("artifact bytes must not be empty")
        job = await self._require_job(job_id)
        if job.artifact_state is not ArtifactState.STAGING:
            raise ArtifactLifecycleBlocked("staging bytes require artifact STAGING")
        identity = await self._require_identity(job_id)
        begin = await self._require_begin(identity, attempt)
        assert begin.staging_relative_path is not None
        path = self.absolute_path(begin.staging_relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        content_hash = _sha256_bytes(data)
        if path.exists():
            existing = path.read_bytes()
            if existing != data:
                raise ArtifactIdentityConflict("immutable staging path already contains different bytes")
        else:
            with open(path, "xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        event = self._event(
            identity=identity,
            job=job,
            attempt=attempt,
            kind=ArtifactEventKind.STAGING_BYTES_WRITTEN,
            recorded_at=recorded_at,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            evidence_refs=evidence_refs,
            paths=ArtifactPaths(
                staging_relative_path=begin.staging_relative_path,
                final_relative_path=begin.final_relative_path or "objects/unknown",
            ),
            observed_input_fingerprint=begin.observed_input_fingerprint,
            content_sha256=content_hash,
            byte_count=len(data),
            media_type=begin.media_type,
        )
        return await self.evidence.append_event(event)

    async def finalize_materialization(
        self,
        *,
        job_id: LogicalId,
        attempt: int,
        current_input_fingerprint: str,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> GenerationJob:
        if not _HASH_RE.fullmatch(current_input_fingerprint):
            raise ArtifactLifecycleBlocked("current_input_fingerprint must be canonical sha256")
        job = await self._require_job(job_id)
        if job.artifact_state not in {ArtifactState.STAGING, ArtifactState.READY, ArtifactState.STALE_RESULT}:
            raise ArtifactLifecycleBlocked("finalize requires STAGING or idempotent terminal materialization state")
        if job.artifact_state in {ArtifactState.READY, ArtifactState.STALE_RESULT}:
            return job
        identity = await self._require_identity(job_id)
        begin = await self._require_begin(identity, attempt)
        staged = await self.evidence.get_event(
            identity.artifact_id, attempt, ArtifactEventKind.STAGING_BYTES_WRITTEN
        )
        if staged is None or staged.content_sha256 is None or staged.byte_count is None:
            raise ArtifactLifecycleBlocked(
                "finalize requires durable STAGING_BYTES_WRITTEN hash/size evidence"
            )
        if begin.staging_relative_path is None or begin.final_relative_path is None:
            raise ArtifactIntegrityError("begin evidence lacks deterministic paths")
        staging = self.absolute_path(begin.staging_relative_path)
        final = self.absolute_path(begin.final_relative_path)

        source = staging if staging.exists() else final if final.exists() else None
        if source is None:
            raise ArtifactIntegrityError("materialization bytes are missing")
        data = source.read_bytes()
        if not data:
            return await self._mark_corrupt(
                job=job,
                identity=identity,
                attempt=attempt,
                paths=ArtifactPaths(staging_relative_path=begin.staging_relative_path, final_relative_path=begin.final_relative_path),
                data=data,
                actor_ref=actor_ref,
                reason="empty/corrupt artifact bytes",
                correlation_id=correlation_id,
                recorded_at=recorded_at,
                evidence_refs=evidence_refs,
            )
        content_hash = _sha256_bytes(data)
        if content_hash != staged.content_sha256 or len(data) != staged.byte_count:
            return await self._mark_corrupt(
                job=job,
                identity=identity,
                attempt=attempt,
                paths=ArtifactPaths(
                    staging_relative_path=begin.staging_relative_path,
                    final_relative_path=begin.final_relative_path,
                ),
                data=data,
                actor_ref=actor_ref,
                reason="artifact bytes differ from durable staging hash/size evidence",
                correlation_id=correlation_id,
                recorded_at=recorded_at,
                evidence_refs=evidence_refs,
            )
        if staging.exists():
            final.parent.mkdir(parents=True, exist_ok=True)
            if final.exists():
                if _sha256_bytes(final.read_bytes()) != content_hash:
                    raise ArtifactIntegrityError("immutable final path already contains different bytes")
                staging.unlink()
            else:
                os.replace(staging, final)
        final_event = self._event(
            identity=identity,
            job=job,
            attempt=attempt,
            kind=ArtifactEventKind.FINAL_BYTES_WRITTEN,
            recorded_at=recorded_at,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            evidence_refs=evidence_refs,
            paths=ArtifactPaths(staging_relative_path=begin.staging_relative_path, final_relative_path=begin.final_relative_path),
            observed_input_fingerprint=current_input_fingerprint,
            content_sha256=content_hash,
            byte_count=len(data),
            media_type=begin.media_type,
        )
        final_event = await self._append_or_verify(final_event)

        if current_input_fingerprint != job.expected_input_fingerprint:
            stale = final_event.model_copy(
                update={
                    "artifact_event_id": derive_artifact_event_id(identity.artifact_id, attempt, ArtifactEventKind.INPUT_BECAME_STALE),
                    "event_kind": ArtifactEventKind.INPUT_BECAME_STALE,
                    "reason": "materialized result input fingerprint is stale",
                }
            )
            await self._append_or_verify(stale)
            result = await self.jobs.transition(
                job_id=job_id,
                axis=GenerationJobAxis.ARTIFACT,
                command="INPUT_BECAME_STALE",
                owner=TransitionOwner.ARTIFACT_RECONCILER,
                guard_evidence=self._guard("stale result fingerprint mismatch", evidence_refs, input_fingerprint_match=False),
                expected_revision=job.revision,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                recorded_at=recorded_at,
            )
            return result.job

        valid = final_event.model_copy(
            update={
                "artifact_event_id": derive_artifact_event_id(identity.artifact_id, attempt, ArtifactEventKind.MATERIALIZE_VALID),
                "event_kind": ArtifactEventKind.MATERIALIZE_VALID,
                "reason": "artifact bytes/hash/lineage validated",
            }
        )
        await self._append_or_verify(valid)
        result = await self.jobs.transition(
            job_id=job_id,
            axis=GenerationJobAxis.ARTIFACT,
            command="MATERIALIZE_VALID",
            owner=TransitionOwner.ARTIFACT_STORE,
            guard_evidence=self._guard("artifact integrity validation", evidence_refs, input_fingerprint_match=True, hash_valid=True),
            expected_revision=job.revision,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            recorded_at=recorded_at,
        )
        return result.job

    async def recover_bytes(
        self,
        *,
        job_id: LogicalId,
        attempt: int,
        extension: str,
        media_type: str,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> tuple[ArtifactIdentity, ArtifactPaths, GenerationJob]:
        job = await self._require_job(job_id)
        if job.artifact_state not in {ArtifactState.MISSING, ArtifactState.CORRUPT}:
            raise ArtifactLifecycleBlocked("RECOVER_BYTES requires MISSING/CORRUPT")
        identity = await self._require_identity(job_id)
        paths = self.paths_for(identity, attempt, extension)
        event = self._event(
            identity=identity,
            job=job,
            attempt=attempt,
            kind=ArtifactEventKind.RECOVER_BYTES,
            recorded_at=recorded_at,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            evidence_refs=evidence_refs,
            paths=paths,
            media_type=media_type,
        )
        await self._append_or_verify(event)
        result = await self.jobs.transition(
            job_id=job_id,
            axis=GenerationJobAxis.ARTIFACT,
            command="RECOVER_BYTES",
            owner=TransitionOwner.ARTIFACT_RECONCILER,
            guard_evidence=self._guard("authorized artifact byte recovery", evidence_refs, authoritative_lineage=True),
            expected_revision=job.revision,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            recorded_at=recorded_at,
        )
        return identity, paths, result.job

    async def archive(
        self,
        *,
        job_id: LogicalId,
        attempt: int,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> GenerationJob:
        job = await self._require_job(job_id)
        if job.artifact_state not in {ArtifactState.READY, ArtifactState.STALE_RESULT, ArtifactState.QUARANTINED}:
            raise ArtifactLifecycleBlocked("ARCHIVE requires READY/STALE_RESULT/QUARANTINED")
        identity = await self._require_identity(job_id)
        prior = await self._best_path_event(identity.artifact_id)
        event = self._event(
            identity=identity,
            job=job,
            attempt=attempt,
            kind=ArtifactEventKind.ARCHIVE,
            recorded_at=recorded_at,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            evidence_refs=evidence_refs,
            paths=None if prior is None or prior.staging_relative_path is None or prior.final_relative_path is None else ArtifactPaths(staging_relative_path=prior.staging_relative_path, final_relative_path=prior.final_relative_path),
            content_sha256=None if prior is None else prior.content_sha256,
            byte_count=None if prior is None else prior.byte_count,
            media_type=None if prior is None else prior.media_type,
        )
        await self._append_or_verify(event)
        result = await self.jobs.transition(
            job_id=job_id,
            axis=GenerationJobAxis.ARTIFACT,
            command="ARCHIVE",
            owner=TransitionOwner.ARTIFACT_STORE,
            guard_evidence=self._guard("artifact retention archive", evidence_refs, archive_authorized=True),
            expected_revision=job.revision,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            recorded_at=recorded_at,
        )
        return result.job

    async def reconcile_job(
        self,
        *,
        job_id: LogicalId,
        current_input_fingerprint: str,
        actor_ref: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...] = ("startup-reconcile",),
    ) -> ReconcileFinding:
        job = await self._require_job(job_id)
        identity = await self.evidence.get_identity_for_job(job_id)
        if identity is None:
            # A deterministic final directory for a known job with no trusted DB lineage is an orphan.
            storage_key = artifact_storage_key(job_id)
            object_dir = self.artifact_root / "objects" / storage_key
            finals = sorted(path for path in object_dir.glob("attempt-*.*") if path.is_file()) if object_dir.exists() else []
            if finals and job.artifact_state is ArtifactState.NONE:
                identity = await self._ensure_identity(job, actor_ref, "startup discovered orphan final bytes", correlation_id, recorded_at)
                event = self._event(
                    identity=identity,
                    job=job,
                    attempt=self._attempt_from_path(finals[0]),
                    kind=ArtifactEventKind.DISCOVER_ORPHAN,
                    recorded_at=recorded_at,
                    actor_ref=actor_ref,
                    reason="final bytes exist without trusted materialization lineage",
                    correlation_id=correlation_id,
                    evidence_refs=evidence_refs,
                    paths=ArtifactPaths(staging_relative_path=f".staging/{storage_key}/orphan.partial", final_relative_path=finals[0].relative_to(self.artifact_root).as_posix()),
                    content_sha256=_sha256_bytes(finals[0].read_bytes()),
                    byte_count=finals[0].stat().st_size,
                    media_type="application/octet-stream",
                )
                await self._append_or_verify(event)
                result = await self.jobs.transition(
                    job_id=job_id,
                    axis=GenerationJobAxis.ARTIFACT,
                    command="DISCOVER_ORPHAN",
                    owner=TransitionOwner.ARTIFACT_RECONCILER,
                    guard_evidence=self._guard("orphan final bytes discovered", evidence_refs, trusted_lineage=False),
                    expected_revision=job.revision,
                    actor_ref=actor_ref,
                    reason=event.reason,
                    correlation_id=correlation_id,
                    recorded_at=recorded_at,
                )
                return ReconcileFinding(
                    generation_job_id=job_id,
                    artifact_id=identity.artifact_id,
                    classification=ReconcileClassification.QUARANTINED_ORPHAN,
                    message="orphan final bytes quarantined; no automatic READY promotion",
                    resulting_artifact_state=result.job.artifact_state,
                )
            return ReconcileFinding(
                generation_job_id=job_id,
                artifact_id=artifact_logical_id(job_id),
                classification=ReconcileClassification.NO_ACTION,
                message="no artifact identity or orphan bytes",
                resulting_artifact_state=job.artifact_state,
            )

        events = await self.evidence.list_events_for_job(job_id)
        begin_events = [item for item in events if item.event_kind in {ArtifactEventKind.BEGIN_MATERIALIZE, ArtifactEventKind.RECOVER_BYTES}]
        latest_begin = max(begin_events, key=lambda item: item.attempt) if begin_events else None
        if job.artifact_state is ArtifactState.NONE:
            orphan_events = [item for item in events if item.event_kind is ArtifactEventKind.DISCOVER_ORPHAN]
            if orphan_events:
                orphan = max(orphan_events, key=lambda item: (item.attempt, item.created_at))
                result = await self.jobs.transition(
                    job_id=job_id,
                    axis=GenerationJobAxis.ARTIFACT,
                    command="DISCOVER_ORPHAN",
                    owner=TransitionOwner.ARTIFACT_RECONCILER,
                    guard_evidence=self._guard(
                        "complete durable orphan discovery after interrupted transition",
                        evidence_refs,
                        trusted_lineage=False,
                    ),
                    expected_revision=job.revision,
                    actor_ref=actor_ref,
                    reason="startup completed durable orphan quarantine transition",
                    correlation_id=correlation_id,
                    recorded_at=recorded_at,
                )
                return ReconcileFinding(
                    generation_job_id=job_id,
                    artifact_id=identity.artifact_id,
                    classification=ReconcileClassification.QUARANTINED_ORPHAN,
                    message=f"completed interrupted orphan quarantine from {orphan.artifact_event_id}",
                    resulting_artifact_state=result.job.artifact_state,
                )
            if latest_begin is not None:
                return ReconcileFinding(
                    generation_job_id=job_id,
                    artifact_id=identity.artifact_id,
                    classification=ReconcileClassification.STAGING_INCOMPLETE,
                    message="begin evidence exists while artifact state is NONE; explicit store resume required",
                    resulting_artifact_state=job.artifact_state,
                )

        if job.artifact_state is ArtifactState.STAGING:
            if latest_begin is None or latest_begin.final_relative_path is None or latest_begin.staging_relative_path is None:
                return ReconcileFinding(generation_job_id=job_id, artifact_id=identity.artifact_id, classification=ReconcileClassification.STAGING_INCOMPLETE, message="STAGING has incomplete durable path evidence", resulting_artifact_state=job.artifact_state)
            final = self.absolute_path(latest_begin.final_relative_path)
            staging = self.absolute_path(latest_begin.staging_relative_path)
            if final.exists():
                updated = await self.finalize_materialization(
                    job_id=job_id,
                    attempt=latest_begin.attempt,
                    current_input_fingerprint=current_input_fingerprint,
                    actor_ref=actor_ref,
                    reason="startup repaired final-bytes-before-state crash window",
                    correlation_id=correlation_id,
                    recorded_at=recorded_at,
                    evidence_refs=evidence_refs,
                )
                classification = ReconcileClassification.RECOVERED_READY if updated.artifact_state is ArtifactState.READY else ReconcileClassification.STALE_RESULT
                return ReconcileFinding(generation_job_id=job_id, artifact_id=identity.artifact_id, classification=classification, message="startup reconciled durable final bytes", resulting_artifact_state=updated.artifact_state)
            if staging.exists():
                return ReconcileFinding(generation_job_id=job_id, artifact_id=identity.artifact_id, classification=ReconcileClassification.STAGING_PRESENT, message="staging bytes remain; materialization may resume", resulting_artifact_state=job.artifact_state)
            return ReconcileFinding(generation_job_id=job_id, artifact_id=identity.artifact_id, classification=ReconcileClassification.STAGING_INCOMPLETE, message="STAGING metadata exists but no staged/final bytes; no illegal transition invented", resulting_artifact_state=job.artifact_state)

        if job.artifact_state is ArtifactState.READY:
            valid_events = [item for item in events if item.event_kind is ArtifactEventKind.MATERIALIZE_VALID]
            latest = max(valid_events, key=lambda item: item.attempt) if valid_events else None
            if latest is None or latest.final_relative_path is None or latest.content_sha256 is None:
                raise ArtifactIntegrityError("READY job lacks immutable materialization evidence")
            final = self.absolute_path(latest.final_relative_path)
            if not final.exists():
                missing = latest.model_copy(update={"artifact_event_id": derive_artifact_event_id(identity.artifact_id, latest.attempt, ArtifactEventKind.FILE_MISSING), "event_kind": ArtifactEventKind.FILE_MISSING, "job_revision_observed": job.revision, "reason": "startup found READY metadata with missing bytes"})
                await self._append_or_verify(missing)
                result = await self.jobs.transition(job_id=job_id, axis=GenerationJobAxis.ARTIFACT, command="FILE_MISSING", owner=TransitionOwner.ARTIFACT_RECONCILER, guard_evidence=self._guard("READY file missing", evidence_refs, file_present=False), expected_revision=job.revision, actor_ref=actor_ref, reason=missing.reason, correlation_id=correlation_id, recorded_at=recorded_at)
                return ReconcileFinding(generation_job_id=job_id, artifact_id=identity.artifact_id, classification=ReconcileClassification.MISSING, message="READY artifact bytes are missing", resulting_artifact_state=result.job.artifact_state)
            data = final.read_bytes()
            if _sha256_bytes(data) != latest.content_sha256 or len(data) != latest.byte_count:
                corrupt = latest.model_copy(update={"artifact_event_id": derive_artifact_event_id(identity.artifact_id, latest.attempt, ArtifactEventKind.INTEGRITY_FAILED), "event_kind": ArtifactEventKind.INTEGRITY_FAILED, "job_revision_observed": job.revision, "reason": "startup checksum/size mismatch"})
                await self._append_or_verify(corrupt)
                result = await self.jobs.transition(job_id=job_id, axis=GenerationJobAxis.ARTIFACT, command="INTEGRITY_FAILED", owner=TransitionOwner.ARTIFACT_RECONCILER, guard_evidence=self._guard("READY integrity mismatch", evidence_refs, hash_valid=False), expected_revision=job.revision, actor_ref=actor_ref, reason=corrupt.reason, correlation_id=correlation_id, recorded_at=recorded_at)
                return ReconcileFinding(generation_job_id=job_id, artifact_id=identity.artifact_id, classification=ReconcileClassification.CORRUPT, message="READY artifact checksum/size mismatch", resulting_artifact_state=result.job.artifact_state)
            if current_input_fingerprint != job.expected_input_fingerprint:
                stale = latest.model_copy(update={"artifact_event_id": derive_artifact_event_id(identity.artifact_id, latest.attempt, ArtifactEventKind.INPUT_BECAME_STALE), "event_kind": ArtifactEventKind.INPUT_BECAME_STALE, "job_revision_observed": job.revision, "observed_input_fingerprint": current_input_fingerprint, "reason": "startup detected current input fingerprint mismatch"})
                await self._append_or_verify(stale)
                result = await self.jobs.transition(job_id=job_id, axis=GenerationJobAxis.ARTIFACT, command="DEPENDENCY_OR_INPUT_INVALIDATED", owner=TransitionOwner.ARTIFACT_RECONCILER, guard_evidence=self._guard("READY input became stale", evidence_refs, input_fingerprint_match=False), expected_revision=job.revision, actor_ref=actor_ref, reason=stale.reason, correlation_id=correlation_id, recorded_at=recorded_at)
                return ReconcileFinding(generation_job_id=job_id, artifact_id=identity.artifact_id, classification=ReconcileClassification.STALE_RESULT, message="READY artifact input fingerprint is stale", resulting_artifact_state=result.job.artifact_state)

        return ReconcileFinding(generation_job_id=job_id, artifact_id=identity.artifact_id, classification=ReconcileClassification.NO_ACTION, message="artifact state/evidence is consistent", resulting_artifact_state=job.artifact_state)

    async def reconcile_startup(
        self,
        *,
        current_input_fingerprint: Callable[[GenerationJob], str],
        actor_ref: str,
        correlation_id: str,
        recorded_at: datetime,
    ) -> tuple[ReconcileFinding, ...]:
        rows = await SQLiteReadRepository(self.writer.db_path).fetchall(
            """
            SELECT generation_job_id FROM studio_generation_job
            WHERE artifact_state IN ('NONE','STAGING','READY')
            ORDER BY created_at,generation_job_id
            """
        )
        findings: list[ReconcileFinding] = []
        for row in rows:
            job = await self._require_job(LogicalId(str(row["generation_job_id"])))
            findings.append(
                await self.reconcile_job(
                    job_id=job.generation_job_id,
                    current_input_fingerprint=current_input_fingerprint(job),
                    actor_ref=actor_ref,
                    correlation_id=correlation_id,
                    recorded_at=recorded_at,
                )
            )
        return tuple(findings)

    async def _mark_corrupt(
        self,
        *,
        job: GenerationJob,
        identity: ArtifactIdentity,
        attempt: int,
        paths: ArtifactPaths,
        data: bytes,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> GenerationJob:
        event = self._event(identity=identity, job=job, attempt=attempt, kind=ArtifactEventKind.INTEGRITY_FAILED, recorded_at=recorded_at, actor_ref=actor_ref, reason=reason, correlation_id=correlation_id, evidence_refs=evidence_refs, paths=paths, content_sha256=_sha256_bytes(data), byte_count=len(data))
        await self._append_or_verify(event)
        result = await self.jobs.transition(job_id=job.generation_job_id, axis=GenerationJobAxis.ARTIFACT, command="INTEGRITY_FAILED", owner=TransitionOwner.ARTIFACT_RECONCILER, guard_evidence=self._guard("artifact integrity failed", evidence_refs, hash_valid=False), expected_revision=job.revision, actor_ref=actor_ref, reason=reason, correlation_id=correlation_id, recorded_at=recorded_at)
        return result.job

    async def _ensure_identity(self, job: GenerationJob, actor_ref: str, reason: str, correlation_id: str, recorded_at: datetime) -> ArtifactIdentity:
        existing = await self.evidence.get_identity_for_job(job.generation_job_id)
        if existing is not None:
            return existing
        identity = ArtifactIdentity(artifact_id=artifact_logical_id(job.generation_job_id), generation_job_id=job.generation_job_id, storage_key=artifact_storage_key(job.generation_job_id), actor_ref=actor_ref, reason=reason, correlation_id=correlation_id, created_at=recorded_at)
        return await self.evidence.ensure_identity(identity)

    async def _require_identity(self, job_id: LogicalId) -> ArtifactIdentity:
        identity = await self.evidence.get_identity_for_job(job_id)
        if identity is None:
            raise ArtifactLifecycleBlocked("artifact identity does not exist")
        return identity

    async def _require_begin(self, identity: ArtifactIdentity, attempt: int) -> ArtifactEvent:
        for kind in (ArtifactEventKind.BEGIN_MATERIALIZE, ArtifactEventKind.RECOVER_BYTES):
            event = await self.evidence.get_event(identity.artifact_id, attempt, kind)
            if event is not None:
                return event
        raise ArtifactLifecycleBlocked("materialization attempt has no begin/recovery evidence")

    async def _require_job(self, job_id: LogicalId) -> GenerationJob:
        job = await self.jobs.get_job(job_id)
        if job is None:
            raise ArtifactLifecycleBlocked("GenerationJob does not exist")
        return job

    async def _append_or_verify(self, event: ArtifactEvent) -> ArtifactEvent:
        # ArtifactEvidenceRepository owns replay semantics: the materialization fact
        # must match, while a retry/reconcile audit envelope may legitimately differ
        # after a crash between durable evidence and the GenerationJob transition.
        return await self.evidence.append_event(event)

    async def _best_path_event(self, artifact_id: LogicalId) -> ArtifactEvent | None:
        identity_rows = await self.evidence.reader.fetchall(
            "SELECT generation_job_id FROM studio_generation_artifact_identity WHERE artifact_id=?",
            (artifact_id.root,),
        )
        if not identity_rows:
            return None
        events = await self.evidence.list_events_for_job(LogicalId(str(identity_rows[0]["generation_job_id"])))
        candidates = [item for item in events if item.final_relative_path]
        return max(candidates, key=lambda item: (item.attempt, item.created_at)) if candidates else None

    def _event(
        self,
        *,
        identity: ArtifactIdentity,
        job: GenerationJob,
        attempt: int,
        kind: ArtifactEventKind,
        recorded_at: datetime,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        evidence_refs: tuple[str, ...],
        paths: ArtifactPaths | None = None,
        observed_input_fingerprint: str | None = None,
        content_sha256: str | None = None,
        byte_count: int | None = None,
        media_type: str | None = None,
    ) -> ArtifactEvent:
        return ArtifactEvent(
            artifact_event_id=derive_artifact_event_id(identity.artifact_id, attempt, kind),
            artifact_id=identity.artifact_id,
            generation_job_id=job.generation_job_id,
            attempt=attempt,
            event_kind=kind,
            job_revision_observed=job.revision,
            expected_input_fingerprint=job.expected_input_fingerprint,
            observed_input_fingerprint=observed_input_fingerprint,
            staging_relative_path=None if paths is None else paths.staging_relative_path,
            final_relative_path=None if paths is None else paths.final_relative_path,
            content_sha256=content_sha256,
            byte_count=byte_count,
            media_type=media_type,
            evidence_refs=evidence_refs,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            created_at=recorded_at,
        )

    @staticmethod
    def _guard(summary: str, evidence_refs: Iterable[str], **facts: bool) -> TransitionGuardEvidence:
        return TransitionGuardEvidence(
            summary=summary,
            evidence_refs=tuple(evidence_refs),
            facts=tuple(GuardFact(key=key, value=value) for key, value in facts.items()),
        )

    @staticmethod
    def _attempt_from_path(path: Path) -> int:
        match = re.match(r"attempt-(\d+)\.", path.name)
        return 1 if match is None else max(1, int(match.group(1)))


__all__ = [
    "ArtifactEvidenceRepository",
    "ArtifactEvent",
    "ArtifactEventKind",
    "ArtifactIdentity",
    "ArtifactIdentityConflict",
    "ArtifactIntegrityError",
    "ArtifactLifecycleBlocked",
    "ArtifactLifecycleError",
    "ArtifactLifecycleService",
    "ArtifactPaths",
    "ReconcileClassification",
    "ReconcileFinding",
    "artifact_logical_id",
    "artifact_storage_key",
    "derive_artifact_event_id",
]
