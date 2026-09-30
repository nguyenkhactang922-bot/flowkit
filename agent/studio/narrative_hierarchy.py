"""Canonical narrative hierarchy for IMP-025.

Authority boundaries:
- MacroStoryBeat, Sequence, Scene, SceneDramaticBeat are canonical narrative truth.
- SequencePlan, SceneBudget, SceneListManifest and SceneBreakdownManifest are
  planning/projection artifacts only.
- Legacy FlowKit operational Scene is intentionally not imported here.
- There is no generic persistent Beat canonical entity.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from .active_profile import ActiveProductionProfile
from .character_state import (
    CharacterKnowledgeState,
    CharacterModelVersion,
    RelationshipState,
)
from .invalidation import (
    DependencyGraphRepository,
    InvalidationRecord,
    InvalidationRepository,
)
from .primitives import (
    GateVerdict,
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    VersionId,
    VersionRef,
)
from .story_core import (
    CausalStoryGraph,
    StoryCorePhase,
    StoryCoreVersion,
    conflict_logical_id,
    stakes_logical_id,
    story_core_logical_id,
    story_graph_logical_id,
)
from .structure_planning import (
    BudgetLevel,
    DurationBudget,
    MacroBeatSheet,
    StructureProfile,
    duration_budget_logical_id,
    macro_beat_sheet_logical_id,
    structure_profile_logical_id,
)
from .versioning import CurrentPointerNotFound, CurrentVersionPointer, VersionRepository


_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class NarrativeHierarchyError(ValueError):
    """Base error for canonical narrative hierarchy operations."""


class NarrativeHierarchyGateBlocked(NarrativeHierarchyError):
    """Raised when an exact-version or semantic gate fails closed."""


class NarrativeHierarchyIdentityError(NarrativeHierarchyError):
    """Raised when identity/provenance crosses canonical ownership."""


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _key(value: str, label: str) -> str:
    value = _trimmed(value, label)
    if not _KEY_RE.fullmatch(value):
        raise ValueError(
            f"{label} must use only letters, digits, '.', '_' or '-'"
        )
    return value


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return (ref.logical_id.root, ref.version_id.root)


def _active_profile_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"active-profile:{project_id.root}")


def macro_story_beat_logical_id(
    project_id: LogicalId,
    beat_key: str,
) -> LogicalId:
    return LogicalId(f"macro-story-beat:{project_id.root}:{_key(beat_key, 'beat_key')}")


def sequence_plan_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"sequence-plan:{project_id.root}")


def sequence_logical_id(
    project_id: LogicalId,
    sequence_key: str,
) -> LogicalId:
    return LogicalId(f"sequence:{project_id.root}:{_key(sequence_key, 'sequence_key')}")


def scene_budget_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"scene-budget:{project_id.root}")


def scene_logical_id(
    project_id: LogicalId,
    scene_key: str,
) -> LogicalId:
    return LogicalId(f"scene:{project_id.root}:{_key(scene_key, 'scene_key')}")


def scene_list_manifest_logical_id(
    project_id: LogicalId,
    sequence_key: str,
) -> LogicalId:
    return LogicalId(
        f"scene-list-manifest:{project_id.root}:{_key(sequence_key, 'sequence_key')}"
    )


def scene_dramatic_beat_logical_id(
    project_id: LogicalId,
    scene_key: str,
    beat_key: str,
) -> LogicalId:
    return LogicalId(
        "scene-dramatic-beat:"
        f"{project_id.root}:{_key(scene_key, 'scene_key')}:{_key(beat_key, 'beat_key')}"
    )


def scene_breakdown_manifest_logical_id(
    project_id: LogicalId,
    scene_key: str,
) -> LogicalId:
    return LogicalId(
        f"scene-breakdown-manifest:{project_id.root}:{_key(scene_key, 'scene_key')}"
    )


def _require_exact_ref(ref: VersionRef, expected: LogicalId, label: str) -> None:
    if ref.logical_id != expected:
        raise ValueError(f"{label} must reference canonical object for same project")


def _is_project_scoped(
    ref: VersionRef,
    *,
    prefix: str,
    project_id: LogicalId,
) -> bool:
    base = f"{prefix}{project_id.root}"
    root = ref.logical_id.root
    return root == base or root.startswith(base + ":")


def _require_project_scoped(
    ref: VersionRef,
    *,
    prefix: str,
    project_id: LogicalId,
    label: str,
) -> None:
    if not _is_project_scoped(ref, prefix=prefix, project_id=project_id):
        raise ValueError(f"{label} must belong to the same project")


class MacroStoryBeat(BaseModel):
    """First-class macro structural dramatic movement; never a camera unit."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    beat_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    story_core_ref: VersionRef
    story_graph_ref: VersionRef
    conflict_ref: VersionRef
    stakes_ref: VersionRef
    structure_profile_ref: VersionRef
    dramatic_role: str
    dramatic_change: str
    cause: str
    consequence: str
    structural_necessity_reason: str

    @field_validator(
        "beat_key",
        "dramatic_role",
        "dramatic_change",
        "cause",
        "consequence",
        "structural_necessity_reason",
    )
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        if info.field_name == "beat_key":
            return _key(value, "beat_key")
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_authority(self) -> "MacroStoryBeat":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.story_core_ref,
            story_core_logical_id(self.project_id),
            "story_core_ref",
        )
        _require_exact_ref(
            self.story_graph_ref,
            story_graph_logical_id(self.project_id),
            "story_graph_ref",
        )
        _require_exact_ref(
            self.conflict_ref,
            conflict_logical_id(self.project_id),
            "conflict_ref",
        )
        _require_exact_ref(
            self.stakes_ref,
            stakes_logical_id(self.project_id),
            "stakes_ref",
        )
        _require_exact_ref(
            self.structure_profile_ref,
            structure_profile_logical_id(self.project_id),
            "structure_profile_ref",
        )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return macro_story_beat_logical_id(self.project_id, self.beat_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return (
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="locked_story_core", source=self.story_core_ref),
            SourceVersionBinding(role="causal_story_graph", source=self.story_graph_ref),
            SourceVersionBinding(role="conflict_model", source=self.conflict_ref),
            SourceVersionBinding(role="stakes_model", source=self.stakes_ref),
            SourceVersionBinding(role="structure_profile", source=self.structure_profile_ref),
        )


