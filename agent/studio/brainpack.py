"""Canonical BrainPack Registry.

The registry owns reusable, immutable, versioned pack definitions only.
It does not own project-specific selection, composition, precedence, conflict
resolution, overrides, or ActiveProductionProfile state.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

import aiosqlite
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from .persistence import CASConflict, PersistenceError, SQLiteReadRepository, SQLiteWriteOwner
from .primitives import LogicalId, Provenance, VersionId


class BrainPackRegistryError(PersistenceError):
    """Base error for BrainPack Registry operations."""


class BrainPackNotFound(BrainPackRegistryError):
    """Raised when an exact pack version is missing."""


class BrainPackConflict(BrainPackRegistryError):
    """Raised when an immutable pack identity collides with different truth."""


class BrainPackInheritanceCycle(BrainPackRegistryError):
    """Raised when exact parent inheritance creates a logical pack cycle."""


class BrainPackLifecycleError(BrainPackRegistryError):
    """Raised for illegal registry lifecycle transitions."""


class BrainPackFamily(str, Enum):
    KNOWLEDGE = "KNOWLEDGE"
    CREATIVE = "CREATIVE"
    STORY = "STORY"
    PRODUCTION_STYLE = "PRODUCTION_STYLE"
    AUDIENCE = "AUDIENCE"
    FORMAT = "FORMAT"
    PLATFORM = "PLATFORM"
    QA_RUBRIC = "QA_RUBRIC"
    OTHER = "OTHER"


class BrainPackLifecycleState(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    FROZEN = "FROZEN"
    DEPRECATED = "DEPRECATED"


class BrainPackRuleStrength(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"


class BrainPackSourceKind(str, Enum):
    INTERNAL = "INTERNAL"
    DONOR = "DONOR"
    EXTERNAL = "EXTERNAL"


_FORBIDDEN_POLICY_KEYS = {
    "provider",
    "provider_id",
    "provider_name",
    "model",
    "model_id",
    "model_key",
    "remote_job_id",
    "request_id",
    "flow_project_id",
    "google_project_id",
}


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _unique_trimmed(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        item = _trimmed(value, label)
        if item not in result:
            result.append(item)
    return tuple(result)


def _assert_provider_neutral(value: Any, path: str = "rule.value") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} mapping keys must be strings")
            if key.casefold() in _FORBIDDEN_POLICY_KEYS:
                raise ValueError(f"{path} contains provider/runtime field {key!r}")
            _assert_provider_neutral(nested, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _assert_provider_neutral(nested, f"{path}[{index}]")


def _canonical_json(value: dict[str, Any]) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("BrainPack definition must be canonical JSON data") from exc


def _content_hash(payload_json: str) -> str:
    return "sha256:" + hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class BrainPackRef(BaseModel):
    """Exact BrainPack identity/version reference."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pack_id: LogicalId
    pack_version: VersionId


class BrainPackApplicability(BaseModel):
    """Typed applicability metadata; empty dimensions mean no restriction."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    topic_labels: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()
    niches: tuple[str, ...] = ()
    genres: tuple[str, ...] = ()
    audiences: tuple[str, ...] = ()
    formats: tuple[str, ...] = ()
    platforms: tuple[str, ...] = ()
    factuality_modes: tuple[str, ...] = ()

    @field_validator(
        "topic_labels",
        "domains",
        "niches",
        "genres",
        "audiences",
        "formats",
        "platforms",
        "factuality_modes",
    )
    @classmethod
    def validate_values(cls, values: tuple[str, ...], info) -> tuple[str, ...]:
        return _unique_trimmed(values, info.field_name)


class BrainPackRule(BaseModel):
    """Reusable provider-neutral policy/knowledge rule definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    value: Any
    strength: BrainPackRuleStrength = BrainPackRuleStrength.SOFT
    override_allowed: bool = True
    reason: str

    @field_validator("key", "reason")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: Any) -> Any:
        _assert_provider_neutral(value)
        _canonical_json({"value": value})
        return value


