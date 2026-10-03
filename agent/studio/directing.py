"""IMP-030 dramatic-to-camera canonical authority.

This module implements ADR-0019 without importing Flow/provider runtime semantics.
Narrative, State and Profile truth stay in their owning repositories; directing
artifacts persist exact refs, scoped authority and auditable decision bases only.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import Enum
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .active_profile import ActiveProductionProfile, profile_path_edge_type
from .character_state import (
    CharacterKnowledgeState,
    CharacterModelVersion,
    RelationshipState,
)
from .entity import EntityKind, EntityVersion
from .invalidation import (
    DependencyGraphRepository,
    InvalidationRecord,
    InvalidationRepository,
)
from .narrative_hierarchy import Scene, SceneDramaticBeat
from .narrative_trace import (
    NarrativeArtifactType,
    NarrativeTraceRepository,
    NarrativeTraceState,
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
from .state_continuity import StateSnapshotRepository
from .story_quality import ScriptLockManifest, script_lock_logical_id
from .versioning import VersionRepository


_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")
_ACCEPTED = {LifecycleState.APPROVED, LifecycleState.LOCKED}


class DirectingAuthorityError(ValueError):
    """Base IMP-030 contract/repository error."""


class DirectingIdentityError(DirectingAuthorityError):
    """Raised when directing artifact identity/version lineage is inconsistent."""


class DirectingGateBlocked(DirectingAuthorityError):
    """Raised when an exact upstream hard gate is missing/stale/invalid."""


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


def _key(value: str, label: str) -> str:
    value = _trimmed(value, label).lower()
    if not _KEY_RE.fullmatch(value):
        raise ValueError(
            f"{label} must contain lowercase letters, digits, '.', '_' or '-'"
        )
    return value


def _unique_text(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    normalized = tuple(_trimmed(value, label) for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{label} values must be unique")
    return normalized


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return ref.logical_id.root, ref.version_id.root


def _unique_refs(values: tuple[VersionRef, ...], label: str) -> tuple[VersionRef, ...]:
    by_key = {_ref_key(ref): ref for ref in values}
    if len(by_key) != len(values):
        raise ValueError(f"{label} must not contain duplicate exact refs")
    return tuple(by_key[key] for key in sorted(by_key))


def _digest(*parts: str) -> str:
    raw = "\0".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def _project_ref(ref: VersionRef, *, prefix: str, project_id: LogicalId, label: str) -> None:
    base = f"{prefix}{project_id.root}"
    root = ref.logical_id.root
    if root != base and not root.startswith(base + ":"):
        raise ValueError(f"{label} must belong to the same project")


def _active_profile_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"active-profile:{project_id.root}")


def audience_experience_target_logical_id(
    project_id: LogicalId,
    scene_dramatic_beat_ref: VersionRef,
) -> LogicalId:
    return LogicalId(
        f"audience-experience:{project_id.root}:"
        + _digest(project_id.root, scene_dramatic_beat_ref.logical_id.root)
    )


def directing_intent_logical_id(
    project_id: LogicalId,
    scene_dramatic_beat_ref: VersionRef,
) -> LogicalId:
    return LogicalId(
        f"directing-intent:{project_id.root}:"
        + _digest(project_id.root, scene_dramatic_beat_ref.logical_id.root)
    )


def scene_spatial_contract_logical_id(
    project_id: LogicalId,
    scene_ref: VersionRef,
) -> LogicalId:
    return LogicalId(
        f"scene-spatial-contract:{project_id.root}:"
        + _digest(project_id.root, scene_ref.logical_id.root)
    )


def blocking_plan_logical_id(
    project_id: LogicalId,
    scene_dramatic_beat_ref: VersionRef,
) -> LogicalId:
    return LogicalId(
        f"blocking-plan:{project_id.root}:"
        + _digest(project_id.root, scene_dramatic_beat_ref.logical_id.root)
    )


def cinematography_objective_logical_id(
    project_id: LogicalId,
    scene_dramatic_beat_ref: VersionRef,
) -> LogicalId:
    return LogicalId(
        f"cinematography-objective:{project_id.root}:"
        + _digest(project_id.root, scene_dramatic_beat_ref.logical_id.root)
    )


class EmotionTarget(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    name: str
    target_intensity: float = Field(ge=0.0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _trimmed(value, "emotion name")


class ExperienceShift(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    before: float = Field(ge=0.0)
    after: float = Field(ge=0.0)


class AudienceExperienceTarget(BaseModel):
    """Beat-scoped viewer-effect authority; never generic style prose."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    audience_experience_target_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    scene_dramatic_beat_ref: VersionRef
    narrative_trace_ref: VersionRef
    primary_emotion: EmotionTarget
    secondary_emotions: tuple[EmotionTarget, ...] = ()
    tension: ExperienceShift | None = None
    curiosity: ExperienceShift | None = None
    viewer_effects: tuple[str, ...] = Field(min_length=1)
    must_understand: tuple[str, ...] = ()
    must_not_yet_understand: tuple[str, ...] = ()
    expected_question: str | None = None
    expected_wait: str | None = None
    desired_uncertainty: float | None = Field(default=None, ge=0.0)
    desired_release: float | None = Field(default=None, ge=0.0)
    attention_primary: str
    attention_secondary: tuple[str, ...] = ()
    forbidden_experience: tuple[str, ...] = ()

    @field_validator(
        "viewer_effects",
        "must_understand",
        "must_not_yet_understand",
        "attention_secondary",
        "forbidden_experience",
    )
    @classmethod
    def validate_text_lists(cls, values: tuple[str, ...], info) -> tuple[str, ...]:
        return _unique_text(values, info.field_name)

    @field_validator("attention_primary")
    @classmethod
    def validate_attention(cls, value: str) -> str:
        return _trimmed(value, "attention_primary")

    @field_validator("expected_question", "expected_wait")
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return _optional_trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_authority(self) -> "AudienceExperienceTarget":
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        _project_ref(
            self.scene_dramatic_beat_ref,
            prefix="scene-dramatic-beat:",
            project_id=self.project_id,
            label="scene_dramatic_beat_ref",
        )
        if not self.narrative_trace_ref.logical_id.root.startswith("narrative-trace:"):
            raise ValueError("narrative_trace_ref must reference NarrativeTrace")
        expected = audience_experience_target_logical_id(
            self.project_id,
            self.scene_dramatic_beat_ref,
        )
        if self.audience_experience_target_id != expected:
            raise ValueError(f"audience_experience_target_id must be {expected.root}")
        overlap = set(self.must_understand) & set(self.must_not_yet_understand)
        if overlap:
            raise ValueError("audience cannot both understand and not-yet-understand the same item")
        generic = {"cinematic", "make it cinematic", "cinematic style"}
        if any(value.strip().lower() in generic for value in self.viewer_effects):
            raise ValueError("AudienceExperienceTarget cannot be generic cinematic style")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.audience_experience_target_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return (
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="scene_dramatic_beat", source=self.scene_dramatic_beat_ref),
            SourceVersionBinding(role="narrative_trace", source=self.narrative_trace_ref),
        )