class SequencePlanEntry(BaseModel):
    """Planning row only; plan_entry_id is not canonical sequence identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    plan_entry_id: str
    order_index: int = Field(ge=0)
    macro_story_beat_ref: VersionRef
    duration_allocation_id: str
    runtime_budget_seconds: int = Field(gt=0)
    sequence_ref: VersionRef | None = None

    @field_validator("plan_entry_id", "duration_allocation_id")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _key(value, info.field_name)

    @model_validator(mode="after")
    def validate_refs(self) -> "SequencePlanEntry":
        if not self.macro_story_beat_ref.logical_id.root.startswith(
            "macro-story-beat:"
        ):
            raise ValueError(
                "SequencePlan entry macro_story_beat_ref must be canonical MacroStoryBeat"
            )
        if (
            self.sequence_ref is not None
            and not self.sequence_ref.logical_id.root.startswith("sequence:")
        ):
            raise ValueError(
                "SequencePlan sequence_ref must be canonical Sequence when present"
            )
        return self


class SequencePlan(BaseModel):
    """Planning/projection artifact; never Sequence narrative truth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    structure_profile_ref: VersionRef
    macro_beat_sheet_ref: VersionRef
    duration_budget_ref: VersionRef
    entries: tuple[SequencePlanEntry, ...] = Field(min_length=1)
    target_count: int = Field(gt=0)
    runtime_budget_seconds: int = Field(gt=0)
    causality_verdict: GateVerdict = GateVerdict.PASS
    causality_evidence: tuple[str, ...] = Field(min_length=1)

    @field_validator("causality_evidence")
    @classmethod
    def validate_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_trimmed(value, "causality_evidence") for value in values)

    @model_validator(mode="after")
    def validate_plan(self) -> "SequencePlan":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.structure_profile_ref,
            structure_profile_logical_id(self.project_id),
            "structure_profile_ref",
        )
        _require_exact_ref(
            self.macro_beat_sheet_ref,
            macro_beat_sheet_logical_id(self.project_id),
            "macro_beat_sheet_ref",
        )
        _require_exact_ref(
            self.duration_budget_ref,
            duration_budget_logical_id(self.project_id),
            "duration_budget_ref",
        )
        if self.causality_verdict is not GateVerdict.PASS:
            raise ValueError("persisted SequencePlan must pass causality gate")

        indexes = [entry.order_index for entry in self.entries]
        if indexes != list(range(len(self.entries))):
            raise ValueError("SequencePlan order_index values must be contiguous")
        ids = [entry.plan_entry_id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("SequencePlan plan_entry_id values must be unique")
        allocation_ids = [entry.duration_allocation_id for entry in self.entries]
        if len(allocation_ids) != len(set(allocation_ids)):
            raise ValueError("SequencePlan duration allocation IDs must be unique")
        if self.target_count != len(self.entries):
            raise ValueError("SequencePlan target_count must equal entry count")
        if sum(item.runtime_budget_seconds for item in self.entries) != self.runtime_budget_seconds:
            raise ValueError(
                "SequencePlan runtime_budget_seconds must equal entry budget sum"
            )
        for entry in self.entries:
            _require_project_scoped(
                entry.macro_story_beat_ref,
                prefix="macro-story-beat:",
                project_id=self.project_id,
                label="SequencePlan macro_story_beat_ref",
            )
            if entry.sequence_ref is not None:
                _require_project_scoped(
                    entry.sequence_ref,
                    prefix="sequence:",
                    project_id=self.project_id,
                    label="SequencePlan sequence_ref",
                )
        seq_refs = [
            _ref_key(item.sequence_ref)
            for item in self.entries
            if item.sequence_ref is not None
        ]
        if len(seq_refs) != len(set(seq_refs)):
            raise ValueError("SequencePlan sequence_ref values must be unique")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return sequence_plan_logical_id(self.project_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="structure_profile", source=self.structure_profile_ref),
            SourceVersionBinding(role="macro_beat_sheet", source=self.macro_beat_sheet_ref),
            SourceVersionBinding(role="duration_budget", source=self.duration_budget_ref),
        ]
        values.extend(
            SourceVersionBinding(
                role=f"macro_story_beat_{index:03d}",
                source=entry.macro_story_beat_ref,
            )
            for index, entry in enumerate(self.entries)
        )
        # sequence_ref is a child projection binding, not an authority dependency;
        # excluding it avoids a SequencePlan <-> Sequence dependency cycle.
        return tuple(values)


class Sequence(BaseModel):
    """Canonical dramatic progression container."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    sequence_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    sequence_plan_ref: VersionRef
    structure_profile_ref: VersionRef
    plan_entry_id: str
    macro_story_beat_refs: tuple[VersionRef, ...] = Field(min_length=1)
    objective: str
    escalation: str
    major_turn: str
    opening_state: str
    closing_state: str
    next_sequence_enablement: str

    @field_validator(
        "sequence_key",
        "plan_entry_id",
        "objective",
        "escalation",
        "major_turn",
        "opening_state",
        "closing_state",
        "next_sequence_enablement",
    )
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        if info.field_name in {"sequence_key", "plan_entry_id"}:
            return _key(value, info.field_name)
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_sequence(self) -> "Sequence":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.sequence_plan_ref,
            sequence_plan_logical_id(self.project_id),
            "sequence_plan_ref",
        )
        _require_exact_ref(
            self.structure_profile_ref,
            structure_profile_logical_id(self.project_id),
            "structure_profile_ref",
        )
        for ref in self.macro_story_beat_refs:
            _require_project_scoped(
                ref,
                prefix="macro-story-beat:",
                project_id=self.project_id,
                label="macro_story_beat_refs",
            )
        keys = [_ref_key(ref) for ref in self.macro_story_beat_refs]
        if len(keys) != len(set(keys)):
            raise ValueError("Sequence macro_story_beat_refs must be unique")
        if self.opening_state == self.closing_state:
            raise ValueError("Sequence must produce a closing-state change")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return sequence_logical_id(self.project_id, self.sequence_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="sequence_plan", source=self.sequence_plan_ref),
            SourceVersionBinding(role="structure_profile", source=self.structure_profile_ref),
        ]
        values.extend(
            SourceVersionBinding(
                role=f"macro_story_beat_{index:03d}",
                source=ref,
            )
            for index, ref in enumerate(self.macro_story_beat_refs)
        )
        return tuple(values)


class SequenceSceneAllocation(BaseModel):
    """SceneBudget allocation for one accepted Sequence; owns no scene IDs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    plan_entry_id: str
    sequence_ref: VersionRef
    minimum_scene_count: int = Field(ge=1)
    preferred_scene_count: int = Field(ge=1)
    maximum_scene_count: int = Field(ge=1)
    runtime_seconds: int = Field(gt=0)
    average_scene_seconds_min: int = Field(gt=0)
    average_scene_seconds_max: int = Field(gt=0)
    rationale: str

    @field_validator("plan_entry_id", "rationale")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        if info.field_name == "plan_entry_id":
            return _key(value, "plan_entry_id")
        return _trimmed(value, "rationale")

    @model_validator(mode="after")
    def validate_range(self) -> "SequenceSceneAllocation":
        if not (
            self.minimum_scene_count
            <= self.preferred_scene_count
            <= self.maximum_scene_count
        ):
            raise ValueError("SceneBudget sequence count range is inconsistent")
        if self.average_scene_seconds_max < self.average_scene_seconds_min:
            raise ValueError("average scene seconds max must be >= min")
        if not self.sequence_ref.logical_id.root.startswith("sequence:"):
            raise ValueError("SceneBudget sequence_ref must be canonical Sequence")
        return self


