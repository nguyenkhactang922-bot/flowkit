"""IMP-005 tests for DependencyGraph + durable InvalidationRecord."""

from __future__ import annotations

from datetime import datetime, timezone

import aiosqlite
import pytest

from agent.studio import (
    CASConflict,
    DEFAULT_MIGRATIONS,
    DependencyEdgeConflict,
    DependencyGraphRepository,
    InvalidationAlreadyResolved,
    InvalidationRepository,
    InvalidationStatus,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SQLiteWriteOwner,
    VersionId,
    VersionRef,
    VersionRepository,
)
from agent.studio.persistence import ensure_schema_compatibility


NOW = datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc)


def _provenance(reason: str = "dependency truth") -> Provenance:
    return Provenance(
        source_refs=("evidence:imp005",),
        actor_ref="studio:test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp005",
    )


def _metadata(
    logical: str,
    version: str,
    *,
    predecessor: str | None = None,
) -> SemanticRecordMetadata:
    logical_id = LogicalId(logical)
    predecessor_ref = (
        VersionRef(logical_id=logical_id, version_id=VersionId(predecessor))
        if predecessor is not None
        else None
    )
    return SemanticRecordMetadata(
        logical_id=logical_id,
        version_id=VersionId(version),
        predecessor=predecessor_ref,
        provenance=_provenance("author semantic version"),
        created_at=NOW,
    )


async def _seed_graph(writer: SQLiteWriteOwner):
    versions = VersionRepository(writer)

    await versions.create_initial(
        metadata=_metadata("reference:hero", "v1"),
        payload={"look": "old"},
    )
    await versions.create_successor(
        metadata=_metadata("reference:hero", "v2", predecessor="v1"),
        payload={"look": "new"},
    )
    await versions.create_initial(
        metadata=_metadata("shotir:1", "v1"),
        payload={"shot": 1},
    )
    await versions.create_initial(
        metadata=_metadata("compiled:1", "v1"),
        payload={"compiled": 1},
    )
    await versions.create_initial(
        metadata=_metadata("unrelated:1", "v1"),
        payload={"keep": True},
    )

    source_old = VersionRef(
        logical_id=LogicalId("reference:hero"),
        version_id=VersionId("v1"),
    )
    source_new = VersionRef(
        logical_id=LogicalId("reference:hero"),
        version_id=VersionId("v2"),
    )
    shot = VersionRef(
        logical_id=LogicalId("shotir:1"),
        version_id=VersionId("v1"),
    )
    compiled = VersionRef(
        logical_id=LogicalId("compiled:1"),
        version_id=VersionId("v1"),
    )
    unrelated = VersionRef(
        logical_id=LogicalId("unrelated:1"),
        version_id=VersionId("v1"),
    )

    graph = DependencyGraphRepository(writer)
    edge1 = await graph.create_edge(
        source=source_old,
        dependent=shot,
        edge_type="REFERENCE_BINDING",
        dependency_reason="ShotIR binds exact hero reference version",
        provenance=_provenance(),
        created_at=NOW,
    )
    edge2 = await graph.create_edge(
        source=shot,
        dependent=compiled,
        edge_type="COMPILES_TO",
        dependency_reason="Compiled request derives from ShotIR version",
        provenance=_provenance(),
        created_at=NOW,
    )
    return graph, source_old, source_new, shot, compiled, unrelated, edge1, edge2


