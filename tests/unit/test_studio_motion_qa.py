"""IMP-061 Motion / Video QA authority, time-range and failure-path tests."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from agent.studio import (
    CreativeState,
    GateVerdict,
    LifecycleState,
    MotionQADimension,
    MotionQAEvaluatorResponse,
    MotionQAExecutionRequest,
    MotionQAExecutionStatus,
    MotionQAFinding,
    MotionQAFindingVerdict,
    MotionQAGateBlocked,
    MotionQAPolicy,
    MotionQAService,
    MotionQASeverity,
    VersionId,
    VersionRef,
    decide_motion_qa_verdict,
)
from agent.studio.artifact_lifecycle import ArtifactLifecycleService
from agent.studio.generation_job import GenerationJobAxis, ProviderRemoteLineage, TransitionOwner
from agent.studio.persistence import SQLiteWriteOwner
from tests.unit.test_studio_directing import NOW
from tests.unit.test_studio_generation_job import _guard, _job_fixture, _transition


EVIDENCE = ("evidence:imp061",)
POLICY = MotionQAPolicy(policy_version="motion-qa-policy-v1", auto_approve_pass=True)
VIDEO_BYTES = b"imp061-canonical-video-bytes"


def _finding(
    dimension: MotionQADimension,
    *,
    duration: float,
    verdict: MotionQAFindingVerdict = MotionQAFindingVerdict.PASS,
    severity: MotionQASeverity = MotionQASeverity.LOW,
    start_seconds: float = 0.0,
    end_seconds: float | None = None,
    source_refs: tuple[VersionRef, ...] = (),
) -> MotionQAFinding:
    return MotionQAFinding(
        dimension=dimension,
        verdict=verdict,
        severity=severity,
        confidence=0.99,
        reason_code=f"IMP061_{dimension.value}",
        explanation=f"fixture evaluation for {dimension.value}",
        start_seconds=start_seconds,
        end_seconds=duration if end_seconds is None else end_seconds,
        evidence_refs=(f"evidence:imp061:{dimension.value.lower()}",),
        source_refs=source_refs,
    )


def _findings(
    *,
    duration: float,
    failing_dimension: MotionQADimension | None = None,
    failing_severity: MotionQASeverity = MotionQASeverity.BLOCKING,
    source_refs: tuple[VersionRef, ...] = (),
) -> tuple[MotionQAFinding, ...]:
    values = []
    for dimension in MotionQADimension:
        failing = dimension is failing_dimension
        values.append(
            _finding(
                dimension,
                duration=duration,
                verdict=MotionQAFindingVerdict.FAIL if failing else MotionQAFindingVerdict.PASS,
                severity=failing_severity if failing else MotionQASeverity.LOW,
                start_seconds=2.0 if failing else 0.0,
                end_seconds=min(4.0, duration) if failing else duration,
                source_refs=source_refs if failing else (),
            )
        )
    return tuple(values)


@dataclass
class _Evaluator:
    response: MotionQAEvaluatorResponse
    evaluator_id: str = "fixture-motion-vision"
    evaluator_version: str = "v1"
    subject = None

    async def evaluate(self, subject):
        self.subject = subject
        return self.response


@dataclass
class _FailingEvaluator:
    evaluator_id: str = "fixture-motion-vision"
    evaluator_version: str = "v1"

    async def evaluate(self, subject):
        raise RuntimeError("motion vision backend unavailable")


async def _provider_success_fixture(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    repo, job, ir, *_ = await _job_fixture(writer)
    job = (
        await _transition(
            repo,
            job,
            axis=GenerationJobAxis.SCHEDULER,
            command="CLAIM",
            owner=TransitionOwner.SCHEDULER,
        )
    ).job
    job = (
        await _transition(
            repo,
            job,
            axis=GenerationJobAxis.SCHEDULER,
            command="START_WORK",
            owner=TransitionOwner.SCHEDULER,
        )
    ).job
    job = (
        await _transition(
            repo,
            job,
            axis=GenerationJobAxis.PROVIDER,
            command="SUBMIT",
            owner=TransitionOwner.PROVIDER_ADAPTER,
            guard=_guard(side_effect_boundary_ready=True),
        )
    ).job
    job = (
        await _transition(
            repo,
            job,
            axis=GenerationJobAxis.PROVIDER,
            command="ACCEPTED_HANDLE",
            owner=TransitionOwner.PROVIDER_ADAPTER,
            remote=ProviderRemoteLineage(provider_operation_id="op-imp061"),
        )
    ).job
    job = (
        await _transition(
            repo,
            job,
            axis=GenerationJobAxis.PROVIDER,
            command="START_POLL",
            owner=TransitionOwner.PROVIDER_ADAPTER,
        )
    ).job
    job = (
        await _transition(
            repo,
            job,
            axis=GenerationJobAxis.PROVIDER,
            command="REMOTE_SUCCESS",
            owner=TransitionOwner.PROVIDER_ADAPTER,
        )
    ).job
    return writer, repo, job, ir


async def _materialize(
    artifact_service: ArtifactLifecycleService,
    job,
    *,
    media_type: str = "video/mp4",
    extension: str = "mp4",
    data: bytes = VIDEO_BYTES,
):
    await artifact_service.begin_materialization(
        job_id=job.generation_job_id,
        attempt=1,
        extension=extension,
        media_type=media_type,
        guard_evidence=_guard(local_result_eligible=True),
        actor_ref="studio:imp061-test",
        reason="begin canonical Motion QA artifact materialization",
        correlation_id="run:imp061",
        recorded_at=NOW,
        evidence_refs=EVIDENCE,
    )
    await artifact_service.write_staging_bytes(
        job_id=job.generation_job_id,
        attempt=1,
        data=data,
        actor_ref="studio:imp061-test",
        reason="write Motion QA artifact bytes",
        correlation_id="run:imp061",
        recorded_at=NOW,
        evidence_refs=EVIDENCE,
    )
    return await artifact_service.finalize_materialization(
        job_id=job.generation_job_id,
        attempt=1,
        current_input_fingerprint=job.expected_input_fingerprint,
        actor_ref="studio:imp061-test",
        reason="finalize Motion QA artifact bytes",
        correlation_id="run:imp061",
        recorded_at=NOW,
        evidence_refs=EVIDENCE,
    )


async def _fixture(tmp_path, *, media_type: str = "video/mp4"):
    writer, repo, job, ir = await _provider_success_fixture(tmp_path)
    artifact_service = ArtifactLifecycleService(writer, tmp_path / "artifacts")
    await _materialize(
        artifact_service,
        job,
        media_type=media_type,
        extension="mp4" if media_type.startswith("video/") else "png",
    )
    service = MotionQAService(writer, tmp_path / "artifacts")
    request = MotionQAExecutionRequest(
        generation_job_id=job.generation_job_id,
        motion_delta_spec_ref=ir.motion_delta_spec_ref,
        result_version_id=VersionId("motion-qa-v1"),
        policy=POLICY,
        actor_ref="studio:imp061-test",
        reason="evaluate canonical generated video",
        correlation_id="run:imp061",
        recorded_at=NOW,
        evidence_refs=EVIDENCE,
    )
    return writer, repo, job, ir, artifact_service, service, request


def test_blocking_motion_failure_cannot_be_masked_by_high_aggregate_score():
    duration = 8.0
    findings = _findings(
        duration=duration,
        failing_dimension=MotionQADimension.TEMPORAL_ACTION,
    )
    response = MotionQAEvaluatorResponse(
        evaluator_id="fixture-motion-vision",
        evaluator_version="v1",
        observed_duration_seconds=duration,
        findings=findings,
        aggregate_score=99.9,
    )
    assert response.aggregate_score == 99.9
    assert decide_motion_qa_verdict(response.findings, POLICY) is GateVerdict.FAIL


@pytest.mark.asyncio
async def test_provider_success_without_ready_video_cannot_imply_motion_qa_pass(tmp_path):
    writer, repo, job, ir = await _provider_success_fixture(tmp_path)
    service = MotionQAService(writer, tmp_path / "artifacts")
    evaluator = _Evaluator(
        MotionQAEvaluatorResponse(
            evaluator_id="fixture-motion-vision",
            evaluator_version="v1",
            observed_duration_seconds=float(ir.motion_delta.duration_seconds),
            findings=_findings(duration=float(ir.motion_delta.duration_seconds)),
        )
    )
    request = MotionQAExecutionRequest(
        generation_job_id=job.generation_job_id,
        motion_delta_spec_ref=ir.motion_delta_spec_ref,
        result_version_id=VersionId("motion-qa-v1"),
        policy=POLICY,
        actor_ref="studio:imp061-test",
        reason="prove provider success is not Motion QA pass",
        correlation_id="run:imp061",
        recorded_at=NOW,
        evidence_refs=EVIDENCE,
    )
    try:
        with pytest.raises(MotionQAGateBlocked, match="artifact READY; provider success alone is insufficient"):
            await service.evaluate(request, evaluator)
        current = await repo.get_job(job.generation_job_id)
        assert current is not None
        assert current.creative_state is CreativeState.NOT_APPLICABLE
        assert evaluator.subject is None
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_pass_inspects_actual_video_and_binds_motion_lineage_provenance(tmp_path):
    writer, _, _, ir, _, service, request = await _fixture(tmp_path)
    duration = float(ir.motion_delta.duration_seconds)
    findings = list(_findings(duration=duration))
    findings[0] = findings[0].model_copy(update={"source_refs": (ir.active_profile_ref,)})
    assert ir.static_state.visible_subject_refs
    identity_ref = ir.static_state.visible_subject_refs[0]
    findings[2] = findings[2].model_copy(update={"source_refs": (identity_ref,)})
    evaluator = _Evaluator(
        MotionQAEvaluatorResponse(
            evaluator_id="fixture-motion-vision",
            evaluator_version="v1",
            observed_duration_seconds=duration,
            findings=tuple(findings),
            aggregate_score=98.5,
        )
    )
    try:
        result = await service.evaluate(request, evaluator)
        assert result.artifact.value.execution_status is MotionQAExecutionStatus.COMPLETED
        assert result.artifact.value.verdict is GateVerdict.PASS
        assert result.job.creative_state is CreativeState.APPROVED
        assert evaluator.subject is not None
        assert evaluator.subject.artifact_path.read_bytes() == VIDEO_BYTES
        assert evaluator.subject.media_type == "video/mp4"
        assert evaluator.subject.shot_ir == ir
        assert evaluator.subject.motion_delta_spec.ref == ir.motion_delta_spec_ref
        assert evaluator.subject.motion_delta_spec.duration_seconds == ir.motion_delta.duration_seconds
        assert evaluator.subject.visible_subject_refs == ir.static_state.visible_subject_refs
        assert result.artifact.value.motion_delta_spec_ref == ir.motion_delta_spec_ref
        assert result.artifact.value.visible_subject_refs == ir.static_state.visible_subject_refs
        assert result.artifact.value.observed_duration_seconds == duration
        assert any(
            binding.role == "finding_technical_integrity_000"
            and binding.source == ir.active_profile_ref
            for binding in result.artifact.value.source_bindings()
        )
        assert any(
            binding.role == "visible_subject_000" and binding.source == identity_ref
            for binding in result.artifact.value.source_bindings()
        )
        assert any(
            binding.role == "finding_identity_drift_000" and binding.source == identity_ref
            for binding in result.artifact.value.source_bindings()
        )
        assert "evaluator:fixture-motion-vision@v1" in result.artifact.metadata.provenance.source_refs
        assert "policy:motion-qa-policy-v1" in result.artifact.metadata.provenance.source_refs
        assert "evidence:imp061:technical_integrity" in result.artifact.metadata.provenance.source_refs
        pointer = await service.versions.get_current(result.artifact.ref.logical_id)
        assert pointer is not None
        assert pointer.version_id == result.artifact.ref.version_id
        assert pointer.status is LifecycleState.APPROVED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_blocking_time_range_defect_forces_qa_failed_even_with_high_score(tmp_path):
    writer, _, _, ir, _, service, request = await _fixture(tmp_path)
    duration = float(ir.motion_delta.duration_seconds)
    evaluator = _Evaluator(
        MotionQAEvaluatorResponse(
            evaluator_id="fixture-motion-vision",
            evaluator_version="v1",
            observed_duration_seconds=duration,
            findings=_findings(
                duration=duration,
                failing_dimension=MotionQADimension.IDENTITY_DRIFT,
            ),
            aggregate_score=99.0,
        )
    )
    try:
        result = await service.evaluate(request, evaluator)
        assert result.artifact.value.verdict is GateVerdict.FAIL
        assert result.job.creative_state is CreativeState.QA_FAILED
        finding = next(
            item
            for item in result.artifact.value.findings
            if item.dimension is MotionQADimension.IDENTITY_DRIFT
        )
        assert finding.start_seconds == 2.0
        assert finding.end_seconds == min(4.0, duration)
        pointer = await service.versions.get_current(result.artifact.ref.logical_id)
        assert pointer is not None and pointer.status is LifecycleState.REVIEW
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_evaluator_failure_is_qa_error_not_artifact_qa_failed(tmp_path):
    writer, _, _, _, _, service, request = await _fixture(tmp_path)
    try:
        result = await service.evaluate(request, _FailingEvaluator())
        assert result.artifact.value.execution_status is MotionQAExecutionStatus.EVALUATOR_ERROR
        assert result.artifact.value.verdict is None
        assert result.artifact.value.error_code == "RuntimeError"
        assert result.job.creative_state is CreativeState.QA_ERROR
        pointer = await service.versions.get_current(result.artifact.ref.logical_id)
        assert pointer is not None and pointer.status is LifecycleState.REVIEW
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_non_video_ready_artifact_is_blocked_before_evaluator(tmp_path):
    writer, repo, job, ir, _, service, request = await _fixture(tmp_path, media_type="image/png")
    duration = float(ir.motion_delta.duration_seconds)
    evaluator = _Evaluator(
        MotionQAEvaluatorResponse(
            evaluator_id="fixture-motion-vision",
            evaluator_version="v1",
            observed_duration_seconds=duration,
            findings=_findings(duration=duration),
        )
    )
    try:
        with pytest.raises(MotionQAGateBlocked, match=r"requires READY video/\* artifact evidence"):
            await service.evaluate(request, evaluator)
        current = await repo.get_job(job.generation_job_id)
        assert current is not None
        assert current.creative_state is CreativeState.NOT_APPLICABLE
        assert evaluator.subject is None
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_noncurrent_motion_spec_is_blocked_before_evaluator(tmp_path):
    writer, repo, job, ir, _, service, request = await _fixture(tmp_path)
    duration = float(ir.motion_delta.duration_seconds)
    evaluator = _Evaluator(
        MotionQAEvaluatorResponse(
            evaluator_id="fixture-motion-vision",
            evaluator_version="v1",
            observed_duration_seconds=duration,
            findings=_findings(duration=duration),
        )
    )
    stale_request = request.model_copy(
        update={
            "motion_delta_spec_ref": VersionRef(
                logical_id=ir.motion_delta_spec_ref.logical_id,
                version_id=VersionId("stale-or-missing-motion-v0"),
            )
        }
    )
    try:
        with pytest.raises(MotionQAGateBlocked, match="not exact current accepted authority"):
            await service.evaluate(stale_request, evaluator)
        current = await repo.get_job(job.generation_job_id)
        assert current is not None
        assert current.creative_state is CreativeState.NOT_APPLICABLE
        assert evaluator.subject is None
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_default_policy_pass_routes_to_human_review(tmp_path):
    writer, _, _, ir, _, service, request = await _fixture(tmp_path)
    duration = float(ir.motion_delta.duration_seconds)
    request = request.model_copy(
        update={"policy": MotionQAPolicy(policy_version="motion-qa-policy-default-v1")}
    )
    evaluator = _Evaluator(
        MotionQAEvaluatorResponse(
            evaluator_id="fixture-motion-vision",
            evaluator_version="v1",
            observed_duration_seconds=duration,
            findings=_findings(duration=duration),
            aggregate_score=100.0,
        )
    )
    try:
        result = await service.evaluate(request, evaluator)
        assert result.artifact.value.verdict is GateVerdict.PASS
        assert result.job.creative_state is CreativeState.NEEDS_HUMAN_REVIEW
        pointer = await service.versions.get_current(result.artifact.ref.logical_id)
        assert pointer is not None and pointer.status is LifecycleState.REVIEW
    finally:
        await writer.close()
