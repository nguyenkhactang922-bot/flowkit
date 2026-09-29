"""Canonical character psychology, relationship and knowledge state.

IMP-022 implements the frozen Story-domain boundaries for Character Psychology,
Relationship State and Knowledge / Belief State. Canonical dramatic state is
kept separate from visual Entity/Reference truth and is persisted through the
shared immutable VersionRepository.

The implementation deliberately supports a two-phase psychology lifecycle:
pre-StoryCore CharacterModelVersion records may exist as DRAFT inputs while
StoryCore itself is being assembled; promotion to APPROVED requires an exact
current StoryCore binding. This preserves the frozen dependency order without
creating a second StoryCore or weakening the Master ordering gate.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .entity import EntityVersion
from .invalidation import DependencyGraphRepository
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


class CharacterStateError(ValueError):
    """Base error for IMP-022 canonical character-state boundaries."""


class CharacterStateGateBlocked(CharacterStateError):
    """Raised when exact-version, chronology or authority gates block promotion."""


class CharacterStateIdentityError(CharacterStateError):
    """Raised when project/entity/state identity crosses canonical boundaries."""


class ObjectiveTruth(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class CharacterEpistemicState(str, Enum):
    KNOWS = "KNOWS"
    BELIEVES = "BELIEVES"
    SUSPECTS = "SUSPECTS"
    MISUNDERSTANDS = "MISUNDERSTANDS"
    UNKNOWN = "UNKNOWN"


class AudienceEpistemicState(str, Enum):
    KNOWS = "KNOWS"
    SUSPECTS = "SUSPECTS"
    UNKNOWN = "UNKNOWN"


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


def _unique_text(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        item = _trimmed(value, label)
        if item not in result:
            result.append(item)
    return tuple(result)


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


def character_model_logical_id(character_id: LogicalId) -> LogicalId:
    return LogicalId(f"character-model:{character_id.root}")


def character_knowledge_logical_id(character_id: LogicalId) -> LogicalId:
    return LogicalId(f"character-knowledge:{character_id.root}")


def relationship_logical_id(
    project_id: LogicalId,
    participant_ids: tuple[LogicalId, ...],
) -> LogicalId:
    if len(participant_ids) < 2:
        raise ValueError("relationship requires at least two participants")
    ordered = sorted({item.root for item in participant_ids})
    if len(ordered) != len(participant_ids):
        raise ValueError("relationship participants must be unique")
    raw = json.dumps(
        {"project": project_id.root, "participants": ordered},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return LogicalId("relationship:" + hashlib.sha256(raw).hexdigest()[:48])


def _require_entity_ref(ref: VersionRef, label: str) -> VersionRef:
    if not ref.logical_id.root.startswith("entity:"):
        raise ValueError(f"{label} must reference canonical EntityVersion")
    return ref


class VoiceRegister(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    register_id: str
    trigger: str
    syntax: str
    vocabulary: str
    rhythm: str

    @field_validator("register_id", "trigger", "syntax", "vocabulary", "rhythm")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)


class CharacterModelVersion(BaseModel):
    """Stable dramatic psychology attached to one canonical EntityVersion."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    character_ref: VersionRef
    version_id: VersionId
    active_profile_ref: VersionRef
    story_core_ref: VersionRef | None = None
    story_context_refs: tuple[VersionRef, ...] = ()
    story_material_refs: tuple[VersionRef, ...] = ()
    relationship_context_refs: tuple[VersionRef, ...] = ()

    role: str
    external_want: str
    internal_need: str | None = None
    fear: str | None = None
    formative_pressure: str | None = None
    mistaken_belief: str | None = None
    values: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    strengths: tuple[str, ...] = ()
    flaws_or_defenses: tuple[str, ...] = ()
    secrets: tuple[str, ...] = ()
    social_mask: str | None = None
    private_self: str | None = None
    preferred_tactics: tuple[str, ...] = ()
    boundaries: tuple[str, ...] = ()
    decision_style: str
    voice_registers: tuple[VoiceRegister, ...] = ()
    arc_hypothesis: str | None = None

    @field_validator("role", "external_want", "decision_style")
    @classmethod
    def validate_required_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator(
        "internal_need",
        "fear",
        "formative_pressure",
        "mistaken_belief",
        "social_mask",
        "private_self",
        "arc_hypothesis",
    )
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return _optional_trimmed(value, info.field_name)

    @field_validator(
        "values",
        "contradictions",
        "strengths",
        "flaws_or_defenses",
        "secrets",
        "preferred_tactics",
        "boundaries",
    )
    @classmethod
    def normalize_text_lists(cls, values: tuple[str, ...], info) -> tuple[str, ...]:
        return _unique_text(values, info.field_name)

    @field_validator(
        "story_context_refs",
        "story_material_refs",
        "relationship_context_refs",
    )
    @classmethod
    def normalize_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        return _unique_refs(values)

    @model_validator(mode="after")
    def validate_authority(self) -> "CharacterModelVersion":
        _require_entity_ref(self.character_ref, "character_ref")
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError(
                "active_profile_ref must bind exact ActiveProductionProfile "
                "for the same project"
            )
        if self.story_core_ref is None and not self.story_context_refs:
            raise ValueError(
                "CharacterModelVersion requires StoryCore or explicit pre-core "
                "story_context_refs"
            )
        if self.story_core_ref is not None and not self.story_core_ref.logical_id.root.startswith(
            "story-core:"
        ):
            raise ValueError("story_core_ref must reference canonical StoryCore")
        allowed_story_context = (
            "story-idea:",
            "story-logline:",
            "story-premise:",
            "story-angle:",
            "story-theme:",
        )
        for ref in self.story_context_refs:
            if not ref.logical_id.root.startswith(allowed_story_context):
                raise ValueError(
                    "story_context_refs must reference canonical early-story intake"
                )
        for ref in self.story_material_refs:
            if not ref.logical_id.root.startswith("story-material:"):
                raise ValueError(
                    "story_material_refs must reference canonical StoryMaterial"
                )
        for ref in self.relationship_context_refs:
            if not ref.logical_id.root.startswith("relationship:"):
                raise ValueError(
                    "relationship_context_refs must reference RelationshipState"
                )
        if not any(
            (
                self.internal_need,
                self.fear,
                self.mistaken_belief,
                self.values,
                self.formative_pressure,
            )
        ):
            raise ValueError(
                "CharacterModelVersion requires at least one internal motivation "
                "or value constraint"
            )
        return self

    @property
    def character_id(self) -> LogicalId:
        return self.character_ref.logical_id

    @property
    def logical_id(self) -> LogicalId:
        return character_model_logical_id(self.character_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="character_entity", source=self.character_ref),
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
        ]
        if self.story_core_ref is not None:
            values.append(
                SourceVersionBinding(role="story_core", source=self.story_core_ref)
            )
        values.extend(
            SourceVersionBinding(role=f"story_context_{index:03d}", source=ref)
            for index, ref in enumerate(self.story_context_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"story_material_{index:03d}", source=ref)
            for index, ref in enumerate(self.story_material_refs)
        )
        values.extend(
            SourceVersionBinding(
                role=f"relationship_context_{index:03d}",
                source=ref,
            )
            for index, ref in enumerate(self.relationship_context_refs)
        )
        return tuple(values)


