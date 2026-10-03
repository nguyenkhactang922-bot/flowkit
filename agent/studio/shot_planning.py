"""IMP-031 canonical shot planning and ShotExpansion boundary.

Authority rules:
- ShotExpansion is a stateless planning transformation and owns no truth store.
- CoverageStrategy and ShotBudget are planning constraints, never narrative/Shot truth.
- ShotListItem is the sole canonical shot_id origin under ADR-0020.
- ShotListManifest is an ordered refs-only projection over existing ShotListItems.
- Provider/runtime payloads are deliberately absent from this module.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from enum import Enum
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .active_profile import ActiveProductionProfile, profile_path_edge_type
from .directing import BlockingPlan, CinematographyObjective, DirectingIntent
from .invalidation import (
    DependencyGraphRepository,
    InvalidationRecord,
    InvalidationRepository,
)
from .narrative_hierarchy import Scene, SceneDramaticBeat
from .narrative_trace import (
    NarrativeArtifactType,
    NarrativeTraceArtifact,
    NarrativeTraceRecord,
    NarrativeTraceRepository,
    NarrativeTraceState,
    build_narrative_trace_provenance,
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
from .story_quality import ScriptLockManifest, script_lock_logical_id
from .structure_planning import (
    BudgetLevel,
    CountRange,
    DurationBudget,
    RuntimeRangeSeconds,
    StructureProfile,
    duration_budget_logical_id,
    structure_profile_logical_id,
)
from .versioning import VersionRepository


_ACCEPTED = {LifecycleState.APPROVED, LifecycleState.LOCKED}
_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")


class ShotPlanningError(ValueError):
    """Base IMP-031 planning error."""


class ShotPlanningIdentityError(ShotPlanningError):
    """Raised when canonical shot/planning identity is inconsistent."""


class ShotPlanningGateBlocked(ShotPlanningError):
    """Raised when an exact-version planning hard gate fails closed."""


class ShotPlanningState(str, Enum):
    PLANNED = "PLANNED"
    ELIGIBLE = "ELIGIBLE"
    REJECTED = "REJECTED"


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
    normalized = _trimmed(value, label).lower()
    if not _KEY_RE.fullmatch(normalized):
        raise ValueError(
            f"{label} must start with lowercase letter/digit and use only lowercase letters, "
            "digits, '.', '_' or '-'"
        )
    return normalized


def _unique_text(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    normalized = tuple(_trimmed(value, label) for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{label} must not contain duplicates")
    return normalized


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return ref.logical_id.root, ref.version_id.root


def _unique_refs(values: tuple[VersionRef, ...], label: str) -> tuple[VersionRef, ...]:
    keys = [_ref_key(value) for value in values]
    if len(keys) != len(set(keys)):
        raise ValueError(f"{label} must not contain duplicate exact refs")
    return tuple(sorted(values, key=_ref_key))


def _digest(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:32]


def _project_ref(
    ref: VersionRef,
    *,
    prefix: str,
    project_id: LogicalId,
    label: str,
) -> None:
    base = f"{prefix}{project_id.root}"
    root = ref.logical_id.root
    if root != base and not root.startswith(base + ":"):
        raise ValueError(f"{label} must belong to the same project and use {prefix} identity")


def _active_profile_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"active-profile:{project_id.root}")


def coverage_strategy_logical_id(project_id: LogicalId, scene_ref: VersionRef) -> LogicalId:
    return LogicalId(
        f"coverage-strategy:{project_id.root}:"
        + _digest(project_id.root, scene_ref.logical_id.root)
    )


def shot_budget_logical_id(project_id: LogicalId, scene_ref: VersionRef) -> LogicalId:
    return LogicalId(
        f"shot-budget:{project_id.root}:"
        + _digest(project_id.root, scene_ref.logical_id.root)
    )


def shot_list_item_logical_id(
    project_id: LogicalId,
    scene_dramatic_beat_ref: VersionRef,
    shot_key: str,
) -> LogicalId:
    stable_key = _key(shot_key, "shot_key")
    return LogicalId(
        f"shot-list-item:{project_id.root}:"
        + _digest(project_id.root, scene_dramatic_beat_ref.logical_id.root, stable_key)
    )


def shot_list_manifest_logical_id(project_id: LogicalId, scene_ref: VersionRef) -> LogicalId:
    return LogicalId(
        f"shot-list-manifest:{project_id.root}:"
        + _digest(project_id.root, scene_ref.logical_id.root)
    )


class CoverageBeatBinding(BaseModel):
    """Exact directing/cinematography authority used to plan coverage for one beat."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scene_dramatic_beat_ref: VersionRef
    blocking_plan_ref: VersionRef
    cinematography_objective_ref: VersionRef

    @model_validator(mode="after")
    def validate_prefixes(self) -> "CoverageBeatBinding":
        if not self.scene_dramatic_beat_ref.logical_id.root.startswith("scene-dramatic-beat:"):
            raise ValueError("scene_dramatic_beat_ref must reference SceneDramaticBeat")
        if not self.blocking_plan_ref.logical_id.root.startswith("blocking-plan:"):
            raise ValueError("blocking_plan_ref must reference BlockingPlan")
        if not self.cinematography_objective_ref.logical_id.root.startswith(
            "cinematography-objective:"
        ):
            raise ValueError("cinematography_objective_ref must reference CinematographyObjective")
        return self


class CoverageRequirement(BaseModel):
    """Provider-neutral coverage need; it cannot choose provider/lens/request parameters."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    coverage_key: str
    scene_dramatic_beat_ref: VersionRef
    coverage_function: str
    viewpoint_intent: str
    rationale: str
    continuity_needs: tuple[str, ...] = ()
    minimum_shots: int = Field(default=1, ge=1)
    maximum_shots: int = Field(default=1, ge=1)

    @field_validator("coverage_key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        return _key(value, "coverage_key")

    @field_validator("coverage_function", "viewpoint_intent", "rationale")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("continuity_needs")
    @classmethod
    def normalize_continuity(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _unique_text(values, "continuity_needs")

    @model_validator(mode="after")
    def validate_range(self) -> "CoverageRequirement":
        if self.maximum_shots < self.minimum_shots:
            raise ValueError("coverage maximum_shots must be >= minimum_shots")
        if not self.scene_dramatic_beat_ref.logical_id.root.startswith("scene-dramatic-beat:"):
            raise ValueError("coverage requirement must bind canonical SceneDramaticBeat")
        return self


class CoverageStrategy(BaseModel):
    """Scene-scoped editing/coverage planning authority; never Shot identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    coverage_strategy_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    scene_ref: VersionRef
    duration_budget_ref: VersionRef
    beat_bindings: tuple[CoverageBeatBinding, ...] = Field(min_length=1)
    requirements: tuple[CoverageRequirement, ...] = Field(min_length=1)
    continuity_needs: tuple[str, ...] = ()
    rationale: str

    @field_validator("continuity_needs")
    @classmethod
    def normalize_continuity(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _unique_text(values, "continuity_needs")

    @field_validator("rationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        return _trimmed(value, "rationale")

    @field_validator("beat_bindings")
    @classmethod
    def normalize_bindings(
        cls,
        values: tuple[CoverageBeatBinding, ...],
    ) -> tuple[CoverageBeatBinding, ...]:
        keys = [_ref_key(item.scene_dramatic_beat_ref) for item in values]
        if len(keys) != len(set(keys)):
            raise ValueError("CoverageStrategy beat_bindings must be unique per beat")
        return tuple(sorted(values, key=lambda item: _ref_key(item.scene_dramatic_beat_ref)))

    @field_validator("requirements")
    @classmethod
    def normalize_requirements(
        cls,
        values: tuple[CoverageRequirement, ...],
    ) -> tuple[CoverageRequirement, ...]:
        keys = [item.coverage_key for item in values]
        if len(keys) != len(set(keys)):
            raise ValueError("CoverageStrategy coverage_key values must be unique")
        return tuple(sorted(values, key=lambda item: item.coverage_key))

    @model_validator(mode="after")
    def validate_authority(self) -> "CoverageStrategy":
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        _project_ref(self.scene_ref, prefix="scene:", project_id=self.project_id, label="scene_ref")
        if self.duration_budget_ref.logical_id != duration_budget_logical_id(self.project_id):
            raise ValueError("duration_budget_ref must bind this project's DurationBudget")
        expected = coverage_strategy_logical_id(self.project_id, self.scene_ref)
        if self.coverage_strategy_id != expected:
            raise ValueError(f"coverage_strategy_id must be {expected.root}")
        beat_keys = {_ref_key(item.scene_dramatic_beat_ref) for item in self.beat_bindings}
        for requirement in self.requirements:
            if _ref_key(requirement.scene_dramatic_beat_ref) not in beat_keys:
                raise ValueError("coverage requirement beat is absent from beat_bindings")
        if not all(
            any(req.scene_dramatic_beat_ref == binding.scene_dramatic_beat_ref for req in self.requirements)
            for binding in self.beat_bindings
        ):
            raise ValueError("every coverage beat binding requires at least one coverage requirement")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.coverage_strategy_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="scene", source=self.scene_ref),
            SourceVersionBinding(role="duration_budget", source=self.duration_budget_ref),
        ]
        for index, binding in enumerate(self.beat_bindings):
            values.extend(
                (
                    SourceVersionBinding(
                        role=f"beat_{index:03d}", source=binding.scene_dramatic_beat_ref
                    ),
                    SourceVersionBinding(
                        role=f"blocking_{index:03d}", source=binding.blocking_plan_ref
                    ),
                    SourceVersionBinding(
                        role=f"cinematography_{index:03d}",
                        source=binding.cinematography_objective_ref,
                    ),
                )
            )
        return tuple(values)