class BrainPackSourceEvidence(BaseModel):
    """Source + license evidence required before registry authority is accepted."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_kind: BrainPackSourceKind
    source_ref: str
    license_expression: str
    license_evidence_ref: str
    validated: bool = True
    adaptation_note: str | None = None

    @field_validator("source_ref", "license_expression", "license_evidence_ref")
    @classmethod
    def validate_required_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("adaptation_note")
    @classmethod
    def validate_adaptation_note(cls, value: str | None) -> str | None:
        return None if value is None else _trimmed(value, "adaptation_note")

    @model_validator(mode="after")
    def validate_donor_authority(self) -> "BrainPackSourceEvidence":
        if self.source_kind is BrainPackSourceKind.DONOR:
            if not self.validated:
                raise ValueError("donor source must be validated before registry authority")
            if self.adaptation_note is None:
                raise ValueError("donor source requires explicit adaptation_note")
        return self


class BrainPackDefinition(BaseModel):
    """Immutable reusable BrainPack definition in the one canonical registry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pack_id: LogicalId
    pack_version: VersionId
    family: BrainPackFamily
    custom_family_key: str | None = None
    name: str
    description: str
    parents: tuple[BrainPackRef, ...] = ()
    applicability: BrainPackApplicability = BrainPackApplicability()
    rules: tuple[BrainPackRule, ...]
    source_evidence: tuple[BrainPackSourceEvidence, ...]
    provenance: Provenance
    created_at: AwareDatetime
    predecessor: BrainPackRef | None = None

    @field_validator("name", "description")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("custom_family_key")
    @classmethod
    def validate_custom_family(cls, value: str | None) -> str | None:
        return None if value is None else _trimmed(value, "custom_family_key")

    @model_validator(mode="after")
    def validate_definition(self) -> "BrainPackDefinition":
        if self.family is BrainPackFamily.OTHER and self.custom_family_key is None:
            raise ValueError("OTHER pack family requires custom_family_key")
        if self.family is not BrainPackFamily.OTHER and self.custom_family_key is not None:
            raise ValueError("custom_family_key is only valid for OTHER family")
        if type(self) is BrainPackDefinition and self.family is BrainPackFamily.STORY:
            raise ValueError(
                "Story family must use StoryBrainPackDefinition specialization"
            )
        if not self.rules:
            raise ValueError("BrainPack requires at least one reusable rule")
        rule_keys = [rule.key.casefold() for rule in self.rules]
        if len(set(rule_keys)) != len(rule_keys):
            raise ValueError("BrainPack rule keys must be unique")
        if not self.source_evidence:
            raise ValueError("BrainPack requires source/license evidence")
        parent_keys = [
            (parent.pack_id.root, parent.pack_version.root) for parent in self.parents
        ]
        if len(set(parent_keys)) != len(parent_keys):
            raise ValueError("BrainPack parent refs must be unique")
        if any(parent.pack_id == self.pack_id for parent in self.parents):
            raise ValueError("BrainPack cannot directly inherit from its own logical ID")
        if self.predecessor is not None:
            if self.predecessor.pack_id != self.pack_id:
                raise ValueError("BrainPack predecessor must share pack_id")
            if self.predecessor.pack_version == self.pack_version:
                raise ValueError("BrainPack predecessor version must differ")
        provenance_refs = set(self.provenance.source_refs)
        required_refs = {
            ref
            for evidence in self.source_evidence
            for ref in (evidence.source_ref, evidence.license_evidence_ref)
        }
        missing = sorted(required_refs - provenance_refs)
        if missing:
            raise ValueError(
                "BrainPack provenance must include source/license evidence refs: "
                + ", ".join(missing)
            )
        return self

    @property
    def ref(self) -> BrainPackRef:
        return BrainPackRef(pack_id=self.pack_id, pack_version=self.pack_version)


