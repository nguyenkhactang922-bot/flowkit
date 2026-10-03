"""IMP-041 canonical ReferenceAsset registry/resolver.

Reference assets are versioned conditioning/evidence, never Entity identity truth,
semantic State truth, or provider payload authority. The module reuses the shared
VersionRepository/DependencyGraph/InvalidationRepository and exposes only an
opaque legacy-media compatibility projection for downstream adapters.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .entity import EntityVersion, LegacyEntityBinding
from .invalidation import (
    DependencyGraphRepository,
    InvalidationRecord,
    InvalidationRepository,
)
from .persistence import SQLiteWriteOwner
from .primitives import (
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    VersionId,
    VersionRef,
)
from .versioning import CurrentVersionPointer, VersionRepository


_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ROLE_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_ACCEPTED = {LifecycleState.APPROVED, LifecycleState.LOCKED}


class ReferenceContractError(ValueError):
    """Base ReferenceAsset/Resolver contract error."""


class ReferenceIdentityError(ReferenceContractError):
    """Raised for invalid reference identity/version lineage."""


class ReferenceResolutionBlocked(ReferenceContractError):
    """Raised when required reference coverage cannot be resolved safely."""


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


def _role(value: str) -> str:
    normalized = _trimmed(value, "reference role").lower()
    if not _ROLE_RE.fullmatch(normalized):
        raise ValueError(
            "reference role must start with a lowercase letter and contain only "
            "lowercase letters, digits, '.', '_' or '-'"
        )
    return normalized


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return ref.logical_id.root, ref.version_id.root


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def reference_asset_logical_id(
    project_id: LogicalId,
    entity_ref: VersionRef,
    *,
    slot: str = "primary",
) -> LogicalId:
    """Stable asset identity for one project/entity logical identity/slot."""

    if not entity_ref.logical_id.root.startswith("entity:"):
        raise ReferenceIdentityError("ReferenceAsset identity requires canonical EntityVersion")
    normalized_slot = _role(slot)
    raw = (
        f"{project_id.root}\0{entity_ref.logical_id.root}\0{normalized_slot}"
    ).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:32]
    return LogicalId(f"reference-asset:{project_id.root}:{digest}")


class ReferenceAsset(BaseModel):
    """One immutable provider-neutral ReferenceAsset version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    reference_asset_id: LogicalId
    version_id: VersionId
    entity_ref: VersionRef
    slot: str = "primary"
    content_hash: str
    role: str
    mime_type: str
    source_uri: str | None = None
    evidence_refs: tuple[str, ...] = ()

    @field_validator("slot", "role")
    @classmethod
    def validate_role_like_fields(cls, value: str) -> str:
        return _role(value)

    @field_validator("content_hash")
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if not _HASH_RE.fullmatch(value):
            raise ValueError("content_hash must be sha256:<64 lowercase hex>")
        return value

    @field_validator("mime_type")
    @classmethod
    def validate_mime(cls, value: str) -> str:
        value = _trimmed(value, "mime_type").lower()
        if "/" not in value or value.startswith("/") or value.endswith("/"):
            raise ValueError("mime_type must be a media type such as image/png")
        return value

    @field_validator("source_uri")
    @classmethod
    def validate_source_uri(cls, value: str | None) -> str | None:
        return _optional_trimmed(value, "source_uri")

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_trimmed(value, "evidence_ref") for value in values)
        if len(normalized) != len(set(normalized)):
            raise ValueError("evidence_refs must be unique")
        return normalized

    @model_validator(mode="after")
    def validate_identity(self) -> "ReferenceAsset":
        expected = reference_asset_logical_id(
            self.project_id,
            self.entity_ref,
            slot=self.slot,
        )
        if self.reference_asset_id != expected:
            raise ValueError(
                "reference_asset_id must equal deterministic project/entity/slot identity"
            )
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.reference_asset_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return (SourceVersionBinding(role="entity_version", source=self.entity_ref),)


