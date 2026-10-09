"""IMP-064 explicit QA/approval -> canonical StateSnapshot commit tests."""

from __future__ import annotations

import pytest

from agent.studio import (
    ApprovalStateCommitBlocked,
    ApprovalStateCommitRequest,
    ApprovalStateCommitService,
    CreativeState,
    GateVerdict,
    LifecycleState,
    LogicalId,
    MotionQAEvaluatorResponse,
    Provenance,
    SemanticRecordMetadata,
    StateFact,
    StateFactNamespace,
    StateSnapshot,
    StateSnapshotRepository,
    StaticQADimension,
    StaticQAEvaluatorResponse,
    VersionId,
    VersionRef,
    VersionRepository,
    build_state_snapshot_provenance,
    state_snapshot_logical_id,
    static_qa_result_logical_id,
)
from agent.studio.persistence import CASConflict
from tests.unit.test_studio_directing import NOW
from tests.unit.test_studio_motion_qa import (
    _Evaluator as _MotionEvaluator,
    _findings as _motion_findings,
    _fixture as _motion_fixture,
)
from tests.unit.test_studio_static_qa import (
    _Evaluator as _StaticEvaluator,
    _findings as _static_findings,
    _fixture as _static_fixture,
)


def _seed_provenance(reason: str) -> Provenance:
    return Provenance(
        source_refs=("evidence:imp064",),
        actor_ref="studio:imp064-test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp064",
    )


async def _seed_accepted(versions: VersionRepository, ref: VersionRef, *, label: str) -> None:
    await versions.create_initial(
        metadata=SemanticRecordMetadata(
            logical_id=ref.logical_id,
            version_id=ref.version_id,
            provenance=_seed_provenance(f"seed {label}"),
            created_at=NOW,
        ),
        payload={"fixture": label},
        status=LifecycleState.APPROVED,
    )


async def _candidate(
    writer,
    *,
    project_id: LogicalId,
    change_ref: VersionRef,
    qa_result_ref: VersionRef,
    suffix: str,
):
    versions = VersionRepository(writer)
    policy_ref = VersionRef(
        logical_id=LogicalId(f"approval-policy:{project_id.root}:{suffix}"),
        version_id=VersionId("policy-v1"),
    )
    outcome_ref = VersionRef(
        logical_id=LogicalId(f"artifact-outcome:{project_id.root}:{suffix}"),
        version_id=VersionId("outcome-v1"),
    )
    await _seed_accepted(versions, policy_ref, label="approval policy")
    await _seed_accepted(versions, outcome_ref, label="source outcome")

    snapshot = StateSnapshot(
        project_id=project_id,
        state_snapshot_id=state_snapshot_logical_id(project_id, f"timeline:imp064:{suffix}"),
        version_id=VersionId("state-v1"),
        scope_key=f"timeline:imp064:{suffix}",
        story_time="T+00:08",
        facts=(
            StateFact(
                namespace=StateFactNamespace.ENVIRONMENT,
                key="weather",
                value_json='{"condition":"clear"}',
            ),
        ),
        source_outcome_ref=outcome_ref,
        change_refs=(change_ref,),
    )
    state_repo = StateSnapshotRepository(writer)
    await state_repo.create_initial(
        snapshot=snapshot,
        provenance=build_state_snapshot_provenance(
            snapshot,
            actor_ref="studio:imp064-test",
            reason="candidate approved end state",
            recorded_at=NOW,
        ),
        created_at=NOW,
    )
    request = ApprovalStateCommitRequest(
        generation_job_id=LogicalId("placeholder:job"),
        state_snapshot_ref=snapshot.ref,
        qa_result_ref=qa_result_ref,
        approval_policy_ref=policy_ref,
        source_outcome_ref=outcome_ref,
        designation_version=VersionId("approval-v1"),
        expected_snapshot_revision=0,
        actor_ref="approval:imp064-test",
        reason="commit QA-approved canonical state",
        recorded_at=NOW,
        correlation_id="run:imp064",
    )
    return state_repo, snapshot, request


def _static_pass_evaluator():
    return _StaticEvaluator(
        StaticQAEvaluatorResponse(
            evaluator_id="fixture-static-vision",
            evaluator_version="v1",
            findings=_static_findings(),
            aggregate_score=98.5,
        )
    )


