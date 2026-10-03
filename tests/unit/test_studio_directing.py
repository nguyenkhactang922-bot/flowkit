"""IMP-030 Audience/Directing/Spatial/Blocking/Cinematography authority tests."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    ActiveProductionProfile,
    ActorDirection,
    AudienceExperienceTarget,
    BlockingMovement,
    BlockingPlan,
    BlockingPosition,
    CinematographyDimension,
    CinematographyObjective,
    CharacterModelVersion,
    DependencyGraphRepository,
    DirectingAuthorityError,
    DirectingAuthorityRepository,
    DirectingGateBlocked,
    DirectingIdentityError,
    DirectingIntent,
    EmotionTarget,
    EntityKind,
    EntityVersion,
    ExperienceShift,
    LifecycleState,
    LogicalId,
    NarrativeArtifactType,
    NarrativeTraceRecord,
    NarrativeTraceRepository,
    Provenance,
    CanonicalScene,
    SceneDramaticBeat,
    SceneSpatialDramaticContract,
    ScriptApprovalPolicy,
    ScriptLockManifest,
    SemanticRecordMetadata,
    SourceVersionBinding,
    SpatialAnchor,
    SpatialZone,
    StateFact,
    StateFactNamespace,
    StateSnapshot,
    StateSnapshotRepository,
    VersionId,
    VersionRef,
    VersionRepository,
    VisualDecisionBasis,
    audience_experience_target_logical_id,
    blocking_plan_logical_id,
    build_directing_provenance,
    build_narrative_trace_provenance,
    build_state_snapshot_provenance,
    cinematography_objective_logical_id,
    character_model_logical_id,
    directing_intent_logical_id,
    locked_refs_digest,
    scene_budget_logical_id,
    scene_dramatic_beat_logical_id,
    scene_logical_id,
    scene_spatial_contract_logical_id,
    state_snapshot_logical_id,
    story_graph_logical_id,
)
from agent.studio.persistence import SQLiteWriteOwner


NOW = datetime(2026, 10, 3, 8, 30, tzinfo=timezone.utc)
PROJECT_ID = LogicalId("project:film")
PROFILE_REF = VersionRef(
    logical_id=LogicalId("active-profile:project:film"),
    version_id=VersionId("profile-v1"),
)
ENTITY_REF = VersionRef(
    logical_id=LogicalId("entity:legacy-char-001"),
    version_id=VersionId("entity-v1"),
)
OTHER_ENTITY_REF = VersionRef(
    logical_id=LogicalId("entity:legacy-char-other"),
    version_id=VersionId("entity-v1"),
)
EXTRA_ENTITY_REF = VersionRef(
    logical_id=LogicalId("entity:legacy-char-extra"),
    version_id=VersionId("entity-v1"),
)
CHAR_MODEL_REF = VersionRef(
    logical_id=character_model_logical_id(ENTITY_REF.logical_id),
    version_id=VersionId("character-model-v1"),
)
STORY_CORE_REF = VersionRef(
    logical_id=LogicalId("story-core:project:film"),
    version_id=VersionId("story-v1"),
)
MACRO_REF = VersionRef(
    logical_id=LogicalId("macro-story-beat:project:film:macro-001"),
    version_id=VersionId("macro-v1"),
)
SEQUENCE_REF = VersionRef(
    logical_id=LogicalId("sequence:project:film:seq-001"),
    version_id=VersionId("sequence-v1"),
)
SCENE_REF = VersionRef(
    logical_id=scene_logical_id(PROJECT_ID, "scene-001"),
    version_id=VersionId("scene-v1"),
)
BEAT_REF = VersionRef(
    logical_id=scene_dramatic_beat_logical_id(PROJECT_ID, "scene-001", "beat-001"),
    version_id=VersionId("beat-v1"),
)
SCRIPT_LOCK_REF = VersionRef(
    logical_id=LogicalId("script-lock:project:film"),
    version_id=VersionId("script-lock-v1"),
)
FULL_SCREENPLAY_REF = VersionRef(
    logical_id=LogicalId("screenplay:project:film:full"),
    version_id=VersionId("screenplay-v1"),
)
QUALITY_REF = VersionRef(
    logical_id=LogicalId("story-quality:project:film:full"),
    version_id=VersionId("quality-v1"),
)
CHANGE_REF = VersionRef(
    logical_id=LogicalId("accepted-change:project:film:beat-001"),
    version_id=VersionId("change-v1"),
)
OUTCOME_REF = VersionRef(
    logical_id=LogicalId("shot-outcome:project:film:beat-000"),
    version_id=VersionId("outcome-v1"),
)
QA_REF = VersionRef(
    logical_id=LogicalId("qa-result:project:film:state-001"),
    version_id=VersionId("qa-v1"),
)
APPROVAL_POLICY_REF = VersionRef(
    logical_id=LogicalId("approval-policy:project:film"),
    version_id=VersionId("policy-v1"),
)
UNRELATED_REF = VersionRef(
    logical_id=LogicalId("unrelated:project:film"),
    version_id=VersionId("unrelated-v1"),
)


def _seed_provenance(reason: str = "IMP-030 fixture seed") -> Provenance:
    return Provenance(
        source_refs=("evidence:imp030-fixture",),
        actor_ref="studio:imp030-test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp030-test",
    )


async def _seed_version(
    versions: VersionRepository,
    ref: VersionRef,
    payload: dict,
    *,
    status: LifecycleState = LifecycleState.APPROVED,
) -> None:
    await versions.create_initial(
        metadata=SemanticRecordMetadata(
            logical_id=ref.logical_id,
            version_id=ref.version_id,
            provenance=_seed_provenance(),
            created_at=NOW,
        ),
        payload=payload,
        status=status,
    )


def _profile() -> ActiveProductionProfile:
    empty_policy_hash = "sha256:" + hashlib.sha256(b"{}").hexdigest()
    zero_hash = "sha256:" + "0" * 64
    return ActiveProductionProfile(
        profile_id=PROFILE_REF.logical_id,
        profile_version=PROFILE_REF.version_id,
        project_id=PROJECT_ID,
        resolver_version=VersionRef(
            logical_id=LogicalId("profile-resolver"),
            version_id=VersionId("resolver-v1"),
        ),
        profile_resolution_ref=VersionRef(
            logical_id=LogicalId("profile-resolution:project:film"),
            version_id=VersionId("resolution-v1"),
        ),
        resolution_id=LogicalId("resolution-run:project:film"),
        project_ref=VersionRef(
            logical_id=PROJECT_ID,
            version_id=VersionId("project-v1"),
        ),
        topic_ref=VersionRef(
            logical_id=LogicalId("topic:project:film"),
            version_id=VersionId("topic-v1"),
        ),
        domain_ref=VersionRef(
            logical_id=LogicalId("domain:project:film"),
            version_id=VersionId("domain-v1"),
        ),
        effective_pack_refs=(),
        policy_entries=(),
        input_fingerprint=zero_hash,
        effective_policy_hash=empty_policy_hash,
        resolution_trace_hash=zero_hash,
    )


def _entity(ref: VersionRef = ENTITY_REF, *, project_id: LogicalId = PROJECT_ID) -> EntityVersion:
    return EntityVersion(
        entity_id=ref.logical_id,
        version_id=ref.version_id,
        kind=EntityKind.CHARACTER,
        name="Lan" if ref == ENTITY_REF else "Other",
        project_ids=(project_id,),
        description="Canonical entity for IMP-030 fixture.",
    )



def _character_model() -> CharacterModelVersion:
    return CharacterModelVersion(
        project_id=PROJECT_ID,
        character_ref=ENTITY_REF,
        version_id=CHAR_MODEL_REF.version_id,
        active_profile_ref=PROFILE_REF,
        story_core_ref=STORY_CORE_REF,
        role="returning son",
        external_want="Sell the family house without reopening old grief.",
        internal_need="Accept that memory cannot be handled as disposable property.",
        fear="Losing emotional control if he listens to the recording.",
        decision_style="Practical avoidance until direct evidence forces engagement.",
    )

def _scene() -> CanonicalScene:
    return CanonicalScene(
        project_id=PROJECT_ID,
        scene_key="scene-001",
        version_id=SCENE_REF.version_id,
        active_profile_ref=PROFILE_REF,
        sequence_ref=SEQUENCE_REF,
        story_graph_ref=VersionRef(
            logical_id=story_graph_logical_id(PROJECT_ID),
            version_id=VersionId("graph-v1"),
        ),
        scene_budget_ref=VersionRef(
            logical_id=scene_budget_logical_id(PROJECT_ID),
            version_id=VersionId("scene-budget-v1"),
        ),
        character_refs=(CHAR_MODEL_REF,),
        relationship_refs=(),
        knowledge_refs=(),
        location="Old family house",
        time_context="Late afternoon",
        context="The return home turns into a confrontation with memory.",
        existence_reason="Force the protagonist to choose whether to sell the house.",
        objective="Open the locked room and face the unresolved decision.",
        opposition="The protagonist resists the emotional cost of remembering.",
        turn="The cassette begins playing the mother's recorded voice.",
        opening_state="Detached and determined to sell.",
        closing_state="Shaken and willing to reconsider.",
        change_summary="The cassette converts avoidance into active engagement.",
    )


def _beat(version: str = "beat-v1") -> SceneDramaticBeat:
    return SceneDramaticBeat(
        project_id=PROJECT_ID,
        scene_key="scene-001",
        beat_key="beat-001",
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        scene_ref=SCENE_REF,
        intention="Stay emotionally detached while inspecting the room.",
        action="He presses play on the cassette despite hesitation.",
        reaction="His posture freezes when his mother's voice begins.",
        resistance="He reaches to stop the tape but cannot complete the motion.",
        reveal=None,
        cause="The sale requires clearing the room before the buyer arrives.",
        effect="The recording disrupts the plan to treat the house as property only.",
        microchange="Detachment gives way to involuntary attention.",
    )


def _script_lock() -> ScriptLockManifest:
    locked = (STORY_CORE_REF, FULL_SCREENPLAY_REF)
    return ScriptLockManifest(
        project_id=PROJECT_ID,
        version_id=SCRIPT_LOCK_REF.version_id,
        active_profile_ref=PROFILE_REF,
        story_core_ref=STORY_CORE_REF,
        full_screenplay_ref=FULL_SCREENPLAY_REF,
        quality_result_ref=QUALITY_REF,
        approval_policy=ScriptApprovalPolicy.AUTOMATED_PASS_ALLOWED,
        approval_ref=None,
        locked_refs=locked,
        locked_versions_digest=locked_refs_digest(locked),
    )


async def _seed_narrative_and_trace(writer: SQLiteWriteOwner) -> VersionRef:
    versions = VersionRepository(writer)
    graph = DependencyGraphRepository(writer)
    await _seed_version(
        versions,
        PROFILE_REF,
        _profile().model_dump(mode="json"),
        status=LifecycleState.LOCKED,
    )
    await _seed_version(
        versions,
        ENTITY_REF,
        _entity().model_dump(mode="json"),
    )
    await _seed_version(
        versions,
        OTHER_ENTITY_REF,
        _entity(OTHER_ENTITY_REF, project_id=LogicalId("project:other")).model_dump(mode="json"),
    )
    await _seed_version(
        versions,
        EXTRA_ENTITY_REF,
        _entity(EXTRA_ENTITY_REF).model_dump(mode="json"),
    )
    await _seed_version(
        versions,
        STORY_CORE_REF,
        {"fixture": "locked story core"},
        status=LifecycleState.LOCKED,
    )
    await _seed_version(
        versions,
        CHAR_MODEL_REF,
        _character_model().model_dump(mode="json"),
    )
    await _seed_version(versions, MACRO_REF, {"fixture": "macro"})
    await _seed_version(versions, SEQUENCE_REF, {"fixture": "sequence"})
    await _seed_version(versions, SCENE_REF, _scene().model_dump(mode="json"))
    await _seed_version(versions, BEAT_REF, _beat().model_dump(mode="json"))
    await _seed_version(versions, FULL_SCREENPLAY_REF, {"fixture": "screenplay"})
    await _seed_version(versions, QUALITY_REF, {"fixture": "quality"})
    await _seed_version(
        versions,
        SCRIPT_LOCK_REF,
        _script_lock().model_dump(mode="json"),
        status=LifecycleState.LOCKED,
    )
    await _seed_version(versions, UNRELATED_REF, {"fixture": "unrelated"})

    for source, dependent in (
        (STORY_CORE_REF, MACRO_REF),
        (MACRO_REF, SEQUENCE_REF),
        (SEQUENCE_REF, SCENE_REF),
        (SCENE_REF, BEAT_REF),
    ):
        await graph.create_edge(
            source=source,
            dependent=dependent,
            edge_type="narrative_hierarchy_input",
            dependency_reason="IMP-030 narrative fixture ancestry",
            provenance=_seed_provenance("seed narrative ancestry"),
            created_at=NOW,
        )

    trace = NarrativeTraceRecord(
        project_id=PROJECT_ID,
        artifact_type=NarrativeArtifactType.SCENE_DRAMATIC_BEAT,
        trace_version=VersionId("trace-v1"),
        traced_ref=BEAT_REF,
        root_story_core_ref=STORY_CORE_REF,
        parent_refs=(SCENE_REF,),
        source_version_refs=(),
    )
    artifact = await NarrativeTraceRepository(writer).create_trace(
        value=trace,
        provenance=build_narrative_trace_provenance(
            trace,
            actor_ref="studio:imp030-test",
            reason="seed current beat narrative trace",
            recorded_at=NOW,
            source_refs=("evidence:imp030-trace",),
        ),
        created_at=NOW,
    )
    return artifact.ref


async def _seed_approved_state(writer: SQLiteWriteOwner):
    versions = VersionRepository(writer)
    for ref in (CHANGE_REF, OUTCOME_REF, QA_REF, APPROVAL_POLICY_REF):
        await _seed_version(versions, ref, {"fixture": ref.logical_id.root})

    snapshot = StateSnapshot(
        project_id=PROJECT_ID,
        state_snapshot_id=state_snapshot_logical_id(PROJECT_ID, "scene-001-end"),
        version_id=VersionId("state-v1"),
        scope_key="scene-001-end",
        story_time="T+00:08",
        facts=(
            StateFact(
                namespace=StateFactNamespace.WARDROBE,
                key="upper_body",
                value_json='{"description":"cream shirt"}',
                subject_ref=ENTITY_REF,
            ),
            StateFact(
                namespace=StateFactNamespace.ENVIRONMENT,
                key="room_light",
                value_json='{"condition":"late-afternoon-window-light"}',
            ),
        ),
        source_outcome_ref=OUTCOME_REF,
        change_refs=(CHANGE_REF,),
    )
    repo = StateSnapshotRepository(writer)
    await repo.create_initial(
        snapshot=snapshot,
        provenance=build_state_snapshot_provenance(
            snapshot,
            actor_ref="studio:imp030-test",
            reason="seed candidate state",
            recorded_at=NOW,
            source_refs=("evidence:imp030-state",),
        ),
        created_at=NOW,
    )
    result = await repo.approve_end_state(
        snapshot_ref=snapshot.ref,
        designation_version=VersionId("state-approval-v1"),
        qa_result_ref=QA_REF,
        approval_policy_ref=APPROVAL_POLICY_REF,
        source_outcome_ref=OUTCOME_REF,
        actor_ref="approval:imp030-test",
        reason="approve state for directing continuity",
        recorded_at=NOW,
        expected_snapshot_revision=0,
        correlation_id="run:imp030-state-approval",
    )
    return snapshot, result.designation.ref


async def _seed_context(writer: SQLiteWriteOwner):
    trace_ref = await _seed_narrative_and_trace(writer)
    state, designation_ref = await _seed_approved_state(writer)
    return trace_ref, state, designation_ref


def _audience(trace_ref: VersionRef, *, version: str = "aud-v1") -> AudienceExperienceTarget:
    return AudienceExperienceTarget(
        project_id=PROJECT_ID,
        audience_experience_target_id=audience_experience_target_logical_id(PROJECT_ID, BEAT_REF),
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        scene_dramatic_beat_ref=BEAT_REF,
        narrative_trace_ref=trace_ref,
        primary_emotion=EmotionTarget(name="unease", target_intensity=0.8),
        secondary_emotions=(EmotionTarget(name="nostalgia", target_intensity=0.5),),
        tension=ExperienceShift(before=0.3, after=0.7),
        curiosity=ExperienceShift(before=0.4, after=0.9),
        viewer_effects=("feel the cost of avoidance", "notice the cassette as causal object"),
        must_understand=("the recording destabilizes his plan",),
        must_not_yet_understand=("the full content of the message",),
        expected_question="What did his mother leave on the tape?",
        expected_wait="Hold the answer until the next beat.",
        desired_uncertainty=0.7,
        desired_release=0.2,
        attention_primary="His aborted attempt to stop the tape.",
        attention_secondary=("The untouched sale papers on the desk.",),
        forbidden_experience=("decorative sentimentality without dramatic pressure",),
    )


def _directing(audience_ref: VersionRef, *, version: str = "direct-v1") -> DirectingIntent:
    return DirectingIntent(
        project_id=PROJECT_ID,
        directing_intent_id=directing_intent_logical_id(PROJECT_ID, BEAT_REF),
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        script_lock_ref=SCRIPT_LOCK_REF,
        scene_dramatic_beat_ref=BEAT_REF,
        audience_experience_target_ref=audience_ref,
        performance_state_refs=(),
        performance_objective="Show resistance breaking without verbal explanation.",
        actor_directions=(
            ActorDirection(
                entity_ref=ENTITY_REF,
                posture="Rigid shoulders that soften only after the voice starts.",
                gaze="Avoid the cassette, then lock onto it.",
                breathing="Shallow before playback; held breath on first word.",
                gesture="Hand reaches for stop and stalls midway.",
                tempo="Controlled then suspended.",
                restraint_level="High restraint; no overt crying.",
            ),
        ),
        reveal=("The voice matters immediately to him.",),
        withhold=("Why he avoided the room for years.",),
        attention_primary="The incomplete stop gesture.",
        attention_secondary="The cassette recorder.",
        hold_before_action_seconds=0.6,
        hold_after_action_seconds=1.1,
        incoming_transition_intent="Enter on practical task energy.",
        outgoing_transition_intent="Leave on unresolved listening pressure.",
    )


def _spatial(
    state_ref: VersionRef,
    designation_ref: VersionRef,
    *,
    version: str = "spatial-v1",
) -> SceneSpatialDramaticContract:
    return SceneSpatialDramaticContract(
        project_id=PROJECT_ID,
        spatial_contract_id=scene_spatial_contract_logical_id(PROJECT_ID, SCENE_REF),
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        scene_ref=SCENE_REF,
        scene_dramatic_beat_refs=(BEAT_REF,),
        state_snapshot_ref=state_ref,
        approved_state_designation_ref=designation_ref,
        participant_entity_refs=(ENTITY_REF,),
        topology="Small rectangular bedroom connected to hallway by one doorway.",
        zones=(
            SpatialZone(zone_key="door", description="Threshold to hallway."),
            SpatialZone(zone_key="desk", description="Desk with cassette and sale papers."),
        ),
        entrances=("door",),
        exits=("door",),
        anchors=(
            SpatialAnchor(
                anchor_key="cassette",
                description="Cassette recorder on desk; dramatic causal anchor.",
            ),
        ),
        sightline_constraints=("From door, cassette is visible but tape label is not readable.",),
        dramatic_constraints=("Character must cross from door zone to desk zone before playback.",),
        axis_policy="Preserve door-to-desk orientation through the beat.",
    )


def _blocking(
    directing_ref: VersionRef,
    spatial_ref: VersionRef,
    state_ref: VersionRef,
    designation_ref: VersionRef,
    *,
    version: str = "blocking-v1",
    start_zone: str = "door",
    entity_ref: VersionRef = ENTITY_REF,
) -> BlockingPlan:
    return BlockingPlan(
        project_id=PROJECT_ID,
        blocking_plan_id=blocking_plan_logical_id(PROJECT_ID, BEAT_REF),
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        scene_dramatic_beat_ref=BEAT_REF,
        directing_intent_ref=directing_ref,
        spatial_contract_ref=spatial_ref,
        state_snapshot_ref=state_ref,
        approved_state_designation_ref=designation_ref,
        positions=(
            BlockingPosition(
                entity_ref=entity_ref,
                start_zone=start_zone,
                end_zone="desk",
                facing="Toward desk, body angled away from cassette until action turn.",
            ),
        ),
        movements=(
            BlockingMovement(
                entity_ref=entity_ref,
                path="door -> desk",
                motivation="Complete the practical clearing task while avoiding emotional engagement.",
            ),
        ),
        eyelines=("Eyes avoid cassette until playback begins.",),
        distance_changes=("Closes distance from threshold to arm's reach of cassette.",),
        dramatic_object_interactions=("Press play; begin stop gesture; abort stop gesture.",),
        must_preserve=("Cassette remains on desk throughout beat.",),
        forbidden_moves=("Do not leave the room before the voice is heard.",),
    )


def _bases(
    audience_ref: VersionRef,
    directing_ref: VersionRef,
    spatial_ref: VersionRef,
    blocking_ref: VersionRef,
) -> tuple[VisualDecisionBasis, ...]:
    return (
        VisualDecisionBasis(
            dimension=CinematographyDimension.FRAMING,
            rationale="Keep aborted gesture and cassette in readable dramatic relation.",
            source_refs=(audience_ref, directing_ref),
        ),
        VisualDecisionBasis(
            dimension=CinematographyDimension.SPATIAL,
            rationale="Respect door-to-desk geography and readable crossing.",
            source_refs=(spatial_ref, blocking_ref),
        ),
        VisualDecisionBasis(
            dimension=CinematographyDimension.PERSPECTIVE,
            rationale="Stay aligned with the protagonist's resistance rather than omniscient sentimentality.",
            source_refs=(audience_ref, directing_ref),
        ),
        VisualDecisionBasis(
            dimension=CinematographyDimension.MOVEMENT,
            rationale="Visual movement follows the actor's motivated crossing, not decorative camera motion.",
            source_refs=(blocking_ref,),
        ),
        VisualDecisionBasis(
            dimension=CinematographyDimension.FOCUS,
            rationale="Attention transfers from task behavior to cassette when the voice begins.",
            source_refs=(audience_ref, directing_ref),
        ),
        VisualDecisionBasis(
            dimension=CinematographyDimension.LIGHTING,
            rationale="Preserve state continuity while supporting late-afternoon emotional pressure.",
            source_refs=(PROFILE_REF, spatial_ref),
        ),
        VisualDecisionBasis(
            dimension=CinematographyDimension.COMPOSITION,
            rationale="Use room geography and blocked position to preserve the cassette as pressure point.",
            source_refs=(spatial_ref, blocking_ref),
        ),
    )


def _cine(
    audience_ref: VersionRef,
    directing_ref: VersionRef,
    spatial_ref: VersionRef,
    blocking_ref: VersionRef,
    *,
    version: str = "cine-v1",
) -> CinematographyObjective:
    return CinematographyObjective(
        project_id=PROJECT_ID,
        cinematography_objective_id=cinematography_objective_logical_id(PROJECT_ID, BEAT_REF),
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        scene_dramatic_beat_ref=BEAT_REF,
        audience_experience_target_ref=audience_ref,
        directing_intent_ref=directing_ref,
        spatial_contract_ref=spatial_ref,
        blocking_plan_ref=blocking_ref,
        visual_goal="Translate resistance breaking into increasingly unavoidable visual attention.",
        emotional_goal="Move the viewer from practical distance into contained unease.",
        framing_strategy="Keep gesture, face orientation and cassette relation legible.",
        spatial_strategy="Preserve door-to-desk geography as the dramatic crossing.",
        perspective_strategy="Stay subjectively aligned with reluctant attention.",
        movement_strategy="Only respond to motivated blocking; avoid decorative drift.",
        focus_strategy="Transfer attention to the cassette at the reveal threshold.",
        lighting_strategy="Preserve approved room state while increasing perceived isolation through staging.",
        composition_strategy="Maintain the cassette as a pressure anchor rather than a beauty object.",
        continuity_constraints=("Preserve approved StateSnapshot wardrobe and room-light facts.",),
        decision_bases=_bases(audience_ref, directing_ref, spatial_ref, blocking_ref),
    )


def _prov(value, reason: str) -> Provenance:
    return build_directing_provenance(
        value,
        actor_ref="studio:imp030-test",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp030",),
        correlation_id="run:imp030",
    )


async def _create_chain(writer: SQLiteWriteOwner):
    trace_ref, state, designation_ref = await _seed_context(writer)
    repo = DirectingAuthorityRepository(writer)
    audience = _audience(trace_ref)
    await repo.create_audience_experience_target(
        value=audience,
        provenance=_prov(audience, "create audience target"),
        created_at=NOW,
    )
    directing = _directing(audience.ref)
    await repo.create_directing_intent(
        value=directing,
        provenance=_prov(directing, "create directing intent"),
        created_at=NOW,
    )
    spatial = _spatial(state.ref, designation_ref)
    await repo.create_spatial_contract(
        value=spatial,
        provenance=_prov(spatial, "create spatial contract"),
        created_at=NOW,
    )
    blocking = _blocking(directing.ref, spatial.ref, state.ref, designation_ref)
    await repo.create_blocking_plan(
        value=blocking,
        provenance=_prov(blocking, "create blocking plan"),
        created_at=NOW,
    )
    cine = _cine(audience.ref, directing.ref, spatial.ref, blocking.ref)
    await repo.create_cinematography_objective(
        value=cine,
        provenance=_prov(cine, "create cinematography objective"),
        created_at=NOW,
    )
    return repo, trace_ref, state, designation_ref, audience, directing, spatial, blocking, cine


@pytest.mark.asyncio
async def test_full_dramatic_to_camera_chain_is_exact_and_provider_neutral(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, _, _, _, audience, directing, spatial, blocking, cine = await _create_chain(writer)
        pointer = await repo.versions.get_current(cine.logical_id)
        assert pointer is not None
        assert pointer.version_id == cine.version_id
        assert pointer.status is LifecycleState.APPROVED

        ancestors = await repo.trace_ancestors(cine.ref)
        ancestor_refs = {item.ref for item in ancestors}
        assert audience.ref in ancestor_refs
        assert directing.ref in ancestor_refs
        assert spatial.ref in ancestor_refs
        assert blocking.ref in ancestor_refs
        assert BEAT_REF in ancestor_refs
        assert PROFILE_REF in ancestor_refs

        field_names = set(CinematographyObjective.model_fields)
        assert "lens_mm" not in field_names
        assert "camera_angle" not in field_names
        assert "provider" not in field_names
        assert "prompt" not in field_names
    finally:
        await writer.close()


def test_audience_rejects_generic_cinematic_style_and_conflicting_information():
    trace_ref = VersionRef(
        logical_id=LogicalId("narrative-trace:scene_dramatic_beat:fixture"),
        version_id=VersionId("trace-v1"),
    )
    with pytest.raises(ValidationError, match="generic cinematic"):
        _audience(trace_ref).model_copy(
            update={"viewer_effects": ("cinematic",)}
        ).model_validate(
            {
                **_audience(trace_ref).model_dump(mode="json"),
                "viewer_effects": ["cinematic"],
            }
        )

    payload = _audience(trace_ref).model_dump(mode="json")
    payload["must_understand"] = ["the tape matters"]
    payload["must_not_yet_understand"] = ["the tape matters"]
    with pytest.raises(ValidationError, match="both understand"):
        AudienceExperienceTarget.model_validate(payload)


@pytest.mark.asyncio
async def test_audience_requires_exact_current_narrative_trace(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        trace_ref, _, _ = await _seed_context(writer)
        trace_repo = NarrativeTraceRepository(writer)
        original = await trace_repo.get_trace(trace_ref)
        assert original is not None
        extra_ref = VersionRef(
            logical_id=LogicalId("story-material:project:film:trace-extra"),
            version_id=VersionId("extra-v1"),
        )
        await _seed_version(VersionRepository(writer), extra_ref, {"fixture": "extra"})
        successor = original.value.model_copy(
            update={
                "trace_version": VersionId("trace-v2"),
                "source_version_refs": (extra_ref,),
            }
        )
        pointer = await trace_repo.versions.get_current(original.value.logical_id)
        assert pointer is not None
        await trace_repo.revise_trace(
            value=successor,
            predecessor=trace_ref,
            provenance=build_narrative_trace_provenance(
                successor,
                actor_ref="studio:imp030-test",
                reason="supersede trace evidence",
                recorded_at=NOW,
                source_refs=("evidence:imp030-trace-v2",),
            ),
            created_at=NOW,
            expected_revision=pointer.revision,
        )

        repo = DirectingAuthorityRepository(writer)
        audience = _audience(trace_ref)
        with pytest.raises(DirectingGateBlocked, match="NarrativeTrace"):
            await repo.create_audience_experience_target(
                value=audience,
                provenance=_prov(audience, "stale trace attempt"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_directing_requires_locked_script_lock(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        trace_ref, _, _ = await _seed_context(writer)
        repo = DirectingAuthorityRepository(writer)
        audience = _audience(trace_ref)
        await repo.create_audience_experience_target(
            value=audience,
            provenance=_prov(audience, "create audience"),
            created_at=NOW,
        )
        pointer = await repo.versions.get_current(SCRIPT_LOCK_REF.logical_id)
        assert pointer is not None
        await repo.versions.update_current(
            logical_id=SCRIPT_LOCK_REF.logical_id,
            version_id=SCRIPT_LOCK_REF.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=pointer.revision,
        )

        directing = _directing(audience.ref)
        with pytest.raises(DirectingGateBlocked, match="ScriptLock"):
            await repo.create_directing_intent(
                value=directing,
                provenance=_prov(directing, "unlocked script attempt"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_directing_rejects_cross_project_actor_entity(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        trace_ref, _, _ = await _seed_context(writer)
        repo = DirectingAuthorityRepository(writer)
        audience = _audience(trace_ref)
        await repo.create_audience_experience_target(
            value=audience,
            provenance=_prov(audience, "create audience"),
            created_at=NOW,
        )
        directing = _directing(audience.ref).model_copy(
            update={
                "actor_directions": (
                    ActorDirection(entity_ref=OTHER_ENTITY_REF, gesture="Reach toward table."),
                )
            }
        )
        with pytest.raises(DirectingGateBlocked, match="different project"):
            await repo.create_directing_intent(
                value=directing,
                provenance=_prov(directing, "cross project actor attempt"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_directing_rejects_same_project_actor_not_declared_by_scene(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        trace_ref, _, _ = await _seed_context(writer)
        repo = DirectingAuthorityRepository(writer)
        audience = _audience(trace_ref)
        await repo.create_audience_experience_target(
            value=audience,
            provenance=_prov(audience, "create audience"),
            created_at=NOW,
        )
        directing = _directing(audience.ref).model_copy(
            update={
                "actor_directions": (
                    ActorDirection(entity_ref=EXTRA_ENTITY_REF, gesture="Cross into frame."),
                )
            }
        )
        with pytest.raises(DirectingGateBlocked, match="not declared by canonical Scene"):
            await repo.create_directing_intent(
                value=directing,
                provenance=_prov(directing, "undeclared same-project actor attempt"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_spatial_rejects_same_project_participant_not_declared_by_scene(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, state, designation_ref = await _seed_context(writer)
        repo = DirectingAuthorityRepository(writer)
        spatial = _spatial(state.ref, designation_ref).model_copy(
            update={"participant_entity_refs": (EXTRA_ENTITY_REF,)}
        )
        with pytest.raises(DirectingGateBlocked, match="spatial participant is not declared"):
            await repo.create_spatial_contract(
                value=spatial,
                provenance=_prov(spatial, "undeclared spatial participant attempt"),
                created_at=NOW,
            )
    finally:
        await writer.close()



@pytest.mark.asyncio
async def test_spatial_rejects_anchor_entity_not_authorized_by_scene_or_state(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, state, designation_ref = await _seed_context(writer)
        repo = DirectingAuthorityRepository(writer)
        spatial = _spatial(state.ref, designation_ref).model_copy(
            update={
                "anchors": (
                    SpatialAnchor(
                        anchor_key="invented-prop",
                        description="Entity-backed prop not present in Scene or approved State.",
                        entity_ref=EXTRA_ENTITY_REF,
                    ),
                )
            }
        )
        with pytest.raises(DirectingGateBlocked, match="not authorized by canonical Scene or approved StateSnapshot"):
            await repo.create_spatial_contract(
                value=spatial,
                provenance=_prov(spatial, "unauthorized spatial anchor attempt"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_spatial_location_ref_requires_location_entity_kind(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, state, designation_ref = await _seed_context(writer)
        repo = DirectingAuthorityRepository(writer)
        spatial = _spatial(state.ref, designation_ref).model_copy(
            update={"location_entity_ref": ENTITY_REF}
        )
        with pytest.raises(DirectingGateBlocked, match="canonical LOCATION"):
            await repo.create_spatial_contract(
                value=spatial,
                provenance=_prov(spatial, "character-as-location attempt"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_spatial_contract_requires_approved_propagatable_state(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_narrative_and_trace(writer)
        versions = VersionRepository(writer)
        for ref in (CHANGE_REF, OUTCOME_REF, QA_REF, APPROVAL_POLICY_REF):
            await _seed_version(versions, ref, {"fixture": ref.logical_id.root})
        candidate = StateSnapshot(
            project_id=PROJECT_ID,
            state_snapshot_id=state_snapshot_logical_id(PROJECT_ID, "scene-001-end"),
            version_id=VersionId("state-draft"),
            scope_key="scene-001-end",
            story_time="T+00:08",
            facts=(
                StateFact(
                    namespace=StateFactNamespace.WARDROBE,
                    key="upper_body",
                    value_json='{"description":"cream shirt"}',
                    subject_ref=ENTITY_REF,
                ),
            ),
            source_outcome_ref=OUTCOME_REF,
            change_refs=(CHANGE_REF,),
        )
        state_repo = StateSnapshotRepository(writer)
        await state_repo.create_initial(
            snapshot=candidate,
            provenance=build_state_snapshot_provenance(
                candidate,
                actor_ref="studio:imp030-test",
                reason="unapproved state candidate",
                recorded_at=NOW,
            ),
            created_at=NOW,
        )
        fake_designation = VersionRef(
            logical_id=LogicalId("approved-end-state:project:film:missing"),
            version_id=VersionId("approval-v0"),
        )
        spatial = _spatial(candidate.ref, fake_designation)
        repo = DirectingAuthorityRepository(writer)
        with pytest.raises(Exception, match="APPROVED|approved|designation"):
            await repo.create_spatial_contract(
                value=spatial,
                provenance=_prov(spatial, "unapproved state attempt"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_blocking_rejects_position_outside_spatial_contract(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        trace_ref, state, designation_ref = await _seed_context(writer)
        repo = DirectingAuthorityRepository(writer)
        audience = _audience(trace_ref)
        await repo.create_audience_experience_target(
            value=audience,
            provenance=_prov(audience, "create audience"),
            created_at=NOW,
        )
        directing = _directing(audience.ref)
        await repo.create_directing_intent(
            value=directing,
            provenance=_prov(directing, "create directing"),
            created_at=NOW,
        )
        spatial = _spatial(state.ref, designation_ref)
        await repo.create_spatial_contract(
            value=spatial,
            provenance=_prov(spatial, "create spatial"),
            created_at=NOW,
        )
        invalid = _blocking(
            directing.ref,
            spatial.ref,
            state.ref,
            designation_ref,
            start_zone="window",
        )
        with pytest.raises(DirectingGateBlocked, match="undeclared spatial zone"):
            await repo.create_blocking_plan(
                value=invalid,
                provenance=_prov(invalid, "invalid zone attempt"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_blocking_rejects_entity_not_declared_by_spatial_contract(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        trace_ref, state, designation_ref = await _seed_context(writer)
        repo = DirectingAuthorityRepository(writer)
        audience = _audience(trace_ref)
        await repo.create_audience_experience_target(
            value=audience, provenance=_prov(audience, "create audience"), created_at=NOW
        )
        directing = _directing(audience.ref)
        await repo.create_directing_intent(
            value=directing, provenance=_prov(directing, "create directing"), created_at=NOW
        )
        spatial = _spatial(state.ref, designation_ref)
        await repo.create_spatial_contract(
            value=spatial, provenance=_prov(spatial, "create spatial"), created_at=NOW
        )
        invalid = _blocking(
            directing.ref,
            spatial.ref,
            state.ref,
            designation_ref,
            entity_ref=EXTRA_ENTITY_REF,
        )
        with pytest.raises(DirectingGateBlocked, match="not declared by SceneSpatialDramaticContract"):
            await repo.create_blocking_plan(
                value=invalid,
                provenance=_prov(invalid, "undeclared blocking entity attempt"),
                created_at=NOW,
            )
    finally:
        await writer.close()



def test_cinematography_schema_rejects_self_authored_extra_camera_setting_and_bad_basis():
    audience_ref = VersionRef(
        logical_id=audience_experience_target_logical_id(PROJECT_ID, BEAT_REF),
        version_id=VersionId("aud-v1"),
    )
    directing_ref = VersionRef(
        logical_id=directing_intent_logical_id(PROJECT_ID, BEAT_REF),
        version_id=VersionId("direct-v1"),
    )
    spatial_ref = VersionRef(
        logical_id=scene_spatial_contract_logical_id(PROJECT_ID, SCENE_REF),
        version_id=VersionId("spatial-v1"),
    )
    blocking_ref = VersionRef(
        logical_id=blocking_plan_logical_id(PROJECT_ID, BEAT_REF),
        version_id=VersionId("blocking-v1"),
    )
    valid = _cine(audience_ref, directing_ref, spatial_ref, blocking_ref)
    payload = valid.model_dump(mode="json")
    payload["lens_mm"] = 50
    with pytest.raises(ValidationError, match="Extra inputs"):
        CinematographyObjective.model_validate(payload)

    external = VersionRef(
        logical_id=LogicalId("provider-camera-preset:50mm"),
        version_id=VersionId("v1"),
    )
    bad_bases = list(valid.decision_bases)
    bad_bases[0] = bad_bases[0].model_copy(update={"source_refs": (external,)})
    with pytest.raises(ValidationError, match="declared upstream authority"):
        valid.model_copy(update={"decision_bases": tuple(bad_bases)}).model_validate(
            {
                **valid.model_dump(mode="json"),
                "decision_bases": [item.model_dump(mode="json") for item in bad_bases],
            }
        )


@pytest.mark.asyncio
async def test_cinematography_rejects_stale_blocking_after_directing_revision(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, _, _, _, audience, directing, spatial, blocking, cine = await _create_chain(writer)
        successor = directing.model_copy(
            update={
                "version_id": VersionId("direct-v2"),
                "performance_objective": "Let resistance break one beat later while preserving the same reveal.",
            }
        )
        pointer = await repo.versions.get_current(directing.logical_id)
        assert pointer is not None
        _, records = await repo.revise_directing_intent(
            value=successor,
            predecessor=directing.ref,
            provenance=_prov(successor, "revise directing"),
            created_at=NOW,
            expected_revision=pointer.revision,
        )
        assert any(record.affected_object_id == blocking.logical_id for record in records)

        contradictory = cine.model_copy(
            update={
                "version_id": VersionId("cine-v2"),
                "directing_intent_ref": successor.ref,
                "decision_bases": _bases(
                    audience.ref,
                    successor.ref,
                    spatial.ref,
                    blocking.ref,
                ),
            }
        )
        with pytest.raises(DirectingGateBlocked, match="BlockingPlan|contradictory|invalidation"):
            await repo.create_cinematography_objective(
                value=contradictory,
                provenance=_prov(contradictory, "stale blocking attempt"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_profile_dependency_uses_selective_profile_path_edge(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        trace_ref, _, _ = await _seed_context(writer)
        repo = DirectingAuthorityRepository(writer)
        audience = _audience(trace_ref)
        await repo.create_audience_experience_target(
            value=audience,
            provenance=_prov(audience, "create audience"),
            created_at=NOW,
        )
        incoming = await repo.graph.list_incoming(audience.ref)
        profile_edges = [edge for edge in incoming if edge.source_ref == PROFILE_REF]
        assert len(profile_edges) == 1
        assert profile_edges[0].edge_type == "PROFILE_PATH:*"
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_blocking_revision_selectively_invalidates_cinematography_only_downstream(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, _, _, designation_ref, audience, directing, spatial, blocking, cine = await _create_chain(writer)
        state_ref = blocking.state_snapshot_ref
        successor = blocking.model_copy(
            update={
                "version_id": VersionId("blocking-v2"),
                "must_preserve": (
                    "Cassette remains on desk throughout beat.",
                    "Actor keeps one hand near the stop control after playback.",
                ),
            }
        )
        pointer = await repo.versions.get_current(blocking.logical_id)
        assert pointer is not None
        _, records = await repo.revise_blocking_plan(
            value=successor,
            predecessor=blocking.ref,
            provenance=_prov(successor, "refine blocking"),
            created_at=NOW,
            expected_revision=pointer.revision,
        )
        affected = {(record.affected_object_id, record.affected_object_version) for record in records}
        assert (cine.logical_id, cine.version_id) in affected
        assert (audience.logical_id, audience.version_id) not in affected
        assert (directing.logical_id, directing.version_id) not in affected
        assert (spatial.logical_id, spatial.version_id) not in affected
        assert (UNRELATED_REF.logical_id, UNRELATED_REF.version_id) not in affected
        assert successor.state_snapshot_ref == state_ref
        assert successor.approved_state_designation_ref == designation_ref
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_directing_provenance_must_exactly_bind_sources(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        trace_ref, _, _ = await _seed_context(writer)
        repo = DirectingAuthorityRepository(writer)
        audience = _audience(trace_ref)
        wrong = _seed_provenance("wrong directing provenance")
        with pytest.raises(DirectingAuthorityError, match="exactly bind"):
            await repo.create_audience_experience_target(
                value=audience,
                provenance=wrong,
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_noop_successor_is_rejected_and_history_remains_immutable(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        trace_ref, _, _ = await _seed_context(writer)
        repo = DirectingAuthorityRepository(writer)
        audience = _audience(trace_ref)
        await repo.create_audience_experience_target(
            value=audience,
            provenance=_prov(audience, "create audience"),
            created_at=NOW,
        )
        noop = audience.model_copy(update={"version_id": VersionId("aud-v2")})
        pointer = await repo.versions.get_current(audience.logical_id)
        assert pointer is not None
        with pytest.raises(DirectingIdentityError, match="semantic/source change"):
            await repo.revise_audience_experience_target(
                value=noop,
                predecessor=audience.ref,
                provenance=_prov(noop, "no-op audience successor"),
                created_at=NOW,
                expected_revision=pointer.revision,
            )
        original = await repo.get_audience_experience_target(audience.ref)
        assert original is not None
        assert original.value == audience
    finally:
        await writer.close()
