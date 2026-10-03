"""IMP-028 NarrativeTrace exact-version lineage tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    DependencyGraphRepository,
    InvalidationRepository,
    LifecycleState,
    LogicalId,
    NarrativeArtifactType,
    NarrativeTraceFindingCode,
    NarrativeTraceGateBlocked,
    NarrativeTraceIdentityError,
    NarrativeTraceRecord,
    NarrativeTraceRepository,
    NarrativeTraceState,
    Provenance,
    SemanticRecordMetadata,
    SQLiteWriteOwner,
    VersionId,
    VersionRef,
    VersionRepository,
    build_narrative_trace_provenance,
)


NOW = datetime(2026, 10, 3, 4, 0, tzinfo=timezone.utc)
PROJECT_ID = LogicalId("project:film")

CORE = VersionRef(
    logical_id=LogicalId("story-core:project:film"),
    version_id=VersionId("core-v1"),
)
MACRO_A = VersionRef(
    logical_id=LogicalId("macro-story-beat:project:film:opening"),
    version_id=VersionId("macro-a-v1"),
)
MACRO_B = VersionRef(
    logical_id=LogicalId("macro-story-beat:project:film:confrontation"),
    version_id=VersionId("macro-b-v1"),
)
SEQUENCE = VersionRef(
    logical_id=LogicalId("sequence:project:film:investigation"),
    version_id=VersionId("sequence-v1"),
)
SCENE = VersionRef(
    logical_id=LogicalId("scene:project:film:cassette-room"),
    version_id=VersionId("scene-v1"),
)
BEAT = VersionRef(
    logical_id=LogicalId("scene-dramatic-beat:project:film:cassette-room:recognition"),
    version_id=VersionId("beat-v1"),
)
PLANNER = VersionRef(
    logical_id=LogicalId("sequence-plan:project:film"),
    version_id=VersionId("planner-v1"),
)


def _seed_provenance(reason: str = "IMP-028 test seed") -> Provenance:
    return Provenance(
        source_refs=("evidence:imp028-test",),
        actor_ref="studio:imp028-test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp028-test",
    )


def _metadata(
    ref: VersionRef,
    *,
    predecessor: VersionRef | None = None,
    reason: str = "IMP-028 test seed",
) -> SemanticRecordMetadata:
    return SemanticRecordMetadata(
        logical_id=ref.logical_id,
        version_id=ref.version_id,
        predecessor=predecessor,
        provenance=_seed_provenance(reason),
        created_at=NOW,
    )


async def _seed_version(
    versions: VersionRepository,
    ref: VersionRef,
    *,
    status: LifecycleState,
) -> None:
    await versions.create_initial(
        metadata=_metadata(ref),
        payload={"fixture": ref.logical_id.root},
        status=status,
    )


async def _edge(
    graph: DependencyGraphRepository,
    source: VersionRef,
    dependent: VersionRef,
) -> None:
    await graph.create_edge(
        source=source,
        dependent=dependent,
        edge_type="narrative_hierarchy_input",
        dependency_reason="canonical narrative parent",
        provenance=_seed_provenance("seed narrative dependency"),
        created_at=NOW,
    )


async def _seed_refs(writer: SQLiteWriteOwner) -> tuple[VersionRepository, DependencyGraphRepository]:
    versions = VersionRepository(writer)
    graph = DependencyGraphRepository(writer)
    for ref, status in (
        (CORE, LifecycleState.LOCKED),
        (MACRO_A, LifecycleState.APPROVED),
        (MACRO_B, LifecycleState.APPROVED),
        (SEQUENCE, LifecycleState.APPROVED),
        (SCENE, LifecycleState.APPROVED),
        (BEAT, LifecycleState.APPROVED),
        (PLANNER, LifecycleState.APPROVED),
    ):
        await _seed_version(versions, ref, status=status)
    return versions, graph


async def _seed_chain(
    writer: SQLiteWriteOwner,
    *,
    multi_macro_sequence: bool = False,
) -> tuple[VersionRepository, DependencyGraphRepository]:
    versions, graph = await _seed_refs(writer)
    await _edge(graph, CORE, MACRO_A)
    await _edge(graph, CORE, MACRO_B)
    await _edge(graph, MACRO_A, SEQUENCE)
    if multi_macro_sequence:
        await _edge(graph, MACRO_B, SEQUENCE)
    await _edge(graph, SEQUENCE, SCENE)
    await _edge(graph, SCENE, BEAT)
    return versions, graph


def _trace(
    artifact_type: NarrativeArtifactType,
    traced_ref: VersionRef,
    *,
    trace_version: str,
    parent_refs: tuple[VersionRef, ...] = (),
    sources: tuple[VersionRef, ...] = (PLANNER,),
) -> NarrativeTraceRecord:
    return NarrativeTraceRecord(
        project_id=PROJECT_ID,
        artifact_type=artifact_type,
        trace_version=VersionId(trace_version),
        traced_ref=traced_ref,
        root_story_core_ref=CORE,
        parent_refs=parent_refs,
        source_version_refs=sources,
    )


def _trace_provenance(value: NarrativeTraceRecord, reason: str = "record trace") -> Provenance:
    return build_narrative_trace_provenance(
        value,
        actor_ref="studio:imp028",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp028",),
        correlation_id="run:imp028",
    )


async def _supersede(
    versions: VersionRepository,
    old: VersionRef,
    *,
    new_version: str,
) -> VersionRef:
    new = VersionRef(logical_id=old.logical_id, version_id=VersionId(new_version))
    await versions.create_successor(
        metadata=_metadata(
            new,
            predecessor=old,
            reason="supersede exact source for IMP-028 test",
        ),
        payload={"fixture": new.logical_id.root, "version": new.version_id.root},
        supersession_reason="supersede exact source for IMP-028 test",
    )
    pointer = await versions.get_current(old.logical_id)
    assert pointer is not None
    await versions.update_current(
        logical_id=new.logical_id,
        version_id=new.version_id,
        status=pointer.status,
        expected_revision=pointer.revision,
    )
    return new


def test_trace_contract_rejects_project_prefix_collision_and_wrong_parent_type():
    with pytest.raises(ValidationError, match="same project"):
        NarrativeTraceRecord(
            project_id=PROJECT_ID,
            artifact_type=NarrativeArtifactType.SCENE,
            trace_version=VersionId("trace-v1"),
            traced_ref=VersionRef(
                logical_id=LogicalId("scene:project:film2:collision"),
                version_id=VersionId("scene-v1"),
            ),
            root_story_core_ref=CORE,
            parent_refs=(SEQUENCE,),
        )

    with pytest.raises(ValidationError, match="required canonical parent type"):
        _trace(
            NarrativeArtifactType.SCENE,
            SCENE,
            trace_version="trace-v1",
            parent_refs=(MACRO_A,),
        )


@pytest.mark.asyncio
async def test_top_down_and_bottom_up_why_exists_are_exact_version_traversals(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_chain(writer)
        repo = NarrativeTraceRepository(writer)
        value = _trace(
            NarrativeArtifactType.SCENE_DRAMATIC_BEAT,
            BEAT,
            trace_version="trace-beat-v1",
            parent_refs=(SCENE,),
        )
        artifact = await repo.create_trace(
            value=value,
            provenance=_trace_provenance(value),
            created_at=NOW,
        )

        incoming = await repo.graph.list_incoming(artifact.ref)
        assert {edge.source_ref for edge in incoming} == {BEAT, SCENE, CORE, PLANNER}
        assert {edge.edge_type for edge in incoming} == {"narrative_trace_source"}

        ancestors = await repo.trace_ancestors(BEAT, project_id=PROJECT_ID)
        assert {item.ref for item in ancestors} == {SCENE, SEQUENCE, MACRO_A, CORE}
        descendants = await repo.trace_descendants(CORE, project_id=PROJECT_ID)
        assert {item.ref for item in descendants} >= {MACRO_A, SEQUENCE, SCENE, BEAT}

        explanation = await repo.why_exists(artifact.ref)
        assert explanation.traced_ref == BEAT
        assert explanation.parent_refs == (SCENE,)
        assert explanation.root_story_core_ref == CORE
        assert explanation.state is NarrativeTraceState.CURRENT
        assert {item.ref for item in explanation.ancestors} == {
            SCENE,
            SEQUENCE,
            MACRO_A,
            CORE,
        }
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_sequence_supports_multiple_exact_macro_parents(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_chain(writer, multi_macro_sequence=True)
        repo = NarrativeTraceRepository(writer)
        value = _trace(
            NarrativeArtifactType.SEQUENCE,
            SEQUENCE,
            trace_version="trace-sequence-v1",
            parent_refs=(MACRO_A, MACRO_B),
        )
        artifact = await repo.create_trace(
            value=value,
            provenance=_trace_provenance(value),
            created_at=NOW,
        )
        assert artifact.value.parent_refs == (MACRO_A, MACRO_B)
        assert await repo.trace_state(artifact.ref) is NarrativeTraceState.CURRENT
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_missing_exact_parent_fails_with_trace_missing_parent(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_refs(writer)
        repo = NarrativeTraceRepository(writer)
        missing_parent = VersionRef(
            logical_id=SEQUENCE.logical_id,
            version_id=VersionId("missing-sequence-version"),
        )
        value = _trace(
            NarrativeArtifactType.SCENE,
            SCENE,
            trace_version="trace-scene-v1",
            parent_refs=(missing_parent,),
        )
        with pytest.raises(NarrativeTraceGateBlocked) as exc_info:
            await repo.validate_trace(value)
        assert exc_info.value.code is NarrativeTraceFindingCode.TRACE_MISSING_PARENT
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_existing_parent_without_required_edge_is_orphan(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_refs(writer)
        repo = NarrativeTraceRepository(writer)
        value = _trace(
            NarrativeArtifactType.SCENE,
            SCENE,
            trace_version="trace-scene-v1",
            parent_refs=(SEQUENCE,),
        )
        with pytest.raises(NarrativeTraceGateBlocked) as exc_info:
            await repo.validate_trace(value)
        assert exc_info.value.code is NarrativeTraceFindingCode.TRACE_ORPHAN_ARTIFACT
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_declared_parent_must_exactly_match_dependency_graph_truth(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, graph = await _seed_refs(writer)
        await _edge(graph, CORE, MACRO_B)
        await _edge(graph, MACRO_B, SEQUENCE)
        repo = NarrativeTraceRepository(writer)
        value = _trace(
            NarrativeArtifactType.SEQUENCE,
            SEQUENCE,
            trace_version="trace-sequence-v1",
            parent_refs=(MACRO_A,),
        )
        with pytest.raises(NarrativeTraceGateBlocked) as exc_info:
            await repo.validate_trace(value)
        assert (
            exc_info.value.code
            is NarrativeTraceFindingCode.TRACE_CONTRADICTORY_PARENT
        )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_canonical_ancestry_cycle_fails_closed(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, graph = await _seed_chain(writer)
        await _edge(graph, BEAT, CORE)
        repo = NarrativeTraceRepository(writer)
        value = _trace(
            NarrativeArtifactType.SCENE_DRAMATIC_BEAT,
            BEAT,
            trace_version="trace-beat-v1",
            parent_refs=(SCENE,),
        )
        with pytest.raises(NarrativeTraceGateBlocked) as exc_info:
            await repo.validate_trace(value)
        assert exc_info.value.code is NarrativeTraceFindingCode.TRACE_CYCLE
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_exact_source_fails_closed_before_trace_persistence(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions, _ = await _seed_chain(writer)
        await _supersede(versions, PLANNER, new_version="planner-v2")
        repo = NarrativeTraceRepository(writer)
        value = _trace(
            NarrativeArtifactType.SCENE,
            SCENE,
            trace_version="trace-scene-v1",
            parent_refs=(SEQUENCE,),
        )
        with pytest.raises(NarrativeTraceGateBlocked) as exc_info:
            await repo.create_trace(
                value=value,
                provenance=_trace_provenance(value),
                created_at=NOW,
            )
        assert exc_info.value.code is NarrativeTraceFindingCode.TRACE_STALE_SOURCE
        assert await repo.get_current_trace(
            artifact_type=NarrativeArtifactType.SCENE,
            traced_ref=SCENE,
        ) is None
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_source_supersession_derives_invalidated_trace_state(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions, _ = await _seed_chain(writer)
        repo = NarrativeTraceRepository(writer)
        value = _trace(
            NarrativeArtifactType.SCENE,
            SCENE,
            trace_version="trace-scene-v1",
            parent_refs=(SEQUENCE,),
        )
        artifact = await repo.create_trace(
            value=value,
            provenance=_trace_provenance(value),
            created_at=NOW,
        )
        assert await repo.trace_state(artifact.ref) is NarrativeTraceState.CURRENT

        planner_v2 = await _supersede(versions, PLANNER, new_version="planner-v2")
        assert await repo.trace_state(artifact.ref) is NarrativeTraceState.INVALIDATED

        invalidations = InvalidationRepository(writer, graph=repo.graph)
        records = await invalidations.create_for_change(
            cause="planner source superseded",
            source_old=PLANNER,
            source_new=planner_v2,
            provenance=_seed_provenance("invalidate trace after source supersession"),
            scope="narrative trace lineage evidence",
            repair_or_recompute_requirement="recompute NarrativeTrace from current exact sources",
        )
        assert any(
            record.affected_object_id == artifact.ref.logical_id
            and record.affected_object_version == artifact.ref.version_id
            and record.dependency_edge_type == "narrative_trace_source"
            for record in records
        )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_trace_revision_is_immutable_successor_and_old_trace_is_superseded(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_chain(writer)
        repo = NarrativeTraceRepository(writer)
        first_value = _trace(
            NarrativeArtifactType.STORY_CORE,
            CORE,
            trace_version="trace-core-v1",
            parent_refs=(),
        )
        first = await repo.create_trace(
            value=first_value,
            provenance=_trace_provenance(first_value, "initial core trace"),
            created_at=NOW,
        )
        pointer = await repo.versions.get_current(first_value.logical_id)
        assert pointer is not None

        second_value = _trace(
            NarrativeArtifactType.STORY_CORE,
            CORE,
            trace_version="trace-core-v2",
            parent_refs=(),
        )
        second = await repo.revise_trace(
            value=second_value,
            predecessor=first.ref,
            provenance=_trace_provenance(second_value, "revise core trace evidence"),
            created_at=NOW,
            expected_revision=pointer.revision,
        )

        assert first.ref != second.ref
        assert await repo.get_trace(first.ref) is not None
        assert await repo.trace_state(first.ref) is NarrativeTraceState.SUPERSEDED
        assert await repo.trace_state(second.ref) is NarrativeTraceState.CURRENT
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_trace_provenance_must_exactly_bind_declared_sources(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_chain(writer)
        repo = NarrativeTraceRepository(writer)
        value = _trace(
            NarrativeArtifactType.SCENE,
            SCENE,
            trace_version="trace-scene-v1",
            parent_refs=(SEQUENCE,),
        )
        wrong = Provenance(
            source_refs=("evidence:wrong",),
            actor_ref="studio:imp028",
            reason="wrong bindings",
            recorded_at=NOW,
        )
        with pytest.raises(NarrativeTraceIdentityError, match="exactly bind"):
            await repo.create_trace(value=value, provenance=wrong, created_at=NOW)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_story_core_rejects_canonical_parent_edge_even_without_cycle(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, graph = await _seed_refs(writer)
        await _edge(graph, MACRO_A, CORE)
        repo = NarrativeTraceRepository(writer)
        value = _trace(
            NarrativeArtifactType.STORY_CORE,
            CORE,
            trace_version="trace-core-v1",
            parent_refs=(),
        )
        with pytest.raises(NarrativeTraceGateBlocked) as exc_info:
            await repo.validate_trace(value)
        assert (
            exc_info.value.code
            is NarrativeTraceFindingCode.TRACE_CONTRADICTORY_PARENT
        )
    finally:
        await writer.close()
