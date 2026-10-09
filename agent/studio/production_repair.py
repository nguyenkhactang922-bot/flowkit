"""Provider-neutral defect localization and targeted production repair for IMP-063.

Authority boundaries:
- QA results remain evidence owners; DefectLocalization diagnoses an exact QA
  finding and never rewrites the evaluated artifact/spec/state.
- Root cause is evidence-backed by exact dependency ancestry, not a defect-code
  dictionary lookup.
- RepairPlan describes preserve/patch/invalidate/recheck scope only; it does not
  perform provider side effects or canonical State commits.
- Every repair plan requires fresh QA for the originating QA family.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .invalidation import (
    DependencyGraphRepository,
    InvalidationRecord,
    InvalidationRepository,
)
from .primitives import (
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    VersionId,
    VersionRef,
)
from .versioning import VersionRepository


class ProductionRepairError(ValueError):
    """Base IMP-063 defect-localization/repair error."""


class ProductionRepairGateBlocked(ProductionRepairError):
    """Raised when exact-version, lineage, preserve, or re-QA gates fail closed."""


class ProductionRepairIdentityError(ProductionRepairError):
    """Raised when persisted production-repair identity/provenance conflicts."""


class QASourceKind(str, Enum):
    STATIC = "STATIC"
    MOTION = "MOTION"
    CONTINUITY = "CONTINUITY"
    SEQUENCE = "SEQUENCE"


class ProductionResponsibleLayer(str, Enum):
    """Canonical layer classes that may own a diagnosed production defect."""

    UPSTREAM_STORY = "UPSTREAM_STORY"
    REFERENCE_ASSET = "REFERENCE_ASSET"
    STATE = "STATE"
    SHOT_PLANNING = "SHOT_PLANNING"
    FULL_SHOT_SPEC = "FULL_SHOT_SPEC"
    STATIC_KEYFRAME_SPEC = "STATIC_KEYFRAME_SPEC"
    MOTION_DELTA_SPEC = "MOTION_DELTA_SPEC"
    SHOT_IR = "SHOT_IR"


class ProductionRepairMode(str, Enum):
    PATCH_IN_PLACE = "PATCH_IN_PLACE"
    REGENERATE_FROM_ANCHOR = "REGENERATE_FROM_ANCHOR"
    REPLAN_SHOT = "REPLAN_SHOT"
    ESCALATE_UPSTREAM = "ESCALATE_UPSTREAM"


_QA_PREFIXES = {
    QASourceKind.STATIC: "qa-result:",
    QASourceKind.MOTION: "motion-qa-result:",
    QASourceKind.CONTINUITY: "continuity-qa-result:",
    QASourceKind.SEQUENCE: "sequence-qa-result:",
}

_LAYER_PREFIXES = {
    ProductionResponsibleLayer.UPSTREAM_STORY: (
        "story-idea:",
        "story-logline:",
        "story-premise:",
        "story-angle:",
        "story-theme:",
        "story-core:",
        "story-graph:",
        "macro-story-beat:",
        "sequence-plan:",
        "sequence:",
        "scene:",
        "scene-dramatic-beat:",
        "dialogue-intent:",
        "setup-payoff-link:",
        "screenplay-scene:",
        "screenplay:",
        "script-lock:",
    ),
    ProductionResponsibleLayer.REFERENCE_ASSET: ("reference-asset:",),
    ProductionResponsibleLayer.STATE: (
        "state-snapshot:",
        "approved-end-state:",
        "continuity-ledger:",
        "character-model:",
        "character-knowledge:",
        "relationship:",
    ),
    ProductionResponsibleLayer.SHOT_PLANNING: (
        "coverage-strategy:",
        "shot-budget:",
        "shot-list-item:",
        "shot-list-manifest:",
    ),
    ProductionResponsibleLayer.FULL_SHOT_SPEC: ("full-shot-spec:",),
    ProductionResponsibleLayer.STATIC_KEYFRAME_SPEC: ("static-keyframe-spec:",),
    ProductionResponsibleLayer.MOTION_DELTA_SPEC: ("motion-delta-spec:",),
    ProductionResponsibleLayer.SHOT_IR: ("shot-ir:",),
}

_SHOT_REPLAN_PREFIXES = (
    "coverage-strategy:",
    "shot-budget:",
    "shot-list-item:",
    "shot-list-manifest:",
    "full-shot-spec:",
)

_ALLOWED_CURRENT = {
    LifecycleState.DRAFT,
    LifecycleState.REVIEW,
    LifecycleState.APPROVED,
    LifecycleState.LOCKED,
}


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _key(value: str, label: str) -> str:
    value = _trimmed(value, label)
    if ":" in value:
        raise ValueError(f"{label} must not contain ':'")
    return value


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return ref.logical_id.root, ref.version_id.root


def _unique_refs(values: tuple[VersionRef, ...], label: str) -> tuple[VersionRef, ...]:
    keys = [_ref_key(ref) for ref in values]
    if len(keys) != len(set(keys)):
        raise ValueError(f"{label} must be unique")
    return values


def _project_scoped(ref: VersionRef, prefix: str, project_id: LogicalId) -> bool:
    root = ref.logical_id.root
    base = f"{prefix}{project_id.root}"
    return root == base or root.startswith(base + ":")


def _layer_matches(
    ref: VersionRef,
    layer: ProductionResponsibleLayer,
    project_id: LogicalId,
) -> bool:
    for prefix in _LAYER_PREFIXES[layer]:
        if _project_scoped(ref, prefix, project_id):
            return True
    return False


def defect_localization_logical_id(project_id: LogicalId, localization_key: str) -> LogicalId:
    return LogicalId(
        f"defect-localization:{project_id.root}:{_key(localization_key, 'localization_key')}"
    )


def production_repair_plan_logical_id(project_id: LogicalId, repair_key: str) -> LogicalId:
    return LogicalId(
        f"production-repair-plan:{project_id.root}:{_key(repair_key, 'repair_key')}"
    )


class _PersistedQAFinding(BaseModel):
    """Common persisted QA-finding projection shared by IMP-060/061/062."""

    model_config = ConfigDict(extra="ignore")

    dimension: str
    verdict: str
    severity: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason_code: str
    explanation: str
    evidence_refs: tuple[str, ...]
    source_refs: tuple[VersionRef, ...] = ()


class _PersistedQAResult(BaseModel):
    """Common exact-version QA envelope used only for localization validation."""

    model_config = ConfigDict(extra="ignore")

    evaluator_version: str
    policy_version: str
    execution_status: str
    verdict: str | None = None
    findings: tuple[_PersistedQAFinding, ...] = ()


class RepairRecheckRequirement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    qa_kind: QASourceKind
    scope_refs: tuple[VersionRef, ...] = Field(min_length=1)
    reason: str

    @field_validator("scope_refs")
    @classmethod
    def validate_scope_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        return _unique_refs(values, "recheck scope_refs")

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        return _trimmed(value, "recheck reason")


class DefectLocalization(BaseModel):
    """Evidence-bound diagnosis from one exact QA finding to one responsible layer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    localization_key: str
    version_id: VersionId
    qa_kind: QASourceKind
    qa_result_ref: VersionRef
    finding_dimension: str
    defect_code: str
    registry_version: str
    detector_version: str
    responsible_ref: VersionRef
    responsible_layer: ProductionResponsibleLayer
    preserve_refs: tuple[VersionRef, ...] = ()
    invalidation_candidate_refs: tuple[VersionRef, ...] = ()
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str

    @field_validator(
        "localization_key",
        "finding_dimension",
        "defect_code",
        "registry_version",
        "detector_version",
        "explanation",
    )
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        if info.field_name == "localization_key":
            return _key(value, info.field_name)
        return _trimmed(value, info.field_name)

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(_trimmed(value, "evidence_refs") for value in values)
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("evidence_refs must be unique")
        return cleaned

    @field_validator("preserve_refs", "invalidation_candidate_refs")
    @classmethod
    def validate_ref_sets(cls, values: tuple[VersionRef, ...], info) -> tuple[VersionRef, ...]:
        return _unique_refs(values, info.field_name)

    @model_validator(mode="after")
    def validate_localization(self) -> "DefectLocalization":
        prefix = _QA_PREFIXES[self.qa_kind]
        if not self.qa_result_ref.logical_id.root.startswith(prefix):
            raise ValueError(f"qa_result_ref must match {self.qa_kind.value} QA identity")
        if not _layer_matches(self.responsible_ref, self.responsible_layer, self.project_id):
            raise ValueError("responsible_layer does not match responsible_ref canonical identity")
        preserve = {_ref_key(ref) for ref in self.preserve_refs}
        invalidate = {_ref_key(ref) for ref in self.invalidation_candidate_refs}
        responsible = _ref_key(self.responsible_ref)
        if preserve & invalidate:
            raise ValueError("preserve_refs cannot overlap invalidation_candidate_refs")
        if responsible in preserve:
            raise ValueError("responsible_ref cannot be preserved by the same localization")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return defect_localization_logical_id(self.project_id, self.localization_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="qa_result", source=self.qa_result_ref),
            SourceVersionBinding(role="responsible_source", source=self.responsible_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"preserve_{index:03d}", source=ref)
            for index, ref in enumerate(self.preserve_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"invalidation_candidate_{index:03d}", source=ref)
            for index, ref in enumerate(self.invalidation_candidate_refs)
        )
        return tuple(values)