class ShotBudget(BaseModel):
    """Scene-scoped shot count/runtime ranges; planning policy, not Shot truth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    shot_budget_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    structure_profile_ref: VersionRef
    duration_budget_ref: VersionRef
    coverage_strategy_ref: VersionRef
    scene_ref: VersionRef
    shot_count_range: CountRange
    shot_duration_range_seconds: RuntimeRangeSeconds
    scene_duration_seconds: int = Field(gt=0)
    tolerance_seconds: int = Field(ge=0)
    rationale: str

    @field_validator("rationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        return _trimmed(value, "rationale")

    @model_validator(mode="after")
    def validate_authority(self) -> "ShotBudget":
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        if self.structure_profile_ref.logical_id != structure_profile_logical_id(self.project_id):
            raise ValueError("structure_profile_ref must bind this project's StructureProfile")
        if self.duration_budget_ref.logical_id != duration_budget_logical_id(self.project_id):
            raise ValueError("duration_budget_ref must bind this project's DurationBudget")
        _project_ref(self.scene_ref, prefix="scene:", project_id=self.project_id, label="scene_ref")
        expected_coverage = coverage_strategy_logical_id(self.project_id, self.scene_ref)
        if self.coverage_strategy_ref.logical_id != expected_coverage:
            raise ValueError("coverage_strategy_ref must bind this Scene's CoverageStrategy")
        expected = shot_budget_logical_id(self.project_id, self.scene_ref)
        if self.shot_budget_id != expected:
            raise ValueError(f"shot_budget_id must be {expected.root}")
        feasible = False
        low_target = max(1, self.scene_duration_seconds - self.tolerance_seconds)
        high_target = self.scene_duration_seconds + self.tolerance_seconds
        for count in range(self.shot_count_range.minimum, self.shot_count_range.maximum + 1):
            low = count * self.shot_duration_range_seconds.minimum
            high = count * self.shot_duration_range_seconds.maximum
            if max(low, low_target) <= min(high, high_target):
                feasible = True
                break
        if not feasible:
            raise ValueError(
                "BUDGET_SHOT_OVERFLOW: shot count/duration ranges cannot realize scene duration within tolerance"
            )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.shot_budget_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return (
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="structure_profile", source=self.structure_profile_ref),
            SourceVersionBinding(role="duration_budget", source=self.duration_budget_ref),
            SourceVersionBinding(role="coverage_strategy", source=self.coverage_strategy_ref),
            SourceVersionBinding(role="scene", source=self.scene_ref),
        )


class ShotExpansionBeatContext(BaseModel):
    """Exact beat-local authority used by the stateless expansion service."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scene_dramatic_beat_ref: VersionRef
    narrative_trace_ref: VersionRef
    directing_intent_ref: VersionRef
    blocking_plan_ref: VersionRef
    cinematography_objective_ref: VersionRef

    @model_validator(mode="after")
    def validate_prefixes(self) -> "ShotExpansionBeatContext":
        refs = (
            (self.scene_dramatic_beat_ref, "scene-dramatic-beat:", "scene_dramatic_beat_ref"),
            (self.narrative_trace_ref, "narrative-trace:", "narrative_trace_ref"),
            (self.directing_intent_ref, "directing-intent:", "directing_intent_ref"),
            (self.blocking_plan_ref, "blocking-plan:", "blocking_plan_ref"),
            (
                self.cinematography_objective_ref,
                "cinematography-objective:",
                "cinematography_objective_ref",
            ),
        )
        for ref, prefix, label in refs:
            if not ref.logical_id.root.startswith(prefix):
                raise ValueError(f"{label} must use {prefix} identity")
        return self


class ShotExpansionCandidate(BaseModel):
    """Ephemeral pre-identity candidate. Deliberately has no shot_id/version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    shot_key: str
    scene_dramatic_beat_ref: VersionRef
    coverage_key: str
    coverage_function: str
    dramatic_function: str
    reason_for_exist: str
    duration_seconds: int = Field(gt=0)
    basic_shot_intent: str
    subject_refs: tuple[VersionRef, ...] = ()
    required_visual_information: tuple[str, ...] = ()
    must_preserve: tuple[str, ...] = ()

    @field_validator("shot_key", "coverage_key")
    @classmethod
    def normalize_keys(cls, value: str, info) -> str:
        return _key(value, info.field_name)

    @field_validator(
        "coverage_function",
        "dramatic_function",
        "reason_for_exist",
        "basic_shot_intent",
    )
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("required_visual_information", "must_preserve")
    @classmethod
    def normalize_text_lists(cls, values: tuple[str, ...], info) -> tuple[str, ...]:
        return _unique_text(values, info.field_name)

    @field_validator("subject_refs")
    @classmethod
    def normalize_subjects(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        values = _unique_refs(values, "subject_refs")
        for ref in values:
            if not ref.logical_id.root.startswith("entity:"):
                raise ValueError("subject_refs must reference canonical EntityVersion")
        return values

    @model_validator(mode="after")
    def validate_beat(self) -> "ShotExpansionCandidate":
        if not self.scene_dramatic_beat_ref.logical_id.root.startswith("scene-dramatic-beat:"):
            raise ValueError("ShotExpansionCandidate must bind canonical SceneDramaticBeat")
        return self


class ShotListItem(BaseModel):
    """Sole origin of canonical shot_id; basic purpose only, not FullShotSpec."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    shot_id: LogicalId
    version_id: VersionId
    state: ShotPlanningState = ShotPlanningState.PLANNED
    shot_key: str
    active_profile_ref: VersionRef
    script_lock_ref: VersionRef
    scene_ref: VersionRef
    parent_scene_dramatic_beat_ref: VersionRef
    narrative_trace_ref: VersionRef
    directing_intent_ref: VersionRef
    blocking_plan_ref: VersionRef
    cinematography_objective_ref: VersionRef
    coverage_strategy_ref: VersionRef
    shot_budget_ref: VersionRef
    duration_budget_ref: VersionRef
    coverage_key: str
    dramatic_function: str
    coverage_function: str
    reason_for_exist: str
    duration_budget_seconds: int = Field(gt=0)
    basic_shot_intent: str
    subject_refs: tuple[VersionRef, ...] = ()
    required_visual_information: tuple[str, ...] = ()
    must_preserve: tuple[str, ...] = ()

    @field_validator("shot_key", "coverage_key")
    @classmethod
    def normalize_keys(cls, value: str, info) -> str:
        return _key(value, info.field_name)

    @field_validator(
        "dramatic_function",
        "coverage_function",
        "reason_for_exist",
        "basic_shot_intent",
    )
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("required_visual_information", "must_preserve")
    @classmethod
    def normalize_text_lists(cls, values: tuple[str, ...], info) -> tuple[str, ...]:
        return _unique_text(values, info.field_name)

    @field_validator("subject_refs")
    @classmethod
    def normalize_subjects(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        values = _unique_refs(values, "subject_refs")
        for ref in values:
            if not ref.logical_id.root.startswith("entity:"):
                raise ValueError("subject_refs must reference canonical EntityVersion")
        return values

    @model_validator(mode="after")
    def validate_authority(self) -> "ShotListItem":
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        if self.script_lock_ref.logical_id != script_lock_logical_id(self.project_id):
            raise ValueError("script_lock_ref must bind this project's ScriptLock")
        _project_ref(self.scene_ref, prefix="scene:", project_id=self.project_id, label="scene_ref")
        _project_ref(
            self.parent_scene_dramatic_beat_ref,
            prefix="scene-dramatic-beat:",
            project_id=self.project_id,
            label="parent_scene_dramatic_beat_ref",
        )
        if not self.narrative_trace_ref.logical_id.root.startswith("narrative-trace:"):
            raise ValueError("narrative_trace_ref must reference NarrativeTrace")
        _project_ref(
            self.directing_intent_ref,
            prefix="directing-intent:",
            project_id=self.project_id,
            label="directing_intent_ref",
        )
        _project_ref(
            self.blocking_plan_ref,
            prefix="blocking-plan:",
            project_id=self.project_id,
            label="blocking_plan_ref",
        )
        _project_ref(
            self.cinematography_objective_ref,
            prefix="cinematography-objective:",
            project_id=self.project_id,
            label="cinematography_objective_ref",
        )
        if self.coverage_strategy_ref.logical_id != coverage_strategy_logical_id(
            self.project_id, self.scene_ref
        ):
            raise ValueError("coverage_strategy_ref must bind this Scene's CoverageStrategy")
        if self.shot_budget_ref.logical_id != shot_budget_logical_id(self.project_id, self.scene_ref):
            raise ValueError("shot_budget_ref must bind this Scene's ShotBudget")
        if self.duration_budget_ref.logical_id != duration_budget_logical_id(self.project_id):
            raise ValueError("duration_budget_ref must bind this project's DurationBudget")
        expected = shot_list_item_logical_id(
            self.project_id,
            self.parent_scene_dramatic_beat_ref,
            self.shot_key,
        )
        if self.shot_id != expected:
            raise ValueError(f"shot_id must originate at ShotListItem as {expected.root}")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.shot_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.shot_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="script_lock", source=self.script_lock_ref),
            SourceVersionBinding(role="parent_scene_dramatic_beat", source=self.parent_scene_dramatic_beat_ref),
            SourceVersionBinding(role="parent_narrative_trace", source=self.narrative_trace_ref),
            SourceVersionBinding(role="directing_intent", source=self.directing_intent_ref),
            SourceVersionBinding(role="blocking_plan", source=self.blocking_plan_ref),
            SourceVersionBinding(role="cinematography_objective", source=self.cinematography_objective_ref),
            SourceVersionBinding(role="coverage_strategy", source=self.coverage_strategy_ref),
            SourceVersionBinding(role="shot_budget", source=self.shot_budget_ref),
            SourceVersionBinding(role="duration_budget", source=self.duration_budget_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"subject_{index:03d}", source=ref)
            for index, ref in enumerate(self.subject_refs)
        )
        return tuple(values)