@pytest.mark.asyncio
async def test_provider_success_without_qa_approval_cannot_commit_state(tmp_path):
    writer, _, job, ir, _, _, qa_request = await _static_fixture(tmp_path)
    qa_ref = VersionRef(
        logical_id=static_qa_result_logical_id(job.project_id, job.generation_job_id),
        version_id=qa_request.result_version_id,
    )
    state_repo, snapshot, request = await _candidate(
        writer,
        project_id=job.project_id,
        change_ref=ir.full_shot_spec_ref,
        qa_result_ref=qa_ref,
        suffix="no-qa",
    )
    request = request.model_copy(update={"generation_job_id": job.generation_job_id})
    service = ApprovalStateCommitService(writer)
    try:
        with pytest.raises(ApprovalStateCommitBlocked, match="NO QA APPROVAL"):
            await service.commit(request)
        pointer = await state_repo.get_current_pointer(snapshot.state_snapshot_id)
        assert pointer is not None and pointer.status is LifecycleState.DRAFT
        assert await state_repo.get_approved_designation(snapshot.ref) is None
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_static_qa_pass_and_creative_approval_commit_exact_state_designation(tmp_path):
    writer, _, job, ir, _, qa_service, qa_request = await _static_fixture(tmp_path)
    qa_execution = await qa_service.evaluate(qa_request, _static_pass_evaluator())
    assert qa_execution.artifact.value.verdict is GateVerdict.PASS
    assert qa_execution.job.creative_state is CreativeState.APPROVED

    state_repo, snapshot, request = await _candidate(
        writer,
        project_id=job.project_id,
        change_ref=ir.full_shot_spec_ref,
        qa_result_ref=qa_execution.artifact.ref,
        suffix="static-pass",
    )
    request = request.model_copy(update={"generation_job_id": job.generation_job_id})
    service = ApprovalStateCommitService(writer)
    try:
        result = await service.commit(request)
        designation = result.state_approval.designation.value
        assert designation.state_snapshot_ref == snapshot.ref
        assert designation.qa_result_ref == qa_execution.artifact.ref
        assert designation.approval_policy_ref == request.approval_policy_ref
        assert designation.source_outcome_ref == request.source_outcome_ref
        pointer = await state_repo.get_current_pointer(snapshot.state_snapshot_id)
        assert pointer is not None
        assert pointer.version_id == snapshot.version_id
        assert pointer.status is LifecycleState.APPROVED
        persisted = await state_repo.get_approved_designation(snapshot.ref)
        assert persisted is not None and persisted.value.state_snapshot_ref == snapshot.ref
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_motion_qa_pass_is_typed_approval_evidence_for_state_commit(tmp_path):
    writer, _, job, ir, _, qa_service, qa_request = await _motion_fixture(tmp_path)
    duration = float(ir.motion_delta.duration_seconds)
    evaluator = _MotionEvaluator(
        MotionQAEvaluatorResponse(
            evaluator_id="fixture-motion-vision",
            evaluator_version="v1",
            observed_duration_seconds=duration,
            findings=_motion_findings(duration=duration),
            aggregate_score=98.5,
        )
    )
    qa_execution = await qa_service.evaluate(qa_request, evaluator)
    assert qa_execution.artifact.value.verdict is GateVerdict.PASS
    assert qa_execution.job.creative_state is CreativeState.APPROVED

    state_repo, snapshot, request = await _candidate(
        writer,
        project_id=job.project_id,
        change_ref=ir.full_shot_spec_ref,
        qa_result_ref=qa_execution.artifact.ref,
        suffix="motion-pass",
    )
    request = request.model_copy(update={"generation_job_id": job.generation_job_id})
    service = ApprovalStateCommitService(writer)
    try:
        result = await service.commit(request)
        assert result.state_approval.designation.value.qa_result_ref == qa_execution.artifact.ref
        assert result.state_approval.designation.value.state_snapshot_ref == snapshot.ref
        pointer = await state_repo.get_current_pointer(snapshot.state_snapshot_id)
        assert pointer is not None and pointer.status is LifecycleState.APPROVED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_candidate_revision_is_rejected_without_designation(tmp_path):
    writer, _, job, ir, _, qa_service, qa_request = await _static_fixture(tmp_path)
    qa_execution = await qa_service.evaluate(qa_request, _static_pass_evaluator())
    state_repo, snapshot, request = await _candidate(
        writer,
        project_id=job.project_id,
        change_ref=ir.full_shot_spec_ref,
        qa_result_ref=qa_execution.artifact.ref,
        suffix="stale-state",
    )
    request = request.model_copy(update={"generation_job_id": job.generation_job_id})
    await VersionRepository(writer).update_current(
        logical_id=snapshot.state_snapshot_id,
        version_id=snapshot.version_id,
        status=LifecycleState.REVIEW,
        expected_revision=0,
    )
    service = ApprovalStateCommitService(writer)
    try:
        with pytest.raises(ApprovalStateCommitBlocked, match="stale or CAS revision changed"):
            await service.commit(request)
        pointer = await state_repo.get_current_pointer(snapshot.state_snapshot_id)
        assert pointer is not None and pointer.revision == 1
        assert await state_repo.get_approved_designation(snapshot.ref) is None
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_free_form_qa_payload_cannot_substitute_typed_pass_evidence(tmp_path):
    writer, _, job, ir, _, qa_service, qa_request = await _static_fixture(tmp_path)
    approved = await qa_service.evaluate(qa_request, _static_pass_evaluator())
    assert approved.job.creative_state is CreativeState.APPROVED

    fake_qa_ref = VersionRef(
        logical_id=LogicalId("qa-result:project:film:free-form"),
        version_id=VersionId("qa-v1"),
    )
    await _seed_accepted(VersionRepository(writer), fake_qa_ref, label="free form qa payload")
    state_repo, snapshot, request = await _candidate(
        writer,
        project_id=job.project_id,
        change_ref=ir.full_shot_spec_ref,
        qa_result_ref=fake_qa_ref,
        suffix="fake-qa",
    )
    request = request.model_copy(update={"generation_job_id": job.generation_job_id})
    service = ApprovalStateCommitService(writer)
    try:
        with pytest.raises(ApprovalStateCommitBlocked, match="not valid typed QA evidence"):
            await service.commit(request)
        pointer = await state_repo.get_current_pointer(snapshot.state_snapshot_id)
        assert pointer is not None and pointer.status is LifecycleState.DRAFT
        assert await state_repo.get_approved_designation(snapshot.ref) is None
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_human_approved_pass_promotes_review_qa_then_commits_state(tmp_path):
    from agent.studio import GenerationJobAxis, StaticQAPolicy, TransitionOwner
    from tests.unit.test_studio_generation_job import _guard

    writer, repo, job, ir, _, qa_service, qa_request = await _static_fixture(tmp_path)
    human_request = qa_request.model_copy(
        update={"policy": StaticQAPolicy(policy_version="static-qa-policy-human-v1")}
    )
    qa_execution = await qa_service.evaluate(human_request, _static_pass_evaluator())
    assert qa_execution.artifact.value.verdict is GateVerdict.PASS
    assert qa_execution.job.creative_state is CreativeState.NEEDS_HUMAN_REVIEW
    versions = VersionRepository(writer)
    qa_pointer = await versions.get_current(qa_execution.artifact.ref.logical_id)
    assert qa_pointer is not None and qa_pointer.status is LifecycleState.REVIEW

    approved_job = (
        await repo.transition(
            job_id=job.generation_job_id,
            axis=GenerationJobAxis.CREATIVE,
            command="HUMAN_APPROVE",
            owner=TransitionOwner.HUMAN_REVIEW,
            guard_evidence=_guard("human approval after typed QA PASS"),
            expected_revision=qa_execution.job.revision,
            actor_ref="human-reviewer:imp064-test",
            reason="explicit human approval of QA PASS artifact",
            correlation_id="run:imp064-human",
            recorded_at=NOW,
        )
    ).job
    assert approved_job.creative_state is CreativeState.APPROVED

    state_repo, snapshot, request = await _candidate(
        writer,
        project_id=job.project_id,
        change_ref=ir.full_shot_spec_ref,
        qa_result_ref=qa_execution.artifact.ref,
        suffix="human-pass",
    )
    request = request.model_copy(update={"generation_job_id": job.generation_job_id})
    service = ApprovalStateCommitService(writer)
    try:
        result = await service.commit(request)
        assert result.state_approval.designation.value.state_snapshot_ref == snapshot.ref
        qa_pointer = await versions.get_current(qa_execution.artifact.ref.logical_id)
        assert qa_pointer is not None and qa_pointer.status is LifecycleState.APPROVED
        state_pointer = await state_repo.get_current_pointer(snapshot.state_snapshot_id)
        assert state_pointer is not None and state_pointer.status is LifecycleState.APPROVED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_interrupted_auto_approval_cannot_be_reinterpreted_as_human_approval(
    tmp_path,
    monkeypatch,
):
    writer, repo, job, ir, _, qa_service, qa_request = await _static_fixture(tmp_path)
    qa_ref = VersionRef(
        logical_id=static_qa_result_logical_id(job.project_id, job.generation_job_id),
        version_id=qa_request.result_version_id,
    )

    async def _crash_after_auto_approval_transition(**_kwargs):
        raise CASConflict("simulated crash before QA pointer promotion")

    monkeypatch.setattr(qa_service.versions, "update_current", _crash_after_auto_approval_transition)
    try:
        with pytest.raises(CASConflict, match="simulated crash"):
            await qa_service.evaluate(qa_request, _static_pass_evaluator())

        interrupted_job = await repo.get_job(job.generation_job_id)
        assert interrupted_job is not None
        assert interrupted_job.creative_state is CreativeState.APPROVED
        versions = VersionRepository(writer)
        qa_pointer = await versions.get_current(qa_ref.logical_id)
        assert qa_pointer is not None
        assert qa_pointer.version_id == qa_ref.version_id
        assert qa_pointer.status is LifecycleState.REVIEW

        state_repo, snapshot, request = await _candidate(
            writer,
            project_id=job.project_id,
            change_ref=ir.full_shot_spec_ref,
            qa_result_ref=qa_ref,
            suffix="interrupted-auto-approval",
        )
        request = request.model_copy(update={"generation_job_id": job.generation_job_id})

        with pytest.raises(ApprovalStateCommitBlocked, match="durable HUMAN_APPROVE"):
            await ApprovalStateCommitService(writer).commit(request)

        qa_pointer = await versions.get_current(qa_ref.logical_id)
        assert qa_pointer is not None and qa_pointer.status is LifecycleState.REVIEW
        state_pointer = await state_repo.get_current_pointer(snapshot.state_snapshot_id)
        assert state_pointer is not None and state_pointer.status is LifecycleState.DRAFT
        assert await state_repo.get_approved_designation(snapshot.ref) is None
    finally:
        await writer.close()
