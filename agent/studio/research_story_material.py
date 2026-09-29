"""Canonical Research Intelligence and Research→StoryMaterial boundaries.

External sources support EvidenceClaims. StoryMaterial is a derived, provider-
neutral transformation that retains exact claim provenance and cannot silently
upgrade factual status.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .primitives import (
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    VersionId,
    VersionRef,
)
from .versioning import CurrentPointerNotFound, CurrentVersionPointer, VersionRepository


class ResearchError(ValueError):
    """Base error for canonical research/story-material boundaries."""


class ResearchGateBlocked(ResearchError):
    """Raised when exact-source/factuality gates block acceptance."""


class UnsupportedSynthesis(ResearchGateBlocked):
    """Raised when story material exceeds or upgrades source evidence."""


class ResearchIdentityError(ResearchError):
    """Raised when project/source identity crosses authority boundaries."""


class ClaimDisposition(str, Enum):
    SUPPORTED = "SUPPORTED"
    DISPUTED = "DISPUTED"
    UNSUPPORTED = "UNSUPPORTED"


class ClaimCertainty(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class SourceKind(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    EXPERT = "EXPERT"
    DATASET = "DATASET"
    OFFICIAL = "OFFICIAL"
    OTHER = "OTHER"


class StoryMaterialKind(str, Enum):
    PRESSURE = "PRESSURE"
    DETAIL = "DETAIL"
    CONSTRAINT = "CONSTRAINT"
    SCENE_MATERIAL = "SCENE_MATERIAL"
    QUESTION = "QUESTION"


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _unique_refs(values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
    result: list[VersionRef] = []
    seen: set[tuple[str, str]] = set()
    for ref in values:
        key = (ref.logical_id.root, ref.version_id.root)
        if key not in seen:
            seen.add(key)
            result.append(ref)
    return tuple(result)


def _active_profile_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"active-profile:{project_id.root}")


def _topic_resolution_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"topic-resolution:{project_id.root}")


def _domain_resolution_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"niche-resolution:{project_id.root}")


def _research_brief_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"research-brief:{project_id.root}")


def _claim_id(project_id: LogicalId, claim_key: str) -> LogicalId:
    return LogicalId(f"evidence-claim:{project_id.root}:{claim_key}")


def _material_id(project_id: LogicalId, material_key: str) -> LogicalId:
    return LogicalId(f"story-material:{project_id.root}:{material_key}")


class ExternalSourceReference(BaseModel):
    """External evidence locator. It supports a claim but is not story truth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str
    kind: SourceKind
    locator: str
    title: str
    publisher_or_author: str
    accessed_at: datetime
    evidence_locator: str
    attribution: str | None = None

    @field_validator(
        "source_id",
        "locator",
        "title",
        "publisher_or_author",
        "evidence_locator",
    )
    @classmethod
    def validate_required_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("attribution")
    @classmethod
    def validate_attribution(cls, value: str | None) -> str | None:
        return None if value is None else _trimmed(value, "attribution")


