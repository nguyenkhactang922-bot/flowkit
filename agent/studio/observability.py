"""Provider-neutral observability, error, and evidence contracts.

The frozen Studio authority is explicit:
- events/logs are audit evidence, never current-state truth;
- errors are typed and retain provider ambiguity / QA distinctions;
- secrets are never embedded in persisted evidence;
- correlation and exact-version provenance travel with evidence.

This module therefore provides immutable evidence contracts plus an append-only
repository. It deliberately exposes no current-pointer or domain-truth mutation.
"""

from __future__ import annotations

import contextvars
import json
import re
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterator, Literal

import aiosqlite
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)

from .persistence import PersistenceError, SQLiteReadRepository, SQLiteWriteOwner
from .primitives import LogicalId, Provenance, SourceVersionBinding, VersionRef


_REDACTED = "[REDACTED]"
_SENSITIVE_KEYS = {
    "authorization",
    "proxy_authorization",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "id_token",
    "token",
    "password",
    "passwd",
    "secret",
    "client_secret",
    "cookie",
    "set_cookie",
    "credential",
    "credentials",
    "session",
    "session_id",
}
_KEY_NORMALIZER = re.compile(r"[^a-z0-9]+")
_BEARER_RE = re.compile(
    r"(?i)\bBearer\s+[A-Za-z0-9._~+\-/=]{6,}"
)
_INLINE_SECRET_RE = re.compile(
    r"(?i)\b("
    r"authorization|proxy[-_ ]?authorization|api[-_ ]?key|apikey|"
    r"access[-_ ]?token|refresh[-_ ]?token|id[-_ ]?token|token|"
    r"password|passwd|client[-_ ]?secret|secret|cookie|"
    r"credential|credentials|session[-_ ]?id"
    r")(\s*[:=]\s*)([^\s,;]+)"
)
_SHA256_RE = r"^sha256:[0-9a-f]{64}$"

_current_correlation: contextvars.ContextVar["CorrelationId | None"] = (
    contextvars.ContextVar("studio_correlation_id", default=None)
)


class ObservabilityError(PersistenceError):
    """Base error for evidence/observability persistence."""


class EvidenceEventConflict(ObservabilityError):
    """Raised when an event identity collides with different immutable evidence."""


class CorrelationId(RootModel[str]):
    """Opaque request/run/decision correlation identity."""

    model_config = ConfigDict(frozen=True)

    @field_validator("root")
    @classmethod
    def validate_root(cls, value: str) -> str:
        return LogicalId(value).root

    def __str__(self) -> str:
        return self.root


class EvidenceEventKind(str, Enum):
    DECISION = "DECISION"
    FAILURE = "FAILURE"


class ErrorClass(str, Enum):
    """Exact error classes from frozen Master section 87."""

    VALIDATION = "validation"
    INVARIANT = "invariant"
    DEPENDENCY = "dependency"
    SECURITY = "security"
    PERSISTENCE = "persistence"
    PROVIDER_TRANSPORT = "provider transport"
    PROVIDER_AMBIGUITY = "provider ambiguity"
    ARTIFACT_INTEGRITY = "artifact integrity"
    QA = "QA"
    REPAIR = "repair"
    MIGRATION = "migration"
    CANCELLATION = "cancellation"