class SceneBudget(BaseModel):
    """Planning range artifact; never allocates canonical scene identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    structure_profile_ref: VersionRef
    duration_budget_ref: VersionRef
    sequence_plan_ref: VersionRef
    minimum_scene_count: int = Field(ge=1)
    preferred_scene_count: int = Field(ge=1)
    maximum_scene_count: int = Field(ge=1)
    per_sequence: tuple[SequenceSceneAllocation, ...] = Field(min_length=1)
    rationale: str

    @field_validator("rationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        return _trimmed(value, "rationale")

    @model_validator(mode="after")
    def validate_budget(self) -> "SceneBudget":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.structure_profile_ref,
            structure_profile_logical_id(self.project_id),
            "structure_profile_ref",
        )
        _require_exact_ref(
            self.duration_budget_ref,
            duration_budget_logical_id(self.project_id),
            "duration_budget_ref",
        )
        _require_exact_ref(
            self.sequence_plan_ref,
            sequence_plan_logical_id(self.project_id),
            "sequence_plan_ref",
        )
        if not (
            self.minimum_scene_count
            <= self.preferred_scene_count
            <= self.maximum_scene_count
        ):
            raise ValueError("SceneBudget total scene range is inconsistent")
        if sum(item.minimum_scene_count for item in self.per_sequence) != self.minimum_scene_count:
            raise ValueError("SceneBudget minimum must equal per-sequence minimum sum")
        if sum(item.preferred_scene_count for item in self.per_sequence) != self.preferred_scene_count:
            raise ValueError("SceneBudget preferred must equal per-sequence preferred sum")
        if sum(item.maximum_scene_count for item in self.per_sequence) != self.maximum_scene_count:
            raise ValueError("SceneBudget maximum must equal per-sequence maximum sum")
        refs = []
        plan_ids = []
        for item in self.per_sequence:
            _require_project_scoped(
                item.sequence_ref,
                prefix="sequence:",
                project_id=self.project_id,
                label="SceneBudget sequence_ref",
            )
            refs.append(_ref_key(item.sequence_ref))
            plan_ids.append(item.plan_entry_id)
        if len(refs) != len(set(refs)):
            raise ValueError("SceneBudget sequence_ref values must be unique")
        if len(plan_ids) != len(set(plan_ids)):
            raise ValueError("SceneBudget plan_entry_id values must be unique")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return scene_budget_logical_id(self.project_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="structure_profile", source=self.structure_profile_ref),
            SourceVersionBinding(role="duration_budget", source=self.duration_budget_ref),
            SourceVersionBinding(role="sequence_plan", source=self.sequence_plan_ref),
        ]
        values.extend(
            SourceVersionBinding(
                role=f"sequence_{index:03d}",
                source=item.sequence_ref,
            )
            for index, item in enumerate(self.per_sequence)
        )
        return tuple(values)


class Scene(BaseModel):
    """Canonical cinematic scene truth, not legacy FlowKit operational Scene."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    scene_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    sequence_ref: VersionRef
    story_graph_ref: VersionRef
    scene_budget_ref: VersionRef
    character_refs: tuple[VersionRef, ...] = ()
    relationship_refs: tuple[VersionRef, ...] = ()
    knowledge_refs: tuple[VersionRef, ...] = ()
    location: str
    time_context: str
    context: str
    existence_reason: str
    objective: str
    opposition: str
    turn: str
    opening_state: str
    closing_state: str
    change_summary: str | None = None
    accepted_no_change_purpose: str | None = None

    @field_validator(
        "scene_key",
        "location",
        "time_context",
        "context",
        "existence_reason",
        "objective",
        "opposition",
        "turn",
        "opening_state",
        "closing_state",
    )
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        if info.field_name == "scene_key":
            return _key(value, "scene_key")
        return _trimmed(value, info.field_name)

    @field_validator("change_summary", "accepted_no_change_purpose")
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return None if value is None else _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_scene(self) -> "Scene":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_project_scoped(
            self.sequence_ref,
            prefix="sequence:",
            project_id=self.project_id,
            label="sequence_ref",
        )
        _require_exact_ref(
            self.story_graph_ref,
            story_graph_logical_id(self.project_id),
            "story_graph_ref",
        )
        _require_exact_ref(
            self.scene_budget_ref,
            scene_budget_logical_id(self.project_id),
            "scene_budget_ref",
        )
        state_changed = self.opening_state != self.closing_state
        if (not state_changed or self.change_summary is None) and self.accepted_no_change_purpose is None:
            raise ValueError(
                "Scene without explicit state change requires accepted_no_change_purpose"
            )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return scene_logical_id(self.project_id, self.scene_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="sequence", source=self.sequence_ref),
            SourceVersionBinding(role="causal_story_graph", source=self.story_graph_ref),
            SourceVersionBinding(role="scene_budget", source=self.scene_budget_ref),
        ]
        for prefix, refs in (
            ("character", self.character_refs),
            ("relationship", self.relationship_refs),
            ("knowledge", self.knowledge_refs),
        ):
            values.extend(
                SourceVersionBinding(role=f"{prefix}_{index:03d}", source=ref)
                for index, ref in enumerate(refs)
            )
        return tuple(values)


class SceneListEntry(BaseModel):
    """Scene order/budget projection row; no Scene semantic payload."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    order_index: int = Field(ge=0)
    scene_ref: VersionRef
    planned_seconds: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_ref(self) -> "SceneListEntry":
        if not self.scene_ref.logical_id.root.startswith("scene:"):
            raise ValueError("SceneListEntry must reference canonical Scene")
        return self


class SceneListManifest(BaseModel):
    """Ordered Scene reference projection; never a second Scene store."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    sequence_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    sequence_ref: VersionRef
    structure_profile_ref: VersionRef
    scene_budget_ref: VersionRef
    entries: tuple[SceneListEntry, ...] = Field(min_length=1)
    projection_verdict: GateVerdict = GateVerdict.PASS

    @field_validator("sequence_key")
    @classmethod
    def validate_sequence_key(cls, value: str) -> str:
        return _key(value, "sequence_key")

    @model_validator(mode="after")
    def validate_manifest(self) -> "SceneListManifest":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.sequence_ref,
            sequence_logical_id(self.project_id, self.sequence_key),
            "sequence_ref",
        )
        _require_exact_ref(
            self.structure_profile_ref,
            structure_profile_logical_id(self.project_id),
            "structure_profile_ref",
        )
        _require_exact_ref(
            self.scene_budget_ref,
            scene_budget_logical_id(self.project_id),
            "scene_budget_ref",
        )
        if self.projection_verdict is not GateVerdict.PASS:
            raise ValueError("persisted SceneListManifest must pass projection gate")
        indexes = [item.order_index for item in self.entries]
        if indexes != list(range(len(self.entries))):
            raise ValueError("SceneListManifest order indexes must be contiguous")
        refs = []
        for item in self.entries:
            _require_project_scoped(
                item.scene_ref,
                prefix="scene:",
                project_id=self.project_id,
                label="SceneListManifest scene_ref",
            )
            refs.append(_ref_key(item.scene_ref))
        if len(refs) != len(set(refs)):
            raise ValueError("SceneListManifest cannot duplicate Scene refs")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return scene_list_manifest_logical_id(self.project_id, self.sequence_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="sequence", source=self.sequence_ref),
            SourceVersionBinding(role="structure_profile", source=self.structure_profile_ref),
            SourceVersionBinding(role="scene_budget", source=self.scene_budget_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"scene_{item.order_index:03d}", source=item.scene_ref)
            for item in self.entries
        )
        return tuple(values)