class LegacyReferenceBinding(BaseModel):
    """Compatibility projection from legacy media fields to one ReferenceAsset."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    asset_ref: VersionRef
    entity_ref: VersionRef
    legacy_media_id: str | None = None
    legacy_reference_image_url: str | None = None

    @field_validator("legacy_media_id")
    @classmethod
    def validate_media_id(cls, value: str | None) -> str | None:
        value = _optional_trimmed(value, "legacy_media_id")
        if value is not None and not _UUID_RE.fullmatch(value):
            raise ValueError("legacy_media_id must be UUID format; CAMS/base64 IDs are forbidden")
        return value

    @field_validator("legacy_reference_image_url")
    @classmethod
    def validate_reference_url(cls, value: str | None) -> str | None:
        return _optional_trimmed(value, "legacy_reference_image_url")

    @model_validator(mode="after")
    def validate_binding(self) -> "LegacyReferenceBinding":
        if self.legacy_media_id is None and self.legacy_reference_image_url is None:
            raise ValueError("legacy reference binding requires media_id or reference URL")
        return self

    @classmethod
    def from_entity_binding(
        cls,
        binding: LegacyEntityBinding,
        *,
        asset_ref: VersionRef,
    ) -> "LegacyReferenceBinding":
        return cls(
            asset_ref=asset_ref,
            entity_ref=binding.canonical_ref,
            legacy_media_id=binding.legacy_media_id,
            legacy_reference_image_url=binding.legacy_reference_image_url,
        )


class ReferenceArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: ReferenceAsset

    @model_validator(mode="after")
    def validate_identity(self) -> "ReferenceArtifact":
        if self.metadata.logical_id != self.value.reference_asset_id:
            raise ValueError("reference metadata logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("reference metadata version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError("reference provenance must exactly bind EntityVersion")
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


class ReferencePromotionResult(BaseModel):
    """Accepted successor activation plus durable invalidation evidence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pointer: CurrentVersionPointer
    invalidations: tuple[InvalidationRecord, ...]


def _reference_change_bindings(
    old: ReferenceAsset,
    new: ReferenceAsset,
) -> tuple[SourceVersionBinding, ...]:
    return (
        SourceVersionBinding(role="old_reference", source=old.ref),
        SourceVersionBinding(role="new_reference", source=new.ref),
    )


def build_reference_change_provenance(
    old: ReferenceAsset,
    new: ReferenceAsset,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=_reference_change_bindings(old, new),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        correlation_id=correlation_id,
    )


def build_reference_provenance(
    asset: ReferenceAsset,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=asset.source_bindings(),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        correlation_id=correlation_id,
    )


