"""IMP-026 tests for dialogue, setup/payoff and screenplay realization."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    AudienceEpistemicState,
    CanonicalScene,
    CausalStoryGraph,
    CharacterEpistemicState,
    CharacterKnowledgeState,
    CharacterModelVersion,
    DialogueIntent,
    EntityKind,
    EntityVersion,
    FullScreenplay,
    GateVerdict,
    KnowledgeItem,
    LifecycleState,
    LogicalId,
    ObjectiveTruth,
    Provenance,
    SceneBreakdownEntry,
    SceneBreakdownManifest,
    SceneDramaticBeat,
    ScreenplayDialogueLine,
    ScreenplayRealizationGateBlocked,
    ScreenplayRealizationIdentityError,
    ScreenplayRealizationRepository,
    ScreenplayScene,
    ScreenplaySceneEntry,
    SemanticRecordMetadata,
    SetupPayoffLink,
    SetupPayoffStatus,
    SQLiteWriteOwner,
    StoryGraphEdge,
    StoryGraphEdgeKind,
    StoryGraphNode,
    StoryGraphNodeKind,
    VersionId,
    VersionRef,
    VersionRepository,
    build_screenplay_provenance,
    character_knowledge_logical_id,
    character_model_logical_id,
    conflict_logical_id,
    scene_breakdown_manifest_logical_id,
    scene_budget_logical_id,
    scene_dramatic_beat_logical_id,
    scene_list_manifest_logical_id,
    scene_logical_id,
    sequence_logical_id,
    stakes_logical_id,
    story_core_logical_id,
    story_graph_logical_id,
)


NOW = datetime(2026, 9, 30, 9, 45, tzinfo=timezone.utc)
PROJECT_ID = LogicalId("project:film")
PROFILE_REF = VersionRef(
    logical_id=LogicalId("active-profile:project:film"),
    version_id=VersionId("profile-v1"),
)
SPEAKER_REF = VersionRef(
    logical_id=LogicalId("entity:hero"),
    version_id=VersionId("hero-v1"),
)
CHARACTER_MODEL_REF = VersionRef(
    logical_id=character_model_logical_id(SPEAKER_REF.logical_id),
    version_id=VersionId("character-model-v1"),
)
KNOWLEDGE_REF = VersionRef(
    logical_id=character_knowledge_logical_id(SPEAKER_REF.logical_id),
    version_id=VersionId("knowledge-v1"),
)
STORY_CORE_DRAFT_REF = VersionRef(
    logical_id=story_core_logical_id(PROJECT_ID),
    version_id=VersionId("story-core-draft-v1"),
)
CONFLICT_REF = VersionRef(
    logical_id=conflict_logical_id(PROJECT_ID),
    version_id=VersionId("conflict-v1"),
)
STAKES_REF = VersionRef(
    logical_id=stakes_logical_id(PROJECT_ID),
    version_id=VersionId("stakes-v1"),
)
GRAPH_REF = VersionRef(
    logical_id=story_graph_logical_id(PROJECT_ID),
    version_id=VersionId("graph-v1"),
)
SEQUENCE_REF = VersionRef(
    logical_id=sequence_logical_id(PROJECT_ID, "seq-1"),
    version_id=VersionId("sequence-v1"),
)
SCENE_BUDGET_REF = VersionRef(
    logical_id=scene_budget_logical_id(PROJECT_ID),
    version_id=VersionId("scene-budget-v1"),
)
SCENE_LIST_REF = VersionRef(
    logical_id=scene_list_manifest_logical_id(PROJECT_ID, "seq-1"),
    version_id=VersionId("scene-list-v1"),
)
SCENE_REF = VersionRef(
    logical_id=scene_logical_id(PROJECT_ID, "scene-1"),
    version_id=VersionId("scene-v1"),
)
BEAT_1_REF = VersionRef(
    logical_id=scene_dramatic_beat_logical_id(
        PROJECT_ID,
        "scene-1",
        "beat-1",
    ),
    version_id=VersionId("beat-1-v1"),
)
BEAT_2_REF = VersionRef(
    logical_id=scene_dramatic_beat_logical_id(
        PROJECT_ID,
        "scene-1",
        "beat-2",
    ),
    version_id=VersionId("beat-2-v1"),
)
BREAKDOWN_REF = VersionRef(
    logical_id=scene_breakdown_manifest_logical_id(PROJECT_ID, "scene-1"),
    version_id=VersionId("breakdown-v1"),
)
EVIDENCE_REF = VersionRef(
    logical_id=LogicalId("story-material:project:film:cassette-evidence"),
    version_id=VersionId("evidence-v1"),
)
EVENT_REF = VersionRef(
    logical_id=LogicalId("story-material:project:film:cassette-discovery"),
    version_id=VersionId("event-v1"),
)


def _seed_provenance(reason: str) -> Provenance:
    return Provenance(
        source_refs=("evidence:imp026-seed",),
        actor_ref="studio:test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp026",
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
        provenance=_seed_provenance("seed exact upstream"),
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


def _entity(*, kind: EntityKind = EntityKind.CHARACTER) -> EntityVersion:
    return EntityVersion(
        entity_id=SPEAKER_REF.logical_id,
        version_id=SPEAKER_REF.version_id,
        kind=kind,
        name="Returning Son",
        project_ids=(PROJECT_ID,),
        slug="returning-son",
    )


def _character_model() -> CharacterModelVersion:
    return CharacterModelVersion(
        project_id=PROJECT_ID,
        character_ref=SPEAKER_REF,
        version_id=CHARACTER_MODEL_REF.version_id,
        active_profile_ref=PROFILE_REF,
        story_core_ref=STORY_CORE_DRAFT_REF,
        role="protagonist",
        external_want="Sell the family house before the deadline.",
        internal_need="Face the unresolved truth about his mother.",
        fear="Losing control of the sale and reopening grief.",
        values=("truth", "family dignity"),
        contradictions=("wants closure but avoids evidence",),
        decision_style="deliberate until family pressure spikes",
        preferred_tactics=("deflect", "ask precise questions"),
    )


def _knowledge() -> CharacterKnowledgeState:
    return CharacterKnowledgeState(
        project_id=PROJECT_ID,
        character_ref=SPEAKER_REF,
        version_id=KNOWLEDGE_REF.version_id,
        sequence_ordinal=0,
        story_time="after cassette discovery",
        items=(
            KnowledgeItem(
                claim_key="claim.mother-left-cassette",
                content="His mother intentionally left the cassette for him.",
                objective_truth=ObjectiveTruth.TRUE,
                character_state=CharacterEpistemicState.KNOWS,
                objective_evidence_refs=(EVIDENCE_REF,),
                source_event_refs=(EVENT_REF,),
                audience_state=AudienceEpistemicState.KNOWS,
            ),
            KnowledgeItem(
                claim_key="claim.buyer-secret",
                content="The buyer secretly caused the family conflict.",
                objective_truth=ObjectiveTruth.UNKNOWN,
                character_state=CharacterEpistemicState.UNKNOWN,
                audience_state=AudienceEpistemicState.UNKNOWN,
            ),
        ),
    )


def _graph(*, include_payoff_edge: bool = True) -> CausalStoryGraph:
    edges = (
        StoryGraphEdge(
            edge_id="edge-setup-payoff",
            source_node_id="setup-cassette",
            target_node_id="payoff-cassette",
            kind=StoryGraphEdgeKind.PAYS_OFF,
            rationale="The hidden cassette recording resolves the planted question.",
        ),
    ) if include_payoff_edge else ()
    return CausalStoryGraph(
        project_id=PROJECT_ID,
        version_id=GRAPH_REF.version_id,
        story_core_draft_ref=STORY_CORE_DRAFT_REF,
        conflict_ref=CONFLICT_REF,
        stakes_ref=STAKES_REF,
        active_profile_ref=PROFILE_REF,
        nodes=(
            StoryGraphNode(
                node_id="setup-cassette",
                kind=StoryGraphNodeKind.SETUP,
                summary="The cassette is planted as unresolved evidence.",
            ),
            StoryGraphNode(
                node_id="payoff-cassette",
                kind=StoryGraphNodeKind.PAYOFF,
                summary="The cassette recording reveals the mother's intent.",
            ),
        ),
        edges=edges,
    )


def _scene(
    *,
    scene_key: str = "scene-1",
    version_id: VersionId = SCENE_REF.version_id,
) -> CanonicalScene:
    return CanonicalScene(
        project_id=PROJECT_ID,
        scene_key=scene_key,
        version_id=version_id,
        active_profile_ref=PROFILE_REF,
        sequence_ref=SEQUENCE_REF,
        story_graph_ref=GRAPH_REF,
        scene_budget_ref=SCENE_BUDGET_REF,
        character_refs=(CHARACTER_MODEL_REF,),
        knowledge_refs=(KNOWLEDGE_REF,),
        location="Old family house",
        time_context="Late afternoon",
        context="He replays the cassette before signing the sale papers.",
        existence_reason="Force the protagonist to confront evidence before the sale.",
        objective="Learn why his mother left the cassette.",
        opposition="He fears delaying the sale and reopening grief.",
        turn="The recording changes the meaning of the house sale.",
        opening_state="He treats the cassette as an inconvenience.",
        closing_state="He treats the cassette as decisive evidence.",
        change_summary="The cassette becomes causally decisive evidence.",
    )


def _beat_1() -> SceneDramaticBeat:
    return SceneDramaticBeat(
        project_id=PROJECT_ID,
        scene_key="scene-1",
        beat_key="beat-1",
        version_id=BEAT_1_REF.version_id,
        active_profile_ref=PROFILE_REF,
        scene_ref=SCENE_REF,
        intention="Get through the recording quickly.",
        action="He presses play and listens while holding the sale papers.",
        reaction="He freezes when his mother addresses him directly.",
        resistance="He reaches to stop the tape.",
        cause="The sale deadline makes him impatient.",
        effect="The direct address stops his attempt to dismiss the recording.",
        microchange="Avoidance becomes reluctant attention.",
    )


def _beat_2() -> SceneDramaticBeat:
    return SceneDramaticBeat(
        project_id=PROJECT_ID,
        scene_key="scene-1",
        beat_key="beat-2",
        version_id=BEAT_2_REF.version_id,
        active_profile_ref=PROFILE_REF,
        scene_ref=SCENE_REF,
        previous_beat_ref=BEAT_1_REF,
        intention="Understand what his mother wanted him to know.",
        action="He rewinds the crucial sentence and listens again.",
        reaction="He sets the sale papers aside.",
        reveal="The recording says the house was meant to preserve evidence.",
        cause="The direct address makes the message personally unavoidable.",
        effect="The sale stops being a purely financial decision.",
        microchange="Reluctant attention becomes a decision to investigate.",
    )


def _breakdown() -> SceneBreakdownManifest:
    return SceneBreakdownManifest(
        project_id=PROJECT_ID,
        scene_key="scene-1",
        version_id=BREAKDOWN_REF.version_id,
        active_profile_ref=PROFILE_REF,
        scene_ref=SCENE_REF,
        scene_list_manifest_ref=SCENE_LIST_REF,
        scene_budget_ref=SCENE_BUDGET_REF,
        entries=(
            SceneBreakdownEntry(
                order_index=0,
                scene_dramatic_beat_ref=BEAT_1_REF,
                planned_seconds=35,
            ),
            SceneBreakdownEntry(
                order_index=1,
                scene_dramatic_beat_ref=BEAT_2_REF,
                planned_seconds=45,
            ),
        ),
    )


async def _seed_context(
    writer: SQLiteWriteOwner,
    *,
    include_payoff_edge: bool = True,
) -> VersionRepository:
    versions = VersionRepository(writer)
    await _seed(
        versions,
        PROFILE_REF,
        status=LifecycleState.LOCKED,
        payload={"profile": "locked"},
    )
    await _seed(
        versions,
        SPEAKER_REF,
        status=LifecycleState.APPROVED,
        payload=_entity().model_dump(mode="json"),
    )
    await _seed(
        versions,
        CHARACTER_MODEL_REF,
        status=LifecycleState.APPROVED,
        payload=_character_model().model_dump(mode="json"),
    )
    await _seed(
        versions,
        KNOWLEDGE_REF,
        status=LifecycleState.APPROVED,
        payload=_knowledge().model_dump(mode="json"),
    )
    await _seed(
        versions,
        GRAPH_REF,
        status=LifecycleState.APPROVED,
        payload=_graph(include_payoff_edge=include_payoff_edge).model_dump(
            mode="json"
        ),
    )
    await _seed(
        versions,
        SCENE_REF,
        status=LifecycleState.APPROVED,
        payload=_scene().model_dump(mode="json"),
    )
    await _seed(
        versions,
        BEAT_1_REF,
        status=LifecycleState.APPROVED,
        payload=_beat_1().model_dump(mode="json"),
    )
    await _seed(
        versions,
        BEAT_2_REF,
        status=LifecycleState.APPROVED,
        payload=_beat_2().model_dump(mode="json"),
    )
    await _seed(
        versions,
        BREAKDOWN_REF,
        status=LifecycleState.APPROVED,
        payload=_breakdown().model_dump(mode="json"),
    )
    return versions


def _dialogue(
    version: str = "dialogue-v1",
    *,
    disclosed_claims: tuple[str, ...] = ("claim.mother-left-cassette",),
) -> DialogueIntent:
    return DialogueIntent(
        project_id=PROJECT_ID,
        scene_key="scene-1",
        beat_key="beat-1",
        intent_key="hero-cassette-response",
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        scene_ref=SCENE_REF,
        scene_dramatic_beat_ref=BEAT_1_REF,
        speaker_character_ref=SPEAKER_REF,
        character_model_ref=CHARACTER_MODEL_REF,
        knowledge_state_ref=KNOWLEDGE_REF,
        communicative_goal="Confirm that the message was meant specifically for him.",
        surface_intent="Ask whether the recording is authentic.",
        subtext="He wants permission to delay the sale without admitting fear.",
        tactic="Frame doubt as a practical verification question.",
        disclosed_claim_keys=disclosed_claims,
        audience_effect="Shift the exchange from logistics to unresolved family truth.",
    )


def _setup_link(
    version: str = "setup-payoff-v1",
    *,
    status: SetupPayoffStatus = SetupPayoffStatus.PAID,
    broken_reason: str | None = None,
) -> SetupPayoffLink:
    if status is SetupPayoffStatus.BROKEN:
        return SetupPayoffLink(
            project_id=PROJECT_ID,
            link_key="cassette-message",
            version_id=VersionId(version),
            active_profile_ref=PROFILE_REF,
            story_graph_ref=GRAPH_REF,
            setup_ref=BEAT_1_REF,
            setup_graph_node_id="setup-cassette",
            status=status,
            broken_reason=broken_reason or "The payoff is missing.",
        )
    return SetupPayoffLink(
        project_id=PROJECT_ID,
        link_key="cassette-message",
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        story_graph_ref=GRAPH_REF,
        setup_ref=BEAT_1_REF,
        setup_graph_node_id="setup-cassette",
        payoff_ref=BEAT_2_REF,
        payoff_graph_node_id="payoff-cassette",
        status=status,
    )


def _screenplay_scene(
    dialogue_ref: VersionRef,
    setup_ref: VersionRef,
    version: str = "screenplay-scene-v1",
    *,
    beat_refs: tuple[VersionRef, ...] = (BEAT_1_REF, BEAT_2_REF),
    realized_claims: tuple[str, ...] = ("claim.mother-left-cassette",),
) -> ScreenplayScene:
    return ScreenplayScene(
        project_id=PROJECT_ID,
        scene_key="scene-1",
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        scene_ref=SCENE_REF,
        scene_breakdown_manifest_ref=BREAKDOWN_REF,
        scene_dramatic_beat_refs=beat_refs,
        dialogue_intent_refs=(dialogue_ref,),
        setup_payoff_refs=(setup_ref,),
        slugline="INT. OLD FAMILY HOUSE - LATE AFTERNOON",
        action_blocks=(
            "He presses PLAY while the unsigned sale papers remain in his hand.",
            "After the message, he sets the papers aside and rewinds the tape.",
        ),
        dialogue_lines=(
            ScreenplayDialogueLine(
                line_id="line-1",
                dialogue_intent_ref=dialogue_ref,
                speaker_character_ref=SPEAKER_REF,
                text="She left this for me. I need to hear the rest.",
                realized_claim_keys=realized_claims,
            ),
        ),
        noncanonical_texture_notes=(
            "A dry click from the cassette button punctuates the silence.",
        ),
    )


def _full_screenplay(
    screenplay_scene_ref: VersionRef,
    setup_ref: VersionRef,
    version: str = "screenplay-v1",
    *,
    scene_ref: VersionRef = SCENE_REF,
    extra_setup_refs: tuple[VersionRef, ...] = (),
) -> FullScreenplay:
    return FullScreenplay(
        project_id=PROJECT_ID,
        screenplay_key="main",
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        entries=(
            ScreenplaySceneEntry(
                order_index=0,
                scene_ref=scene_ref,
                screenplay_scene_ref=screenplay_scene_ref,
            ),
        ),
        setup_payoff_refs=(setup_ref, *extra_setup_refs),
        assembled_text=(
            "INT. OLD FAMILY HOUSE - LATE AFTERNOON\n"
            "He presses PLAY. The message changes the sale decision."
        ),
    )


def _provenance(value, reason: str) -> Provenance:
    return build_screenplay_provenance(
        value,
        actor_ref="studio:imp026",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp026",),
        correlation_id="run:imp026",
    )


async def _ready_pipeline(
    writer: SQLiteWriteOwner,
):
    versions = await _seed_context(writer)
    repo = ScreenplayRealizationRepository(writer)

    dialogue = _dialogue()
    dialogue_artifact = await repo.create_dialogue_intent(
        value=dialogue,
        provenance=_provenance(dialogue, "create dialogue intent"),
        created_at=NOW,
    )

    setup = _setup_link()
    setup_artifact = await repo.create_setup_payoff_link(
        value=setup,
        provenance=_provenance(setup, "create setup payoff link"),
        created_at=NOW,
    )

    scene = _screenplay_scene(dialogue_artifact.ref, setup_artifact.ref)
    scene_artifact = await repo.create_screenplay_scene(
        value=scene,
        provenance=_provenance(scene, "realize screenplay scene"),
        created_at=NOW,
    )

    screenplay = _full_screenplay(scene_artifact.ref, setup_artifact.ref)
    screenplay_artifact = await repo.create_full_screenplay(
        value=screenplay,
        provenance=_provenance(screenplay, "assemble full screenplay"),
        created_at=NOW,
    )

    return (
        versions,
        repo,
        dialogue_artifact,
        setup_artifact,
        scene_artifact,
        screenplay_artifact,
    )


@pytest.mark.asyncio
async def test_full_pipeline_persists_realization_and_traces_exact_ancestry(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        (
            _versions,
            repo,
            dialogue,
            setup,
            scene,
            screenplay,
        ) = await _ready_pipeline(writer)

        ancestors = {
            (item.object_id.root, item.version_id.root)
            for item in await repo.trace_ancestors(screenplay.ref)
        }
        assert (SCENE_REF.logical_id.root, SCENE_REF.version_id.root) in ancestors
        assert (BEAT_1_REF.logical_id.root, BEAT_1_REF.version_id.root) in ancestors
        assert (dialogue.ref.logical_id.root, dialogue.ref.version_id.root) in ancestors
        assert (setup.ref.logical_id.root, setup.ref.version_id.root) in ancestors
        assert (scene.ref.logical_id.root, scene.ref.version_id.root) in ancestors

        current = await repo.versions.get_current(screenplay.ref.logical_id)
        assert current.version_id == screenplay.ref.version_id
        assert current.status is LifecycleState.APPROVED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_dialogue_intent_rejects_unknown_character_knowledge(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_context(writer)
        repo = ScreenplayRealizationRepository(writer)
        dialogue = _dialogue(
            disclosed_claims=("claim.buyer-secret",),
        )
        with pytest.raises(
            ScreenplayRealizationGateBlocked,
            match="cannot use unknown character knowledge",
        ):
            await repo.create_dialogue_intent(
                value=dialogue,
                provenance=_provenance(dialogue, "unknown knowledge leak"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_dialogue_intent_rejects_stale_speaker_entity_version(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_context(writer)
        repo = ScreenplayRealizationRepository(writer)

        speaker_v2 = VersionRef(
            logical_id=SPEAKER_REF.logical_id,
            version_id=VersionId("hero-v2"),
        )
        entity_v2 = _entity().model_copy(update={"version_id": speaker_v2.version_id})
        await versions.create_successor(
            metadata=_metadata(speaker_v2, predecessor=SPEAKER_REF),
            payload=entity_v2.model_dump(mode="json"),
            supersession_reason="entity identity detail revised",
        )
        await versions.update_current(
            logical_id=speaker_v2.logical_id,
            version_id=speaker_v2.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )

        dialogue = _dialogue()
        with pytest.raises(
            ScreenplayRealizationGateBlocked,
            match="speaker EntityVersion is not exact current accepted version",
        ):
            await repo.create_dialogue_intent(
                value=dialogue,
                provenance=_provenance(dialogue, "stale speaker entity"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_setup_payoff_paid_requires_story_graph_pays_off_trace(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_context(writer, include_payoff_edge=False)
        repo = ScreenplayRealizationRepository(writer)
        link = _setup_link()
        with pytest.raises(
            ScreenplayRealizationGateBlocked,
            match="PAYS_OFF edge",
        ):
            await repo.create_setup_payoff_link(
                value=link,
                provenance=_provenance(link, "missing causal payoff trace"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_broken_setup_payoff_link_cannot_enter_screenplay_scene(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_context(writer)
        repo = ScreenplayRealizationRepository(writer)

        dialogue = _dialogue()
        dialogue_artifact = await repo.create_dialogue_intent(
            value=dialogue,
            provenance=_provenance(dialogue, "dialogue"),
            created_at=NOW,
        )
        broken = _setup_link(
            status=SetupPayoffStatus.BROKEN,
            broken_reason="No accepted payoff endpoint exists.",
        )
        broken_artifact = await repo.create_setup_payoff_link(
            value=broken,
            provenance=_provenance(broken, "broken setup/payoff finding"),
            created_at=NOW,
        )
        scene = _screenplay_scene(dialogue_artifact.ref, broken_artifact.ref)
        with pytest.raises(
            ScreenplayRealizationGateBlocked,
            match="cannot accept BROKEN SetupPayoffLink",
        ):
            await repo.create_screenplay_scene(
                value=scene,
                provenance=_provenance(scene, "reject broken payoff"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_screenplay_scene_requires_exact_breakdown_beat_order(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_context(writer)
        repo = ScreenplayRealizationRepository(writer)
        dialogue = _dialogue()
        dialogue_artifact = await repo.create_dialogue_intent(
            value=dialogue,
            provenance=_provenance(dialogue, "dialogue"),
            created_at=NOW,
        )
        setup = _setup_link()
        setup_artifact = await repo.create_setup_payoff_link(
            value=setup,
            provenance=_provenance(setup, "setup/payoff"),
            created_at=NOW,
        )

        incomplete = _screenplay_scene(
            dialogue_artifact.ref,
            setup_artifact.ref,
            beat_refs=(BEAT_1_REF,),
        )
        with pytest.raises(
            ScreenplayRealizationGateBlocked,
            match="exact SceneBreakdownManifest beat order",
        ):
            await repo.create_screenplay_scene(
                value=incomplete,
                provenance=_provenance(incomplete, "omitted accepted beat"),
                created_at=NOW,
            )

        reversed_scene = _screenplay_scene(
            dialogue_artifact.ref,
            setup_artifact.ref,
            version="screenplay-scene-reversed",
            beat_refs=(BEAT_2_REF, BEAT_1_REF),
        )
        with pytest.raises(
            ScreenplayRealizationGateBlocked,
            match="exact SceneBreakdownManifest beat order",
        ):
            await repo.create_screenplay_scene(
                value=reversed_scene,
                provenance=_provenance(reversed_scene, "reordered accepted beats"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_screenplay_dialogue_line_cannot_realize_undisclosed_claim(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_context(writer)
        repo = ScreenplayRealizationRepository(writer)
        dialogue = _dialogue()
        dialogue_artifact = await repo.create_dialogue_intent(
            value=dialogue,
            provenance=_provenance(dialogue, "dialogue"),
            created_at=NOW,
        )
        setup = _setup_link()
        setup_artifact = await repo.create_setup_payoff_link(
            value=setup,
            provenance=_provenance(setup, "setup/payoff"),
            created_at=NOW,
        )
        scene = _screenplay_scene(
            dialogue_artifact.ref,
            setup_artifact.ref,
            realized_claims=("claim.buyer-secret",),
        )
        with pytest.raises(
            ScreenplayRealizationGateBlocked,
            match="claim not disclosed by DialogueIntent",
        ):
            await repo.create_screenplay_scene(
                value=scene,
                provenance=_provenance(scene, "line exceeds intent"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_full_screenplay_rejects_scene_realization_mismatch(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        (
            versions,
            repo,
            _dialogue,
            setup,
            scene,
            _screenplay,
        ) = await _ready_pipeline(writer)

        other_ref = VersionRef(
            logical_id=scene_logical_id(PROJECT_ID, "scene-2"),
            version_id=VersionId("scene-2-v1"),
        )
        other = _scene(
            scene_key="scene-2",
            version_id=other_ref.version_id,
        )
        await _seed(
            versions,
            other_ref,
            status=LifecycleState.APPROVED,
            payload=other.model_dump(mode="json"),
        )

        mismatched = _full_screenplay(
            scene.ref,
            setup.ref,
            version="screenplay-mismatch-v1",
            scene_ref=other_ref,
        )
        with pytest.raises(
            ScreenplayRealizationGateBlocked,
            match="canonical Scene does not match",
        ):
            await repo.create_full_screenplay(
                value=mismatched,
                provenance=_provenance(mismatched, "scene mismatch"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_dialogue_revision_invalidates_scene_and_full_screenplay(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        (
            _versions,
            repo,
            dialogue_v1,
            _setup,
            scene,
            screenplay,
        ) = await _ready_pipeline(writer)

        dialogue_v2 = _dialogue("dialogue-v2")
        _artifact, invalidations = await repo.revise_dialogue_intent(
            value=dialogue_v2,
            predecessor=dialogue_v1.ref,
            provenance=_provenance(dialogue_v2, "refine dialogue intent"),
            created_at=NOW,
            expected_revision=1,
        )
        affected = {
            (item.affected_object_id.root, item.affected_object_version.root)
            for item in invalidations
        }
        assert (scene.ref.logical_id.root, scene.ref.version_id.root) in affected
        assert (
            screenplay.ref.logical_id.root,
            screenplay.ref.version_id.root,
        ) in affected
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_revision_rejects_historical_noncurrent_predecessor(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_context(writer)
        repo = ScreenplayRealizationRepository(writer)
        dialogue_v1 = _dialogue()
        a1 = await repo.create_dialogue_intent(
            value=dialogue_v1,
            provenance=_provenance(dialogue_v1, "v1"),
            created_at=NOW,
        )
        dialogue_v2 = _dialogue("dialogue-v2")
        await repo.revise_dialogue_intent(
            value=dialogue_v2,
            predecessor=a1.ref,
            provenance=_provenance(dialogue_v2, "v2"),
            created_at=NOW,
            expected_revision=1,
        )
        dialogue_v3 = _dialogue("dialogue-v3")
        with pytest.raises(
            ScreenplayRealizationGateBlocked,
            match="revision predecessor is not exact current accepted version",
        ):
            await repo.revise_dialogue_intent(
                value=dialogue_v3,
                predecessor=a1.ref,
                provenance=_provenance(dialogue_v3, "stale fork"),
                created_at=NOW,
                expected_revision=2,
            )
    finally:
        await writer.close()


def test_project_prefix_collision_is_rejected():
    payload = _setup_link().model_dump(mode="python")
    payload["setup_ref"] = VersionRef(
        logical_id=LogicalId("scene:project:film2:scene-1"),
        version_id=VersionId("scene-v1"),
    )
    with pytest.raises(ValidationError, match="same project"):
        SetupPayoffLink.model_validate(payload)


@pytest.mark.asyncio
async def test_provenance_must_match_exact_declared_sources(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_context(writer)
        repo = ScreenplayRealizationRepository(writer)
        dialogue = _dialogue()
        bad = Provenance(
            source_refs=("evidence:wrong",),
            actor_ref="studio:test",
            reason="wrong source bindings",
            recorded_at=NOW,
            rule_version=PROFILE_REF,
            correlation_id="run:bad",
        )
        with pytest.raises(
            ScreenplayRealizationIdentityError,
            match="exactly match declared source bindings",
        ):
            await repo.create_dialogue_intent(
                value=dialogue,
                provenance=bad,
                created_at=NOW,
            )
    finally:
        await writer.close()