class SceneDramaticBeat(BaseModel):
    """Intra-scene intention/action/reaction/resistance/reveal/microchange truth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    scene_key: str
    beat_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    scene_ref: VersionRef
    previous_beat_ref: VersionRef | None = None
    intention: str
    action: str
    reaction: str
    resistance: str | None = None
    reveal: str | None = None
    cause: str
    effect: str
    microchange: str

    @field_validator(
        "scene_key",
        "beat_key",
        "intention",
        "action",
        "reaction",
        "cause",
        "effect",
        "microchange",
    )
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        if info.field_name in {"scene_key", "beat_key"}:
            return _key(value, info.field_name)
        return _trimmed(value, info.field_name)

    @field_validator("resistance", "reveal")
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return None if value is None else _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_beat(self) -> "SceneDramaticBeat":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.scene_ref,
            scene_logical_id(self.project_id, self.scene_key),
            "scene_ref",
        )
        if self.resistance is None and self.reveal is None:
            raise ValueError(
                "SceneDramaticBeat requires resistance or reveal/new information"
            )
        if self.previous_beat_ref is not None:
            expected_prefix = (
                f"scene-dramatic-beat:{self.project_id.root}:{self.scene_key}:"
            )
            if not self.previous_beat_ref.logical_id.root.startswith(expected_prefix):
                raise ValueError(
                    "previous_beat_ref must belong to the same canonical Scene"
                )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return scene_dramatic_beat_logical_id(
            self.project_id,
            self.scene_key,
            self.beat_key,
        )

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="scene", source=self.scene_ref),
        ]
        if self.previous_beat_ref is not None:
            values.append(
                SourceVersionBinding(role="previous_scene_dramatic_beat", source=self.previous_beat_ref)
            )
        return tuple(values)


class SceneBreakdownEntry(BaseModel):
    """Breakdown projection row: beat reference + planned duration only."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    order_index: int = Field(ge=0)
    scene_dramatic_beat_ref: VersionRef
    planned_seconds: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_ref(self) -> "SceneBreakdownEntry":
        if not self.scene_dramatic_beat_ref.logical_id.root.startswith(
            "scene-dramatic-beat:"
        ):
            raise ValueError(
                "SceneBreakdownEntry must reference canonical SceneDramaticBeat"
            )
        return self


