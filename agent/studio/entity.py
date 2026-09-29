"""Canonical EntityVersion adapter over legacy FlowKit character/entity records.

IMP-040 keeps the useful legacy entity identity/project linkage while moving
canonical semantic truth into the shared immutable VersionRepository. Legacy
reference media and prompt fields remain compatibility data and never become
canonical Entity identity truth.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from .primitives import (
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    VersionId,
    VersionRef,
)
from .versioning import CurrentVersionPointer, StoredSemanticVersion, VersionRepository


class EntityContractError(ValueError):
    """Base error for canonical EntityVersion contract violations."""


class EntityIdentityError(EntityContractError):
    """Raised when legacy/canonical identity or successor lineage is invalid."""


class EntityKind(str, Enum):
    """Canonical entity kinds supported by the current FlowKit compatibility surface."""

    CHARACTER = "character"
    LOCATION = "location"
    CREATURE = "creature"
    VISUAL_ASSET = "visual_asset"
    GENERIC_TROOP = "generic_troop"
    FACTION = "faction"


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _optional_trimmed(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    return _trimmed(value, label)


def _unique_projects(values: tuple[LogicalId, ...]) -> tuple[LogicalId, ...]:
    seen: set[str] = set()
    result: list[LogicalId] = []
    for value in values:
        if value.root not in seen:
            seen.add(value.root)
            result.append(value)
    return tuple(result)


def entity_logical_id(legacy_entity_id: str) -> LogicalId:
    """Map one legacy entity ID to one stable canonical logical identity."""

    legacy = _trimmed(legacy_entity_id, "legacy entity ID")
    return LogicalId(f"entity:{legacy}")


class LegacyEntitySnapshot(BaseModel):
    """Read-only compatibility snapshot of the current FlowKit character row.

    Media/prompt fields are deliberately retained only here so existing FlowKit
    execution can keep using them while the canonical EntityVersion excludes
    them from semantic identity truth.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    entity_type: EntityKind = EntityKind.CHARACTER
    project_ids: tuple[LogicalId, ...] = ()
    slug: str | None = None
    description: str | None = None
    voice_description: str | None = None
    image_prompt: str | None = None
    reference_image_url: str | None = None
    media_id: str | None = None
    updated_at: str | None = None

    @field_validator("id", "name")
    @classmethod
    def validate_required_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator(
        "slug",
        "description",
        "voice_description",
        "image_prompt",
        "reference_image_url",
        "media_id",
        "updated_at",
    )
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return _optional_trimmed(value, info.field_name)

    @field_validator("project_ids")
    @classmethod
    def normalize_projects(cls, values: tuple[LogicalId, ...]) -> tuple[LogicalId, ...]:
        return _unique_projects(values)

    @classmethod
    def from_legacy(
        cls,
        row: Mapping[str, Any] | Any,
        *,
        project_ids: tuple[LogicalId, ...] = (),
    ) -> "LegacyEntitySnapshot":
        """Build from a legacy dict/Pydantic/dataclass-like entity object."""

        def read(name: str, default: Any = None) -> Any:
            if isinstance(row, Mapping):
                return row.get(name, default)
            return getattr(row, name, default)

        return cls(
            id=read("id"),
            name=read("name"),
            entity_type=read("entity_type", EntityKind.CHARACTER.value),
            project_ids=project_ids,
            slug=read("slug"),
            description=read("description"),
            voice_description=read("voice_description"),
            image_prompt=read("image_prompt"),
            reference_image_url=read("reference_image_url"),
            media_id=read("media_id"),
            updated_at=read("updated_at"),
        )


class EntityVersion(BaseModel):
    """One immutable canonical semantic realization of an entity identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_id: LogicalId
    version_id: VersionId
    kind: EntityKind
    name: str
    project_ids: tuple[LogicalId, ...] = ()
    slug: str | None = None
    description: str | None = None
    voice_description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _trimmed(value, "name")

    @field_validator("slug", "description", "voice_description")
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return _optional_trimmed(value, info.field_name)

    @field_validator("project_ids")
    @classmethod
    def normalize_projects(cls, values: tuple[LogicalId, ...]) -> tuple[LogicalId, ...]:
        return _unique_projects(values)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.entity_id, version_id=self.version_id)


class LegacyEntityBinding(BaseModel):
    """Compatibility mapping; never a second canonical Entity truth store."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    legacy_entity_id: str
    canonical_ref: VersionRef
    project_ids: tuple[LogicalId, ...] = ()
    legacy_media_id: str | None = None
    legacy_reference_image_url: str | None = None

    @field_validator("legacy_entity_id")
    @classmethod
    def validate_legacy_id(cls, value: str) -> str:
        return _trimmed(value, "legacy_entity_id")

    @field_validator("legacy_media_id", "legacy_reference_image_url")
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return _optional_trimmed(value, info.field_name)

    @field_validator("project_ids")
    @classmethod
    def normalize_projects(cls, values: tuple[LogicalId, ...]) -> tuple[LogicalId, ...]:
        return _unique_projects(values)

    @model_validator(mode="after")
    def validate_mapping(self) -> "LegacyEntityBinding":
        expected = entity_logical_id(self.legacy_entity_id)
        if self.canonical_ref.logical_id != expected:
            raise ValueError(
                "canonical_ref logical ID must be the stable mapping of legacy_entity_id"
            )
        return self


