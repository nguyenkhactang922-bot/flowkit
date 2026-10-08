"""IMP-062 provider-neutral Continuity QA and Sequence QA boundaries.

These evaluators own cross-boundary QA evidence only. They bind exact accepted
canonical inputs, never rewrite Story/Shot/State truth, and persist immutable
versioned results through the shared semantic VersionRepository.
"""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Protocol

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from .invalidation import DependencyGraphRepository, InvalidationRepository
from .primitives import (
    FindingSeverity,
    GateVerdict,
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    VersionId,
    VersionRef,
)
from .state_continuity import ContinuityLedger, StateSnapshot
from .versioning import VersionRepository


_ACCEPTED = {LifecycleState.APPROVED, LifecycleState.LOCKED}


class CrossBoundaryQAError(RuntimeError):
    """Base IMP-062 QA error."""


class CrossBoundaryQAGateBlocked(CrossBoundaryQAError):
    """Exact-version, stale-input, or authority-scope gate failed closed."""


class CrossBoundaryQAIdentityError(CrossBoundaryQAError):
    """Immutable result identity/replay conflict."""


class CrossBoundaryQAExecutionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    EVALUATOR_ERROR = "EVALUATOR_ERROR"


class CrossBoundaryQAFindingVerdict(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_EVALUATED = "NOT_EVALUATED"


class CrossBoundaryQAPolicy(BaseModel):
    """Versioned cross-boundary acceptance policy; aggregate score is never authoritative."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_version: str
    auto_approve_pass: bool = False
    not_evaluated_requires_review: bool = True

    @field_validator("policy_version")
    @classmethod
    def validate_policy_version(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("policy_version must be non-empty")
        return value


class ShotQABinding(BaseModel):
    """Ordered shot member plus one-or-more exact accepted per-shot QA results."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    shot_ref: VersionRef
    qa_result_refs: tuple[VersionRef, ...] = Field(min_length=1)

    @field_validator("qa_result_refs")
    @classmethod
    def normalize_qa_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        keys = [(ref.logical_id.root, ref.version_id.root) for ref in values]
        if len(keys) != len(set(keys)):
            raise ValueError("qa_result_refs must be unique")
        for ref in values:
            if not ref.logical_id.root.startswith(("qa-result:", "motion-qa-result:")):
                raise ValueError("shot QA refs must identify StaticQAResult or MotionQAResult")
        return values


class ContinuityQADimension(str, Enum):
    IDENTITY = "IDENTITY"
    WARDROBE = "WARDROBE"
    PROPS = "PROPS"
    LOCATION_WORLD = "LOCATION_WORLD"
    TIME_LIGHT = "TIME_LIGHT"
    SPATIAL = "SPATIAL"
    ACTION = "ACTION"
    RELATIONSHIP_KNOWLEDGE = "RELATIONSHIP_KNOWLEDGE"


class ContinuityQAFinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dimension: ContinuityQADimension
    verdict: CrossBoundaryQAFindingVerdict
    severity: FindingSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    reason_code: str
    explanation: str
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    source_refs: tuple[VersionRef, ...] = ()
    scene_refs: tuple[VersionRef, ...] = ()
    shot_refs: tuple[VersionRef, ...] = ()
    state_fact_keys: tuple[str, ...] = ()
    canonical_state_contradiction: bool = False
    visual_similarity_score: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("reason_code", "explanation")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{info.field_name} must be non-empty")
        return value

    @field_validator("evidence_refs")
    @classmethod
    def normalize_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        values = tuple(value.strip() for value in values)
        if any(not value for value in values) or len(values) != len(set(values)):
            raise ValueError("evidence_refs must be non-empty and unique")
        return values

    @field_validator("source_refs", "scene_refs", "shot_refs")
    @classmethod
    def unique_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        keys = [(ref.logical_id.root, ref.version_id.root) for ref in values]
        if len(keys) != len(set(keys)):
            raise ValueError("localized refs must be unique")
        return values

    @field_validator("state_fact_keys")
    @classmethod
    def normalize_fact_keys(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(value.strip() for value in values)
        if any(not value for value in cleaned) or len(cleaned) != len(set(cleaned)):
            raise ValueError("state_fact_keys must be non-empty and unique when present")
        return cleaned

    @model_validator(mode="after")
    def validate_contradiction(self) -> "ContinuityQAFinding":
        if self.canonical_state_contradiction:
            if not self.state_fact_keys:
                raise ValueError("canonical state contradiction requires exact StateFact keys")
            if self.verdict is not CrossBoundaryQAFindingVerdict.FAIL:
                raise ValueError("canonical state contradiction must be FAIL")
            if self.severity is not FindingSeverity.BLOCKER:
                raise ValueError("canonical state contradiction must be BLOCKER")
        return self


class ContinuityQAEvaluatorResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_id: str
    evaluator_version: str
    findings: tuple[ContinuityQAFinding, ...]
    aggregate_score: float | None = Field(default=None, ge=0.0, le=100.0)

    @field_validator("evaluator_id", "evaluator_version")
    @classmethod
    def validate_identity(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{info.field_name} must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_dimensions(self) -> "ContinuityQAEvaluatorResponse":
        dimensions = [finding.dimension for finding in self.findings]
        if len(dimensions) != len(set(dimensions)) or set(dimensions) != set(ContinuityQADimension):
            raise ValueError("Continuity QA must return every canonical dimension exactly once")
        return self


class ContinuityQAEvaluatorSubject(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    continuity_ledger: ContinuityLedger
    state_snapshots: tuple[StateSnapshot, ...]
    scene_refs: tuple[VersionRef, ...]
    shot_qa_bindings: tuple[ShotQABinding, ...]


class ContinuityQAEvaluator(Protocol):
    evaluator_id: str
    evaluator_version: str

    async def evaluate(self, subject: ContinuityQAEvaluatorSubject) -> ContinuityQAEvaluatorResponse:
        """Evaluate adjacent/cross-shot continuity against canonical state authority."""


class ContinuityQAExecutionRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    continuity_ledger_ref: VersionRef
    scene_refs: tuple[VersionRef, ...] = Field(min_length=1)
    shot_qa_bindings: tuple[ShotQABinding, ...] = Field(min_length=2)
    result_version_id: VersionId
    policy: CrossBoundaryQAPolicy
    actor_ref: str
    reason: str
    correlation_id: str
    recorded_at: AwareDatetime
    evidence_refs: tuple[str, ...] = Field(min_length=1)

    @field_validator("actor_ref", "reason", "correlation_id")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{info.field_name} must be non-empty")
        return value

    @field_validator("evidence_refs")
    @classmethod
    def normalize_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        values = tuple(value.strip() for value in values)
        if any(not value for value in values) or len(values) != len(set(values)):
            raise ValueError("evidence_refs must be non-empty and unique")
        return values

    @model_validator(mode="after")
    def validate_scope(self) -> "ContinuityQAExecutionRequest":
        if not self.continuity_ledger_ref.logical_id.root.startswith(
            f"continuity-ledger:{self.project_id.root}:"
        ):
            raise ValueError("continuity_ledger_ref must belong to project")
        scene_keys = []
        for ref in self.scene_refs:
            if not ref.logical_id.root.startswith(f"scene:{self.project_id.root}:"):
                raise ValueError("scene_refs must belong to project")
            scene_keys.append((ref.logical_id.root, ref.version_id.root))
        if len(scene_keys) != len(set(scene_keys)):
            raise ValueError("scene_refs must be unique")
        shot_keys = []
        for binding in self.shot_qa_bindings:
            if not binding.shot_ref.logical_id.root.startswith(f"shot-list-item:{self.project_id.root}:"):
                raise ValueError("shot refs must belong to project")
            shot_keys.append((binding.shot_ref.logical_id.root, binding.shot_ref.version_id.root))
        if len(shot_keys) != len(set(shot_keys)):
            raise ValueError("shot_qa_bindings cannot duplicate shot refs")
        return self


class ContinuityQAResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    qa_result_id: LogicalId
    version_id: VersionId
    continuity_ledger_ref: VersionRef
    state_snapshot_refs: tuple[VersionRef, ...]
    approval_designation_refs: tuple[VersionRef, ...]
    reference_asset_refs: tuple[VersionRef, ...] = ()
    approved_artifact_refs: tuple[VersionRef, ...] = ()
    scene_refs: tuple[VersionRef, ...]
    shot_qa_bindings: tuple[ShotQABinding, ...]
    evaluator_id: str
    evaluator_version: str
    policy_version: str
    execution_status: CrossBoundaryQAExecutionStatus
    findings: tuple[ContinuityQAFinding, ...] = ()
    aggregate_score: float | None = Field(default=None, ge=0.0, le=100.0)
    verdict: GateVerdict | None = None
    error_code: str | None = None
    error_message: str | None = None
    evaluated_at: AwareDatetime

    @model_validator(mode="after")
    def validate_result(self) -> "ContinuityQAResult":
        expected = continuity_qa_result_logical_id(self.project_id, self.continuity_ledger_ref)
        if self.qa_result_id != expected:
            raise ValueError(f"qa_result_id must be {expected.root}")
        if self.execution_status is CrossBoundaryQAExecutionStatus.EVALUATOR_ERROR:
            if self.verdict is not None or self.findings or not self.error_code or not self.error_message:
                raise ValueError("EVALUATOR_ERROR requires error evidence and no verdict/findings")
            return self
        if self.error_code is not None or self.error_message is not None:
            raise ValueError("completed ContinuityQAResult cannot carry evaluator error fields")
        if self.verdict is None or self.verdict is GateVerdict.OPEN:
            raise ValueError("completed ContinuityQAResult requires closed verdict")
        dimensions = [finding.dimension for finding in self.findings]
        if len(dimensions) != len(set(dimensions)) or set(dimensions) != set(ContinuityQADimension):
            raise ValueError("completed ContinuityQAResult requires every dimension exactly once")
        if any(finding.canonical_state_contradiction for finding in self.findings):
            if self.verdict is not GateVerdict.FAIL:
                raise ValueError("canonical state contradiction forces Continuity QA FAIL")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.qa_result_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [SourceVersionBinding(role="continuity_ledger", source=self.continuity_ledger_ref)]
        values.extend(
            SourceVersionBinding(role=f"state_snapshot_{index:03d}", source=ref)
            for index, ref in enumerate(self.state_snapshot_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"state_approval_{index:03d}", source=ref)
            for index, ref in enumerate(self.approval_designation_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"reference_asset_{index:03d}", source=ref)
            for index, ref in enumerate(self.reference_asset_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"approved_artifact_{index:03d}", source=ref)
            for index, ref in enumerate(self.approved_artifact_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"scene_{index:03d}", source=ref)
            for index, ref in enumerate(self.scene_refs)
        )
        for shot_index, binding in enumerate(self.shot_qa_bindings):
            values.append(SourceVersionBinding(role=f"shot_{shot_index:03d}", source=binding.shot_ref))
            values.extend(
                SourceVersionBinding(
                    role=f"shot_{shot_index:03d}_qa_{qa_index:03d}",
                    source=ref,
                )
                for qa_index, ref in enumerate(binding.qa_result_refs)
            )
        for finding in self.findings:
            values.extend(
                SourceVersionBinding(
                    role=f"finding_{finding.dimension.value.lower()}_{index:03d}",
                    source=ref,
                )
                for index, ref in enumerate(finding.source_refs)
            )
        return tuple(values)


class ContinuityQAArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: ContinuityQAResult

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


class SequenceQADimension(str, Enum):
    NARRATIVE_CONTINUITY = "NARRATIVE_CONTINUITY"
    CHARACTER_CONTINUITY = "CHARACTER_CONTINUITY"
    WARDROBE_PROP_CONTINUITY = "WARDROBE_PROP_CONTINUITY"
    LOCATION_WORLD_CONTINUITY = "LOCATION_WORLD_CONTINUITY"
    TIME_LIGHTING_CONTINUITY = "TIME_LIGHTING_CONTINUITY"
    SPATIAL_CONTINUITY = "SPATIAL_CONTINUITY"
    ACTION_CONTINUITY = "ACTION_CONTINUITY"
    VISUAL_RHYTHM = "VISUAL_RHYTHM"
    SHOT_REDUNDANCY = "SHOT_REDUNDANCY"
    COVERAGE_SUFFICIENCY = "COVERAGE_SUFFICIENCY"
    TRANSITION_COHERENCE = "TRANSITION_COHERENCE"
    EMOTIONAL_PROGRESSION = "EMOTIONAL_PROGRESSION"
    SETUP_PAYOFF_CONTINUITY = "SETUP_PAYOFF_CONTINUITY"
    APPROVED_END_STATE_PROPAGATION = "APPROVED_END_STATE_PROPAGATION"


class SequenceQAFinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dimension: SequenceQADimension
    verdict: CrossBoundaryQAFindingVerdict
    severity: FindingSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    reason_code: str
    explanation: str
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    source_refs: tuple[VersionRef, ...] = ()
    scene_refs: tuple[VersionRef, ...] = ()
    shot_refs: tuple[VersionRef, ...] = ()
    transition_from_shot_ref: VersionRef | None = None
    transition_to_shot_ref: VersionRef | None = None

    @field_validator("reason_code", "explanation")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{info.field_name} must be non-empty")
        return value

    @field_validator("evidence_refs")
    @classmethod
    def normalize_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        values = tuple(value.strip() for value in values)
        if any(not value for value in values) or len(values) != len(set(values)):
            raise ValueError("evidence_refs must be non-empty and unique")
        return values

    @field_validator("source_refs", "scene_refs", "shot_refs")
    @classmethod
    def unique_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        keys = [(ref.logical_id.root, ref.version_id.root) for ref in values]
        if len(keys) != len(set(keys)):
            raise ValueError("localized refs must be unique")
        return values

    @model_validator(mode="after")
    def validate_transition_pair(self) -> "SequenceQAFinding":
        if (self.transition_from_shot_ref is None) != (self.transition_to_shot_ref is None):
            raise ValueError("transition localization requires both from/to shot refs")
        if self.transition_from_shot_ref is not None and self.transition_from_shot_ref == self.transition_to_shot_ref:
            raise ValueError("transition from/to shot refs must differ")
        return self


class SequenceQAEvaluatorResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_id: str
    evaluator_version: str
    findings: tuple[SequenceQAFinding, ...]
    aggregate_score: float | None = Field(default=None, ge=0.0, le=100.0)

    @field_validator("evaluator_id", "evaluator_version")
    @classmethod
    def validate_identity(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{info.field_name} must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_dimensions(self) -> "SequenceQAEvaluatorResponse":
        dimensions = [finding.dimension for finding in self.findings]
        if len(dimensions) != len(set(dimensions)) or set(dimensions) != set(SequenceQADimension):
            raise ValueError("Sequence QA must return every minimum canonical dimension exactly once")
        return self


class SequenceQAEvaluatorSubject(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    sequence_ref: VersionRef
    scene_refs: tuple[VersionRef, ...]
    shot_qa_bindings: tuple[ShotQABinding, ...]
    continuity_qa_refs: tuple[VersionRef, ...]
    setup_payoff_refs: tuple[VersionRef, ...]


class SequenceQAEvaluator(Protocol):
    evaluator_id: str
    evaluator_version: str

    async def evaluate(self, subject: SequenceQAEvaluatorSubject) -> SequenceQAEvaluatorResponse:
        """Evaluate cross-shot/cross-scene sequence quality without rewriting narrative truth."""


class SequenceQAExecutionRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    sequence_ref: VersionRef
    scene_refs: tuple[VersionRef, ...] = Field(min_length=1)
    shot_qa_bindings: tuple[ShotQABinding, ...] = Field(min_length=1)
    continuity_qa_refs: tuple[VersionRef, ...] = ()
    setup_payoff_refs: tuple[VersionRef, ...] = ()
    result_version_id: VersionId
    policy: CrossBoundaryQAPolicy
    actor_ref: str
    reason: str
    correlation_id: str
    recorded_at: AwareDatetime
    evidence_refs: tuple[str, ...] = Field(min_length=1)

    @field_validator("actor_ref", "reason", "correlation_id")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{info.field_name} must be non-empty")
        return value

    @field_validator("evidence_refs")
    @classmethod
    def normalize_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        values = tuple(value.strip() for value in values)
        if any(not value for value in values) or len(values) != len(set(values)):
            raise ValueError("evidence_refs must be non-empty and unique")
        return values

    @model_validator(mode="after")
    def validate_scope(self) -> "SequenceQAExecutionRequest":
        if not self.sequence_ref.logical_id.root.startswith(f"sequence:{self.project_id.root}:"):
            raise ValueError("sequence_ref must belong to project")
        scene_keys = []
        for ref in self.scene_refs:
            if not ref.logical_id.root.startswith(f"scene:{self.project_id.root}:"):
                raise ValueError("scene_refs must belong to project")
            scene_keys.append((ref.logical_id.root, ref.version_id.root))
        if len(scene_keys) != len(set(scene_keys)):
            raise ValueError("scene_refs must be unique")
        shot_keys = []
        for binding in self.shot_qa_bindings:
            if not binding.shot_ref.logical_id.root.startswith(f"shot-list-item:{self.project_id.root}:"):
                raise ValueError("shot refs must belong to project")
            shot_keys.append((binding.shot_ref.logical_id.root, binding.shot_ref.version_id.root))
        if len(shot_keys) != len(set(shot_keys)):
            raise ValueError("shot_qa_bindings cannot duplicate shot refs")
        continuity_keys = [(ref.logical_id.root, ref.version_id.root) for ref in self.continuity_qa_refs]
        if len(continuity_keys) != len(set(continuity_keys)):
            raise ValueError("continuity_qa_refs must be unique")
        if any(not ref.logical_id.root.startswith("continuity-qa-result:") for ref in self.continuity_qa_refs):
            raise ValueError("continuity_qa_refs must identify ContinuityQAResult")
        payoff_keys = [(ref.logical_id.root, ref.version_id.root) for ref in self.setup_payoff_refs]
        if len(payoff_keys) != len(set(payoff_keys)):
            raise ValueError("setup_payoff_refs must be unique")
        if any(not ref.logical_id.root.startswith(f"setup-payoff:{self.project_id.root}:") for ref in self.setup_payoff_refs):
            raise ValueError("setup_payoff_refs must belong to project")
        return self


class SequenceQAResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    qa_result_id: LogicalId
    version_id: VersionId
    sequence_ref: VersionRef
    scene_refs: tuple[VersionRef, ...]
    shot_qa_bindings: tuple[ShotQABinding, ...]
    continuity_qa_refs: tuple[VersionRef, ...] = ()
    setup_payoff_refs: tuple[VersionRef, ...] = ()
    evaluator_id: str
    evaluator_version: str
    policy_version: str
    execution_status: CrossBoundaryQAExecutionStatus
    findings: tuple[SequenceQAFinding, ...] = ()
    aggregate_score: float | None = Field(default=None, ge=0.0, le=100.0)
    verdict: GateVerdict | None = None
    error_code: str | None = None
    error_message: str | None = None
    evaluated_at: AwareDatetime

    @model_validator(mode="after")
    def validate_result(self) -> "SequenceQAResult":
        expected = sequence_qa_result_logical_id(self.project_id, self.sequence_ref)
        if self.qa_result_id != expected:
            raise ValueError(f"qa_result_id must be {expected.root}")
        if self.execution_status is CrossBoundaryQAExecutionStatus.EVALUATOR_ERROR:
            if self.verdict is not None or self.findings or not self.error_code or not self.error_message:
                raise ValueError("EVALUATOR_ERROR requires error evidence and no verdict/findings")
            return self
        if self.error_code is not None or self.error_message is not None:
            raise ValueError("completed SequenceQAResult cannot carry evaluator error fields")
        if self.verdict is None or self.verdict is GateVerdict.OPEN:
            raise ValueError("completed SequenceQAResult requires closed verdict")
        dimensions = [finding.dimension for finding in self.findings]
        if len(dimensions) != len(set(dimensions)) or set(dimensions) != set(SequenceQADimension):
            raise ValueError("completed SequenceQAResult requires every dimension exactly once")
        if any(
            finding.verdict is CrossBoundaryQAFindingVerdict.FAIL
            and finding.severity is FindingSeverity.BLOCKER
            for finding in self.findings
        ) and self.verdict is not GateVerdict.FAIL:
            raise ValueError("blocking sequence defect forces Sequence QA FAIL")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.qa_result_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [SourceVersionBinding(role="sequence", source=self.sequence_ref)]
        values.extend(
            SourceVersionBinding(role=f"scene_{index:03d}", source=ref)
            for index, ref in enumerate(self.scene_refs)
        )
        for shot_index, binding in enumerate(self.shot_qa_bindings):
            values.append(SourceVersionBinding(role=f"shot_{shot_index:03d}", source=binding.shot_ref))
            values.extend(
                SourceVersionBinding(
                    role=f"shot_{shot_index:03d}_qa_{qa_index:03d}",
                    source=ref,
                )
                for qa_index, ref in enumerate(binding.qa_result_refs)
            )
        values.extend(
            SourceVersionBinding(role=f"continuity_qa_{index:03d}", source=ref)
            for index, ref in enumerate(self.continuity_qa_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"setup_payoff_{index:03d}", source=ref)
            for index, ref in enumerate(self.setup_payoff_refs)
        )
        for finding in self.findings:
            values.extend(
                SourceVersionBinding(
                    role=f"finding_{finding.dimension.value.lower()}_{index:03d}",
                    source=ref,
                )
                for index, ref in enumerate(finding.source_refs)
            )
        return tuple(values)


class SequenceQAArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: SequenceQAResult

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


def continuity_qa_result_logical_id(project_id: LogicalId, ledger_ref: VersionRef) -> LogicalId:
    raw = f"{project_id.root}\0{ledger_ref.logical_id.root}".encode("utf-8")
    return LogicalId("continuity-qa-result:" + hashlib.sha256(raw).hexdigest())


def sequence_qa_result_logical_id(project_id: LogicalId, sequence_ref: VersionRef) -> LogicalId:
    raw = f"{project_id.root}\0{sequence_ref.logical_id.root}".encode("utf-8")
    return LogicalId("sequence-qa-result:" + hashlib.sha256(raw).hexdigest())


def _decide(
    findings,
    policy: CrossBoundaryQAPolicy,
    *,
    contradiction: bool = False,
) -> GateVerdict:
    if contradiction:
        return GateVerdict.FAIL
    if any(finding.verdict is CrossBoundaryQAFindingVerdict.FAIL for finding in findings):
        return GateVerdict.FAIL
    if policy.not_evaluated_requires_review and any(
        finding.verdict is CrossBoundaryQAFindingVerdict.NOT_EVALUATED for finding in findings
    ):
        return GateVerdict.NEEDS_HUMAN_REVIEW
    if any(finding.verdict is CrossBoundaryQAFindingVerdict.WARN for finding in findings):
        return GateVerdict.WARN
    return GateVerdict.PASS


def decide_continuity_qa_verdict(
    findings: tuple[ContinuityQAFinding, ...],
    policy: CrossBoundaryQAPolicy,
) -> GateVerdict:
    dimensions = [finding.dimension for finding in findings]
    if len(dimensions) != len(set(dimensions)) or set(dimensions) != set(ContinuityQADimension):
        raise CrossBoundaryQAGateBlocked("Continuity QA verdict requires every canonical dimension")
    return _decide(
        findings,
        policy,
        contradiction=any(finding.canonical_state_contradiction for finding in findings),
    )


def decide_sequence_qa_verdict(
    findings: tuple[SequenceQAFinding, ...],
    policy: CrossBoundaryQAPolicy,
) -> GateVerdict:
    dimensions = [finding.dimension for finding in findings]
    if len(dimensions) != len(set(dimensions)) or set(dimensions) != set(SequenceQADimension):
        raise CrossBoundaryQAGateBlocked("Sequence QA verdict requires every canonical dimension")
    return _decide(findings, policy)


class _CrossBoundaryQAStore:
    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)

    async def assert_exact_current_accepted(self, ref: VersionRef, label: str) -> None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise CrossBoundaryQAGateBlocked(f"{label} exact version does not exist")
        pointer = await self.versions.get_current(ref.logical_id)
        if pointer is None or pointer.version_id != ref.version_id or pointer.status not in _ACCEPTED:
            raise CrossBoundaryQAGateBlocked(f"{label} is not exact current APPROVED/LOCKED")
        for record in await self.invalidations.list_unresolved():
            if record.affected_object_id == ref.logical_id and record.affected_object_version == ref.version_id:
                raise CrossBoundaryQAGateBlocked(f"{label} has unresolved durable invalidation")

    async def persist(self, value, request, *, edge_type: str):
        finding_evidence = tuple(
            evidence
            for finding in value.findings
            for evidence in finding.evidence_refs
        )
        source_refs = tuple(
            dict.fromkeys(
                (
                    f"evaluator:{value.evaluator_id}@{value.evaluator_version}",
                    f"policy:{value.policy_version}",
                    *request.evidence_refs,
                    *finding_evidence,
                )
            )
        )
        provenance = Provenance(
            source_versions=value.source_bindings(),
            source_refs=source_refs,
            actor_ref=request.actor_ref,
            reason=request.reason,
            recorded_at=request.recorded_at,
            correlation_id=request.correlation_id,
        )
        existing = await self.versions.get_version(value.ref)
        if existing is not None:
            if existing.payload != value.model_dump(mode="json") or existing.metadata.provenance != provenance:
                raise CrossBoundaryQAIdentityError("exact QA result replay conflicts with immutable evidence")
            return existing.metadata

        pointer = await self.versions.get_current(value.logical_id)
        metadata = SemanticRecordMetadata(
            logical_id=value.logical_id,
            version_id=value.version_id,
            provenance=provenance,
            created_at=request.recorded_at,
            predecessor=None
            if pointer is None
            else VersionRef(logical_id=value.logical_id, version_id=pointer.version_id),
        )
        if pointer is None:
            stored = await self.versions.create_initial(
                metadata=metadata,
                payload=value.model_dump(mode="json"),
                status=LifecycleState.REVIEW,
            )
        else:
            stored = await self.versions.create_successor(
                metadata=metadata,
                payload=value.model_dump(mode="json"),
                supersession_reason=request.reason,
            )
            await self.versions.update_current(
                logical_id=value.logical_id,
                version_id=value.version_id,
                status=LifecycleState.REVIEW,
                expected_revision=pointer.revision,
            )
        await self._register_dependencies(value, stored.metadata, edge_type=edge_type)
        if value.verdict is GateVerdict.PASS and request.policy.auto_approve_pass:
            current = await self.versions.get_current(value.logical_id)
            assert current is not None and current.version_id == value.version_id
            await self.versions.update_current(
                logical_id=value.logical_id,
                version_id=value.version_id,
                status=LifecycleState.APPROVED,
                expected_revision=current.revision,
            )
        return stored.metadata

    async def _register_dependencies(self, value, metadata, *, edge_type: str) -> None:
        refs: dict[tuple[str, str], tuple[VersionRef, list[str]]] = {}
        for binding in value.source_bindings():
            key = (binding.source.logical_id.root, binding.source.version_id.root)
            if key not in refs:
                refs[key] = (binding.source, [])
            refs[key][1].append(binding.role)
        for key in sorted(refs):
            ref, roles = refs[key]
            await self.graph.create_edge(
                source=ref,
                dependent=value.ref,
                edge_type=edge_type,
                dependency_reason=" + ".join(sorted(set(roles))),
                provenance=metadata.provenance,
                created_at=metadata.created_at,
            )


class ContinuityQAService:
    def __init__(self, writer) -> None:
        self.store = _CrossBoundaryQAStore(writer)
        self.versions = self.store.versions
        self.graph = self.store.graph

    async def evaluate(
        self,
        request: ContinuityQAExecutionRequest,
        evaluator: ContinuityQAEvaluator,
    ) -> ContinuityQAArtifact:
        await self.store.assert_exact_current_accepted(request.continuity_ledger_ref, "ContinuityLedger")
        stored_ledger = await self.versions.get_version(request.continuity_ledger_ref)
        assert stored_ledger is not None
        ledger = ContinuityLedger.model_validate(stored_ledger.payload)
        if ledger.project_id != request.project_id or ledger.ref != request.continuity_ledger_ref:
            raise CrossBoundaryQAGateBlocked("ContinuityLedger project/identity mismatch")

        state_snapshots: list[StateSnapshot] = []
        for binding in ledger.source_bindings():
            await self.store.assert_exact_current_accepted(binding.source, binding.role)
        for ref in ledger.state_snapshot_refs:
            stored = await self.versions.get_version(ref)
            assert stored is not None
            snapshot = StateSnapshot.model_validate(stored.payload)
            if snapshot.project_id != request.project_id or snapshot.ref != ref:
                raise CrossBoundaryQAGateBlocked("StateSnapshot project/identity mismatch")
            state_snapshots.append(snapshot)

        for index, ref in enumerate(request.scene_refs):
            await self.store.assert_exact_current_accepted(ref, f"scene_{index:03d}")
        for index, binding in enumerate(request.shot_qa_bindings):
            await self.store.assert_exact_current_accepted(binding.shot_ref, f"shot_{index:03d}")
            for qa_index, ref in enumerate(binding.qa_result_refs):
                await self.store.assert_exact_current_accepted(ref, f"shot_{index:03d}_qa_{qa_index:03d}")

        evaluator_id = str(getattr(evaluator, "evaluator_id", "")).strip()
        evaluator_version = str(getattr(evaluator, "evaluator_version", "")).strip()
        if not evaluator_id or not evaluator_version:
            raise CrossBoundaryQAGateBlocked("Continuity QA evaluator must declare identity/version")

        subject = ContinuityQAEvaluatorSubject(
            continuity_ledger=ledger,
            state_snapshots=tuple(state_snapshots),
            scene_refs=request.scene_refs,
            shot_qa_bindings=request.shot_qa_bindings,
        )
        base_refs = self._base_refs(request, ledger)
        allowed_fact_keys = {fact.fact_key for snapshot in state_snapshots for fact in snapshot.facts}
        try:
            response = await evaluator.evaluate(subject)
            if response.evaluator_id != evaluator_id or response.evaluator_version != evaluator_version:
                raise CrossBoundaryQAGateBlocked("Continuity evaluator response identity/version mismatch")
            self._validate_response_scope(request, response, base_refs, allowed_fact_keys)
            verdict = decide_continuity_qa_verdict(response.findings, request.policy)
            value = ContinuityQAResult(
                project_id=request.project_id,
                qa_result_id=continuity_qa_result_logical_id(request.project_id, request.continuity_ledger_ref),
                version_id=request.result_version_id,
                continuity_ledger_ref=request.continuity_ledger_ref,
                state_snapshot_refs=ledger.state_snapshot_refs,
                approval_designation_refs=ledger.approval_designation_refs,
                reference_asset_refs=ledger.reference_asset_refs,
                approved_artifact_refs=ledger.approved_artifact_refs,
                scene_refs=request.scene_refs,
                shot_qa_bindings=request.shot_qa_bindings,
                evaluator_id=response.evaluator_id,
                evaluator_version=response.evaluator_version,
                policy_version=request.policy.policy_version,
                execution_status=CrossBoundaryQAExecutionStatus.COMPLETED,
                findings=response.findings,
                aggregate_score=response.aggregate_score,
                verdict=verdict,
                evaluated_at=request.recorded_at,
            )
        except Exception as exc:
            value = ContinuityQAResult(
                project_id=request.project_id,
                qa_result_id=continuity_qa_result_logical_id(request.project_id, request.continuity_ledger_ref),
                version_id=request.result_version_id,
                continuity_ledger_ref=request.continuity_ledger_ref,
                state_snapshot_refs=ledger.state_snapshot_refs,
                approval_designation_refs=ledger.approval_designation_refs,
                reference_asset_refs=ledger.reference_asset_refs,
                approved_artifact_refs=ledger.approved_artifact_refs,
                scene_refs=request.scene_refs,
                shot_qa_bindings=request.shot_qa_bindings,
                evaluator_id=evaluator_id,
                evaluator_version=evaluator_version,
                policy_version=request.policy.policy_version,
                execution_status=CrossBoundaryQAExecutionStatus.EVALUATOR_ERROR,
                error_code=type(exc).__name__,
                error_message=str(exc) or type(exc).__name__,
                evaluated_at=request.recorded_at,
            )
        metadata = await self.store.persist(value, request, edge_type="continuity_qa_source")
        return ContinuityQAArtifact(metadata=metadata, value=value)

    async def get_result(self, ref: VersionRef) -> ContinuityQAArtifact | None:
        if not ref.logical_id.root.startswith("continuity-qa-result:"):
            raise CrossBoundaryQAIdentityError("expected ContinuityQAResult ref")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = ContinuityQAResult.model_validate(stored.payload)
        if value.ref != ref:
            raise CrossBoundaryQAIdentityError("stored ContinuityQAResult identity mismatch")
        return ContinuityQAArtifact(metadata=stored.metadata, value=value)

    @staticmethod
    def _base_refs(request: ContinuityQAExecutionRequest, ledger: ContinuityLedger) -> set[tuple[str, str]]:
        refs = [request.continuity_ledger_ref, *ledger.state_snapshot_refs, *ledger.approval_designation_refs]
        refs.extend(ledger.reference_asset_refs)
        refs.extend(ledger.approved_artifact_refs)
        refs.extend(request.scene_refs)
        for binding in request.shot_qa_bindings:
            refs.append(binding.shot_ref)
            refs.extend(binding.qa_result_refs)
        return {(ref.logical_id.root, ref.version_id.root) for ref in refs}

    @staticmethod
    def _validate_response_scope(
        request: ContinuityQAExecutionRequest,
        response: ContinuityQAEvaluatorResponse,
        allowed_refs: set[tuple[str, str]],
        allowed_fact_keys: set[str],
    ) -> None:
        scene_keys = {(ref.logical_id.root, ref.version_id.root) for ref in request.scene_refs}
        shot_keys = {
            (binding.shot_ref.logical_id.root, binding.shot_ref.version_id.root)
            for binding in request.shot_qa_bindings
        }
        for finding in response.findings:
            for ref in finding.source_refs:
                if (ref.logical_id.root, ref.version_id.root) not in allowed_refs:
                    raise CrossBoundaryQAGateBlocked("Continuity finding cites source outside exact inputs")
            if any((ref.logical_id.root, ref.version_id.root) not in scene_keys for ref in finding.scene_refs):
                raise CrossBoundaryQAGateBlocked("Continuity finding localizes scene outside QA scope")
            if any((ref.logical_id.root, ref.version_id.root) not in shot_keys for ref in finding.shot_refs):
                raise CrossBoundaryQAGateBlocked("Continuity finding localizes shot outside QA scope")
            if any(key not in allowed_fact_keys for key in finding.state_fact_keys):
                raise CrossBoundaryQAGateBlocked("Continuity finding cites unknown canonical StateFact key")


class SequenceQAService:
    def __init__(self, writer) -> None:
        self.store = _CrossBoundaryQAStore(writer)
        self.versions = self.store.versions
        self.graph = self.store.graph

    async def evaluate(
        self,
        request: SequenceQAExecutionRequest,
        evaluator: SequenceQAEvaluator,
    ) -> SequenceQAArtifact:
        await self.store.assert_exact_current_accepted(request.sequence_ref, "Sequence")
        for index, ref in enumerate(request.scene_refs):
            await self.store.assert_exact_current_accepted(ref, f"scene_{index:03d}")
        for index, binding in enumerate(request.shot_qa_bindings):
            await self.store.assert_exact_current_accepted(binding.shot_ref, f"shot_{index:03d}")
            for qa_index, ref in enumerate(binding.qa_result_refs):
                await self.store.assert_exact_current_accepted(ref, f"shot_{index:03d}_qa_{qa_index:03d}")
        for index, ref in enumerate(request.continuity_qa_refs):
            await self.store.assert_exact_current_accepted(ref, f"continuity_qa_{index:03d}")
            stored = await self.versions.get_version(ref)
            assert stored is not None
            continuity = ContinuityQAResult.model_validate(stored.payload)
            if continuity.project_id != request.project_id or continuity.verdict is not GateVerdict.PASS:
                raise CrossBoundaryQAGateBlocked("Sequence QA requires PASS continuity evidence for bound continuity refs")
        for index, ref in enumerate(request.setup_payoff_refs):
            await self.store.assert_exact_current_accepted(ref, f"setup_payoff_{index:03d}")

        evaluator_id = str(getattr(evaluator, "evaluator_id", "")).strip()
        evaluator_version = str(getattr(evaluator, "evaluator_version", "")).strip()
        if not evaluator_id or not evaluator_version:
            raise CrossBoundaryQAGateBlocked("Sequence QA evaluator must declare identity/version")

        subject = SequenceQAEvaluatorSubject(
            sequence_ref=request.sequence_ref,
            scene_refs=request.scene_refs,
            shot_qa_bindings=request.shot_qa_bindings,
            continuity_qa_refs=request.continuity_qa_refs,
            setup_payoff_refs=request.setup_payoff_refs,
        )
        allowed_refs = self._base_refs(request)
        try:
            response = await evaluator.evaluate(subject)
            if response.evaluator_id != evaluator_id or response.evaluator_version != evaluator_version:
                raise CrossBoundaryQAGateBlocked("Sequence evaluator response identity/version mismatch")
            self._validate_response_scope(request, response, allowed_refs)
            verdict = decide_sequence_qa_verdict(response.findings, request.policy)
            value = SequenceQAResult(
                project_id=request.project_id,
                qa_result_id=sequence_qa_result_logical_id(request.project_id, request.sequence_ref),
                version_id=request.result_version_id,
                sequence_ref=request.sequence_ref,
                scene_refs=request.scene_refs,
                shot_qa_bindings=request.shot_qa_bindings,
                continuity_qa_refs=request.continuity_qa_refs,
                setup_payoff_refs=request.setup_payoff_refs,
                evaluator_id=response.evaluator_id,
                evaluator_version=response.evaluator_version,
                policy_version=request.policy.policy_version,
                execution_status=CrossBoundaryQAExecutionStatus.COMPLETED,
                findings=response.findings,
                aggregate_score=response.aggregate_score,
                verdict=verdict,
                evaluated_at=request.recorded_at,
            )
        except Exception as exc:
            value = SequenceQAResult(
                project_id=request.project_id,
                qa_result_id=sequence_qa_result_logical_id(request.project_id, request.sequence_ref),
                version_id=request.result_version_id,
                sequence_ref=request.sequence_ref,
                scene_refs=request.scene_refs,
                shot_qa_bindings=request.shot_qa_bindings,
                continuity_qa_refs=request.continuity_qa_refs,
                setup_payoff_refs=request.setup_payoff_refs,
                evaluator_id=evaluator_id,
                evaluator_version=evaluator_version,
                policy_version=request.policy.policy_version,
                execution_status=CrossBoundaryQAExecutionStatus.EVALUATOR_ERROR,
                error_code=type(exc).__name__,
                error_message=str(exc) or type(exc).__name__,
                evaluated_at=request.recorded_at,
            )
        metadata = await self.store.persist(value, request, edge_type="sequence_qa_source")
        return SequenceQAArtifact(metadata=metadata, value=value)

    async def get_result(self, ref: VersionRef) -> SequenceQAArtifact | None:
        if not ref.logical_id.root.startswith("sequence-qa-result:"):
            raise CrossBoundaryQAIdentityError("expected SequenceQAResult ref")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = SequenceQAResult.model_validate(stored.payload)
        if value.ref != ref:
            raise CrossBoundaryQAIdentityError("stored SequenceQAResult identity mismatch")
        return SequenceQAArtifact(metadata=stored.metadata, value=value)

    @staticmethod
    def _base_refs(request: SequenceQAExecutionRequest) -> set[tuple[str, str]]:
        refs = [request.sequence_ref, *request.scene_refs, *request.continuity_qa_refs, *request.setup_payoff_refs]
        for binding in request.shot_qa_bindings:
            refs.append(binding.shot_ref)
            refs.extend(binding.qa_result_refs)
        return {(ref.logical_id.root, ref.version_id.root) for ref in refs}

    @staticmethod
    def _validate_response_scope(
        request: SequenceQAExecutionRequest,
        response: SequenceQAEvaluatorResponse,
        allowed_refs: set[tuple[str, str]],
    ) -> None:
        scene_keys = {(ref.logical_id.root, ref.version_id.root) for ref in request.scene_refs}
        ordered_shots = [binding.shot_ref for binding in request.shot_qa_bindings]
        shot_keys = {(ref.logical_id.root, ref.version_id.root) for ref in ordered_shots}
        positions = {
            (ref.logical_id.root, ref.version_id.root): index
            for index, ref in enumerate(ordered_shots)
        }
        for finding in response.findings:
            for ref in finding.source_refs:
                if (ref.logical_id.root, ref.version_id.root) not in allowed_refs:
                    raise CrossBoundaryQAGateBlocked("Sequence finding cites source outside exact inputs")
            if any((ref.logical_id.root, ref.version_id.root) not in scene_keys for ref in finding.scene_refs):
                raise CrossBoundaryQAGateBlocked("Sequence finding localizes scene outside sequence scope")
            if any((ref.logical_id.root, ref.version_id.root) not in shot_keys for ref in finding.shot_refs):
                raise CrossBoundaryQAGateBlocked("Sequence finding localizes shot outside sequence scope")
            if finding.transition_from_shot_ref is not None:
                from_key = (
                    finding.transition_from_shot_ref.logical_id.root,
                    finding.transition_from_shot_ref.version_id.root,
                )
                to_key = (
                    finding.transition_to_shot_ref.logical_id.root,
                    finding.transition_to_shot_ref.version_id.root,
                )
                if from_key not in positions or to_key not in positions or positions[to_key] != positions[from_key] + 1:
                    raise CrossBoundaryQAGateBlocked("Sequence transition localization must bind adjacent ordered shots")


__all__ = [
    "ContinuityQAArtifact",
    "ContinuityQADimension",
    "ContinuityQAEvaluator",
    "ContinuityQAEvaluatorResponse",
    "ContinuityQAEvaluatorSubject",
    "ContinuityQAExecutionRequest",
    "ContinuityQAFinding",
    "ContinuityQAResult",
    "ContinuityQAService",
    "CrossBoundaryQAError",
    "CrossBoundaryQAExecutionStatus",
    "CrossBoundaryQAFindingVerdict",
    "CrossBoundaryQAGateBlocked",
    "CrossBoundaryQAIdentityError",
    "CrossBoundaryQAPolicy",
    "SequenceQAArtifact",
    "SequenceQADimension",
    "SequenceQAEvaluator",
    "SequenceQAEvaluatorResponse",
    "SequenceQAEvaluatorSubject",
    "SequenceQAExecutionRequest",
    "SequenceQAFinding",
    "SequenceQAResult",
    "SequenceQAService",
    "ShotQABinding",
    "continuity_qa_result_logical_id",
    "decide_continuity_qa_verdict",
    "decide_sequence_qa_verdict",
    "sequence_qa_result_logical_id",
]