class SceneBreakdownManifest(BaseModel):
    """Scene-to-SceneDramaticBeat projection; owns no dramatic beat truth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    scene_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    scene_ref: VersionRef
    scene_list_manifest_ref: VersionRef
    scene_budget_ref: VersionRef
    opening_state_ref: VersionRef | None = None
    closing_state_ref: VersionRef | None = None
    entries: tuple[SceneBreakdownEntry, ...] = Field(min_length=1)
    projection_verdict: GateVerdict = GateVerdict.PASS

    @field_validator("scene_key")
    @classmethod
    def validate_scene_key(cls, value: str) -> str:
        return _key(value, "scene_key")

    @model_validator(mode="after")
    def validate_manifest(self) -> "SceneBreakdownManifest":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.scene_ref,
            scene_logical_id(self.project_id, self.scene_key),
            "scene_ref",
        )
        _require_exact_ref(
            self.scene_budget_ref,
            scene_budget_logical_id(self.project_id),
            "scene_budget_ref",
        )
        _require_project_scoped(
            self.scene_list_manifest_ref,
            prefix="scene-list-manifest:",
            project_id=self.project_id,
            label="scene_list_manifest_ref",
        )
        if self.projection_verdict is not GateVerdict.PASS:
            raise ValueError("persisted SceneBreakdownManifest must pass projection gate")
        indexes = [item.order_index for item in self.entries]
        if indexes != list(range(len(self.entries))):
            raise ValueError("SceneBreakdownManifest order indexes must be contiguous")
        refs = []
        expected_prefix = (
            f"scene-dramatic-beat:{self.project_id.root}:{self.scene_key}:"
        )
        for item in self.entries:
            if not item.scene_dramatic_beat_ref.logical_id.root.startswith(
                expected_prefix
            ):
                raise ValueError(
                    "SceneBreakdownManifest beat refs must belong to the same Scene"
                )
            refs.append(_ref_key(item.scene_dramatic_beat_ref))
        if len(refs) != len(set(refs)):
            raise ValueError(
                "SceneBreakdownManifest cannot duplicate SceneDramaticBeat refs"
            )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return scene_breakdown_manifest_logical_id(
            self.project_id,
            self.scene_key,
        )

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="scene", source=self.scene_ref),
            SourceVersionBinding(role="scene_list_manifest", source=self.scene_list_manifest_ref),
            SourceVersionBinding(role="scene_budget", source=self.scene_budget_ref),
        ]
        if self.opening_state_ref is not None:
            values.append(
                SourceVersionBinding(role="opening_state", source=self.opening_state_ref)
            )
        if self.closing_state_ref is not None:
            values.append(
                SourceVersionBinding(role="closing_state", source=self.closing_state_ref)
            )
        values.extend(
            SourceVersionBinding(
                role=f"scene_dramatic_beat_{item.order_index:03d}",
                source=item.scene_dramatic_beat_ref,
            )
            for item in self.entries
        )
        return tuple(values)


NarrativeHierarchyValue: TypeAlias = (
    MacroStoryBeat
    | SequencePlan
    | Sequence
    | SceneBudget
    | Scene
    | SceneListManifest
    | SceneDramaticBeat
    | SceneBreakdownManifest
)


class NarrativeHierarchyArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: NarrativeHierarchyValue

    @model_validator(mode="after")
    def validate_artifact(self) -> "NarrativeHierarchyArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("narrative artifact logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("narrative artifact version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError(
                "narrative artifact provenance must exactly bind declared sources"
            )
        if self.metadata.provenance.rule_version != self.value.active_profile_ref:
            raise ValueError(
                "narrative provenance rule_version must pin ActiveProductionProfile"
            )
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


def build_narrative_hierarchy_provenance(
    value: NarrativeHierarchyValue,
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
        rule_version=value.active_profile_ref,
        correlation_id=correlation_id,
    )


class NarrativeHierarchyRepository:
    """Immutable canonical narrative hierarchy over shared Studio repositories."""

    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, self.graph)

    async def create_macro_story_beat(
        self,
        *,
        value: MacroStoryBeat,
        provenance: Provenance,
        created_at: datetime,
    ) -> NarrativeHierarchyArtifact:
        await self._assert_macro_story_beat_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_macro_story_beat(
        self,
        *,
        value: MacroStoryBeat,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[NarrativeHierarchyArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_macro_story_beat_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="MacroStoryBeat",
            cause="MacroStoryBeat narrative revision",
            scope="macro_story_beat_descendants",
            repair=(
                "Recompute dependency-reachable Sequence/Scene/SceneDramaticBeat "
                "truth and projections from the accepted MacroStoryBeat successor."
            ),
        )

    async def create_sequence_plan(
        self,
        *,
        value: SequencePlan,
        provenance: Provenance,
        created_at: datetime,
    ) -> NarrativeHierarchyArtifact:
        await self._assert_sequence_plan_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_sequence_plan(
        self,
        *,
        value: SequencePlan,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[NarrativeHierarchyArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_sequence_plan_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="SequencePlan",
            cause="SequencePlan projection revision",
            scope="sequence_plan_descendants",
            repair=(
                "Recompute plan-dependent Sequence/Scene planning descendants; "
                "do not mutate accepted narrative truth merely because order changed."
            ),
        )

    async def create_sequence(
        self,
        *,
        value: Sequence,
        provenance: Provenance,
        created_at: datetime,
    ) -> NarrativeHierarchyArtifact:
        await self._assert_sequence_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_sequence(
        self,
        *,
        value: Sequence,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[NarrativeHierarchyArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_sequence_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="Sequence",
            cause="Sequence narrative revision",
            scope="sequence_descendants",
            repair=(
                "Recompute dependency-reachable Scene/SceneDramaticBeat truth "
                "and planning projections from the accepted Sequence successor."
            ),
        )

    async def create_scene_budget(
        self,
        *,
        value: SceneBudget,
        provenance: Provenance,
        created_at: datetime,
    ) -> NarrativeHierarchyArtifact:
        await self._assert_scene_budget_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_scene_budget(
        self,
        *,
        value: SceneBudget,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[NarrativeHierarchyArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_scene_budget_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="SceneBudget",
            cause="SceneBudget planning revision",
            scope="scene_budget_descendants",
            repair=(
                "Recompute SceneList/SceneBreakdown planning consumers; "
                "do not rewrite accepted Scene truth solely to fit arithmetic."
            ),
        )

    async def create_scene(
        self,
        *,
        value: Scene,
        provenance: Provenance,
        created_at: datetime,
    ) -> NarrativeHierarchyArtifact:
        await self._assert_scene_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_scene(
        self,
        *,
        value: Scene,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[NarrativeHierarchyArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_scene_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="Scene",
            cause="Scene narrative revision",
            scope="scene_descendants",
            repair=(
                "Recompute dependency-reachable SceneDramaticBeat/directing/shot "
                "descendants from the accepted Scene successor."
            ),
        )

    async def create_scene_list_manifest(
        self,
        *,
        value: SceneListManifest,
        provenance: Provenance,
        created_at: datetime,
    ) -> NarrativeHierarchyArtifact:
        await self._assert_scene_list_manifest_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_scene_list_manifest(
        self,
        *,
        value: SceneListManifest,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[NarrativeHierarchyArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_scene_list_manifest_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="SceneListManifest",
            cause="SceneListManifest projection revision",
            scope="scene_list_order_consumers",
            repair=(
                "Recompute order-dependent planning consumers only; "
                "canonical Scene truth remains unchanged."
            ),
        )

    async def create_scene_dramatic_beat(
        self,
        *,
        value: SceneDramaticBeat,
        provenance: Provenance,
        created_at: datetime,
    ) -> NarrativeHierarchyArtifact:
        await self._assert_scene_dramatic_beat_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_scene_dramatic_beat(
        self,
        *,
        value: SceneDramaticBeat,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[NarrativeHierarchyArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_scene_dramatic_beat_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="SceneDramaticBeat",
            cause="SceneDramaticBeat narrative revision",
            scope="scene_dramatic_beat_descendants",
            repair=(
                "Recompute dependency-reachable audience/directing/shot descendants "
                "from the accepted SceneDramaticBeat successor."
            ),
        )

    async def create_scene_breakdown_manifest(
        self,
        *,
        value: SceneBreakdownManifest,
        provenance: Provenance,
        created_at: datetime,
    ) -> NarrativeHierarchyArtifact:
        await self._assert_scene_breakdown_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_scene_breakdown_manifest(
        self,
        *,
        value: SceneBreakdownManifest,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[NarrativeHierarchyArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_scene_breakdown_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="SceneBreakdownManifest",
            cause="SceneBreakdownManifest projection revision",
            scope="scene_breakdown_order_consumers",
            repair=(
                "Recompute breakdown/order consumers only; canonical "
                "SceneDramaticBeat truth remains unchanged."
            ),
        )

    async def get_macro_story_beat(self, ref: VersionRef) -> NarrativeHierarchyArtifact | None:
        return await self._get_typed(ref, MacroStoryBeat, "macro-story-beat:")

    async def get_sequence_plan(self, ref: VersionRef) -> NarrativeHierarchyArtifact | None:
        return await self._get_typed(ref, SequencePlan, "sequence-plan:")

    async def get_sequence(self, ref: VersionRef) -> NarrativeHierarchyArtifact | None:
        return await self._get_typed(ref, Sequence, "sequence:")

    async def get_scene_budget(self, ref: VersionRef) -> NarrativeHierarchyArtifact | None:
        return await self._get_typed(ref, SceneBudget, "scene-budget:")

    async def get_scene(self, ref: VersionRef) -> NarrativeHierarchyArtifact | None:
        return await self._get_typed(ref, Scene, "scene:")

    async def get_scene_list_manifest(self, ref: VersionRef) -> NarrativeHierarchyArtifact | None:
        return await self._get_typed(ref, SceneListManifest, "scene-list-manifest:")

    async def get_scene_dramatic_beat(self, ref: VersionRef) -> NarrativeHierarchyArtifact | None:
        return await self._get_typed(ref, SceneDramaticBeat, "scene-dramatic-beat:")

    async def get_scene_breakdown_manifest(self, ref: VersionRef) -> NarrativeHierarchyArtifact | None:
        return await self._get_typed(
            ref,
            SceneBreakdownManifest,
            "scene-breakdown-manifest:",
        )

    async def trace_ancestors(self, ref: VersionRef):
        # Exact-version upstream ancestry from the shared dependency graph.
        return tuple(await self.graph.ancestors(ref))

    async def trace_descendants(self, ref: VersionRef):
        # Exact-version downstream descendants from the shared dependency graph.
        return tuple(await self.graph.descendants(ref))

    async def _create_approved(
        self,
        value: NarrativeHierarchyValue,
        provenance: Provenance,
        created_at: datetime,
    ) -> NarrativeHierarchyArtifact:
        self._assert_provenance(value, provenance)
        artifact = self._artifact(value, provenance, created_at, None)
        stored = await self.versions.create_initial(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        materialized = NarrativeHierarchyArtifact(
            metadata=stored.metadata,
            value=value,
        )
        await self._register_dependencies(materialized)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )
        return materialized

    async def _revise_approved(
        self,
        *,
        value: NarrativeHierarchyValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
        label: str,
        cause: str,
        scope: str,
        repair: str,
    ) -> tuple[NarrativeHierarchyArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise NarrativeHierarchyIdentityError(
                f"{label} revision must preserve logical identity"
            )
        await self._assert_current(
            predecessor,
            f"{label} revision predecessor",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        self._assert_provenance(value, provenance)
        artifact = self._artifact(
            value,
            provenance,
            created_at,
            predecessor,
        )
        stored = await self.versions.create_successor(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        materialized = NarrativeHierarchyArtifact(
            metadata=stored.metadata,
            value=value,
        )
        await self._register_dependencies(materialized)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )
        records = await self.invalidations.create_for_change(
            cause=cause,
            source_old=predecessor,
            source_new=materialized.ref,
            provenance=provenance,
            scope=scope,
            repair_or_recompute_requirement=repair,
        )
        return materialized, tuple(records)

    async def _get_typed(self, ref, model, prefix) -> NarrativeHierarchyArtifact | None:
        if not ref.logical_id.root.startswith(prefix):
            raise NarrativeHierarchyIdentityError(
                f"expected {prefix.rstrip(':')} artifact, got {ref.logical_id.root}"
            )
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = model.model_validate(stored.payload)
        return NarrativeHierarchyArtifact(metadata=stored.metadata, value=value)

    async def _register_dependencies(
        self,
        artifact: NarrativeHierarchyArtifact,
    ) -> None:
        grouped: dict[tuple[str, str], list[str]] = {}
        refs: dict[tuple[str, str], VersionRef] = {}
        for binding in artifact.value.source_bindings():
            if binding.source == artifact.ref:
                continue
            key = _ref_key(binding.source)
            refs[key] = binding.source
            grouped.setdefault(key, []).append(binding.role)
        for key in sorted(grouped):
            await self.graph.create_edge(
                source=refs[key],
                dependent=artifact.ref,
                edge_type="narrative_hierarchy_input",
                dependency_reason=" + ".join(sorted(set(grouped[key]))),
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _assert_macro_story_beat_inputs(self, value: MacroStoryBeat) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.story_core_ref,
            "locked StoryCore",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.story_graph_ref,
            "CausalStoryGraph",
            {LifecycleState.APPROVED},
        )
        await self._assert_current(
            value.conflict_ref,
            "ConflictModel",
            {LifecycleState.APPROVED},
        )
        await self._assert_current(
            value.stakes_ref,
            "StakesModel",
            {LifecycleState.APPROVED},
        )
        await self._assert_current(
            value.structure_profile_ref,
            "StructureProfile",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )

        core = await self._load(value.story_core_ref, StoryCoreVersion, "StoryCore")
        graph = await self._load(value.story_graph_ref, CausalStoryGraph, "CausalStoryGraph")
        structure = await self._load(
            value.structure_profile_ref,
            StructureProfile,
            "StructureProfile",
        )
        if core.phase is not StoryCorePhase.FROZEN_FOR_STRUCTURE or core.lock_manifest is None:
            raise NarrativeHierarchyGateBlocked(
                "MacroStoryBeat requires FROZEN_FOR_STRUCTURE StoryCore"
            )
        if core.active_profile_ref != value.active_profile_ref:
            raise NarrativeHierarchyGateBlocked(
                "MacroStoryBeat StoryCore must share exact ActiveProductionProfile"
            )
        if core.lock_manifest.story_graph_ref != value.story_graph_ref:
            raise NarrativeHierarchyGateBlocked(
                "MacroStoryBeat StoryGraph must be the exact graph locked by StoryCore"
            )
        if graph.story_core_draft_ref != core.lock_manifest.draft_ref:
            raise NarrativeHierarchyGateBlocked(
                "MacroStoryBeat StoryGraph must bind StoryCore lock draft"
            )
        if graph.conflict_ref != value.conflict_ref or graph.stakes_ref != value.stakes_ref:
            raise NarrativeHierarchyGateBlocked(
                "MacroStoryBeat Conflict/Stakes must match exact StoryGraph lineage"
            )
        if graph.active_profile_ref != value.active_profile_ref:
            raise NarrativeHierarchyGateBlocked(
                "MacroStoryBeat StoryGraph profile lineage mismatch"
            )
        if structure.active_profile_ref != value.active_profile_ref:
            raise NarrativeHierarchyGateBlocked(
                "MacroStoryBeat StructureProfile profile lineage mismatch"
            )

    async def _assert_sequence_plan_inputs(self, value: SequencePlan) -> None:
        await self._assert_all_sources_exist(value)
        for ref, label, allowed in (
            (value.active_profile_ref, "ActiveProductionProfile", {LifecycleState.LOCKED}),
            (
                value.structure_profile_ref,
                "StructureProfile",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            ),
            (
                value.macro_beat_sheet_ref,
                "MacroBeatSheet",
                {LifecycleState.APPROVED},
            ),
            (
                value.duration_budget_ref,
                "DurationBudget",
                {LifecycleState.APPROVED},
            ),
        ):
            await self._assert_current(ref, label, allowed)
        for entry in value.entries:
            await self._assert_current(
                entry.macro_story_beat_ref,
                "MacroStoryBeat",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
            if entry.sequence_ref is not None:
                await self._assert_current(
                    entry.sequence_ref,
                    "SequencePlan projected Sequence",
                    {LifecycleState.APPROVED, LifecycleState.LOCKED},
                )

        structure = await self._load(
            value.structure_profile_ref,
            StructureProfile,
            "StructureProfile",
        )
        sheet = await self._load(
            value.macro_beat_sheet_ref,
            MacroBeatSheet,
            "MacroBeatSheet",
        )
        budget = await self._load(
            value.duration_budget_ref,
            DurationBudget,
            "DurationBudget",
        )
        if not structure.sequence_count.contains(value.target_count):
            raise NarrativeHierarchyGateBlocked(
                "SequencePlan target_count falls outside StructureProfile range"
            )
        if (
            sheet.structure_profile_ref != value.structure_profile_ref
            or budget.structure_profile_ref != value.structure_profile_ref
        ):
            raise NarrativeHierarchyGateBlocked(
                "SequencePlan planning inputs must bind exact StructureProfile"
            )
        if (
            sheet.active_profile_ref != value.active_profile_ref
            or budget.active_profile_ref != value.active_profile_ref
            or structure.active_profile_ref != value.active_profile_ref
        ):
            raise NarrativeHierarchyGateBlocked(
                "SequencePlan planning inputs must share exact ActiveProductionProfile"
            )
        if sheet.duration_budget_ref != value.duration_budget_ref:
            raise NarrativeHierarchyGateBlocked(
                "SequencePlan MacroBeatSheet must bind exact DurationBudget"
            )

        sheet_macro_to_alloc = {
            _ref_key(entry.macro_story_beat_ref): entry.duration_allocation_id
            for entry in sheet.entries
        }
        plan_macro_keys = {_ref_key(entry.macro_story_beat_ref) for entry in value.entries}
        if plan_macro_keys != set(sheet_macro_to_alloc):
            raise NarrativeHierarchyGateBlocked(
                "SequencePlan must cover every MacroBeatSheet MacroStoryBeat"
            )

        sequence_allocations = {
            item.allocation_id: item
            for item in budget.allocations
            if item.level is BudgetLevel.SEQUENCE
        }
        if {entry.duration_allocation_id for entry in value.entries} != set(sequence_allocations):
            raise NarrativeHierarchyGateBlocked(
                "SequencePlan must cover each DurationBudget Sequence allocation exactly once"
            )
        for entry in value.entries:
            allocation = sequence_allocations[entry.duration_allocation_id]
            expected_parent = sheet_macro_to_alloc[_ref_key(entry.macro_story_beat_ref)]
            if allocation.parent_allocation_id != expected_parent:
                raise NarrativeHierarchyGateBlocked(
                    "SequencePlan allocation parent does not match MacroBeatSheet ancestry"
                )
            if allocation.seconds != entry.runtime_budget_seconds:
                raise NarrativeHierarchyGateBlocked(
                    "SequencePlan runtime budget must match DurationBudget allocation"
                )
        if value.runtime_budget_seconds != budget.total_seconds:
            raise NarrativeHierarchyGateBlocked(
                "SequencePlan runtime budget must reconcile to DurationBudget total"
            )

    async def _assert_sequence_inputs(self, value: Sequence) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.sequence_plan_ref,
            "SequencePlan",
            {LifecycleState.APPROVED},
        )
        await self._assert_current(
            value.structure_profile_ref,
            "StructureProfile",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        for ref in value.macro_story_beat_refs:
            await self._assert_current(
                ref,
                "MacroStoryBeat",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )

        plan = await self._load(value.sequence_plan_ref, SequencePlan, "SequencePlan")
        structure = await self._load(
            value.structure_profile_ref,
            StructureProfile,
            "StructureProfile",
        )
        matches = [
            entry for entry in plan.entries if entry.plan_entry_id == value.plan_entry_id
        ]
        if len(matches) != 1:
            raise NarrativeHierarchyGateBlocked(
                "Sequence must bind exactly one SequencePlan entry"
            )
        entry = matches[0]
        if tuple(value.macro_story_beat_refs) != (entry.macro_story_beat_ref,):
            raise NarrativeHierarchyGateBlocked(
                "Sequence MacroStoryBeat ancestry must match SequencePlan entry"
            )
        if entry.sequence_ref is not None and entry.sequence_ref != value.ref:
            raise NarrativeHierarchyGateBlocked(
                "SequencePlan projected Sequence ref conflicts with canonical Sequence"
            )
        if (
            plan.active_profile_ref != value.active_profile_ref
            or structure.active_profile_ref != value.active_profile_ref
        ):
            raise NarrativeHierarchyGateBlocked(
                "Sequence profile lineage mismatch"
            )
        if plan.structure_profile_ref != value.structure_profile_ref:
            raise NarrativeHierarchyGateBlocked(
                "Sequence must bind SequencePlan StructureProfile"
            )

    async def _assert_scene_budget_inputs(self, value: SceneBudget) -> None:
        await self._assert_all_sources_exist(value)
        for ref, label, allowed in (
            (value.active_profile_ref, "ActiveProductionProfile", {LifecycleState.LOCKED}),
            (
                value.structure_profile_ref,
                "StructureProfile",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            ),
            (
                value.duration_budget_ref,
                "DurationBudget",
                {LifecycleState.APPROVED},
            ),
            (
                value.sequence_plan_ref,
                "SequencePlan",
                {LifecycleState.APPROVED},
            ),
        ):
            await self._assert_current(ref, label, allowed)
        for item in value.per_sequence:
            await self._assert_current(
                item.sequence_ref,
                "SceneBudget Sequence",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )

        structure = await self._load(
            value.structure_profile_ref,
            StructureProfile,
            "StructureProfile",
        )
        duration = await self._load(
            value.duration_budget_ref,
            DurationBudget,
            "DurationBudget",
        )
        plan = await self._load(
            value.sequence_plan_ref,
            SequencePlan,
            "SequencePlan",
        )
        if (
            duration.structure_profile_ref != value.structure_profile_ref
            or plan.structure_profile_ref != value.structure_profile_ref
        ):
            raise NarrativeHierarchyGateBlocked(
                "SceneBudget planning inputs must bind exact StructureProfile"
            )
        if (
            duration.active_profile_ref != value.active_profile_ref
            or plan.active_profile_ref != value.active_profile_ref
            or structure.active_profile_ref != value.active_profile_ref
        ):
            raise NarrativeHierarchyGateBlocked(
                "SceneBudget planning inputs must share exact ActiveProductionProfile"
            )
        if value.minimum_scene_count < structure.scene_count.minimum:
            raise NarrativeHierarchyGateBlocked(
                "SceneBudget minimum falls below StructureProfile scene range"
            )
        if value.maximum_scene_count > structure.scene_count.maximum:
            raise NarrativeHierarchyGateBlocked(
                "SceneBudget maximum exceeds StructureProfile scene range"
            )
        if not structure.scene_count.contains(value.preferred_scene_count):
            raise NarrativeHierarchyGateBlocked(
                "SceneBudget preferred count falls outside StructureProfile range"
            )

        plan_by_id = {entry.plan_entry_id: entry for entry in plan.entries}
        if {item.plan_entry_id for item in value.per_sequence} != set(plan_by_id):
            raise NarrativeHierarchyGateBlocked(
                "SceneBudget must cover each SequencePlan entry exactly once"
            )
        runtime_total = 0
        for item in value.per_sequence:
            plan_entry = plan_by_id[item.plan_entry_id]
            sequence = await self._load(item.sequence_ref, Sequence, "Sequence")
            if sequence.sequence_plan_ref != value.sequence_plan_ref:
                raise NarrativeHierarchyGateBlocked(
                    "SceneBudget Sequence must bind exact SequencePlan"
                )
            if sequence.plan_entry_id != item.plan_entry_id:
                raise NarrativeHierarchyGateBlocked(
                    "SceneBudget Sequence plan_entry_id mismatch"
                )
            if item.runtime_seconds != plan_entry.runtime_budget_seconds:
                raise NarrativeHierarchyGateBlocked(
                    "SceneBudget per-sequence runtime must match SequencePlan"
                )
            runtime_total += item.runtime_seconds
        if abs(runtime_total - duration.total_seconds) > structure.budget_tolerance_seconds:
            raise NarrativeHierarchyGateBlocked(
                "BUDGET_SCENE_OVERFLOW: SceneBudget runtime does not reconcile "
                "to DurationBudget within tolerance"
            )

    async def _assert_scene_inputs(self, value: Scene) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.sequence_ref,
            "Sequence",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.story_graph_ref,
            "CausalStoryGraph",
            {LifecycleState.APPROVED},
        )
        await self._assert_current(
            value.scene_budget_ref,
            "SceneBudget",
            {LifecycleState.APPROVED},
        )
        for ref in value.character_refs:
            await self._assert_current(
                ref,
                "CharacterModelVersion",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
        for ref in value.relationship_refs:
            await self._assert_current(
                ref,
                "RelationshipState",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
        for ref in value.knowledge_refs:
            await self._assert_current(
                ref,
                "CharacterKnowledgeState",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )

        sequence = await self._load(value.sequence_ref, Sequence, "Sequence")
        budget = await self._load(value.scene_budget_ref, SceneBudget, "SceneBudget")
        graph = await self._load(value.story_graph_ref, CausalStoryGraph, "CausalStoryGraph")
        if not any(item.sequence_ref == value.sequence_ref for item in budget.per_sequence):
            raise NarrativeHierarchyGateBlocked(
                "Scene parent Sequence is not covered by current SceneBudget"
            )
        if (
            sequence.active_profile_ref != value.active_profile_ref
            or budget.active_profile_ref != value.active_profile_ref
            or graph.active_profile_ref != value.active_profile_ref
        ):
            raise NarrativeHierarchyGateBlocked("Scene profile lineage mismatch")

        for ref in value.character_refs:
            character = await self._load(
                ref,
                CharacterModelVersion,
                "CharacterModelVersion",
            )
            if character.project_id != value.project_id:
                raise NarrativeHierarchyGateBlocked(
                    "Scene CharacterModelVersion belongs to a different project"
                )
        for ref in value.relationship_refs:
            relationship = await self._load(
                ref,
                RelationshipState,
                "RelationshipState",
            )
            if relationship.project_id != value.project_id:
                raise NarrativeHierarchyGateBlocked(
                    "Scene RelationshipState belongs to a different project"
                )
        for ref in value.knowledge_refs:
            knowledge = await self._load(
                ref,
                CharacterKnowledgeState,
                "CharacterKnowledgeState",
            )
            if knowledge.project_id != value.project_id:
                raise NarrativeHierarchyGateBlocked(
                    "Scene CharacterKnowledgeState belongs to a different project"
                )

    async def _assert_scene_list_manifest_inputs(
        self,
        value: SceneListManifest,
    ) -> None:
        await self._assert_all_sources_exist(value)
        for ref, label, allowed in (
            (value.active_profile_ref, "ActiveProductionProfile", {LifecycleState.LOCKED}),
            (value.sequence_ref, "Sequence", {LifecycleState.APPROVED, LifecycleState.LOCKED}),
            (
                value.structure_profile_ref,
                "StructureProfile",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            ),
            (value.scene_budget_ref, "SceneBudget", {LifecycleState.APPROVED}),
        ):
            await self._assert_current(ref, label, allowed)
        for entry in value.entries:
            await self._assert_current(
                entry.scene_ref,
                "SceneListManifest Scene",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )

        structure = await self._load(
            value.structure_profile_ref,
            StructureProfile,
            "StructureProfile",
        )
        budget = await self._load(value.scene_budget_ref, SceneBudget, "SceneBudget")
        allocation = next(
            (item for item in budget.per_sequence if item.sequence_ref == value.sequence_ref),
            None,
        )
        if allocation is None:
            raise NarrativeHierarchyGateBlocked(
                "SceneListManifest Sequence is not covered by SceneBudget"
            )
        if not (
            allocation.minimum_scene_count
            <= len(value.entries)
            <= allocation.maximum_scene_count
        ):
            raise NarrativeHierarchyGateBlocked(
                "SceneListManifest scene count falls outside SceneBudget range"
            )
        planned_seconds = sum(item.planned_seconds for item in value.entries)
        if abs(planned_seconds - allocation.runtime_seconds) > structure.budget_tolerance_seconds:
            raise NarrativeHierarchyGateBlocked(
                "SceneListManifest planned duration does not reconcile to SceneBudget"
            )
        for entry in value.entries:
            scene = await self._load(entry.scene_ref, Scene, "Scene")
            if scene.sequence_ref != value.sequence_ref:
                raise NarrativeHierarchyGateBlocked(
                    "SceneListManifest Scene belongs to a different Sequence"
                )

    async def _assert_scene_dramatic_beat_inputs(
        self,
        value: SceneDramaticBeat,
    ) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.scene_ref,
            "Scene",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        scene = await self._load(value.scene_ref, Scene, "Scene")
        if scene.active_profile_ref != value.active_profile_ref:
            raise NarrativeHierarchyGateBlocked(
                "SceneDramaticBeat profile lineage mismatch"
            )
        if value.previous_beat_ref is not None:
            await self._assert_current(
                value.previous_beat_ref,
                "previous SceneDramaticBeat",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
            previous = await self._load(
                value.previous_beat_ref,
                SceneDramaticBeat,
                "SceneDramaticBeat",
            )
            if previous.scene_ref != value.scene_ref:
                raise NarrativeHierarchyGateBlocked(
                    "previous SceneDramaticBeat must belong to the same Scene"
                )

    async def _assert_scene_breakdown_inputs(
        self,
        value: SceneBreakdownManifest,
    ) -> None:
        await self._assert_all_sources_exist(value)
        for ref, label, allowed in (
            (value.active_profile_ref, "ActiveProductionProfile", {LifecycleState.LOCKED}),
            (value.scene_ref, "Scene", {LifecycleState.APPROVED, LifecycleState.LOCKED}),
            (
                value.scene_list_manifest_ref,
                "SceneListManifest",
                {LifecycleState.APPROVED},
            ),
            (value.scene_budget_ref, "SceneBudget", {LifecycleState.APPROVED}),
        ):
            await self._assert_current(ref, label, allowed)
        for item in value.entries:
            await self._assert_current(
                item.scene_dramatic_beat_ref,
                "SceneDramaticBeat",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
        for ref, label in (
            (value.opening_state_ref, "opening state"),
            (value.closing_state_ref, "closing state"),
        ):
            if ref is not None:
                await self._assert_current(
                    ref,
                    label,
                    {
                        LifecycleState.DRAFT,
                        LifecycleState.REVIEW,
                        LifecycleState.APPROVED,
                        LifecycleState.LOCKED,
                    },
                )

        scene_list = await self._load(
            value.scene_list_manifest_ref,
            SceneListManifest,
            "SceneListManifest",
        )
        scene = await self._load(value.scene_ref, Scene, "Scene")
        matching_scene_entry = next(
            (item for item in scene_list.entries if item.scene_ref == value.scene_ref),
            None,
        )
        if matching_scene_entry is None:
            raise NarrativeHierarchyGateBlocked(
                "SceneBreakdownManifest Scene is not present in SceneListManifest"
            )
        structure = await self._load(
            scene_list.structure_profile_ref,
            StructureProfile,
            "StructureProfile",
        )
        planned_seconds = sum(item.planned_seconds for item in value.entries)
        if (
            abs(planned_seconds - matching_scene_entry.planned_seconds)
            > structure.budget_tolerance_seconds
        ):
            raise NarrativeHierarchyGateBlocked(
                "SceneBreakdownManifest duration does not reconcile to SceneListManifest"
            )
        for item in value.entries:
            beat = await self._load(
                item.scene_dramatic_beat_ref,
                SceneDramaticBeat,
                "SceneDramaticBeat",
            )
            if beat.scene_ref != value.scene_ref:
                raise NarrativeHierarchyGateBlocked(
                    "SceneBreakdownManifest beat belongs to a different Scene"
                )
        if scene.active_profile_ref != value.active_profile_ref:
            raise NarrativeHierarchyGateBlocked(
                "SceneBreakdownManifest profile lineage mismatch"
            )

    async def _assert_all_sources_exist(
        self,
        value: NarrativeHierarchyValue,
    ) -> None:
        for binding in value.source_bindings():
            if await self.versions.get_version(binding.source) is None:
                raise NarrativeHierarchyGateBlocked(
                    f"missing exact source {binding.role}="
                    f"{binding.source.logical_id.root}/"
                    f"{binding.source.version_id.root}"
                )

    async def _assert_current(
        self,
        ref: VersionRef,
        label: str,
        allowed: set[LifecycleState],
    ) -> CurrentVersionPointer:
        try:
            pointer = await self.versions.get_current(ref.logical_id)
        except CurrentPointerNotFound as exc:
            raise NarrativeHierarchyGateBlocked(
                f"{label} has no current version"
            ) from exc
        if pointer.version_id != ref.version_id or pointer.status not in allowed:
            raise NarrativeHierarchyGateBlocked(
                f"{label} is not exact current accepted version"
            )
        return pointer

    async def _load(self, ref: VersionRef, model, label: str):
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise NarrativeHierarchyGateBlocked(f"{label} exact version not found")
        try:
            return model.model_validate(stored.payload)
        except ValidationError as exc:
            raise NarrativeHierarchyGateBlocked(
                f"{label} payload is not canonical {model.__name__}"
            ) from exc

    @staticmethod
    def _assert_provenance(
        value: NarrativeHierarchyValue,
        provenance: Provenance,
    ) -> None:
        if provenance.source_versions != value.source_bindings():
            raise NarrativeHierarchyIdentityError(
                "narrative provenance must exactly match declared source bindings"
            )
        if provenance.rule_version != value.active_profile_ref:
            raise NarrativeHierarchyIdentityError(
                "narrative provenance rule_version must pin ActiveProductionProfile"
            )

    @staticmethod
    def _artifact(
        value: NarrativeHierarchyValue,
        provenance: Provenance,
        created_at: datetime,
        predecessor: VersionRef | None,
    ) -> NarrativeHierarchyArtifact:
        return NarrativeHierarchyArtifact(
            metadata=SemanticRecordMetadata(
                logical_id=value.logical_id,
                version_id=value.version_id,
                predecessor=predecessor,
                provenance=provenance,
                created_at=created_at,
            ),
            value=value,
        )