class ActorDirection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_ref: VersionRef
    posture: str | None = None
    gaze: str | None = None
    breathing: str | None = None
    gesture: str | None = None
    tempo: str | None = None
    restraint_level: str | None = None

    @field_validator("posture", "gaze", "breathing", "gesture", "tempo", "restraint_level")
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return _optional_trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_direction(self) -> "ActorDirection":
        if not self.entity_ref.logical_id.root.startswith("entity:"):
            raise ValueError("ActorDirection entity_ref must be canonical EntityVersion")
        if not any(
            (
                self.posture,
                self.gaze,
                self.breathing,
                self.gesture,
                self.tempo,
                self.restraint_level,
            )
        ):
            raise ValueError("ActorDirection requires at least one performance instruction")
        return self


class DirectingIntent(BaseModel):
    """Beat-scoped performance/reveal/staging authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    directing_intent_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    script_lock_ref: VersionRef
    scene_dramatic_beat_ref: VersionRef
    audience_experience_target_ref: VersionRef
    performance_state_refs: tuple[VersionRef, ...] = ()
    performance_objective: str
    actor_directions: tuple[ActorDirection, ...] = ()
    reveal: tuple[str, ...] = ()
    withhold: tuple[str, ...] = ()
    attention_primary: str
    attention_secondary: str | None = None
    hold_before_action_seconds: float | None = Field(default=None, ge=0.0)
    hold_after_action_seconds: float | None = Field(default=None, ge=0.0)
    incoming_transition_intent: str | None = None
    outgoing_transition_intent: str | None = None

    @field_validator("performance_objective", "attention_primary")
    @classmethod
    def validate_required_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator(
        "attention_secondary",
        "incoming_transition_intent",
        "outgoing_transition_intent",
    )
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return _optional_trimmed(value, info.field_name)

    @field_validator("reveal", "withhold")
    @classmethod
    def validate_text_lists(cls, values: tuple[str, ...], info) -> tuple[str, ...]:
        return _unique_text(values, info.field_name)

    @field_validator("performance_state_refs")
    @classmethod
    def normalize_state_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        return _unique_refs(values, "performance_state_refs")

    @field_validator("actor_directions")
    @classmethod
    def normalize_actor_directions(
        cls,
        values: tuple[ActorDirection, ...],
    ) -> tuple[ActorDirection, ...]:
        keys = [_ref_key(value.entity_ref) for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("actor_directions must not duplicate entity refs")
        return tuple(sorted(values, key=lambda value: _ref_key(value.entity_ref)))

    @model_validator(mode="after")
    def validate_authority(self) -> "DirectingIntent":
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        if self.script_lock_ref.logical_id != script_lock_logical_id(self.project_id):
            raise ValueError("script_lock_ref must bind this project's ScriptLock")
        _project_ref(
            self.scene_dramatic_beat_ref,
            prefix="scene-dramatic-beat:",
            project_id=self.project_id,
            label="scene_dramatic_beat_ref",
        )
        _project_ref(
            self.audience_experience_target_ref,
            prefix="audience-experience:",
            project_id=self.project_id,
            label="audience_experience_target_ref",
        )
        expected = directing_intent_logical_id(self.project_id, self.scene_dramatic_beat_ref)
        if self.directing_intent_id != expected:
            raise ValueError(f"directing_intent_id must be {expected.root}")
        allowed_state_prefixes = ("character-model:", "relationship:", "character-knowledge:")
        for ref in self.performance_state_refs:
            if not ref.logical_id.root.startswith(allowed_state_prefixes):
                raise ValueError("performance_state_refs must reference canonical character-state artifacts")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.directing_intent_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="script_lock", source=self.script_lock_ref),
            SourceVersionBinding(role="scene_dramatic_beat", source=self.scene_dramatic_beat_ref),
            SourceVersionBinding(role="audience_experience_target", source=self.audience_experience_target_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"performance_state_{index:03d}", source=ref)
            for index, ref in enumerate(self.performance_state_refs)
        )
        actor_refs = {_ref_key(item.entity_ref): item.entity_ref for item in self.actor_directions}
        values.extend(
            SourceVersionBinding(role=f"actor_entity_{index:03d}", source=actor_refs[key])
            for index, key in enumerate(sorted(actor_refs))
        )
        return tuple(values)


class SpatialZone(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    zone_key: str
    description: str

    @field_validator("zone_key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        return _key(value, "zone_key")

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        return _trimmed(value, "zone description")


class SpatialAnchor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    anchor_key: str
    description: str
    entity_ref: VersionRef | None = None

    @field_validator("anchor_key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        return _key(value, "anchor_key")

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        return _trimmed(value, "anchor description")

    @model_validator(mode="after")
    def validate_entity(self) -> "SpatialAnchor":
        if self.entity_ref is not None and not self.entity_ref.logical_id.root.startswith("entity:"):
            raise ValueError("SpatialAnchor entity_ref must be canonical EntityVersion")
        return self


class SceneSpatialDramaticContract(BaseModel):
    """Scene-scoped dramatic geography baseline; never camera authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    spatial_contract_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    scene_ref: VersionRef
    scene_dramatic_beat_refs: tuple[VersionRef, ...] = Field(min_length=1)
    state_snapshot_ref: VersionRef
    approved_state_designation_ref: VersionRef
    location_entity_ref: VersionRef | None = None
    participant_entity_refs: tuple[VersionRef, ...] = ()
    topology: str
    zones: tuple[SpatialZone, ...] = Field(min_length=1)
    entrances: tuple[str, ...] = ()
    exits: tuple[str, ...] = ()
    anchors: tuple[SpatialAnchor, ...] = ()
    sightline_constraints: tuple[str, ...] = ()
    dramatic_constraints: tuple[str, ...] = Field(min_length=1)
    axis_policy: str | None = None

    @field_validator("topology")
    @classmethod
    def validate_topology(cls, value: str) -> str:
        return _trimmed(value, "topology")

    @field_validator("axis_policy")
    @classmethod
    def validate_axis_policy(cls, value: str | None) -> str | None:
        return _optional_trimmed(value, "axis_policy")

    @field_validator(
        "entrances",
        "exits",
        "sightline_constraints",
        "dramatic_constraints",
    )
    @classmethod
    def validate_text_lists(cls, values: tuple[str, ...], info) -> tuple[str, ...]:
        return _unique_text(values, info.field_name)

    @field_validator("scene_dramatic_beat_refs", "participant_entity_refs")
    @classmethod
    def normalize_refs(cls, values: tuple[VersionRef, ...], info) -> tuple[VersionRef, ...]:
        return _unique_refs(values, info.field_name)

    @field_validator("zones")
    @classmethod
    def normalize_zones(cls, values: tuple[SpatialZone, ...]) -> tuple[SpatialZone, ...]:
        keys = [value.zone_key for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("zones must have unique zone_key values")
        return tuple(sorted(values, key=lambda value: value.zone_key))

    @field_validator("anchors")
    @classmethod
    def normalize_anchors(cls, values: tuple[SpatialAnchor, ...]) -> tuple[SpatialAnchor, ...]:
        keys = [value.anchor_key for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("anchors must have unique anchor_key values")
        return tuple(sorted(values, key=lambda value: value.anchor_key))

    @model_validator(mode="after")
    def validate_authority(self) -> "SceneSpatialDramaticContract":
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        _project_ref(self.scene_ref, prefix="scene:", project_id=self.project_id, label="scene_ref")
        for ref in self.scene_dramatic_beat_refs:
            _project_ref(
                ref,
                prefix="scene-dramatic-beat:",
                project_id=self.project_id,
                label="scene_dramatic_beat_refs",
            )
        _project_ref(
            self.state_snapshot_ref,
            prefix="state-snapshot:",
            project_id=self.project_id,
            label="state_snapshot_ref",
        )
        _project_ref(
            self.approved_state_designation_ref,
            prefix="approved-end-state:",
            project_id=self.project_id,
            label="approved_state_designation_ref",
        )
        if self.location_entity_ref is not None and not self.location_entity_ref.logical_id.root.startswith("entity:"):
            raise ValueError("location_entity_ref must be canonical EntityVersion")
        for ref in self.participant_entity_refs:
            if not ref.logical_id.root.startswith("entity:"):
                raise ValueError("participant_entity_refs must be canonical EntityVersion refs")
        expected = scene_spatial_contract_logical_id(self.project_id, self.scene_ref)
        if self.spatial_contract_id != expected:
            raise ValueError(f"spatial_contract_id must be {expected.root}")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.spatial_contract_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="scene", source=self.scene_ref),
            SourceVersionBinding(role="state_snapshot", source=self.state_snapshot_ref),
            SourceVersionBinding(role="approved_state_designation", source=self.approved_state_designation_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"scene_dramatic_beat_{index:03d}", source=ref)
            for index, ref in enumerate(self.scene_dramatic_beat_refs)
        )
        entity_refs: dict[tuple[str, str], VersionRef] = {}
        if self.location_entity_ref is not None:
            entity_refs[_ref_key(self.location_entity_ref)] = self.location_entity_ref
        for ref in self.participant_entity_refs:
            entity_refs[_ref_key(ref)] = ref
        for anchor in self.anchors:
            if anchor.entity_ref is not None:
                entity_refs[_ref_key(anchor.entity_ref)] = anchor.entity_ref
        values.extend(
            SourceVersionBinding(role=f"spatial_entity_{index:03d}", source=entity_refs[key])
            for index, key in enumerate(sorted(entity_refs))
        )
        return tuple(values)


