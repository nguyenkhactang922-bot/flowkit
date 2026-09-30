"""IMP-025 canonical narrative hierarchy tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.models.scene import Scene as LegacyFlowKitScene
from agent.studio import (
    BudgetAllocation,
    BudgetLevel,
    CanonicalScene,
    CountRange,
    DurationBudget,
    GateVerdict,
    LifecycleState,
    LogicalId,
    MacroBeatSheet,
    MacroBeatSheetEntry,
    MacroStoryBeat,
    NarrativeHierarchyGateBlocked,
    NarrativeHierarchyIdentityError,
    NarrativeHierarchyRepository,
    Provenance,
    RuntimeRangeSeconds,
    SceneBreakdownEntry,
    SceneBreakdownManifest,
    SceneBudget,
    SceneDramaticBeat,
    SceneListEntry,
    SceneListManifest,
    SemanticRecordMetadata,
    Sequence,
    SequencePlan,
    SequencePlanEntry,
    SequenceSceneAllocation,
    SQLiteWriteOwner,
    StructureProfile,
    VersionId,
    VersionRef,
    VersionRepository,
    build_narrative_hierarchy_provenance,
)
from agent.studio import narrative_hierarchy as narrative_module
from agent.studio.story_core import (
    CausalStoryGraph,
    StoryCoreLockManifest,
    StoryCorePhase,
    StoryCoreVersion,
    StoryGraphEdge,
    StoryGraphEdgeKind,
    StoryGraphNode,
    StoryGraphNodeKind,
    causal_validation_logical_id,
    conflict_logical_id,
    stakes_logical_id,
    story_core_logical_id,
    story_graph_logical_id,
)


NOW = datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc)
PROJECT_ID = LogicalId("project:film")
PROFILE_REF = VersionRef(
    logical_id=LogicalId("active-profile:project:film"),
    version_id=VersionId("profile-v1"),
)
CORE_DRAFT_REF = VersionRef(
    logical_id=story_core_logical_id(PROJECT_ID),
    version_id=VersionId("core-draft-v1"),
)
CORE_FROZEN_REF = VersionRef(
    logical_id=story_core_logical_id(PROJECT_ID),
    version_id=VersionId("core-frozen-v1"),
)
GRAPH_REF = VersionRef(
    logical_id=story_graph_logical_id(PROJECT_ID),
    version_id=VersionId("graph-v1"),
)
CONFLICT_REF = VersionRef(
    logical_id=conflict_logical_id(PROJECT_ID),
    version_id=VersionId("conflict-v1"),
)
STAKES_REF = VersionRef(
    logical_id=stakes_logical_id(PROJECT_ID),
    version_id=VersionId("stakes-v1"),
)
STRUCTURE_REF = VersionRef(
    logical_id=LogicalId("structure-profile:project:film"),
    version_id=VersionId("structure-v1"),
)
DURATION_REF = VersionRef(
    logical_id=LogicalId("duration-budget:project:film"),
    version_id=VersionId("duration-v1"),
)
MACRO_SHEET_REF = VersionRef(
    logical_id=LogicalId("macro-beat-sheet:project:film"),
    version_id=VersionId("macro-sheet-v1"),
)
PROJECT_REF = VersionRef(
    logical_id=LogicalId("project-input:project:film"),
    version_id=VersionId("project-v1"),
)
DOMAIN_REF = VersionRef(
    logical_id=LogicalId("niche-resolution:project:film"),
    version_id=VersionId("domain-v1"),
)

IDEA_REF = VersionRef(
    logical_id=LogicalId("story-idea:project:film"),
    version_id=VersionId("idea-v1"),
)
LOGLINE_REF = VersionRef(
    logical_id=LogicalId("story-logline:project:film"),
    version_id=VersionId("logline-v1"),
)
PREMISE_REF = VersionRef(
    logical_id=LogicalId("story-premise:project:film"),
    version_id=VersionId("premise-v1"),
)
ANGLE_REF = VersionRef(
    logical_id=LogicalId("story-angle:project:film"),
    version_id=VersionId("angle-v1"),
)
THEME_REF = VersionRef(
    logical_id=LogicalId("story-theme:project:film"),
    version_id=VersionId("theme-v1"),
)


def _seed_provenance(reason: str = "IMP-025 upstream seed") -> Provenance:
    return Provenance(
        source_refs=("evidence:imp025-seed",),
        actor_ref="studio:imp025-test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp025",
    )


def _metadata(
    ref: VersionRef,
    *,
    predecessor: VersionRef | None = None,
) -> SemanticRecordMetadata:
    return SemanticRecordMetadata(
        logical_id=ref.logical_id,
        version_id=ref.version_id,
        predecessor=predecessor,
        provenance=_seed_provenance(),
        created_at=NOW,
    )


async def _seed(
    versions: VersionRepository,
    ref: VersionRef,
    *,
    status: LifecycleState,
    payload: dict,
) -> None:
    await versions.create_initial(
        metadata=_metadata(ref),
        payload=payload,
        status=status,
    )


def _frozen_core() -> StoryCoreVersion:
    return StoryCoreVersion(
        project_id=PROJECT_ID,
        version_id=CORE_FROZEN_REF.version_id,
        phase=StoryCorePhase.FROZEN_FOR_STRUCTURE,
        active_profile_ref=PROFILE_REF,
        idea_ref=IDEA_REF,
        logline_ref=LOGLINE_REF,
        premise_ref=PREMISE_REF,
        angle_ref=ANGLE_REF,
        theme_ref=THEME_REF,
        core_goal="Resolve the cassette evidence before deciding the house sale.",
        core_question="Can he face the family truth before the sale deadline?",
        core_conflict="The sale deadline conflicts with the need to investigate.",
        core_stakes="A rushed sale can erase the last chance for truthful closure.",
        lock_manifest=StoryCoreLockManifest(
            draft_ref=CORE_DRAFT_REF,
            story_graph_ref=GRAPH_REF,
            causal_validation_ref=VersionRef(
                logical_id=causal_validation_logical_id(PROJECT_ID),
                version_id=VersionId("validation-v1"),
            ),
            locked_at=NOW,
        ),
    )


def _graph() -> CausalStoryGraph:
    return CausalStoryGraph(
        project_id=PROJECT_ID,
        version_id=GRAPH_REF.version_id,
        story_core_draft_ref=CORE_DRAFT_REF,
        conflict_ref=CONFLICT_REF,
        stakes_ref=STAKES_REF,
        active_profile_ref=PROFILE_REF,
        nodes=(
            StoryGraphNode(
                node_id="cassette",
                kind=StoryGraphNodeKind.REVELATION,
                summary="He hears evidence on the cassette.",
                root_cause=True,
                requires_consequence=True,
            ),
            StoryGraphNode(
                node_id="decision",
                kind=StoryGraphNodeKind.DECISION,
                summary="He delays the sale and confronts the family.",
                major_change=True,
            ),
        ),
        edges=(
            StoryGraphEdge(
                edge_id="edge-1",
                source_node_id="cassette",
                target_node_id="decision",
                kind=StoryGraphEdgeKind.CAUSES,
                rationale="The evidence makes immediate departure impossible.",
            ),
        ),
    )


def _structure_profile() -> StructureProfile:
    return StructureProfile(
        project_id=PROJECT_ID,
        version_id=STRUCTURE_REF.version_id,
        active_profile_ref=PROFILE_REF,
        project_ref=PROJECT_REF,
        domain_ref=DOMAIN_REF,
        format_name="short-film",
        genre_niche_label="family mystery drama",
        target_runtime_seconds=120,
        macro_story_beat_count=CountRange(minimum=2, maximum=3),
        sequence_count=CountRange(minimum=2, maximum=4),
        scene_count=CountRange(minimum=2, maximum=6),
        scene_dramatic_beat_count=CountRange(minimum=2, maximum=8),
        runtime_range_seconds=RuntimeRangeSeconds(minimum=90, maximum=180),
        budget_tolerance_seconds=2,
    )


def _duration_budget() -> DurationBudget:
    return DurationBudget(
        project_id=PROJECT_ID,
        version_id=DURATION_REF.version_id,
        active_profile_ref=PROFILE_REF,
        structure_profile_ref=STRUCTURE_REF,
        total_seconds=120,
        tolerance_seconds=2,
        allocations=(
            BudgetAllocation(
                allocation_id="macro-a",
                level=BudgetLevel.MACRO_STORY_BEAT,
                seconds=60,
            ),
            BudgetAllocation(
                allocation_id="macro-b",
                level=BudgetLevel.MACRO_STORY_BEAT,
                seconds=60,
            ),
            BudgetAllocation(
                allocation_id="seq-a",
                level=BudgetLevel.SEQUENCE,
                parent_allocation_id="macro-a",
                seconds=60,
            ),
            BudgetAllocation(
                allocation_id="seq-b",
                level=BudgetLevel.SEQUENCE,
                parent_allocation_id="macro-b",
                seconds=60,
            ),
        ),
    )


async def _seed_upstream(writer: SQLiteWriteOwner) -> VersionRepository:
    versions = VersionRepository(writer)
    await _seed(
        versions,
        PROFILE_REF,
        status=LifecycleState.LOCKED,
        payload={"profile": "locked"},
    )
    await _seed(
        versions,
        CORE_FROZEN_REF,
        status=LifecycleState.LOCKED,
        payload=_frozen_core().model_dump(mode="json"),
    )
    await _seed(
        versions,
        GRAPH_REF,
        status=LifecycleState.APPROVED,
        payload=_graph().model_dump(mode="json"),
    )
    await _seed(
        versions,
        CONFLICT_REF,
        status=LifecycleState.APPROVED,
        payload={"conflict": "accepted"},
    )
    await _seed(
        versions,
        STAKES_REF,
        status=LifecycleState.APPROVED,
        payload={"stakes": "accepted"},
    )
    await _seed(
        versions,
        STRUCTURE_REF,
        status=LifecycleState.APPROVED,
        payload=_structure_profile().model_dump(mode="json"),
    )
    await _seed(
        versions,
        DURATION_REF,
        status=LifecycleState.APPROVED,
        payload=_duration_budget().model_dump(mode="json"),
    )
    return versions


def _macro(
    beat_key: str,
    version: str,
    *,
    role: str,
    change: str,
    cause: str,
    consequence: str,
) -> MacroStoryBeat:
    return MacroStoryBeat(
        project_id=PROJECT_ID,
        beat_key=beat_key,
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        story_core_ref=CORE_FROZEN_REF,
        story_graph_ref=GRAPH_REF,
        conflict_ref=CONFLICT_REF,
        stakes_ref=STAKES_REF,
        structure_profile_ref=STRUCTURE_REF,
        dramatic_role=role,
        dramatic_change=change,
        cause=cause,
        consequence=consequence,
        structural_necessity_reason="Removing this movement breaks the causal escalation.",
    )


def _prov(value, reason: str) -> Provenance:
    return build_narrative_hierarchy_provenance(
        value,
        actor_ref="studio:imp025",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp025",),
        correlation_id="run:imp025",
    )


async def _ready_hierarchy(writer: SQLiteWriteOwner):
    versions = await _seed_upstream(writer)
    repo = NarrativeHierarchyRepository(writer)

    macro_a = _macro(
        "opening",
        "macro-a-v1",
        role="inciting structural turn",
        change="The cassette turns a routine sale into an investigation.",
        cause="He discovers the cassette.",
        consequence="He delays the sale.",
    )
    macro_b = _macro(
        "confrontation",
        "macro-b-v1",
        role="confrontation/payoff",
        change="Investigation becomes direct family confrontation.",
        cause="The cassette evidence implicates a family decision.",
        consequence="He must redefine what selling the house means.",
    )
    macro_a_art = await repo.create_macro_story_beat(
        value=macro_a,
        provenance=_prov(macro_a, "create macro opening"),
        created_at=NOW,
    )
    macro_b_art = await repo.create_macro_story_beat(
        value=macro_b,
        provenance=_prov(macro_b, "create macro confrontation"),
        created_at=NOW,
    )

    sheet = MacroBeatSheet(
        project_id=PROJECT_ID,
        version_id=MACRO_SHEET_REF.version_id,
        active_profile_ref=PROFILE_REF,
        story_core_ref=CORE_FROZEN_REF,
        structure_profile_ref=STRUCTURE_REF,
        duration_budget_ref=DURATION_REF,
        entries=(
            MacroBeatSheetEntry(
                order_index=0,
                macro_story_beat_ref=macro_a_art.ref,
                duration_allocation_id="macro-a",
            ),
            MacroBeatSheetEntry(
                order_index=1,
                macro_story_beat_ref=macro_b_art.ref,
                duration_allocation_id="macro-b",
            ),
        ),
    )
    await _seed(
        versions,
        MACRO_SHEET_REF,
        status=LifecycleState.APPROVED,
        payload=sheet.model_dump(mode="json"),
    )

    plan = SequencePlan(
        project_id=PROJECT_ID,
        version_id=VersionId("sequence-plan-v1"),
        active_profile_ref=PROFILE_REF,
        structure_profile_ref=STRUCTURE_REF,
        macro_beat_sheet_ref=MACRO_SHEET_REF,
        duration_budget_ref=DURATION_REF,
        entries=(
            SequencePlanEntry(
                plan_entry_id="plan-a",
                order_index=0,
                macro_story_beat_ref=macro_a_art.ref,
                duration_allocation_id="seq-a",
                runtime_budget_seconds=60,
            ),
            SequencePlanEntry(
                plan_entry_id="plan-b",
                order_index=1,
                macro_story_beat_ref=macro_b_art.ref,
                duration_allocation_id="seq-b",
                runtime_budget_seconds=60,
            ),
        ),
        target_count=2,
        runtime_budget_seconds=120,
        causality_evidence=(
            "The investigation sequence is enabled by the cassette discovery.",
            "The confrontation sequence is enabled by the investigation.",
        ),
    )
    plan_art = await repo.create_sequence_plan(
        value=plan,
        provenance=_prov(plan, "create sequence plan"),
        created_at=NOW,
    )

    seq_a = Sequence(
        project_id=PROJECT_ID,
        sequence_key="investigation",
        version_id=VersionId("seq-a-v1"),
        active_profile_ref=PROFILE_REF,
        sequence_plan_ref=plan_art.ref,
        structure_profile_ref=STRUCTURE_REF,
        plan_entry_id="plan-a",
        macro_story_beat_refs=(macro_a_art.ref,),
        objective="Determine what the cassette proves.",
        escalation="Each clue makes the sale deadline more costly to ignore.",
        major_turn="He realizes a relative concealed the cassette deliberately.",
        opening_state="He intends to sell immediately.",
        closing_state="He chooses to delay the sale and investigate.",
        next_sequence_enablement="The discovered concealment forces a confrontation.",
    )
    seq_b = Sequence(
        project_id=PROJECT_ID,
        sequence_key="confrontation",
        version_id=VersionId("seq-b-v1"),
        active_profile_ref=PROFILE_REF,
        sequence_plan_ref=plan_art.ref,
        structure_profile_ref=STRUCTURE_REF,
        plan_entry_id="plan-b",
        macro_story_beat_refs=(macro_b_art.ref,),
        objective="Confront the family decision hidden by the cassette.",
        escalation="Denial gives way to irreversible disclosure.",
        major_turn="The family admits why the truth was buried.",
        opening_state="He enters seeking confirmation.",
        closing_state="He accepts that the sale now carries a moral choice.",
        next_sequence_enablement="The truth enables the final house decision.",
    )
    seq_a_art = await repo.create_sequence(
        value=seq_a,
        provenance=_prov(seq_a, "create investigation sequence"),
        created_at=NOW,
    )
    seq_b_art = await repo.create_sequence(
        value=seq_b,
        provenance=_prov(seq_b, "create confrontation sequence"),
        created_at=NOW,
    )

    scene_budget = SceneBudget(
        project_id=PROJECT_ID,
        version_id=VersionId("scene-budget-v1"),
        active_profile_ref=PROFILE_REF,
        structure_profile_ref=STRUCTURE_REF,
        duration_budget_ref=DURATION_REF,
        sequence_plan_ref=plan_art.ref,
        minimum_scene_count=2,
        preferred_scene_count=2,
        maximum_scene_count=4,
        per_sequence=(
            SequenceSceneAllocation(
                plan_entry_id="plan-a",
                sequence_ref=seq_a_art.ref,
                minimum_scene_count=1,
                preferred_scene_count=1,
                maximum_scene_count=2,
                runtime_seconds=60,
                average_scene_seconds_min=30,
                average_scene_seconds_max=60,
                rationale="One focused investigation scene is sufficient for this fixture.",
            ),
            SequenceSceneAllocation(
                plan_entry_id="plan-b",
                sequence_ref=seq_b_art.ref,
                minimum_scene_count=1,
                preferred_scene_count=1,
                maximum_scene_count=2,
                runtime_seconds=60,
                average_scene_seconds_min=30,
                average_scene_seconds_max=60,
                rationale="One focused confrontation scene is sufficient for this fixture.",
            ),
        ),
        rationale="Two scenes fit the 120 second targeted fixture.",
    )
    scene_budget_art = await repo.create_scene_budget(
        value=scene_budget,
        provenance=_prov(scene_budget, "create scene budget"),
        created_at=NOW,
    )

    scene_a = CanonicalScene(
        project_id=PROJECT_ID,
        scene_key="cassette-room",
        version_id=VersionId("scene-a-v1"),
        active_profile_ref=PROFILE_REF,
        sequence_ref=seq_a_art.ref,
        story_graph_ref=GRAPH_REF,
        scene_budget_ref=scene_budget_art.ref,
        location="Family house living room.",
        time_context="Late afternoon before the buyer deadline.",
        context="He listens alone before calling the family.",
        existence_reason="The cassette must change his immediate sale intention.",
        objective="Understand whether the recording is authentic.",
        opposition="Fear of what the recording will force him to admit.",
        turn="A familiar voice confirms the hidden decision was real.",
        opening_state="He expects a meaningless keepsake.",
        closing_state="He accepts the recording as actionable evidence.",
        change_summary="Doubt becomes a commitment to investigate.",
    )
    scene_b = CanonicalScene(
        project_id=PROJECT_ID,
        scene_key="family-confrontation",
        version_id=VersionId("scene-b-v1"),
        active_profile_ref=PROFILE_REF,
        sequence_ref=seq_b_art.ref,
        story_graph_ref=GRAPH_REF,
        scene_budget_ref=scene_budget_art.ref,
        location="Family house kitchen.",
        time_context="Evening on the same day.",
        context="The family gathers after his phone call.",
        existence_reason="The buried decision must be confronted before the sale.",
        objective="Get a direct admission about the cassette.",
        opposition="A relative insists the past should remain buried.",
        turn="The relative admits the concealment and explains the motive.",
        opening_state="The family denies the recording changes anything.",
        closing_state="The family acknowledges the truth changes the sale decision.",
        change_summary="Denial becomes explicit acknowledgment.",
    )
    scene_a_art = await repo.create_scene(
        value=scene_a,
        provenance=_prov(scene_a, "create cassette scene"),
        created_at=NOW,
    )
    scene_b_art = await repo.create_scene(
        value=scene_b,
        provenance=_prov(scene_b, "create confrontation scene"),
        created_at=NOW,
    )

    list_a = SceneListManifest(
        project_id=PROJECT_ID,
        sequence_key="investigation",
        version_id=VersionId("scene-list-a-v1"),
        active_profile_ref=PROFILE_REF,
        sequence_ref=seq_a_art.ref,
        structure_profile_ref=STRUCTURE_REF,
        scene_budget_ref=scene_budget_art.ref,
        entries=(
            SceneListEntry(
                order_index=0,
                scene_ref=scene_a_art.ref,
                planned_seconds=60,
            ),
        ),
    )
    list_b = SceneListManifest(
        project_id=PROJECT_ID,
        sequence_key="confrontation",
        version_id=VersionId("scene-list-b-v1"),
        active_profile_ref=PROFILE_REF,
        sequence_ref=seq_b_art.ref,
        structure_profile_ref=STRUCTURE_REF,
        scene_budget_ref=scene_budget_art.ref,
        entries=(
            SceneListEntry(
                order_index=0,
                scene_ref=scene_b_art.ref,
                planned_seconds=60,
            ),
        ),
    )
    list_a_art = await repo.create_scene_list_manifest(
        value=list_a,
        provenance=_prov(list_a, "create investigation scene list"),
        created_at=NOW,
    )
    list_b_art = await repo.create_scene_list_manifest(
        value=list_b,
        provenance=_prov(list_b, "create confrontation scene list"),
        created_at=NOW,
    )

    beat_a = SceneDramaticBeat(
        project_id=PROJECT_ID,
        scene_key="cassette-room",
        beat_key="recognition",
        version_id=VersionId("beat-a-v1"),
        active_profile_ref=PROFILE_REF,
        scene_ref=scene_a_art.ref,
        intention="Prove the cassette is irrelevant.",
        action="He replays the recording and isolates the familiar voice.",
        reaction="Recognition stops him from packing the sale documents.",
        resistance="He tries to dismiss the timing as coincidence.",
        cause="The voice matches a memory only his family would know.",
        effect="He accepts the recording deserves investigation.",
        microchange="Dismissal becomes belief.",
    )
    beat_b = SceneDramaticBeat(
        project_id=PROJECT_ID,
        scene_key="family-confrontation",
        beat_key="admission",
        version_id=VersionId("beat-b-v1"),
        active_profile_ref=PROFILE_REF,
        scene_ref=scene_b_art.ref,
        intention="Force a direct answer.",
        action="He plays the key cassette passage to the family.",
        reaction="The relative stops denying the recording.",
        reveal="The relative admits why the cassette was hidden.",
        cause="The exact recorded detail removes plausible denial.",
        effect="The family must discuss the real reason for the sale.",
        microchange="Denial becomes admission.",
    )
    beat_a_art = await repo.create_scene_dramatic_beat(
        value=beat_a,
        provenance=_prov(beat_a, "create recognition beat"),
        created_at=NOW,
    )
    beat_b_art = await repo.create_scene_dramatic_beat(
        value=beat_b,
        provenance=_prov(beat_b, "create admission beat"),
        created_at=NOW,
    )

    breakdown_a = SceneBreakdownManifest(
        project_id=PROJECT_ID,
        scene_key="cassette-room",
        version_id=VersionId("breakdown-a-v1"),
        active_profile_ref=PROFILE_REF,
        scene_ref=scene_a_art.ref,
        scene_list_manifest_ref=list_a_art.ref,
        scene_budget_ref=scene_budget_art.ref,
        entries=(
            SceneBreakdownEntry(
                order_index=0,
                scene_dramatic_beat_ref=beat_a_art.ref,
                planned_seconds=60,
            ),
        ),
    )
    breakdown_b = SceneBreakdownManifest(
        project_id=PROJECT_ID,
        scene_key="family-confrontation",
        version_id=VersionId("breakdown-b-v1"),
        active_profile_ref=PROFILE_REF,
        scene_ref=scene_b_art.ref,
        scene_list_manifest_ref=list_b_art.ref,
        scene_budget_ref=scene_budget_art.ref,
        entries=(
            SceneBreakdownEntry(
                order_index=0,
                scene_dramatic_beat_ref=beat_b_art.ref,
                planned_seconds=60,
            ),
        ),
    )
    breakdown_a_art = await repo.create_scene_breakdown_manifest(
        value=breakdown_a,
        provenance=_prov(breakdown_a, "create recognition breakdown"),
        created_at=NOW,
    )
    breakdown_b_art = await repo.create_scene_breakdown_manifest(
        value=breakdown_b,
        provenance=_prov(breakdown_b, "create confrontation breakdown"),
        created_at=NOW,
    )

    return {
        "versions": versions,
        "repo": repo,
        "macro_a": macro_a_art,
        "macro_b": macro_b_art,
        "plan": plan_art,
        "seq_a": seq_a_art,
        "seq_b": seq_b_art,
        "scene_budget": scene_budget_art,
        "scene_a": scene_a_art,
        "scene_b": scene_b_art,
        "list_a": list_a_art,
        "list_b": list_b_art,
        "beat_a": beat_a_art,
        "beat_b": beat_b_art,
        "breakdown_a": breakdown_a_art,
        "breakdown_b": breakdown_b_art,
    }


def test_no_generic_persistent_beat_and_legacy_scene_is_not_canonical_scene():
    assert not hasattr(narrative_module, "Beat")
    assert CanonicalScene is not LegacyFlowKitScene
    assert "prompt" not in CanonicalScene.model_fields
    assert "video_prompt" not in CanonicalScene.model_fields


def test_scene_requires_state_change_or_explicit_exception():
    with pytest.raises(ValidationError, match="accepted_no_change_purpose"):
        CanonicalScene(
            project_id=PROJECT_ID,
            scene_key="static",
            version_id=VersionId("scene-static-v1"),
            active_profile_ref=PROFILE_REF,
            sequence_ref=VersionRef(
                logical_id=LogicalId("sequence:project:film:test"),
                version_id=VersionId("seq-v1"),
            ),
            story_graph_ref=GRAPH_REF,
            scene_budget_ref=VersionRef(
                logical_id=LogicalId("scene-budget:project:film"),
                version_id=VersionId("scene-budget-v1"),
            ),
            location="Empty room.",
            time_context="Night.",
            context="A pause.",
            existence_reason="Atmosphere.",
            objective="Wait.",
            opposition="Silence.",
            turn="Nothing changes.",
            opening_state="Still.",
            closing_state="Still.",
        )

    valid = CanonicalScene(
        project_id=PROJECT_ID,
        scene_key="atmosphere",
        version_id=VersionId("scene-atmosphere-v1"),
        active_profile_ref=PROFILE_REF,
        sequence_ref=VersionRef(
            logical_id=LogicalId("sequence:project:film:test"),
            version_id=VersionId("seq-v1"),
        ),
        story_graph_ref=GRAPH_REF,
        scene_budget_ref=VersionRef(
            logical_id=LogicalId("scene-budget:project:film"),
            version_id=VersionId("scene-budget-v1"),
        ),
        location="Empty room.",
        time_context="Night.",
        context="A deliberate atmosphere beat.",
        existence_reason="Hold unresolved tension before the confrontation.",
        objective="Hold tension.",
        opposition="Silence.",
        turn="The held silence becomes the point.",
        opening_state="Still.",
        closing_state="Still.",
        accepted_no_change_purpose="Atmosphere/tension hold explicitly accepted.",
    )
    assert valid.accepted_no_change_purpose is not None


def test_scene_dramatic_beat_requires_microchange_and_resistance_or_reveal():
    base = {
        "project_id": PROJECT_ID,
        "scene_key": "cassette-room",
        "beat_key": "test",
        "version_id": VersionId("beat-test-v1"),
        "active_profile_ref": PROFILE_REF,
        "scene_ref": VersionRef(
            logical_id=LogicalId("scene:project:film:cassette-room"),
            version_id=VersionId("scene-a-v1"),
        ),
        "intention": "Understand the recording.",
        "action": "Replay the key line.",
        "reaction": "He recognizes the voice.",
        "cause": "The voice is unmistakable.",
        "effect": "He must investigate.",
        "microchange": "Doubt becomes belief.",
    }
    with pytest.raises(ValidationError, match="resistance or reveal"):
        SceneDramaticBeat(**base)

    with pytest.raises(ValidationError):
        SceneDramaticBeat(
            **{
                **base,
                "resistance": "He still tries to dismiss it.",
                "microchange": " ",
            }
        )


def test_projection_contracts_forbid_narrative_shadow_truth():
    scene_entry = SceneListEntry(
        order_index=0,
        scene_ref=VersionRef(
            logical_id=LogicalId("scene:project:film:test"),
            version_id=VersionId("scene-v1"),
        ),
        planned_seconds=30,
    ).model_dump(mode="python")
    scene_entry["objective"] = "Shadow scene objective"
    with pytest.raises(ValidationError):
        SceneListEntry.model_validate(scene_entry)

    beat_entry = SceneBreakdownEntry(
        order_index=0,
        scene_dramatic_beat_ref=VersionRef(
            logical_id=LogicalId("scene-dramatic-beat:project:film:test:beat"),
            version_id=VersionId("beat-v1"),
        ),
        planned_seconds=15,
    ).model_dump(mode="python")
    beat_entry["microchange"] = "Shadow beat truth"
    with pytest.raises(ValidationError):
        SceneBreakdownEntry.model_validate(beat_entry)

    allocation = SequenceSceneAllocation(
        plan_entry_id="plan-a",
        sequence_ref=VersionRef(
            logical_id=LogicalId("sequence:project:film:test"),
            version_id=VersionId("seq-v1"),
        ),
        minimum_scene_count=1,
        preferred_scene_count=1,
        maximum_scene_count=2,
        runtime_seconds=60,
        average_scene_seconds_min=30,
        average_scene_seconds_max=60,
        rationale="Range only.",
    ).model_dump(mode="python")
    allocation["scene_ref"] = VersionRef(
        logical_id=LogicalId("scene:project:film:forbidden"),
        version_id=VersionId("scene-v1"),
    )
    with pytest.raises(ValidationError):
        SequenceSceneAllocation.model_validate(allocation)


@pytest.mark.asyncio
async def test_full_hierarchy_persists_and_traces_bidirectionally(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        ready = await _ready_hierarchy(writer)
        repo = ready["repo"]

        ancestors = {item.ref for item in await repo.trace_ancestors(ready["beat_a"].ref)}
        assert ready["scene_a"].ref in ancestors
        assert ready["seq_a"].ref in ancestors
        assert ready["macro_a"].ref in ancestors
        assert CORE_FROZEN_REF in ancestors

        descendants = {
            item.ref for item in await repo.trace_descendants(CORE_FROZEN_REF)
        }
        assert ready["macro_a"].ref in descendants
        assert ready["seq_a"].ref in descendants
        assert ready["scene_a"].ref in descendants
        assert ready["beat_a"].ref in descendants

        assert (
            await repo.get_scene_dramatic_beat(ready["beat_a"].ref)
        ).ref == ready["beat_a"].ref
        assert (
            await repo.get_scene(ready["scene_a"].ref)
        ).ref == ready["scene_a"].ref
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_macro_revision_invalidates_dependency_reachable_descendants(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        ready = await _ready_hierarchy(writer)
        repo = ready["repo"]
        old = ready["macro_a"]

        revised = _macro(
            "opening",
            "macro-a-v2",
            role="inciting structural turn",
            change="The cassette forces an even earlier commitment to investigate.",
            cause="He recognizes both the voice and a hidden date.",
            consequence="He immediately suspends the sale.",
        )
        revised_art, invalidations = await repo.revise_macro_story_beat(
            value=revised,
            predecessor=old.ref,
            provenance=_prov(revised, "strengthen causal opening"),
            created_at=NOW,
            expected_revision=1,
        )
        assert revised_art.ref.version_id == VersionId("macro-a-v2")

        affected = {
            VersionRef(
                logical_id=item.affected_object_id,
                version_id=item.affected_object_version,
            )
            for item in invalidations
        }
        assert ready["plan"].ref in affected
        assert ready["seq_a"].ref in affected
        assert ready["scene_a"].ref in affected
        assert ready["beat_a"].ref in affected
        assert ready["breakdown_a"].ref in affected
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_macro_parent_fails_closed_after_successor(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        ready = await _ready_hierarchy(writer)
        repo = ready["repo"]
        old = ready["macro_a"]

        revised = _macro(
            "opening",
            "macro-a-v2",
            role="inciting structural turn",
            change="The cassette forces immediate investigation.",
            cause="The recording includes a unique family fact.",
            consequence="The sale is suspended.",
        )
        await repo.revise_macro_story_beat(
            value=revised,
            predecessor=old.ref,
            provenance=_prov(revised, "replace opening macro"),
            created_at=NOW,
            expected_revision=1,
        )

        stale_sequence = Sequence(
            project_id=PROJECT_ID,
            sequence_key="stale-sequence",
            version_id=VersionId("stale-seq-v1"),
            active_profile_ref=PROFILE_REF,
            sequence_plan_ref=ready["plan"].ref,
            structure_profile_ref=STRUCTURE_REF,
            plan_entry_id="plan-a",
            macro_story_beat_refs=(old.ref,),
            objective="Attempt to use a stale macro.",
            escalation="Should fail before persistence.",
            major_turn="No valid turn.",
            opening_state="Old.",
            closing_state="New.",
            next_sequence_enablement="None.",
        )
        with pytest.raises(
            NarrativeHierarchyGateBlocked,
            match="MacroStoryBeat is not exact current accepted version",
        ):
            await repo.create_sequence(
                value=stale_sequence,
                provenance=_prov(stale_sequence, "stale macro use"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_revision_rejects_historical_noncurrent_predecessor(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        ready = await _ready_hierarchy(writer)
        repo = ready["repo"]
        old = ready["beat_a"]

        v2 = SceneDramaticBeat(
            **{
                **old.value.model_dump(mode="python"),
                "version_id": VersionId("beat-a-v2"),
                "microchange": "Dismissal becomes committed investigation.",
            }
        )
        await repo.revise_scene_dramatic_beat(
            value=v2,
            predecessor=old.ref,
            provenance=_prov(v2, "beat v2"),
            created_at=NOW,
            expected_revision=1,
        )

        v3 = SceneDramaticBeat(
            **{
                **old.value.model_dump(mode="python"),
                "version_id": VersionId("beat-a-v3"),
                "microchange": "Historical fork must fail.",
            }
        )
        with pytest.raises(
            NarrativeHierarchyGateBlocked,
            match="revision predecessor is not exact current accepted version",
        ):
            await repo.revise_scene_dramatic_beat(
                value=v3,
                predecessor=old.ref,
                provenance=_prov(v3, "illegal historical fork"),
                created_at=NOW,
                expected_revision=2,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_manifest_revision_does_not_change_canonical_scene_identity(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        ready = await _ready_hierarchy(writer)
        repo = ready["repo"]
        old_manifest = ready["list_a"]

        revised = SceneListManifest(
            **{
                **old_manifest.value.model_dump(mode="python"),
                "version_id": VersionId("scene-list-a-v2"),
            }
        )
        new_manifest, _ = await repo.revise_scene_list_manifest(
            value=revised,
            predecessor=old_manifest.ref,
            provenance=_prov(revised, "manifest-only successor"),
            created_at=NOW,
            expected_revision=1,
        )

        scene_pointer = await repo.versions.get_current(ready["scene_a"].ref.logical_id)
        assert scene_pointer.version_id == ready["scene_a"].ref.version_id
        assert new_manifest.ref.logical_id == old_manifest.ref.logical_id
        assert new_manifest.ref.version_id != old_manifest.ref.version_id
    finally:
        await writer.close()


def test_project_prefix_collision_is_rejected_for_sequence_and_breakdown_refs():
    with pytest.raises(ValidationError, match="same project"):
        SequencePlan(
            project_id=PROJECT_ID,
            version_id=VersionId("plan-collision"),
            active_profile_ref=PROFILE_REF,
            structure_profile_ref=STRUCTURE_REF,
            macro_beat_sheet_ref=MACRO_SHEET_REF,
            duration_budget_ref=DURATION_REF,
            entries=(
                SequencePlanEntry(
                    plan_entry_id="entry",
                    order_index=0,
                    macro_story_beat_ref=VersionRef(
                        logical_id=LogicalId("macro-story-beat:project:film2:opening"),
                        version_id=VersionId("macro-v1"),
                    ),
                    duration_allocation_id="seq-a",
                    runtime_budget_seconds=120,
                ),
            ),
            target_count=1,
            runtime_budget_seconds=120,
            causality_evidence=("fixture",),
        )

    payload = SceneBreakdownManifest(
        project_id=PROJECT_ID,
        scene_key="cassette-room",
        version_id=VersionId("breakdown-v1"),
        active_profile_ref=PROFILE_REF,
        scene_ref=VersionRef(
            logical_id=LogicalId("scene:project:film:cassette-room"),
            version_id=VersionId("scene-v1"),
        ),
        scene_list_manifest_ref=VersionRef(
            logical_id=LogicalId("scene-list-manifest:project:film:investigation"),
            version_id=VersionId("list-v1"),
        ),
        scene_budget_ref=VersionRef(
            logical_id=LogicalId("scene-budget:project:film"),
            version_id=VersionId("budget-v1"),
        ),
        entries=(
            SceneBreakdownEntry(
                order_index=0,
                scene_dramatic_beat_ref=VersionRef(
                    logical_id=LogicalId(
                        "scene-dramatic-beat:project:film:cassette-room:beat"
                    ),
                    version_id=VersionId("beat-v1"),
                ),
                planned_seconds=30,
            ),
        ),
    ).model_dump(mode="python")
    payload["entries"][0]["scene_dramatic_beat_ref"] = VersionRef(
        logical_id=LogicalId(
            "scene-dramatic-beat:project:film:cassette-room2:beat"
        ),
        version_id=VersionId("beat-v1"),
    )
    with pytest.raises(ValidationError, match="same Scene"):
        SceneBreakdownManifest.model_validate(payload)


@pytest.mark.asyncio
async def test_provenance_must_match_exact_declared_sources(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_upstream(writer)
        repo = NarrativeHierarchyRepository(writer)
        macro = _macro(
            "opening",
            "macro-provenance-v1",
            role="opening",
            change="A change.",
            cause="A cause.",
            consequence="A consequence.",
        )
        bad = Provenance(
            source_refs=("evidence:bad",),
            actor_ref="studio:test",
            reason="wrong sources",
            recorded_at=NOW,
            rule_version=PROFILE_REF,
            correlation_id="run:bad",
        )
        with pytest.raises(
            NarrativeHierarchyIdentityError,
            match="exactly match declared source bindings",
        ):
            await repo.create_macro_story_beat(
                value=macro,
                provenance=bad,
                created_at=NOW,
            )
    finally:
        await writer.close()