class RetryDisposition(str, Enum):
    """Typed retryability without collapsing provider ambiguity."""

    RETRYABLE = "RETRYABLE"
    NOT_RETRYABLE = "NOT_RETRYABLE"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class EvidenceReference(BaseModel):
    """Reference to evidence used to support a specific claim."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_id: str
    evidence_class: str
    locator: str | None = None
    content_hash: str | None = Field(default=None, pattern=_SHA256_RE)
    claim_scope: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("evidence_id")
    @classmethod
    def validate_evidence_id(cls, value: str) -> str:
        return LogicalId(value).root

    @field_validator("evidence_class")
    @classmethod
    def validate_evidence_class(cls, value: str) -> str:
        return _require_trimmed(value, "evidence_class")

    @field_validator("locator", "claim_scope", mode="before")
    @classmethod
    def redact_optional_text(cls, value: Any) -> Any:
        if value is None:
            return None
        return redact_text(_require_trimmed(str(value), "evidence text"))

    @field_validator("metadata", mode="before")
    @classmethod
    def redact_metadata(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("evidence metadata must be an object")
        return redact_secrets(value)


class StudioErrorRecord(BaseModel):
    """Immutable typed error evidence; not domain/current-state truth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    error_id: str
    error_code: str
    error_class: ErrorClass
    retryability: RetryDisposition
    responsible_boundary: str
    evidence: tuple[EvidenceReference, ...] = ()
    user_safe_message: str
    correlation_id: CorrelationId
    source_versions: tuple[SourceVersionBinding, ...] = ()
    provenance: Provenance
    occurred_at: AwareDatetime
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("error_id")
    @classmethod
    def validate_error_id(cls, value: str) -> str:
        return LogicalId(value).root

    @field_validator("error_code")
    @classmethod
    def validate_error_code(cls, value: str) -> str:
        value = _require_trimmed(value, "error_code")
        if value.upper() == "FAILED":
            raise ValueError('generic error code "FAILED" is not allowed')
        return value

    @field_validator("responsible_boundary")
    @classmethod
    def validate_boundary(cls, value: str) -> str:
        return _require_trimmed(value, "responsible_boundary")

    @field_validator("user_safe_message", mode="before")
    @classmethod
    def redact_user_message(cls, value: Any) -> str:
        return redact_text(_require_trimmed(str(value), "user_safe_message"))

    @field_validator("details", mode="before")
    @classmethod
    def redact_details(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("error details must be an object")
        return redact_secrets(value)

    @field_validator("provenance", mode="before")
    @classmethod
    def redact_provenance(cls, value: Any) -> Provenance:
        return _redacted_provenance(value)

    @model_validator(mode="after")
    def validate_semantics(self) -> "StudioErrorRecord":
        if (
            self.error_class is ErrorClass.PROVIDER_AMBIGUITY
            and self.retryability is not RetryDisposition.RECONCILIATION_REQUIRED
        ):
            raise ValueError(
                "provider ambiguity must require reconciliation before retry"
            )
        if (
            self.provenance.correlation_id is not None
            and self.provenance.correlation_id != self.correlation_id.root
        ):
            raise ValueError(
                "error provenance correlation_id must match error correlation_id"
            )
        return self


class EvidenceEvent(BaseModel):
    """Append-only structured decision/failure evidence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str
    event_kind: EvidenceEventKind
    correlation_id: CorrelationId
    responsible_boundary: str
    occurred_at: AwareDatetime
    source_versions: tuple[SourceVersionBinding, ...] = ()
    input_refs: tuple[VersionRef, ...] = ()
    output_refs: tuple[VersionRef, ...] = ()
    evidence_refs: tuple[EvidenceReference, ...] = ()
    provenance: Provenance
    decision_code: str | None = None
    reason: str
    error: StudioErrorRecord | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    authority_scope: Literal["EVIDENCE_ONLY"] = "EVIDENCE_ONLY"

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, value: str) -> str:
        return LogicalId(value).root

    @field_validator("responsible_boundary")
    @classmethod
    def validate_boundary(cls, value: str) -> str:
        return _require_trimmed(value, "responsible_boundary")

    @field_validator("decision_code")
    @classmethod
    def validate_decision_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _require_trimmed(value, "decision_code")

    @field_validator("reason", mode="before")
    @classmethod
    def redact_reason(cls, value: Any) -> str:
        return redact_text(_require_trimmed(str(value), "reason"))

    @field_validator("attributes", mode="before")
    @classmethod
    def redact_attributes(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("event attributes must be an object")
        return redact_secrets(value)

    @field_validator("provenance", mode="before")
    @classmethod
    def redact_provenance(cls, value: Any) -> Provenance:
        return _redacted_provenance(value)

    @model_validator(mode="after")
    def validate_event_contract(self) -> "EvidenceEvent":
        if self.event_kind is EvidenceEventKind.DECISION:
            if self.decision_code is None:
                raise ValueError("decision event requires decision_code")
            if self.error is not None:
                raise ValueError("decision event cannot carry error evidence")
        else:
            if self.error is None:
                raise ValueError("failure event requires typed error evidence")
            if self.decision_code is not None:
                raise ValueError("failure event cannot carry decision_code")
            if self.error.correlation_id != self.correlation_id:
                raise ValueError(
                    "failure error correlation_id must match event correlation_id"
                )

        if (
            self.provenance.correlation_id is not None
            and self.provenance.correlation_id != self.correlation_id.root
        ):
            raise ValueError(
                "event provenance correlation_id must match event correlation_id"
            )
        return self


def _require_trimmed(value: str, label: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"{label} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _normalized_key(value: str) -> str:
    return _KEY_NORMALIZER.sub("_", value.strip().lower()).strip("_")


def _is_sensitive_key(value: str) -> bool:
    normalized = _normalized_key(value)
    return normalized in _SENSITIVE_KEYS


def redact_text(value: str) -> str:
    """Redact inline credential-like material deterministically."""

    redacted = _BEARER_RE.sub("Bearer " + _REDACTED, value)

    def replace_match(match: re.Match[str]) -> str:
        return f"{match.group(1)}{match.group(2)}{_REDACTED}"

    return _INLINE_SECRET_RE.sub(replace_match, redacted)


def redact_secrets(value: Any) -> Any:
    """Recursively redact common secret-bearing keys and inline credentials."""

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            result[key_text] = (
                _REDACTED
                if _is_sensitive_key(key_text)
                else redact_secrets(item)
            )
        return result
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item) for item in value)
    if isinstance(value, str):
        return redact_text(value)
    return value


def _redacted_provenance(value: Any) -> Provenance:
    payload = (
        value.model_dump(mode="json")
        if isinstance(value, Provenance)
        else value
    )
    if not isinstance(payload, dict):
        raise ValueError("provenance must be a Provenance object")
    return Provenance.model_validate(redact_secrets(payload))


def new_correlation_id() -> CorrelationId:
    return CorrelationId("corr:" + uuid.uuid4().hex)


def new_event_id() -> str:
    return "event:" + uuid.uuid4().hex


def new_error_id() -> str:
    return "error:" + uuid.uuid4().hex


@contextmanager
def correlation_scope(
    correlation_id: CorrelationId | str | None = None,
) -> Iterator[CorrelationId]:
    """Bind a correlation ID across sync/async call boundaries."""

    bound = (
        new_correlation_id()
        if correlation_id is None
        else (
            correlation_id
            if isinstance(correlation_id, CorrelationId)
            else CorrelationId(correlation_id)
        )
    )
    token = _current_correlation.set(bound)
    try:
        yield bound
    finally:
        _current_correlation.reset(token)


def current_correlation_id(*, required: bool = False) -> CorrelationId | None:
    value = _current_correlation.get()
    if required and value is None:
        raise RuntimeError("no Studio correlation ID is bound")
    return value


class EvidenceEventRepository:
    """Append-only evidence store; deliberately not a current-state authority."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.reader = SQLiteReadRepository(writer.db_path)

    async def append(self, event: EvidenceEvent) -> EvidenceEvent:
        payload_json = event.model_dump_json()
        provenance_json = event.provenance.model_dump_json()

        async def command(tx):
            existing = await tx.fetchone(
                "SELECT payload_json FROM studio_evidence_event WHERE event_id=?",
                (event.event_id,),
            )
            if existing is not None:
                if existing["payload_json"] == payload_json:
                    return event
                raise EvidenceEventConflict(
                    f"event identity already exists with different evidence: "
                    f"{event.event_id}"
                )

            await tx.execute(
                """
                INSERT INTO studio_evidence_event (
                    event_id,
                    correlation_id,
                    event_kind,
                    responsible_boundary,
                    occurred_at,
                    authority_scope,
                    payload_json,
                    provenance_json
                ) VALUES (?, ?, ?, ?, ?, 'EVIDENCE_ONLY', ?, ?)
                """,
                (
                    event.event_id,
                    event.correlation_id.root,
                    event.event_kind.value,
                    event.responsible_boundary,
                    event.occurred_at.isoformat(),
                    payload_json,
                    provenance_json,
                ),
            )
            return event

        try:
            return await self.writer.execute(command)
        except aiosqlite.IntegrityError as exc:
            raise ObservabilityError(
                f"failed to append evidence event {event.event_id}"
            ) from exc

    async def get(self, event_id: str) -> EvidenceEvent | None:
        event_id = LogicalId(event_id).root
        row = await self.reader.fetchone(
            "SELECT payload_json FROM studio_evidence_event WHERE event_id=?",
            (event_id,),
        )
        if row is None:
            return None
        return EvidenceEvent.model_validate_json(row["payload_json"])

    async def list_by_correlation(
        self,
        correlation_id: CorrelationId | str,
    ) -> list[EvidenceEvent]:
        correlation = (
            correlation_id
            if isinstance(correlation_id, CorrelationId)
            else CorrelationId(correlation_id)
        )
        rows = await self.reader.fetchall(
            """
            SELECT payload_json
            FROM studio_evidence_event
            WHERE correlation_id=?
            ORDER BY occurred_at, event_id
            """,
            (correlation.root,),
        )
        return [
            EvidenceEvent.model_validate_json(row["payload_json"])
            for row in rows
        ]


def utc_now() -> datetime:
    """Public helper for evidence timestamps."""

    return datetime.now(timezone.utc)