class ReferenceAssetRepository:
    """Immutable ReferenceAsset versions over the shared semantic repository."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)

    async def create_initial(
        self,
        *,
        asset: ReferenceAsset,
        provenance: Provenance,
        created_at: datetime,
    ) -> ReferenceArtifact:
        self._assert_provenance(asset, provenance)
        await self._assert_entity_current(asset.entity_ref, project_id=asset.project_id)
        metadata = SemanticRecordMetadata(
            logical_id=asset.reference_asset_id,
            version_id=asset.version_id,
            provenance=provenance,
            created_at=created_at,
        )
        stored = await self.versions.create_initial(
            metadata=metadata,
            payload=asset.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        artifact = ReferenceArtifact(metadata=stored.metadata, value=asset)
        await self._register_entity_dependency(artifact)
        return artifact

    async def create_successor(
        self,
        *,
        asset: ReferenceAsset,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> ReferenceArtifact:
        if predecessor.logical_id != asset.reference_asset_id:
            raise ReferenceIdentityError("reference successor must preserve logical identity")
        pointer = await self.versions.get_current(asset.reference_asset_id)
        if (
            pointer is None
            or pointer.version_id != predecessor.version_id
            or pointer.status not in _ACCEPTED
        ):
            raise ReferenceIdentityError(
                "reference successor predecessor must be exact current approved/locked version"
            )
        previous = await self.get_version(predecessor)
        if previous is None:
            raise ReferenceIdentityError("reference successor predecessor does not exist")
        self._assert_semantic_change(previous.value, asset)
        self._assert_provenance(asset, provenance)
        await self._assert_entity_current(asset.entity_ref, project_id=asset.project_id)
        metadata = SemanticRecordMetadata(
            logical_id=asset.reference_asset_id,
            version_id=asset.version_id,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
        )
        stored = await self.versions.create_successor(
            metadata=metadata,
            payload=asset.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        artifact = ReferenceArtifact(metadata=stored.metadata, value=asset)
        await self._register_entity_dependency(artifact)
        return artifact

    async def get_version(self, ref: VersionRef) -> ReferenceArtifact | None:
        if not ref.logical_id.root.startswith("reference-asset:"):
            raise ReferenceIdentityError("expected ReferenceAsset ref")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        return ReferenceArtifact(
            metadata=stored.metadata,
            value=ReferenceAsset.model_validate(stored.payload),
        )

    async def get_current_pointer(
        self,
        reference_asset_id: LogicalId,
    ) -> CurrentVersionPointer | None:
        return await self.versions.get_current(reference_asset_id)

    async def promote_current(
        self,
        *,
        ref: VersionRef,
        expected_revision: int,
        status: LifecycleState = LifecycleState.APPROVED,
    ) -> CurrentVersionPointer:
        """Promote only an initial ReferenceAsset version.

        Successor activation must use ``promote_successor_current`` so the
        FM-005 invalidation set is durably emitted before the current pointer
        moves. This prevents callers from bypassing selective invalidation.
        """

        if status not in _ACCEPTED:
            raise ReferenceContractError("ReferenceAsset current status must be APPROVED or LOCKED")
        artifact = await self.get_version(ref)
        if artifact is None:
            raise ReferenceContractError("ReferenceAsset exact version does not exist")
        if artifact.metadata.predecessor is not None:
            raise ReferenceContractError(
                "successor ReferenceAsset must use promote_successor_current with invalidation"
            )
        await self._assert_entity_current(
            artifact.value.entity_ref,
            project_id=artifact.value.project_id,
        )
        await self._assert_not_invalidated(ref)
        return await self.versions.update_current(
            logical_id=ref.logical_id,
            version_id=ref.version_id,
            status=status,
            expected_revision=expected_revision,
        )

    async def promote_successor_current(
        self,
        *,
        ref: VersionRef,
        expected_revision: int,
        invalidation_provenance: Provenance,
        repair_or_recompute_requirement: str,
        status: LifecycleState = LifecycleState.APPROVED,
    ) -> ReferencePromotionResult:
        """Activate a successor only after durable selective invalidation.

        Planning/creation of invalidation records happens before moving the
        current pointer, matching the frozen ordering requirement. If a later
        CAS loses a race, the conservative invalidation records remain safe and
        idempotent; replay uses the same deterministic dedupe keys.
        """

        if status not in _ACCEPTED:
            raise ReferenceContractError("ReferenceAsset current status must be APPROVED or LOCKED")
        artifact = await self.get_version(ref)
        if artifact is None:
            raise ReferenceContractError("ReferenceAsset exact version does not exist")
        predecessor_ref = artifact.metadata.predecessor
        if predecessor_ref is None:
            raise ReferenceContractError(
                "initial ReferenceAsset must use promote_current"
            )
        previous = await self.get_version(predecessor_ref)
        if previous is None:
            raise ReferenceIdentityError("successor predecessor ReferenceAsset does not exist")
        if invalidation_provenance.source_versions != _reference_change_bindings(
            previous.value, artifact.value
        ):
            raise ReferenceContractError(
                "reference change provenance must exactly bind old/new versions"
            )

        pointer = await self.versions.get_current(ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != predecessor_ref.version_id
            or pointer.status not in _ACCEPTED
            or pointer.revision != expected_revision
        ):
            raise ReferenceIdentityError(
                "successor activation requires exact current accepted predecessor/revision"
            )
        await self._assert_entity_current(
            artifact.value.entity_ref,
            project_id=artifact.value.project_id,
        )
        await self._assert_not_invalidated(ref)

        invalidations = await self.invalidations.create_for_change(
            cause="REFERENCE_VERSION_CHANGED",
            source_old=previous.ref,
            source_new=artifact.ref,
            provenance=invalidation_provenance,
            scope=(
                f"REFERENCE_ROLE:{previous.value.role}->{artifact.value.role};"
                f"HASH:{previous.value.content_hash}->{artifact.value.content_hash}"
            ),
            repair_or_recompute_requirement=_trimmed(
                repair_or_recompute_requirement,
                "repair_or_recompute_requirement",
            ),
        )
        updated = await self.versions.update_current(
            logical_id=ref.logical_id,
            version_id=ref.version_id,
            status=status,
            expected_revision=expected_revision,
        )
        return ReferencePromotionResult(
            pointer=updated,
            invalidations=tuple(invalidations),
        )

    async def _assert_entity_current(
        self,
        entity_ref: VersionRef,
        *,
        project_id: LogicalId,
    ) -> None:
        stored = await self.versions.get_version(entity_ref)
        if stored is None:
            raise ReferenceContractError("bound EntityVersion does not exist")
        entity = EntityVersion.model_validate(stored.payload)
        if project_id not in entity.project_ids:
            raise ReferenceContractError("bound EntityVersion does not belong to project")
        pointer = await self.versions.get_current(entity_ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != entity_ref.version_id
            or pointer.status not in _ACCEPTED
        ):
            raise ReferenceContractError("bound EntityVersion is not exact current approved/locked")

    async def _assert_not_invalidated(self, ref: VersionRef) -> None:
        for record in await self.invalidations.list_unresolved():
            if (
                record.affected_object_id == ref.logical_id
                and record.affected_object_version == ref.version_id
            ):
                raise ReferenceContractError("ReferenceAsset has unresolved invalidation")

    def _assert_provenance(self, asset: ReferenceAsset, provenance: Provenance) -> None:
        if provenance.source_versions != asset.source_bindings():
            raise ReferenceContractError(
                "ReferenceAsset provenance must exactly bind EntityVersion"
            )

    def _assert_semantic_change(
        self,
        previous: ReferenceAsset,
        successor: ReferenceAsset,
    ) -> None:
        previous_payload = previous.model_dump(mode="json", exclude={"version_id"})
        successor_payload = successor.model_dump(mode="json", exclude={"version_id"})
        if previous_payload == successor_payload:
            raise ReferenceContractError(
                "ReferenceAsset successor requires semantic/content/role/source change"
            )

    async def _register_entity_dependency(self, artifact: ReferenceArtifact) -> None:
        await self.graph.create_edge(
            source=artifact.value.entity_ref,
            dependent=artifact.ref,
            edge_type="reference_entity_version",
            dependency_reason="ReferenceAsset identity/coverage source EntityVersion",
            provenance=artifact.metadata.provenance,
            created_at=artifact.metadata.created_at,
        )


class ReferenceCapabilityConstraint(BaseModel):
    """Provider-neutral capability facts supplied to the resolver."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_references: int = Field(ge=1, le=64)
    supported_roles: tuple[str, ...]
    accepted_mime_types: tuple[str, ...] = ()
    requires_media_id: bool = True

    @field_validator("supported_roles")
    @classmethod
    def validate_roles(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(sorted({_role(value) for value in values}))
        if not normalized:
            raise ValueError("supported_roles must not be empty")
        return normalized

    @field_validator("accepted_mime_types")
    @classmethod
    def validate_mimes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    _trimmed(value, "accepted_mime_type").lower()
                    for value in values
                }
            )
        )


