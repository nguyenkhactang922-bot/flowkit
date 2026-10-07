"""IMP-060 Static QA authority, policy, evidence-binding and failure tests."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from agent.studio import (
    CreativeState,
    GateVerdict,
    LifecycleState,
    StaticQADimension,
    StaticQAEvaluatorResponse,
    StaticQAExecutionRequest,
    StaticQAExecutionStatus,
    StaticQAFinding,
    StaticQAFindingVerdict,
    StaticQAGateBlocked,
    StaticQAPolicy,
    StaticQAService,
    StaticQASeverity,
    VersionId,
    VersionRef,
    decide_static_qa_verdict,
)
from agent.studio.artifact_lifecycle import ArtifactLifecycleService
from agent.studio.generation_job import GenerationJobAxis, ProviderRemoteLineage, TransitionOwner
from agent.studio.persistence import SQLiteWriteOwner
from tests.unit.test_studio_artifact_lifecycle import _ready
from tests.unit.test_studio_directing import NOW
from tests.unit.test_studio_generation_job import _guard, _job_fixture, _transition


EVIDENCE = ("evidence:imp060",)
POLICY = StaticQAPolicy(policy_version="static-qa-policy-v1", auto_approve_pass=True)


def _finding(
    dimension: StaticQADimension,
    *,
    verdict: StaticQAFindingVerdict = StaticQAFindingVerdict.PASS,
    severity: StaticQASeverity = StaticQASeverity.LOW,
    source_refs: tuple[VersionRef, ...] = (),
) -> StaticQAFinding:
    return StaticQAFinding(
        dimension=dimension,
        verdict=verdict,
        severity=severity,
        confidence=0.99,
        reason_code=f"IMP060_{dimension.value}",
        explanation=f"fixture evaluation for {dimension.value}",
        evidence_refs=(f"evidence:imp060:{dimension.value.lower()}",),
        source_refs=source_refs,
    )


def _findings(
    *,
    failing_dimension: StaticQADimension | None = None,
    failing_severity: StaticQASeverity = StaticQASeverity.BLOCKING,
    source_refs: tuple[VersionRef, ...] = (),
) -> tuple[StaticQAFinding, ...]:
    return tuple(
        _finding(
            dimension,
            verdict=(
                StaticQAFindingVerdict.FAIL
                if dimension is failing_dimension
                else StaticQAFindingVerdict.PASS
            ),
            severity=(failing_severity if dimension is failing_dimension else StaticQASeverity.LOW),
            source_refs=source_refs if dimension is failing_dimension else (),
        )
        for dimension in StaticQADimension
    )


@dataclass
class _Evaluator:
    response: StaticQAEvaluatorResponse
    evaluator_id: str = "fixture-static-vision"
    evaluator_version: str = "v1"
    subject = None

    async def evaluate(self, subject):
        self.subject = subject
        return self.response


@dataclass
class _FailingEvaluator:
    evaluator_id: str = "fixture-static-vision"
    evaluator_version: str = "v1"

    async def evaluate(self, subject):
        raise RuntimeError("vision backend unavailable")


async def _fixture(tmp_path):
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
            remote=ProviderRemoteLineage(provider_operation_id="op-imp060"),
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
    artifact_service = ArtifactLifecycleService(writer, tmp_path / "artifacts")
    await _ready(artifact_service, job, data=b"imp060-static-image-bytes")
    service = StaticQAService(writer, tmp_path / "artifacts")
    request = StaticQAExecutionRequest(
        generation_job_id=job.generation_job_id,
        static_keyframe_spec_ref=ir.static_keyframe_spec_ref,
        result_version_id=VersionId("qa-v1"),
        policy=POLICY,
        actor_ref="studio:imp060-test",
        reason="evaluate canonical static artifact",
        correlation_id="run:imp060",
        recorded_at=NOW,
        evidence_refs=EVIDENCE,
    )
    return writer, repo, job, ir, artifact_service, service, request


def test_blocking_identity_failure_cannot_be_masked_by_high_aggregate_score():
    findings = _findings(failing_dimension=StaticQADimension.IDENTITY)
    response = StaticQAEvaluatorResponse(
        evaluator_id="fixture-static-vision",
        evaluator_version="v1",
        findings=findings,
        aggregate_score=99.9,
    )
    assert response.aggregate_score == 99.9
    assert decide_static_qa_verdict(response.findings, POLICY) is GateVerdict.FAIL


@pytest.mark.asyncio
async def test_pass_inspects_actual_ready_artifact_and_auto_approves_exact_qa_result(tmp_path):
    writer, _, job, ir, _, service, request = await _fixture(tmp_path)
    findings = list(_findings())
    findings[0] = findings[0].model_copy(update={"source_refs": (ir.active_profile_ref,)})
    evaluator = _Evaluator(
        StaticQAEvaluatorResponse(
            evaluator_id="fixture-static-vision",
            evaluator_version="v1",
            findings=tuple(findings),
            aggregate_score=98.5,
        )
    )
    try:
        result = await service.evaluate(request, evaluator)
        assert result.artifact.value.execution_status is StaticQAExecutionStatus.COMPLETED
        assert result.artifact.value.verdict is GateVerdict.PASS
        assert result.job.creative_state is CreativeState.APPROVED
        assert evaluator.subject is not None
        assert evaluator.subject.artifact_path.read_bytes() == b"imp060-static-image-bytes"
        assert evaluator.subject.shot_ir == ir
        assert evaluator.subject.shot_ir.qa_expectations == ir.qa_expectations
        assert result.artifact.value.active_profile_ref == ir.active_profile_ref
        assert any(
            binding.role == "finding_technical_integrity_000"
            and binding.source == ir.active_profile_ref
            for binding in result.artifact.value.source_bindings()
        )
        assert "evaluator:fixture-static-vision@v1" in result.artifact.metadata.provenance.source_refs
        assert "policy:static-qa-policy-v1" in result.artifact.metadata.provenance.source_refs
        assert "evidence:imp060:technical_integrity" in result.artifact.metadata.provenance.source_refs
        pointer = await service.versions.get_current(result.artifact.ref.logical_id)
        assert pointer is not None
        assert pointer.version_id == result.artifact.ref.version_id
        assert pointer.status is LifecycleState.APPROVED
    finally:
        await writer.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dimension",
    [StaticQADimension.IDENTITY, StaticQADimension.STATE_WARDROBE],
)
async def test_blocking_identity_or_state_defect_forces_qa_failed_even_with_high_score(tmp_path, dimension):
    writer, _, _, _, _, service, request = await _fixture(tmp_path)
    evaluator = _Evaluator(
        StaticQAEvaluatorResponse(
            evaluator_id="fixture-static-vision",
            evaluator_version="v1",
            findings=_findings(failing_dimension=dimension),
            aggregate_score=99.0,
        )
    )
    try:
        result = await service.evaluate(request, evaluator)
        assert result.artifact.value.verdict is GateVerdict.FAIL
        assert result.job.creative_state is CreativeState.QA_FAILED
        pointer = await service.versions.get_current(result.artifact.ref.logical_id)
        assert pointer is not None
        assert pointer.status is LifecycleState.REVIEW
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_evaluator_failure_is_qa_error_not_artifact_qa_failed(tmp_path):
    writer, _, _, _, _, service, request = await _fixture(tmp_path)
    try:
        result = await service.evaluate(request, _FailingEvaluator())
        assert result.artifact.value.execution_status is StaticQAExecutionStatus.EVALUATOR_ERROR
        assert result.artifact.value.verdict is None
        assert result.artifact.value.error_code == "RuntimeError"
        assert result.job.creative_state is CreativeState.QA_ERROR
        pointer = await service.versions.get_current(result.artifact.ref.logical_id)
        assert pointer is not None
        assert pointer.status is LifecycleState.REVIEW
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_tampered_ready_bytes_are_rejected_before_evaluator_or_creative_transition(tmp_path):
    writer, repo, job, _, artifact_service, service, request = await _fixture(tmp_path)
    evaluator = _Evaluator(
        StaticQAEvaluatorResponse(
            evaluator_id="fixture-static-vision",
            evaluator_version="v1",
            findings=_findings(),
        )
    )
    try:
        identity = await artifact_service.evidence.get_identity_for_job(job.generation_job_id)
        assert identity is not None
        events = await artifact_service.evidence.list_events_for_job(job.generation_job_id)
        ready_event = next(event for event in events if event.event_kind.value == "MATERIALIZE_VALID")
        assert ready_event.final_relative_path is not None
        artifact_service.absolute_path(ready_event.final_relative_path).write_bytes(b"tampered")

        with pytest.raises(StaticQAGateBlocked, match="no longer match immutable materialization evidence"):
            await service.evaluate(request, evaluator)
        current = await repo.get_job(job.generation_job_id)
        assert current is not None
        assert current.creative_state is CreativeState.NOT_APPLICABLE
        assert evaluator.subject is None
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_noncurrent_or_missing_static_spec_is_blocked_before_evaluator(tmp_path):
    writer, repo, job, ir, _, service, request = await _fixture(tmp_path)
    evaluator = _Evaluator(
        StaticQAEvaluatorResponse(
            evaluator_id="fixture-static-vision",
            evaluator_version="v1",
            findings=_findings(),
        )
    )
    stale_request = request.model_copy(
        update={
            "static_keyframe_spec_ref": VersionRef(
                logical_id=ir.static_keyframe_spec_ref.logical_id,
                version_id=VersionId("stale-or-missing-static-v0"),
            )
        }
    )
    try:
        with pytest.raises(StaticQAGateBlocked, match="not exact current accepted authority"):
            await service.evaluate(stale_request, evaluator)
        current = await repo.get_job(job.generation_job_id)
        assert current is not None
        assert current.creative_state is CreativeState.NOT_APPLICABLE
        assert evaluator.subject is None
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_default_policy_is_fail_closed_and_routes_pass_to_human_review(tmp_path):
    writer, _, _, _, _, service, request = await _fixture(tmp_path)
    request = request.model_copy(
        update={"policy": StaticQAPolicy(policy_version="static-qa-policy-default-v1")}
    )
    evaluator = _Evaluator(
        StaticQAEvaluatorResponse(
            evaluator_id="fixture-static-vision",
            evaluator_version="v1",
            findings=_findings(),
            aggregate_score=100.0,
        )
    )
    try:
        result = await service.evaluate(request, evaluator)
        assert result.artifact.value.verdict is GateVerdict.PASS
        assert result.job.creative_state is CreativeState.NEEDS_HUMAN_REVIEW
        pointer = await service.versions.get_current(result.artifact.ref.logical_id)
        assert pointer is not None
        assert pointer.status is LifecycleState.REVIEW
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_evaluator_response_identity_mismatch_is_qa_error(tmp_path):
    writer, _, _, _, _, service, request = await _fixture(tmp_path)
    evaluator = _Evaluator(
        StaticQAEvaluatorResponse(
            evaluator_id="spoofed-evaluator",
            evaluator_version="v999",
            findings=_findings(),
        )
    )
    try:
        result = await service.evaluate(request, evaluator)
        assert result.artifact.value.execution_status is StaticQAExecutionStatus.EVALUATOR_ERROR
        assert result.artifact.value.evaluator_id == evaluator.evaluator_id
        assert result.artifact.value.evaluator_version == evaluator.evaluator_version
        assert result.artifact.value.error_code == "StaticQAGateBlocked"
        assert "identity/version" in result.artifact.value.error_message
        assert result.job.creative_state is CreativeState.QA_ERROR
    finally:
        await writer.close()