class BlockingPosition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_ref: VersionRef
    start_zone: str
    end_zone: str
    facing: str | None = None

    @field_validator("start_zone", "end_zone")
    @classmethod
    def validate_zone(cls, value: str, info) -> str:
        return _key(value, info.field_name)

    @field_validator("facing")
    @classmethod
    def validate_facing(cls, value: str | None) -> str | None:
        return _optional_trimmed(value, "facing")

    @model_validator(mode="after")
    def validate_entity(self) -> "BlockingPosition":
        if not self.entity_ref.logical_id.root.startswith("entity:"):
            raise ValueError("BlockingPosition entity_ref must be canonical EntityVersion")
        return self


class BlockingMovement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_ref: VersionRef
    path: str
    motivation: str

    @field_validator("path", "motivation")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_entity(self) -> "BlockingMovement":
        if not self.entity_ref.logical_id.root.startswith("entity:"):
            raise ValueError("BlockingMovement entity_ref must be canonical EntityVersion")
        return self


class BlockingPlan(BaseModel):
    """Beat-scoped actor/object movement and spatial execution authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    blocking_plan_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    scene_dramatic_beat_ref: VersionRef
    directing_intent_ref: VersionRef
    spatial_contract_ref: VersionRef
    state_snapshot_ref: VersionRef
    approved_state_designation_ref: VersionRef
    positions: tuple[BlockingPosition, ...] = Field(min_length=1)
    movements: tuple[BlockingMovement, ...] = ()
    eyelines: tuple[str, ...] = ()
    distance_changes: tuple[str, ...] = ()
    dramatic_object_interactions: tuple[str, ...] = ()
    must_preserve: tuple[str, ...] = ()
    forbidden_moves: tuple[str, ...] = ()

    @field_validator(
        "eyelines",
        "distance_changes",
        "dramatic_object_interactions",
        "must_preserve",
        "forbidden_moves",
    )
    @classmethod
    def validate_text_lists(cls, values: tuple[str, ...], info) -> tuple[str, ...]:
        return _unique_text(values, info.field_name)

    @field_validator("positions")
    @classmethod
    def normalize_positions(
        cls,
        values: tuple[BlockingPosition, ...],
    ) -> tuple[BlockingPosition, ...]:
        keys = [_ref_key(value.entity_ref) for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("positions must not duplicate entity refs")
        return tuple(sorted(values, key=lambda value: _ref_key(value.entity_ref)))

    @field_validator("movements")
    @classmethod
    def normalize_movements(
        cls,
        values: tuple[BlockingMovement, ...],
    ) -> tuple[BlockingMovement, ...]:
        keys = [_ref_key(value.entity_ref) for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("movements must not duplicate entity refs")
        return tuple(sorted(values, key=lambda value: _ref_key(value.entity_ref)))

    @model_validator(mode="after")
    def validate_authority(self) -> "BlockingPlan":
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        _project_ref(
            self.scene_dramatic_beat_ref,
            prefix="scene-dramatic-beat:",
            project_id=self.project_id,
            label="scene_dramatic_beat_ref",
        )
        _project_ref(
            self.directing_intent_ref,
            prefix="directing-intent:",
            project_id=self.project_id,
            label="directing_intent_ref",
        )
        _project_ref(
            self.spatial_contract_ref,
            prefix="scene-spatial-contract:",
            project_id=self.project_id,
            label="spatial_contract_ref",
        )
        _project_ref(
            self.state_snapshot_ref,
            prefix="state-snapshot:",
            project_id=self.project_id,
            label="state_snapshot_ref",
        )
        _project_ref(
            self.approved_state_designation_ref,
            prefix="approved-end-state:",
            project_id=self.project_id,
            label="approved_state_designation_ref",
        )
        expected = blocking_plan_logical_id(self.project_id, self.scene_dramatic_beat_ref)
        if self.blocking_plan_id != expected:
            raise ValueError(f"blocking_plan_id must be {expected.root}")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.blocking_plan_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="scene_dramatic_beat", source=self.scene_dramatic_beat_ref),
            SourceVersionBinding(role="directing_intent", source=self.directing_intent_ref),
            SourceVersionBinding(role="scene_spatial_dramatic_contract", source=self.spatial_contract_ref),
            SourceVersionBinding(role="state_snapshot", source=self.state_snapshot_ref),
            SourceVersionBinding(role="approved_state_designation", source=self.approved_state_designation_ref),
        ]
        entity_refs = {
            _ref_key(item.entity_ref): item.entity_ref
            for item in (*self.positions, *self.movements)
        }
        values.extend(
            SourceVersionBinding(role=f"blocking_entity_{index:03d}", source=entity_refs[key])
            for index, key in enumerate(sorted(entity_refs))
        )
        return tuple(values)


class CinematographyDimension(str, Enum):
    FRAMING = "FRAMING"
    SPATIAL = "SPATIAL"
    PERSPECTIVE = "PERSPECTIVE"
    MOVEMENT = "MOVEMENT"
    FOCUS = "FOCUS"
    LIGHTING = "LIGHTING"
    COMPOSITION = "COMPOSITION"


class VisualDecisionBasis(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dimension: CinematographyDimension
    rationale: str
    source_refs: tuple[VersionRef, ...] = Field(min_length=1)

    @field_validator("rationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        return _trimmed(value, "rationale")

    @field_validator("source_refs")
    @classmethod
    def normalize_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        return _unique_refs(values, "decision basis source_refs")


class CinematographyObjective(BaseModel):
    """Visual-language translation; no independent narrative/camera authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    cinematography_objective_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    scene_dramatic_beat_ref: VersionRef
    audience_experience_target_ref: VersionRef
    directing_intent_ref: VersionRef
    spatial_contract_ref: VersionRef
    blocking_plan_ref: VersionRef
    visual_goal: str
    emotional_goal: str
    framing_strategy: str
    spatial_strategy: str
    perspective_strategy: str
    movement_strategy: str
    focus_strategy: str
    lighting_strategy: str
    composition_strategy: str
    continuity_constraints: tuple[str, ...] = ()
    decision_bases: tuple[VisualDecisionBasis, ...] = Field(min_length=7, max_length=7)

    @field_validator(
        "visual_goal",
        "emotional_goal",
        "framing_strategy",
        "spatial_strategy",
        "perspective_strategy",
        "movement_strategy",
        "focus_strategy",
        "lighting_strategy",
        "composition_strategy",
    )
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("continuity_constraints")
    @classmethod
    def validate_constraints(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _unique_text(values, "continuity_constraints")

    @field_validator("decision_bases")
    @classmethod
    def normalize_bases(
        cls,
        values: tuple[VisualDecisionBasis, ...],
    ) -> tuple[VisualDecisionBasis, ...]:
        dimensions = [value.dimension for value in values]
        if len(dimensions) != len(set(dimensions)):
            raise ValueError("decision_bases must contain one basis per visual dimension")
        if set(dimensions) != set(CinematographyDimension):
            raise ValueError("decision_bases must cover every cinematography dimension")
        return tuple(sorted(values, key=lambda value: value.dimension.value))

    @model_validator(mode="after")
    def validate_authority(self) -> "CinematographyObjective":
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        refs = (
            (self.scene_dramatic_beat_ref, "scene-dramatic-beat:", "scene_dramatic_beat_ref"),
            (self.audience_experience_target_ref, "audience-experience:", "audience_experience_target_ref"),
            (self.directing_intent_ref, "directing-intent:", "directing_intent_ref"),
            (self.spatial_contract_ref, "scene-spatial-contract:", "spatial_contract_ref"),
            (self.blocking_plan_ref, "blocking-plan:", "blocking_plan_ref"),
        )
        for ref, prefix, label in refs:
            _project_ref(ref, prefix=prefix, project_id=self.project_id, label=label)
        expected = cinematography_objective_logical_id(
            self.project_id,
            self.scene_dramatic_beat_ref,
        )
        if self.cinematography_objective_id != expected:
            raise ValueError(f"cinematography_objective_id must be {expected.root}")
        allowed = {
            _ref_key(self.active_profile_ref),
            _ref_key(self.scene_dramatic_beat_ref),
            _ref_key(self.audience_experience_target_ref),
            _ref_key(self.directing_intent_ref),
            _ref_key(self.spatial_contract_ref),
            _ref_key(self.blocking_plan_ref),
        }
        for basis in self.decision_bases:
            if any(_ref_key(ref) not in allowed for ref in basis.source_refs):
                raise ValueError(
                    "cinematography decision basis may cite declared upstream authority only"
                )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.cinematography_objective_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return (
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="scene_dramatic_beat", source=self.scene_dramatic_beat_ref),
            SourceVersionBinding(role="audience_experience_target", source=self.audience_experience_target_ref),
            SourceVersionBinding(role="directing_intent", source=self.directing_intent_ref),
            SourceVersionBinding(role="scene_spatial_dramatic_contract", source=self.spatial_contract_ref),
            SourceVersionBinding(role="blocking_plan", source=self.blocking_plan_ref),
        )