class ManifestCoverageSummary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    coverage_key: str
    shot_count: int = Field(ge=1)

    @field_validator("coverage_key")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        return _key(value, "coverage_key")


class ShotListManifest(BaseModel):
    """Ordered projection over exact ShotListItem refs; contains no Shot payload."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    shot_list_manifest_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    scene_ref: VersionRef
    coverage_strategy_ref: VersionRef
    shot_budget_ref: VersionRef
    duration_budget_ref: VersionRef
    ordered_shot_refs: tuple[VersionRef, ...] = Field(min_length=1)
    coverage_summary: tuple[ManifestCoverageSummary, ...] = Field(min_length=1)
    ordering_rationale: str

    @field_validator("ordering_rationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        return _trimmed(value, "ordering_rationale")

    @field_validator("ordered_shot_refs")
    @classmethod
    def normalize_shots(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        keys = [_ref_key(ref) for ref in values]
        logical_ids = [ref.logical_id.root for ref in values]
        if len(keys) != len(set(keys)) or len(logical_ids) != len(set(logical_ids)):
            raise ValueError("ShotListManifest cannot contain duplicate shot_id/member versions")
        for ref in values:
            if not ref.logical_id.root.startswith("shot-list-item:"):
                raise ValueError("ShotListManifest members must reference ShotListItem")
        return values

    @field_validator("coverage_summary")
    @classmethod
    def normalize_summary(
        cls,
        values: tuple[ManifestCoverageSummary, ...],
    ) -> tuple[ManifestCoverageSummary, ...]:
        keys = [item.coverage_key for item in values]
        if len(keys) != len(set(keys)):
            raise ValueError("coverage_summary keys must be unique")
        return tuple(sorted(values, key=lambda item: item.coverage_key))

    @model_validator(mode="after")
    def validate_authority(self) -> "ShotListManifest":
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        _project_ref(self.scene_ref, prefix="scene:", project_id=self.project_id, label="scene_ref")
        if self.coverage_strategy_ref.logical_id != coverage_strategy_logical_id(
            self.project_id, self.scene_ref
        ):
            raise ValueError("coverage_strategy_ref must bind this Scene's CoverageStrategy")
        if self.shot_budget_ref.logical_id != shot_budget_logical_id(self.project_id, self.scene_ref):
            raise ValueError("shot_budget_ref must bind this Scene's ShotBudget")
        if self.duration_budget_ref.logical_id != duration_budget_logical_id(self.project_id):
            raise ValueError("duration_budget_ref must bind this project's DurationBudget")
        for ref in self.ordered_shot_refs:
            _project_ref(
                ref,
                prefix="shot-list-item:",
                project_id=self.project_id,
                label="ordered_shot_refs",
            )
        expected = shot_list_manifest_logical_id(self.project_id, self.scene_ref)
        if self.shot_list_manifest_id != expected:
            raise ValueError(f"shot_list_manifest_id must be {expected.root}")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.shot_list_manifest_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="scene", source=self.scene_ref),
            SourceVersionBinding(role="coverage_strategy", source=self.coverage_strategy_ref),
            SourceVersionBinding(role="shot_budget", source=self.shot_budget_ref),
            SourceVersionBinding(role="duration_budget", source=self.duration_budget_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"shot_member_{index:03d}", source=ref)
            for index, ref in enumerate(self.ordered_shot_refs)
        )
        return tuple(values)


class ShotExpansionRequest(BaseModel):
    """One scene-level stateless planning request. It carries no canonical output IDs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    active_profile_ref: VersionRef
    script_lock_ref: VersionRef
    scene_ref: VersionRef
    duration_budget_ref: VersionRef
    coverage_strategy_ref: VersionRef
    shot_budget_ref: VersionRef
    planner_rule_version: VersionRef
    beat_contexts: tuple[ShotExpansionBeatContext, ...] = Field(min_length=1)
    candidates: tuple[ShotExpansionCandidate, ...] = Field(min_length=1)
    ordering_rationale: str

    @field_validator("ordering_rationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        return _trimmed(value, "ordering_rationale")

    @field_validator("beat_contexts")
    @classmethod
    def normalize_contexts(
        cls,
        values: tuple[ShotExpansionBeatContext, ...],
    ) -> tuple[ShotExpansionBeatContext, ...]:
        keys = [_ref_key(value.scene_dramatic_beat_ref) for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("beat_contexts must be unique per SceneDramaticBeat")
        return tuple(sorted(values, key=lambda value: _ref_key(value.scene_dramatic_beat_ref)))

    @field_validator("candidates")
    @classmethod
    def normalize_candidates(
        cls,
        values: tuple[ShotExpansionCandidate, ...],
    ) -> tuple[ShotExpansionCandidate, ...]:
        shot_keys = [value.shot_key for value in values]
        if len(shot_keys) != len(set(shot_keys)):
            raise ValueError("ShotExpansion shot_key values must be unique within scene scope")
        return values

    @model_validator(mode="after")
    def validate_scope(self) -> "ShotExpansionRequest":
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        if self.script_lock_ref.logical_id != script_lock_logical_id(self.project_id):
            raise ValueError("script_lock_ref must bind this project's ScriptLock")
        _project_ref(self.scene_ref, prefix="scene:", project_id=self.project_id, label="scene_ref")
        if self.duration_budget_ref.logical_id != duration_budget_logical_id(self.project_id):
            raise ValueError("duration_budget_ref must bind this project's DurationBudget")
        if self.coverage_strategy_ref.logical_id != coverage_strategy_logical_id(
            self.project_id, self.scene_ref
        ):
            raise ValueError("coverage_strategy_ref must bind this Scene's CoverageStrategy")
        if self.shot_budget_ref.logical_id != shot_budget_logical_id(self.project_id, self.scene_ref):
            raise ValueError("shot_budget_ref must bind this Scene's ShotBudget")
        beat_keys = {_ref_key(value.scene_dramatic_beat_ref) for value in self.beat_contexts}
        if any(_ref_key(candidate.scene_dramatic_beat_ref) not in beat_keys for candidate in self.candidates):
            raise ValueError("every ShotExpansion candidate must bind a declared beat_context")
        return self


ShotPlanningValue: TypeAlias = CoverageStrategy | ShotBudget | ShotListItem | ShotListManifest


class ShotPlanningArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: ShotPlanningValue

    @model_validator(mode="after")
    def validate_artifact(self) -> "ShotPlanningArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("shot planning artifact logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("shot planning artifact version mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError("shot planning provenance must exactly bind declared source versions")
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(
            logical_id=self.metadata.logical_id,
            version_id=self.metadata.version_id,
        )


class ShotExpansionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    shot_items: tuple[ShotPlanningArtifact, ...]
    shot_traces: tuple[NarrativeTraceArtifact, ...]
    manifest: ShotPlanningArtifact


def build_shot_planning_provenance(
    value: ShotPlanningValue,
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


class ShotPlanningRepository:
    """Exact-version repository plus stateless ShotExpansion service."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)
        self.traces = NarrativeTraceRepository(writer)

    async def create_coverage_strategy(
        self,
        *,
        value: CoverageStrategy,
        provenance: Provenance,
        created_at: datetime,
    ) -> ShotPlanningArtifact:
        await self._assert_coverage_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_coverage_strategy(
        self,
        *,
        value: CoverageStrategy,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ShotPlanningArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_coverage_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="CoverageStrategy",
            cause="CoverageStrategy revision",
            scope="coverage_shot_descendants",
            repair="Replan affected ShotBudget/ShotExpansion/ShotList outputs from current coverage authority.",
        )

    async def create_shot_budget(
        self,
        *,
        value: ShotBudget,
        provenance: Provenance,
        created_at: datetime,
    ) -> ShotPlanningArtifact:
        await self._assert_shot_budget_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_shot_budget(
        self,
        *,
        value: ShotBudget,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ShotPlanningArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_shot_budget_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="ShotBudget",
            cause="ShotBudget revision",
            scope="shot_planning_descendants",
            repair="Replan affected ShotListItems/manifests from current shot budget.",
        )

    async def create_shot_list_item(
        self,
        *,
        value: ShotListItem,
        trace_version: VersionId,
        provenance: Provenance,
        created_at: datetime,
    ) -> tuple[ShotPlanningArtifact, NarrativeTraceArtifact]:
        """Allocate shot_id and its mandatory NarrativeTrace as one creation boundary."""

        await self._assert_item_inputs(value)
        artifact = await self._create_approved(value, provenance, created_at)
        trace = await self._create_shot_trace(
            value=value,
            artifact=artifact,
            trace_version=trace_version,
            provenance=provenance,
            created_at=created_at,
        )
        return artifact, trace

    async def revise_shot_list_item(
        self,
        *,
        value: ShotListItem,
        predecessor: VersionRef,
        trace_version: VersionId,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[
        ShotPlanningArtifact,
        NarrativeTraceArtifact,
        tuple[InvalidationRecord, ...],
    ]:
        """Revise ShotListItem and advance the same shot lineage trace."""

        await self._assert_item_inputs(value)
        previous_trace = await self.traces.get_current_trace(
            artifact_type=NarrativeArtifactType.SHOT_LIST_ITEM,
            traced_ref=predecessor,
        )
        if previous_trace is None or await self.traces.trace_state(previous_trace.ref) is not NarrativeTraceState.CURRENT:
            raise ShotPlanningGateBlocked(
                "ShotListItem revision requires exact CURRENT NarrativeTrace for predecessor"
            )
        trace_pointer = await self.versions.get_current(previous_trace.value.logical_id)
        if trace_pointer is None:
            raise ShotPlanningGateBlocked("ShotListItem NarrativeTrace current pointer missing")
        artifact, records = await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="ShotListItem",
            cause="ShotListItem revision",
            scope="shot_realization_descendants",
            repair="Re-evaluate eligibility and recompute dependent FullShotSpec/ShotIR/provider derivatives.",
        )
        shot_trace = NarrativeTraceRecord(
            project_id=value.project_id,
            artifact_type=NarrativeArtifactType.SHOT_LIST_ITEM,
            trace_version=trace_version,
            traced_ref=artifact.ref,
            root_story_core_ref=previous_trace.value.root_story_core_ref,
            parent_refs=(value.parent_scene_dramatic_beat_ref,),
            source_version_refs=self._shot_trace_sources(value),
        )
        trace_artifact = await self.traces.revise_trace(
            value=shot_trace,
            predecessor=previous_trace.ref,
            provenance=build_narrative_trace_provenance(
                shot_trace,
                actor_ref=provenance.actor_ref,
                reason=f"{provenance.reason}: shot narrative lineage successor",
                recorded_at=created_at,
                source_refs=provenance.source_refs,
                rule_version=provenance.rule_version,
                correlation_id=provenance.correlation_id,
            ),
            created_at=created_at,
            expected_revision=trace_pointer.revision,
        )
        return artifact, trace_artifact, records

    async def create_manifest(
        self,
        *,
        value: ShotListManifest,
        provenance: Provenance,
        created_at: datetime,
    ) -> ShotPlanningArtifact:
        await self._assert_manifest_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_manifest(
        self,
        *,
        value: ShotListManifest,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ShotPlanningArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_manifest_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="ShotListManifest",
            cause="ShotListManifest revision",
            scope="shot_manifest_consumers",
            repair="Rebuild dependent eligibility/realization ordering from current manifest membership.",
        )

    async def get_coverage_strategy(self, ref: VersionRef) -> ShotPlanningArtifact | None:
        return await self._get_typed(ref, CoverageStrategy, "coverage-strategy:")

    async def get_shot_budget(self, ref: VersionRef) -> ShotPlanningArtifact | None:
        return await self._get_typed(ref, ShotBudget, "shot-budget:")

    async def get_shot_list_item(self, ref: VersionRef) -> ShotPlanningArtifact | None:
        return await self._get_typed(ref, ShotListItem, "shot-list-item:")

    async def get_manifest(self, ref: VersionRef) -> ShotPlanningArtifact | None:
        return await self._get_typed(ref, ShotListManifest, "shot-list-manifest:")

    async def expand_scene(
        self,
        *,
        request: ShotExpansionRequest,
        shot_item_version: VersionId,
        shot_trace_version: VersionId,
        manifest_version: VersionId,
        actor_ref: str,
        reason: str,
        recorded_at: datetime,
        source_refs: tuple[str, ...] = (),
        correlation_id: str | None = None,
    ) -> ShotExpansionResult:
        """Validate a whole scene plan before allocating any canonical shot_id."""

        validated = await self._validate_expansion_request(request)
        coverage: CoverageStrategy = validated["coverage"]
        budget: ShotBudget = validated["budget"]
        context_by_beat: dict[tuple[str, str], ShotExpansionBeatContext] = validated["contexts"]

        item_values: list[ShotListItem] = []
        for candidate in request.candidates:
            context = context_by_beat[_ref_key(candidate.scene_dramatic_beat_ref)]
            value = ShotListItem(
                project_id=request.project_id,
                shot_id=shot_list_item_logical_id(
                    request.project_id,
                    candidate.scene_dramatic_beat_ref,
                    candidate.shot_key,
                ),
                version_id=shot_item_version,
                state=ShotPlanningState.PLANNED,
                shot_key=candidate.shot_key,
                active_profile_ref=request.active_profile_ref,
                script_lock_ref=request.script_lock_ref,
                scene_ref=request.scene_ref,
                parent_scene_dramatic_beat_ref=candidate.scene_dramatic_beat_ref,
                narrative_trace_ref=context.narrative_trace_ref,
                directing_intent_ref=context.directing_intent_ref,
                blocking_plan_ref=context.blocking_plan_ref,
                cinematography_objective_ref=context.cinematography_objective_ref,
                coverage_strategy_ref=request.coverage_strategy_ref,
                shot_budget_ref=request.shot_budget_ref,
                duration_budget_ref=request.duration_budget_ref,
                coverage_key=candidate.coverage_key,
                dramatic_function=candidate.dramatic_function,
                coverage_function=candidate.coverage_function,
                reason_for_exist=candidate.reason_for_exist,
                duration_budget_seconds=candidate.duration_seconds,
                basic_shot_intent=candidate.basic_shot_intent,
                subject_refs=candidate.subject_refs,
                required_visual_information=candidate.required_visual_information,
                must_preserve=candidate.must_preserve,
            )
            if await self.versions.get_current(value.logical_id) is not None:
                raise ShotPlanningIdentityError(
                    f"shot_id already exists; ShotExpansion cannot allocate parallel/reused identity: {value.shot_id.root}"
                )
            item_values.append(value)

        manifest_id = shot_list_manifest_logical_id(request.project_id, request.scene_ref)
        if await self.versions.get_current(manifest_id) is not None:
            raise ShotPlanningIdentityError(
                "scene already has current ShotListManifest; use successor manifest revision, not parallel expansion"
            )

        item_artifacts: list[ShotPlanningArtifact] = []
        trace_artifacts: list[NarrativeTraceArtifact] = []
        for value in item_values:
            provenance = build_shot_planning_provenance(
                value,
                actor_ref=actor_ref,
                reason=reason,
                recorded_at=recorded_at,
                source_refs=source_refs,
                rule_version=request.planner_rule_version,
                correlation_id=correlation_id,
            )
            artifact, trace_artifact = await self.create_shot_list_item(
                value=value,
                trace_version=shot_trace_version,
                provenance=provenance,
                created_at=recorded_at,
            )
            item_artifacts.append(artifact)
            trace_artifacts.append(trace_artifact)

        counts: dict[str, int] = {}
        for candidate in request.candidates:
            counts[candidate.coverage_key] = counts.get(candidate.coverage_key, 0) + 1
        manifest = ShotListManifest(
            project_id=request.project_id,
            shot_list_manifest_id=manifest_id,
            version_id=manifest_version,
            active_profile_ref=request.active_profile_ref,
            scene_ref=request.scene_ref,
            coverage_strategy_ref=coverage.ref,
            shot_budget_ref=budget.ref,
            duration_budget_ref=request.duration_budget_ref,
            ordered_shot_refs=tuple(item.ref for item in item_artifacts),
            coverage_summary=tuple(
                ManifestCoverageSummary(coverage_key=key, shot_count=counts[key])
                for key in sorted(counts)
            ),
            ordering_rationale=request.ordering_rationale,
        )
        manifest_artifact = await self.create_manifest(
            value=manifest,
            provenance=build_shot_planning_provenance(
                manifest,
                actor_ref=actor_ref,
                reason=f"{reason}: manifest projection",
                recorded_at=recorded_at,
                source_refs=source_refs,
                rule_version=request.planner_rule_version,
                correlation_id=correlation_id,
            ),
            created_at=recorded_at,
        )
        return ShotExpansionResult(
            shot_items=tuple(item_artifacts),
            shot_traces=tuple(trace_artifacts),
            manifest=manifest_artifact,
        )

    def _shot_trace_sources(self, value: ShotListItem) -> tuple[VersionRef, ...]:
        return (
            value.narrative_trace_ref,
            value.active_profile_ref,
            value.script_lock_ref,
            value.directing_intent_ref,
            value.blocking_plan_ref,
            value.cinematography_objective_ref,
            value.coverage_strategy_ref,
            value.shot_budget_ref,
            value.duration_budget_ref,
        )

    async def _create_shot_trace(
        self,
        *,
        value: ShotListItem,
        artifact: ShotPlanningArtifact,
        trace_version: VersionId,
        provenance: Provenance,
        created_at: datetime,
    ) -> NarrativeTraceArtifact:
        parent_trace = await self._assert_trace(
            project_id=value.project_id,
            beat_ref=value.parent_scene_dramatic_beat_ref,
            trace_ref=value.narrative_trace_ref,
        )
        shot_trace = NarrativeTraceRecord(
            project_id=value.project_id,
            artifact_type=NarrativeArtifactType.SHOT_LIST_ITEM,
            trace_version=trace_version,
            traced_ref=artifact.ref,
            root_story_core_ref=parent_trace.value.root_story_core_ref,
            parent_refs=(value.parent_scene_dramatic_beat_ref,),
            source_version_refs=self._shot_trace_sources(value),
        )
        return await self.traces.create_trace(
            value=shot_trace,
            provenance=build_narrative_trace_provenance(
                shot_trace,
                actor_ref=provenance.actor_ref,
                reason=f"{provenance.reason}: shot narrative lineage",
                recorded_at=created_at,
                source_refs=provenance.source_refs,
                rule_version=provenance.rule_version,
                correlation_id=provenance.correlation_id,
            ),
            created_at=created_at,
        )

    async def _create_approved(
        self,
        value: ShotPlanningValue,
        provenance: Provenance,
        created_at: datetime,
    ) -> ShotPlanningArtifact:
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
        artifact = ShotPlanningArtifact(metadata=stored.metadata, value=value)
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
        value: ShotPlanningValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
        label: str,
        cause: str,
        scope: str,
        repair: str,
    ) -> tuple[ShotPlanningArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise ShotPlanningIdentityError(f"{label} revision must preserve logical identity")
        await self._assert_current_valid(predecessor, f"{label} predecessor", _ACCEPTED)
        previous = await self.versions.get_version(predecessor)
        if previous is None:
            raise ShotPlanningIdentityError(f"{label} predecessor does not exist")
        previous_payload = dict(previous.payload)
        current_payload = value.model_dump(mode="json")
        previous_payload.pop("version_id", None)
        current_payload.pop("version_id", None)
        if previous_payload == current_payload:
            raise ShotPlanningIdentityError(f"{label} successor requires semantic/source change")
        self._assert_provenance(value, provenance)
        pointer = await self.versions.get_current(value.logical_id)
        if (
            pointer is None
            or pointer.version_id != predecessor.version_id
            or pointer.status not in _ACCEPTED
            or pointer.revision != expected_revision
        ):
            raise ShotPlanningIdentityError(
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
        artifact = ShotPlanningArtifact(metadata=stored.metadata, value=value)
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

    async def _get_typed(self, ref: VersionRef, model, prefix: str) -> ShotPlanningArtifact | None:
        if not ref.logical_id.root.startswith(prefix):
            raise ShotPlanningIdentityError(f"expected {prefix.rstrip(':')} ref")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = model.model_validate(stored.payload)
        if value.logical_id != ref.logical_id:
            raise ShotPlanningIdentityError("stored shot planning payload logical identity mismatch")
        return ShotPlanningArtifact(metadata=stored.metadata, value=value)

    async def _register_dependencies(self, artifact: ShotPlanningArtifact) -> None:
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
                else "shot_planning_input"
            )
            await self.graph.create_edge(
                source=source,
                dependent=artifact.ref,
                edge_type=edge_type,
                dependency_reason=" + ".join(sorted(set(grouped[key]))),
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    def _assert_provenance(self, value: ShotPlanningValue, provenance: Provenance) -> None:
        if provenance.source_versions != value.source_bindings():
            raise ShotPlanningIdentityError(
                "shot planning provenance must exactly bind declared source versions"
            )

    async def _assert_current_valid(
        self,
        ref: VersionRef,
        label: str,
        allowed: set[LifecycleState],
    ) -> None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise ShotPlanningGateBlocked(f"{label} exact version does not exist")
        pointer = await self.versions.get_current(ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != ref.version_id
            or pointer.status not in allowed
        ):
            raise ShotPlanningGateBlocked(f"{label} is not exact current accepted version")
        unresolved = await self.invalidations.list_unresolved()
        if any(
            record.affected_object_id == ref.logical_id
            and record.affected_object_version == ref.version_id
            for record in unresolved
        ):
            raise ShotPlanningGateBlocked(f"{label} has unresolved durable invalidation")

    async def _load(self, ref: VersionRef, model, label: str):
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise ShotPlanningGateBlocked(f"{label} exact version does not exist")
        try:
            return model.model_validate(stored.payload)
        except Exception as exc:  # pydantic validation is converted to domain gate failure
            raise ShotPlanningGateBlocked(f"{label} payload is invalid") from exc

    async def _assert_profile(self, project_id: LogicalId, ref: VersionRef) -> ActiveProductionProfile:
        if ref.logical_id != _active_profile_id(project_id):
            raise ShotPlanningGateBlocked("ActiveProductionProfile belongs to a different project")
        await self._assert_current_valid(ref, "ActiveProductionProfile", {LifecycleState.LOCKED})
        value = await self._load(ref, ActiveProductionProfile, "ActiveProductionProfile")
        if value.project_id != project_id:
            raise ShotPlanningGateBlocked("ActiveProductionProfile project mismatch")
        return value

    async def _assert_scene(
        self,
        project_id: LogicalId,
        scene_ref: VersionRef,
        profile_ref: VersionRef,
    ) -> Scene:
        await self._assert_current_valid(scene_ref, "Scene", _ACCEPTED)
        scene = await self._load(scene_ref, Scene, "Scene")
        if scene.project_id != project_id or scene.active_profile_ref != profile_ref:
            raise ShotPlanningGateBlocked("Scene project/profile lineage mismatch")
        return scene

    async def _assert_beat(
        self,
        project_id: LogicalId,
        beat_ref: VersionRef,
        profile_ref: VersionRef,
        scene_ref: VersionRef,
    ) -> SceneDramaticBeat:
        await self._assert_current_valid(beat_ref, "SceneDramaticBeat", _ACCEPTED)
        beat = await self._load(beat_ref, SceneDramaticBeat, "SceneDramaticBeat")
        if (
            beat.project_id != project_id
            or beat.active_profile_ref != profile_ref
            or beat.scene_ref != scene_ref
        ):
            raise ShotPlanningGateBlocked("SceneDramaticBeat scene/profile lineage mismatch")
        return beat

    async def _assert_script_lock(
        self,
        project_id: LogicalId,
        profile_ref: VersionRef,
        ref: VersionRef,
    ) -> ScriptLockManifest:
        if ref.logical_id != script_lock_logical_id(project_id):
            raise ShotPlanningGateBlocked("ScriptLock belongs to a different project")
        await self._assert_current_valid(ref, "ScriptLock", {LifecycleState.LOCKED})
        value = await self._load(ref, ScriptLockManifest, "ScriptLock")
        if value.project_id != project_id or value.active_profile_ref != profile_ref:
            raise ShotPlanningGateBlocked("ScriptLock project/profile lineage mismatch")
        return value

    async def _assert_duration_budget(
        self,
        project_id: LogicalId,
        profile_ref: VersionRef,
        ref: VersionRef,
    ) -> DurationBudget:
        if ref.logical_id != duration_budget_logical_id(project_id):
            raise ShotPlanningGateBlocked("DurationBudget belongs to a different project")
        await self._assert_current_valid(ref, "DurationBudget", _ACCEPTED)
        value = await self._load(ref, DurationBudget, "DurationBudget")
        if value.project_id != project_id or value.active_profile_ref != profile_ref:
            raise ShotPlanningGateBlocked("DurationBudget project/profile lineage mismatch")
        return value

    async def _assert_structure_profile(
        self,
        project_id: LogicalId,
        profile_ref: VersionRef,
        ref: VersionRef,
    ) -> StructureProfile:
        if ref.logical_id != structure_profile_logical_id(project_id):
            raise ShotPlanningGateBlocked("StructureProfile belongs to a different project")
        await self._assert_current_valid(ref, "StructureProfile", _ACCEPTED)
        value = await self._load(ref, StructureProfile, "StructureProfile")
        if value.project_id != project_id or value.active_profile_ref != profile_ref:
            raise ShotPlanningGateBlocked("StructureProfile project/profile lineage mismatch")
        return value

    async def _assert_trace(
        self,
        *,
        project_id: LogicalId,
        beat_ref: VersionRef,
        trace_ref: VersionRef,
    ) -> NarrativeTraceArtifact:
        trace = await self.traces.get_trace(trace_ref)
        if trace is None:
            raise ShotPlanningGateBlocked("NarrativeTrace exact version does not exist")
        if (
            trace.value.project_id != project_id
            or trace.value.artifact_type is not NarrativeArtifactType.SCENE_DRAMATIC_BEAT
            or trace.value.traced_ref != beat_ref
        ):
            raise ShotPlanningGateBlocked("NarrativeTrace does not trace exact SceneDramaticBeat")
        if await self.traces.trace_state(trace_ref) is not NarrativeTraceState.CURRENT:
            raise ShotPlanningGateBlocked("NarrativeTrace is stale/superseded/invalidated")
        return trace

    async def _assert_directing_chain(
        self,
        *,
        project_id: LogicalId,
        profile_ref: VersionRef,
        scene_ref: VersionRef,
        script_lock_ref: VersionRef,
        context: ShotExpansionBeatContext,
    ) -> tuple[DirectingIntent, BlockingPlan, CinematographyObjective]:
        await self._assert_beat(
            project_id,
            context.scene_dramatic_beat_ref,
            profile_ref,
            scene_ref,
        )
        await self._assert_current_valid(context.directing_intent_ref, "DirectingIntent", _ACCEPTED)
        directing = await self._load(context.directing_intent_ref, DirectingIntent, "DirectingIntent")
        await self._assert_current_valid(context.blocking_plan_ref, "BlockingPlan", _ACCEPTED)
        blocking = await self._load(context.blocking_plan_ref, BlockingPlan, "BlockingPlan")
        await self._assert_current_valid(
            context.cinematography_objective_ref,
            "CinematographyObjective",
            _ACCEPTED,
        )
        cine = await self._load(
            context.cinematography_objective_ref,
            CinematographyObjective,
            "CinematographyObjective",
        )
        beat_ref = context.scene_dramatic_beat_ref
        if (
            directing.project_id != project_id
            or directing.active_profile_ref != profile_ref
            or directing.script_lock_ref != script_lock_ref
            or directing.scene_dramatic_beat_ref != beat_ref
            or blocking.project_id != project_id
            or blocking.active_profile_ref != profile_ref
            or blocking.scene_dramatic_beat_ref != beat_ref
            or blocking.directing_intent_ref != context.directing_intent_ref
            or cine.project_id != project_id
            or cine.active_profile_ref != profile_ref
            or cine.scene_dramatic_beat_ref != beat_ref
            or cine.directing_intent_ref != context.directing_intent_ref
            or cine.blocking_plan_ref != context.blocking_plan_ref
        ):
            raise ShotPlanningGateBlocked("directing/blocking/cinematography exact lineage mismatch")
        return directing, blocking, cine

    async def _assert_coverage_inputs(self, value: CoverageStrategy) -> None:
        await self._assert_profile(value.project_id, value.active_profile_ref)
        await self._assert_scene(value.project_id, value.scene_ref, value.active_profile_ref)
        await self._assert_duration_budget(
            value.project_id,
            value.active_profile_ref,
            value.duration_budget_ref,
        )
        current_scene_beats: dict[tuple[str, str], VersionRef] = {}
        beat_prefix = f"scene-dramatic-beat:{value.project_id.root}:"
        for edge in await self.graph.list_outgoing(value.scene_ref):
            beat_ref = edge.dependent_ref
            if not beat_ref.logical_id.root.startswith(beat_prefix):
                continue
            pointer = await self.versions.get_current(beat_ref.logical_id)
            if (
                pointer is not None
                and pointer.version_id == beat_ref.version_id
                and pointer.status in _ACCEPTED
            ):
                beat = await self._load(beat_ref, SceneDramaticBeat, "SceneDramaticBeat")
                if beat.scene_ref == value.scene_ref:
                    current_scene_beats[_ref_key(beat_ref)] = beat_ref
        declared_beats = {
            _ref_key(binding.scene_dramatic_beat_ref): binding.scene_dramatic_beat_ref
            for binding in value.beat_bindings
        }
        if not current_scene_beats or set(declared_beats) != set(current_scene_beats):
            raise ShotPlanningGateBlocked(
                "SHOT_MISSING_REQUIRED_COVERAGE: CoverageStrategy must cover exact current SceneDramaticBeat set"
            )
        for binding in value.beat_bindings:
            await self._assert_beat(
                value.project_id,
                binding.scene_dramatic_beat_ref,
                value.active_profile_ref,
                value.scene_ref,
            )
            await self._assert_current_valid(binding.blocking_plan_ref, "BlockingPlan", _ACCEPTED)
            blocking = await self._load(binding.blocking_plan_ref, BlockingPlan, "BlockingPlan")
            await self._assert_current_valid(
                binding.cinematography_objective_ref,
                "CinematographyObjective",
                _ACCEPTED,
            )
            cine = await self._load(
                binding.cinematography_objective_ref,
                CinematographyObjective,
                "CinematographyObjective",
            )
            if (
                blocking.project_id != value.project_id
                or blocking.active_profile_ref != value.active_profile_ref
                or blocking.scene_dramatic_beat_ref != binding.scene_dramatic_beat_ref
                or cine.project_id != value.project_id
                or cine.active_profile_ref != value.active_profile_ref
                or cine.scene_dramatic_beat_ref != binding.scene_dramatic_beat_ref
                or cine.blocking_plan_ref != binding.blocking_plan_ref
                or cine.directing_intent_ref != blocking.directing_intent_ref
            ):
                raise ShotPlanningGateBlocked("CoverageStrategy beat authority lineage mismatch")

    async def _assert_shot_budget_inputs(self, value: ShotBudget) -> None:
        await self._assert_profile(value.project_id, value.active_profile_ref)
        await self._assert_scene(value.project_id, value.scene_ref, value.active_profile_ref)
        structure = await self._assert_structure_profile(
            value.project_id,
            value.active_profile_ref,
            value.structure_profile_ref,
        )
        duration = await self._assert_duration_budget(
            value.project_id,
            value.active_profile_ref,
            value.duration_budget_ref,
        )
        await self._assert_current_valid(value.coverage_strategy_ref, "CoverageStrategy", _ACCEPTED)
        coverage_artifact = await self.get_coverage_strategy(value.coverage_strategy_ref)
        if coverage_artifact is None:
            raise ShotPlanningGateBlocked("CoverageStrategy exact version does not exist")
        coverage = coverage_artifact.value
        assert isinstance(coverage, CoverageStrategy)
        if (
            coverage.project_id != value.project_id
            or coverage.active_profile_ref != value.active_profile_ref
            or coverage.scene_ref != value.scene_ref
            or coverage.duration_budget_ref != value.duration_budget_ref
            or duration.structure_profile_ref != structure.ref
        ):
            raise ShotPlanningGateBlocked("ShotBudget planning lineage mismatch")

        scene_allocations = [
            item
            for item in duration.allocations
            if item.level is BudgetLevel.SCENE and item.target_ref == value.scene_ref
        ]
        if len(scene_allocations) != 1:
            raise ShotPlanningGateBlocked(
                "ShotBudget requires exactly one DurationBudget allocation for the Scene"
            )
        if value.scene_duration_seconds != scene_allocations[0].seconds:
            raise ShotPlanningGateBlocked(
                "ShotBudget scene_duration_seconds must equal exact DurationBudget Scene allocation"
            )
        if value.tolerance_seconds != duration.tolerance_seconds:
            raise ShotPlanningGateBlocked(
                "ShotBudget tolerance_seconds must equal governing DurationBudget tolerance"
            )
        required_min = sum(item.minimum_shots for item in coverage.requirements)
        allowed_max = sum(item.maximum_shots for item in coverage.requirements)
        if value.shot_count_range.minimum < required_min:
            raise ShotPlanningGateBlocked(
                "SHOT_MISSING_REQUIRED_COVERAGE: ShotBudget minimum cannot satisfy CoverageStrategy"
            )
        if value.shot_count_range.maximum > allowed_max:
            raise ShotPlanningGateBlocked(
                "ShotBudget maximum exceeds declared non-redundant CoverageStrategy capacity"
            )

    async def _assert_item_inputs(self, value: ShotListItem) -> None:
        if value.state is not ShotPlanningState.PLANNED:
            raise ShotPlanningGateBlocked(
                "IMP-031 may persist ShotListItem only as PLANNED; eligibility belongs to IMP-032 ShotEligibilityGate"
            )
        await self._assert_profile(value.project_id, value.active_profile_ref)
        await self._assert_script_lock(value.project_id, value.active_profile_ref, value.script_lock_ref)
        await self._assert_scene(value.project_id, value.scene_ref, value.active_profile_ref)
        await self._assert_beat(
            value.project_id,
            value.parent_scene_dramatic_beat_ref,
            value.active_profile_ref,
            value.scene_ref,
        )
        await self._assert_trace(
            project_id=value.project_id,
            beat_ref=value.parent_scene_dramatic_beat_ref,
            trace_ref=value.narrative_trace_ref,
        )
        context = ShotExpansionBeatContext(
            scene_dramatic_beat_ref=value.parent_scene_dramatic_beat_ref,
            narrative_trace_ref=value.narrative_trace_ref,
            directing_intent_ref=value.directing_intent_ref,
            blocking_plan_ref=value.blocking_plan_ref,
            cinematography_objective_ref=value.cinematography_objective_ref,
        )
        _, blocking, _ = await self._assert_directing_chain(
            project_id=value.project_id,
            profile_ref=value.active_profile_ref,
            scene_ref=value.scene_ref,
            script_lock_ref=value.script_lock_ref,
            context=context,
        )
        await self._assert_current_valid(value.coverage_strategy_ref, "CoverageStrategy", _ACCEPTED)
        coverage_artifact = await self.get_coverage_strategy(value.coverage_strategy_ref)
        await self._assert_current_valid(value.shot_budget_ref, "ShotBudget", _ACCEPTED)
        budget_artifact = await self.get_shot_budget(value.shot_budget_ref)
        await self._assert_duration_budget(
            value.project_id,
            value.active_profile_ref,
            value.duration_budget_ref,
        )
        if coverage_artifact is None or budget_artifact is None:
            raise ShotPlanningGateBlocked("ShotListItem planning inputs are missing")
        coverage = coverage_artifact.value
        budget = budget_artifact.value
        assert isinstance(coverage, CoverageStrategy)
        assert isinstance(budget, ShotBudget)
        requirement = next(
            (
                item
                for item in coverage.requirements
                if item.coverage_key == value.coverage_key
                and item.scene_dramatic_beat_ref == value.parent_scene_dramatic_beat_ref
            ),
            None,
        )
        if requirement is None or requirement.coverage_function != value.coverage_function:
            raise ShotPlanningGateBlocked(
                "SHOT_MISSING_REQUIRED_COVERAGE: ShotListItem coverage role is not authorized"
            )
        if not budget.shot_duration_range_seconds.contains(value.duration_budget_seconds):
            raise ShotPlanningGateBlocked("ShotListItem duration lies outside ShotBudget range")
        blocking_entities = {
            _ref_key(item.entity_ref)
            for item in (*blocking.positions, *blocking.movements)
        }
        if any(_ref_key(ref) not in blocking_entities for ref in value.subject_refs):
            raise ShotPlanningGateBlocked(
                "ShotListItem subject must be declared by exact BlockingPlan"
            )

    async def _assert_manifest_inputs(self, value: ShotListManifest) -> None:
        await self._assert_profile(value.project_id, value.active_profile_ref)
        await self._assert_scene(value.project_id, value.scene_ref, value.active_profile_ref)
        await self._assert_current_valid(value.coverage_strategy_ref, "CoverageStrategy", _ACCEPTED)
        coverage_artifact = await self.get_coverage_strategy(value.coverage_strategy_ref)
        await self._assert_current_valid(value.shot_budget_ref, "ShotBudget", _ACCEPTED)
        budget_artifact = await self.get_shot_budget(value.shot_budget_ref)
        await self._assert_duration_budget(
            value.project_id,
            value.active_profile_ref,
            value.duration_budget_ref,
        )
        if coverage_artifact is None or budget_artifact is None:
            raise ShotPlanningGateBlocked("ShotListManifest planning inputs are missing")
        coverage = coverage_artifact.value
        budget = budget_artifact.value
        assert isinstance(coverage, CoverageStrategy)
        assert isinstance(budget, ShotBudget)
        if (
            coverage.scene_ref != value.scene_ref
            or budget.scene_ref != value.scene_ref
            or budget.coverage_strategy_ref != coverage.ref
            or budget.duration_budget_ref != value.duration_budget_ref
        ):
            raise ShotPlanningGateBlocked("ShotListManifest planning lineage mismatch")

        items: list[ShotListItem] = []
        for ref in value.ordered_shot_refs:
            await self._assert_current_valid(ref, "ShotListItem", _ACCEPTED)
            artifact = await self.get_shot_list_item(ref)
            if artifact is None:
                raise ShotPlanningGateBlocked("ShotListManifest contains dangling ShotListItem")
            item = artifact.value
            assert isinstance(item, ShotListItem)
            if (
                item.project_id != value.project_id
                or item.scene_ref != value.scene_ref
                or item.coverage_strategy_ref != coverage.ref
                or item.shot_budget_ref != budget.ref
                or item.duration_budget_ref != value.duration_budget_ref
                or item.state is ShotPlanningState.REJECTED
            ):
                raise ShotPlanningGateBlocked("ShotListManifest member lineage/status mismatch")
            items.append(item)

        if not budget.shot_count_range.contains(len(items)):
            raise ShotPlanningGateBlocked("BUDGET_SHOT_OVERFLOW: manifest shot count outside ShotBudget")
        total_seconds = sum(item.duration_budget_seconds for item in items)
        if abs(total_seconds - budget.scene_duration_seconds) > budget.tolerance_seconds:
            raise ShotPlanningGateBlocked(
                "BUDGET_SHOT_OVERFLOW: manifest durations do not reconcile to Scene budget"
            )
        counts: dict[str, int] = {}
        for item in items:
            counts[item.coverage_key] = counts.get(item.coverage_key, 0) + 1
        requirement_by_key = {item.coverage_key: item for item in coverage.requirements}
        for key, requirement in requirement_by_key.items():
            count = counts.get(key, 0)
            if not requirement.minimum_shots <= count <= requirement.maximum_shots:
                raise ShotPlanningGateBlocked(
                    "SHOT_MISSING_REQUIRED_COVERAGE: manifest coverage count outside requirement"
                )
        if set(counts) != set(requirement_by_key):
            raise ShotPlanningGateBlocked("manifest contains undeclared coverage role")
        declared_summary = {item.coverage_key: item.shot_count for item in value.coverage_summary}
        if declared_summary != counts:
            raise ShotPlanningGateBlocked("manifest coverage_summary does not match member refs")

    async def _validate_expansion_request(self, request: ShotExpansionRequest) -> dict:
        await self._assert_profile(request.project_id, request.active_profile_ref)
        await self._assert_script_lock(
            request.project_id,
            request.active_profile_ref,
            request.script_lock_ref,
        )
        await self._assert_scene(request.project_id, request.scene_ref, request.active_profile_ref)
        duration = await self._assert_duration_budget(
            request.project_id,
            request.active_profile_ref,
            request.duration_budget_ref,
        )
        await self._assert_current_valid(request.coverage_strategy_ref, "CoverageStrategy", _ACCEPTED)
        coverage_artifact = await self.get_coverage_strategy(request.coverage_strategy_ref)
        await self._assert_current_valid(request.shot_budget_ref, "ShotBudget", _ACCEPTED)
        budget_artifact = await self.get_shot_budget(request.shot_budget_ref)
        if coverage_artifact is None or budget_artifact is None:
            raise ShotPlanningGateBlocked("ShotExpansion planning input missing")
        coverage = coverage_artifact.value
        budget = budget_artifact.value
        assert isinstance(coverage, CoverageStrategy)
        assert isinstance(budget, ShotBudget)
        if (
            coverage.scene_ref != request.scene_ref
            or coverage.duration_budget_ref != request.duration_budget_ref
            or budget.scene_ref != request.scene_ref
            or budget.coverage_strategy_ref != coverage.ref
            or budget.duration_budget_ref != request.duration_budget_ref
        ):
            raise ShotPlanningGateBlocked("ShotExpansion coverage/budget lineage mismatch")

        context_by_beat: dict[tuple[str, str], ShotExpansionBeatContext] = {}
        trace_by_beat: dict[tuple[str, str], NarrativeTraceArtifact] = {}
        coverage_bindings = {
            _ref_key(item.scene_dramatic_beat_ref): item for item in coverage.beat_bindings
        }
        for context in request.beat_contexts:
            key = _ref_key(context.scene_dramatic_beat_ref)
            binding = coverage_bindings.get(key)
            if binding is None:
                raise ShotPlanningGateBlocked(
                    "SHOT_MISSING_REQUIRED_COVERAGE: expansion beat absent from CoverageStrategy"
                )
            if (
                binding.blocking_plan_ref != context.blocking_plan_ref
                or binding.cinematography_objective_ref != context.cinematography_objective_ref
            ):
                raise ShotPlanningGateBlocked("ShotExpansion context differs from CoverageStrategy authority")
            await self._assert_directing_chain(
                project_id=request.project_id,
                profile_ref=request.active_profile_ref,
                scene_ref=request.scene_ref,
                script_lock_ref=request.script_lock_ref,
                context=context,
            )
            trace = await self._assert_trace(
                project_id=request.project_id,
                beat_ref=context.scene_dramatic_beat_ref,
                trace_ref=context.narrative_trace_ref,
            )
            context_by_beat[key] = context
            trace_by_beat[key] = trace
        if set(context_by_beat) != set(coverage_bindings):
            raise ShotPlanningGateBlocked(
                "ShotExpansion must cover the exact beat set declared by CoverageStrategy"
            )

        if not budget.shot_count_range.contains(len(request.candidates)):
            raise ShotPlanningGateBlocked("BUDGET_SHOT_OVERFLOW: candidate count outside ShotBudget")
        total_seconds = sum(candidate.duration_seconds for candidate in request.candidates)
        if abs(total_seconds - budget.scene_duration_seconds) > budget.tolerance_seconds:
            raise ShotPlanningGateBlocked(
                "BUDGET_SHOT_OVERFLOW: candidate durations do not reconcile to Scene budget"
            )
        for candidate in request.candidates:
            if not budget.shot_duration_range_seconds.contains(candidate.duration_seconds):
                raise ShotPlanningGateBlocked("candidate duration lies outside ShotBudget range")

        requirement_by_key = {item.coverage_key: item for item in coverage.requirements}
        counts: dict[str, int] = {}
        semantic_signatures: set[tuple[str, str, str, str]] = set()
        blocking_by_beat: dict[tuple[str, str], BlockingPlan] = {}
        for context in request.beat_contexts:
            _, blocking, _ = await self._assert_directing_chain(
                project_id=request.project_id,
                profile_ref=request.active_profile_ref,
                scene_ref=request.scene_ref,
                script_lock_ref=request.script_lock_ref,
                context=context,
            )
            blocking_by_beat[_ref_key(context.scene_dramatic_beat_ref)] = blocking

        for candidate in request.candidates:
            requirement = requirement_by_key.get(candidate.coverage_key)
            if (
                requirement is None
                or requirement.scene_dramatic_beat_ref != candidate.scene_dramatic_beat_ref
                or requirement.coverage_function != candidate.coverage_function
            ):
                raise ShotPlanningGateBlocked(
                    "SHOT_MISSING_REQUIRED_COVERAGE: candidate coverage role is undeclared/mismatched"
                )
            counts[candidate.coverage_key] = counts.get(candidate.coverage_key, 0) + 1
            signature = (
                candidate.scene_dramatic_beat_ref.logical_id.root,
                candidate.coverage_key,
                candidate.dramatic_function.casefold(),
                candidate.basic_shot_intent.casefold(),
            )
            if signature in semantic_signatures:
                raise ShotPlanningGateBlocked(
                    "duplicate shot without non-redundant dramatic/coverage purpose"
                )
            semantic_signatures.add(signature)
            blocking = blocking_by_beat[_ref_key(candidate.scene_dramatic_beat_ref)]
            allowed_entities = {
                _ref_key(item.entity_ref)
                for item in (*blocking.positions, *blocking.movements)
            }
            if any(_ref_key(ref) not in allowed_entities for ref in candidate.subject_refs):
                raise ShotPlanningGateBlocked(
                    "ShotExpansion candidate subject is not declared by exact BlockingPlan"
                )
        for key, requirement in requirement_by_key.items():
            count = counts.get(key, 0)
            if not requirement.minimum_shots <= count <= requirement.maximum_shots:
                raise ShotPlanningGateBlocked(
                    "SHOT_MISSING_REQUIRED_COVERAGE: candidate coverage count outside requirement"
                )
        if set(counts) != set(requirement_by_key):
            raise ShotPlanningGateBlocked("ShotExpansion candidate uses undeclared coverage role")

        # DurationBudget is re-read above for exact-current validity. Keep the variable
        # deliberately referenced so a future implementation cannot silently remove it.
        if duration.ref != request.duration_budget_ref:
            raise ShotPlanningGateBlocked("DurationBudget exact ref mismatch")
        return {
            "coverage": coverage,
            "budget": budget,
            "contexts": context_by_beat,
            "traces": trace_by_beat,
        }
