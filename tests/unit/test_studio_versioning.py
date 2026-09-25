"""IMP-004 tests for version/provenance repository primitives."""

from __future__ import annotations

from datetime import datetime, timezone

import aiosqlite
import pytest

from agent.studio import (
    CASConflict,
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SQLiteWriteOwner,
    VersionId,
    VersionRef,
)
from agent.studio.persistence import Migration, ensure_schema_compatibility
from agent.studio.versioning import (
    ContentHashMismatch,
    VersionRepository,
    VersionNotFound,
)


NOW = datetime(2026, 9, 25, 9, 0, tzinfo=timezone.utc)


def _metadata(
    logical: str,
    version: str,
    *,
    predecessor: str | None = None,
    reason: str = "author canonical semantic version",
    content_hash: str | None = None,
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
        provenance=Provenance(
            source_refs=("evidence:seed",),
            actor_ref="studio:test",
            reason=reason,
            recorded_at=NOW,
            correlation_id="run:imp004",
        ),
        created_at=NOW,
        content_hash=content_hash,
    )


@pytest.mark.asyncio
async def test_initial_version_persists_provenance_and_pointer_separately(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    repo = VersionRepository(writer)

    try:
        stored = await repo.create_initial(
            metadata=_metadata("story:1", "v1"),
            payload={"title": "First", "facts": [1, 2]},
        )
        pointer = await repo.get_current(LogicalId("story:1"))
        loaded = await repo.get_version(
            VersionRef(logical_id=LogicalId("story:1"), version_id=VersionId("v1"))
        )

        assert stored.metadata.content_hash is not None
        assert loaded == stored
        assert loaded is not None
        assert loaded.metadata.provenance.actor_ref == "studio:test"
        assert loaded.metadata.provenance.correlation_id == "run:imp004"
        assert pointer is not None
        assert pointer.version_id == VersionId("v1")
        assert pointer.status is LifecycleState.DRAFT
        assert pointer.revision == 0
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_approved_semantic_version_is_immutable_in_database(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    repo = VersionRepository(writer)

    try:
        await repo.create_initial(
            metadata=_metadata("scene:1", "v1"),
            payload={"text": "locked truth"},
        )
        pointer = await repo.update_current(
            logical_id=LogicalId("scene:1"),
            version_id=VersionId("v1"),
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )
        assert pointer.status is LifecycleState.APPROVED
        assert pointer.revision == 1

        async def illegal_update(tx):
            await tx.execute(
                """
                UPDATE studio_semantic_version
                SET payload_json='{"text":"mutated"}'
                WHERE logical_id='scene:1' AND version_id='v1'
                """
            )

        with pytest.raises(aiosqlite.IntegrityError, match="immutable"):
            await writer.execute(illegal_update)

        loaded = await repo.get_version(
            VersionRef(logical_id=LogicalId("scene:1"), version_id=VersionId("v1"))
        )
        assert loaded is not None
        assert loaded.payload == {"text": "locked truth"}
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_successor_preserves_old_version_and_supersession_history(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    repo = VersionRepository(writer)

    try:
        await repo.create_initial(
            metadata=_metadata("shot:9", "v1"),
            payload={"intent": "wide"},
        )
        successor = await repo.create_successor(
            metadata=_metadata(
                "shot:9",
                "v2",
                predecessor="v1",
                reason="repair framing",
            ),
            payload={"intent": "medium"},
        )

        old = await repo.get_version(
            VersionRef(logical_id=LogicalId("shot:9"), version_id=VersionId("v1"))
        )
        current = await repo.get_current(LogicalId("shot:9"))
        history = await repo.list_supersession_history(LogicalId("shot:9"))

        assert old is not None
        assert old.payload == {"intent": "wide"}
        assert successor.payload == {"intent": "medium"}
        assert current is not None
        assert current.version_id == VersionId("v1")
        assert len(history) == 1
        assert history[0].predecessor.version_id == VersionId("v1")
        assert history[0].successor.version_id == VersionId("v2")
        assert history[0].reason == "repair framing"
        assert history[0].provenance.reason == "repair framing"
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_current_pointer_switch_uses_cas_and_rejects_stale_revision(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    repo = VersionRepository(writer)

    try:
        await repo.create_initial(
            metadata=_metadata("profile:1", "v1"),
            payload={"mode": "a"},
        )
        await repo.create_successor(
            metadata=_metadata("profile:1", "v2", predecessor="v1"),
            payload={"mode": "b"},
        )

        updated = await repo.update_current(
            logical_id=LogicalId("profile:1"),
            version_id=VersionId("v2"),
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )
        assert updated.version_id == VersionId("v2")
        assert updated.status is LifecycleState.APPROVED
        assert updated.revision == 1

        with pytest.raises(CASConflict):
            await repo.update_current(
                logical_id=LogicalId("profile:1"),
                version_id=VersionId("v1"),
                status=LifecycleState.DRAFT,
                expected_revision=0,
            )

        current = await repo.get_current(LogicalId("profile:1"))
        assert current == updated
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_restart_readback_preserves_versions_pointer_and_history(tmp_path):
    db_path = tmp_path / "studio.db"
    writer = SQLiteWriteOwner(db_path)
    await writer.start()
    repo = VersionRepository(writer)

    await repo.create_initial(
        metadata=_metadata("story:restart", "v1"),
        payload={"step": 1},
    )
    await repo.create_successor(
        metadata=_metadata("story:restart", "v2", predecessor="v1"),
        payload={"step": 2},
    )
    await repo.update_current(
        logical_id=LogicalId("story:restart"),
        version_id=VersionId("v2"),
        status=LifecycleState.LOCKED,
        expected_revision=0,
    )
    await writer.close()

    writer2 = SQLiteWriteOwner(db_path)
    await writer2.start()
    repo2 = VersionRepository(writer2)
    try:
        current = await repo2.get_current(LogicalId("story:restart"))
        v1 = await repo2.get_version(
            VersionRef(
                logical_id=LogicalId("story:restart"),
                version_id=VersionId("v1"),
            )
        )
        v2 = await repo2.get_version(
            VersionRef(
                logical_id=LogicalId("story:restart"),
                version_id=VersionId("v2"),
            )
        )
        history = await repo2.list_supersession_history(
            LogicalId("story:restart")
        )

        assert current is not None
        assert current.version_id == VersionId("v2")
        assert current.status is LifecycleState.LOCKED
        assert current.revision == 1
        assert v1 is not None and v1.payload == {"step": 1}
        assert v2 is not None and v2.payload == {"step": 2}
        assert len(history) == 1
    finally:
        await writer2.close()


@pytest.mark.asyncio
async def test_successor_requires_existing_predecessor(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    repo = VersionRepository(writer)
    try:
        with pytest.raises(VersionNotFound):
            await repo.create_successor(
                metadata=_metadata("missing:1", "v2", predecessor="v1"),
                payload={"value": 2},
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_payload_hash_mismatch_is_rejected_before_write(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    repo = VersionRepository(writer)
    try:
        with pytest.raises(ContentHashMismatch):
            await repo.create_initial(
                metadata=_metadata(
                    "hash:1",
                    "v1",
                    content_hash="sha256:" + ("0" * 64),
                ),
                payload={"value": "actual"},
            )
        assert await repo.get_current(LogicalId("hash:1")) is None
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_schema_v1_upgrades_to_v2_without_losing_migration_history(tmp_path):
    db_path = tmp_path / "studio.db"
    v1_only = (Migration(1, "studio_persistence_foundation"),)
    assert await ensure_schema_compatibility(
        db_path,
        supported_version=1,
        migrations=v1_only,
    ) == 1

    writer = SQLiteWriteOwner(db_path)
    await writer.start()
    try:
        async with aiosqlite.connect(str(db_path)) as db:
            rows = await (
                await db.execute(
                    """
                    SELECT version, name
                    FROM studio_schema_migration
                    ORDER BY version
                    """
                )
            ).fetchall()
        assert rows == [
            (1, "studio_persistence_foundation"),
            (2, "studio_version_provenance_repository"),
        ]
    finally:
        await writer.close()