class RepairPlan(BaseModel):
    """Typed minimum-scope production repair plan; execution remains downstream."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    repair_key: str
    version_id: VersionId
    localization_ref: VersionRef
    mode: ProductionRepairMode
    patch_refs: tuple[VersionRef, ...] = Field(min_length=1)
    preserve_refs: tuple[VersionRef, ...] = ()
    invalidate_refs: tuple[VersionRef, ...] = ()
    recheck: tuple[RepairRecheckRequirement, ...] = Field(min_length=1)
    planner_version: str
    expected_resolution: str
    cost_constraint: str | None = None
    provider_constraint: str | None = None
    prior_repair_plan_ref: VersionRef | None = None
    escalation_reason: str | None = None

    @field_validator("repair_key", "planner_version", "expected_resolution")
    @classmethod
    def validate_required_text(cls, value: str, info) -> str:
        if info.field_name == "repair_key":
            return _key(value, info.field_name)
        return _trimmed(value, info.field_name)

    @field_validator("cost_constraint", "provider_constraint", "escalation_reason")
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return None if value is None else _trimmed(value, info.field_name)

    @field_validator("patch_refs", "preserve_refs", "invalidate_refs")
    @classmethod
    def validate_ref_sets(cls, values: tuple[VersionRef, ...], info) -> tuple[VersionRef, ...]:
        return _unique_refs(values, info.field_name)

    @model_validator(mode="after")
    def validate_plan(self) -> "RepairPlan":
        if not self.localization_ref.logical_id.root.startswith(
            f"defect-localization:{self.project_id.root}:"
        ):
            raise ValueError("localization_ref must belong to project")
        patch = {_ref_key(ref) for ref in self.patch_refs}
        preserve = {_ref_key(ref) for ref in self.preserve_refs}
        invalidate = {_ref_key(ref) for ref in self.invalidate_refs}
        if patch & preserve:
            raise ValueError("patch_refs cannot overlap preserve_refs")
        if invalidate & preserve:
            raise ValueError("invalidate_refs cannot overlap preserve_refs")
        if patch & invalidate:
            raise ValueError("patch_refs cannot overlap invalidate_refs")
        if self.mode is ProductionRepairMode.ESCALATE_UPSTREAM:
            if self.prior_repair_plan_ref is None or self.escalation_reason is None:
                raise ValueError("ESCALATE_UPSTREAM requires prior_repair_plan_ref and escalation_reason")
        elif self.escalation_reason is not None:
            raise ValueError("escalation_reason is only valid for ESCALATE_UPSTREAM")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return production_repair_plan_logical_id(self.project_id, self.repair_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [SourceVersionBinding(role="defect_localization", source=self.localization_ref)]
        values.extend(
            SourceVersionBinding(role=f"patch_{index:03d}", source=ref)
            for index, ref in enumerate(self.patch_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"preserve_{index:03d}", source=ref)
            for index, ref in enumerate(self.preserve_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"invalidate_{index:03d}", source=ref)
            for index, ref in enumerate(self.invalidate_refs)
        )
        for recheck_index, requirement in enumerate(self.recheck):
            values.extend(
                SourceVersionBinding(
                    role=f"recheck_{recheck_index:03d}_{scope_index:03d}",
                    source=ref,
                )
                for scope_index, ref in enumerate(requirement.scope_refs)
            )
        if self.prior_repair_plan_ref is not None:
            values.append(
                SourceVersionBinding(role="prior_repair_plan", source=self.prior_repair_plan_ref)
            )
        return tuple(values)


ProductionRepairValue: TypeAlias = DefectLocalization | RepairPlan


class ProductionRepairArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: ProductionRepairValue

    @model_validator(mode="after")
    def validate_artifact(self) -> "ProductionRepairArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("production-repair artifact logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("production-repair artifact version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError("production-repair provenance must exactly bind declared sources")
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


def _version_provenance_refs(value: ProductionRepairValue) -> tuple[str, ...]:
    if isinstance(value, DefectLocalization):
        return (
            f"defect-registry:{value.registry_version}",
            f"detector:{value.detector_version}",
        )
    return (f"repair-planner:{value.planner_version}",)


def build_production_repair_provenance(
    value: ProductionRepairValue,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    version_refs = _version_provenance_refs(value)
    merged_source_refs = tuple(dict.fromkeys((*source_refs, *version_refs)))
    return Provenance(
        source_versions=value.source_bindings(),
        source_refs=merged_source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        correlation_id=correlation_id,
    )


class ProductionRepairRepository:
    """Immutable IMP-063 evidence/plan repository with graph-validated repair gates."""

    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, self.graph)

    async def create_localization(
        self,
        *,
        value: DefectLocalization,
        provenance: Provenance,
        created_at: datetime,
    ) -> ProductionRepairArtifact:
        await self._assert_localization_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_localization(
        self,
        *,
        value: DefectLocalization,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ProductionRepairArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_localization_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            cause="DefectLocalization revision",
            scope="defect_localization_dependents",
        )

    async def create_repair_plan(
        self,
        *,
        value: RepairPlan,
        provenance: Provenance,
        created_at: datetime,
    ) -> ProductionRepairArtifact:
        await self._assert_repair_plan_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_repair_plan(
        self,
        *,
        value: RepairPlan,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ProductionRepairArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_repair_plan_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            cause="Production RepairPlan revision",
            scope="production_repair_plan_dependents",
        )

    async def get_localization(self, ref: VersionRef) -> ProductionRepairArtifact | None:
        return await self._get_typed(ref, DefectLocalization, "defect-localization:")

    async def get_repair_plan(self, ref: VersionRef) -> ProductionRepairArtifact | None:
        return await self._get_typed(ref, RepairPlan, "production-repair-plan:")

    async def trace_ancestors(self, ref: VersionRef):
        return tuple(await self.graph.ancestors(ref))

    async def trace_descendants(self, ref: VersionRef):
        return tuple(await self.graph.descendants(ref))

    async def _create_approved(
        self,
        value: ProductionRepairValue,
        provenance: Provenance,
        created_at: datetime,
    ) -> ProductionRepairArtifact:
        artifact = await self._create_initial(value, provenance, created_at)
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
        value: ProductionRepairValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
        cause: str,
        scope: str,
    ) -> tuple[ProductionRepairArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise ProductionRepairIdentityError("production-repair revision must preserve logical identity")
        await self._assert_current(predecessor, "production-repair predecessor", {LifecycleState.APPROVED})
        artifact = await self._create_successor(value, predecessor, provenance, created_at)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )
        records = await self.invalidations.create_for_change(
            cause=cause,
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope=scope,
            repair_or_recompute_requirement=(
                "Recompute only dependency-reachable repair/QA descendants and re-run declared QA gates."
            ),
        )
        return artifact, tuple(records)

    async def _create_initial(
        self,
        value: ProductionRepairValue,
        provenance: Provenance,
        created_at: datetime,
    ) -> ProductionRepairArtifact:
        self._assert_provenance(value, provenance)
        artifact = self._artifact(value, provenance, created_at, None)
        stored = await self.versions.create_initial(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        materialized = ProductionRepairArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(materialized)
        return materialized

    async def _create_successor(
        self,
        value: ProductionRepairValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> ProductionRepairArtifact:
        self._assert_provenance(value, provenance)
        artifact = self._artifact(value, provenance, created_at, predecessor)
        stored = await self.versions.create_successor(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        materialized = ProductionRepairArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(materialized)
        return materialized

    async def _get_typed(self, ref: VersionRef, model, prefix: str) -> ProductionRepairArtifact | None:
        if not ref.logical_id.root.startswith(prefix):
            raise ProductionRepairIdentityError(f"expected {prefix.rstrip(':')} artifact")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = model.model_validate(stored.payload)
        return ProductionRepairArtifact(metadata=stored.metadata, value=value)

    async def _register_dependencies(self, artifact: ProductionRepairArtifact) -> None:
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
                edge_type="production_repair_input",
                dependency_reason=" + ".join(sorted(set(grouped[key]))),
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _assert_localization_inputs(self, value: DefectLocalization) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(value.qa_result_ref, "QA result", {LifecycleState.REVIEW, LifecycleState.APPROVED, LifecycleState.LOCKED})
        stored = await self.versions.get_version(value.qa_result_ref)
        if stored is None:
            raise ProductionRepairGateBlocked("QA result exact version not found")
        qa = _PersistedQAResult.model_validate(stored.payload)
        if qa.execution_status != "COMPLETED":
            raise ProductionRepairGateBlocked("defect localization requires completed QA evidence")
        if value.detector_version != qa.evaluator_version:
            raise ProductionRepairGateBlocked("detector_version must match exact QA evaluator_version")
        matches = [
            finding
            for finding in qa.findings
            if finding.dimension == value.finding_dimension and finding.reason_code == value.defect_code
        ]
        if len(matches) != 1:
            raise ProductionRepairGateBlocked("defect code/dimension must identify exactly one persisted QA finding")
        finding = matches[0]
        if finding.verdict != "FAIL":
            raise ProductionRepairGateBlocked("repair localization requires a FAIL finding")
        if not set(finding.evidence_refs).issubset(set(value.evidence_refs)):
            raise ProductionRepairGateBlocked("localization evidence must preserve all QA finding evidence refs")

        responsible_key = _ref_key(value.responsible_ref)
        if finding.source_refs:
            evidence_backed = False
            for source_ref in finding.source_refs:
                source_ancestors = {
                    _ref_key(item.ref) for item in await self.graph.ancestors(source_ref)
                }
                if responsible_key == _ref_key(source_ref) or responsible_key in source_ancestors:
                    evidence_backed = True
                    break
            if not evidence_backed:
                raise ProductionRepairGateBlocked(
                    "responsible_ref must be a cited finding source or exact ancestor of one"
                )

        await self._assert_current(value.responsible_ref, "responsible source", _ALLOWED_CURRENT)
        ancestors = {_ref_key(item.ref) for item in await self.graph.ancestors(value.qa_result_ref)}
        if responsible_key not in ancestors:
            raise ProductionRepairGateBlocked(
                "responsible_ref must be an exact dependency ancestor of the manifested QA result"
            )
        for ref in value.preserve_refs:
            await self._assert_current(ref, "preserve obligation", _ALLOWED_CURRENT)
            if _ref_key(ref) not in ancestors:
                raise ProductionRepairGateBlocked("preserve ref must belong to the evaluated QA ancestry")

        descendants = {_ref_key(item.ref) for item in await self.graph.descendants(value.responsible_ref)}
        for ref in value.invalidation_candidate_refs:
            await self._assert_current(ref, "invalidation candidate", _ALLOWED_CURRENT)
            if _ref_key(ref) not in descendants:
                raise ProductionRepairGateBlocked(
                    "invalidation candidate must be an exact dependency descendant of responsible_ref"
                )

    async def _assert_repair_plan_inputs(self, value: RepairPlan) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(value.localization_ref, "DefectLocalization", {LifecycleState.APPROVED})
        localization_artifact = await self.get_localization(value.localization_ref)
        if localization_artifact is None:
            raise ProductionRepairGateBlocked("DefectLocalization exact version not found")
        localization = localization_artifact.value
        assert isinstance(localization, DefectLocalization)
        if localization.project_id != value.project_id:
            raise ProductionRepairGateBlocked("RepairPlan project/localization mismatch")
        if {_ref_key(ref) for ref in value.preserve_refs} != {
            _ref_key(ref) for ref in localization.preserve_refs
        }:
            raise ProductionRepairGateBlocked("RepairPlan must preserve the exact diagnosed preserve set")

        responsible = localization.responsible_ref
        responsible_key = _ref_key(responsible)
        descendants = {_ref_key(item.ref) for item in await self.graph.descendants(responsible)}
        ancestors = {_ref_key(item.ref) for item in await self.graph.ancestors(responsible)}

        for ref in value.patch_refs:
            await self._assert_current(ref, "repair patch target", _ALLOWED_CURRENT)
            key = _ref_key(ref)
            if value.mode is ProductionRepairMode.PATCH_IN_PLACE:
                if key != responsible_key:
                    raise ProductionRepairGateBlocked("PATCH_IN_PLACE must patch the diagnosed responsible_ref")
            elif value.mode is ProductionRepairMode.REGENERATE_FROM_ANCHOR:
                if key not in descendants:
                    raise ProductionRepairGateBlocked("REGENERATE_FROM_ANCHOR patch target must be downstream of responsible_ref")
            elif value.mode is ProductionRepairMode.REPLAN_SHOT:
                if not ref.logical_id.root.startswith(_SHOT_REPLAN_PREFIXES):
                    raise ProductionRepairGateBlocked("REPLAN_SHOT may patch only canonical shot-planning/spec scope")
                if key != responsible_key and key not in ancestors and key not in descendants:
                    raise ProductionRepairGateBlocked("REPLAN_SHOT target must stay on the diagnosed dependency path")
            else:
                if key not in ancestors:
                    raise ProductionRepairGateBlocked("ESCALATE_UPSTREAM must patch a strict ancestor of responsible_ref")

        if value.mode is ProductionRepairMode.ESCALATE_UPSTREAM:
            assert value.prior_repair_plan_ref is not None
            await self._assert_current(value.prior_repair_plan_ref, "prior RepairPlan", {LifecycleState.APPROVED})
            prior = await self.get_repair_plan(value.prior_repair_plan_ref)
            if prior is None:
                raise ProductionRepairGateBlocked("prior RepairPlan exact version not found")
            prior_value = prior.value
            assert isinstance(prior_value, RepairPlan)
            if prior_value.localization_ref != value.localization_ref:
                raise ProductionRepairGateBlocked("escalation must continue the same exact DefectLocalization")

        patch_descendants: set[tuple[str, str]] = set()
        for patch_ref in value.patch_refs:
            patch_descendants.update(_ref_key(item.ref) for item in await self.graph.descendants(patch_ref))
        for ref in value.invalidate_refs:
            await self._assert_current(ref, "invalidate target", _ALLOWED_CURRENT)
            if _ref_key(ref) not in patch_descendants:
                raise ProductionRepairGateBlocked("invalidate_refs must be strict dependency descendants of patch_refs")

        for ref in value.preserve_refs:
            await self._assert_current(ref, "preserve obligation", _ALLOWED_CURRENT)
            if _ref_key(ref) in patch_descendants:
                raise ProductionRepairGateBlocked("preserve obligation cannot be downstream of a patched source")

        if localization.qa_kind not in {requirement.qa_kind for requirement in value.recheck}:
            raise ProductionRepairGateBlocked("RepairPlan must re-run the originating QA family")
        valid_recheck_scope = {
            responsible_key,
            *({_ref_key(ref) for ref in value.patch_refs}),
            *({_ref_key(ref) for ref in value.invalidate_refs}),
            *patch_descendants,
        }
        for requirement in value.recheck:
            for ref in requirement.scope_refs:
                await self._assert_current(ref, "re-QA scope", _ALLOWED_CURRENT)
                if _ref_key(ref) not in valid_recheck_scope:
                    raise ProductionRepairGateBlocked("re-QA scope must be within the diagnosed repair dependency path")

    async def _assert_all_sources_exist(self, value: ProductionRepairValue) -> None:
        for binding in value.source_bindings():
            if await self.versions.get_version(binding.source) is None:
                raise ProductionRepairGateBlocked(
                    f"missing exact source version for {binding.role}: "
                    f"{binding.source.logical_id.root}/{binding.source.version_id.root}"
                )

    async def _assert_current(
        self,
        ref: VersionRef,
        label: str,
        allowed: set[LifecycleState],
    ) -> None:
        pointer = await self.versions.get_current(ref.logical_id)
        if pointer is None or pointer.version_id != ref.version_id:
            raise ProductionRepairGateBlocked(f"{label} must reference the exact current version")
        if pointer.status not in allowed:
            raise ProductionRepairGateBlocked(
                f"{label} lifecycle {pointer.status.value} is not allowed"
            )

    def _assert_provenance(self, value: ProductionRepairValue, provenance: Provenance) -> None:
        if provenance.source_versions != value.source_bindings():
            raise ProductionRepairIdentityError("provenance must exactly bind production-repair sources")
        required_version_refs = set(_version_provenance_refs(value))
        if not required_version_refs.issubset(set(provenance.source_refs)):
            raise ProductionRepairIdentityError(
                "provenance must pin production-repair registry/detector/planner version evidence"
            )

    @staticmethod
    def _artifact(
        value: ProductionRepairValue,
        provenance: Provenance,
        created_at: datetime,
        predecessor: VersionRef | None,
    ) -> ProductionRepairArtifact:
        return ProductionRepairArtifact(
            metadata=SemanticRecordMetadata(
                logical_id=value.logical_id,
                version_id=value.version_id,
                provenance=provenance,
                created_at=created_at,
                predecessor=predecessor,
            ),
            value=value,
        )
