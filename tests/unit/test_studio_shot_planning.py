"""IMP-031 ShotExpansion / ShotListManifest / ShotListItem authority tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    BudgetAllocation,
    BudgetLevel,
    CountRange,
    DependencyGraphRepository,
    CoverageBeatBinding,
    CoverageRequirement,
    CoverageStrategy,
    LifecycleState,
    LogicalId,
    ManifestCoverageSummary,
    NarrativeArtifactType,
    NarrativeTraceState,
    RuntimeRangeSeconds,
    SemanticRecordMetadata,
    ShotBudget,
    ShotExpansionBeatContext,
    ShotExpansionCandidate,
    ShotExpansionRequest,
    ShotListItem,
    ShotListManifest,
    ShotPlanningGateBlocked,
    ShotPlanningIdentityError,
    ShotPlanningRepository,
    ShotPlanningState,
    StructureProfile,
    DurationBudget,
    VersionId,
    VersionRef,
    VersionRepository,
    build_narrative_trace_provenance,
    build_shot_planning_provenance,
    coverage_strategy_logical_id,
    duration_budget_logical_id,
    shot_budget_logical_id,
    shot_list_item_logical_id,
    shot_list_manifest_logical_id,
    structure_profile_logical_id,
)
from agent.studio.persistence import SQLiteWriteOwner
from tests.unit.test_studio_directing import (
    BEAT_REF,
    MACRO_REF,
    NOW,
    PROFILE_REF,
    PROJECT_ID,
    SCENE_REF,
    SCRIPT_LOCK_REF,
    SEQUENCE_REF,
    _beat,
    _create_chain,
    _seed_provenance,
    _seed_version,
    _script_lock,
)


STRUCTURE_REF = VersionRef(
    logical_id=structure_profile_logical_id(PROJECT_ID),
    version_id=VersionId("structure-v1"),
)
DURATION_REF = VersionRef(
    logical_id=duration_budget_logical_id(PROJECT_ID),
    version_id=VersionId("duration-v1"),
)
PLANNER_RULE_REF = VersionRef(
    logical_id=LogicalId("shot-expansion-rule"),
    version_id=VersionId("rule-v1"),
)


def _structure() -> StructureProfile:
    return StructureProfile(
        project_id=PROJECT_ID,
        version_id=STRUCTURE_REF.version_id,
        active_profile_ref=PROFILE_REF,
        project_ref=VersionRef(
            logical_id=LogicalId("project-input:project:film"),
            version_id=VersionId("project-v1"),
        ),
        domain_ref=VersionRef(
            logical_id=LogicalId("niche-resolution:project:film"),
            version_id=VersionId("domain-v1"),
        ),
        format_name="short film",
        genre_niche_label="family drama",
        target_runtime_seconds=20,
        macro_story_beat_count=CountRange(minimum=1, maximum=3),
        sequence_count=CountRange(minimum=1, maximum=3),
        scene_count=CountRange(minimum=1, maximum=4),
        scene_dramatic_beat_count=CountRange(minimum=1, maximum=6),
        runtime_range_seconds=RuntimeRangeSeconds(minimum=10, maximum=120),
        budget_tolerance_seconds=0,
    )


def _duration() -> DurationBudget:
    return DurationBudget(
        project_id=PROJECT_ID,
        version_id=DURATION_REF.version_id,
        active_profile_ref=PROFILE_REF,
        structure_profile_ref=STRUCTURE_REF,
        total_seconds=20,
        tolerance_seconds=0,
        allocations=(
            BudgetAllocation(
                allocation_id="macro-001",
                level=BudgetLevel.MACRO_STORY_BEAT,
                seconds=20,
                target_ref=MACRO_REF,
            ),
            BudgetAllocation(
                allocation_id="sequence-001",
                level=BudgetLevel.SEQUENCE,
                seconds=20,
                parent_allocation_id="macro-001",
                target_ref=SEQUENCE_REF,
            ),
            BudgetAllocation(
                allocation_id="scene-001",
                level=BudgetLevel.SCENE,
                seconds=20,
                parent_allocation_id="sequence-001",
                target_ref=SCENE_REF,
            ),
        ),
    )


def _coverage(blocking_ref: VersionRef, cine_ref: VersionRef, *, version: str = "coverage-v1") -> CoverageStrategy:
    return CoverageStrategy(
        project_id=PROJECT_ID,
        coverage_strategy_id=coverage_strategy_logical_id(PROJECT_ID, SCENE_REF),
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        scene_ref=SCENE_REF,
        duration_budget_ref=DURATION_REF,
        beat_bindings=(
            CoverageBeatBinding(
                scene_dramatic_beat_ref=BEAT_REF,
                blocking_plan_ref=blocking_ref,
                cinematography_objective_ref=cine_ref,
            ),
        ),
        requirements=(
            CoverageRequirement(
                coverage_key="action",
                scene_dramatic_beat_ref=BEAT_REF,
                coverage_function="establish motivated action and spatial crossing",
                viewpoint_intent="Keep the crossing readable before the emotional turn.",
                rationale="The viewer must understand the practical task before the recording disrupts it.",
                continuity_needs=("preserve door-to-desk screen direction",),
                minimum_shots=1,
                maximum_shots=1,
            ),
            CoverageRequirement(
                coverage_key="reaction",
                scene_dramatic_beat_ref=BEAT_REF,
                coverage_function="isolate the aborted stop gesture and emotional reaction",
                viewpoint_intent="Prioritize the reaction when the mother's voice begins.",
                rationale="The beat microchange must be visible rather than narrated.",
                continuity_needs=("preserve cassette position and hand continuity",),
                minimum_shots=1,
                maximum_shots=1,
            ),
        ),
        continuity_needs=("preserve axis and cassette geography",),
        rationale="Two complementary functions cover action then reaction without redundant angles.",
    )


def _budget(coverage_ref: VersionRef, *, version: str = "shot-budget-v1") -> ShotBudget:
    return ShotBudget(
        project_id=PROJECT_ID,
        shot_budget_id=shot_budget_logical_id(PROJECT_ID, SCENE_REF),
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        structure_profile_ref=STRUCTURE_REF,
        duration_budget_ref=DURATION_REF,
        coverage_strategy_ref=coverage_ref,
        scene_ref=SCENE_REF,
        shot_count_range=CountRange(minimum=2, maximum=2),
        shot_duration_range_seconds=RuntimeRangeSeconds(minimum=10, maximum=10),
        scene_duration_seconds=20,
        tolerance_seconds=0,
        rationale="Two ten-second planned shots satisfy the two required coverage functions.",
    )


def _candidate(
    shot_key: str,
    coverage_key: str,
    coverage_function: str,
    dramatic_function: str,
    intent: str,
    *,
    duration: int = 10,
) -> ShotExpansionCandidate:
    return ShotExpansionCandidate(
        shot_key=shot_key,
        scene_dramatic_beat_ref=BEAT_REF,
        coverage_key=coverage_key,
        coverage_function=coverage_function,
        dramatic_function=dramatic_function,
        reason_for_exist=f"{dramatic_function}; this function is not duplicated by the other shot.",
        duration_seconds=duration,
        basic_shot_intent=intent,
        subject_refs=(),
        required_visual_information=("motivated action remains legible",),
        must_preserve=("approved spatial axis",),
    )


def _candidates() -> tuple[ShotExpansionCandidate, ...]:
    return (
        _candidate(
            "shot-a",
            "action",
            "establish motivated action and spatial crossing",
            "Establish the practical crossing before the emotional interruption.",
            "Track the motivated door-to-desk action without decorative camera choice.",
        ),
        _candidate(
            "shot-b",
            "reaction",
            "isolate the aborted stop gesture and emotional reaction",
            "Reveal the beat microchange through the aborted stop gesture.",
            "Prioritize reaction and cassette relation at the reveal threshold.",
        ),
    )


def _request(trace_ref: VersionRef, directing_ref: VersionRef, blocking_ref: VersionRef, cine_ref: VersionRef, *, candidates=None, script_lock_ref: VersionRef = SCRIPT_LOCK_REF) -> ShotExpansionRequest:
    coverage_ref = VersionRef(
        logical_id=coverage_strategy_logical_id(PROJECT_ID, SCENE_REF),
        version_id=VersionId("coverage-v1"),
    )
    budget_ref = VersionRef(
        logical_id=shot_budget_logical_id(PROJECT_ID, SCENE_REF),
        version_id=VersionId("shot-budget-v1"),
    )
    return ShotExpansionRequest(
        project_id=PROJECT_ID,
        active_profile_ref=PROFILE_REF,
        script_lock_ref=script_lock_ref,
        scene_ref=SCENE_REF,
        duration_budget_ref=DURATION_REF,
        coverage_strategy_ref=coverage_ref,
        shot_budget_ref=budget_ref,
        planner_rule_version=PLANNER_RULE_REF,
        beat_contexts=(
            ShotExpansionBeatContext(
                scene_dramatic_beat_ref=BEAT_REF,
                narrative_trace_ref=trace_ref,
                directing_intent_ref=directing_ref,
                blocking_plan_ref=blocking_ref,
                cinematography_objective_ref=cine_ref,
            ),
        ),
        candidates=_candidates() if candidates is None else candidates,
        ordering_rationale="Action coverage precedes reaction coverage to preserve dramatic causality.",
    )


def _planning_prov(value, reason: str):
    return build_shot_planning_provenance(
        value,
        actor_ref="studio:imp031-test",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp031",),
        rule_version=PLANNER_RULE_REF,
        correlation_id="run:imp031",
    )


async def _ready(writer: SQLiteWriteOwner):
    _, trace_ref, _, _, _, directing, _, blocking, cine = await _create_chain(writer)
    versions = VersionRepository(writer)
    structure = _structure()
    duration = _duration()
    await _seed_version(versions, structure.ref, structure.model_dump(mode="json"))
    await _seed_version(versions, duration.ref, duration.model_dump(mode="json"))

    repo = ShotPlanningRepository(writer)
    coverage = _coverage(blocking.ref, cine.ref)
    await repo.create_coverage_strategy(
        value=coverage,
        provenance=_planning_prov(coverage, "create coverage strategy"),
        created_at=NOW,
    )
    budget = _budget(coverage.ref)
    await repo.create_shot_budget(
        value=budget,
        provenance=_planning_prov(budget, "create shot budget"),
        created_at=NOW,
    )
    request = _request(trace_ref, directing.ref, blocking.ref, cine.ref)
    return repo, request, coverage, budget, trace_ref, directing, blocking, cine


async def _expand(repo: ShotPlanningRepository, request: ShotExpansionRequest):
    return await repo.expand_scene(
        request=request,
        shot_item_version=VersionId("shot-v1"),
        shot_trace_version=VersionId("shot-trace-v1"),
        manifest_version=VersionId("manifest-v1"),
        actor_ref="studio:imp031-test",
        reason="expand accepted beat into justified shots",
        recorded_at=NOW,
        source_refs=("evidence:imp031-expansion",),
        correlation_id="run:imp031-expansion",
    )


def test_expansion_candidate_has_no_shot_identity_surface():
    candidate = _candidates()[0]
    assert "shot_id" not in ShotExpansionCandidate.model_fields
    assert "version_id" not in ShotExpansionCandidate.model_fields
    payload = candidate.model_dump(mode="json")
    payload["shot_id"] = "shot-list-item:forbidden"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ShotExpansionCandidate.model_validate(payload)


@pytest.mark.asyncio
async def test_full_expansion_allocates_one_canonical_shot_id_origin_and_current_trace(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, request, _, _, _, _, _, _ = await _ready(writer)
        result = await _expand(repo, request)
        assert len(result.shot_items) == 2
        assert len(result.shot_traces) == 2
        assert result.manifest.value.ordered_shot_refs == tuple(item.ref for item in result.shot_items)
        for candidate, item_artifact, trace_artifact in zip(
            request.candidates, result.shot_items, result.shot_traces, strict=True
        ):
            item = item_artifact.value
            assert isinstance(item, ShotListItem)
            assert item.state is ShotPlanningState.PLANNED
            assert item.shot_id == shot_list_item_logical_id(
                PROJECT_ID, candidate.scene_dramatic_beat_ref, candidate.shot_key
            )
            assert trace_artifact.value.artifact_type is NarrativeArtifactType.SHOT_LIST_ITEM
            assert trace_artifact.value.traced_ref == item.ref
            assert trace_artifact.value.parent_refs == (BEAT_REF,)
            assert await repo.traces.trace_state(trace_artifact.ref) is NarrativeTraceState.CURRENT
            why = await repo.traces.why_exists(trace_artifact.ref)
            assert why.root_story_core_ref.logical_id.root == "story-core:project:film"
            incoming = await repo.graph.list_incoming(item.ref)
            incoming_refs = {edge.source_ref for edge in incoming}
            assert BEAT_REF in incoming_refs
            assert SCENE_REF not in incoming_refs
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_manifest_is_refs_only_projection_and_rejects_shadow_shot_payload(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, request, _, _, _, _, _, _ = await _ready(writer)
        result = await _expand(repo, request)
        manifest = result.manifest.value
        assert isinstance(manifest, ShotListManifest)
        assert "dramatic_function" not in ShotListManifest.model_fields
        assert "basic_shot_intent" not in ShotListManifest.model_fields
        payload = manifest.model_dump(mode="json")
        payload["dramatic_function"] = "shadow truth"
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            ShotListManifest.model_validate(payload)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_expansion_fails_required_coverage_when_one_role_is_duplicated(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, request, _, _, _, _, _, _ = await _ready(writer)
        first = request.candidates[0]
        duplicate_role = first.model_copy(
            update={
                "shot_key": "shot-c",
                "dramatic_function": "Show the same beat from a distinct reaction purpose.",
                "basic_shot_intent": "Hold for a distinct reaction purpose.",
            }
        )
        request = request.model_copy(update={"candidates": (first, duplicate_role)})
        with pytest.raises(ShotPlanningGateBlocked, match="SHOT_MISSING_REQUIRED_COVERAGE"):
            await _expand(repo, request)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_expansion_rejects_semantically_redundant_shot_even_with_distinct_shot_key(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, request, _, _, _, _, _, _ = await _ready(writer)
        first = request.candidates[0]
        redundant = first.model_copy(update={"shot_key": "shot-c"})
        request = request.model_copy(update={"candidates": (first, redundant)})
        with pytest.raises(ShotPlanningGateBlocked, match="duplicate shot"):
            await _expand(repo, request)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_expansion_fails_budget_overflow_before_identity_allocation(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, request, _, _, _, _, _, _ = await _ready(writer)
        changed = request.candidates[0].model_copy(update={"duration_seconds": 11})
        request = request.model_copy(update={"candidates": (changed, request.candidates[1])})
        with pytest.raises(ShotPlanningGateBlocked, match="BUDGET_SHOT_OVERFLOW"):
            await _expand(repo, request)
        assert await repo.versions.get_current(
            shot_list_item_logical_id(PROJECT_ID, BEAT_REF, "shot-a")
        ) is None
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_direct_create_cannot_mark_shot_eligible_before_imp032_gate(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, request, _, _, _, _, _, _ = await _ready(writer)
        candidate = request.candidates[0]
        context = request.beat_contexts[0]
        value = ShotListItem(
            project_id=PROJECT_ID,
            shot_id=shot_list_item_logical_id(PROJECT_ID, BEAT_REF, candidate.shot_key),
            version_id=VersionId("shot-v1"),
            state=ShotPlanningState.ELIGIBLE,
            shot_key=candidate.shot_key,
            active_profile_ref=PROFILE_REF,
            script_lock_ref=SCRIPT_LOCK_REF,
            scene_ref=SCENE_REF,
            parent_scene_dramatic_beat_ref=BEAT_REF,
            narrative_trace_ref=context.narrative_trace_ref,
            directing_intent_ref=context.directing_intent_ref,
            blocking_plan_ref=context.blocking_plan_ref,
            cinematography_objective_ref=context.cinematography_objective_ref,
            coverage_strategy_ref=request.coverage_strategy_ref,
            shot_budget_ref=request.shot_budget_ref,
            duration_budget_ref=DURATION_REF,
            coverage_key=candidate.coverage_key,
            dramatic_function=candidate.dramatic_function,
            coverage_function=candidate.coverage_function,
            reason_for_exist=candidate.reason_for_exist,
            duration_budget_seconds=candidate.duration_seconds,
            basic_shot_intent=candidate.basic_shot_intent,
        )
        with pytest.raises(ShotPlanningGateBlocked, match="eligibility belongs to IMP-032"):
            await repo.create_shot_list_item(
                value=value,
                trace_version=VersionId("premature-trace-v1"),
                provenance=_planning_prov(value, "attempt premature eligibility"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_expansion_rejects_stale_parent_narrative_trace(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, request, _, _, trace_ref, _, _, _ = await _ready(writer)
        old = await repo.traces.get_trace(trace_ref)
        assert old is not None
        pointer = await repo.versions.get_current(old.value.logical_id)
        assert pointer is not None
        successor = old.value.model_copy(update={"trace_version": VersionId("trace-v2")})
        await repo.traces.revise_trace(
            value=successor,
            predecessor=old.ref,
            provenance=build_narrative_trace_provenance(
                successor,
                actor_ref="studio:imp031-test",
                reason="supersede parent trace for stale-input test",
                recorded_at=NOW,
                source_refs=("evidence:imp031-stale-trace",),
            ),
            created_at=NOW,
            expected_revision=pointer.revision,
        )
        with pytest.raises(ShotPlanningGateBlocked, match="NarrativeTrace is stale"):
            await _expand(repo, request)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_unresolved_upstream_invalidation_blocks_current_coverage_consumption(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, request, coverage, _, _, _, _, _ = await _ready(writer)
        duration_v2 = _duration().model_copy(update={"version_id": VersionId("duration-v2")})
        duration_v2_ref = VersionRef(
            logical_id=DURATION_REF.logical_id,
            version_id=duration_v2.version_id,
        )
        await repo.versions.create_successor(
            metadata=SemanticRecordMetadata(
                logical_id=duration_v2_ref.logical_id,
                version_id=duration_v2_ref.version_id,
                predecessor=DURATION_REF,
                provenance=_seed_provenance("duration successor without pointer promotion"),
                created_at=NOW,
            ),
            payload=duration_v2.model_dump(mode="json"),
            supersession_reason="fixture upstream change before current-pointer promotion",
        )
        current = await repo.versions.get_current(DURATION_REF.logical_id)
        assert current is not None and current.version_id == DURATION_REF.version_id
        records = await repo.invalidations.create_for_change(
            cause="DurationBudget changed",
            source_old=DURATION_REF,
            source_new=duration_v2_ref,
            provenance=_seed_provenance("invalidate duration descendants"),
            scope="shot_planning",
            repair_or_recompute_requirement="recompute coverage and shot planning",
        )
        assert any(
            record.affected_object_id == coverage.logical_id
            and record.affected_object_version == coverage.version_id
            for record in records
        )
        with pytest.raises(ShotPlanningGateBlocked, match="unresolved durable invalidation"):
            await _expand(repo, request)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_expansion_rejects_second_parallel_allocation_of_same_shot_ids(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, request, _, _, _, _, _, _ = await _ready(writer)
        await _expand(repo, request)
        with pytest.raises(ShotPlanningIdentityError, match="shot_id already exists"):
            await repo.expand_scene(
                request=request,
                shot_item_version=VersionId("shot-v2"),
                shot_trace_version=VersionId("shot-trace-v2"),
                manifest_version=VersionId("manifest-v2"),
                actor_ref="studio:imp031-test",
                reason="forbidden parallel allocation",
                recorded_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_manifest_rejects_duplicate_dangling_and_stale_members(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, request, _, _, _, _, _, _ = await _ready(writer)
        result = await _expand(repo, request)
        manifest = result.manifest.value
        assert isinstance(manifest, ShotListManifest)

        payload = manifest.model_dump(mode="json")
        payload["ordered_shot_refs"] = [
            result.shot_items[0].ref.model_dump(mode="json"),
            result.shot_items[0].ref.model_dump(mode="json"),
        ]
        with pytest.raises(ValidationError, match="duplicate shot_id"):
            ShotListManifest.model_validate(payload)

        dangling = manifest.model_copy(
            update={
                "version_id": VersionId("manifest-dangling"),
                "ordered_shot_refs": (
                    result.shot_items[0].ref,
                    VersionRef(
                        logical_id=LogicalId("shot-list-item:project:film:deadbeef"),
                        version_id=VersionId("shot-v1"),
                    ),
                ),
            }
        )
        with pytest.raises(ShotPlanningGateBlocked, match="exact version does not exist"):
            await repo.revise_manifest(
                value=dangling,
                predecessor=manifest.ref,
                provenance=_planning_prov(dangling, "dangling member test"),
                created_at=NOW,
                expected_revision=1,
            )

        old_item = result.shot_items[0].value
        assert isinstance(old_item, ShotListItem)
        item_pointer = await repo.versions.get_current(old_item.logical_id)
        assert item_pointer is not None
        successor = old_item.model_copy(
            update={
                "version_id": VersionId("shot-v2"),
                "reason_for_exist": old_item.reason_for_exist + " Revised purpose evidence.",
            }
        )
        revised_item, revised_trace, _ = await repo.revise_shot_list_item(
            value=successor,
            predecessor=old_item.ref,
            trace_version=VersionId("shot-trace-v2"),
            provenance=_planning_prov(successor, "revise shot item"),
            created_at=NOW,
            expected_revision=item_pointer.revision,
        )
        assert revised_trace.value.traced_ref == revised_item.ref
        assert await repo.traces.trace_state(revised_trace.ref) is NarrativeTraceState.CURRENT
        stale_manifest = manifest.model_copy(update={"version_id": VersionId("manifest-stale")})
        with pytest.raises(ShotPlanningGateBlocked, match="not exact current"):
            await repo.revise_manifest(
                value=stale_manifest,
                predecessor=manifest.ref,
                provenance=_planning_prov(stale_manifest, "stale member test"),
                created_at=NOW,
                expected_revision=1,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_expansion_script_lock_must_match_directing_intent_exact_version(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, request, _, _, _, _, _, _ = await _ready(writer)
        old_lock = _script_lock()
        new_lock = old_lock.model_copy(update={"version_id": VersionId("script-lock-v2")})
        new_ref = VersionRef(logical_id=SCRIPT_LOCK_REF.logical_id, version_id=new_lock.version_id)
        pointer = await repo.versions.get_current(SCRIPT_LOCK_REF.logical_id)
        assert pointer is not None
        await repo.versions.create_successor(
            metadata=SemanticRecordMetadata(
                logical_id=new_ref.logical_id,
                version_id=new_ref.version_id,
                predecessor=SCRIPT_LOCK_REF,
                provenance=_seed_provenance("script lock successor fixture"),
                created_at=NOW,
            ),
            payload=new_lock.model_dump(mode="json"),
            supersession_reason="fixture exact ScriptLock mismatch",
        )
        await repo.versions.update_current(
            logical_id=new_ref.logical_id,
            version_id=new_ref.version_id,
            status=LifecycleState.LOCKED,
            expected_revision=pointer.revision,
        )
        request = request.model_copy(update={"script_lock_ref": new_ref})
        with pytest.raises(ShotPlanningGateBlocked, match="exact lineage mismatch"):
            await _expand(repo, request)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_coverage_and_budget_successors_selectively_invalidate_dependents(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, request, coverage, _, _, _, _, _ = await _ready(writer)
        result = await _expand(repo, request)
        pointer = await repo.versions.get_current(coverage.logical_id)
        assert pointer is not None
        coverage_v2 = coverage.model_copy(
            update={
                "version_id": VersionId("coverage-v2"),
                "rationale": coverage.rationale + " Revalidated after editorial coverage review.",
            }
        )
        _, records = await repo.revise_coverage_strategy(
            value=coverage_v2,
            predecessor=coverage.ref,
            provenance=_planning_prov(coverage_v2, "revise coverage"),
            created_at=NOW,
            expected_revision=pointer.revision,
        )
        affected = {(r.affected_object_id.root, r.affected_object_version.root) for r in records}
        assert (request.shot_budget_ref.logical_id.root, request.shot_budget_ref.version_id.root) in affected
        assert (result.manifest.ref.logical_id.root, result.manifest.ref.version_id.root) in affected
        for item in result.shot_items:
            assert (item.ref.logical_id.root, item.ref.version_id.root) in affected
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_coverage_strategy_must_cover_exact_current_scene_beat_set(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, _, coverage, _, _, _, _, _ = await _ready(writer)
        payload = _beat().model_dump(mode="json")
        payload["beat_key"] = "beat-002"
        payload["version_id"] = "beat-v1"
        beat2 = type(_beat()).model_validate(payload)
        await _seed_version(
            repo.versions,
            beat2.ref,
            beat2.model_dump(mode="json"),
        )
        await DependencyGraphRepository(writer).create_edge(
            source=SCENE_REF,
            dependent=beat2.ref,
            edge_type="narrative_hierarchy_input",
            dependency_reason="IMP-031 missing coverage fixture",
            provenance=_seed_provenance("seed second current beat"),
            created_at=NOW,
        )
        pointer = await repo.versions.get_current(coverage.logical_id)
        assert pointer is not None
        coverage_v2 = coverage.model_copy(
            update={
                "version_id": VersionId("coverage-v2"),
                "rationale": coverage.rationale + " Attempt without second beat coverage.",
            }
        )
        with pytest.raises(ShotPlanningGateBlocked, match="SHOT_MISSING_REQUIRED_COVERAGE"):
            await repo.revise_coverage_strategy(
                value=coverage_v2,
                predecessor=coverage.ref,
                provenance=_planning_prov(coverage_v2, "missing beat coverage attempt"),
                created_at=NOW,
                expected_revision=pointer.revision,
            )
    finally:
        await writer.close()


def test_shot_budget_rejects_false_precision_that_cannot_realize_scene_duration():
    coverage_ref = VersionRef(
        logical_id=coverage_strategy_logical_id(PROJECT_ID, SCENE_REF),
        version_id=VersionId("coverage-v1"),
    )
    with pytest.raises(ValidationError, match="BUDGET_SHOT_OVERFLOW"):
        ShotBudget(
            project_id=PROJECT_ID,
            shot_budget_id=shot_budget_logical_id(PROJECT_ID, SCENE_REF),
            version_id=VersionId("bad-budget"),
            active_profile_ref=PROFILE_REF,
            structure_profile_ref=STRUCTURE_REF,
            duration_budget_ref=DURATION_REF,
            coverage_strategy_ref=coverage_ref,
            scene_ref=SCENE_REF,
            shot_count_range=CountRange(minimum=2, maximum=2),
            shot_duration_range_seconds=RuntimeRangeSeconds(minimum=3, maximum=4),
            scene_duration_seconds=20,
            tolerance_seconds=0,
            rationale="Impossible precision fixture.",
        )
