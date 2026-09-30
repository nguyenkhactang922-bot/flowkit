"""Canonical structure-planning contracts for IMP-024.

This module owns planning policy/projections only:

- StructureProfile: count/runtime ranges derived under one pinned
  ActiveProductionProfile.
- DurationBudget: hierarchical runtime allocation with explicit tolerance.
- MacroBeatSheet: ordered references to canonical MacroStoryBeat versions.

It intentionally owns no StoryCore or MacroStoryBeat narrative truth.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from .active_profile import ActiveProductionProfile, profile_path_edge_type
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
from .story_core import StoryCorePhase, StoryCoreVersion, story_core_logical_id
from .topic_domain import (
    ClassificationAxis,
    DomainResolution,
    ProjectBootstrapInput,
)
from .versioning import CurrentPointerNotFound, CurrentVersionPointer, VersionRepository


class StructurePlanningError(ValueError):
    """Base error for IMP-024 structure-planning boundaries."""


class StructurePlanningGateBlocked(StructurePlanningError):
    """Raised when exact-version or planning gates fail closed."""


class StructurePlanningIdentityError(StructurePlanningError):
    """Raised when planning identity/provenance crosses canonical ownership."""


class BudgetLevel(str, Enum):
    MACRO_STORY_BEAT = "MACRO_STORY_BEAT"
    SEQUENCE = "SEQUENCE"
    SCENE = "SCENE"
    SCENE_DRAMATIC_BEAT = "SCENE_DRAMATIC_BEAT"
    SHOT = "SHOT"


class PlanningGateCheck(str, Enum):
    REFERENCE_INTEGRITY = "REFERENCE_INTEGRITY"
    ORDER_COVERAGE = "ORDER_COVERAGE"
    BUDGET_RECONCILIATION = "BUDGET_RECONCILIATION"


_LEVEL_ORDER = {
    BudgetLevel.MACRO_STORY_BEAT: 0,
    BudgetLevel.SEQUENCE: 1,
    BudgetLevel.SCENE: 2,
    BudgetLevel.SCENE_DRAMATIC_BEAT: 3,
    BudgetLevel.SHOT: 4,
}

_LEVEL_PREFIX = {
    BudgetLevel.MACRO_STORY_BEAT: "macro-story-beat:",
    BudgetLevel.SEQUENCE: "sequence:",
    BudgetLevel.SCENE: "scene:",
    BudgetLevel.SCENE_DRAMATIC_BEAT: "scene-dramatic-beat:",
    BudgetLevel.SHOT: "shot:",
}


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return (ref.logical_id.root, ref.version_id.root)


def structure_profile_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"structure-profile:{project_id.root}")


def duration_budget_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"duration-budget:{project_id.root}")


def macro_beat_sheet_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"macro-beat-sheet:{project_id.root}")


def _active_profile_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"active-profile:{project_id.root}")


def _project_input_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"project-input:{project_id.root}")


def _domain_resolution_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"niche-resolution:{project_id.root}")


def _require_same_project_ref(
    ref: VersionRef,
    expected: LogicalId,
    label: str,
) -> None:
    if ref.logical_id != expected:
        raise ValueError(
            f"{label} must reference canonical object for the same project"
        )


class CountRange(BaseModel):
    """Profile-driven count range; deliberately has no universal exact target."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    minimum: int = Field(ge=1)
    maximum: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_range(self) -> "CountRange":
        if self.maximum < self.minimum:
            raise ValueError("count range maximum must be >= minimum")
        return self

    def contains(self, value: int) -> bool:
        return self.minimum <= value <= self.maximum


