"""IMP-081 operational Scene -> execution projection authority tests."""

from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from agent.studio import (
    GenerationJobAxis,
    LegacyImportAntiCorruptionService,
    LegacyImportDisposition,
    LegacyImportRequest,
    LegacyMediaRole,
    LegacyOrientation,
    LegacySourceEvidence,
    LegacySourceKind,
    LogicalId,
    OperationalSceneExecutionProjection,
    OperationalSceneExecutionProjectionService,
    OperationalSceneProjectionGateBlocked,
    OperationalSceneProjectionRequest,
    SQLiteReadRepository,
    SQLiteWriteOwner,
    TransitionOwner,
    VersionId,
    VersionRef,
    operational_scene_projection_logical_id,
)
from tests.unit.test_studio_directing import NOW, PROJECT_ID
from tests.unit.test_studio_generation_job import _job_fixture, _transition


MIGRATION_RUN = "imp081-run-001"
TARGET_SCHEMA = "studio-schema-v9"
SIGNED_VIDEO_URL = "https://example.invalid/video/legacy-media-video-001?token=secret-signed-value"


def _scene_row(**updates):
    row = {
        "id": "legacy-scene-001",
        "video_id": "legacy-video-001",
        "display_order": 3,
        "prompt": "A man returns home and finds an old cassette on the table.",
        "image_prompt": "cinematic living room, late afternoon",
        "video_prompt": "0-3s: slow push in toward cassette",
        "narrator_text": "He had not been home in years.",
        "parent_scene_id": None,
        "chain_type": "ROOT",
        "source": "legacy-flowkit",
        "vertical_image_media_id": "legacy-media-image-001",
        "vertical_image_status": "COMPLETED",
        "vertical_video_media_id": "legacy-media-video-001",
        "vertical_video_url": SIGNED_VIDEO_URL,
        "vertical_video_status": "COMPLETED",
    }
    row.update(updates)
    return row


def _source(row) -> LegacySourceEvidence:
    return LegacySourceEvidence.from_legacy(
        row,
        source_kind=LegacySourceKind.OPERATIONAL_SCENE,
        source_table="scene",
        source_id=str(row["id"]),
        source_schema_version="flowkit-v1",
    )


def _import_request(
    row,
    *,
    version: str,
    shot_ref: VersionRef | None = None,
    generation_job_id: LogicalId | None = None,
    generation_job_revision: int | None = None,
) -> LegacyImportRequest:
    return LegacyImportRequest(
        migration_run_id=MIGRATION_RUN,
        target_schema_version=TARGET_SCHEMA,
        record_version_id=VersionId(version),
        source=_source(row),
        canonical_project_id=PROJECT_ID,
        explicit_target_refs=() if shot_ref is None else (shot_ref,),
        generation_job_id=generation_job_id,
        generation_job_revision=generation_job_revision,
        actor_ref="studio:imp081-test",
        reason="classify operational scene compatibility proof",
        recorded_at=NOW,
        correlation_id="run:imp081-import",
        evidence_refs=("evidence:imp081-import",),
    )


def _projection_request(mapping_ref: VersionRef, row, *, version: str = "projection-v1"):
    return OperationalSceneProjectionRequest(
        scene_mapping_ref=mapping_ref,
        scene_row=row,
        result_version_id=VersionId(version),
        actor_ref="studio:imp081-test",
        reason="project legacy operational scene into execution compatibility view",
        recorded_at=NOW,
        correlation_id="run:imp081-projection",
        evidence_refs=("evidence:imp081-projection",),
    )