class StoryBrainPackDefinition(BrainPackDefinition):
    """StoryBrainPack specialization stored in the same canonical registry."""

    family: Literal[BrainPackFamily.STORY] = BrainPackFamily.STORY
    story_dimensions: tuple[str, ...]

    @field_validator("story_dimensions")
    @classmethod
    def validate_story_dimensions(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        result = _unique_trimmed(values, "story dimension")
        if not result:
            raise ValueError("StoryBrainPack requires at least one story dimension")
        return result


class BrainPackLifecycle(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ref: BrainPackRef
    state: BrainPackLifecycleState
    revision: int = Field(ge=0)
    updated_at: AwareDatetime


class BrainPackLifecycleTransition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    transition_id: str
    ref: BrainPackRef
    from_state: BrainPackLifecycleState
    to_state: BrainPackLifecycleState
    from_revision: int = Field(ge=0)
    to_revision: int = Field(ge=1)
    reason: str
    provenance: Provenance
    created_at: AwareDatetime


_ALLOWED_TRANSITIONS = {
    BrainPackLifecycleState.DRAFT: {
        BrainPackLifecycleState.VALIDATED,
        BrainPackLifecycleState.DEPRECATED,
    },
    BrainPackLifecycleState.VALIDATED: {
        BrainPackLifecycleState.FROZEN,
        BrainPackLifecycleState.DEPRECATED,
    },
    BrainPackLifecycleState.FROZEN: {
        BrainPackLifecycleState.DEPRECATED,
    },
    BrainPackLifecycleState.DEPRECATED: set(),
}


class BrainPackRegistryRepository:
    """The single canonical registry for all BrainPack families."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.reader = SQLiteReadRepository(writer.db_path)

    async def create(self, definition: BrainPackDefinition) -> BrainPackDefinition:
        await self._validate_predecessor(definition)
        await self._validate_parent_graph(definition)

        payload = definition.model_dump(
            mode="json",
            exclude={"provenance", "created_at"},
        )
        payload_json = _canonical_json(payload)
        content_hash = _content_hash(payload_json)

        async def command(tx):
            existing = await tx.fetchone(
                """
                SELECT payload_json, provenance_json, created_at
                FROM studio_brainpack_definition
                WHERE pack_id=? AND pack_version=?
                """,
                (definition.pack_id.root, definition.pack_version.root),
            )
            if existing is not None:
                stored = self._definition_from_row(existing)
                if stored != definition:
                    raise BrainPackConflict(
                        f"BrainPack identity already exists with different truth: "
                        f"{definition.pack_id.root}/{definition.pack_version.root}"
                    )
                return stored

            await tx.execute(
                """
                INSERT INTO studio_brainpack_definition (
                    pack_id,
                    pack_version,
                    family,
                    payload_json,
                    provenance_json,
                    created_at,
                    predecessor_version,
                    content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    definition.pack_id.root,
                    definition.pack_version.root,
                    definition.family.value,
                    payload_json,
                    definition.provenance.model_dump_json(),
                    definition.created_at.isoformat(),
                    None
                    if definition.predecessor is None
                    else definition.predecessor.pack_version.root,
                    content_hash,
                ),
            )
            for ordinal, parent in enumerate(definition.parents):
                await tx.execute(
                    """
                    INSERT INTO studio_brainpack_parent (
                        pack_id,
                        pack_version,
                        ordinal,
                        parent_pack_id,
                        parent_pack_version
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        definition.pack_id.root,
                        definition.pack_version.root,
                        ordinal,
                        parent.pack_id.root,
                        parent.pack_version.root,
                    ),
                )
            await tx.execute(
                """
                INSERT INTO studio_brainpack_lifecycle (
                    pack_id,
                    pack_version,
                    lifecycle_state,
                    revision,
                    updated_at
                ) VALUES (?, ?, 'DRAFT', 0, ?)
                """,
                (
                    definition.pack_id.root,
                    definition.pack_version.root,
                    _utc_text(_utc_now()),
                ),
            )
            return definition

        try:
            return await self.writer.execute(command)
        except aiosqlite.IntegrityError as exc:
            raise BrainPackRegistryError(
                "BrainPack references missing predecessor/parent truth"
            ) from exc

    async def get(self, ref: BrainPackRef) -> BrainPackDefinition | None:
        row = await self.reader.fetchone(
            """
            SELECT payload_json, provenance_json, created_at
            FROM studio_brainpack_definition
            WHERE pack_id=? AND pack_version=?
            """,
            (ref.pack_id.root, ref.pack_version.root),
        )
        return None if row is None else self._definition_from_row(row)

    async def require(self, ref: BrainPackRef) -> BrainPackDefinition:
        value = await self.get(ref)
        if value is None:
            raise BrainPackNotFound(
                f"BrainPack not found: {ref.pack_id.root}/{ref.pack_version.root}"
            )
        return value

    async def list_definitions(
        self,
        *,
        family: BrainPackFamily | None = None,
    ) -> list[BrainPackDefinition]:
        if family is None:
            rows = await self.reader.fetchall(
                """
                SELECT payload_json, provenance_json, created_at
                FROM studio_brainpack_definition
                ORDER BY pack_id, pack_version
                """
            )
        else:
            rows = await self.reader.fetchall(
                """
                SELECT payload_json, provenance_json, created_at
                FROM studio_brainpack_definition
                WHERE family=?
                ORDER BY pack_id, pack_version
                """,
                (family.value,),
            )
        return [self._definition_from_row(row) for row in rows]

    async def get_lifecycle(self, ref: BrainPackRef) -> BrainPackLifecycle:
        row = await self.reader.fetchone(
            """
            SELECT lifecycle_state, revision, updated_at
            FROM studio_brainpack_lifecycle
            WHERE pack_id=? AND pack_version=?
            """,
            (ref.pack_id.root, ref.pack_version.root),
        )
        if row is None:
            raise BrainPackNotFound(
                f"BrainPack lifecycle not found: {ref.pack_id.root}/{ref.pack_version.root}"
            )
        return BrainPackLifecycle(
            ref=ref,
            state=BrainPackLifecycleState(row["lifecycle_state"]),
            revision=int(row["revision"]),
            updated_at=row["updated_at"],
        )

    async def transition_lifecycle(
        self,
        *,
        ref: BrainPackRef,
        target: BrainPackLifecycleState,
        expected_revision: int,
        reason: str,
        provenance: Provenance,
    ) -> BrainPackLifecycle:
        reason = _trimmed(reason, "lifecycle transition reason")
        current = await self.get_lifecycle(ref)
        if target not in _ALLOWED_TRANSITIONS[current.state]:
            raise BrainPackLifecycleError(
                f"illegal BrainPack lifecycle transition: "
                f"{current.state.value}->{target.value}"
            )

        changed_at = _utc_now()

        async def command(tx):
            row = await tx.fetchone(
                """
                SELECT lifecycle_state, revision
                FROM studio_brainpack_lifecycle
                WHERE pack_id=? AND pack_version=?
                """,
                (ref.pack_id.root, ref.pack_version.root),
            )
            if row is None:
                raise BrainPackNotFound(
                    f"BrainPack lifecycle not found: "
                    f"{ref.pack_id.root}/{ref.pack_version.root}"
                )
            persisted_state = BrainPackLifecycleState(row["lifecycle_state"])
            if target not in _ALLOWED_TRANSITIONS[persisted_state]:
                raise BrainPackLifecycleError(
                    f"illegal BrainPack lifecycle transition: "
                    f"{persisted_state.value}->{target.value}"
                )

            new_revision = await tx.cas_update(
                table="studio_brainpack_lifecycle",
                pk_column="pack_id",
                pk_value=ref.pack_id.root,
                expected_revision=expected_revision,
                changes={
                    "lifecycle_state": target.value,
                    "updated_at": _utc_text(changed_at),
                },
                revision_column="revision",
                extra_where={
                    "pack_version": ref.pack_version.root,
                },
            )
            transition_id = self._transition_id(ref, new_revision)
            await tx.execute(
                """
                INSERT INTO studio_brainpack_lifecycle_transition (
                    transition_id,
                    pack_id,
                    pack_version,
                    from_state,
                    to_state,
                    from_revision,
                    to_revision,
                    reason,
                    provenance_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transition_id,
                    ref.pack_id.root,
                    ref.pack_version.root,
                    persisted_state.value,
                    target.value,
                    expected_revision,
                    new_revision,
                    reason,
                    provenance.model_dump_json(),
                    _utc_text(changed_at),
                ),
            )
            return BrainPackLifecycle(
                ref=ref,
                state=target,
                revision=new_revision,
                updated_at=changed_at,
            )

        try:
            return await self.writer.execute(command)
        except aiosqlite.IntegrityError as exc:
            raise BrainPackLifecycleError(str(exc)) from exc

    async def lifecycle_history(
        self,
        ref: BrainPackRef,
    ) -> list[BrainPackLifecycleTransition]:
        rows = await self.reader.fetchall(
            """
            SELECT *
            FROM studio_brainpack_lifecycle_transition
            WHERE pack_id=? AND pack_version=?
            ORDER BY to_revision
            """,
            (ref.pack_id.root, ref.pack_version.root),
        )
        return [
            BrainPackLifecycleTransition(
                transition_id=row["transition_id"],
                ref=ref,
                from_state=BrainPackLifecycleState(row["from_state"]),
                to_state=BrainPackLifecycleState(row["to_state"]),
                from_revision=int(row["from_revision"]),
                to_revision=int(row["to_revision"]),
                reason=row["reason"],
                provenance=Provenance.model_validate_json(row["provenance_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def _validate_predecessor(self, definition: BrainPackDefinition) -> None:
        if definition.predecessor is None:
            rows = await self.reader.fetchall(
                """
                SELECT 1
                FROM studio_brainpack_definition
                WHERE pack_id=?
                LIMIT 1
                """,
                (definition.pack_id.root,),
            )
            if rows:
                raise BrainPackRegistryError(
                    "non-initial BrainPack version requires exact predecessor"
                )
            return
        await self.require(definition.predecessor)

    async def _validate_parent_graph(self, definition: BrainPackDefinition) -> None:
        target_pack_id = definition.pack_id
        visited: set[tuple[str, str]] = set()

        async def walk(ref: BrainPackRef) -> None:
            key = (ref.pack_id.root, ref.pack_version.root)
            if key in visited:
                return
            visited.add(key)
            if ref.pack_id == target_pack_id:
                raise BrainPackInheritanceCycle(
                    f"BrainPack logical inheritance cycle reaches {target_pack_id.root}"
                )
            parent_definition = await self.require(ref)
            for parent in parent_definition.parents:
                await walk(parent)

        for parent in definition.parents:
            await walk(parent)

    @staticmethod
    def _definition_from_row(row) -> BrainPackDefinition:
        payload = json.loads(row["payload_json"])
        payload["provenance"] = json.loads(row["provenance_json"])
        payload["created_at"] = row["created_at"]
        family = BrainPackFamily(payload["family"])
        model = (
            StoryBrainPackDefinition
            if family is BrainPackFamily.STORY
            else BrainPackDefinition
        )
        return model.model_validate(payload)

    @staticmethod
    def _transition_id(ref: BrainPackRef, revision: int) -> str:
        raw = (
            f"{ref.pack_id.root}\0{ref.pack_version.root}\0{revision}"
        ).encode("utf-8")
        return "brainpack-transition:" + hashlib.sha256(raw).hexdigest()