class ResearchBrief(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    version_id: VersionId
    topic_ref: VersionRef
    domain_ref: VersionRef
    active_profile_ref: VersionRef
    factuality_class: str
    questions: tuple[str, ...]
    perspectives: tuple[str, ...] = ()
    scope: str

    @field_validator("factuality_class", "scope")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("questions", "perspectives")
    @classmethod
    def validate_tuple_text(cls, values: tuple[str, ...], info) -> tuple[str, ...]:
        result: list[str] = []
        for value in values:
            item = _trimmed(value, info.field_name)
            if item not in result:
                result.append(item)
        if info.field_name == "questions" and not result:
            raise ValueError("research brief requires at least one question")
        return tuple(result)

    @model_validator(mode="after")
    def validate_project_bindings(self) -> "ResearchBrief":
        if self.topic_ref.logical_id != _topic_resolution_id(self.project_id):
            raise ValueError(
                "topic_ref must bind canonical TopicResolution for the same project"
            )
        if self.domain_ref.logical_id != _domain_resolution_id(self.project_id):
            raise ValueError(
                "domain_ref must bind canonical DomainResolution for the same project"
            )
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError(
                "active_profile_ref must bind exact ActiveProductionProfile "
                "for the same project"
            )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return _research_brief_id(self.project_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return (
            SourceVersionBinding(role="topic_resolution", source=self.topic_ref),
            SourceVersionBinding(role="domain_resolution", source=self.domain_ref),
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
        )


class EvidenceClaim(BaseModel):
    """Canonical evidence-grounded claim with explicit uncertainty/dispute state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    claim_key: str
    version_id: VersionId
    research_brief_ref: VersionRef
    statement: str
    disposition: ClaimDisposition
    certainty: ClaimCertainty
    confidence: float = Field(ge=0.0, le=1.0)
    scope: str
    sources: tuple[ExternalSourceReference, ...]
    contradicts: tuple[VersionRef, ...] = ()
    attribution_required: bool = False
    attribution_note: str | None = None

    @field_validator("claim_key", "statement", "scope")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("contradicts")
    @classmethod
    def normalize_contradicts(
        cls, values: tuple[VersionRef, ...]
    ) -> tuple[VersionRef, ...]:
        return _unique_refs(values)

    @field_validator("attribution_note")
    @classmethod
    def validate_attribution_note(cls, value: str | None) -> str | None:
        return None if value is None else _trimmed(value, "attribution_note")

    @model_validator(mode="after")
    def validate_claim(self) -> "EvidenceClaim":
        if self.research_brief_ref.logical_id != _research_brief_id(self.project_id):
            raise ValueError(
                "research_brief_ref must bind canonical ResearchBrief for same project"
            )
        if self.disposition is ClaimDisposition.SUPPORTED and not self.sources:
            raise ValueError("supported claim requires at least one external source")
        if self.disposition is ClaimDisposition.DISPUTED:
            if not self.sources:
                raise ValueError("disputed claim requires attributed source evidence")
            if not self.attribution_required:
                raise ValueError("disputed claim must require attribution")
            if self.attribution_note is None:
                raise ValueError("disputed claim requires attribution_note")
        if self.disposition is ClaimDisposition.UNSUPPORTED and self.confidence > 0.5:
            raise ValueError("unsupported claim cannot have confidence > 0.5")
        if self.contradicts:
            for ref in self.contradicts:
                if not ref.logical_id.root.startswith(
                    f"evidence-claim:{self.project_id.root}:"
                ):
                    raise ValueError(
                        "contradicts must reference EvidenceClaim in same project"
                    )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return _claim_id(self.project_id, self.claim_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(
                role="research_brief",
                source=self.research_brief_ref,
            )
        ]
        values.extend(
            SourceVersionBinding(role=f"contradicts_{index:03d}", source=ref)
            for index, ref in enumerate(self.contradicts)
        )
        return tuple(values)

    def external_source_refs(self) -> tuple[str, ...]:
        refs: list[str] = []
        for source in self.sources:
            for value in (source.source_id, source.locator):
                if value not in refs:
                    refs.append(value)
        return tuple(refs)


class ClaimSupportBinding(BaseModel):
    """Exact claim/version support carried into StoryMaterial."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    claim_ref: VersionRef
    disposition: ClaimDisposition
    certainty: ClaimCertainty
    attribution_required: bool
    attribution_note: str | None = None

    @field_validator("attribution_note")
    @classmethod
    def validate_note(cls, value: str | None) -> str | None:
        return None if value is None else _trimmed(value, "attribution_note")


class StoryMaterial(BaseModel):
    """Derived story-use record; never factual authority above its claims."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    material_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    kind: StoryMaterialKind
    story_need: str
    content: str
    allowed_transformations: tuple[str, ...]
    claim_support: tuple[ClaimSupportBinding, ...]
    factual_disposition: ClaimDisposition
    attribution_required: bool = False
    attribution_note: str | None = None

    @field_validator("material_key", "story_need", "content")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("allowed_transformations")
    @classmethod
    def validate_transformations(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        result: list[str] = []
        for value in values:
            item = _trimmed(value, "allowed transformation")
            if item not in result:
                result.append(item)
        if not result:
            raise ValueError("StoryMaterial requires allowed_transformations")
        return tuple(result)

    @field_validator("attribution_note")
    @classmethod
    def validate_note(cls, value: str | None) -> str | None:
        return None if value is None else _trimmed(value, "attribution_note")

    @model_validator(mode="after")
    def validate_material(self) -> "StoryMaterial":
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError(
                "active_profile_ref must bind exact ActiveProductionProfile "
                "for the same project"
            )
        if not self.claim_support:
            raise ValueError("StoryMaterial requires exact EvidenceClaim support")
        claim_keys = [
            (item.claim_ref.logical_id.root, item.claim_ref.version_id.root)
            for item in self.claim_support
        ]
        if len(set(claim_keys)) != len(claim_keys):
            raise ValueError("StoryMaterial claim_support refs must be unique")
        for item in self.claim_support:
            if not item.claim_ref.logical_id.root.startswith(
                f"evidence-claim:{self.project_id.root}:"
            ):
                raise ValueError(
                    "StoryMaterial claims must belong to the same project"
                )
        if any(
            item.disposition is ClaimDisposition.UNSUPPORTED
            for item in self.claim_support
        ):
            raise ValueError("unsupported claims cannot support StoryMaterial")
        expected = (
            ClaimDisposition.DISPUTED
            if any(
                item.disposition is ClaimDisposition.DISPUTED
                for item in self.claim_support
            )
            else ClaimDisposition.SUPPORTED
        )
        if self.factual_disposition is not expected:
            raise ValueError(
                "StoryMaterial cannot upgrade or alter source claim factual status"
            )
        if expected is ClaimDisposition.DISPUTED:
            if not self.attribution_required:
                raise ValueError(
                    "StoryMaterial using disputed claims must require attribution"
                )
            if self.attribution_note is None:
                raise ValueError(
                    "StoryMaterial using disputed claims requires attribution_note"
                )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return _material_id(self.project_id, self.material_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            )
        ]
        values.extend(
            SourceVersionBinding(role=f"evidence_claim_{index:03d}", source=item.claim_ref)
            for index, item in enumerate(self.claim_support)
        )
        return tuple(values)


class ResearchArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: ResearchBrief | EvidenceClaim | StoryMaterial

    @model_validator(mode="after")
    def validate_identity(self) -> "ResearchArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("research artifact logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("research artifact version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError(
                "research artifact provenance must exactly bind declared inputs"
            )
        if isinstance(self.value, EvidenceClaim):
            provenance_refs = set(self.metadata.provenance.source_refs)
            missing_external = [
                ref
                for ref in self.value.external_source_refs()
                if ref not in provenance_refs
            ]
            if missing_external:
                raise ValueError(
                    "EvidenceClaim provenance must retain all external source refs: "
                    + ", ".join(missing_external)
                )
        if isinstance(self.value, (ResearchBrief, StoryMaterial)):
            if self.metadata.provenance.rule_version != self.value.active_profile_ref:
                raise ValueError(
                    "profile-consuming artifact provenance must pin "
                    "ActiveProductionProfile"
                )
        return self


def build_research_provenance(
    value: ResearchBrief | EvidenceClaim | StoryMaterial,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    refs = list(source_refs)
    if isinstance(value, EvidenceClaim):
        for ref in value.external_source_refs():
            if ref not in refs:
                refs.append(ref)
    rule_version = (
        value.active_profile_ref
        if isinstance(value, (ResearchBrief, StoryMaterial))
        else None
    )
    return Provenance(
        source_versions=value.source_bindings(),
        source_refs=tuple(refs),
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        rule_version=rule_version,
        correlation_id=correlation_id,
    )


class ResearchRepository:
    """Immutable ResearchBrief/EvidenceClaim/StoryMaterial repository adapter."""

    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)

    async def create_initial(
        self,
        *,
        value: ResearchBrief | EvidenceClaim | StoryMaterial,
        provenance: Provenance,
        created_at: datetime,
    ) -> ResearchArtifact:
        artifact = self._artifact(
            value=value,
            provenance=provenance,
            created_at=created_at,
            predecessor=None,
        )
        stored = await self.versions.create_initial(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        return ResearchArtifact(metadata=stored.metadata, value=value)

    async def create_successor(
        self,
        *,
        value: ResearchBrief | EvidenceClaim | StoryMaterial,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> ResearchArtifact:
        if predecessor.logical_id != value.logical_id:
            raise ResearchIdentityError(
                "research successor predecessor must share logical identity"
            )
        artifact = self._artifact(
            value=value,
            provenance=provenance,
            created_at=created_at,
            predecessor=predecessor,
        )
        stored = await self.versions.create_successor(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        return ResearchArtifact(metadata=stored.metadata, value=value)

    async def get(self, ref: VersionRef) -> ResearchArtifact | None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        payload = stored.payload
        logical = stored.metadata.logical_id.root
        if logical.startswith("research-brief:"):
            value = ResearchBrief.model_validate(payload)
        elif logical.startswith("evidence-claim:"):
            value = EvidenceClaim.model_validate(payload)
        elif logical.startswith("story-material:"):
            value = StoryMaterial.model_validate(payload)
        else:
            raise ResearchIdentityError(
                f"not a Research Intelligence artifact: {logical}"
            )
        return ResearchArtifact(metadata=stored.metadata, value=value)

    async def promote(
        self,
        *,
        ref: VersionRef,
        expected_revision: int,
    ) -> CurrentVersionPointer:
        artifact = await self.get(ref)
        if artifact is None:
            raise ResearchIdentityError(
                f"research artifact not found: {ref.logical_id.root}/{ref.version_id.root}"
            )
        await self._assert_ready(artifact.value)
        return await self.versions.update_current(
            logical_id=artifact.value.logical_id,
            version_id=artifact.value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )

    async def get_current(
        self,
        logical_id: LogicalId,
    ) -> ResearchArtifact | None:
        try:
            pointer = await self.versions.get_current(logical_id)
        except CurrentPointerNotFound:
            return None
        if pointer is None:
            return None
        return await self.get(
            VersionRef(logical_id=logical_id, version_id=pointer.version_id)
        )

    async def _assert_ready(
        self,
        value: ResearchBrief | EvidenceClaim | StoryMaterial,
    ) -> None:
        for binding in value.source_bindings():
            if await self.versions.get_version(binding.source) is None:
                raise ResearchGateBlocked(
                    f"missing exact source {binding.role}="
                    f"{binding.source.logical_id.root}/{binding.source.version_id.root}"
                )

        if isinstance(value, ResearchBrief):
            await self._assert_current_accepted(
                value.topic_ref,
                label="TopicResolution",
            )
            await self._assert_current_accepted(
                value.domain_ref,
                label="DomainResolution",
            )
            await self._assert_profile_locked(value.active_profile_ref)
            return

        if isinstance(value, EvidenceClaim):
            brief_pointer = await self.versions.get_current(
                value.research_brief_ref.logical_id
            )
            if (
                brief_pointer is None
                or brief_pointer.version_id != value.research_brief_ref.version_id
                or brief_pointer.status not in {
                    LifecycleState.APPROVED,
                    LifecycleState.LOCKED,
                }
            ):
                raise ResearchGateBlocked(
                    "EvidenceClaim research brief is not exact current accepted version"
                )
            return

        await self._assert_profile_locked(value.active_profile_ref)
        for support in value.claim_support:
            pointer = await self.versions.get_current(support.claim_ref.logical_id)
            if (
                pointer is None
                or pointer.version_id != support.claim_ref.version_id
                or pointer.status not in {
                    LifecycleState.APPROVED,
                    LifecycleState.LOCKED,
                }
            ):
                raise ResearchGateBlocked(
                    "StoryMaterial EvidenceClaim is not exact current accepted version"
                )
            claim_artifact = await self.get(support.claim_ref)
            if claim_artifact is None or not isinstance(
                claim_artifact.value, EvidenceClaim
            ):
                raise ResearchGateBlocked("StoryMaterial support is not EvidenceClaim")
            claim = claim_artifact.value
            if (
                claim.disposition is not support.disposition
                or claim.certainty is not support.certainty
                or claim.attribution_required != support.attribution_required
                or claim.attribution_note != support.attribution_note
            ):
                raise UnsupportedSynthesis(
                    "StoryMaterial claim support does not match source claim truth"
                )
            if claim.disposition is ClaimDisposition.UNSUPPORTED:
                raise UnsupportedSynthesis(
                    "unsupported claim cannot produce StoryMaterial"
                )

    async def _assert_current_accepted(
        self,
        ref: VersionRef,
        *,
        label: str,
    ) -> None:
        try:
            pointer = await self.versions.get_current(ref.logical_id)
        except CurrentPointerNotFound as exc:
            raise ResearchGateBlocked(
                f"missing {label} current pointer"
            ) from exc
        if (
            pointer is None
            or pointer.version_id != ref.version_id
            or pointer.status
            not in {LifecycleState.APPROVED, LifecycleState.LOCKED}
        ):
            raise ResearchGateBlocked(f"stale/unaccepted {label}")

    async def _assert_profile_locked(self, ref: VersionRef) -> None:
        try:
            pointer = await self.versions.get_current(ref.logical_id)
        except CurrentPointerNotFound as exc:
            raise ResearchGateBlocked(
                "missing ActiveProductionProfile current pointer"
            ) from exc
        if (
            pointer is None
            or pointer.version_id != ref.version_id
            or pointer.status is not LifecycleState.LOCKED
        ):
            raise ResearchGateBlocked("stale/unlocked ActiveProductionProfile")

    @staticmethod
    def _artifact(
        *,
        value: ResearchBrief | EvidenceClaim | StoryMaterial,
        provenance: Provenance,
        created_at: datetime,
        predecessor: VersionRef | None,
    ) -> ResearchArtifact:
        return ResearchArtifact(
            metadata=SemanticRecordMetadata(
                logical_id=value.logical_id,
                version_id=value.version_id,
                predecessor=predecessor,
                provenance=provenance,
                created_at=created_at,
            ),
            value=value,
        )


class ResearchToStoryMaterialService:
    """Transforms accepted claims into material without factual-authority uplift."""

    def __init__(self, repository: ResearchRepository) -> None:
        self.repository = repository

    async def build_material(
        self,
        *,
        project_id: LogicalId,
        material_key: str,
        version_id: VersionId,
        active_profile_ref: VersionRef,
        kind: StoryMaterialKind,
        story_need: str,
        content: str,
        allowed_transformations: tuple[str, ...],
        claim_refs: tuple[VersionRef, ...],
        attribution_note: str | None = None,
    ) -> StoryMaterial:
        support: list[ClaimSupportBinding] = []
        for ref in _unique_refs(claim_refs):
            artifact = await self.repository.get(ref)
            if artifact is None or not isinstance(artifact.value, EvidenceClaim):
                raise UnsupportedSynthesis(
                    f"StoryMaterial source is not an EvidenceClaim: "
                    f"{ref.logical_id.root}/{ref.version_id.root}"
                )
            claim = artifact.value
            if claim.project_id != project_id:
                raise UnsupportedSynthesis(
                    "StoryMaterial cannot consume claim from another project"
                )
            if claim.disposition is ClaimDisposition.UNSUPPORTED:
                raise UnsupportedSynthesis(
                    "unsupported claim cannot produce StoryMaterial"
                )
            support.append(
                ClaimSupportBinding(
                    claim_ref=claim.ref,
                    disposition=claim.disposition,
                    certainty=claim.certainty,
                    attribution_required=claim.attribution_required,
                    attribution_note=claim.attribution_note,
                )
            )

        if not support:
            raise UnsupportedSynthesis(
                "StoryMaterial requires at least one exact EvidenceClaim"
            )
        disposition = (
            ClaimDisposition.DISPUTED
            if any(item.disposition is ClaimDisposition.DISPUTED for item in support)
            else ClaimDisposition.SUPPORTED
        )
        required = disposition is ClaimDisposition.DISPUTED
        if required and attribution_note is None:
            notes = [
                item.attribution_note
                for item in support
                if item.attribution_note is not None
            ]
            attribution_note = "; ".join(notes) if notes else None

        return StoryMaterial(
            project_id=project_id,
            material_key=material_key,
            version_id=version_id,
            active_profile_ref=active_profile_ref,
            kind=kind,
            story_need=story_need,
            content=content,
            allowed_transformations=allowed_transformations,
            claim_support=tuple(support),
            factual_disposition=disposition,
            attribution_required=required,
            attribution_note=attribution_note,
        )