async def _mapped_fixture(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    job_repo, job, ir, *_ = await _job_fixture(writer)
    row = _scene_row()
    importer = LegacyImportAntiCorruptionService(writer)
    mapping = await importer.assess(
        _import_request(
            row,
            version="mapping-v1",
            shot_ref=ir.shot_ref,
            generation_job_id=job.generation_job_id,
            generation_job_revision=job.revision,
        )
    )
    assert mapping.artifact.value.disposition is LegacyImportDisposition.COMPATIBILITY_MAPPED
    return writer, job_repo, job, ir, row, mapping


@pytest.mark.asyncio
async def test_exact_projection_keeps_execution_media_reachable_without_minting_cinematic_truth(tmp_path):
    writer, _job_repo, job, ir, row, mapping = await _mapped_fixture(tmp_path)
    try:
        reader = SQLiteReadRepository(writer.db_path)
        before_rows = await reader.fetchall("SELECT logical_id FROM studio_semantic_version")
        before_ids = {str(item["logical_id"]) for item in before_rows}

        service = OperationalSceneExecutionProjectionService(writer)
        result = await service.project(_projection_request(mapping.artifact.ref, row))
        value = result.artifact.value

        assert value.projection_id == operational_scene_projection_logical_id(
            MIGRATION_RUN, "legacy-scene-001"
        )
        assert value.shot_refs == (ir.shot_ref,)
        assert value.generation_job_id == job.generation_job_id
        assert value.generation_job_revision == job.revision
        assert value.legacy_scene_id == "legacy-scene-001"
        assert value.legacy_video_id == "legacy-video-001"
        assert {(item.orientation, item.role, item.media_id) for item in value.media} >= {
            (LegacyOrientation.VERTICAL, LegacyMediaRole.IMAGE, "legacy-media-image-001"),
            (LegacyOrientation.VERTICAL, LegacyMediaRole.VIDEO, "legacy-media-video-001"),
        }
        video = next(item for item in value.media if item.role is LegacyMediaRole.VIDEO)
        assert video.output_url == SIGNED_VIDEO_URL

        serialized = result.artifact.value.model_dump_json()
        assert "A man returns home" not in serialized
        assert "cinematic living room" not in serialized
        assert "slow push in" not in serialized

        after_rows = await reader.fetchall("SELECT logical_id FROM studio_semantic_version")
        new_ids = {str(item["logical_id"]) for item in after_rows} - before_ids
        assert new_ids == {value.projection_id.root}
        assert not any(item.startswith("scene:") for item in new_ids)
        assert not any(item.startswith("full-shot-spec:") for item in new_ids)
        assert not any(item.startswith("shot-ir:") for item in new_ids)

        outgoing = await service.graph.list_outgoing(ir.shot_ref)
        assert any(edge.dependent_ref == result.artifact.ref for edge in outgoing)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_projection_replay_is_idempotent_and_does_not_duplicate_semantic_version(tmp_path):
    writer, _job_repo, _job, _ir, row, mapping = await _mapped_fixture(tmp_path)
    try:
        service = OperationalSceneExecutionProjectionService(writer)
        request = _projection_request(mapping.artifact.ref, row)
        first = await service.project(request)
        replay = await service.project(request)
        assert replay == first

        reader = SQLiteReadRepository(writer.db_path)
        count = await reader.fetchone(
            "SELECT COUNT(*) AS count FROM studio_semantic_version WHERE logical_id=?",
            (first.artifact.ref.logical_id.root,),
        )
        assert count is not None and count["count"] == 1
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_prompt_only_operational_scene_mapping_cannot_be_projected(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        row = _scene_row()
        importer = LegacyImportAntiCorruptionService(writer)
        mapping = await importer.assess(_import_request(row, version="mapping-v1"))
        assert mapping.artifact.value.disposition is LegacyImportDisposition.NOT_PROVABLE

        service = OperationalSceneExecutionProjectionService(writer)
        with pytest.raises(OperationalSceneProjectionGateBlocked, match="exact-current APPROVED"):
            await service.project(_projection_request(mapping.artifact.ref, row))
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_raw_scene_drift_after_import_mapping_is_rejected(tmp_path):
    writer, _job_repo, _job, _ir, row, mapping = await _mapped_fixture(tmp_path)
    try:
        changed = dict(row)
        changed["prompt"] = "Changed prompt must not silently reuse old import proof."
        service = OperationalSceneExecutionProjectionService(writer)
        with pytest.raises(OperationalSceneProjectionGateBlocked, match="no longer matches"):
            await service.project(_projection_request(mapping.artifact.ref, changed))
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_generation_job_revision_blocks_projection(tmp_path):
    writer, job_repo, job, _ir, row, mapping = await _mapped_fixture(tmp_path)
    try:
        transitioned = await _transition(
            job_repo,
            job,
            axis=GenerationJobAxis.SCHEDULER,
            command="CLAIM",
            owner=TransitionOwner.SCHEDULER,
        )
        assert transitioned.job.revision > job.revision

        service = OperationalSceneExecutionProjectionService(writer)
        with pytest.raises(OperationalSceneProjectionGateBlocked, match="revision is stale"):
            await service.project(_projection_request(mapping.artifact.ref, row))
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_projection_provenance_hashes_signed_url_instead_of_logging_it(tmp_path):
    writer, _job_repo, _job, _ir, row, mapping = await _mapped_fixture(tmp_path)
    try:
        service = OperationalSceneExecutionProjectionService(writer)
        result = await service.project(_projection_request(mapping.artifact.ref, row))
        refs = result.artifact.metadata.provenance.source_refs

        assert all(SIGNED_VIDEO_URL not in item for item in refs)
        digest = hashlib.sha256(SIGNED_VIDEO_URL.encode("utf-8")).hexdigest()
        assert any(item.endswith(f"url-sha256:{digest}") for item in refs)
        assert any(item.endswith("id:legacy-media-video-001") for item in refs)
    finally:
        await writer.close()


def test_projection_model_rejects_cinematic_scene_as_compatibility_shot_authority():
    with pytest.raises(ValidationError, match="ShotListItem"):
        OperationalSceneExecutionProjection(
            projection_id=operational_scene_projection_logical_id(
                MIGRATION_RUN, "legacy-scene-001"
            ),
            version_id=VersionId("projection-v1"),
            migration_run_id=MIGRATION_RUN,
            canonical_project_id=PROJECT_ID,
            scene_mapping_ref=VersionRef(
                logical_id=LogicalId("legacy-import-mapping:proof"),
                version_id=VersionId("mapping-v1"),
            ),
            source_payload_sha256="sha256:" + "0" * 64,
            legacy_scene_id="legacy-scene-001",
            legacy_video_id="legacy-video-001",
            display_order=0,
            shot_refs=(
                VersionRef(
                    logical_id=LogicalId("scene:project:film:cinematic-authority"),
                    version_id=VersionId("scene-v1"),
                ),
            ),
        )