class RelationshipState(BaseModel):
    """Versioned relationship truth with explicit causal chronology."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    participant_refs: tuple[VersionRef, ...]
    version_id: VersionId
    sequence_ordinal: int = Field(ge=0)
    story_time: str
    previous_state_ref: VersionRef | None = None
    change_cause_refs: tuple[VersionRef, ...] = ()

    public_relation: str
    private_relation: str
    trust: float | None = Field(default=None, ge=-1.0, le=1.0)
    power_balance: str
    debts: tuple[str, ...] = ()
    resentments: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    secrets_between_them: tuple[str, ...] = ()
    current_pressure: str | None = None
    delta_summary: str | None = None

    @field_validator("story_time", "public_relation", "private_relation", "power_balance")
    @classmethod
    def validate_required_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("current_pressure", "delta_summary")
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return _optional_trimmed(value, info.field_name)

    @field_validator(
        "debts",
        "resentments",
        "dependencies",
        "secrets_between_them",
    )
    @classmethod
    def normalize_text_lists(cls, values: tuple[str, ...], info) -> tuple[str, ...]:
        return _unique_text(values, info.field_name)

    @field_validator("participant_refs", "change_cause_refs")
    @classmethod
    def normalize_refs(
        cls,
        values: tuple[VersionRef, ...],
        info,
    ) -> tuple[VersionRef, ...]:
        normalized = _unique_refs(values)
        if info.field_name == "participant_refs":
            return tuple(
                sorted(
                    normalized,
                    key=lambda ref: (ref.logical_id.root, ref.version_id.root),
                )
            )
        return normalized

    @model_validator(mode="after")
    def validate_chronology_shape(self) -> "RelationshipState":
        if len(self.participant_refs) < 2:
            raise ValueError("RelationshipState requires at least two participants")
        for ref in self.participant_refs:
            _require_entity_ref(ref, "participant_refs")
        relationship_logical_id(
            self.project_id,
            tuple(ref.logical_id for ref in self.participant_refs),
        )
        if not self.change_cause_refs:
            raise ValueError(
                "RelationshipState requires causal/baseline evidence for its claims"
            )
        if self.sequence_ordinal == 0:
            if self.previous_state_ref is not None:
                raise ValueError("initial RelationshipState cannot have previous_state_ref")
        else:
            if self.previous_state_ref is None:
                raise ValueError(
                    "non-initial RelationshipState requires previous_state_ref"
                )
            if self.delta_summary is None:
                raise ValueError("relationship change requires delta_summary")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return relationship_logical_id(
            self.project_id,
            tuple(ref.logical_id for ref in self.participant_refs),
        )

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role=f"participant_{index:03d}", source=ref)
            for index, ref in enumerate(self.participant_refs)
        ]
        if self.previous_state_ref is not None:
            values.append(
                SourceVersionBinding(
                    role="previous_relationship_state",
                    source=self.previous_state_ref,
                )
            )
        values.extend(
            SourceVersionBinding(role=f"change_cause_{index:03d}", source=ref)
            for index, ref in enumerate(self.change_cause_refs)
        )
        return tuple(values)


class KnowledgeItem(BaseModel):
    """One proposition tracked across objective, character and audience knowledge."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    claim_key: str
    content: str
    objective_truth: ObjectiveTruth
    character_state: CharacterEpistemicState
    objective_evidence_refs: tuple[VersionRef, ...] = ()
    source_event_refs: tuple[VersionRef, ...] = ()
    inference_basis_refs: tuple[VersionRef, ...] = ()
    audience_state: AudienceEpistemicState = AudienceEpistemicState.UNKNOWN
    hidden_from_others: bool = False

    @field_validator("claim_key", "content")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator(
        "objective_evidence_refs",
        "source_event_refs",
        "inference_basis_refs",
    )
    @classmethod
    def normalize_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        return _unique_refs(values)

    @model_validator(mode="after")
    def validate_epistemics(self) -> "KnowledgeItem":
        character_evidence = self.source_event_refs or self.inference_basis_refs
        if (
            self.objective_truth is not ObjectiveTruth.UNKNOWN
            and not self.objective_evidence_refs
        ):
            raise ValueError(
                "known objective truth requires exact objective evidence"
            )
        if (
            self.audience_state is AudienceEpistemicState.KNOWS
            and not (self.objective_evidence_refs or self.source_event_refs)
        ):
            raise ValueError("audience KNOWS requires exact evidence")
        if self.character_state is CharacterEpistemicState.KNOWS:
            if self.objective_truth is not ObjectiveTruth.TRUE:
                raise ValueError(
                    "KNOWS requires objective_truth=TRUE; false/uncertain propositions "
                    "belong in belief/misunderstanding tracks"
                )
            if not self.source_event_refs:
                raise ValueError(
                    "character cannot KNOW information without acquisition evidence"
                )
        elif self.character_state in {
            CharacterEpistemicState.BELIEVES,
            CharacterEpistemicState.SUSPECTS,
        }:
            if not character_evidence:
                raise ValueError(
                    "belief/suspicion requires source or inference basis evidence"
                )
        elif self.character_state is CharacterEpistemicState.MISUNDERSTANDS:
            if self.objective_truth is ObjectiveTruth.TRUE:
                raise ValueError(
                    "MISUNDERSTANDS cannot be used for an objectively true proposition"
                )
            if not character_evidence:
                raise ValueError(
                    "misunderstanding requires source or inference basis evidence"
                )
        elif self.character_state is CharacterEpistemicState.UNKNOWN:
            if character_evidence:
                raise ValueError(
                    "UNKNOWN character knowledge cannot carry acquisition/inference evidence"
                )
        return self

    def source_bindings(self, prefix: str) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(
                role=f"{prefix}_objective_{index:03d}",
                source=ref,
            )
            for index, ref in enumerate(self.objective_evidence_refs)
        ]
        values.extend(
            SourceVersionBinding(
                role=f"{prefix}_source_{index:03d}",
                source=ref,
            )
            for index, ref in enumerate(self.source_event_refs)
        )
        values.extend(
            SourceVersionBinding(
                role=f"{prefix}_inference_{index:03d}",
                source=ref,
            )
            for index, ref in enumerate(self.inference_basis_refs)
        )
        return tuple(values)


