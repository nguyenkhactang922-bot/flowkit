"""IMP-062 Continuity QA + Sequence QA cross-boundary authority tests."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from agent.studio import (
    ContinuityQADimension,
    ContinuityQAEvaluatorResponse,
    ContinuityQAExecutionRequest,
    ContinuityQAFinding,
    ContinuityQAService,
    CrossBoundaryQAExecutionStatus,
    CrossBoundaryQAFindingVerdict,
    CrossBoundaryQAGateBlocked,
    CrossBoundaryQAPolicy,
    FindingSeverity,
    GateVerdict,
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SequenceQADimension,
    SequenceQAEvaluatorResponse,
    SequenceQAExecutionRequest,
    SequenceQAFinding,
    SequenceQAService,
    ShotQABinding,
    VersionId,
    VersionRef,
    VersionRepository,
    build_continuity_ledger_provenance,
)
from agent.studio.persistence import SQLiteWriteOwner
from tests.unit.test_studio_state_continuity import (
    NOW,
    PROJECT_ID,
    _create_approved_initial,
    _ledger,
)
from agent.studio.state_continuity import ContinuityLedgerRepository


SCENE_1 = VersionRef(logical_id=LogicalId("scene:project:film:scene-001"), version_id=VersionId("scene-v1"))
SCENE_2 = VersionRef(logical_id=LogicalId("scene:project:film:scene-002"), version_id=VersionId("scene-v1"))
SHOT_1 = VersionRef(logical_id=LogicalId("shot-list-item:project:film:shot-001"), version_id=VersionId("shot-v1"))
SHOT_2 = VersionRef(logical_id=LogicalId("shot-list-item:project:film:shot-002"), version_id=VersionId("shot-v1"))
SHOT_3 = VersionRef(logical_id=LogicalId("shot-list-item:project:film:shot-003"), version_id=VersionId("shot-v1"))
SHOT_QA_1 = VersionRef(logical_id=LogicalId("qa-result:imp062-shot-001"), version_id=VersionId("qa-v1"))
SHOT_QA_2 = VersionRef(logical_id=LogicalId("motion-qa-result:imp062-shot-002"), version_id=VersionId("qa-v1"))
SHOT_QA_3 = VersionRef(logical_id=LogicalId("qa-result:imp062-shot-003"), version_id=VersionId("qa-v1"))
SEQUENCE_1 = VersionRef(logical_id=LogicalId("sequence:project:film:sequence-001"), version_id=VersionId("sequence-v1"))
SETUP_PAYOFF_1 = VersionRef(logical_id=LogicalId("setup-payoff:project:film:link-001"), version_id=VersionId("link-v1"))
POLICY = CrossBoundaryQAPolicy(policy_version="cross-boundary-qa-v1", auto_approve_pass=True)
EVIDENCE = ("evidence:imp062",)


def _provenance(reason: str) -> Provenance:
    return Provenance(
        source_refs=("evidence:imp062-fixture",),
        actor_ref="studio:imp062-test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp062",
    )


async def _seed_version(
    versions: VersionRepository,
    ref: VersionRef,
    *,
    status: LifecycleState = LifecycleState.APPROVED,
    revision_marker: int = 1,
) -> None:
    await versions.create_initial(
        metadata=SemanticRecordMetadata(
            logical_id=ref.logical_id,
            version_id=ref.version_id,
            provenance=_provenance(f"seed {ref.logical_id.root}"),
            created_at=NOW,
        ),
        payload={"fixture": ref.logical_id.root, "revision_marker": revision_marker},
        status=status,
    )


async def _supersede(versions: VersionRepository, ref: VersionRef, new_version: str) -> VersionRef:
    pointer = await versions.get_current(ref.logical_id)
    assert pointer is not None and pointer.version_id == ref.version_id
    successor = VersionRef(logical_id=ref.logical_id, version_id=VersionId(new_version))
    await versions.create_successor(
        metadata=SemanticRecordMetadata(
            logical_id=successor.logical_id,
            version_id=successor.version_id,
            predecessor=ref,
            provenance=_provenance(f"supersede {ref.logical_id.root}"),
            created_at=NOW,
        ),
        payload={"fixture": ref.logical_id.root, "revision_marker": 2},
        supersession_reason="IMP-062 stale-version test",
    )
    await versions.update_current(
        logical_id=successor.logical_id,
        version_id=successor.version_id,
        status=LifecycleState.APPROVED,
        expected_revision=pointer.revision,
    )
    return successor


async def _continuity_fixture(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    _, snapshot, approved = await _create_approved_initial(writer)
    versions = VersionRepository(writer)
    for ref in (SCENE_1, SCENE_2, SHOT_1, SHOT_2, SHOT_QA_1, SHOT_QA_2, SEQUENCE_1, SETUP_PAYOFF_1):
        await _seed_version(versions, ref)
    ledger = _ledger(snapshot, approved.designation.ref)
    ledger_repo = ContinuityLedgerRepository(writer)
    artifact = await ledger_repo.create_initial(
        ledger=ledger,
        provenance=build_continuity_ledger_provenance(
            ledger,
            actor_ref="studio:imp062-test",
            reason="create exact ContinuityLedger for IMP-062",
            recorded_at=NOW,
            source_refs=EVIDENCE,
            correlation_id="run:imp062",
        ),
        created_at=NOW,
    )
    await ledger_repo.promote_current(ref=artifact.ref, expected_revision=0)
    request = ContinuityQAExecutionRequest(
        project_id=PROJECT_ID,
        continuity_ledger_ref=artifact.ref,
        scene_refs=(SCENE_1, SCENE_2),
        shot_qa_bindings=(
            ShotQABinding(shot_ref=SHOT_1, qa_result_refs=(SHOT_QA_1,)),
            ShotQABinding(shot_ref=SHOT_2, qa_result_refs=(SHOT_QA_2,)),
        ),
        result_version_id=VersionId("continuity-qa-v1"),
        policy=POLICY,
        actor_ref="studio:imp062-test",
        reason="evaluate adjacent canonical shots",
        correlation_id="run:imp062",
        recorded_at=NOW,
        evidence_refs=EVIDENCE,
    )
    return writer, versions, snapshot, artifact.value, request


def _continuity_findings(
    *,
    snapshot,
    failing_dimension: ContinuityQADimension | None = None,
    contradiction: bool = False,
    source_refs: tuple[VersionRef, ...] = (),
) -> tuple[ContinuityQAFinding, ...]:
    values = []
    fact_key = snapshot.facts[0].fact_key
    for dimension in ContinuityQADimension:
        failing = dimension is failing_dimension
        values.append(
            ContinuityQAFinding(
                dimension=dimension,
                verdict=CrossBoundaryQAFindingVerdict.FAIL if failing else CrossBoundaryQAFindingVerdict.PASS,
                severity=FindingSeverity.BLOCKER if failing else FindingSeverity.NOTE,
                confidence=0.99,
                reason_code=f"IMP062_CONT_{dimension.value}",
                explanation=f"fixture continuity evaluation for {dimension.value}",
                evidence_refs=(f"evidence:imp062:continuity:{dimension.value.lower()}",),
                source_refs=source_refs if failing else (),
                scene_refs=(SCENE_1, SCENE_2) if failing else (),
                shot_refs=(SHOT_1, SHOT_2) if failing else (),
                state_fact_keys=(fact_key,) if failing else (),
                canonical_state_contradiction=contradiction and failing,
                visual_similarity_score=1.0 if contradiction and failing else None,
            )
        )
    return tuple(values)


def _sequence_findings(
    *,
    failing_dimension: SequenceQADimension | None = None,
    source_refs: tuple[VersionRef, ...] = (),
) -> tuple[SequenceQAFinding, ...]:
    values = []
    for dimension in SequenceQADimension:
        failing = dimension is failing_dimension
        transition = dimension is SequenceQADimension.TRANSITION_COHERENCE
        values.append(
            SequenceQAFinding(
                dimension=dimension,
                verdict=CrossBoundaryQAFindingVerdict.FAIL if failing else CrossBoundaryQAFindingVerdict.PASS,
                severity=FindingSeverity.BLOCKER if failing else FindingSeverity.NOTE,
                confidence=0.99,
                reason_code=f"IMP062_SEQ_{dimension.value}",
                explanation=f"fixture sequence evaluation for {dimension.value}",
                evidence_refs=(f"evidence:imp062:sequence:{dimension.value.lower()}",),
                source_refs=source_refs if failing else (),
                scene_refs=(SCENE_1, SCENE_2) if failing else (),
                shot_refs=(SHOT_1, SHOT_2) if failing else (),
                transition_from_shot_ref=SHOT_1 if transition else None,
                transition_to_shot_ref=SHOT_2 if transition else None,
            )
        )
    return tuple(values)


@dataclass
class _ContinuityEvaluator:
    response: ContinuityQAEvaluatorResponse
    evaluator_id: str = "fixture-continuity-evaluator"
    evaluator_version: str = "v1"
    subject = None

    async def evaluate(self, subject):
        self.subject = subject
        return self.response


@dataclass
class _SequenceEvaluator:
    response: SequenceQAEvaluatorResponse
    evaluator_id: str = "fixture-sequence-evaluator"
    evaluator_version: str = "v1"
    subject = None

    async def evaluate(self, subject):
        self.subject = subject
        return self.response


@dataclass
class _FailingContinuityEvaluator:
    evaluator_id: str = "fixture-continuity-evaluator"
    evaluator_version: str = "v1"

    async def evaluate(self, subject):
        raise RuntimeError("continuity evaluator unavailable")


@pytest.mark.asyncio
async def test_canonical_state_contradiction_beats_perfect_visual_similarity(tmp_path):
    writer, _, snapshot, _, request = await _continuity_fixture(tmp_path)
    try:
        findings = _continuity_findings(
            snapshot=snapshot,
            failing_dimension=ContinuityQADimension.WARDROBE,
            contradiction=True,
            source_refs=(snapshot.ref,),
        )
        evaluator = _ContinuityEvaluator(
            ContinuityQAEvaluatorResponse(
                evaluator_id="fixture-continuity-evaluator",
                evaluator_version="v1",
                findings=findings,
                aggregate_score=100.0,
            )
        )
        artifact = await ContinuityQAService(writer).evaluate(request, evaluator)
        assert artifact.value.verdict is GateVerdict.FAIL
        wardrobe = next(item for item in artifact.value.findings if item.dimension is ContinuityQADimension.WARDROBE)
        assert wardrobe.canonical_state_contradiction is True
        assert wardrobe.visual_similarity_score == 1.0
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_adjacent_shot_drift_is_localized_to_exact_pair_and_blocks(tmp_path):
    writer, _, snapshot, _, request = await _continuity_fixture(tmp_path)
    try:
        findings = _continuity_findings(
            snapshot=snapshot,
            failing_dimension=ContinuityQADimension.ACTION,
            source_refs=(snapshot.ref,),
        )
        evaluator = _ContinuityEvaluator(
            ContinuityQAEvaluatorResponse(
                evaluator_id="fixture-continuity-evaluator",
                evaluator_version="v1",
                findings=findings,
                aggregate_score=98.0,
            )
        )
        artifact = await ContinuityQAService(writer).evaluate(request, evaluator)
        assert artifact.value.verdict is GateVerdict.FAIL
        action = next(item for item in artifact.value.findings if item.dimension is ContinuityQADimension.ACTION)
        assert action.shot_refs == (SHOT_1, SHOT_2)
        assert evaluator.subject.shot_qa_bindings[0].shot_ref == SHOT_1
        assert evaluator.subject.shot_qa_bindings[1].shot_ref == SHOT_2
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_sequence_blocking_coverage_defect_cannot_be_hidden_by_per_shot_pass(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = VersionRepository(writer)
        for ref in (SEQUENCE_1, SCENE_1, SCENE_2, SHOT_1, SHOT_2, SHOT_QA_1, SHOT_QA_2, SETUP_PAYOFF_1):
            await _seed_version(versions, ref)
        request = SequenceQAExecutionRequest(
            project_id=PROJECT_ID,
            sequence_ref=SEQUENCE_1,
            scene_refs=(SCENE_1, SCENE_2),
            shot_qa_bindings=(
                ShotQABinding(shot_ref=SHOT_1, qa_result_refs=(SHOT_QA_1,)),
                ShotQABinding(shot_ref=SHOT_2, qa_result_refs=(SHOT_QA_2,)),
            ),
            setup_payoff_refs=(SETUP_PAYOFF_1,),
            result_version_id=VersionId("sequence-qa-v1"),
            policy=POLICY,
            actor_ref="studio:imp062-test",
            reason="cross-shot sequence gate",
            correlation_id="run:imp062",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        findings = _sequence_findings(
            failing_dimension=SequenceQADimension.COVERAGE_SUFFICIENCY,
            source_refs=(SEQUENCE_1,),
        )
        artifact = await SequenceQAService(writer).evaluate(
            request,
            _SequenceEvaluator(
                SequenceQAEvaluatorResponse(
                    evaluator_id="fixture-sequence-evaluator",
                    evaluator_version="v1",
                    findings=findings,
                    aggregate_score=100.0,
                )
            ),
        )
        assert artifact.value.verdict is GateVerdict.FAIL
        pointer = await versions.get_current(artifact.ref.logical_id)
        assert pointer is not None and pointer.status is LifecycleState.REVIEW
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_shot_qa_version_fails_closed_before_sequence_evaluator(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = VersionRepository(writer)
        for ref in (SEQUENCE_1, SCENE_1, SHOT_1, SHOT_QA_1):
            await _seed_version(versions, ref)
        await _supersede(versions, SHOT_QA_1, "qa-v2")
        request = SequenceQAExecutionRequest(
            project_id=PROJECT_ID,
            sequence_ref=SEQUENCE_1,
            scene_refs=(SCENE_1,),
            shot_qa_bindings=(ShotQABinding(shot_ref=SHOT_1, qa_result_refs=(SHOT_QA_1,)),),
            result_version_id=VersionId("sequence-qa-v1"),
            policy=POLICY,
            actor_ref="studio:imp062-test",
            reason="stale shot QA gate",
            correlation_id="run:imp062",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        evaluator = _SequenceEvaluator(
            SequenceQAEvaluatorResponse(
                evaluator_id="fixture-sequence-evaluator",
                evaluator_version="v1",
                findings=_sequence_findings(),
            )
        )
        with pytest.raises(CrossBoundaryQAGateBlocked, match="exact current"):
            await SequenceQAService(writer).evaluate(request, evaluator)
        assert evaluator.subject is None
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_continuity_evaluator_error_is_immutable_review_evidence(tmp_path):
    writer, versions, _, _, request = await _continuity_fixture(tmp_path)
    try:
        request = request.model_copy(update={"result_version_id": VersionId("continuity-qa-error-v1")})
        service = ContinuityQAService(writer)
        artifact = await service.evaluate(request, _FailingContinuityEvaluator())
        assert artifact.value.execution_status is CrossBoundaryQAExecutionStatus.EVALUATOR_ERROR
        assert artifact.value.verdict is None
        assert artifact.value.error_code == "RuntimeError"
        pointer = await versions.get_current(artifact.ref.logical_id)
        assert pointer is not None and pointer.status is LifecycleState.REVIEW
        persisted = await service.get_result(artifact.ref)
        assert persisted is not None and persisted.value == artifact.value
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_pass_result_pins_provenance_and_dependency_edges(tmp_path):
    writer, versions, snapshot, _, request = await _continuity_fixture(tmp_path)
    try:
        evaluator = _ContinuityEvaluator(
            ContinuityQAEvaluatorResponse(
                evaluator_id="fixture-continuity-evaluator",
                evaluator_version="v1",
                findings=_continuity_findings(snapshot=snapshot),
                aggregate_score=100.0,
            )
        )
        service = ContinuityQAService(writer)
        artifact = await service.evaluate(request, evaluator)
        assert artifact.value.verdict is GateVerdict.PASS
        assert artifact.metadata.provenance.source_versions == artifact.value.source_bindings()
        pointer = await versions.get_current(artifact.ref.logical_id)
        assert pointer is not None and pointer.status is LifecycleState.APPROVED
        descendants = {item.ref for item in await service.graph.descendants(snapshot.ref)}
        assert artifact.ref in descendants
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_sequence_transition_localization_must_bind_adjacent_ordered_shots(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = VersionRepository(writer)
        for ref in (SEQUENCE_1, SCENE_1, SHOT_1, SHOT_2, SHOT_3, SHOT_QA_1, SHOT_QA_2, SHOT_QA_3):
            await _seed_version(versions, ref)
        request = SequenceQAExecutionRequest(
            project_id=PROJECT_ID,
            sequence_ref=SEQUENCE_1,
            scene_refs=(SCENE_1,),
            shot_qa_bindings=(
                ShotQABinding(shot_ref=SHOT_1, qa_result_refs=(SHOT_QA_1,)),
                ShotQABinding(shot_ref=SHOT_2, qa_result_refs=(SHOT_QA_2,)),
                ShotQABinding(shot_ref=SHOT_3, qa_result_refs=(SHOT_QA_3,)),
            ),
            result_version_id=VersionId("sequence-qa-v1"),
            policy=POLICY,
            actor_ref="studio:imp062-test",
            reason="validate transition localization",
            correlation_id="run:imp062",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        findings = list(_sequence_findings())
        index = next(i for i, item in enumerate(findings) if item.dimension is SequenceQADimension.TRANSITION_COHERENCE)
        findings[index] = findings[index].model_copy(
            update={
                "transition_from_shot_ref": SHOT_1,
                "transition_to_shot_ref": SHOT_3,
            }
        )
        artifact = await SequenceQAService(writer).evaluate(
            request,
            _SequenceEvaluator(
                SequenceQAEvaluatorResponse(
                    evaluator_id="fixture-sequence-evaluator",
                    evaluator_version="v1",
                    findings=tuple(findings),
                )
            ),
        )
        assert artifact.value.execution_status is CrossBoundaryQAExecutionStatus.EVALUATOR_ERROR
        assert artifact.value.error_code == "CrossBoundaryQAGateBlocked"
        assert "adjacent ordered shots" in artifact.value.error_message
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_policy_can_allow_not_evaluated_without_forcing_human_review(tmp_path):
    writer, versions, snapshot, _, request = await _continuity_fixture(tmp_path)
    try:
        findings = list(_continuity_findings(snapshot=snapshot))
        findings[0] = findings[0].model_copy(
            update={
                "verdict": CrossBoundaryQAFindingVerdict.NOT_EVALUATED,
                "severity": FindingSeverity.NOTE,
            }
        )
        policy = request.policy.model_copy(update={"not_evaluated_requires_review": False})
        request = request.model_copy(
            update={
                "result_version_id": VersionId("continuity-qa-policy-v1"),
                "policy": policy,
            }
        )
        artifact = await ContinuityQAService(writer).evaluate(
            request,
            _ContinuityEvaluator(
                ContinuityQAEvaluatorResponse(
                    evaluator_id="fixture-continuity-evaluator",
                    evaluator_version="v1",
                    findings=tuple(findings),
                    aggregate_score=100.0,
                )
            ),
        )
        assert artifact.value.verdict is GateVerdict.PASS
        pointer = await versions.get_current(artifact.ref.logical_id)
        assert pointer is not None and pointer.status is LifecycleState.APPROVED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_default_policy_keeps_pass_result_in_review(tmp_path):
    writer, versions, snapshot, _, request = await _continuity_fixture(tmp_path)
    try:
        policy = CrossBoundaryQAPolicy(policy_version="cross-boundary-qa-default-v1")
        request = request.model_copy(
            update={
                "result_version_id": VersionId("continuity-qa-default-policy-v1"),
                "policy": policy,
            }
        )
        artifact = await ContinuityQAService(writer).evaluate(
            request,
            _ContinuityEvaluator(
                ContinuityQAEvaluatorResponse(
                    evaluator_id="fixture-continuity-evaluator",
                    evaluator_version="v1",
                    findings=_continuity_findings(snapshot=snapshot),
                    aggregate_score=100.0,
                )
            ),
        )
        assert artifact.value.verdict is GateVerdict.PASS
        pointer = await versions.get_current(artifact.ref.logical_id)
        assert pointer is not None and pointer.status is LifecycleState.REVIEW
    finally:
        await writer.close()