DirectingAuthorityValue: TypeAlias = (
    AudienceExperienceTarget
    | DirectingIntent
    | SceneSpatialDramaticContract
    | BlockingPlan
    | CinematographyObjective
)


class DirectingAuthorityArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: DirectingAuthorityValue

    @model_validator(mode="after")
    def validate_artifact(self) -> "DirectingAuthorityArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("directing artifact logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("directing artifact version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError("directing artifact provenance must exactly bind declared sources")
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(
            logical_id=self.metadata.logical_id,
            version_id=self.metadata.version_id,
        )


def build_directing_provenance(
    value: DirectingAuthorityValue,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    rule_version: VersionRef | None = None,
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=value.source_bindings(),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        rule_version=rule_version,
        correlation_id=correlation_id,
    )


class DirectingAuthorityRepository:
    """Shared exact-version repository for the ADR-0019 authority chain."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)
        self.traces = NarrativeTraceRepository(writer)
        self.states = StateSnapshotRepository(writer)

    async def create_audience_experience_target(
        self,
        *,
        value: AudienceExperienceTarget,
        provenance: Provenance,
        created_at: datetime,
    ) -> DirectingAuthorityArtifact:
        await self._assert_audience_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_audience_experience_target(
        self,
        *,
        value: AudienceExperienceTarget,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[DirectingAuthorityArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_audience_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="AudienceExperienceTarget",
            cause="AudienceExperienceTarget revision",
            scope="audience_directing_cinematography_descendants",
            repair="Recompute dependent directing/blocking/cinematography/shot planning from the new audience target.",
        )

    async def create_directing_intent(
        self,
        *,
        value: DirectingIntent,
        provenance: Provenance,
        created_at: datetime,
    ) -> DirectingAuthorityArtifact:
        await self._assert_directing_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_directing_intent(
        self,
        *,
        value: DirectingIntent,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[DirectingAuthorityArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_directing_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="DirectingIntent",
            cause="DirectingIntent revision",
            scope="directing_blocking_cinematography_descendants",
            repair="Recompute dependent blocking/cinematography/shot planning from the new directing intent.",
        )

    async def create_spatial_contract(
        self,
        *,
        value: SceneSpatialDramaticContract,
        provenance: Provenance,
        created_at: datetime,
    ) -> DirectingAuthorityArtifact:
        await self._assert_spatial_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_spatial_contract(
        self,
        *,
        value: SceneSpatialDramaticContract,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[DirectingAuthorityArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_spatial_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="SceneSpatialDramaticContract",
            cause="SceneSpatialDramaticContract revision",
            scope="spatial_blocking_cinematography_descendants",
            repair="Recompute dependent blocking/camera/composition/shot realization from the new spatial contract.",
        )

    async def create_blocking_plan(
        self,
        *,
        value: BlockingPlan,
        provenance: Provenance,
        created_at: datetime,
    ) -> DirectingAuthorityArtifact:
        await self._assert_blocking_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_blocking_plan(
        self,
        *,
        value: BlockingPlan,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[DirectingAuthorityArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_blocking_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="BlockingPlan",
            cause="BlockingPlan revision",
            scope="blocking_cinematography_shot_descendants",
            repair="Recompute dependent cinematography/camera/composition/shot realization from the new blocking plan.",
        )

    async def create_cinematography_objective(
        self,
        *,
        value: CinematographyObjective,
        provenance: Provenance,
        created_at: datetime,
    ) -> DirectingAuthorityArtifact:
        await self._assert_cinematography_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_cinematography_objective(
        self,
        *,
        value: CinematographyObjective,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[DirectingAuthorityArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_cinematography_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="CinematographyObjective",
            cause="CinematographyObjective revision",
            scope="cinematography_shot_descendants",
            repair="Recompute dependency-reachable shot planning/realization from the new cinematography objective.",
        )

    async def get_audience_experience_target(
        self,
        ref: VersionRef,
    ) -> DirectingAuthorityArtifact | None:
        return await self._get_typed(ref, AudienceExperienceTarget, "audience-experience:")

    async def get_directing_intent(self, ref: VersionRef) -> DirectingAuthorityArtifact | None:
        return await self._get_typed(ref, DirectingIntent, "directing-intent:")

    async def get_spatial_contract(self, ref: VersionRef) -> DirectingAuthorityArtifact | None:
        return await self._get_typed(ref, SceneSpatialDramaticContract, "scene-spatial-contract:")

    async def get_blocking_plan(self, ref: VersionRef) -> DirectingAuthorityArtifact | None:
        return await self._get_typed(ref, BlockingPlan, "blocking-plan:")

    async def get_cinematography_objective(
        self,
        ref: VersionRef,
    ) -> DirectingAuthorityArtifact | None:
        return await self._get_typed(ref, CinematographyObjective, "cinematography-objective:")

    async def _create_approved(
        self,
        value: DirectingAuthorityValue,
        provenance: Provenance,
        created_at: datetime,
    ) -> DirectingAuthorityArtifact:
        self._assert_provenance(value, provenance)
        metadata = SemanticRecordMetadata(
            logical_id=value.logical_id,
            version_id=value.version_id,
            provenance=provenance,
            created_at=created_at,
        )
        stored = await self.versions.create_initial(
            metadata=metadata,
            payload=value.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        artifact = DirectingAuthorityArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(artifact)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )
        return artifact

    async def _revise_approved(
        self,
        *,
        value: DirectingAuthorityValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
        label: str,
        cause: str,
        scope: str,
        repair: str,
    ) -> tuple[DirectingAuthorityArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise DirectingIdentityError(f"{label} revision must preserve logical identity")
        await self._assert_current(predecessor, f"{label} predecessor", _ACCEPTED)
        previous = await self.versions.get_version(predecessor)
        if previous is None:
            raise DirectingIdentityError(f"{label} predecessor does not exist")
        previous_payload = dict(previous.payload)
        current_payload = value.model_dump(mode="json")
        previous_payload.pop("version_id", None)
        current_payload.pop("version_id", None)
        if previous_payload == current_payload:
            raise DirectingIdentityError(f"{label} successor requires a semantic/source change")
        self._assert_provenance(value, provenance)
        pointer = await self.versions.get_current(value.logical_id)
        if (
            pointer is None
            or pointer.version_id != predecessor.version_id
            or pointer.status not in _ACCEPTED
            or pointer.revision != expected_revision
        ):
            raise DirectingIdentityError(
                f"{label} successor requires exact current accepted predecessor/revision"
            )
        metadata = SemanticRecordMetadata(
            logical_id=value.logical_id,
            version_id=value.version_id,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
        )
        stored = await self.versions.create_successor(
            metadata=metadata,
            payload=value.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        artifact = DirectingAuthorityArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(artifact)
        records = await self.invalidations.create_for_change(
            cause=cause,
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope=scope,
            repair_or_recompute_requirement=repair,
        )
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )
        return artifact, tuple(records)

    async def _get_typed(
        self,
        ref: VersionRef,
        model,
        prefix: str,
    ) -> DirectingAuthorityArtifact | None:
        if not ref.logical_id.root.startswith(prefix):
            raise DirectingIdentityError(f"expected {prefix.rstrip(':')} ref")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = model.model_validate(stored.payload)
        if value.logical_id != ref.logical_id:
            raise DirectingIdentityError("stored directing payload logical identity mismatch")
        return DirectingAuthorityArtifact(metadata=stored.metadata, value=value)

    async def _register_dependencies(self, artifact: DirectingAuthorityArtifact) -> None:
        grouped: dict[tuple[str, str], list[str]] = {}
        refs: dict[tuple[str, str], VersionRef] = {}
        for binding in artifact.value.source_bindings():
            if binding.source == artifact.ref:
                continue
            key = _ref_key(binding.source)
            refs[key] = binding.source
            grouped.setdefault(key, []).append(binding.role)
        for key in sorted(grouped):
            source = refs[key]
            edge_type = (
                profile_path_edge_type("*")
                if source == artifact.value.active_profile_ref
                else "directing_authority_input"
            )
            await self.graph.create_edge(
                source=source,
                dependent=artifact.ref,
                edge_type=edge_type,
                dependency_reason=" + ".join(sorted(set(grouped[key]))),
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    def _assert_provenance(
        self,
        value: DirectingAuthorityValue,
        provenance: Provenance,
    ) -> None:
        if provenance.source_versions != value.source_bindings():
            raise DirectingAuthorityError(
                "directing provenance must exactly bind declared source versions"
            )

    async def _assert_current(
        self,
        ref: VersionRef,
        label: str,
        allowed: set[LifecycleState],
    ) -> None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise DirectingGateBlocked(f"{label} exact version does not exist")
        pointer = await self.versions.get_current(ref.logical_id)
        if pointer is None or pointer.version_id != ref.version_id or pointer.status not in allowed:
            raise DirectingGateBlocked(f"{label} is not exact current accepted authority")
        unresolved = await self.invalidations.list_unresolved()
        if any(
            record.affected_object_id == ref.logical_id
            and record.affected_object_version == ref.version_id
            for record in unresolved
        ):
            raise DirectingGateBlocked(f"{label} has unresolved invalidation")

    async def _load(self, ref: VersionRef, model, label: str):
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise DirectingGateBlocked(f"{label} exact version does not exist")
        try:
            return model.model_validate(stored.payload)
        except Exception as exc:
            raise DirectingGateBlocked(f"{label} payload does not match canonical contract") from exc

    async def _assert_profile(
        self,
        project_id: LogicalId,
        ref: VersionRef,
    ) -> ActiveProductionProfile:
        if ref.logical_id != _active_profile_id(project_id):
            raise DirectingGateBlocked("ActiveProductionProfile belongs to a different project")
        await self._assert_current(ref, "ActiveProductionProfile", {LifecycleState.LOCKED})
        profile = await self._load(ref, ActiveProductionProfile, "ActiveProductionProfile")
        if profile.project_id != project_id:
            raise DirectingGateBlocked("ActiveProductionProfile project mismatch")
        return profile

    async def _assert_scene(
        self,
        project_id: LogicalId,
        ref: VersionRef,
        profile_ref: VersionRef,
    ) -> Scene:
        await self._assert_current(ref, "Scene", _ACCEPTED)
        scene = await self._load(ref, Scene, "Scene")
        if scene.project_id != project_id or scene.active_profile_ref != profile_ref:
            raise DirectingGateBlocked("Scene project/profile lineage mismatch")
        return scene

    async def _assert_beat(
        self,
        project_id: LogicalId,
        ref: VersionRef,
        profile_ref: VersionRef,
    ) -> SceneDramaticBeat:
        await self._assert_current(ref, "SceneDramaticBeat", _ACCEPTED)
        beat = await self._load(ref, SceneDramaticBeat, "SceneDramaticBeat")
        if beat.project_id != project_id or beat.active_profile_ref != profile_ref:
            raise DirectingGateBlocked("SceneDramaticBeat project/profile lineage mismatch")
        return beat

    async def _assert_trace(
        self,
        *,
        project_id: LogicalId,
        beat_ref: VersionRef,
        trace_ref: VersionRef,
    ) -> None:
        trace = await self.traces.get_trace(trace_ref)
        if trace is None:
            raise DirectingGateBlocked("NarrativeTrace exact version does not exist")
        if (
            trace.value.project_id != project_id
            or trace.value.artifact_type is not NarrativeArtifactType.SCENE_DRAMATIC_BEAT
            or trace.value.traced_ref != beat_ref
        ):
            raise DirectingGateBlocked("NarrativeTrace does not trace the required SceneDramaticBeat")
        if await self.traces.trace_state(trace_ref) is not NarrativeTraceState.CURRENT:
            raise DirectingGateBlocked("NarrativeTrace is stale/superseded/invalidated")

    async def _assert_script_lock(
        self,
        *,
        project_id: LogicalId,
        profile_ref: VersionRef,
        ref: VersionRef,
    ) -> ScriptLockManifest:
        if ref.logical_id != script_lock_logical_id(project_id):
            raise DirectingGateBlocked("ScriptLock belongs to a different project")
        await self._assert_current(ref, "ScriptLock", {LifecycleState.LOCKED})
        lock = await self._load(ref, ScriptLockManifest, "ScriptLock")
        if lock.project_id != project_id or lock.active_profile_ref != profile_ref:
            raise DirectingGateBlocked("ScriptLock project/profile lineage mismatch")
        return lock

    async def _assert_entity(
        self,
        *,
        project_id: LogicalId,
        ref: VersionRef,
        label: str,
    ) -> EntityVersion:
        if not ref.logical_id.root.startswith("entity:"):
            raise DirectingGateBlocked(f"{label} must reference canonical EntityVersion")
        await self._assert_current(ref, label, _ACCEPTED)
        entity = await self._load(ref, EntityVersion, label)
        if project_id not in entity.project_ids:
            raise DirectingGateBlocked(f"{label} belongs to a different project")
        return entity

    async def _scene_character_entities(
        self,
        *,
        project_id: LogicalId,
        scene: Scene,
    ) -> dict[tuple[str, str], VersionRef]:
        declared: dict[tuple[str, str], VersionRef] = {}
        for character_model_ref in scene.character_refs:
            await self._assert_current(
                character_model_ref,
                "Scene CharacterModelVersion",
                _ACCEPTED,
            )
            model = await self._load(
                character_model_ref,
                CharacterModelVersion,
                "Scene CharacterModelVersion",
            )
            if model.project_id != project_id:
                raise DirectingGateBlocked(
                    "Scene CharacterModelVersion belongs to a different project"
                )
            await self._assert_entity(
                project_id=project_id,
                ref=model.character_ref,
                label="Scene character EntityVersion",
            )
            declared[_ref_key(model.character_ref)] = model.character_ref
        return declared

    async def _assert_performance_state(
        self,
        *,
        project_id: LogicalId,
        ref: VersionRef,
    ) -> tuple[VersionRef, ...]:
        await self._assert_current(ref, "performance state", _ACCEPTED)
        root = ref.logical_id.root
        if root.startswith("character-model:"):
            value = await self._load(ref, CharacterModelVersion, "CharacterModelVersion")
            if value.project_id != project_id:
                raise DirectingGateBlocked("CharacterModelVersion project mismatch")
            await self._assert_entity(
                project_id=project_id,
                ref=value.character_ref,
                label="performance-state character EntityVersion",
            )
            return (value.character_ref,)
        if root.startswith("relationship:"):
            value = await self._load(ref, RelationshipState, "RelationshipState")
            if value.project_id != project_id:
                raise DirectingGateBlocked("RelationshipState project mismatch")
            for participant_ref in value.participant_refs:
                await self._assert_entity(
                    project_id=project_id,
                    ref=participant_ref,
                    label="relationship participant EntityVersion",
                )
            return value.participant_refs
        if root.startswith("character-knowledge:"):
            value = await self._load(ref, CharacterKnowledgeState, "CharacterKnowledgeState")
            if value.project_id != project_id:
                raise DirectingGateBlocked("CharacterKnowledgeState project mismatch")
            await self._assert_entity(
                project_id=project_id,
                ref=value.character_ref,
                label="knowledge-state character EntityVersion",
            )
            return (value.character_ref,)
        raise DirectingGateBlocked("unsupported performance-state authority")

    async def _assert_state_pair(
        self,
        *,
        project_id: LogicalId,
        state_ref: VersionRef,
        designation_ref: VersionRef,
    ) -> set[tuple[str, str]]:
        designation = await self.states.assert_propagatable(state_ref)
        if designation.value.project_id != project_id:
            raise DirectingGateBlocked("StateSnapshot belongs to a different project")
        if designation.ref != designation_ref:
            raise DirectingGateBlocked(
                "approved_state_designation_ref does not authorize the exact StateSnapshot"
            )
        snapshot = await self.states.get_version(state_ref)
        if snapshot is None:
            raise DirectingGateBlocked("approved StateSnapshot version disappeared")
        return {
            _ref_key(fact.subject_ref)
            for fact in snapshot.value.facts
            if fact.subject_ref is not None
        }

    async def _assert_audience_inputs(self, value: AudienceExperienceTarget) -> None:
        await self._assert_profile(value.project_id, value.active_profile_ref)
        await self._assert_beat(
            value.project_id,
            value.scene_dramatic_beat_ref,
            value.active_profile_ref,
        )
        await self._assert_trace(
            project_id=value.project_id,
            beat_ref=value.scene_dramatic_beat_ref,
            trace_ref=value.narrative_trace_ref,
        )

    async def _assert_directing_inputs(self, value: DirectingIntent) -> None:
        await self._assert_profile(value.project_id, value.active_profile_ref)
        beat = await self._assert_beat(
            value.project_id,
            value.scene_dramatic_beat_ref,
            value.active_profile_ref,
        )
        scene = await self._assert_scene(
            value.project_id,
            beat.scene_ref,
            value.active_profile_ref,
        )
        declared_scene_entities = await self._scene_character_entities(
            project_id=value.project_id,
            scene=scene,
        )
        await self._assert_script_lock(
            project_id=value.project_id,
            profile_ref=value.active_profile_ref,
            ref=value.script_lock_ref,
        )
        await self._assert_current(
            value.audience_experience_target_ref,
            "AudienceExperienceTarget",
            _ACCEPTED,
        )
        audience = await self._load(
            value.audience_experience_target_ref,
            AudienceExperienceTarget,
            "AudienceExperienceTarget",
        )
        if (
            audience.project_id != value.project_id
            or audience.active_profile_ref != value.active_profile_ref
            or audience.scene_dramatic_beat_ref != value.scene_dramatic_beat_ref
        ):
            raise DirectingGateBlocked("AudienceExperienceTarget lineage mismatch")
        for ref in value.performance_state_refs:
            state_entities = await self._assert_performance_state(
                project_id=value.project_id,
                ref=ref,
            )
            if any(_ref_key(entity_ref) not in declared_scene_entities for entity_ref in state_entities):
                raise DirectingGateBlocked(
                    "performance state references character not declared by canonical Scene"
                )
        for item in value.actor_directions:
            await self._assert_entity(
                project_id=value.project_id,
                ref=item.entity_ref,
                label="ActorDirection entity",
            )
            if _ref_key(item.entity_ref) not in declared_scene_entities:
                raise DirectingGateBlocked(
                    "ActorDirection entity is not declared by canonical Scene"
                )

    async def _assert_spatial_inputs(self, value: SceneSpatialDramaticContract) -> None:
        await self._assert_profile(value.project_id, value.active_profile_ref)
        scene = await self._assert_scene(
            value.project_id,
            value.scene_ref,
            value.active_profile_ref,
        )
        declared_scene_entities = await self._scene_character_entities(
            project_id=value.project_id,
            scene=scene,
        )
        for beat_ref in value.scene_dramatic_beat_refs:
            beat = await self._assert_beat(
                value.project_id,
                beat_ref,
                value.active_profile_ref,
            )
            if beat.scene_ref != value.scene_ref:
                raise DirectingGateBlocked(
                    "SceneSpatialDramaticContract beat belongs to a different Scene"
                )
        state_subject_entities = await self._assert_state_pair(
            project_id=value.project_id,
            state_ref=value.state_snapshot_ref,
            designation_ref=value.approved_state_designation_ref,
        )
        if value.location_entity_ref is not None:
            location_entity = await self._assert_entity(
                project_id=value.project_id,
                ref=value.location_entity_ref,
                label="spatial location EntityVersion",
            )
            if location_entity.kind is not EntityKind.LOCATION:
                raise DirectingGateBlocked(
                    "location_entity_ref must bind a canonical LOCATION EntityVersion"
                )
        for ref in value.participant_entity_refs:
            await self._assert_entity(
                project_id=value.project_id,
                ref=ref,
                label="spatial participant EntityVersion",
            )
            if _ref_key(ref) not in declared_scene_entities:
                raise DirectingGateBlocked(
                    "spatial participant is not declared by canonical Scene"
                )
        for anchor in value.anchors:
            if anchor.entity_ref is None:
                continue
            await self._assert_entity(
                project_id=value.project_id,
                ref=anchor.entity_ref,
                label="spatial anchor EntityVersion",
            )
            key = _ref_key(anchor.entity_ref)
            if key not in declared_scene_entities and key not in state_subject_entities:
                raise DirectingGateBlocked(
                    "spatial anchor EntityVersion is not authorized by canonical Scene or approved StateSnapshot"
                )

    async def _assert_blocking_inputs(self, value: BlockingPlan) -> None:
        await self._assert_profile(value.project_id, value.active_profile_ref)
        beat = await self._assert_beat(
            value.project_id,
            value.scene_dramatic_beat_ref,
            value.active_profile_ref,
        )
        await self._assert_current(value.directing_intent_ref, "DirectingIntent", _ACCEPTED)
        directing = await self._load(
            value.directing_intent_ref,
            DirectingIntent,
            "DirectingIntent",
        )
        if (
            directing.project_id != value.project_id
            or directing.active_profile_ref != value.active_profile_ref
            or directing.scene_dramatic_beat_ref != value.scene_dramatic_beat_ref
        ):
            raise DirectingGateBlocked("DirectingIntent lineage mismatch")
        await self._assert_current(
            value.spatial_contract_ref,
            "SceneSpatialDramaticContract",
            _ACCEPTED,
        )
        spatial = await self._load(
            value.spatial_contract_ref,
            SceneSpatialDramaticContract,
            "SceneSpatialDramaticContract",
        )
        if (
            spatial.project_id != value.project_id
            or spatial.active_profile_ref != value.active_profile_ref
            or spatial.scene_ref != beat.scene_ref
            or value.scene_dramatic_beat_ref not in spatial.scene_dramatic_beat_refs
            or spatial.state_snapshot_ref != value.state_snapshot_ref
            or spatial.approved_state_designation_ref
            != value.approved_state_designation_ref
        ):
            raise DirectingGateBlocked("BlockingPlan spatial/state lineage mismatch")
        await self._assert_state_pair(
            project_id=value.project_id,
            state_ref=value.state_snapshot_ref,
            designation_ref=value.approved_state_designation_ref,
        )
        allowed_blocking_entities = {_ref_key(ref) for ref in spatial.participant_entity_refs}
        allowed_blocking_entities.update(
            _ref_key(anchor.entity_ref)
            for anchor in spatial.anchors
            if anchor.entity_ref is not None
        )
        zone_keys = {zone.zone_key for zone in spatial.zones}
        for item in value.positions:
            if item.start_zone not in zone_keys or item.end_zone not in zone_keys:
                raise DirectingGateBlocked("BlockingPosition references undeclared spatial zone")
            await self._assert_entity(
                project_id=value.project_id,
                ref=item.entity_ref,
                label="BlockingPosition entity",
            )
            if _ref_key(item.entity_ref) not in allowed_blocking_entities:
                raise DirectingGateBlocked(
                    "BlockingPosition entity is not declared by SceneSpatialDramaticContract"
                )
        for movement in value.movements:
            await self._assert_entity(
                project_id=value.project_id,
                ref=movement.entity_ref,
                label="BlockingMovement entity",
            )
            if _ref_key(movement.entity_ref) not in allowed_blocking_entities:
                raise DirectingGateBlocked(
                    "BlockingMovement entity is not declared by SceneSpatialDramaticContract"
                )

    async def _assert_cinematography_inputs(self, value: CinematographyObjective) -> None:
        await self._assert_profile(value.project_id, value.active_profile_ref)
        beat = await self._assert_beat(
            value.project_id,
            value.scene_dramatic_beat_ref,
            value.active_profile_ref,
        )
        await self._assert_current(
            value.audience_experience_target_ref,
            "AudienceExperienceTarget",
            _ACCEPTED,
        )
        audience = await self._load(
            value.audience_experience_target_ref,
            AudienceExperienceTarget,
            "AudienceExperienceTarget",
        )
        await self._assert_current(value.directing_intent_ref, "DirectingIntent", _ACCEPTED)
        directing = await self._load(value.directing_intent_ref, DirectingIntent, "DirectingIntent")
        await self._assert_current(
            value.spatial_contract_ref,
            "SceneSpatialDramaticContract",
            _ACCEPTED,
        )
        spatial = await self._load(
            value.spatial_contract_ref,
            SceneSpatialDramaticContract,
            "SceneSpatialDramaticContract",
        )
        await self._assert_current(value.blocking_plan_ref, "BlockingPlan", _ACCEPTED)
        blocking = await self._load(value.blocking_plan_ref, BlockingPlan, "BlockingPlan")
        if (
            audience.project_id != value.project_id
            or audience.active_profile_ref != value.active_profile_ref
            or audience.scene_dramatic_beat_ref != value.scene_dramatic_beat_ref
            or directing.project_id != value.project_id
            or directing.active_profile_ref != value.active_profile_ref
            or directing.scene_dramatic_beat_ref != value.scene_dramatic_beat_ref
            or directing.audience_experience_target_ref
            != value.audience_experience_target_ref
            or spatial.project_id != value.project_id
            or spatial.active_profile_ref != value.active_profile_ref
            or spatial.scene_ref != beat.scene_ref
            or value.scene_dramatic_beat_ref not in spatial.scene_dramatic_beat_refs
            or blocking.project_id != value.project_id
            or blocking.active_profile_ref != value.active_profile_ref
            or blocking.scene_dramatic_beat_ref != value.scene_dramatic_beat_ref
            or blocking.directing_intent_ref != value.directing_intent_ref
            or blocking.spatial_contract_ref != value.spatial_contract_ref
        ):
            raise DirectingGateBlocked(
                "CinematographyObjective upstream authority chain is contradictory"
            )

    async def trace_ancestors(self, ref: VersionRef):
        return tuple(await self.graph.ancestors(ref))

    async def trace_descendants(self, ref: VersionRef):
        return tuple(await self.graph.descendants(ref))