class RuntimeRangeSeconds(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    minimum: int = Field(ge=1)
    maximum: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_range(self) -> "RuntimeRangeSeconds":
        if self.maximum < self.minimum:
            raise ValueError("runtime range maximum must be >= minimum")
        return self

    def contains(self, value: int) -> bool:
        return self.minimum <= value <= self.maximum


class StructureProfile(BaseModel):
    """Immutable planning policy. It never owns narrative facts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    project_ref: VersionRef
    domain_ref: VersionRef
    format_name: str
    genre_niche_label: str
    target_runtime_seconds: int = Field(ge=1)
    macro_story_beat_count: CountRange
    sequence_count: CountRange
    scene_count: CountRange
    scene_dramatic_beat_count: CountRange
    runtime_range_seconds: RuntimeRangeSeconds
    budget_tolerance_seconds: int = Field(ge=0)

    @field_validator("format_name", "genre_niche_label")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_authority(self) -> "StructureProfile":
        _require_same_project_ref(
            self.active_profile_ref,
            _active_profile_logical_id(self.project_id),
            "active_profile_ref",
        )
        _require_same_project_ref(
            self.project_ref,
            _project_input_logical_id(self.project_id),
            "project_ref",
        )
        _require_same_project_ref(
            self.domain_ref,
            _domain_resolution_logical_id(self.project_id),
            "domain_ref",
        )
        if not self.runtime_range_seconds.contains(self.target_runtime_seconds):
            raise ValueError(
                "target_runtime_seconds must stay inside profile runtime range"
            )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return structure_profile_logical_id(self.project_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return (
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
            SourceVersionBinding(role="project_input", source=self.project_ref),
            SourceVersionBinding(role="domain_resolution", source=self.domain_ref),
        )


class BudgetAllocation(BaseModel):
    """One planning allocation; allocation_id is local planning identity only."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    allocation_id: str
    level: BudgetLevel
    seconds: int = Field(gt=0)
    parent_allocation_id: str | None = None
    target_ref: VersionRef | None = None

    @field_validator("allocation_id")
    @classmethod
    def validate_allocation_id(cls, value: str) -> str:
        return _trimmed(value, "allocation_id")

    @field_validator("parent_allocation_id")
    @classmethod
    def validate_parent_id(cls, value: str | None) -> str | None:
        return None if value is None else _trimmed(value, "parent_allocation_id")

    @model_validator(mode="after")
    def validate_target(self) -> "BudgetAllocation":
        if self.parent_allocation_id == self.allocation_id:
            raise ValueError("budget allocation cannot parent itself")
        if self.target_ref is not None:
            prefix = _LEVEL_PREFIX[self.level]
            if not self.target_ref.logical_id.root.startswith(prefix):
                raise ValueError(
                    f"{self.level.value} allocation target must use {prefix} identity"
                )
        return self


class DurationBudget(BaseModel):
    """Hierarchical runtime allocation contract; never narrative truth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    structure_profile_ref: VersionRef
    total_seconds: int = Field(gt=0)
    tolerance_seconds: int = Field(ge=0)
    allocations: tuple[BudgetAllocation, ...] = Field(min_length=1)
    reconciliation_verdict: GateVerdict = GateVerdict.PASS

    @model_validator(mode="after")
    def validate_budget(self) -> "DurationBudget":
        _require_same_project_ref(
            self.active_profile_ref,
            _active_profile_logical_id(self.project_id),
            "active_profile_ref",
        )
        _require_same_project_ref(
            self.structure_profile_ref,
            structure_profile_logical_id(self.project_id),
            "structure_profile_ref",
        )
        if self.reconciliation_verdict is not GateVerdict.PASS:
            raise ValueError("persisted DurationBudget must pass reconciliation")

        for item in self.allocations:
            if item.target_ref is not None:
                expected_prefix = f"{_LEVEL_PREFIX[item.level]}{self.project_id.root}"
                if not item.target_ref.logical_id.root.startswith(expected_prefix):
                    raise ValueError(
                        "budget allocation target must belong to the same project"
                    )

        by_id = {item.allocation_id: item for item in self.allocations}
        if len(by_id) != len(self.allocations):
            raise ValueError("budget allocation_id values must be unique")

        target_keys = [
            _ref_key(item.target_ref)
            for item in self.allocations
            if item.target_ref is not None
        ]
        if len(target_keys) != len(set(target_keys)):
            raise ValueError("budget allocation target refs must be unique")

        top = [item for item in self.allocations if item.parent_allocation_id is None]
        if not top:
            raise ValueError("DurationBudget requires top-level macro allocations")
        if any(item.level is not BudgetLevel.MACRO_STORY_BEAT for item in top):
            raise ValueError(
                "top-level DurationBudget allocations must be MACRO_STORY_BEAT"
            )

        children: dict[str, list[BudgetAllocation]] = {
            item.allocation_id: [] for item in self.allocations
        }
        for item in self.allocations:
            if item.parent_allocation_id is None:
                continue
            parent = by_id.get(item.parent_allocation_id)
            if parent is None:
                raise ValueError(
                    f"budget allocation parent not found: {item.parent_allocation_id}"
                )
            if _LEVEL_ORDER[item.level] != _LEVEL_ORDER[parent.level] + 1:
                raise ValueError(
                    "budget child level must be exactly one canonical level below parent"
                )
            children[parent.allocation_id].append(item)

        top_sum = sum(item.seconds for item in top)
        if abs(top_sum - self.total_seconds) > self.tolerance_seconds:
            raise ValueError(
                "BUDGET_RUNTIME_OVERFLOW: top-level allocations do not reconcile "
                "to total_seconds within tolerance"
            )

        for parent in self.allocations:
            direct_children = children[parent.allocation_id]
            if not direct_children:
                continue
            child_sum = sum(item.seconds for item in direct_children)
            if abs(child_sum - parent.seconds) > self.tolerance_seconds:
                raise ValueError(
                    "BUDGET_RUNTIME_OVERFLOW: child allocations do not reconcile "
                    f"to parent {parent.allocation_id} within tolerance"
                )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return duration_budget_logical_id(self.project_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
            SourceVersionBinding(
                role="structure_profile",
                source=self.structure_profile_ref,
            ),
        ]
        for index, item in enumerate(self.allocations):
            if item.target_ref is not None:
                values.append(
                    SourceVersionBinding(
                        role=f"allocation_target_{index:03d}",
                        source=item.target_ref,
                    )
                )
        return tuple(values)

    def allocation_map(self) -> dict[str, BudgetAllocation]:
        return {item.allocation_id: item for item in self.allocations}

    def top_level_allocations(self) -> tuple[BudgetAllocation, ...]:
        return tuple(
            item for item in self.allocations if item.parent_allocation_id is None
        )


class MacroBeatSheetEntry(BaseModel):
    """Projection row: reference + order + budget binding, no beat narrative payload."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    order_index: int = Field(ge=0)
    macro_story_beat_ref: VersionRef
    duration_allocation_id: str

    @field_validator("duration_allocation_id")
    @classmethod
    def validate_allocation_id(cls, value: str) -> str:
        return _trimmed(value, "duration_allocation_id")

    @model_validator(mode="after")
    def validate_ref(self) -> "MacroBeatSheetEntry":
        if not self.macro_story_beat_ref.logical_id.root.startswith(
            "macro-story-beat:"
        ):
            raise ValueError(
                "MacroBeatSheet entries must reference canonical MacroStoryBeat IDs"
            )
        return self


class MacroBeatSheet(BaseModel):
    """Ordered structural projection; never duplicate MacroStoryBeat truth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    story_core_ref: VersionRef
    structure_profile_ref: VersionRef
    duration_budget_ref: VersionRef
    entries: tuple[MacroBeatSheetEntry, ...] = Field(min_length=1)
    projection_verdict: GateVerdict = GateVerdict.PASS
    gate_checks: tuple[PlanningGateCheck, ...] = (
        PlanningGateCheck.REFERENCE_INTEGRITY,
        PlanningGateCheck.ORDER_COVERAGE,
        PlanningGateCheck.BUDGET_RECONCILIATION,
    )

    @model_validator(mode="after")
    def validate_manifest(self) -> "MacroBeatSheet":
        _require_same_project_ref(
            self.active_profile_ref,
            _active_profile_logical_id(self.project_id),
            "active_profile_ref",
        )
        _require_same_project_ref(
            self.story_core_ref,
            story_core_logical_id(self.project_id),
            "story_core_ref",
        )
        _require_same_project_ref(
            self.structure_profile_ref,
            structure_profile_logical_id(self.project_id),
            "structure_profile_ref",
        )
        _require_same_project_ref(
            self.duration_budget_ref,
            duration_budget_logical_id(self.project_id),
            "duration_budget_ref",
        )
        if self.projection_verdict is not GateVerdict.PASS:
            raise ValueError("persisted MacroBeatSheet must pass projection gate")
        if self.gate_checks != tuple(PlanningGateCheck):
            raise ValueError(
                "MacroBeatSheet gate evidence must exactly include reference/order/budget checks"
            )

        indexes = [entry.order_index for entry in self.entries]
        if indexes != list(range(len(self.entries))):
            raise ValueError(
                "MacroBeatSheet order_index values must be contiguous from zero"
            )
        expected_macro_prefix = f"macro-story-beat:{self.project_id.root}"
        if any(
            not entry.macro_story_beat_ref.logical_id.root.startswith(
                expected_macro_prefix
            )
            for entry in self.entries
        ):
            raise ValueError(
                "MacroBeatSheet MacroStoryBeat refs must belong to the same project"
            )

        refs = [_ref_key(entry.macro_story_beat_ref) for entry in self.entries]
        if len(refs) != len(set(refs)):
            raise ValueError("MacroBeatSheet cannot duplicate MacroStoryBeat refs")
        allocation_ids = [entry.duration_allocation_id for entry in self.entries]
        if len(allocation_ids) != len(set(allocation_ids)):
            raise ValueError("MacroBeatSheet cannot duplicate duration allocations")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return macro_beat_sheet_logical_id(self.project_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
            SourceVersionBinding(role="locked_story_core", source=self.story_core_ref),
            SourceVersionBinding(
                role="structure_profile",
                source=self.structure_profile_ref,
            ),
            SourceVersionBinding(
                role="duration_budget",
                source=self.duration_budget_ref,
            ),
        ]
        values.extend(
            SourceVersionBinding(
                role=f"macro_story_beat_{entry.order_index:03d}",
                source=entry.macro_story_beat_ref,
            )
            for entry in self.entries
        )
        return tuple(values)


StructurePlanningValue: TypeAlias = StructureProfile | DurationBudget | MacroBeatSheet


class StructurePlanningArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: StructurePlanningValue

    @model_validator(mode="after")
    def validate_identity(self) -> "StructurePlanningArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("planning artifact logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("planning artifact version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError(
                "planning artifact provenance must exactly bind declared sources"
            )
        if self.metadata.provenance.rule_version != self.value.active_profile_ref:
            raise ValueError(
                "planning provenance rule_version must pin ActiveProductionProfile"
            )
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


def build_structure_planning_provenance(
    value: StructurePlanningValue,
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


class StructurePlanningRepository:
    """Shared immutable repository/gates for IMP-024 planning artifacts."""

    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, self.graph)

    async def create_structure_profile(
        self,
        *,
        value: StructureProfile,
        provenance: Provenance,
        created_at: datetime,
    ) -> StructurePlanningArtifact:
        await self._assert_structure_profile_inputs(value)
        artifact = await self._create_initial(value, provenance, created_at)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )
        return artifact

    async def revise_structure_profile(
        self,
        *,
        value: StructureProfile,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[StructurePlanningArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise StructurePlanningIdentityError(
                "StructureProfile revision must preserve logical identity"
            )
        await self._assert_current(
            predecessor,
            "StructureProfile revision predecessor",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        await self._assert_structure_profile_inputs(value)
        artifact = await self._create_successor(
            value,
            predecessor,
            provenance,
            created_at,
        )
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )
        records = await self.invalidations.create_for_change(
            cause="StructureProfile planning policy revision",
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope="structure_planning_descendants",
            repair_or_recompute_requirement=(
                "Recompute dependency-reachable DurationBudget/MacroBeatSheet/"
                "downstream planning projections; do not rewrite locked narrative truth."
            ),
        )
        return artifact, tuple(records)

    async def create_duration_budget(
        self,
        *,
        value: DurationBudget,
        provenance: Provenance,
        created_at: datetime,
    ) -> StructurePlanningArtifact:
        await self._assert_duration_budget_inputs(value)
        artifact = await self._create_initial(value, provenance, created_at)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )
        return artifact

    async def revise_duration_budget(
        self,
        *,
        value: DurationBudget,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[StructurePlanningArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise StructurePlanningIdentityError(
                "DurationBudget revision must preserve logical identity"
            )
        await self._assert_current(
            predecessor,
            "DurationBudget revision predecessor",
            {LifecycleState.APPROVED},
        )
        await self._assert_duration_budget_inputs(value)
        artifact = await self._create_successor(
            value,
            predecessor,
            provenance,
            created_at,
        )
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )
        records = await self.invalidations.create_for_change(
            cause="DurationBudget allocation revision",
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope="duration_budget_descendants",
            repair_or_recompute_requirement=(
                "Recompute dependency-reachable structural manifests/plans under "
                "the new accepted budget; do not mutate narrative entities."
            ),
        )
        return artifact, tuple(records)

    async def create_macro_beat_sheet(
        self,
        *,
        value: MacroBeatSheet,
        provenance: Provenance,
        created_at: datetime,
    ) -> StructurePlanningArtifact:
        await self._assert_macro_beat_sheet_inputs(value)
        artifact = await self._create_initial(value, provenance, created_at)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )
        return artifact

    async def revise_macro_beat_sheet(
        self,
        *,
        value: MacroBeatSheet,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[StructurePlanningArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise StructurePlanningIdentityError(
                "MacroBeatSheet revision must preserve manifest identity"
            )
        await self._assert_current(
            predecessor,
            "MacroBeatSheet revision predecessor",
            {LifecycleState.APPROVED},
        )
        await self._assert_macro_beat_sheet_inputs(value)
        artifact = await self._create_successor(
            value,
            predecessor,
            provenance,
            created_at,
        )
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )
        records = await self.invalidations.create_for_change(
            cause="MacroBeatSheet projection revision",
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope="macro_beat_sheet_order_consumers",
            repair_or_recompute_requirement=(
                "Recompute order/budget-dependent descendants only; referenced "
                "MacroStoryBeat narrative truth is unchanged."
            ),
        )
        return artifact, tuple(records)

    async def get_structure_profile(
        self,
        ref: VersionRef,
    ) -> StructurePlanningArtifact | None:
        return await self._get_typed(ref, StructureProfile, "structure-profile:")

    async def get_duration_budget(
        self,
        ref: VersionRef,
    ) -> StructurePlanningArtifact | None:
        return await self._get_typed(ref, DurationBudget, "duration-budget:")

    async def get_macro_beat_sheet(
        self,
        ref: VersionRef,
    ) -> StructurePlanningArtifact | None:
        return await self._get_typed(ref, MacroBeatSheet, "macro-beat-sheet:")

    async def _create_initial(
        self,
        value: StructurePlanningValue,
        provenance: Provenance,
        created_at: datetime,
    ) -> StructurePlanningArtifact:
        self._assert_provenance(value, provenance)
        artifact = self._artifact(value, provenance, created_at, None)
        stored = await self.versions.create_initial(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        materialized = StructurePlanningArtifact(
            metadata=stored.metadata,
            value=value,
        )
        await self._register_dependencies(materialized)
        return materialized

    async def _create_successor(
        self,
        value: StructurePlanningValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> StructurePlanningArtifact:
        if predecessor.logical_id != value.logical_id:
            raise StructurePlanningIdentityError(
                "planning successor must preserve logical identity"
            )
        self._assert_provenance(value, provenance)
        artifact = self._artifact(value, provenance, created_at, predecessor)
        stored = await self.versions.create_successor(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        materialized = StructurePlanningArtifact(
            metadata=stored.metadata,
            value=value,
        )
        await self._register_dependencies(materialized)
        return materialized

    async def _get_typed(self, ref, model, prefix) -> StructurePlanningArtifact | None:
        if not ref.logical_id.root.startswith(prefix):
            raise StructurePlanningIdentityError(
                f"expected {prefix.rstrip(':')} artifact, got {ref.logical_id.root}"
            )
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = model.model_validate(stored.payload)
        return StructurePlanningArtifact(metadata=stored.metadata, value=value)

    async def _register_dependencies(
        self,
        artifact: StructurePlanningArtifact,
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
            source = refs[key]
            edge_type = (
                profile_path_edge_type("*")
                if source == artifact.value.active_profile_ref
                else "structure_planning_input"
            )
            await self.graph.create_edge(
                source=source,
                dependent=artifact.ref,
                edge_type=edge_type,
                dependency_reason=" + ".join(sorted(set(grouped[key]))),
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _assert_structure_profile_inputs(
        self,
        value: StructureProfile,
    ) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        profile = await self._load_active_profile(value.active_profile_ref)
        if profile.project_id != value.project_id:
            raise StructurePlanningGateBlocked(
                "ActiveProductionProfile belongs to a different project"
            )
        if profile.project_ref != value.project_ref:
            raise StructurePlanningGateBlocked(
                "StructureProfile project_ref must match pinned ActiveProductionProfile"
            )
        if profile.domain_ref != value.domain_ref:
            raise StructurePlanningGateBlocked(
                "StructureProfile domain_ref must match pinned ActiveProductionProfile"
            )

        project = await self._load_project_input(value.project_ref)
        domain = await self._load_domain_resolution(value.domain_ref)
        if project.project_id != value.project_id or domain.project_id != value.project_id:
            raise StructurePlanningGateBlocked(
                "StructureProfile project/domain inputs belong to a different project"
            )
        if (
            project.target_duration_seconds is not None
            and project.target_duration_seconds != value.target_runtime_seconds
        ):
            raise StructurePlanningGateBlocked(
                "StructureProfile target runtime must match canonical ProjectBootstrapInput"
            )

        format_labels = {
            item.label.casefold()
            for item in domain.axis(ClassificationAxis.FORMAT).labels
        }
        if value.format_name.casefold() not in format_labels:
            raise StructurePlanningGateBlocked(
                "StructureProfile format_name must come from canonical DomainResolution FORMAT axis"
            )

        genre_niche_labels = {
            item.label.casefold()
            for axis in (ClassificationAxis.GENRE, ClassificationAxis.NICHE)
            for item in domain.axis(axis).labels
        }
        if value.genre_niche_label.casefold() not in genre_niche_labels:
            raise StructurePlanningGateBlocked(
                "StructureProfile genre_niche_label must come from canonical "
                "DomainResolution GENRE/NICHE axes"
            )

    async def _assert_duration_budget_inputs(
        self,
        value: DurationBudget,
    ) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.structure_profile_ref,
            "StructureProfile",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        structure_artifact = await self.get_structure_profile(
            value.structure_profile_ref
        )
        if structure_artifact is None:
            raise StructurePlanningGateBlocked(
                "DurationBudget StructureProfile exact version not found"
            )
        structure = structure_artifact.value
        if structure.active_profile_ref != value.active_profile_ref:
            raise StructurePlanningGateBlocked(
                "DurationBudget must use same exact ActiveProductionProfile as StructureProfile"
            )
        if structure.target_runtime_seconds != value.total_seconds:
            raise StructurePlanningGateBlocked(
                "DurationBudget total_seconds must equal StructureProfile target runtime"
            )
        if structure.budget_tolerance_seconds != value.tolerance_seconds:
            raise StructurePlanningGateBlocked(
                "DurationBudget tolerance must equal StructureProfile tolerance policy"
            )

        level_ranges = {
            BudgetLevel.MACRO_STORY_BEAT: structure.macro_story_beat_count,
            BudgetLevel.SEQUENCE: structure.sequence_count,
            BudgetLevel.SCENE: structure.scene_count,
            BudgetLevel.SCENE_DRAMATIC_BEAT: structure.scene_dramatic_beat_count,
        }
        for level, count_range in level_ranges.items():
            count = sum(1 for item in value.allocations if item.level is level)
            if count and not count_range.contains(count):
                raise StructurePlanningGateBlocked(
                    f"{level.value} allocation count falls outside StructureProfile range"
                )

        for allocation in value.allocations:
            if allocation.target_ref is not None:
                await self._assert_current(
                    allocation.target_ref,
                    "DurationBudget allocation target",
                    {
                        LifecycleState.DRAFT,
                        LifecycleState.REVIEW,
                        LifecycleState.APPROVED,
                        LifecycleState.LOCKED,
                    },
                )

    async def _assert_macro_beat_sheet_inputs(
        self,
        value: MacroBeatSheet,
    ) -> None:
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
            value.structure_profile_ref,
            "StructureProfile",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.duration_budget_ref,
            "DurationBudget",
            {LifecycleState.APPROVED},
        )

        story_stored = await self.versions.get_version(value.story_core_ref)
        if story_stored is None:
            raise StructurePlanningGateBlocked("locked StoryCore not found")
        try:
            story_core = StoryCoreVersion.model_validate(story_stored.payload)
        except ValidationError as exc:
            raise StructurePlanningGateBlocked(
                "story_core_ref payload is not canonical StoryCoreVersion"
            ) from exc
        if story_core.phase is not StoryCorePhase.FROZEN_FOR_STRUCTURE:
            raise StructurePlanningGateBlocked(
                "MacroBeatSheet requires FROZEN_FOR_STRUCTURE StoryCore"
            )

        structure_artifact = await self.get_structure_profile(
            value.structure_profile_ref
        )
        budget_artifact = await self.get_duration_budget(
            value.duration_budget_ref
        )
        if structure_artifact is None or budget_artifact is None:
            raise StructurePlanningGateBlocked(
                "MacroBeatSheet planning inputs not found"
            )
        structure = structure_artifact.value
        budget = budget_artifact.value
        if (
            structure.active_profile_ref != value.active_profile_ref
            or budget.active_profile_ref != value.active_profile_ref
        ):
            raise StructurePlanningGateBlocked(
                "MacroBeatSheet planning inputs must share exact ActiveProductionProfile"
            )
        if budget.structure_profile_ref != structure.ref:
            raise StructurePlanningGateBlocked(
                "MacroBeatSheet DurationBudget must bind exact StructureProfile"
            )
        if not structure.macro_story_beat_count.contains(len(value.entries)):
            raise StructurePlanningGateBlocked(
                "MacroBeatSheet entry count falls outside StructureProfile range"
            )

        allocation_map = budget.allocation_map()
        top_ids = {
            item.allocation_id for item in budget.top_level_allocations()
        }
        entry_ids = {entry.duration_allocation_id for entry in value.entries}
        if entry_ids != top_ids:
            raise StructurePlanningGateBlocked(
                "MacroBeatSheet must cover each top-level macro duration allocation exactly once"
            )

        for entry in value.entries:
            allocation = allocation_map[entry.duration_allocation_id]
            if allocation.level is not BudgetLevel.MACRO_STORY_BEAT:
                raise StructurePlanningGateBlocked(
                    "MacroBeatSheet entry must bind MACRO_STORY_BEAT allocation"
                )
            if (
                allocation.target_ref is not None
                and allocation.target_ref != entry.macro_story_beat_ref
            ):
                raise StructurePlanningGateBlocked(
                    "MacroBeatSheet beat ref conflicts with DurationBudget allocation target"
                )
            await self._assert_current(
                entry.macro_story_beat_ref,
                "MacroStoryBeat projection ref",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )

    async def _load_project_input(
        self,
        ref: VersionRef,
    ) -> ProjectBootstrapInput:
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise StructurePlanningGateBlocked(
                "ProjectBootstrapInput exact version not found"
            )
        try:
            return ProjectBootstrapInput.model_validate(stored.payload)
        except ValidationError as exc:
            raise StructurePlanningGateBlocked(
                "project_ref payload is not canonical ProjectBootstrapInput"
            ) from exc

    async def _load_domain_resolution(
        self,
        ref: VersionRef,
    ) -> DomainResolution:
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise StructurePlanningGateBlocked(
                "DomainResolution exact version not found"
            )
        try:
            return DomainResolution.model_validate(stored.payload)
        except ValidationError as exc:
            raise StructurePlanningGateBlocked(
                "domain_ref payload is not canonical DomainResolution"
            ) from exc

    async def _load_active_profile(
        self,
        ref: VersionRef,
    ) -> ActiveProductionProfile:
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise StructurePlanningGateBlocked(
                "ActiveProductionProfile exact version not found"
            )
        try:
            return ActiveProductionProfile.model_validate(stored.payload)
        except ValidationError as exc:
            raise StructurePlanningGateBlocked(
                "active_profile_ref payload is not canonical ActiveProductionProfile"
            ) from exc

    async def _assert_all_sources_exist(
        self,
        value: StructurePlanningValue,
    ) -> None:
        for binding in value.source_bindings():
            if await self.versions.get_version(binding.source) is None:
                raise StructurePlanningGateBlocked(
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
            raise StructurePlanningGateBlocked(
                f"{label} has no current version"
            ) from exc
        if pointer.version_id != ref.version_id or pointer.status not in allowed:
            raise StructurePlanningGateBlocked(
                f"{label} is not exact current accepted version"
            )
        return pointer

    @staticmethod
    def _assert_provenance(
        value: StructurePlanningValue,
        provenance: Provenance,
    ) -> None:
        if provenance.source_versions != value.source_bindings():
            raise StructurePlanningIdentityError(
                "planning provenance must exactly match declared source bindings"
            )
        if provenance.rule_version != value.active_profile_ref:
            raise StructurePlanningIdentityError(
                "planning provenance rule_version must pin ActiveProductionProfile"
            )

    @staticmethod
    def _artifact(
        value: StructurePlanningValue,
        provenance: Provenance,
        created_at: datetime,
        predecessor: VersionRef | None,
    ) -> StructurePlanningArtifact:
        return StructurePlanningArtifact(
            metadata=SemanticRecordMetadata(
                logical_id=value.logical_id,
                version_id=value.version_id,
                predecessor=predecessor,
                provenance=provenance,
                created_at=created_at,
            ),
            value=value,
        )
