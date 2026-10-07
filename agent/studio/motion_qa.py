"""IMP-061 provider-neutral Motion / Video QA contracts and orchestration.

Motion QA evaluates actual READY video bytes against exact canonical motion,
shot, state, reference and compiled expectations.  It owns QA evidence/verdict
only: it never rewrites provider state, artifact materialization truth or
upstream canonical shot/state authority.
"""

from __future__ import annotations

import hashlib
from enum import Enum
from pathlib import Path
from typing import Protocol

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from .artifact_lifecycle import ArtifactEvent, ArtifactEventKind, ArtifactEvidenceRepository, ArtifactLifecycleService
from .generation_job import (
    ArtifactState,
    CreativeState,
    GenerationJob,
    GenerationJobAxis,
    GenerationJobRepository,
    GuardFact,
    TransitionGuardEvidence,
    TransitionOwner,
)
from .invalidation import DependencyGraphRepository, InvalidationRepository
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
from .production_compiler import ShotIR
from .reference import ReferenceAsset
from .shot_realization import FullShotSpec, MotionDeltaSpec, StaticKeyframeSpec
from .state_continuity import StateSnapshot
from .versioning import VersionRepository


_ACCEPTED = {LifecycleState.APPROVED, LifecycleState.LOCKED}
_HASH_PREFIX = "sha256:"
_EPSILON = 1e-6


class MotionQAError(RuntimeError):
    """Base Motion QA error."""


class MotionQAGateBlocked(MotionQAError):
    """Raised when exact-version/video prerequisites are not safe for QA."""


class MotionQAIdentityError(MotionQAError):
    """Raised when persisted Motion QA identity/evidence conflicts."""


class MotionQADimension(str, Enum):
    TECHNICAL_INTEGRITY = "TECHNICAL_INTEGRITY"
    TEMPORAL_ACTION = "TEMPORAL_ACTION"
    IDENTITY_DRIFT = "IDENTITY_DRIFT"
    STATE_PROP_LOCATION_DRIFT = "STATE_PROP_LOCATION_DRIFT"
    CAMERA_MOTION = "CAMERA_MOTION"
    DURATION = "DURATION"
    SPEECH_ACTION_SYNC = "SPEECH_ACTION_SYNC"
    END_STATE_OBSERVABILITY = "END_STATE_OBSERVABILITY"