@pytest.mark.asyncio
async def test_forward_reverse_reachability_is_exact_and_deterministic(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        graph, source_old, _, shot, compiled, unrelated, edge1, edge2 = (
            await _seed_graph(writer)
        )

        descendants = await graph.descendants(source_old)
        assert [item.ref for item in descendants] == [shot, compiled]
        assert [item.depth for item in descendants] == [1, 2]
        assert descendants[0].path_edge_ids == (edge1.edge_id,)
        assert descendants[1].path_edge_ids == (edge1.edge_id, edge2.edge_id)

        ancestors = await graph.ancestors(compiled)
        assert [item.ref for item in ancestors] == [shot, source_old]
        assert [item.depth for item in ancestors] == [1, 2]

        assert await graph.descendants(unrelated) == []
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_invalidation_is_selective_and_preserves_unrelated_descendants(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        graph, source_old, source_new, shot, compiled, unrelated, _, _ = (
            await _seed_graph(writer)
        )
        repo = InvalidationRepository(writer, graph)

        records = await repo.create_for_change(
            cause="REFERENCE_VERSION_CHANGED",
            source_old=source_old,
            source_new=source_new,
            provenance=_provenance("accepted reference successor"),
            scope="REFERENCE_DEPENDENTS",
            repair_or_recompute_requirement="recompute affected descendants",
        )

        affected = {
            VersionRef(
                logical_id=record.affected_object_id,
                version_id=record.affected_object_version,
            )
            for record in records
        }
        assert affected == {shot, compiled}
        assert unrelated not in affected
        assert all(record.status is InvalidationStatus.UNRESOLVED for record in records)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_duplicate_change_replay_is_idempotent(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        graph, source_old, source_new, *_ = await _seed_graph(writer)
        repo = InvalidationRepository(writer, graph)
        kwargs = dict(
            cause="REFERENCE_VERSION_CHANGED",
            source_old=source_old,
            source_new=source_new,
            provenance=_provenance("accepted reference successor"),
            scope="REFERENCE_DEPENDENTS",
            repair_or_recompute_requirement="recompute affected descendants",
        )

        first = await repo.create_for_change(**kwargs)
        second = await repo.create_for_change(**kwargs)

        assert [record.invalidation_id for record in second] == [
            record.invalidation_id for record in first
        ]
        assert [record.dedupe_key for record in second] == [
            record.dedupe_key for record in first
        ]

        async with aiosqlite.connect(str(writer.db_path)) as db:
            count = await (
                await db.execute("SELECT COUNT(*) FROM studio_invalidation_record")
            ).fetchone()
        assert count == (2,)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_restart_replays_only_unresolved_records(tmp_path):
    db_path = tmp_path / "studio.db"
    writer = SQLiteWriteOwner(db_path)
    await writer.start()
    graph, source_old, source_new, *_ = await _seed_graph(writer)
    repo = InvalidationRepository(writer, graph)
    records = await repo.create_for_change(
        cause="REFERENCE_VERSION_CHANGED",
        source_old=source_old,
        source_new=source_new,
        provenance=_provenance("accepted reference successor"),
        scope="REFERENCE_DEPENDENTS",
        repair_or_recompute_requirement="recompute affected descendants",
    )
    await repo.resolve(
        invalidation_id=records[0].invalidation_id,
        expected_revision=0,
        resolution_record_id="repair:1",
        provenance=_provenance("repair complete"),
    )
    await writer.close()

    writer2 = SQLiteWriteOwner(db_path)
    await writer2.start()
    repo2 = InvalidationRepository(writer2)
    try:
        unresolved = await repo2.list_unresolved()
        assert len(unresolved) == 1
        assert unresolved[0].invalidation_id == records[1].invalidation_id
        assert unresolved[0].status is InvalidationStatus.UNRESOLVED
    finally:
        await writer2.close()


@pytest.mark.asyncio
async def test_resolution_uses_cas_and_retains_transition_history(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        graph, source_old, source_new, *_ = await _seed_graph(writer)
        repo = InvalidationRepository(writer, graph)
        records = await repo.create_for_change(
            cause="REFERENCE_VERSION_CHANGED",
            source_old=source_old,
            source_new=source_new,
            provenance=_provenance("accepted reference successor"),
            scope="REFERENCE_DEPENDENTS",
            repair_or_recompute_requirement="recompute affected descendants",
        )
        record = records[0]

        with pytest.raises(CASConflict):
            await repo.resolve(
                invalidation_id=record.invalidation_id,
                expected_revision=7,
                resolution_record_id="repair:stale",
                provenance=_provenance("stale resolution"),
            )

        resolved = await repo.resolve(
            invalidation_id=record.invalidation_id,
            expected_revision=0,
            resolution_record_id="repair:ok",
            provenance=_provenance("repair complete"),
        )
        assert resolved.status is InvalidationStatus.RESOLVED
        assert resolved.revision == 1
        assert resolved.resolution_record_id == "repair:ok"
        assert resolved.resolved_at is not None

        history = await repo.list_resolution_history(record.invalidation_id)
        assert len(history) == 1
        assert history[0].from_status is InvalidationStatus.UNRESOLVED
        assert history[0].to_status is InvalidationStatus.RESOLVED
        assert history[0].from_revision == 0
        assert history[0].to_revision == 1

        with pytest.raises(InvalidationAlreadyResolved):
            await repo.resolve(
                invalidation_id=record.invalidation_id,
                expected_revision=1,
                resolution_record_id="repair:again",
                provenance=_provenance("duplicate resolution"),
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_cause_and_dependency_edge_truth_are_immutable(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        graph, source_old, source_new, *_ = await _seed_graph(writer)
        repo = InvalidationRepository(writer, graph)
        record = (
            await repo.create_for_change(
                cause="REFERENCE_VERSION_CHANGED",
                source_old=source_old,
                source_new=source_new,
                provenance=_provenance("accepted reference successor"),
                scope="REFERENCE_DEPENDENTS",
                repair_or_recompute_requirement="recompute affected descendants",
            )
        )[0]

        async def mutate_cause(tx):
            await tx.execute(
                """
                UPDATE studio_invalidation_record
                SET cause='MUTATED'
                WHERE invalidation_id=?
                """,
                (record.invalidation_id,),
            )

        with pytest.raises(aiosqlite.IntegrityError, match="immutable"):
            await writer.execute(mutate_cause)

        outgoing = await graph.list_outgoing(source_old)
        async def mutate_edge(tx):
            await tx.execute(
                """
                UPDATE studio_dependency_edge
                SET dependency_reason='rewritten'
                WHERE edge_id=?
                """,
                (outgoing[0].edge_id,),
            )

        with pytest.raises(aiosqlite.IntegrityError, match="immutable"):
            await writer.execute(mutate_edge)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_dependency_edge_replay_is_idempotent_but_conflicting_truth_rejected(
    tmp_path,
):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        graph, source_old, _, shot, _, _, edge1, _ = await _seed_graph(writer)

        replay = await graph.create_edge(
            source=source_old,
            dependent=shot,
            edge_type="REFERENCE_BINDING",
            dependency_reason="ShotIR binds exact hero reference version",
            provenance=_provenance(),
            created_at=NOW,
        )
        assert replay == edge1

        with pytest.raises(DependencyEdgeConflict):
            await graph.create_edge(
                source=source_old,
                dependent=shot,
                edge_type="REFERENCE_BINDING",
                dependency_reason="different immutable reason",
                provenance=_provenance(),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_schema_v2_upgrades_to_v3_and_preserves_migration_history(tmp_path):
    db_path = tmp_path / "studio.db"
    assert await ensure_schema_compatibility(
        db_path,
        supported_version=2,
        migrations=DEFAULT_MIGRATIONS[:2],
    ) == 2

    writer = SQLiteWriteOwner(db_path)
    await writer.start()
    try:
        async with aiosqlite.connect(str(db_path)) as db:
            rows = await (
                await db.execute(
                    "SELECT version, name FROM studio_schema_migration ORDER BY version"
                )
            ).fetchall()
        assert rows == [
            (1, "studio_persistence_foundation"),
            (2, "studio_version_provenance_repository"),
            (3, "studio_dependency_invalidation"),
        ]
    finally:
        await writer.close()