class EntityArtifact(BaseModel):
    """Canonical EntityVersion plus immutable semantic metadata."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: EntityVersion

    @model_validator(mode="after")
    def validate_identity(self) -> "EntityArtifact":
        if self.metadata.logical_id != self.value.entity_id:
            raise ValueError("entity metadata logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("entity metadata version identity mismatch")
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


class EntityImportResult(BaseModel):
    """Result of adapting a legacy FlowKit entity into canonical version truth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact: EntityArtifact
    compatibility: LegacyEntityBinding


def build_legacy_entity_provenance(
    snapshot: LegacyEntitySnapshot,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    correlation_id: str | None = None,
) -> Provenance:
    """Bind canonical EntityVersion provenance to the legacy compatibility source."""

    source = f"legacy-character:{snapshot.id}"
    if snapshot.updated_at is not None:
        source = f"{source}@{snapshot.updated_at}"
    return Provenance(
        source_refs=(source,),
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        correlation_id=correlation_id,
    )


class CanonicalEntityAdapter:
    """Deterministic anti-corruption mapper from legacy FlowKit entity rows."""

    @staticmethod
    def materialize(
        snapshot: LegacyEntitySnapshot,
        *,
        version_id: VersionId,
    ) -> EntityVersion:
        return EntityVersion(
            entity_id=entity_logical_id(snapshot.id),
            version_id=version_id,
            kind=snapshot.entity_type,
            name=snapshot.name,
            project_ids=snapshot.project_ids,
            slug=snapshot.slug,
            description=snapshot.description,
            voice_description=snapshot.voice_description,
        )

    @staticmethod
    def compatibility_binding(
        snapshot: LegacyEntitySnapshot,
        *,
        canonical_ref: VersionRef,
    ) -> LegacyEntityBinding:
        return LegacyEntityBinding(
            legacy_entity_id=snapshot.id,
            canonical_ref=canonical_ref,
            project_ids=snapshot.project_ids,
            legacy_media_id=snapshot.media_id,
            legacy_reference_image_url=snapshot.reference_image_url,
        )


class CanonicalEntityRepository:
    """Canonical EntityVersion repository backed by the shared VersionRepository.

    No entity-specific semantic table is introduced. This avoids creating a
    second canonical entity store while preserving the legacy character table as
    a compatibility/execution source until later migration work.
    """

    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)
        self.adapter = CanonicalEntityAdapter()

    async def create_initial_from_legacy(
        self,
        *,
        snapshot: LegacyEntitySnapshot,
        version_id: VersionId,
        actor_ref: str,
        reason: str,
        recorded_at: datetime,
        correlation_id: str | None = None,
    ) -> EntityImportResult:
        value = self.adapter.materialize(snapshot, version_id=version_id)
        provenance = build_legacy_entity_provenance(
            snapshot,
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=recorded_at,
            correlation_id=correlation_id,
        )
        metadata = SemanticRecordMetadata(
            logical_id=value.entity_id,
            version_id=value.version_id,
            provenance=provenance,
            created_at=recorded_at,
        )
        stored = await self.versions.create_initial(
            metadata=metadata,
            payload=value.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        artifact = EntityArtifact(metadata=stored.metadata, value=value)
        return EntityImportResult(
            artifact=artifact,
            compatibility=self.adapter.compatibility_binding(
                snapshot,
                canonical_ref=artifact.ref,
            ),
        )

    async def create_successor_from_legacy(
        self,
        *,
        snapshot: LegacyEntitySnapshot,
        version_id: VersionId,
        predecessor: VersionRef,
        actor_ref: str,
        reason: str,
        recorded_at: datetime,
        correlation_id: str | None = None,
    ) -> EntityImportResult:
        expected = entity_logical_id(snapshot.id)
        if predecessor.logical_id != expected:
            raise EntityIdentityError(
                "entity successor predecessor must share the stable canonical entity ID"
            )

        value = self.adapter.materialize(snapshot, version_id=version_id)
        provenance = build_legacy_entity_provenance(
            snapshot,
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=recorded_at,
            correlation_id=correlation_id,
        )
        metadata = SemanticRecordMetadata(
            logical_id=value.entity_id,
            version_id=value.version_id,
            predecessor=predecessor,
            provenance=provenance,
            created_at=recorded_at,
        )
        stored = await self.versions.create_successor(
            metadata=metadata,
            payload=value.model_dump(mode="json"),
            supersession_reason=reason,
        )
        artifact = EntityArtifact(metadata=stored.metadata, value=value)
        return EntityImportResult(
            artifact=artifact,
            compatibility=self.adapter.compatibility_binding(
                snapshot,
                canonical_ref=artifact.ref,
            ),
        )

    async def get_version(self, ref: VersionRef) -> EntityArtifact | None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = EntityVersion.model_validate(stored.payload)
        return EntityArtifact(metadata=stored.metadata, value=value)

    async def get_current_pointer(
        self,
        entity_id: LogicalId,
    ) -> CurrentVersionPointer | None:
        return await self.versions.get_current(entity_id)

    async def promote_current(
        self,
        *,
        ref: VersionRef,
        expected_revision: int,
        status: LifecycleState = LifecycleState.APPROVED,
    ) -> CurrentVersionPointer:
        return await self.versions.update_current(
            logical_id=ref.logical_id,
            version_id=ref.version_id,
            status=status,
            expected_revision=expected_revision,
        )
