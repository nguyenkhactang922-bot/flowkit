"""IMP-063 tests for defect localization and targeted production repair."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    DefectLocalization,
    DependencyGraphRepository,
    FindingSeverity,
    GateVerdict,
    LifecycleState,
    LogicalId,
    ProductionRepairGateBlocked,
    ProductionRepairIdentityError,
    ProductionRepairMode,
    ProductionRepairRepository,
    ProductionResponsibleLayer,
    Provenance,
    QASourceKind,
    RepairPlan,
    RepairRecheckRequirement,
    SemanticRecordMetadata,
    SQLiteWriteOwner,
    StaticQADimension,
    StaticQAExecutionStatus,
    StaticQAFinding,
    StaticQAFindingVerdict,
    StaticQAResult,
    StaticQASeverity,
    VersionId,
    VersionRef,
    VersionRepository,
    build_production_repair_provenance,
    static_qa_result_logical_id,
)


NOW = datetime(2026, 10, 8, 9, 30, tzinfo=timezone.utc)
PROJECT_ID = LogicalId("project:film")
JOB_ID = LogicalId("generation-job:imp063")
PROFILE_REF = VersionRef(
    logical_id=LogicalId("active-profile:project:film"), version_id=VersionId("profile-v1")
)
RESPONSIBLE_REF = VersionRef(
    logical_id=LogicalId("shot-list-item:project:film:shot-a"), version_id=VersionId("shot-v1")
)
FULL_SPEC_REF = VersionRef(
    logical_id=LogicalId("full-shot-spec:project:film:shot-a"), version_id=VersionId("full-v1")
)
STATIC_SPEC_REF = VersionRef(
    logical_id=LogicalId("static-keyframe-spec:project:film:shot-a"), version_id=VersionId("static-v1")
)
SHOT_IR_REF = VersionRef(
    logical_id=LogicalId("shot-ir:project:film:shot-a"), version_id=VersionId("ir-v1")
)
STATE_REF = VersionRef(
    logical_id=LogicalId("state-snapshot:project:film:state-a"), version_id=VersionId("state-v1")
)
APPROVAL_REF = VersionRef(
    logical_id=LogicalId("approved-end-state:project:film:state-a"), version_id=VersionId("approval-v1")
)
UNRELATED_REF = VersionRef(
    logical_id=LogicalId("static-keyframe-spec:project:film:unrelated"), version_id=VersionId("static-v1")
)
QA_REF = VersionRef(
    logical_id=static_qa_result_logical_id(PROJECT_ID, JOB_ID), version_id=VersionId("qa-v1")
)


def _seed_provenance(reason: str = "seed IMP-063 exact source") -> Provenance:
    return Provenance(
        source_refs=("evidence:imp063-seed",),
        actor_ref="studio:imp063-test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp063",
    )


def _metadata(
    ref: VersionRef,
    *,
    predecessor: VersionRef | None = None,
    provenance: Provenance | None = None,
) -> SemanticRecordMetadata:
    return SemanticRecordMetadata(
        logical_id=ref.logical_id,
        version_id=ref.version_id,
        predecessor=predecessor,
        provenance=provenance or _seed_provenance(),
        created_at=NOW,
    )


async def _seed(
    versions: VersionRepository,
    ref: VersionRef,
    *,
    status: LifecycleState = LifecycleState.APPROVED,
    payload: dict | None = None,
) -> None:
    await versions.create_initial(
        metadata=_metadata(ref),
        payload=payload or {"fixture_ref": ref.logical_id.root},
        status=status,
    )


def _static_findings() -> tuple[StaticQAFinding, ...]:
    return tuple(
        StaticQAFinding(
            dimension=dimension,
            verdict=(
                StaticQAFindingVerdict.FAIL
                if dimension is StaticQADimension.IDENTITY
                else StaticQAFindingVerdict.PASS
            ),
            severity=(
                StaticQASeverity.BLOCKING
                if dimension is StaticQADimension.IDENTITY
                else StaticQASeverity.LOW
            ),
            confidence=0.98,
            reason_code=("IDENTITY_DRIFT" if dimension is StaticQADimension.IDENTITY else f"PASS_{dimension.value}"),
            explanation=f"fixture {dimension.value}",
            evidence_refs=(f"evidence:imp063:{dimension.value.lower()}",),
            source_refs=(RESPONSIBLE_REF,) if dimension is StaticQADimension.IDENTITY else (),
        )
        for dimension in StaticQADimension
    )


def _qa_result(*, version: str = "qa-v1") -> StaticQAResult:
    return StaticQAResult(
        project_id=PROJECT_ID,
        qa_result_id=QA_REF.logical_id,
        version_id=VersionId(version),
        generation_job_id=JOB_ID,
        artifact_id=LogicalId("artifact:project:film:shot-a"),
        artifact_event_id="artifact-event:imp063",
        artifact_content_sha256="sha256:abc123",
        artifact_byte_count=123,
        media_type="image/png",
        shot_ir_ref=SHOT_IR_REF,
        static_keyframe_spec_ref=STATIC_SPEC_REF,
        full_shot_spec_ref=FULL_SPEC_REF,
        state_snapshot_ref=STATE_REF,
        approved_state_designation_ref=APPROVAL_REF,
        active_profile_ref=PROFILE_REF,
        evaluator_id="fixture-static-evaluator",
        evaluator_version="static-evaluator-v1",
        policy_version="static-policy-v1",
        execution_status=StaticQAExecutionStatus.COMPLETED,
        findings=_static_findings(),
        aggregate_score=99.0,
        verdict=GateVerdict.FAIL,
        evaluated_at=NOW,
    )


async def _fixture(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    versions = VersionRepository(writer)
    graph = DependencyGraphRepository(writer)

    for ref, status in (
        (PROFILE_REF, LifecycleState.LOCKED),
        (RESPONSIBLE_REF, LifecycleState.APPROVED),
        (FULL_SPEC_REF, LifecycleState.APPROVED),
        (STATIC_SPEC_REF, LifecycleState.APPROVED),
        (SHOT_IR_REF, LifecycleState.APPROVED),
        (STATE_REF, LifecycleState.LOCKED),
        (APPROVAL_REF, LifecycleState.APPROVED),
        (UNRELATED_REF, LifecycleState.APPROVED),
    ):
        await _seed(versions, ref, status=status)

    qa = _qa_result()
    await _seed(
        versions,
        qa.ref,
        status=LifecycleState.REVIEW,
        payload=qa.model_dump(mode="json"),
    )

    provenance = _seed_provenance("bind exact production dependency chain")
    for source, dependent, edge_type in (
        (RESPONSIBLE_REF, FULL_SPEC_REF, "shot_planning_to_full_spec"),
        (FULL_SPEC_REF, STATIC_SPEC_REF, "full_spec_to_static_spec"),
        (STATIC_SPEC_REF, SHOT_IR_REF, "static_spec_to_shot_ir"),
        (SHOT_IR_REF, qa.ref, "shot_ir_to_static_qa"),
        (STATE_REF, qa.ref, "state_to_static_qa"),
        (APPROVAL_REF, qa.ref, "approval_to_static_qa"),
        (RESPONSIBLE_REF, qa.ref, "finding_source_to_static_qa"),
    ):
        await graph.create_edge(
            source=source,
            dependent=dependent,
            edge_type=edge_type,
            dependency_reason="IMP-063 fixture lineage",
            provenance=provenance,
            created_at=NOW,
        )

    return writer, versions, graph, qa


def _localization(
    *,
    responsible_ref: VersionRef = RESPONSIBLE_REF,
    responsible_layer: ProductionResponsibleLayer = ProductionResponsibleLayer.SHOT_PLANNING,
    version: str = "localization-v1",
) -> DefectLocalization:
    return DefectLocalization(
        project_id=PROJECT_ID,
        localization_key="identity-drift-shot-a",
        version_id=VersionId(version),
        qa_kind=QASourceKind.STATIC,
        qa_result_ref=QA_REF,
        finding_dimension=StaticQADimension.IDENTITY.value,
        defect_code="IDENTITY_DRIFT",
        registry_version="production-defects-v1",
        detector_version="static-evaluator-v1",
        responsible_ref=responsible_ref,
        responsible_layer=responsible_layer,
        preserve_refs=(STATE_REF,),
        invalidation_candidate_refs=(FULL_SPEC_REF,),
        evidence_refs=("evidence:imp063:identity", "diagnosis:shot-a"),
        confidence=0.95,
        explanation=(
            "Identity drift manifests in the rendered/static QA result, while exact lineage "
            "localizes the earliest responsible source to the ShotListItem planning branch."
        ),
    )


def _repair(
    localization_ref: VersionRef,
    *,
    preserve_refs: tuple[VersionRef, ...] = (STATE_REF,),
    recheck: tuple[RepairRecheckRequirement, ...] | None = None,
    version: str = "repair-v1",
) -> RepairPlan:
    return RepairPlan(
        project_id=PROJECT_ID,
        repair_key="identity-drift-shot-a",
        version_id=VersionId(version),
        localization_ref=localization_ref,
        mode=ProductionRepairMode.PATCH_IN_PLACE,
        patch_refs=(RESPONSIBLE_REF,),
        preserve_refs=preserve_refs,
        invalidate_refs=(FULL_SPEC_REF,),
        recheck=(
            recheck
            if recheck is not None
            else (
                RepairRecheckRequirement(
                    qa_kind=QASourceKind.STATIC,
                    scope_refs=(RESPONSIBLE_REF, FULL_SPEC_REF),
                    reason="Re-run Static QA after the repaired successor is materialized.",
                ),
            )
        ),
        planner_version="production-repair-planner-v1",
        expected_resolution="Correct identity drift without changing approved state truth.",
        cost_constraint="Prefer minimum dependency scope before broader regeneration.",
    )


@pytest.mark.asyncio
async def test_localization_uses_exact_qa_finding_and_persists_stable_code(tmp_path):
    writer, _versions, _graph, _qa = await _fixture(tmp_path)
    try:
        repo = ProductionRepairRepository(writer)
        value = _localization()
        artifact = await repo.create_localization(
            value=value,
            provenance=build_production_repair_provenance(
                value,
                actor_ref="studio:imp063-test",
                reason="localize exact production defect",
                recorded_at=NOW,
                source_refs=("evidence:imp063-localization",),
                correlation_id="run:imp063",
            ),
            created_at=NOW,
        )
        assert artifact.value.defect_code == "IDENTITY_DRIFT"
        assert artifact.value.registry_version == "production-defects-v1"
        assert "defect-registry:production-defects-v1" in artifact.metadata.provenance.source_refs
        assert "detector:static-evaluator-v1" in artifact.metadata.provenance.source_refs
        assert artifact.value.responsible_ref == RESPONSIBLE_REF
        assert artifact.value.responsible_layer is ProductionResponsibleLayer.SHOT_PLANNING
        ancestors = await repo.trace_ancestors(artifact.ref)
        assert any(item.ref == QA_REF for item in ancestors)
        assert any(item.ref == RESPONSIBLE_REF for item in ancestors)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_manual_provenance_without_registry_and_detector_markers_is_rejected(tmp_path):
    writer, _versions, _graph, _qa = await _fixture(tmp_path)
    try:
        repo = ProductionRepairRepository(writer)
        value = _localization()
        provenance = Provenance(
            source_versions=value.source_bindings(),
            source_refs=("evidence:manual-provenance",),
            actor_ref="studio:imp063-test",
            reason="attempt localization without pinned version evidence",
            recorded_at=NOW,
            correlation_id="run:imp063",
        )
        with pytest.raises(ProductionRepairIdentityError, match="registry/detector/planner version evidence"):
            await repo.create_localization(
                value=value,
                provenance=provenance,
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_wrong_layer_localization_rejected_even_when_identity_prefix_is_valid(tmp_path):
    writer, _versions, _graph, _qa = await _fixture(tmp_path)
    try:
        repo = ProductionRepairRepository(writer)
        value = _localization(
            responsible_ref=UNRELATED_REF,
            responsible_layer=ProductionResponsibleLayer.STATIC_KEYFRAME_SPEC,
        )
        with pytest.raises(ProductionRepairGateBlocked, match="cited finding source or exact ancestor"):
            await repo.create_localization(
                value=value,
                provenance=build_production_repair_provenance(
                    value,
                    actor_ref="studio:imp063-test",
                    reason="reject wrong repair layer",
                    recorded_at=NOW,
                    source_refs=("evidence:wrong-layer",),
                ),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_connected_but_downstream_manifestation_layer_is_rejected(tmp_path):
    writer, _versions, _graph, _qa = await _fixture(tmp_path)
    try:
        repo = ProductionRepairRepository(writer)
        value = _localization(
            responsible_ref=FULL_SPEC_REF,
            responsible_layer=ProductionResponsibleLayer.FULL_SHOT_SPEC,
        )
        with pytest.raises(
            ProductionRepairGateBlocked,
            match="cited finding source or exact ancestor",
        ):
            await repo.create_localization(
                value=value,
                provenance=build_production_repair_provenance(
                    value,
                    actor_ref="studio:imp063-test",
                    reason="reject downstream manifestation layer as root cause",
                    recorded_at=NOW,
                    source_refs=("evidence:downstream-manifestation",),
                ),
                created_at=NOW,
            )
    finally:
        await writer.close()


def test_responsible_layer_identity_mismatch_fails_schema_before_persistence():
    with pytest.raises(ValidationError, match="responsible_layer"):
        _localization(responsible_layer=ProductionResponsibleLayer.STATIC_KEYFRAME_SPEC)


@pytest.mark.asyncio
async def test_repair_plan_must_preserve_exact_diagnosed_preserve_set(tmp_path):
    writer, _versions, _graph, _qa = await _fixture(tmp_path)
    try:
        repo = ProductionRepairRepository(writer)
        localization = _localization()
        localized = await repo.create_localization(
            value=localization,
            provenance=build_production_repair_provenance(
                localization,
                actor_ref="studio:imp063-test",
                reason="localize before preserve regression test",
                recorded_at=NOW,
                source_refs=("evidence:preserve-localization",),
            ),
            created_at=NOW,
        )
        plan = _repair(localized.ref, preserve_refs=())
        with pytest.raises(ProductionRepairGateBlocked, match="exact diagnosed preserve set"):
            await repo.create_repair_plan(
                value=plan,
                provenance=build_production_repair_provenance(
                    plan,
                    actor_ref="studio:imp063-test",
                    reason="reject preserve-set regression",
                    recorded_at=NOW,
                    source_refs=("evidence:preserve-regression",),
                ),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_repair_plan_requires_originating_qa_family_recheck(tmp_path):
    writer, _versions, _graph, _qa = await _fixture(tmp_path)
    try:
        repo = ProductionRepairRepository(writer)
        localization = _localization()
        localized = await repo.create_localization(
            value=localization,
            provenance=build_production_repair_provenance(
                localization,
                actor_ref="studio:imp063-test",
                reason="localize before recheck test",
                recorded_at=NOW,
                source_refs=("evidence:recheck-localization",),
            ),
            created_at=NOW,
        )
        plan = _repair(
            localized.ref,
            recheck=(
                RepairRecheckRequirement(
                    qa_kind=QASourceKind.MOTION,
                    scope_refs=(RESPONSIBLE_REF,),
                    reason="Motion-only recheck is insufficient for a Static QA defect.",
                ),
            ),
        )
        with pytest.raises(ProductionRepairGateBlocked, match="originating QA family"):
            await repo.create_repair_plan(
                value=plan,
                provenance=build_production_repair_provenance(
                    plan,
                    actor_ref="studio:imp063-test",
                    reason="reject missing originating QA recheck",
                    recorded_at=NOW,
                    source_refs=("evidence:mandatory-recheck",),
                ),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_valid_repair_plan_persists_minimum_scope_without_provider_side_effect(tmp_path):
    writer, _versions, _graph, _qa = await _fixture(tmp_path)
    try:
        repo = ProductionRepairRepository(writer)
        localization = _localization()
        localized = await repo.create_localization(
            value=localization,
            provenance=build_production_repair_provenance(
                localization,
                actor_ref="studio:imp063-test",
                reason="localize before valid repair",
                recorded_at=NOW,
                source_refs=("evidence:valid-localization",),
            ),
            created_at=NOW,
        )
        plan = _repair(localized.ref)
        artifact = await repo.create_repair_plan(
            value=plan,
            provenance=build_production_repair_provenance(
                plan,
                actor_ref="studio:imp063-test",
                reason="persist minimum-scope production repair plan",
                recorded_at=NOW,
                source_refs=("evidence:valid-repair",),
            ),
            created_at=NOW,
        )
        assert artifact.value.mode is ProductionRepairMode.PATCH_IN_PLACE
        assert artifact.value.patch_refs == (RESPONSIBLE_REF,)
        assert artifact.value.preserve_refs == (STATE_REF,)
        assert artifact.value.invalidate_refs == (FULL_SPEC_REF,)
        assert artifact.value.recheck[0].qa_kind is QASourceKind.STATIC
        assert "repair-planner:production-repair-planner-v1" in artifact.metadata.provenance.source_refs
        assert "prompt_suffix" not in RepairPlan.model_fields
        descendants = await repo.trace_descendants(localized.ref)
        assert any(item.ref == artifact.ref for item in descendants)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_qa_result_cannot_be_reused_for_new_localization(tmp_path):
    writer, versions, _graph, qa_v1 = await _fixture(tmp_path)
    try:
        qa_v2 = _qa_result(version="qa-v2")
        successor_ref = qa_v2.ref
        await versions.create_successor(
            metadata=_metadata(
                successor_ref,
                predecessor=qa_v1.ref,
                provenance=_seed_provenance("supersede stale QA evidence"),
            ),
            payload=qa_v2.model_dump(mode="json"),
            supersession_reason="new evaluator run",
        )
        await versions.update_current(
            logical_id=qa_v1.logical_id,
            version_id=qa_v2.version_id,
            status=LifecycleState.REVIEW,
            expected_revision=0,
        )

        repo = ProductionRepairRepository(writer)
        value = _localization()
        with pytest.raises(ProductionRepairGateBlocked, match="exact current version"):
            await repo.create_localization(
                value=value,
                provenance=build_production_repair_provenance(
                    value,
                    actor_ref="studio:imp063-test",
                    reason="reject stale QA localization",
                    recorded_at=NOW,
                    source_refs=("evidence:stale-qa",),
                ),
                created_at=NOW,
            )
    finally:
        await writer.close()
