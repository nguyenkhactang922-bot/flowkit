"""Provider-neutral canonical contract primitives for Studio domains.

These value objects implement the frozen Master rules shared by later domains:
stable logical identity, immutable semantic versions, exact source-version
bindings, explicit provenance, lifecycle/gate/finding values, and immutable
semantic-record metadata.

This module must remain free of provider/runtime transport fields.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)

_OPAQUE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+-]{0,127}$")
_ROLE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._:/-]{0,63}$")
_SHA256_RE = r"^sha256:[0-9a-f]{64}$"


def _validate_opaque_token(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain leading/trailing whitespace")
    if not _OPAQUE_TOKEN_RE.fullmatch(value):
        raise ValueError(
            f"{label} must be 1-128 characters using only letters, digits, "
            "'.', '_', ':', '/', '+', or '-'"
        )
    return value


class LogicalId(RootModel[str]):
    """Stable logical identity owned by a canonical domain."""

    model_config = ConfigDict(frozen=True)

    @field_validator("root")
    @classmethod
    def validate_root(cls, value: str) -> str:
        return _validate_opaque_token(value, "logical ID")

    def __str__(self) -> str:
        return self.root


class VersionId(RootModel[str]):
    """Immutable semantic version identity for one canonical logical object."""

    model_config = ConfigDict(frozen=True)

    @field_validator("root")
    @classmethod
    def validate_root(cls, value: str) -> str:
        return _validate_opaque_token(value, "version ID")

    def __str__(self) -> str:
        return self.root


class VersionRef(BaseModel):
    """Exact logical-ID/version pair."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    logical_id: LogicalId
    version_id: VersionId


class SourceVersionBinding(BaseModel):
    """Named dependency binding to an exact canonical source version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: str
    source: VersionRef

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if not isinstance(value, str) or not _ROLE_RE.fullmatch(value):
            raise ValueError(
                "source role must be 1-64 characters, start with a letter, "
                "and contain only letters, digits, '.', '_', ':', '/', or '-'"
            )
        return value


class LifecycleState(str, Enum):
    """Generic creative-artifact lifecycle; stricter local contracts may override."""

    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    LOCKED = "LOCKED"
    SUPERSEDED = "SUPERSEDED"
    INVALIDATED = "INVALIDATED"


class GateVerdict(str, Enum):
    """Provider-neutral QA/gate verdict values used by canonical result contracts."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


class FindingSeverity(str, Enum):
    """Explicit finding severity; blocking disposition remains policy-bound."""

    BLOCKER = "BLOCKER"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    NOTE = "NOTE"


class Provenance(BaseModel):
    """Immutable provenance for a canonical semantic version/evidence record."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_versions: tuple[SourceVersionBinding, ...] = ()
    source_refs: tuple[str, ...] = ()
    actor_ref: str
    reason: str
    recorded_at: AwareDatetime
    rule_version: VersionRef | None = None
    correlation_id: str | None = None

    @field_validator("actor_ref", "reason")
    @classmethod
    def validate_nonblank(cls, value: str, info) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{info.field_name} must be non-empty")
        if value != value.strip():
            raise ValueError(f"{info.field_name} must not contain leading/trailing whitespace")
        return value

    @field_validator("source_refs")
    @classmethod
    def validate_source_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized: list[str] = []
        for value in values:
            if not isinstance(value, str) or not value.strip():
                raise ValueError("source_refs entries must be non-empty strings")
            if value != value.strip():
                raise ValueError("source_refs entries must not contain surrounding whitespace")
            normalized.append(value)
        if len(set(normalized)) != len(normalized):
            raise ValueError("source_refs must not contain duplicates")
        return tuple(normalized)

    @field_validator("correlation_id")
    @classmethod
    def validate_correlation_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_opaque_token(value, "correlation ID")

    @model_validator(mode="after")
    def validate_sources(self) -> "Provenance":
        if not self.source_versions and not self.source_refs:
            raise ValueError(
                "provenance requires at least one exact source-version binding "
                "or source reference"
            )

        keys = [
            (binding.role, binding.source.logical_id.root, binding.source.version_id.root)
            for binding in self.source_versions
        ]
        if len(set(keys)) != len(keys):
            raise ValueError("source_versions must not contain duplicate bindings")
        return self


class SemanticRecordMetadata(BaseModel):
    """Immutable metadata shared by canonical semantic version records."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    logical_id: LogicalId
    version_id: VersionId
    provenance: Provenance
    created_at: AwareDatetime
    predecessor: VersionRef | None = None
    content_hash: str | None = Field(default=None, pattern=_SHA256_RE)

    @model_validator(mode="after")
    def validate_predecessor(self) -> "SemanticRecordMetadata":
        if self.predecessor is None:
            return self
        if self.predecessor.logical_id != self.logical_id:
            raise ValueError("predecessor must reference the same logical ID")
        if self.predecessor.version_id == self.version_id:
            raise ValueError("predecessor version must differ from current version")
        return self
