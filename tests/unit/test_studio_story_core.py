"""IMP-023 tests for StoryCore, Conflict/Stakes, CausalStoryGraph and lock."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    CausalStoryGraph,
    CharacterModelVersion,
    ConflictModel,
    GateVerdict,
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SQLiteWriteOwner,
    StakesModel,
    StoryCoreGateBlocked,
    StoryCoreLockManifest,
    StoryCorePhase,
    StoryCoreRepository,
    StoryCoreVersion,
    StoryGraphEdge,
    StoryGraphEdgeKind,
    StoryGraphNode,
    StoryGraphNodeKind,
    VersionId,
    VersionRef,
    VersionRepository,
    build_story_core_provenance,
)


NOW = datetime(2026, 9, 30, 3, 0, tzinfo=timezone.utc)
PROJECT_ID = LogicalId("project:film")
PROFILE_REF = VersionRef(
    logical_id=LogicalId("active-profile:project:film"),
    version_id=VersionId("profile-v1"),
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
RESEARCH_REF = VersionRef(
    logical_id=LogicalId("story-material:project:film:cassette"),
    version_id=VersionId("research-v1"),
)
CHAR_ENTITY_REF = VersionRef(
    logical_id=LogicalId("entity:protagonist"),
    version_id=VersionId("entity-v1"),
)
CHAR_DRAFT_REF = VersionRef(
    logical_id=LogicalId("character-model:entity:protagonist"),
    version_id=VersionId("character-v1"),
)
CHAR_APPROVED_REF = VersionRef(
    logical_id=CHAR_DRAFT_REF.logical_id,
    version_id=VersionId("character-v2"),
)


def _seed_provenance(reason: str) -> Provenance:
    return Provenance(
        source_refs=("evidence:imp023-seed",),
        actor_ref="studio:test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp023",
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
        provenance=_seed_provenance("seed exact source"),
        created_at=NOW,
    )


async def _seed(
    versions: VersionRepository,
    ref: VersionRef,
    *,
    status: LifecycleState,
    payload: dict | None = None,
) -> None:
    await versions.create_initial(
        metadata=_metadata(ref),
        payload=payload or {"seed": ref.logical_id.root},
        status=status,
    )


def _character_model(
    version: str,
    *,
    story_core_ref: VersionRef | None = None,
) -> CharacterModelVersion:
    return CharacterModelVersion(
        project_id=PROJECT_ID,
        character_ref=CHAR_ENTITY_REF,
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        story_core_ref=story_core_ref,
        story_context_refs=(PREMISE_REF,),
        story_material_refs=(RESEARCH_REF,),
        role="protagonist",
        external_want="Sell the inherited family house and return to city life.",
        internal_need="Face the grief and family truth avoided by leaving.",
        fear="Being trapped by obligations from the past.",
        decision_style="Decisive until emotional evidence makes avoidance impossible.",
    )


async def _seed_context(writer: SQLiteWriteOwner) -> VersionRepository:
    versions = VersionRepository(writer)
    await _seed(versions, PROFILE_REF, status=LifecycleState.LOCKED)
    for ref in (IDEA_REF, LOGLINE_REF, PREMISE_REF, ANGLE_REF, THEME_REF, RESEARCH_REF):
        await _seed(versions, ref, status=LifecycleState.APPROVED)
    await _seed(
        versions,
        CHAR_DRAFT_REF,
        status=LifecycleState.DRAFT,
        payload=_character_model("character-v1").model_dump(mode="json"),
    )
    return versions


async def _accept_character(
    versions: VersionRepository,
    story_core_ref: VersionRef,
    *,
    target_ref: VersionRef = CHAR_APPROVED_REF,
    predecessor: VersionRef = CHAR_DRAFT_REF,
    expected_revision: int = 0,
) -> VersionRef:
    character = _character_model(
        target_ref.version_id.root,
        story_core_ref=story_core_ref,
    )
    await versions.create_successor(
        metadata=_metadata(
            target_ref,
            predecessor=predecessor,
        ),
        payload=character.model_dump(mode="json"),
        supersession_reason="bind exact StoryCore draft",
    )
    await versions.update_current(
        logical_id=target_ref.logical_id,
        version_id=target_ref.version_id,
        status=LifecycleState.APPROVED,
        expected_revision=expected_revision,
    )
    return target_ref


def _core(
    version: str = "core-v1",
    *,
    character_ref: VersionRef = CHAR_DRAFT_REF,
    core_goal: str = "Sell the inherited house and leave town.",
    factuality_compatible: bool = True,
) -> StoryCoreVersion:
    return StoryCoreVersion(
        project_id=PROJECT_ID,
        version_id=VersionId(version),
        phase=StoryCorePhase.DRAFT,
        active_profile_ref=PROFILE_REF,
        idea_ref=IDEA_REF,
        logline_ref=LOGLINE_REF,
        premise_ref=PREMISE_REF,
        angle_ref=ANGLE_REF,
        theme_ref=THEME_REF,
        character_refs=(character_ref,),
        research_refs=(RESEARCH_REF,),
        core_goal=core_goal,
        core_question="Can he leave honestly without confronting what the cassette proves?",
        core_conflict=(
            "The clean sale he wants conflicts with evidence that demands he stay "
            "long enough to face his family."
        ),
        core_stakes=(
            "Leaving preserves speed but may erase his last chance for truthful closure."
        ),
        factual_constraints=("The mother is already deceased before the story begins.",),
        canonical_hard_constraints_satisfied=True,
        factuality_compatible=factuality_compatible,
    )


def _conflict(
    core_ref: VersionRef,
    *,
    version: str = "conflict-v1",
    produces_resistance: bool = True,
) -> ConflictModel:
    return ConflictModel(
        project_id=PROJECT_ID,
        version_id=VersionId(version),
        story_core_draft_ref=core_ref,
        active_profile_ref=PROFILE_REF,
        theme_ref=THEME_REF,
        character_refs=(CHAR_APPROVED_REF,),
        incompatible_objectives=(
            "Complete the house sale immediately.",
            "Investigate the cassette before surrendering the house.",
        ),
        opposition_forces=("Sale deadline and family resistance.",),
        leverage_points=("Signed buyer deadline.", "Cassette contains unresolved evidence."),
        escalation_steps=(
            "Delay threatens the sale.",
            "Investigation forces direct family confrontation.",
        ),
        produces_resistance=produces_resistance,
        change_potential=True,
    )


def _stakes(
    core_ref: VersionRef,
    conflict_ref: VersionRef,
    *,
    version: str = "stakes-v1",
) -> StakesModel:
    return StakesModel(
        project_id=PROJECT_ID,
        version_id=VersionId(version),
        story_core_draft_ref=core_ref,
        conflict_ref=conflict_ref,
        active_profile_ref=PROFILE_REF,
        practical_stakes=("The house sale can collapse.",),
        relational_stakes=("His remaining family may stop trusting him.",),
        identity_stakes=("He must decide whether avoidance still defines him.",),
        irreversible_stakes=("Once sold, access to the family home is gone.",),
        escalation_steps=(
            "Delay costs money.",
            "Truth-seeking risks the relationship.",
            "The final sale makes the choice irreversible.",
        ),
        major_turn_consequences=(
            "Listening to the cassette makes immediate departure impossible.",
            "Confrontation changes what the sale means.",
        ),
        genre_scale_compatible=True,
    )


def _graph(
    core_ref: VersionRef,
    conflict_ref: VersionRef,
    stakes_ref: VersionRef,
    *,
    version: str = "graph-v1",
    causal_gap: bool = False,
    cycle: bool = False,
    character_refs: tuple[VersionRef, ...] = (CHAR_APPROVED_REF,),
) -> CausalStoryGraph:
    edges = [
        StoryGraphEdge(
            edge_id="edge-1",
            source_node_id="setup",
            target_node_id="decision",
            kind=StoryGraphEdgeKind.CAUSES,
            rationale="The cassette makes an immediate sale emotionally impossible.",
        ),
        StoryGraphEdge(
            edge_id="edge-2",
            source_node_id="decision",
            target_node_id="payoff",
            kind=StoryGraphEdgeKind.CAUSES,
            rationale="Choosing to investigate forces the final family confrontation.",
        ),
    ]
    if cycle:
        edges.append(
            StoryGraphEdge(
                edge_id="edge-3",
                source_node_id="payoff",
                target_node_id="setup",
                kind=StoryGraphEdgeKind.CAUSES,
                rationale="Deliberately illegal fixture cycle.",
            )
        )
    return CausalStoryGraph(
        project_id=PROJECT_ID,
        version_id=VersionId(version),
        story_core_draft_ref=core_ref,
        conflict_ref=conflict_ref,
        stakes_ref=stakes_ref,
        active_profile_ref=PROFILE_REF,
        character_refs=character_refs,
        research_refs=(RESEARCH_REF,),
        nodes=(
            StoryGraphNode(
                node_id="setup",
                kind=StoryGraphNodeKind.REVELATION,
                summary="He finds and listens to the cassette.",
                root_cause=True,
                requires_consequence=True,
            ),
            StoryGraphNode(
                node_id="decision",
                kind=StoryGraphNodeKind.DECISION,
                summary="He postpones the sale to investigate.",
                major_change=True,
                requires_consequence=True,
                causal_gap=causal_gap,
            ),
            StoryGraphNode(
                node_id="payoff",
                kind=StoryGraphNodeKind.PAYOFF,
                summary="He confronts the family and redefines the sale decision.",
                major_change=True,
            ),
        ),
        edges=tuple(edges),
    )


def _provenance(value, reason: str) -> Provenance:
    return build_story_core_provenance(
        value,
        actor_ref="studio:imp023",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp023",),
        correlation_id="run:imp023",
    )


async def _ready_pipeline(writer: SQLiteWriteOwner):
    versions = await _seed_context(writer)
    repo = StoryCoreRepository(writer)

    draft = _core()
    draft_artifact = await repo.create_story_core_draft(
        value=draft,
        provenance=_provenance(draft, "create StoryCore draft"),
        created_at=NOW,
    )
    await _accept_character(versions, draft_artifact.ref)

    conflict = _conflict(draft_artifact.ref)
    conflict_artifact = await repo.create_conflict(
        value=conflict,
        provenance=_provenance(conflict, "derive conflict"),
        created_at=NOW,
    )
    stakes = _stakes(draft_artifact.ref, conflict_artifact.ref)
    stakes_artifact = await repo.create_stakes(
        value=stakes,
        provenance=_provenance(stakes, "derive stakes"),
        created_at=NOW,
    )
    graph = _graph(draft_artifact.ref, conflict_artifact.ref, stakes_artifact.ref)
    graph_artifact = await repo.create_story_graph(
        value=graph,
        provenance=_provenance(graph, "create causal graph"),
        created_at=NOW,
    )
    preview = repo.causal_gate.evaluate(
        graph,
        version_id=VersionId("validation-v1"),
    )
    validation_artifact = await repo.validate_story_graph(
        graph_ref=graph_artifact.ref,
        validation_version_id=preview.version_id,
        provenance=_provenance(preview, "validate causal graph"),
        created_at=NOW,
    )
    return (
        versions,
        repo,
        draft_artifact,
        conflict_artifact,
        stakes_artifact,
        graph_artifact,
        validation_artifact,
    )


def _frozen_candidate(draft, graph_ref, validation_ref, version: str):
    return draft.model_copy(
        update={
            "version_id": VersionId(version),
            "phase": StoryCorePhase.FROZEN_FOR_STRUCTURE,
            "lock_manifest": StoryCoreLockManifest(
                draft_ref=draft.ref,
                story_graph_ref=graph_ref,
                causal_validation_ref=validation_ref,
                locked_at=NOW,
            ),
        }
    )


@pytest.mark.asyncio
async def test_draft_graph_validation_lock_preserves_one_story_core_identity(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        (
            _versions,
            repo,
            draft_artifact,
            _conflict,
            _stakes,
            graph_artifact,
            validation_artifact,
        ) = await _ready_pipeline(writer)

        assert validation_artifact.value.verdict is GateVerdict.PASS
        frozen_candidate = _frozen_candidate(
            draft_artifact.value,
            graph_artifact.ref,
            validation_artifact.ref,
            "core-v2",
        )
        frozen_artifact = await repo.lock_story_core(
            draft_ref=draft_artifact.ref,
            graph_ref=graph_artifact.ref,
            validation_ref=validation_artifact.ref,
            frozen_version_id=frozen_candidate.version_id,
            provenance=_provenance(frozen_candidate, "freeze StoryCore for structure"),
            created_at=NOW,
            expected_revision=0,
        )

        assert frozen_artifact.value.phase is StoryCorePhase.FROZEN_FOR_STRUCTURE
        assert frozen_artifact.ref.logical_id == draft_artifact.ref.logical_id
        assert frozen_artifact.metadata.predecessor == draft_artifact.ref
        assert frozen_artifact.value.lock_manifest.draft_ref == draft_artifact.ref

        current = await repo.versions.get_current(draft_artifact.ref.logical_id)
        assert current.version_id == frozen_artifact.ref.version_id
        assert current.status is LifecycleState.LOCKED

        original = await repo.get_story_core(draft_artifact.ref)
        assert original.value.phase is StoryCorePhase.DRAFT
        history = await repo.versions.list_supersession_history(
            draft_artifact.ref.logical_id
        )
        assert history[-1].predecessor == draft_artifact.ref
        assert history[-1].successor == frozen_artifact.ref

        draft_descendants = {
            item.ref for item in await repo.graph.descendants(draft_artifact.ref)
        }
        assert graph_artifact.ref in draft_descendants
        graph_descendants = {
            item.ref for item in await repo.graph.descendants(graph_artifact.ref)
        }
        assert draft_artifact.ref not in graph_descendants
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_story_graph_never_requires_locked_story_core(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        (
            _versions,
            repo,
            draft_artifact,
            conflict_artifact,
            stakes_artifact,
            graph_artifact,
            validation_artifact,
        ) = await _ready_pipeline(writer)
        frozen_candidate = _frozen_candidate(
            draft_artifact.value,
            graph_artifact.ref,
            validation_artifact.ref,
            "core-v2",
        )
        frozen = await repo.lock_story_core(
            draft_ref=draft_artifact.ref,
            graph_ref=graph_artifact.ref,
            validation_ref=validation_artifact.ref,
            frozen_version_id=frozen_candidate.version_id,
            provenance=_provenance(frozen_candidate, "freeze StoryCore"),
            created_at=NOW,
            expected_revision=0,
        )

        wrong_graph = _graph(
            frozen.ref,
            conflict_artifact.ref,
            stakes_artifact.ref,
            version="graph-v2",
        )
        with pytest.raises(StoryCoreGateBlocked, match="StoryCore DRAFT"):
            await repo.revise_story_graph(
                value=wrong_graph,
                predecessor=graph_artifact.ref,
                provenance=_provenance(wrong_graph, "illegal locked-core graph"),
                created_at=NOW,
                expected_revision=1,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_causal_gap_and_illegal_cycle_fail_closed_and_block_lock(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_context(writer)
        repo = StoryCoreRepository(writer)
        draft = _core()
        draft_artifact = await repo.create_story_core_draft(
            value=draft,
            provenance=_provenance(draft, "create draft"),
            created_at=NOW,
        )
        await _accept_character(versions, draft_artifact.ref)
        conflict = _conflict(draft_artifact.ref)
        conflict_artifact = await repo.create_conflict(
            value=conflict,
            provenance=_provenance(conflict, "conflict"),
            created_at=NOW,
        )
        stakes = _stakes(draft_artifact.ref, conflict_artifact.ref)
        stakes_artifact = await repo.create_stakes(
            value=stakes,
            provenance=_provenance(stakes, "stakes"),
            created_at=NOW,
        )
        bad_graph = _graph(
            draft_artifact.ref,
            conflict_artifact.ref,
            stakes_artifact.ref,
            causal_gap=True,
            cycle=True,
        )
        graph_artifact = await repo.create_story_graph(
            value=bad_graph,
            provenance=_provenance(bad_graph, "bad graph"),
            created_at=NOW,
        )
        preview = repo.causal_gate.evaluate(
            bad_graph,
            version_id=VersionId("validation-v1"),
        )
        assert preview.verdict is GateVerdict.FAIL
        codes = {finding.code for finding in preview.findings}
        assert "STORY_GRAPH_CAUSAL_GAP" in codes
        assert "STORY_GRAPH_ILLEGAL_CYCLE" in codes

        validation = await repo.validate_story_graph(
            graph_ref=graph_artifact.ref,
            validation_version_id=preview.version_id,
            provenance=_provenance(preview, "persist failed validation"),
            created_at=NOW,
        )
        assert validation.value.verdict is GateVerdict.FAIL
        frozen_candidate = _frozen_candidate(
            draft_artifact.value,
            graph_artifact.ref,
            validation.ref,
            "core-v2",
        )
        with pytest.raises(StoryCoreGateBlocked, match="unresolved causal defect"):
            await repo.lock_story_core(
                draft_ref=draft_artifact.ref,
                graph_ref=graph_artifact.ref,
                validation_ref=validation.ref,
                frozen_version_id=frozen_candidate.version_id,
                provenance=_provenance(frozen_candidate, "blocked freeze"),
                created_at=NOW,
                expected_revision=0,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_character_version_blocks_story_graph(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_context(writer)
        repo = StoryCoreRepository(writer)
        draft = _core()
        draft_artifact = await repo.create_story_core_draft(
            value=draft,
            provenance=_provenance(draft, "draft"),
            created_at=NOW,
        )
        await _accept_character(versions, draft_artifact.ref)
        conflict = _conflict(draft_artifact.ref)
        conflict_artifact = await repo.create_conflict(
            value=conflict,
            provenance=_provenance(conflict, "conflict"),
            created_at=NOW,
        )
        stakes = _stakes(draft_artifact.ref, conflict_artifact.ref)
        stakes_artifact = await repo.create_stakes(
            value=stakes,
            provenance=_provenance(stakes, "stakes"),
            created_at=NOW,
        )

        char_v3 = VersionRef(
            logical_id=CHAR_APPROVED_REF.logical_id,
            version_id=VersionId("character-v3"),
        )
        char_v3_value = _character_model(
            "character-v3",
            story_core_ref=draft_artifact.ref,
        )
        await versions.create_successor(
            metadata=_metadata(char_v3, predecessor=CHAR_APPROVED_REF),
            payload=char_v3_value.model_dump(mode="json"),
            supersession_reason="psychology changed",
        )
        await versions.update_current(
            logical_id=char_v3.logical_id,
            version_id=char_v3.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=1,
        )

        stale_graph = _graph(
            draft_artifact.ref,
            conflict_artifact.ref,
            stakes_artifact.ref,
        )
        with pytest.raises(
            StoryCoreGateBlocked,
            match="StoryGraph CharacterModelVersion is not exact current",
        ):
            await repo.create_story_graph(
                value=stale_graph,
                provenance=_provenance(stale_graph, "stale character graph"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_conflict_rejects_character_bound_to_different_story_core(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_context(writer)
        repo = StoryCoreRepository(writer)
        draft = _core()
        draft_artifact = await repo.create_story_core_draft(
            value=draft,
            provenance=_provenance(draft, "draft"),
            created_at=NOW,
        )
        wrong_core_ref = VersionRef(
            logical_id=draft_artifact.ref.logical_id,
            version_id=VersionId("other-core-draft"),
        )
        await _accept_character(versions, wrong_core_ref)
        conflict = _conflict(draft_artifact.ref)

        with pytest.raises(
            StoryCoreGateBlocked,
            match="same exact StoryCore DRAFT",
        ):
            await repo.create_conflict(
                value=conflict,
                provenance=_provenance(conflict, "mismatched character binding"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_graph_rejects_conflict_stakes_from_previous_story_core_draft(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_context(writer)
        repo = StoryCoreRepository(writer)

        draft = _core()
        draft_artifact = await repo.create_story_core_draft(
            value=draft,
            provenance=_provenance(draft, "draft v1"),
            created_at=NOW,
        )
        await _accept_character(versions, draft_artifact.ref)
        conflict = _conflict(draft_artifact.ref)
        conflict_artifact = await repo.create_conflict(
            value=conflict,
            provenance=_provenance(conflict, "conflict v1"),
            created_at=NOW,
        )
        stakes = _stakes(draft_artifact.ref, conflict_artifact.ref)
        stakes_artifact = await repo.create_stakes(
            value=stakes,
            provenance=_provenance(stakes, "stakes v1"),
            created_at=NOW,
        )

        revised = _core(
            "core-v2",
            character_ref=CHAR_APPROVED_REF,
            core_goal="Delay the sale until the cassette evidence is resolved.",
        )
        revised_artifact, _invalidations = await repo.revise_story_core_draft(
            value=revised,
            predecessor=draft_artifact.ref,
            provenance=_provenance(revised, "revise StoryCore draft"),
            created_at=NOW,
            expected_revision=0,
        )

        mismatched = _graph(
            revised_artifact.ref,
            conflict_artifact.ref,
            stakes_artifact.ref,
            version="graph-v2",
            character_refs=(),
        )
        with pytest.raises(
            StoryCoreGateBlocked,
            match="ConflictModel must bind the same exact StoryCore DRAFT",
        ):
            await repo.create_story_graph(
                value=mismatched,
                provenance=_provenance(mismatched, "mismatched graph lineage"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_story_graph_version_cannot_emit_new_validation_evidence(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        (
            _versions,
            repo,
            draft_artifact,
            conflict_artifact,
            stakes_artifact,
            graph_artifact,
            _validation_artifact,
        ) = await _ready_pipeline(writer)

        revised_graph = _graph(
            draft_artifact.ref,
            conflict_artifact.ref,
            stakes_artifact.ref,
            version="graph-v2",
        )
        await repo.revise_story_graph(
            value=revised_graph,
            predecessor=graph_artifact.ref,
            provenance=_provenance(revised_graph, "revise graph"),
            created_at=NOW,
            expected_revision=1,
        )

        stale_preview = repo.causal_gate.evaluate(
            graph_artifact.value,
            version_id=VersionId("validation-stale"),
        )
        with pytest.raises(
            StoryCoreGateBlocked,
            match="StoryGraph is not exact current accepted version",
        ):
            await repo.validate_story_graph(
                graph_ref=graph_artifact.ref,
                validation_version_id=stale_preview.version_id,
                provenance=_provenance(stale_preview, "stale graph validation"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_story_core_revision_invalidates_old_graph_validation_and_lock(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        (
            _versions,
            repo,
            draft_artifact,
            _conflict,
            _stakes,
            graph_artifact,
            validation_artifact,
        ) = await _ready_pipeline(writer)
        frozen_candidate = _frozen_candidate(
            draft_artifact.value,
            graph_artifact.ref,
            validation_artifact.ref,
            "core-v2",
        )
        frozen = await repo.lock_story_core(
            draft_ref=draft_artifact.ref,
            graph_ref=graph_artifact.ref,
            validation_ref=validation_artifact.ref,
            frozen_version_id=frozen_candidate.version_id,
            provenance=_provenance(frozen_candidate, "freeze"),
            created_at=NOW,
            expected_revision=0,
        )

        revised = _core(
            "core-v3",
            character_ref=CHAR_APPROVED_REF,
            core_goal="Delay the sale until the cassette's claim is resolved.",
        )
        revised_artifact, invalidations = await repo.revise_story_core_draft(
            value=revised,
            predecessor=frozen.ref,
            provenance=_provenance(revised, "reopen StoryCore after core-fact change"),
            created_at=NOW,
            expected_revision=1,
        )
        affected = {
            (item.affected_object_id.root, item.affected_object_version.root)
            for item in invalidations
        }
        assert (
            graph_artifact.ref.logical_id.root,
            graph_artifact.ref.version_id.root,
        ) in affected
        assert (
            validation_artifact.ref.logical_id.root,
            validation_artifact.ref.version_id.root,
        ) in affected
        assert (
            frozen.ref.logical_id.root,
            frozen.ref.version_id.root,
        ) in affected

        current = await repo.versions.get_current(revised_artifact.ref.logical_id)
        assert current.version_id == revised_artifact.ref.version_id
        assert current.status is LifecycleState.DRAFT
        assert (await repo.get_story_core(frozen.ref)).value.phase is StoryCorePhase.FROZEN_FOR_STRUCTURE
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_failed_graph_can_be_repaired_by_successor_and_revalidated(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_context(writer)
        repo = StoryCoreRepository(writer)
        draft = _core()
        draft_artifact = await repo.create_story_core_draft(
            value=draft,
            provenance=_provenance(draft, "draft"),
            created_at=NOW,
        )
        await _accept_character(versions, draft_artifact.ref)
        conflict = _conflict(draft_artifact.ref)
        conflict_artifact = await repo.create_conflict(
            value=conflict,
            provenance=_provenance(conflict, "conflict"),
            created_at=NOW,
        )
        stakes = _stakes(draft_artifact.ref, conflict_artifact.ref)
        stakes_artifact = await repo.create_stakes(
            value=stakes,
            provenance=_provenance(stakes, "stakes"),
            created_at=NOW,
        )

        bad = _graph(
            draft_artifact.ref,
            conflict_artifact.ref,
            stakes_artifact.ref,
            causal_gap=True,
        )
        bad_artifact = await repo.create_story_graph(
            value=bad,
            provenance=_provenance(bad, "bad graph"),
            created_at=NOW,
        )
        bad_preview = repo.causal_gate.evaluate(
            bad,
            version_id=VersionId("validation-v1"),
        )
        failed_validation = await repo.validate_story_graph(
            graph_ref=bad_artifact.ref,
            validation_version_id=bad_preview.version_id,
            provenance=_provenance(bad_preview, "failed validation"),
            created_at=NOW,
        )
        assert failed_validation.value.verdict is GateVerdict.FAIL

        repaired = _graph(
            draft_artifact.ref,
            conflict_artifact.ref,
            stakes_artifact.ref,
            version="graph-v2",
        )
        repaired_artifact, invalidations = await repo.revise_story_graph(
            value=repaired,
            predecessor=bad_artifact.ref,
            provenance=_provenance(repaired, "repair causal graph"),
            created_at=NOW,
            expected_revision=0,
        )
        assert any(
            item.affected_object_id == failed_validation.ref.logical_id
            and item.affected_object_version == failed_validation.ref.version_id
            for item in invalidations
        )

        repaired_preview = repo.causal_gate.evaluate(
            repaired,
            version_id=VersionId("validation-v2"),
        )
        passed_validation = await repo.validate_story_graph(
            graph_ref=repaired_artifact.ref,
            validation_version_id=repaired_preview.version_id,
            provenance=_provenance(repaired_preview, "passing validation"),
            created_at=NOW,
        )
        assert passed_validation.value.verdict is GateVerdict.PASS
        graph_pointer = await repo.versions.get_current(repaired_artifact.ref.logical_id)
        validation_pointer = await repo.versions.get_current(
            passed_validation.ref.logical_id
        )
        assert graph_pointer.version_id == repaired_artifact.ref.version_id
        assert graph_pointer.status is LifecycleState.APPROVED
        assert validation_pointer.version_id == passed_validation.ref.version_id
        assert validation_pointer.status is LifecycleState.APPROVED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_conflict_gate_rejects_no_resistance(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_context(writer)
        repo = StoryCoreRepository(writer)
        draft = _core()
        draft_artifact = await repo.create_story_core_draft(
            value=draft,
            provenance=_provenance(draft, "draft"),
            created_at=NOW,
        )
        await _accept_character(versions, draft_artifact.ref)
        conflict = _conflict(
            draft_artifact.ref,
            produces_resistance=False,
        )
        with pytest.raises(StoryCoreGateBlocked, match="produce resistance"):
            await repo.create_conflict(
                value=conflict,
                provenance=_provenance(conflict, "invalid conflict"),
                created_at=NOW,
            )
    finally:
        await writer.close()


def test_story_core_rejects_provider_runtime_authority_fields():
    payload = _core().model_dump(mode="python")
    payload["provider"] = "veo"
    with pytest.raises(ValidationError):
        StoryCoreVersion.model_validate(payload)


def test_cross_project_story_refs_are_rejected_fail_closed():
    payload = _core().model_dump(mode="python")
    payload["theme_ref"] = VersionRef(
        logical_id=LogicalId("story-theme:project:other"),
        version_id=VersionId("theme-v1"),
    )
    with pytest.raises(ValidationError, match="same project"):
        StoryCoreVersion.model_validate(payload)

    with pytest.raises(ValidationError, match="same project"):
        _graph(
            VersionRef(
                logical_id=LogicalId("story-core:project:other"),
                version_id=VersionId("core-v1"),
            ),
            VersionRef(
                logical_id=LogicalId("conflict:project:film"),
                version_id=VersionId("conflict-v1"),
            ),
            VersionRef(
                logical_id=LogicalId("stakes:project:film"),
                version_id=VersionId("stakes-v1"),
            ),
        )
