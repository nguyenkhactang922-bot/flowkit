"""IMP-040 tests for canonical EntityVersion compatibility adapter."""

from __future__ import annotations

from datetime import datetime, timezone

import aiosqlite
import pytest

from agent.sdk.models.character import Character
from agent.studio.entity import (
    CanonicalEntityAdapter,
    CanonicalEntityRepository,
    EntityIdentityError,
    EntityKind,
    LegacyEntitySnapshot,
    entity_logical_id,
)
from agent.studio.persistence import SQLiteWriteOwner
from agent.studio.primitives import LifecycleState, LogicalId, VersionId, VersionRef


NOW = datetime(2026, 9, 29, 9, 0, tzinfo=timezone.utc)


def _legacy(
    *,
    entity_id: str = "legacy-char-001",
    name: str = "Lan",
    description: str = "Vietnamese woman in her thirties",
    media_id: str | None = "11111111-1111-1111-1111-111111111111",
    reference_image_url: str | None = "https://example.invalid/reference.png",
    project_ids: tuple[LogicalId, ...] = (LogicalId("project-001"),),
) -> LegacyEntitySnapshot:
    return LegacyEntitySnapshot(
        id=entity_id,
        name=name,
        entity_type=EntityKind.CHARACTER,
        project_ids=project_ids,
        slug="lan",
        description=description,
        voice_description="warm calm voice",
        image_prompt="legacy provider-facing portrait prompt",
        reference_image_url=reference_image_url,
        media_id=media_id,
        updated_at="2026-09-29T09:00:00Z",
    )


def test_legacy_character_maps_to_stable_canonical_entity_identity():
    legacy = Character(
        id="legacy-char-001",
        name="Lan",
        entity_type="character",
        description="Vietnamese woman in her thirties",
        media_id="11111111-1111-1111-1111-111111111111",
    )
    snapshot = LegacyEntitySnapshot.from_legacy(
        legacy,
        project_ids=(LogicalId("project-001"),),
    )

    first = CanonicalEntityAdapter.materialize(snapshot, version_id=VersionId("v1"))
    second = CanonicalEntityAdapter.materialize(snapshot, version_id=VersionId("v2"))

    assert first.entity_id == LogicalId("entity:legacy-char-001")
    assert second.entity_id == first.entity_id
    assert first.version_id != second.version_id
    assert first.project_ids == (LogicalId("project-001"),)


def test_reference_media_and_legacy_prompt_are_not_entity_semantic_truth():
    snapshot = _legacy()
    entity = CanonicalEntityAdapter.materialize(snapshot, version_id=VersionId("v1"))
    payload = entity.model_dump(mode="json")

    assert "media_id" not in payload
    assert "reference_image_url" not in payload
    assert "image_prompt" not in payload
    assert payload["name"] == "Lan"
    assert payload["kind"] == "character"

    binding = CanonicalEntityAdapter.compatibility_binding(
        snapshot,
        canonical_ref=entity.ref,
    )
    assert binding.legacy_media_id == snapshot.media_id
    assert binding.legacy_reference_image_url == snapshot.reference_image_url
    assert binding.canonical_ref == entity.ref


@pytest.mark.asyncio
async def test_initial_entity_version_persists_in_shared_version_repository(tmp_path):
    db_path = tmp_path / "studio.db"
    writer = SQLiteWriteOwner(db_path)
    await writer.start()
    repo = CanonicalEntityRepository(writer)
    try:
        result = await repo.create_initial_from_legacy(
            snapshot=_legacy(),
            version_id=VersionId("v1"),
            actor_ref="studio:test",
            reason="import legacy entity into canonical version authority",
            recorded_at=NOW,
            correlation_id="run:imp040",
        )

        loaded = await repo.get_version(result.artifact.ref)
        pointer = await repo.get_current_pointer(result.artifact.value.entity_id)

        assert loaded == result.artifact
        assert loaded is not None
        assert loaded.metadata.provenance.source_refs == (
            "legacy-character:legacy-char-001@2026-09-29T09:00:00Z",
        )
        assert pointer is not None
        assert pointer.version_id == VersionId("v1")
        assert pointer.status is LifecycleState.DRAFT

        async with aiosqlite.connect(str(db_path)) as db:
            tables = {
                row[0]
                for row in await (
                    await db.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                ).fetchall()
            }
        assert "studio_semantic_version" in tables
        assert not any(name.startswith("studio_entity") for name in tables)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_successor_keeps_logical_id_and_preserves_old_version(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    repo = CanonicalEntityRepository(writer)
    try:
        initial = await repo.create_initial_from_legacy(
            snapshot=_legacy(),
            version_id=VersionId("v1"),
            actor_ref="studio:test",
            reason="initial import",
            recorded_at=NOW,
        )
        successor = await repo.create_successor_from_legacy(
            snapshot=_legacy(name="Lan Nguyen", description="updated canonical description"),
            version_id=VersionId("v2"),
            predecessor=initial.artifact.ref,
            actor_ref="studio:test",
            reason="semantic entity description revision",
            recorded_at=NOW,
        )

        old = await repo.get_version(initial.artifact.ref)
        new = await repo.get_version(successor.artifact.ref)

        assert old is not None and old.value.name == "Lan"
        assert new is not None and new.value.name == "Lan Nguyen"
        assert old.value.entity_id == new.value.entity_id
        assert new.metadata.predecessor == initial.artifact.ref

        pointer = await repo.promote_current(
            ref=successor.artifact.ref,
            expected_revision=0,
            status=LifecycleState.APPROVED,
        )
        assert pointer.version_id == VersionId("v2")
        assert pointer.status is LifecycleState.APPROVED
        assert pointer.revision == 1
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_successor_rejects_predecessor_from_different_entity(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    repo = CanonicalEntityRepository(writer)
    try:
        with pytest.raises(EntityIdentityError):
            await repo.create_successor_from_legacy(
                snapshot=_legacy(entity_id="legacy-char-001"),
                version_id=VersionId("v2"),
                predecessor=VersionRef(
                    logical_id=entity_logical_id("legacy-char-999"),
                    version_id=VersionId("v1"),
                ),
                actor_ref="studio:test",
                reason="invalid cross-entity successor",
                recorded_at=NOW,
            )
    finally:
        await writer.close()


def test_project_links_are_deduplicated_without_changing_entity_identity():
    snapshot = _legacy(
        project_ids=(
            LogicalId("project-001"),
            LogicalId("project-001"),
            LogicalId("project-002"),
        )
    )
    entity = CanonicalEntityAdapter.materialize(snapshot, version_id=VersionId("v1"))

    assert entity.entity_id == LogicalId("entity:legacy-char-001")
    assert entity.project_ids == (
        LogicalId("project-001"),
        LogicalId("project-002"),
    )


def test_binding_rejects_shadow_canonical_identity():
    snapshot = _legacy()
    with pytest.raises(ValueError, match="stable mapping"):
        CanonicalEntityAdapter.compatibility_binding(
            snapshot,
            canonical_ref=VersionRef(
                logical_id=LogicalId("entity:someone-else"),
                version_id=VersionId("v1"),
            ),
        )