class ReferenceRequirement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_ref: VersionRef
    role: str
    required: bool = True

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        return _role(value)


class ReferenceCandidate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    asset_ref: VersionRef
    compatibility: LegacyReferenceBinding

    @model_validator(mode="after")
    def validate_refs(self) -> "ReferenceCandidate":
        if self.compatibility.asset_ref != self.asset_ref:
            raise ValueError("candidate compatibility must bind the same asset_ref")
        return self


class ProviderReferenceBindingProjection(BaseModel):
    """Minimal opaque projection consumed later by provider adapters."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    asset_ref: VersionRef
    entity_ref: VersionRef
    role: str
    content_hash: str
    media_id: str | None = None
    source_uri: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        return _role(value)

    @field_validator("content_hash")
    @classmethod
    def validate_content_hash(cls, value: str) -> str:
        if not _HASH_RE.fullmatch(value):
            raise ValueError("content_hash must be sha256:<64 lowercase hex>")
        return value

    @field_validator("media_id")
    @classmethod
    def validate_media_id(cls, value: str | None) -> str | None:
        if value is not None and not _UUID_RE.fullmatch(value):
            raise ValueError("media_id must be UUID format")
        return value

    @field_validator("source_uri")
    @classmethod
    def validate_source_uri(cls, value: str | None) -> str | None:
        return _optional_trimmed(value, "source_uri")


class ReferenceRejection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    asset_ref: VersionRef
    reason: str

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        return _trimmed(value, "rejection reason")


class ReferenceResolutionTrace(BaseModel):
    """Deterministic evidence explaining selected and rejected exact references."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    active_profile_ref: VersionRef
    requirements: tuple[ReferenceRequirement, ...]
    capability: ReferenceCapabilityConstraint
    candidate_refs: tuple[VersionRef, ...]
    selected: tuple[ProviderReferenceBindingProjection, ...]
    rejected: tuple[ReferenceRejection, ...]

    @model_validator(mode="after")
    def validate_trace(self) -> "ReferenceResolutionTrace":
        candidate_keys = [_ref_key(ref) for ref in self.candidate_refs]
        if candidate_keys != sorted(candidate_keys) or len(candidate_keys) != len(set(candidate_keys)):
            raise ValueError("candidate_refs must be sorted and unique")
        selected_keys = [_ref_key(item.asset_ref) for item in self.selected]
        if len(selected_keys) != len(set(selected_keys)):
            raise ValueError("selected reference assets must be unique")
        if not set(selected_keys).issubset(set(candidate_keys)):
            raise ValueError("selected asset refs must come from candidate_refs")
        return self

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        bindings: list[SourceVersionBinding] = [
            SourceVersionBinding(role="active_profile", source=self.active_profile_ref)
        ]
        bindings.extend(
            SourceVersionBinding(
                role=f"requirement_entity_{index:03d}",
                source=requirement.entity_ref,
            )
            for index, requirement in enumerate(self.requirements)
        )
        bindings.extend(
            SourceVersionBinding(
                role=f"selected_reference_{index:03d}",
                source=selected.asset_ref,
            )
            for index, selected in enumerate(self.selected)
        )
        return tuple(bindings)


class ReferenceResolveRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    active_profile_ref: VersionRef
    requirements: tuple[ReferenceRequirement, ...]
    capability: ReferenceCapabilityConstraint

    @field_validator("requirements")
    @classmethod
    def normalize_requirements(
        cls,
        values: tuple[ReferenceRequirement, ...],
    ) -> tuple[ReferenceRequirement, ...]:
        keys = [(_ref_key(req.entity_ref), req.role) for req in values]
        if len(keys) != len(set(keys)):
            raise ValueError("reference requirements must be unique by entity/version + role")
        return tuple(
            sorted(
                values,
                key=lambda req: (
                    not req.required,
                    req.entity_ref.logical_id.root,
                    req.entity_ref.version_id.root,
                    req.role,
                ),
            )
        )

    @model_validator(mode="after")
    def validate_request(self) -> "ReferenceResolveRequest":
        if self.active_profile_ref.logical_id != LogicalId(
            f"active-profile:{self.project_id.root}"
        ):
            raise ValueError("active_profile_ref belongs to a different project")
        return self


def build_reference_resolution_provenance(
    resolution: ReferenceResolutionTrace,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=resolution.source_bindings(),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        correlation_id=correlation_id,
    )


class ReferenceResolver:
    """Deterministic minimal-subset Reference Resolver."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)

    async def resolve(
        self,
        *,
        request: ReferenceResolveRequest,
        candidates: tuple[ReferenceCandidate, ...],
    ) -> ReferenceResolutionTrace:
        await self._assert_profile_current(
            project_id=request.project_id,
            profile_ref=request.active_profile_ref,
        )
        for requirement in request.requirements:
            await self._assert_entity_current(
                requirement.entity_ref,
                project_id=request.project_id,
            )
            if requirement.required and requirement.role not in request.capability.supported_roles:
                raise ReferenceResolutionBlocked(
                    f"required role is unsupported by capability: {requirement.role}"
                )

        candidate_refs = tuple(sorted((item.asset_ref for item in candidates), key=_ref_key))
        candidate_keys = [_ref_key(ref) for ref in candidate_refs]
        if len(candidate_keys) != len(set(candidate_keys)):
            raise ReferenceResolutionBlocked("candidate ReferenceAsset refs must be unique")

        unresolved = {
            (record.affected_object_id.root, record.affected_object_version.root)
            for record in await self.invalidations.list_unresolved()
        }
        loaded: dict[tuple[str, str], tuple[ReferenceAsset, LegacyReferenceBinding]] = {}
        rejected: list[ReferenceRejection] = []

        for candidate in sorted(candidates, key=lambda item: _ref_key(item.asset_ref)):
            stored = await self.versions.get_version(candidate.asset_ref)
            if stored is None:
                rejected.append(
                    ReferenceRejection(asset_ref=candidate.asset_ref, reason="missing_asset")
                )
                continue
            asset = ReferenceAsset.model_validate(stored.payload)
            pointer = await self.versions.get_current(asset.reference_asset_id)
            if (
                pointer is None
                or pointer.version_id != asset.version_id
                or pointer.status not in _ACCEPTED
            ):
                rejected.append(
                    ReferenceRejection(asset_ref=asset.ref, reason="stale_or_unapproved")
                )
                continue
            if _ref_key(asset.ref) in unresolved:
                rejected.append(ReferenceRejection(asset_ref=asset.ref, reason="invalidated"))
                continue
            if asset.project_id != request.project_id:
                rejected.append(ReferenceRejection(asset_ref=asset.ref, reason="wrong_project"))
                continue
            if candidate.compatibility.entity_ref != asset.entity_ref:
                rejected.append(
                    ReferenceRejection(asset_ref=asset.ref, reason="entity_binding_mismatch")
                )
                continue
            try:
                await self._assert_entity_current(
                    asset.entity_ref,
                    project_id=request.project_id,
                )
            except ReferenceResolutionBlocked:
                rejected.append(
                    ReferenceRejection(asset_ref=asset.ref, reason="stale_entity_version")
                )
                continue
            if asset.role not in request.capability.supported_roles:
                rejected.append(
                    ReferenceRejection(asset_ref=asset.ref, reason="unsupported_role")
                )
                continue
            if (
                request.capability.accepted_mime_types
                and asset.mime_type not in request.capability.accepted_mime_types
            ):
                rejected.append(
                    ReferenceRejection(asset_ref=asset.ref, reason="unsupported_mime")
                )
                continue
            if (
                request.capability.requires_media_id
                and candidate.compatibility.legacy_media_id is None
            ):
                rejected.append(
                    ReferenceRejection(asset_ref=asset.ref, reason="missing_media_id")
                )
                continue
            loaded[_ref_key(asset.ref)] = (asset, candidate.compatibility)

        selected: list[ProviderReferenceBindingProjection] = []
        selected_keys: set[tuple[str, str]] = set()
        for requirement in request.requirements:
            matches = [
                (asset, compatibility)
                for asset, compatibility in loaded.values()
                if asset.entity_ref == requirement.entity_ref and asset.role == requirement.role
            ]
            matches.sort(key=lambda pair: _ref_key(pair[0].ref))
            if not matches:
                if requirement.required:
                    raise ReferenceResolutionBlocked(
                        "missing required reference coverage for "
                        f"{requirement.entity_ref.logical_id.root}/{requirement.role}"
                    )
                continue
            asset, compatibility = matches[0]
            key = _ref_key(asset.ref)
            if key in selected_keys:
                continue
            if len(selected) >= request.capability.max_references:
                if requirement.required:
                    raise ReferenceResolutionBlocked(
                        "required reference coverage exceeds max_references capability"
                    )
                continue
            selected_keys.add(key)
            selected.append(
                ProviderReferenceBindingProjection(
                    asset_ref=asset.ref,
                    entity_ref=asset.entity_ref,
                    role=asset.role,
                    content_hash=asset.content_hash,
                    media_id=compatibility.legacy_media_id,
                    source_uri=compatibility.legacy_reference_image_url or asset.source_uri,
                )
            )

        for key, (asset, _) in sorted(loaded.items()):
            if key not in selected_keys:
                rejected.append(
                    ReferenceRejection(
                        asset_ref=asset.ref,
                        reason="not_selected_minimal_subset",
                    )
                )

        return ReferenceResolutionTrace(
            project_id=request.project_id,
            active_profile_ref=request.active_profile_ref,
            requirements=request.requirements,
            capability=request.capability,
            candidate_refs=candidate_refs,
            selected=tuple(selected),
            rejected=tuple(
                sorted(
                    rejected,
                    key=lambda item: (_ref_key(item.asset_ref), item.reason),
                )
            ),
        )

    async def bind_consumer(
        self,
        *,
        resolution: ReferenceResolutionTrace,
        consumer_ref: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> None:
        if provenance.source_versions != resolution.source_bindings():
            raise ReferenceContractError(
                "reference binding provenance must exactly match resolution sources"
            )
        await self._assert_profile_current(
            project_id=resolution.project_id,
            profile_ref=resolution.active_profile_ref,
        )
        consumer = await self.versions.get_version(consumer_ref)
        if consumer is None:
            raise ReferenceContractError("reference consumer exact version does not exist")

        unresolved = {
            (record.affected_object_id.root, record.affected_object_version.root)
            for record in await self.invalidations.list_unresolved()
        }
        for selected in resolution.selected:
            stored = await self.versions.get_version(selected.asset_ref)
            if stored is None:
                raise ReferenceContractError("selected ReferenceAsset exact version disappeared")
            asset = ReferenceAsset.model_validate(stored.payload)
            pointer = await self.versions.get_current(asset.reference_asset_id)
            if (
                pointer is None
                or pointer.version_id != asset.version_id
                or pointer.status not in _ACCEPTED
                or _ref_key(asset.ref) in unresolved
            ):
                raise ReferenceContractError(
                    "selected ReferenceAsset is no longer exact current accepted/valid"
                )
            await self._assert_entity_current(
                asset.entity_ref,
                project_id=resolution.project_id,
            )
            if (
                asset.entity_ref != selected.entity_ref
                or asset.role != selected.role
                or asset.content_hash != selected.content_hash
            ):
                raise ReferenceContractError(
                    "selected provider projection does not match canonical ReferenceAsset"
                )
            await self.graph.create_edge(
                source=selected.asset_ref,
                dependent=consumer_ref,
                edge_type="reference_binding",
                dependency_reason=f"reference_role:{selected.role}",
                provenance=provenance,
                created_at=created_at,
            )

    async def _assert_profile_current(
        self,
        *,
        project_id: LogicalId,
        profile_ref: VersionRef,
    ) -> None:
        expected = LogicalId(f"active-profile:{project_id.root}")
        if profile_ref.logical_id != expected:
            raise ReferenceResolutionBlocked("active profile belongs to different project")
        stored = await self.versions.get_version(profile_ref)
        if stored is None:
            raise ReferenceResolutionBlocked("active profile exact version does not exist")
        pointer = await self.versions.get_current(profile_ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != profile_ref.version_id
            or pointer.status not in _ACCEPTED
        ):
            raise ReferenceResolutionBlocked(
                "active profile is not exact current approved/locked"
            )

    async def _assert_entity_current(
        self,
        entity_ref: VersionRef,
        *,
        project_id: LogicalId,
    ) -> None:
        stored = await self.versions.get_version(entity_ref)
        if stored is None:
            raise ReferenceResolutionBlocked("required EntityVersion does not exist")
        entity = EntityVersion.model_validate(stored.payload)
        if project_id not in entity.project_ids:
            raise ReferenceResolutionBlocked("required EntityVersion belongs to different project")
        pointer = await self.versions.get_current(entity_ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != entity_ref.version_id
            or pointer.status not in _ACCEPTED
        ):
            raise ReferenceResolutionBlocked(
                "required EntityVersion is not exact current approved/locked"
            )


class ReferenceAssetInvalidationService:
    """Durable selective invalidation for accepted ReferenceVersion changes."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)

    async def invalidate_change(
        self,
        *,
        old: ReferenceAsset,
        new: ReferenceAsset,
        provenance: Provenance,
        repair_or_recompute_requirement: str,
    ) -> tuple[InvalidationRecord, ...]:
        if old.reference_asset_id != new.reference_asset_id:
            raise ReferenceIdentityError("reference invalidation requires same logical asset")
        if old.version_id == new.version_id:
            raise ReferenceIdentityError("reference invalidation requires a new version")
        if (
            old.model_dump(mode="json", exclude={"version_id"})
            == new.model_dump(mode="json", exclude={"version_id"})
        ):
            raise ReferenceIdentityError("reference invalidation requires semantic change")
        if provenance.source_versions != _reference_change_bindings(old, new):
            raise ReferenceContractError(
                "reference invalidation provenance must exactly bind old/new versions"
            )
        old_stored = await self.versions.get_version(old.ref)
        new_stored = await self.versions.get_version(new.ref)
        if old_stored is None or new_stored is None:
            raise ReferenceContractError("reference invalidation requires persisted old/new versions")
        pointer = await self.versions.get_current(new.reference_asset_id)
        if (
            pointer is None
            or pointer.version_id not in {old.version_id, new.version_id}
            or pointer.status not in _ACCEPTED
        ):
            raise ReferenceContractError(
                "reference invalidation requires old or new exact version to be current accepted"
            )
        records = await self.invalidations.create_for_change(
            cause="REFERENCE_VERSION_CHANGED",
            source_old=old.ref,
            source_new=new.ref,
            provenance=provenance,
            scope=(
                f"REFERENCE_ROLE:{old.role}->{new.role};"
                f"HASH:{old.content_hash}->{new.content_hash}"
            ),
            repair_or_recompute_requirement=_trimmed(
                repair_or_recompute_requirement,
                "repair_or_recompute_requirement",
            ),
        )
        return tuple(records)