class MotionQAFindingVerdict(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_EVALUATED = "NOT_EVALUATED"


class MotionQASeverity(str, Enum):
    BLOCKING = "BLOCKING"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    COSMETIC = "COSMETIC"


class MotionQAExecutionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    EVALUATOR_ERROR = "EVALUATOR_ERROR"


class MotionQAPolicy(BaseModel):
    """Versioned acceptance policy; aggregate score is never authoritative."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_version: str
    auto_approve_pass: bool = False
    high_fail_count_for_fail: int = Field(default=2, ge=1)
    medium_fail_requires_review: bool = True
    not_evaluated_requires_review: bool = True

    @field_validator("policy_version")
    @classmethod
    def validate_policy_version(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("policy_version must be non-empty")
        return value


class MotionQAFinding(BaseModel):
    """One canonical time-bound finding for one Motion QA dimension."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dimension: MotionQADimension
    verdict: MotionQAFindingVerdict
    severity: MotionQASeverity
    confidence: float = Field(ge=0.0, le=1.0)
    reason_code: str
    explanation: str
    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(ge=0.0)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    source_refs: tuple[VersionRef, ...] = ()

    @field_validator("reason_code", "explanation")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{info.field_name} must be non-empty")
        return value

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(value.strip() for value in values)
        if any(not value for value in cleaned):
            raise ValueError("evidence_refs must be non-empty")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("evidence_refs must be unique")
        return cleaned

    @field_validator("source_refs")
    @classmethod
    def validate_source_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        keys = [(ref.logical_id.root, ref.version_id.root) for ref in values]
        if len(set(keys)) != len(keys):
            raise ValueError("source_refs must be unique")
        return values

    @model_validator(mode="after")
    def validate_range(self) -> "MotionQAFinding":
        if self.end_seconds + _EPSILON < self.start_seconds:
            raise ValueError("end_seconds must be >= start_seconds")
        return self


class MotionQAEvaluatorResponse(BaseModel):
    """Provider-neutral evaluator output before policy application."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_id: str
    evaluator_version: str
    observed_duration_seconds: float = Field(gt=0.0)
    findings: tuple[MotionQAFinding, ...]
    aggregate_score: float | None = Field(default=None, ge=0.0, le=100.0)

    @field_validator("evaluator_id", "evaluator_version")
    @classmethod
    def validate_identity(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{info.field_name} must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_dimensions_and_ranges(self) -> "MotionQAEvaluatorResponse":
        dimensions = [finding.dimension for finding in self.findings]
        if len(dimensions) != len(set(dimensions)) or set(dimensions) != set(MotionQADimension):
            raise ValueError("Motion QA evaluator must return exactly one finding for every canonical dimension")
        if any(finding.end_seconds > self.observed_duration_seconds + _EPSILON for finding in self.findings):
            raise ValueError("Motion QA finding time range exceeds observed video duration")
        return self


class MotionQAEvaluatorSubject(BaseModel):
    """Runtime-only evaluator subject; absolute path is never canonical truth."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    artifact_path: Path
    artifact_id: LogicalId
    artifact_event_id: str
    content_sha256: str
    byte_count: int = Field(ge=0)
    media_type: str
    generation_job_id: LogicalId
    shot_ir: ShotIR
    motion_delta_spec: MotionDeltaSpec
    full_shot_spec: FullShotSpec
    static_keyframe_spec: StaticKeyframeSpec
    state_snapshot: StateSnapshot
    reference_assets: tuple[ReferenceAsset, ...]
    visible_subject_refs: tuple[VersionRef, ...] = ()


class MotionQAEvaluator(Protocol):
    evaluator_id: str
    evaluator_version: str

    async def evaluate(self, subject: MotionQAEvaluatorSubject) -> MotionQAEvaluatorResponse:
        """Inspect actual video bytes and return time-bound canonical findings."""


class MotionQAExecutionRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    generation_job_id: LogicalId
    motion_delta_spec_ref: VersionRef
    result_version_id: VersionId
    policy: MotionQAPolicy
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
    def validate_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(value.strip() for value in values)
        if any(not value for value in cleaned):
            raise ValueError("evidence_refs must be non-empty")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("evidence_refs must be unique")
        return cleaned


class MotionQAResult(BaseModel):
    """Immutable Motion QA evidence bound to exact video bytes and expectations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    qa_result_id: LogicalId
    version_id: VersionId
    generation_job_id: LogicalId
    artifact_id: LogicalId
    artifact_event_id: str
    artifact_content_sha256: str
    artifact_byte_count: int = Field(ge=0)
    media_type: str
    shot_ir_ref: VersionRef
    motion_delta_spec_ref: VersionRef
    full_shot_spec_ref: VersionRef
    static_keyframe_spec_ref: VersionRef
    state_snapshot_ref: VersionRef
    approved_state_designation_ref: VersionRef
    active_profile_ref: VersionRef
    reference_asset_refs: tuple[VersionRef, ...] = ()
    visible_subject_refs: tuple[VersionRef, ...] = ()
    expected_duration_seconds: int = Field(gt=0)
    observed_duration_seconds: float | None = Field(default=None, gt=0.0)
    evaluator_id: str
    evaluator_version: str
    policy_version: str
    execution_status: MotionQAExecutionStatus
    findings: tuple[MotionQAFinding, ...] = ()
    aggregate_score: float | None = Field(default=None, ge=0.0, le=100.0)
    verdict: GateVerdict | None = None
    error_code: str | None = None
    error_message: str | None = None
    evaluated_at: AwareDatetime

    @model_validator(mode="after")
    def validate_result(self) -> "MotionQAResult":
        expected = motion_qa_result_logical_id(self.project_id, self.generation_job_id)
        if self.qa_result_id != expected:
            raise ValueError(f"qa_result_id must be {expected.root}")
        if not self.artifact_content_sha256.startswith(_HASH_PREFIX):
            raise ValueError("artifact_content_sha256 must be sha256-prefixed")
        if not self.media_type.lower().startswith("video/"):
            raise ValueError("MotionQAResult media_type must be video/*")
        refs = [(ref.logical_id.root, ref.version_id.root) for ref in self.reference_asset_refs]
        if len(set(refs)) != len(refs):
            raise ValueError("reference_asset_refs must be unique")
        subjects = [(ref.logical_id.root, ref.version_id.root) for ref in self.visible_subject_refs]
        if len(set(subjects)) != len(subjects):
            raise ValueError("visible_subject_refs must be unique")
        if any(not ref.logical_id.root.startswith("entity:") for ref in self.visible_subject_refs):
            raise ValueError("visible_subject_refs must reference canonical EntityVersion")
        if self.execution_status is MotionQAExecutionStatus.EVALUATOR_ERROR:
            if (
                self.verdict is not None
                or self.findings
                or self.observed_duration_seconds is not None
                or not self.error_code
                or not self.error_message
            ):
                raise ValueError("EVALUATOR_ERROR requires error evidence and no completed verdict/findings")
            return self
        if self.error_code is not None or self.error_message is not None:
            raise ValueError("completed MotionQAResult cannot carry evaluator error fields")
        if self.verdict is None or self.verdict is GateVerdict.OPEN:
            raise ValueError("completed MotionQAResult requires a closed verdict")
        if self.observed_duration_seconds is None:
            raise ValueError("completed MotionQAResult requires observed_duration_seconds")
        dimensions = [finding.dimension for finding in self.findings]
        if len(dimensions) != len(set(dimensions)) or set(dimensions) != set(MotionQADimension):
            raise ValueError("completed MotionQAResult requires every canonical dimension exactly once")
        if any(
            finding.end_seconds > self.observed_duration_seconds + _EPSILON
            for finding in self.findings
        ):
            raise ValueError("completed Motion QA finding exceeds observed duration")
        if any(
            finding.verdict is MotionQAFindingVerdict.FAIL
            and finding.severity is MotionQASeverity.BLOCKING
            for finding in self.findings
        ) and self.verdict is not GateVerdict.FAIL:
            raise ValueError("BLOCKING FAIL must force overall FAIL")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.qa_result_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="shot_ir", source=self.shot_ir_ref),
            SourceVersionBinding(role="motion_delta_spec", source=self.motion_delta_spec_ref),
            SourceVersionBinding(role="full_shot_spec", source=self.full_shot_spec_ref),
            SourceVersionBinding(role="static_keyframe_spec", source=self.static_keyframe_spec_ref),
            SourceVersionBinding(role="state_snapshot", source=self.state_snapshot_ref),
            SourceVersionBinding(role="approved_state_designation", source=self.approved_state_designation_ref),
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"reference_asset_{index:03d}", source=ref)
            for index, ref in enumerate(self.reference_asset_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"visible_subject_{index:03d}", source=ref)
            for index, ref in enumerate(self.visible_subject_refs)
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


class MotionQAArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: MotionQAResult

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


class MotionQAExecutionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact: MotionQAArtifact
    job: GenerationJob


def motion_qa_result_logical_id(project_id: LogicalId, generation_job_id: LogicalId) -> LogicalId:
    raw = f"{project_id.root}\0{generation_job_id.root}".encode("utf-8")
    return LogicalId("motion-qa-result:" + hashlib.sha256(raw).hexdigest())


def decide_motion_qa_verdict(
    findings: tuple[MotionQAFinding, ...],
    policy: MotionQAPolicy,
) -> GateVerdict:
    """Apply severity policy without allowing aggregate score to mask blockers."""

    dimensions = [finding.dimension for finding in findings]
    if len(dimensions) != len(set(dimensions)) or set(dimensions) != set(MotionQADimension):
        raise MotionQAGateBlocked("cannot decide Motion QA verdict without every canonical dimension exactly once")

    failures = [finding for finding in findings if finding.verdict is MotionQAFindingVerdict.FAIL]
    if any(finding.severity is MotionQASeverity.BLOCKING for finding in failures):
        return GateVerdict.FAIL
    high_failures = sum(finding.severity is MotionQASeverity.HIGH for finding in failures)
    if high_failures >= policy.high_fail_count_for_fail:
        return GateVerdict.FAIL
    if high_failures:
        return GateVerdict.NEEDS_HUMAN_REVIEW
    if policy.medium_fail_requires_review and any(
        finding.severity is MotionQASeverity.MEDIUM for finding in failures
    ):
        return GateVerdict.NEEDS_HUMAN_REVIEW
    if policy.not_evaluated_requires_review and any(
        finding.verdict is MotionQAFindingVerdict.NOT_EVALUATED for finding in findings
    ):
        return GateVerdict.NEEDS_HUMAN_REVIEW
    if failures or any(finding.verdict is MotionQAFindingVerdict.WARN for finding in findings):
        return GateVerdict.WARN
    return GateVerdict.PASS


class MotionQAService:
    """Coordinates exact motion inputs, video evaluator execution and QA evidence."""

    def __init__(self, writer, artifact_root: Path) -> None:
        self.writer = writer
        self.jobs = GenerationJobRepository(writer)
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)
        self.artifact_evidence = ArtifactEvidenceRepository(writer)
        self.artifacts = ArtifactLifecycleService(writer, artifact_root)

    async def evaluate(
        self,
        request: MotionQAExecutionRequest,
        evaluator: MotionQAEvaluator,
    ) -> MotionQAExecutionResult:
        job = await self.jobs.get_job(request.generation_job_id)
        if job is None:
            raise MotionQAGateBlocked("GenerationJob does not exist")
        if job.artifact_state is not ArtifactState.READY:
            raise MotionQAGateBlocked("Motion QA requires artifact READY; provider success alone is insufficient")

        motion = await self._load_exact(
            request.motion_delta_spec_ref,
            MotionDeltaSpec,
            "motion-delta-spec:",
            "MotionDeltaSpec",
        )
        if motion.project_id != job.project_id:
            raise MotionQAGateBlocked("MotionDeltaSpec belongs to a different project")
        full = await self._load_exact(
            motion.full_shot_spec_ref,
            FullShotSpec,
            "full-shot-spec:",
            "FullShotSpec",
        )
        static = await self._load_exact(
            motion.static_keyframe_spec_ref,
            StaticKeyframeSpec,
            "static-keyframe-spec:",
            "StaticKeyframeSpec",
        )
        if (
            full.project_id != job.project_id
            or static.project_id != job.project_id
            or full.shot_ref != motion.shot_ref
            or static.shot_ref != motion.shot_ref
            or static.full_shot_spec_ref != full.ref
            or motion.duration_seconds != full.duration_seconds
        ):
            raise MotionQAGateBlocked("MotionDeltaSpec/FullShotSpec/StaticKeyframeSpec lineage mismatch")
        if (
            static.state_snapshot_ref != full.state_snapshot_ref
            or static.approved_state_designation_ref != full.approved_state_designation_ref
        ):
            raise MotionQAGateBlocked("static/full shot state authority mismatch")
        state = await self._load_exact(
            full.state_snapshot_ref,
            StateSnapshot,
            "state-snapshot:",
            "StateSnapshot",
        )
        await self._assert_exact_current_accepted(
            full.approved_state_designation_ref,
            "ApprovedEndStateDesignation",
        )

        references: list[ReferenceAsset] = []
        for ref in static.reference_asset_refs:
            references.append(
                await self._load_exact(ref, ReferenceAsset, "reference-asset:", "ReferenceAsset")
            )

        shot_ir = await self._load_exact(job.shot_ir_ref, ShotIR, "shot-ir:", "ShotIR")
        if shot_ir.project_id != job.project_id:
            raise MotionQAGateBlocked("ShotIR belongs to a different project")
        if (
            shot_ir.shot_ref != motion.shot_ref
            or shot_ir.full_shot_spec_ref != full.ref
            or shot_ir.static_keyframe_spec_ref != static.ref
            or shot_ir.motion_delta_spec_ref != motion.ref
            or shot_ir.state_snapshot_ref != full.state_snapshot_ref
            or shot_ir.approved_state_designation_ref != full.approved_state_designation_ref
            or shot_ir.active_profile_ref != full.active_profile_ref
        ):
            raise MotionQAGateBlocked("ShotIR exact lineage does not match Motion QA canonical inputs")
        static_reference_refs = tuple(
            sorted(
                static.reference_asset_refs,
                key=lambda ref: (ref.logical_id.root, ref.version_id.root),
            )
        )
        shot_ir_reference_refs = tuple(binding.asset_ref for binding in shot_ir.reference_bindings)
        if shot_ir_reference_refs != static_reference_refs:
            raise MotionQAGateBlocked("ShotIR ReferenceAsset bindings do not match StaticKeyframeSpec")
        await self._assert_all_sources_current(
            shot_ir.source_bindings()
            + motion.source_bindings()
            + static.source_bindings()
            + full.source_bindings()
        )

        identity = await self.artifact_evidence.get_identity_for_job(job.generation_job_id)
        if identity is None:
            raise MotionQAGateBlocked("READY GenerationJob lacks canonical artifact identity")
        event = await self._ready_materialization_event(job)
        assert event.final_relative_path is not None
        assert event.content_sha256 is not None
        assert event.byte_count is not None
        assert event.media_type is not None
        if not event.media_type.lower().startswith("video/"):
            raise MotionQAGateBlocked("Motion QA requires READY video/* artifact evidence")
        artifact_path = self.artifacts.absolute_path(event.final_relative_path)
        if not artifact_path.is_file():
            raise MotionQAGateBlocked("READY video artifact bytes are missing before Motion QA")
        data = artifact_path.read_bytes()
        observed_hash = "sha256:" + hashlib.sha256(data).hexdigest()
        if observed_hash != event.content_sha256 or len(data) != event.byte_count:
            raise MotionQAGateBlocked("READY video bytes no longer match immutable materialization evidence")
        if event.expected_input_fingerprint != job.expected_input_fingerprint:
            raise MotionQAGateBlocked("video materialization evidence is stale for current GenerationJob input")

        evaluator_id = str(getattr(evaluator, "evaluator_id", "")).strip()
        evaluator_version = str(getattr(evaluator, "evaluator_version", "")).strip()
        if not evaluator_id or not evaluator_version:
            raise MotionQAGateBlocked("Motion QA evaluator must declare non-empty evaluator_id and evaluator_version")

        job = await self._enter_qa(job, request)
        subject = MotionQAEvaluatorSubject(
            artifact_path=artifact_path,
            artifact_id=identity.artifact_id,
            artifact_event_id=event.artifact_event_id,
            content_sha256=event.content_sha256,
            byte_count=event.byte_count,
            media_type=event.media_type,
            generation_job_id=job.generation_job_id,
            shot_ir=shot_ir,
            motion_delta_spec=motion,
            full_shot_spec=full,
            static_keyframe_spec=static,
            state_snapshot=state,
            reference_assets=tuple(references),
            visible_subject_refs=static.visible_subject_refs,
        )
        allowed_refs = {
            (binding.source.logical_id.root, binding.source.version_id.root)
            for binding in (
                self._result_source_bindings(job, motion, full, static, shot_ir)
                + shot_ir.source_bindings()
                + motion.source_bindings()
                + static.source_bindings()
                + full.source_bindings()
            )
        }

        try:
            response = await evaluator.evaluate(subject)
            if (
                response.evaluator_id != evaluator_id
                or response.evaluator_version != evaluator_version
            ):
                raise MotionQAGateBlocked(
                    "evaluator response identity/version does not match evaluator port"
                )
            for finding in response.findings:
                for ref in finding.source_refs:
                    if (ref.logical_id.root, ref.version_id.root) not in allowed_refs:
                        raise MotionQAGateBlocked(
                            "evaluator finding cites a source version outside exact Motion QA inputs"
                        )
            verdict = decide_motion_qa_verdict(response.findings, request.policy)
            value = self._completed_result(
                request,
                job,
                identity.artifact_id,
                event,
                motion,
                full,
                static,
                shot_ir,
                response,
                verdict,
            )
        except Exception as exc:
            value = self._error_result(
                request,
                job,
                identity.artifact_id,
                event,
                motion,
                full,
                static,
                shot_ir,
                evaluator_id,
                evaluator_version,
                exc,
            )
            artifact = await self._persist_result(value, request)
            current = await self.jobs.get_job(job.generation_job_id)
            assert current is not None
            if current.creative_state is CreativeState.QA_RUNNING:
                current = (
                    await self.jobs.transition(
                        job_id=current.generation_job_id,
                        axis=GenerationJobAxis.CREATIVE,
                        command="EVALUATOR_ERROR",
                        owner=TransitionOwner.QA_SUBSYSTEM,
                        guard_evidence=self._guard(
                            "Motion QA evaluator failed",
                            request.evidence_refs + (event.artifact_event_id,),
                            evaluator_failed=True,
                        ),
                        expected_revision=current.revision,
                        actor_ref=request.actor_ref,
                        reason=f"Motion QA evaluator failure: {type(exc).__name__}",
                        correlation_id=request.correlation_id,
                        recorded_at=request.recorded_at,
                    )
                ).job
            return MotionQAExecutionResult(artifact=artifact, job=current)

        artifact = await self._persist_result(value, request)
        current = await self.jobs.get_job(job.generation_job_id)
        assert current is not None
        if current.creative_state is not CreativeState.QA_RUNNING:
            raise MotionQAGateBlocked("Motion QA result can close only a QA_RUNNING creative state")

        if verdict is GateVerdict.FAIL:
            command = "ARTIFACT_QA_FAILED"
            reason = "Motion QA found blocking video/artifact defects"
        elif verdict in {GateVerdict.NEEDS_HUMAN_REVIEW, GateVerdict.WARN} or not request.policy.auto_approve_pass:
            command = "REVIEW_REQUIRED"
            reason = "Motion QA requires human review under current policy"
        else:
            command = "QA_PASS_AND_AUTO_APPROVE"
            reason = "Motion QA PASS under explicit auto-approval policy"

        current = (
            await self.jobs.transition(
                job_id=current.generation_job_id,
                axis=GenerationJobAxis.CREATIVE,
                command=command,
                owner=TransitionOwner.QA_SUBSYSTEM,
                guard_evidence=self._guard(
                    "Motion QA closed verdict",
                    request.evidence_refs + (event.artifact_event_id, artifact.ref.logical_id.root),
                    qa_result_bound=True,
                    blocking_fail=(verdict is GateVerdict.FAIL),
                ),
                expected_revision=current.revision,
                actor_ref=request.actor_ref,
                reason=reason,
                correlation_id=request.correlation_id,
                recorded_at=request.recorded_at,
            )
        ).job

        if command == "QA_PASS_AND_AUTO_APPROVE":
            pointer = await self.versions.get_current(artifact.ref.logical_id)
            if pointer is None or pointer.version_id != artifact.ref.version_id:
                raise MotionQAIdentityError("persisted Motion QA result lost current-pointer authority")
            await self.versions.update_current(
                logical_id=artifact.ref.logical_id,
                version_id=artifact.ref.version_id,
                status=LifecycleState.APPROVED,
                expected_revision=pointer.revision,
            )
        return MotionQAExecutionResult(artifact=artifact, job=current)

    async def get_result(self, ref: VersionRef) -> MotionQAArtifact | None:
        if not ref.logical_id.root.startswith("motion-qa-result:"):
            raise MotionQAIdentityError("expected motion-qa-result reference")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = MotionQAResult.model_validate(stored.payload)
        if value.ref != ref:
            raise MotionQAIdentityError("stored MotionQAResult identity mismatch")
        return MotionQAArtifact(metadata=stored.metadata, value=value)

    async def _enter_qa(self, job: GenerationJob, request: MotionQAExecutionRequest) -> GenerationJob:
        evidence = request.evidence_refs
        current = job
        if current.creative_state is CreativeState.QA_ERROR:
            current = (
                await self.jobs.transition(
                    job_id=current.generation_job_id,
                    axis=GenerationJobAxis.CREATIVE,
                    command="RETRY_EVALUATOR",
                    owner=TransitionOwner.QA_ORCHESTRATOR,
                    guard_evidence=self._guard("retry Motion QA evaluator", evidence, retry_authorized=True),
                    expected_revision=current.revision,
                    actor_ref=request.actor_ref,
                    reason="retry Motion QA evaluator after QA_ERROR",
                    correlation_id=request.correlation_id,
                    recorded_at=request.recorded_at,
                )
            ).job
        if current.creative_state is CreativeState.NOT_APPLICABLE:
            current = (
                await self.jobs.transition(
                    job_id=current.generation_job_id,
                    axis=GenerationJobAxis.CREATIVE,
                    command="QUEUE_QA",
                    owner=TransitionOwner.QA_ORCHESTRATOR,
                    guard_evidence=self._guard("queue Motion QA", evidence, artifact_ready=True),
                    expected_revision=current.revision,
                    actor_ref=request.actor_ref,
                    reason="queue READY video artifact for Motion QA",
                    correlation_id=request.correlation_id,
                    recorded_at=request.recorded_at,
                )
            ).job
        if current.creative_state is CreativeState.PENDING_QA:
            current = (
                await self.jobs.transition(
                    job_id=current.generation_job_id,
                    axis=GenerationJobAxis.CREATIVE,
                    command="START_QA",
                    owner=TransitionOwner.QA_ORCHESTRATOR,
                    guard_evidence=self._guard("start Motion QA", evidence, artifact_ready=True),
                    expected_revision=current.revision,
                    actor_ref=request.actor_ref,
                    reason="start Motion QA evaluation",
                    correlation_id=request.correlation_id,
                    recorded_at=request.recorded_at,
                )
            ).job
        if current.creative_state is not CreativeState.QA_RUNNING:
            raise MotionQAGateBlocked(
                f"Motion QA cannot run from creative state {current.creative_state.value}"
            )
        return current

    async def _persist_result(
        self,
        value: MotionQAResult,
        request: MotionQAExecutionRequest,
    ) -> MotionQAArtifact:
        finding_evidence_refs = tuple(
            evidence_ref
            for finding in value.findings
            for evidence_ref in finding.evidence_refs
        )
        source_refs = tuple(
            dict.fromkeys(
                (
                    value.artifact_id.root,
                    value.artifact_event_id,
                    value.artifact_content_sha256,
                    f"evaluator:{value.evaluator_id}@{value.evaluator_version}",
                    f"policy:{value.policy_version}",
                    *request.evidence_refs,
                    *finding_evidence_refs,
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
            materialized = MotionQAArtifact(
                metadata=existing.metadata,
                value=MotionQAResult.model_validate(existing.payload),
            )
            if materialized.value != value or materialized.metadata.provenance != provenance:
                raise MotionQAIdentityError("MotionQAResult exact replay conflicts with persisted evidence")
            return materialized

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
        artifact = MotionQAArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(artifact)
        return artifact

    async def _register_dependencies(self, artifact: MotionQAArtifact) -> None:
        seen: set[tuple[str, str]] = set()
        for binding in artifact.value.source_bindings():
            key = (binding.source.logical_id.root, binding.source.version_id.root)
            if key in seen:
                continue
            seen.add(key)
            await self.graph.create_edge(
                source=binding.source,
                dependent=artifact.ref,
                edge_type="motion_qa_source",
                dependency_reason=f"motion_qa_source:{binding.role}",
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _load_exact(self, ref: VersionRef, model, prefix: str, label: str):
        if not ref.logical_id.root.startswith(prefix):
            raise MotionQAGateBlocked(f"{label} reference has wrong canonical identity")
        await self._assert_exact_current_accepted(ref, label)
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise MotionQAGateBlocked(f"{label} exact version does not exist")
        return model.model_validate(stored.payload)

    async def _assert_exact_current_accepted(self, ref: VersionRef, label: str) -> None:
        pointer = await self.versions.get_current(ref.logical_id)
        if pointer is None or pointer.version_id != ref.version_id or pointer.status not in _ACCEPTED:
            raise MotionQAGateBlocked(f"{label} is not exact current accepted authority")
        for record in await self.invalidations.list_unresolved():
            if record.affected_object_id == ref.logical_id and record.affected_object_version == ref.version_id:
                raise MotionQAGateBlocked(f"{label} has unresolved durable invalidation")

    async def _assert_all_sources_current(self, bindings: tuple[SourceVersionBinding, ...]) -> None:
        seen: set[tuple[str, str]] = set()
        for binding in bindings:
            key = (binding.source.logical_id.root, binding.source.version_id.root)
            if key in seen:
                continue
            seen.add(key)
            await self._assert_exact_current_accepted(binding.source, binding.role)

    async def _ready_materialization_event(self, job: GenerationJob) -> ArtifactEvent:
        events = await self.artifact_evidence.list_events_for_job(job.generation_job_id)
        valid = [event for event in events if event.event_kind is ArtifactEventKind.MATERIALIZE_VALID]
        if not valid:
            raise MotionQAGateBlocked("READY GenerationJob lacks MATERIALIZE_VALID evidence")
        event = max(valid, key=lambda item: (item.attempt, item.created_at, item.artifact_event_id))
        if (
            event.final_relative_path is None
            or event.content_sha256 is None
            or event.byte_count is None
            or event.media_type is None
        ):
            raise MotionQAGateBlocked("MATERIALIZE_VALID evidence is incomplete")
        return event

    def _completed_result(
        self,
        request: MotionQAExecutionRequest,
        job: GenerationJob,
        artifact_id: LogicalId,
        event: ArtifactEvent,
        motion: MotionDeltaSpec,
        full: FullShotSpec,
        static: StaticKeyframeSpec,
        shot_ir: ShotIR,
        response: MotionQAEvaluatorResponse,
        verdict: GateVerdict,
    ) -> MotionQAResult:
        assert event.content_sha256 is not None and event.byte_count is not None and event.media_type is not None
        return MotionQAResult(
            project_id=job.project_id,
            qa_result_id=motion_qa_result_logical_id(job.project_id, job.generation_job_id),
            version_id=request.result_version_id,
            generation_job_id=job.generation_job_id,
            artifact_id=artifact_id,
            artifact_event_id=event.artifact_event_id,
            artifact_content_sha256=event.content_sha256,
            artifact_byte_count=event.byte_count,
            media_type=event.media_type,
            shot_ir_ref=job.shot_ir_ref,
            motion_delta_spec_ref=motion.ref,
            full_shot_spec_ref=full.ref,
            static_keyframe_spec_ref=static.ref,
            state_snapshot_ref=full.state_snapshot_ref,
            approved_state_designation_ref=full.approved_state_designation_ref,
            active_profile_ref=shot_ir.active_profile_ref,
            reference_asset_refs=static.reference_asset_refs,
            visible_subject_refs=static.visible_subject_refs,
            expected_duration_seconds=motion.duration_seconds,
            observed_duration_seconds=response.observed_duration_seconds,
            evaluator_id=response.evaluator_id,
            evaluator_version=response.evaluator_version,
            policy_version=request.policy.policy_version,
            execution_status=MotionQAExecutionStatus.COMPLETED,
            findings=response.findings,
            aggregate_score=response.aggregate_score,
            verdict=verdict,
            evaluated_at=request.recorded_at,
        )

    def _error_result(
        self,
        request: MotionQAExecutionRequest,
        job: GenerationJob,
        artifact_id: LogicalId,
        event: ArtifactEvent,
        motion: MotionDeltaSpec,
        full: FullShotSpec,
        static: StaticKeyframeSpec,
        shot_ir: ShotIR,
        evaluator_id: str,
        evaluator_version: str,
        exc: Exception,
    ) -> MotionQAResult:
        assert event.content_sha256 is not None and event.byte_count is not None and event.media_type is not None
        return MotionQAResult(
            project_id=job.project_id,
            qa_result_id=motion_qa_result_logical_id(job.project_id, job.generation_job_id),
            version_id=request.result_version_id,
            generation_job_id=job.generation_job_id,
            artifact_id=artifact_id,
            artifact_event_id=event.artifact_event_id,
            artifact_content_sha256=event.content_sha256,
            artifact_byte_count=event.byte_count,
            media_type=event.media_type,
            shot_ir_ref=job.shot_ir_ref,
            motion_delta_spec_ref=motion.ref,
            full_shot_spec_ref=full.ref,
            static_keyframe_spec_ref=static.ref,
            state_snapshot_ref=full.state_snapshot_ref,
            approved_state_designation_ref=full.approved_state_designation_ref,
            active_profile_ref=shot_ir.active_profile_ref,
            reference_asset_refs=static.reference_asset_refs,
            visible_subject_refs=static.visible_subject_refs,
            expected_duration_seconds=motion.duration_seconds,
            evaluator_id=evaluator_id,
            evaluator_version=evaluator_version,
            policy_version=request.policy.policy_version,
            execution_status=MotionQAExecutionStatus.EVALUATOR_ERROR,
            error_code=type(exc).__name__,
            error_message=str(exc) or type(exc).__name__,
            evaluated_at=request.recorded_at,
        )

    def _result_source_bindings(
        self,
        job: GenerationJob,
        motion: MotionDeltaSpec,
        full: FullShotSpec,
        static: StaticKeyframeSpec,
        shot_ir: ShotIR,
    ) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="shot_ir", source=job.shot_ir_ref),
            SourceVersionBinding(role="motion_delta_spec", source=motion.ref),
            SourceVersionBinding(role="full_shot_spec", source=full.ref),
            SourceVersionBinding(role="static_keyframe_spec", source=static.ref),
            SourceVersionBinding(role="state_snapshot", source=full.state_snapshot_ref),
            SourceVersionBinding(
                role="approved_state_designation",
                source=full.approved_state_designation_ref,
            ),
            SourceVersionBinding(
                role="active_production_profile",
                source=shot_ir.active_profile_ref,
            ),
        ]
        values.extend(
            SourceVersionBinding(role=f"reference_asset_{index:03d}", source=ref)
            for index, ref in enumerate(static.reference_asset_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"visible_subject_{index:03d}", source=ref)
            for index, ref in enumerate(static.visible_subject_refs)
        )
        return tuple(values)

    @staticmethod
    def _guard(summary: str, evidence_refs: tuple[str, ...], **facts) -> TransitionGuardEvidence:
        refs = tuple(dict.fromkeys(str(ref) for ref in evidence_refs if str(ref).strip()))
        return TransitionGuardEvidence(
            summary=summary,
            evidence_refs=refs or ("evidence:motion-qa",),
            facts=tuple(GuardFact(key=key, value=value) for key, value in facts.items()),
        )


__all__ = [
    "MotionQAArtifact",
    "MotionQADimension",
    "MotionQAError",
    "MotionQAEvaluator",
    "MotionQAEvaluatorResponse",
    "MotionQAEvaluatorSubject",
    "MotionQAExecutionRequest",
    "MotionQAExecutionResult",
    "MotionQAExecutionStatus",
    "MotionQAFinding",
    "MotionQAFindingVerdict",
    "MotionQAGateBlocked",
    "MotionQAIdentityError",
    "MotionQAPolicy",
    "MotionQAResult",
    "MotionQAService",
    "MotionQASeverity",
    "decide_motion_qa_verdict",
    "motion_qa_result_logical_id",
]