class CharacterKnowledgeState(BaseModel):
    """Versioned character knowledge/belief state with chronology."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    character_ref: VersionRef
    version_id: VersionId
    sequence_ordinal: int = Field(ge=0)
    story_time: str
    previous_state_ref: VersionRef | None = None
    change_event_refs: tuple[VersionRef, ...] = ()
    items: tuple[KnowledgeItem, ...]

    @field_validator("story_time")
    @classmethod
    def validate_story_time(cls, value: str) -> str:
        return _trimmed(value, "story_time")

    @field_validator("change_event_refs")
    @classmethod
    def normalize_change_refs(
        cls,
        values: tuple[VersionRef, ...],
    ) -> tuple[VersionRef, ...]:
        return _unique_refs(values)

    @model_validator(mode="after")
    def validate_state(self) -> "CharacterKnowledgeState":
        _require_entity_ref(self.character_ref, "character_ref")
        if not self.items:
            raise ValueError("CharacterKnowledgeState requires at least one KnowledgeItem")
        keys = [item.claim_key for item in self.items]
        if len(set(keys)) != len(keys):
            raise ValueError("KnowledgeItem claim_key values must be unique")
        if self.sequence_ordinal == 0:
            if self.previous_state_ref is not None:
                raise ValueError(
                    "initial CharacterKnowledgeState cannot have previous_state_ref"
                )
        else:
            if self.previous_state_ref is None:
                raise ValueError(
                    "non-initial CharacterKnowledgeState requires previous_state_ref"
                )
            if not self.change_event_refs:
                raise ValueError(
                    "knowledge-state successor requires a causal change event"
                )
        return self

    @property
    def character_id(self) -> LogicalId:
        return self.character_ref.logical_id

    @property
    def logical_id(self) -> LogicalId:
        return character_knowledge_logical_id(self.character_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="character_entity", source=self.character_ref)
        ]
        if self.previous_state_ref is not None:
            values.append(
                SourceVersionBinding(
                    role="previous_knowledge_state",
                    source=self.previous_state_ref,
                )
            )
        values.extend(
            SourceVersionBinding(role=f"change_event_{index:03d}", source=ref)
            for index, ref in enumerate(self.change_event_refs)
        )
        for index, item in enumerate(self.items):
            values.extend(item.source_bindings(f"knowledge_{index:03d}"))
        result: list[SourceVersionBinding] = []
        seen: set[tuple[str, str, str]] = set()
        for binding in values:
            key = (
                binding.role,
                binding.source.logical_id.root,
                binding.source.version_id.root,
            )
            if key not in seen:
                seen.add(key)
                result.append(binding)
        return tuple(result)


CharacterStateValue: TypeAlias = (
    CharacterModelVersion | RelationshipState | CharacterKnowledgeState
)


class CharacterStateArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: CharacterStateValue

    @model_validator(mode="after")
    def validate_identity(self) -> "CharacterStateArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("character-state logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("character-state version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError(
                "character-state provenance must exactly bind declared inputs"
            )
        if isinstance(self.value, CharacterModelVersion):
            if self.metadata.provenance.rule_version != self.value.active_profile_ref:
                raise ValueError(
                    "CharacterModelVersion provenance must pin ActiveProductionProfile"
                )
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


def build_character_state_provenance(
    value: CharacterStateValue,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=value.source_bindings(),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        rule_version=(
            value.active_profile_ref
            if isinstance(value, CharacterModelVersion)
            else None
        ),
        correlation_id=correlation_id,
    )


class CharacterStateRepository:
    """Shared immutable repository + exact-input/chronology promotion gates."""

    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)

    async def create_initial(
        self,
        *,
        value: CharacterStateValue,
        provenance: Provenance,
        created_at: datetime,
    ) -> CharacterStateArtifact:
        if isinstance(value, RelationshipState) and value.sequence_ordinal != 0:
            raise CharacterStateIdentityError(
                "initial RelationshipState must have sequence_ordinal=0"
            )
        if isinstance(value, CharacterKnowledgeState) and value.sequence_ordinal != 0:
            raise CharacterStateIdentityError(
                "initial CharacterKnowledgeState must have sequence_ordinal=0"
            )
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
        materialized = CharacterStateArtifact(
            metadata=stored.metadata,
            value=value,
        )
        await self._register_dependencies(materialized)
        return materialized

    async def create_successor(
        self,
        *,
        value: CharacterStateValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> CharacterStateArtifact:
        if predecessor.logical_id != value.logical_id:
            raise CharacterStateIdentityError(
                "character-state successor predecessor must share logical identity"
            )
        previous = await self.get(predecessor)
        if previous is None:
            raise CharacterStateIdentityError("character-state predecessor not found")
        self._validate_successor(previous.value, value, predecessor)

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
        materialized = CharacterStateArtifact(
            metadata=stored.metadata,
            value=value,
        )
        await self._register_dependencies(materialized)
        return materialized

    async def get(self, ref: VersionRef) -> CharacterStateArtifact | None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        root = stored.metadata.logical_id.root
        if root.startswith("character-model:"):
            value: CharacterStateValue = CharacterModelVersion.model_validate(
                stored.payload
            )
        elif root.startswith("relationship:"):
            value = RelationshipState.model_validate(stored.payload)
        elif root.startswith("character-knowledge:"):
            value = CharacterKnowledgeState.model_validate(stored.payload)
        else:
            raise CharacterStateIdentityError(
                f"not an IMP-022 character-state artifact: {root}"
            )
        return CharacterStateArtifact(metadata=stored.metadata, value=value)

    async def get_current(
        self,
        logical_id: LogicalId,
    ) -> CharacterStateArtifact | None:
        try:
            pointer = await self.versions.get_current(logical_id)
        except CurrentPointerNotFound:
            return None
        return await self.get(
            VersionRef(logical_id=logical_id, version_id=pointer.version_id)
        )

    async def promote(
        self,
        *,
        ref: VersionRef,
        expected_revision: int,
    ) -> CurrentVersionPointer:
        artifact = await self.get(ref)
        if artifact is None:
            raise CharacterStateIdentityError(
                f"character-state artifact not found: "
                f"{ref.logical_id.root}/{ref.version_id.root}"
            )
        await self._assert_ready(artifact.value)
        return await self.versions.update_current(
            logical_id=artifact.value.logical_id,
            version_id=artifact.value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )

    async def _register_dependencies(
        self,
        artifact: CharacterStateArtifact,
    ) -> None:
        roles_by_source: dict[tuple[str, str], list[str]] = {}
        refs_by_source: dict[tuple[str, str], VersionRef] = {}
        for binding in artifact.value.source_bindings():
            key = (
                binding.source.logical_id.root,
                binding.source.version_id.root,
            )
            refs_by_source[key] = binding.source
            roles_by_source.setdefault(key, []).append(binding.role)

        for key in sorted(roles_by_source):
            source = refs_by_source[key]
            roles = sorted(set(roles_by_source[key]))
            await self.graph.create_edge(
                source=source,
                dependent=artifact.ref,
                edge_type="character_state_input",
                dependency_reason=" + ".join(roles),
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _assert_ready(self, value: CharacterStateValue) -> None:
        for binding in value.source_bindings():
            if await self.versions.get_version(binding.source) is None:
                raise CharacterStateGateBlocked(
                    f"missing exact source {binding.role}="
                    f"{binding.source.logical_id.root}/"
                    f"{binding.source.version_id.root}"
                )

        if isinstance(value, CharacterModelVersion):
            await self._assert_entity_current(value.character_ref, value.project_id)
            await self._assert_profile_locked(value.active_profile_ref)
            if value.story_core_ref is None:
                raise CharacterStateGateBlocked(
                    "CharacterModelVersion remains DRAFT until exact StoryCore is bound"
                )
            await self._assert_current(
                value.story_core_ref,
                label="StoryCore",
                allowed={
                    LifecycleState.DRAFT,
                    LifecycleState.REVIEW,
                    LifecycleState.APPROVED,
                    LifecycleState.LOCKED,
                },
            )
            for ref in value.story_context_refs:
                await self._assert_current(
                    ref,
                    label="story context",
                    allowed={LifecycleState.APPROVED, LifecycleState.LOCKED},
                )
            for ref in value.story_material_refs:
                await self._assert_current(
                    ref,
                    label="StoryMaterial",
                    allowed={LifecycleState.APPROVED, LifecycleState.LOCKED},
                )
            for ref in value.relationship_context_refs:
                await self._assert_current(
                    ref,
                    label="RelationshipState",
                    allowed={LifecycleState.APPROVED, LifecycleState.LOCKED},
                )
            return

        if isinstance(value, RelationshipState):
            for ref in value.participant_refs:
                await self._assert_entity_current(ref, value.project_id)
            if value.previous_state_ref is not None:
                await self._assert_current(
                    value.previous_state_ref,
                    label="previous RelationshipState",
                    allowed={LifecycleState.APPROVED, LifecycleState.LOCKED},
                )
            for ref in value.change_cause_refs:
                await self._assert_current(
                    ref,
                    label="relationship change cause",
                    allowed={LifecycleState.APPROVED, LifecycleState.LOCKED},
                )
            return

        await self._assert_entity_current(value.character_ref, value.project_id)
        if value.previous_state_ref is not None:
            await self._assert_current(
                value.previous_state_ref,
                label="previous CharacterKnowledgeState",
                allowed={LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
        for ref in value.change_event_refs:
            await self._assert_current(
                ref,
                label="knowledge change event",
                allowed={LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
        for item in value.items:
            for ref in (
                *item.objective_evidence_refs,
                *item.source_event_refs,
                *item.inference_basis_refs,
            ):
                await self._assert_current(
                    ref,
                    label=f"knowledge evidence {item.claim_key}",
                    allowed={LifecycleState.APPROVED, LifecycleState.LOCKED},
                )

    async def _assert_entity_current(
        self,
        ref: VersionRef,
        project_id: LogicalId,
    ) -> None:
        await self._assert_current(
            ref,
            label="EntityVersion",
            allowed={LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        stored = await self.versions.get_version(ref)
        assert stored is not None
        entity = EntityVersion.model_validate(stored.payload)
        if project_id not in entity.project_ids:
            raise CharacterStateGateBlocked(
                "EntityVersion does not belong to character-state project"
            )

    async def _assert_profile_locked(self, ref: VersionRef) -> None:
        await self._assert_current(
            ref,
            label="ActiveProductionProfile",
            allowed={LifecycleState.LOCKED},
        )

    async def _assert_current(
        self,
        ref: VersionRef,
        *,
        label: str,
        allowed: set[LifecycleState],
    ) -> None:
        try:
            pointer = await self.versions.get_current(ref.logical_id)
        except CurrentPointerNotFound as exc:
            raise CharacterStateGateBlocked(
                f"missing {label} current pointer"
            ) from exc
        if (
            pointer is None
            or pointer.version_id != ref.version_id
            or pointer.status not in allowed
        ):
            raise CharacterStateGateBlocked(
                f"{label} is not exact current accepted version"
            )

    @staticmethod
    def _validate_successor(
        previous: CharacterStateValue,
        value: CharacterStateValue,
        predecessor: VersionRef,
    ) -> None:
        if type(previous) is not type(value):
            raise CharacterStateIdentityError(
                "character-state successor cannot change artifact type"
            )
        if isinstance(value, CharacterModelVersion):
            assert isinstance(previous, CharacterModelVersion)
            if value.character_id != previous.character_id:
                raise CharacterStateIdentityError(
                    "CharacterModelVersion successor cannot change character identity"
                )
            if value.project_id != previous.project_id:
                raise CharacterStateIdentityError(
                    "CharacterModelVersion successor cannot change project"
                )
            return

        if isinstance(value, RelationshipState):
            assert isinstance(previous, RelationshipState)
            if tuple(ref.logical_id for ref in value.participant_refs) != tuple(
                ref.logical_id for ref in previous.participant_refs
            ):
                raise CharacterStateIdentityError(
                    "RelationshipState successor cannot change participant identities"
                )
            if value.project_id != previous.project_id:
                raise CharacterStateIdentityError(
                    "RelationshipState successor cannot change project"
                )
            if value.previous_state_ref != predecessor:
                raise CharacterStateIdentityError(
                    "RelationshipState previous_state_ref must equal predecessor"
                )
            if value.sequence_ordinal != previous.sequence_ordinal + 1:
                raise CharacterStateIdentityError(
                    "RelationshipState sequence_ordinal must advance by exactly one"
                )
            return

        assert isinstance(previous, CharacterKnowledgeState)
        assert isinstance(value, CharacterKnowledgeState)
        if value.character_ref.logical_id != previous.character_ref.logical_id:
            raise CharacterStateIdentityError(
                "CharacterKnowledgeState successor cannot change character identity"
            )
        if value.project_id != previous.project_id:
            raise CharacterStateIdentityError(
                "CharacterKnowledgeState successor cannot change project"
            )
        if value.previous_state_ref != predecessor:
            raise CharacterStateIdentityError(
                "CharacterKnowledgeState previous_state_ref must equal predecessor"
            )
        if value.sequence_ordinal != previous.sequence_ordinal + 1:
            raise CharacterStateIdentityError(
                "CharacterKnowledgeState sequence_ordinal must advance by exactly one"
            )

    @staticmethod
    def _artifact(
        *,
        value: CharacterStateValue,
        provenance: Provenance,
        created_at: datetime,
        predecessor: VersionRef | None,
    ) -> CharacterStateArtifact:
        return CharacterStateArtifact(
            metadata=SemanticRecordMetadata(
                logical_id=value.logical_id,
                version_id=value.version_id,
                predecessor=predecessor,
                provenance=provenance,
                created_at=created_at,
            ),
            value=value,
        )
