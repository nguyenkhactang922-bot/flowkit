"""IMP-060 provider-neutral Static QA contracts and orchestration.

Static QA evaluates actual READY artifact bytes against exact canonical
Shot/State/Reference expectations.  It owns QA evidence/verdict only: it does
not rewrite upstream truth, artifact materialization state, or provider state.
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
from .shot_realization import FullShotSpec, StaticKeyframeSpec
from .state_continuity import StateSnapshot
from .versioning import VersionRepository


_ACCEPTED = {LifecycleState.APPROVED, LifecycleState.LOCKED}
_HASH_PREFIX = "sha256:"


class StaticQAError(RuntimeError):
    """Base Static QA error."""


class StaticQAGateBlocked(StaticQAError):
    """Raised when exact-version/artifact prerequisites are not safe for QA."""


class StaticQAIdentityError(StaticQAError):
    """Raised when persisted QA identity/evidence conflicts."""


class StaticQADimension(str, Enum):
    TECHNICAL_INTEGRITY = "TECHNICAL_INTEGRITY"
    IDENTITY = "IDENTITY"
    STATE_WARDROBE = "STATE_WARDROBE"
    PROPS_ASSETS = "PROPS_ASSETS"
    ENVIRONMENT = "ENVIRONMENT"
    ACTION_PERFORMANCE = "ACTION_PERFORMANCE"
    CAMERA_COMPOSITION = "CAMERA_COMPOSITION"
    LIGHTING_STYLE = "LIGHTING_STYLE"
    CONTINUITY = "CONTINUITY"
    NARRATIVE_INTENT = "NARRATIVE_INTENT"


class StaticQAFindingVerdict(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_EVALUATED = "NOT_EVALUATED"


class StaticQASeverity(str, Enum):
    BLOCKING = "BLOCKING"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    COSMETIC = "COSMETIC"


class StaticQAExecutionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    EVALUATOR_ERROR = "EVALUATOR_ERROR"


class StaticQAPolicy(BaseModel):
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


class StaticQAFinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dimension: StaticQADimension
    verdict: StaticQAFindingVerdict
    severity: StaticQASeverity
    confidence: float = Field(ge=0.0, le=1.0)
    reason_code: str
    explanation: str
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


class StaticQAEvaluatorResponse(BaseModel):
    """Provider-neutral evaluator output before policy application."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_id: str
    evaluator_version: str
    findings: tuple[StaticQAFinding, ...]
    aggregate_score: float | None = Field(default=None, ge=0.0, le=100.0)

    @field_validator("evaluator_id", "evaluator_version")
    @classmethod
    def validate_identity(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{info.field_name} must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_dimensions(self) -> "StaticQAEvaluatorResponse":
        dimensions = [finding.dimension for finding in self.findings]
        if len(dimensions) != len(set(dimensions)) or set(dimensions) != set(StaticQADimension):
            raise ValueError("Static QA evaluator must return exactly one finding for every canonical dimension")
        return self


class StaticQAEvaluatorSubject(BaseModel):
    """Runtime-only evaluator subject; absolute path is never persisted as canonical truth."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    artifact_path: Path
    artifact_id: LogicalId
    artifact_event_id: str
    content_sha256: str
    byte_count: int = Field(ge=0)
    media_type: str
    generation_job_id: LogicalId
    shot_ir: ShotIR
    static_keyframe_spec: StaticKeyframeSpec
    full_shot_spec: FullShotSpec
    state_snapshot: StateSnapshot
    reference_assets: tuple[ReferenceAsset, ...]


class StaticQAEvaluator(Protocol):
    evaluator_id: str
    evaluator_version: str

    async def evaluate(self, subject: StaticQAEvaluatorSubject) -> StaticQAEvaluatorResponse:
        """Inspect actual artifact bytes and return dimension-scoped findings."""


class StaticQAExecutionRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    generation_job_id: LogicalId
    static_keyframe_spec_ref: VersionRef
    result_version_id: VersionId
    policy: StaticQAPolicy
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


class StaticQAResult(BaseModel):
    """Immutable QA evidence bound to exact artifact bytes and expectations."""

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
    static_keyframe_spec_ref: VersionRef
    full_shot_spec_ref: VersionRef
    state_snapshot_ref: VersionRef
    approved_state_designation_ref: VersionRef
    active_profile_ref: VersionRef
    reference_asset_refs: tuple[VersionRef, ...] = ()
    evaluator_id: str
    evaluator_version: str
    policy_version: str
    execution_status: StaticQAExecutionStatus
    findings: tuple[StaticQAFinding, ...] = ()
    aggregate_score: float | None = Field(default=None, ge=0.0, le=100.0)
    verdict: GateVerdict | None = None
    error_code: str | None = None
    error_message: str | None = None
    evaluated_at: AwareDatetime

    @model_validator(mode="after")
    def validate_result(self) -> "StaticQAResult":
        expected = static_qa_result_logical_id(self.project_id, self.generation_job_id)
        if self.qa_result_id != expected:
            raise ValueError(f"qa_result_id must be {expected.root}")
        if not self.artifact_content_sha256.startswith(_HASH_PREFIX):
            raise ValueError("artifact_content_sha256 must be sha256-prefixed")
        refs = [(ref.logical_id.root, ref.version_id.root) for ref in self.reference_asset_refs]
        if len(set(refs)) != len(refs):
            raise ValueError("reference_asset_refs must be unique")
        if self.execution_status is StaticQAExecutionStatus.EVALUATOR_ERROR:
            if self.verdict is not None or self.findings or not self.error_code or not self.error_message:
                raise ValueError("EVALUATOR_ERROR requires error evidence and no completed verdict/findings")
            return self
        if self.error_code is not None or self.error_message is not None:
            raise ValueError("completed StaticQAResult cannot carry evaluator error fields")
        if self.verdict is None or self.verdict is GateVerdict.OPEN:
            raise ValueError("completed StaticQAResult requires a closed verdict")
        dimensions = [finding.dimension for finding in self.findings]
        if len(dimensions) != len(set(dimensions)) or set(dimensions) != set(StaticQADimension):
            raise ValueError("completed StaticQAResult requires every canonical dimension exactly once")
        if any(
            finding.verdict is StaticQAFindingVerdict.FAIL
            and finding.severity is StaticQASeverity.BLOCKING
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
            SourceVersionBinding(role="static_keyframe_spec", source=self.static_keyframe_spec_ref),
            SourceVersionBinding(role="full_shot_spec", source=self.full_shot_spec_ref),
            SourceVersionBinding(role="state_snapshot", source=self.state_snapshot_ref),
            SourceVersionBinding(role="approved_state_designation", source=self.approved_state_designation_ref),
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"reference_asset_{index:03d}", source=ref)
            for index, ref in enumerate(self.reference_asset_refs)
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


class StaticQAArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: StaticQAResult

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


class StaticQAExecutionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact: StaticQAArtifact
    job: GenerationJob


def static_qa_result_logical_id(project_id: LogicalId, generation_job_id: LogicalId) -> LogicalId:
    raw = f"{project_id.root}\0{generation_job_id.root}".encode("utf-8")
    return LogicalId("qa-result:" + hashlib.sha256(raw).hexdigest())


def decide_static_qa_verdict(
    findings: tuple[StaticQAFinding, ...],
    policy: StaticQAPolicy,
) -> GateVerdict:
    """Apply severity policy without allowing aggregate score to mask blockers."""

    dimensions = [finding.dimension for finding in findings]
    if len(dimensions) != len(set(dimensions)) or set(dimensions) != set(StaticQADimension):
        raise StaticQAGateBlocked("cannot decide QA verdict without every canonical dimension exactly once")

    failures = [finding for finding in findings if finding.verdict is StaticQAFindingVerdict.FAIL]
    if any(finding.severity is StaticQASeverity.BLOCKING for finding in failures):
        return GateVerdict.FAIL
    high_failures = sum(finding.severity is StaticQASeverity.HIGH for finding in failures)
    if high_failures >= policy.high_fail_count_for_fail:
        return GateVerdict.FAIL
    if high_failures:
        return GateVerdict.NEEDS_HUMAN_REVIEW
    if policy.medium_fail_requires_review and any(
        finding.severity is StaticQASeverity.MEDIUM for finding in failures
    ):
        return GateVerdict.NEEDS_HUMAN_REVIEW
    if policy.not_evaluated_requires_review and any(
        finding.verdict is StaticQAFindingVerdict.NOT_EVALUATED for finding in findings
    ):
        return GateVerdict.NEEDS_HUMAN_REVIEW
    if failures or any(finding.verdict is StaticQAFindingVerdict.WARN for finding in findings):
        return GateVerdict.WARN
    return GateVerdict.PASS


class StaticQAService:
    """Coordinates exact inputs, evaluator execution, QA evidence and creative state."""

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
        request: StaticQAExecutionRequest,
        evaluator: StaticQAEvaluator,
    ) -> StaticQAExecutionResult:
        job = await self.jobs.get_job(request.generation_job_id)
        if job is None:
            raise StaticQAGateBlocked("GenerationJob does not exist")
        if job.artifact_state is not ArtifactState.READY:
            raise StaticQAGateBlocked("Static QA requires artifact READY")

        static = await self._load_exact(
            request.static_keyframe_spec_ref,
            StaticKeyframeSpec,
            "static-keyframe-spec:",
            "StaticKeyframeSpec",
        )
        if static.project_id != job.project_id:
            raise StaticQAGateBlocked("StaticKeyframeSpec belongs to a different project")
        full = await self._load_exact(
            static.full_shot_spec_ref,
            FullShotSpec,
            "full-shot-spec:",
            "FullShotSpec",
        )
        if full.project_id != job.project_id or full.shot_ref != static.shot_ref:
            raise StaticQAGateBlocked("FullShotSpec does not match StaticKeyframeSpec shot authority")
        if full.state_snapshot_ref != static.state_snapshot_ref:
            raise StaticQAGateBlocked("StaticKeyframeSpec/FullShotSpec state binding mismatch")
        state = await self._load_exact(
            static.state_snapshot_ref,
            StateSnapshot,
            "state-snapshot:",
            "StateSnapshot",
        )
        await self._assert_exact_current_accepted(
            static.approved_state_designation_ref,
            "ApprovedEndStateDesignation",
        )
        references: list[ReferenceAsset] = []
        for ref in static.reference_asset_refs:
            references.append(
                await self._load_exact(ref, ReferenceAsset, "reference-asset:", "ReferenceAsset")
            )
        shot_ir = await self._load_exact(job.shot_ir_ref, ShotIR, "shot-ir:", "ShotIR")
        if shot_ir.project_id != job.project_id:
            raise StaticQAGateBlocked("ShotIR belongs to a different project")
        if (
            shot_ir.shot_ref != static.shot_ref
            or shot_ir.full_shot_spec_ref != full.ref
            or shot_ir.static_keyframe_spec_ref != static.ref
            or shot_ir.state_snapshot_ref != static.state_snapshot_ref
            or shot_ir.approved_state_designation_ref != static.approved_state_designation_ref
            or shot_ir.active_profile_ref != full.active_profile_ref
        ):
            raise StaticQAGateBlocked("ShotIR exact lineage does not match Static QA canonical inputs")
        static_reference_refs = tuple(
            sorted(
                static.reference_asset_refs,
                key=lambda ref: (ref.logical_id.root, ref.version_id.root),
            )
        )
        shot_ir_reference_refs = tuple(binding.asset_ref for binding in shot_ir.reference_bindings)
        if shot_ir_reference_refs != static_reference_refs:
            raise StaticQAGateBlocked("ShotIR ReferenceAsset bindings do not match StaticKeyframeSpec")
        await self._assert_all_sources_current(
            shot_ir.source_bindings() + static.source_bindings() + full.source_bindings()
        )

        identity = await self.artifact_evidence.get_identity_for_job(job.generation_job_id)
        if identity is None:
            raise StaticQAGateBlocked("READY GenerationJob lacks canonical artifact identity")
        event = await self._ready_materialization_event(job)
        assert event.final_relative_path is not None
        assert event.content_sha256 is not None
        assert event.byte_count is not None
        assert event.media_type is not None
        artifact_path = self.artifacts.absolute_path(event.final_relative_path)
        if not artifact_path.is_file():
            raise StaticQAGateBlocked("READY artifact bytes are missing before Static QA")
        data = artifact_path.read_bytes()
        observed_hash = "sha256:" + hashlib.sha256(data).hexdigest()
        if observed_hash != event.content_sha256 or len(data) != event.byte_count:
            raise StaticQAGateBlocked("READY artifact bytes no longer match immutable materialization evidence")
        if event.expected_input_fingerprint != job.expected_input_fingerprint:
            raise StaticQAGateBlocked("artifact materialization evidence is stale for current GenerationJob input")

        evaluator_id = str(getattr(evaluator, "evaluator_id", "")).strip()
        evaluator_version = str(getattr(evaluator, "evaluator_version", "")).strip()
        if not evaluator_id or not evaluator_version:
            raise StaticQAGateBlocked("Static QA evaluator must declare non-empty evaluator_id and evaluator_version")

        job = await self._enter_qa(job, request)
        subject = StaticQAEvaluatorSubject(
            artifact_path=artifact_path,
            artifact_id=identity.artifact_id,
            artifact_event_id=event.artifact_event_id,
            content_sha256=event.content_sha256,
            byte_count=event.byte_count,
            media_type=event.media_type,
            generation_job_id=job.generation_job_id,
            shot_ir=shot_ir,
            static_keyframe_spec=static,
            full_shot_spec=full,
            state_snapshot=state,
            reference_assets=tuple(references),
        )
        allowed_refs = {
            (binding.source.logical_id.root, binding.source.version_id.root)
            for binding in (
                self._result_source_bindings(job, static, shot_ir)
                + shot_ir.source_bindings()
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
                raise StaticQAGateBlocked(
                    "evaluator response identity/version does not match evaluator port"
                )
            for finding in response.findings:
                for ref in finding.source_refs:
                    if (ref.logical_id.root, ref.version_id.root) not in allowed_refs:
                        raise StaticQAGateBlocked(
                            "evaluator finding cites a source version outside exact Static QA inputs"
                        )
            verdict = decide_static_qa_verdict(response.findings, request.policy)
            value = self._completed_result(
                request,
                job,
                identity.artifact_id,
                event,
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
                            "Static QA evaluator failed",
                            request.evidence_refs + (event.artifact_event_id,),
                            evaluator_failed=True,
                        ),
                        expected_revision=current.revision,
                        actor_ref=request.actor_ref,
                        reason=f"Static QA evaluator failure: {type(exc).__name__}",
                        correlation_id=request.correlation_id,
                        recorded_at=request.recorded_at,
                    )
                ).job
            return StaticQAExecutionResult(artifact=artifact, job=current)

        artifact = await self._persist_result(value, request)
        current = await self.jobs.get_job(job.generation_job_id)
        assert current is not None
        if current.creative_state is not CreativeState.QA_RUNNING:
            raise StaticQAGateBlocked("Static QA result can close only a QA_RUNNING creative state")

        if verdict is GateVerdict.FAIL:
            command = "ARTIFACT_QA_FAILED"
            reason = "Static QA found blocking/artifact defects"
        elif verdict in {GateVerdict.NEEDS_HUMAN_REVIEW, GateVerdict.WARN} or not request.policy.auto_approve_pass:
            command = "REVIEW_REQUIRED"
            reason = "Static QA requires human review under current policy"
        else:
            command = "QA_PASS_AND_AUTO_APPROVE"
            reason = "Static QA PASS under explicit auto-approval policy"

        current = (
            await self.jobs.transition(
                job_id=current.generation_job_id,
                axis=GenerationJobAxis.CREATIVE,
                command=command,
                owner=TransitionOwner.QA_SUBSYSTEM,
                guard_evidence=self._guard(
                    "Static QA closed verdict",
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
                raise StaticQAIdentityError("persisted QA result lost current-pointer authority")
            await self.versions.update_current(
                logical_id=artifact.ref.logical_id,
                version_id=artifact.ref.version_id,
                status=LifecycleState.APPROVED,
                expected_revision=pointer.revision,
            )
        return StaticQAExecutionResult(artifact=artifact, job=current)

    async def get_result(self, ref: VersionRef) -> StaticQAArtifact | None:
        if not ref.logical_id.root.startswith("qa-result:"):
            raise StaticQAIdentityError("expected qa-result reference")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = StaticQAResult.model_validate(stored.payload)
        if value.ref != ref:
            raise StaticQAIdentityError("stored StaticQAResult identity mismatch")
        return StaticQAArtifact(metadata=stored.metadata, value=value)

    async def _enter_qa(self, job: GenerationJob, request: StaticQAExecutionRequest) -> GenerationJob:
        evidence = request.evidence_refs
        current = job
        if current.creative_state is CreativeState.QA_ERROR:
            current = (
                await self.jobs.transition(
                    job_id=current.generation_job_id,
                    axis=GenerationJobAxis.CREATIVE,
                    command="RETRY_EVALUATOR",
                    owner=TransitionOwner.QA_ORCHESTRATOR,
                    guard_evidence=self._guard("retry Static QA evaluator", evidence, retry_authorized=True),
                    expected_revision=current.revision,
                    actor_ref=request.actor_ref,
                    reason="retry Static QA evaluator after QA_ERROR",
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
                    guard_evidence=self._guard("queue Static QA", evidence, artifact_ready=True),
                    expected_revision=current.revision,
                    actor_ref=request.actor_ref,
                    reason="queue READY artifact for Static QA",
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
                    guard_evidence=self._guard("start Static QA", evidence, artifact_ready=True),
                    expected_revision=current.revision,
                    actor_ref=request.actor_ref,
                    reason="start Static QA evaluation",
                    correlation_id=request.correlation_id,
                    recorded_at=request.recorded_at,
                )
            ).job
        if current.creative_state is not CreativeState.QA_RUNNING:
            raise StaticQAGateBlocked(
                f"Static QA cannot run from creative state {current.creative_state.value}"
            )
        return current

    async def _persist_result(
        self,
        value: StaticQAResult,
        request: StaticQAExecutionRequest,
    ) -> StaticQAArtifact:
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
            materialized = StaticQAArtifact(
                metadata=existing.metadata,
                value=StaticQAResult.model_validate(existing.payload),
            )
            if materialized.value != value or materialized.metadata.provenance != provenance:
                raise StaticQAIdentityError("StaticQAResult exact replay conflicts with persisted evidence")
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
        artifact = StaticQAArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(artifact)
        return artifact

    async def _register_dependencies(self, artifact: StaticQAArtifact) -> None:
        seen: set[tuple[str, str]] = set()
        for binding in artifact.value.source_bindings():
            key = (binding.source.logical_id.root, binding.source.version_id.root)
            if key in seen:
                continue
            seen.add(key)
            await self.graph.create_edge(
                source=binding.source,
                dependent=artifact.ref,
                edge_type="static_qa_source",
                dependency_reason=f"static_qa_source:{binding.role}",
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _load_exact(self, ref: VersionRef, model, prefix: str, label: str):
        if not ref.logical_id.root.startswith(prefix):
            raise StaticQAGateBlocked(f"{label} reference has wrong canonical identity")
        await self._assert_exact_current_accepted(ref, label)
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise StaticQAGateBlocked(f"{label} exact version does not exist")
        return model.model_validate(stored.payload)

    async def _assert_exact_current_accepted(self, ref: VersionRef, label: str) -> None:
        pointer = await self.versions.get_current(ref.logical_id)
        if pointer is None or pointer.version_id != ref.version_id or pointer.status not in _ACCEPTED:
            raise StaticQAGateBlocked(f"{label} is not exact current accepted authority")
        for record in await self.invalidations.list_unresolved():
            if record.affected_object_id == ref.logical_id and record.affected_object_version == ref.version_id:
                raise StaticQAGateBlocked(f"{label} has unresolved durable invalidation")

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
            raise StaticQAGateBlocked("READY GenerationJob lacks MATERIALIZE_VALID evidence")
        event = max(valid, key=lambda item: (item.attempt, item.created_at, item.artifact_event_id))
        if (
            event.final_relative_path is None
            or event.content_sha256 is None
            or event.byte_count is None
            or event.media_type is None
        ):
            raise StaticQAGateBlocked("MATERIALIZE_VALID evidence is incomplete")
        return event

    def _completed_result(
        self,
        request: StaticQAExecutionRequest,
        job: GenerationJob,
        artifact_id: LogicalId,
        event: ArtifactEvent,
        static: StaticKeyframeSpec,
        shot_ir: ShotIR,
        response: StaticQAEvaluatorResponse,
        verdict: GateVerdict,
    ) -> StaticQAResult:
        assert event.content_sha256 is not None and event.byte_count is not None and event.media_type is not None
        return StaticQAResult(
            project_id=job.project_id,
            qa_result_id=static_qa_result_logical_id(job.project_id, job.generation_job_id),
            version_id=request.result_version_id,
            generation_job_id=job.generation_job_id,
            artifact_id=artifact_id,
            artifact_event_id=event.artifact_event_id,
            artifact_content_sha256=event.content_sha256,
            artifact_byte_count=event.byte_count,
            media_type=event.media_type,
            shot_ir_ref=job.shot_ir_ref,
            static_keyframe_spec_ref=static.ref,
            full_shot_spec_ref=static.full_shot_spec_ref,
            state_snapshot_ref=static.state_snapshot_ref,
            approved_state_designation_ref=static.approved_state_designation_ref,
            active_profile_ref=shot_ir.active_profile_ref,
            reference_asset_refs=static.reference_asset_refs,
            evaluator_id=response.evaluator_id,
            evaluator_version=response.evaluator_version,
            policy_version=request.policy.policy_version,
            execution_status=StaticQAExecutionStatus.COMPLETED,
            findings=response.findings,
            aggregate_score=response.aggregate_score,
            verdict=verdict,
            evaluated_at=request.recorded_at,
        )

    def _error_result(
        self,
        request: StaticQAExecutionRequest,
        job: GenerationJob,
        artifact_id: LogicalId,
        event: ArtifactEvent,
        static: StaticKeyframeSpec,
        shot_ir: ShotIR,
        evaluator_id: str,
        evaluator_version: str,
        exc: Exception,
    ) -> StaticQAResult:
        assert event.content_sha256 is not None and event.byte_count is not None and event.media_type is not None
        return StaticQAResult(
            project_id=job.project_id,
            qa_result_id=static_qa_result_logical_id(job.project_id, job.generation_job_id),
            version_id=request.result_version_id,
            generation_job_id=job.generation_job_id,
            artifact_id=artifact_id,
            artifact_event_id=event.artifact_event_id,
            artifact_content_sha256=event.content_sha256,
            artifact_byte_count=event.byte_count,
            media_type=event.media_type,
            shot_ir_ref=job.shot_ir_ref,
            static_keyframe_spec_ref=static.ref,
            full_shot_spec_ref=static.full_shot_spec_ref,
            state_snapshot_ref=static.state_snapshot_ref,
            approved_state_designation_ref=static.approved_state_designation_ref,
            active_profile_ref=shot_ir.active_profile_ref,
            reference_asset_refs=static.reference_asset_refs,
            evaluator_id=evaluator_id,
            evaluator_version=evaluator_version,
            policy_version=request.policy.policy_version,
            execution_status=StaticQAExecutionStatus.EVALUATOR_ERROR,
            error_code=type(exc).__name__,
            error_message=str(exc) or type(exc).__name__,
            evaluated_at=request.recorded_at,
        )

    def _result_source_bindings(
        self,
        job: GenerationJob,
        static: StaticKeyframeSpec,
        shot_ir: ShotIR,
    ) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="shot_ir", source=job.shot_ir_ref),
            SourceVersionBinding(role="static_keyframe_spec", source=static.ref),
            SourceVersionBinding(role="full_shot_spec", source=static.full_shot_spec_ref),
            SourceVersionBinding(role="state_snapshot", source=static.state_snapshot_ref),
            SourceVersionBinding(
                role="approved_state_designation",
                source=static.approved_state_designation_ref,
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
        return tuple(values)

    @staticmethod
    def _guard(summary: str, evidence_refs: tuple[str, ...], **facts) -> TransitionGuardEvidence:
        refs = tuple(dict.fromkeys(str(ref) for ref in evidence_refs if str(ref).strip()))
        return TransitionGuardEvidence(
            summary=summary,
            evidence_refs=refs or ("evidence:static-qa",),
            facts=tuple(GuardFact(key=key, value=value) for key, value in facts.items()),
        )
