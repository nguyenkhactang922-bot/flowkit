"""IMP-080 Legacy Import Anti-Corruption authority and migration-boundary tests."""

from __future__ import annotations

import pytest

from agent.studio import (
    FindingSeverity,
    LegacyImportAntiCorruptionService,
    LegacyImportDisposition,
    LegacyImportFindingCode,
    LegacyImportRequest,
    LegacySourceEvidence,
    LegacySourceKind,
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SQLiteReadRepository,
    SQLiteWriteOwner,
    VersionId,
    VersionRef,
)
from tests.unit.test_studio_directing import NOW, PROJECT_ID
from tests.unit.test_studio_generation_job import _job_fixture


MIGRATION_RUN = "imp080-run-001"
TARGET_SCHEMA = "studio-schema-v9"


def _scene_source(**updates) -> LegacySourceEvidence:
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
        "vertical_image_media_id": "legacy-media-image-001",
        "vertical_video_media_id": "legacy-media-video-001",
    }
    row.update(updates)
    return LegacySourceEvidence.from_legacy(
        row,
        source_kind=LegacySourceKind.OPERATIONAL_SCENE,
        source_table="scene",
        source_id=str(row["id"]),
        source_schema_version="flowkit-v1",
    )


def _project_source(story: str | None = "A son returns to sell his late mother's house."):
    return LegacySourceEvidence.from_legacy(
        {
            "id": "legacy-project-001",
            "name": "Old project",
            "story": story,
            "language": "vi",
        },
        source_kind=LegacySourceKind.PROJECT,
        source_table="project",
        source_id="legacy-project-001",
        source_schema_version="flowkit-v1",
    )


def _request(
    source: LegacySourceEvidence,
    *,
    version: str,
    explicit_target_refs: tuple[VersionRef, ...] = (),
    generation_job_id: LogicalId | None = None,
    generation_job_revision: int | None = None,
    canonical_project_id: LogicalId | None = PROJECT_ID,
) -> LegacyImportRequest:
    return LegacyImportRequest(
        migration_run_id=MIGRATION_RUN,
        target_schema_version=TARGET_SCHEMA,
        record_version_id=VersionId(version),
        source=source,
        canonical_project_id=canonical_project_id,
        explicit_target_refs=explicit_target_refs,
        generation_job_id=generation_job_id,
        generation_job_revision=generation_job_revision,
        actor_ref="studio:imp080-test",
        reason="classify bounded legacy import evidence",
        recorded_at=NOW,
        correlation_id="run:imp080",
        evidence_refs=("evidence:imp080",),
    )


@pytest.mark.asyncio
async def test_prompt_only_operational_scene_is_not_provable_and_cannot_mint_creative_truth(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        service = LegacyImportAntiCorruptionService(writer)
        result = await service.assess(_request(_scene_source(), version="mapping-v1"))

        value = result.artifact.value
        assert value.disposition is LegacyImportDisposition.NOT_PROVABLE
        assert value.target_refs == ()
        assert value.generation_job_id is None
        codes = {finding.code for finding in value.findings}
        assert LegacyImportFindingCode.OPERATIONAL_SCENE_NOT_CANONICAL_SCENE in codes
        assert LegacyImportFindingCode.PROMPT_PROSE_DERIVATIVE_ONLY in codes
        assert LegacyImportFindingCode.EXPLICIT_TARGET_PROOF_REQUIRED in codes
        assert any(
            finding.severity is FindingSeverity.MAJOR
            for finding in value.findings
            if finding.code is LegacyImportFindingCode.EXPLICIT_TARGET_PROOF_REQUIRED
        )

        reader = SQLiteReadRepository(writer.db_path)
        rows = await reader.fetchall("SELECT logical_id,payload_json FROM studio_semantic_version")
        logical_ids = {str(row["logical_id"]) for row in rows}
        assert all(not item.startswith("scene-dramatic-beat:") for item in logical_ids)
        assert all(not item.startswith("full-shot-spec:") for item in logical_ids)
        assert all(not item.startswith("shot-ir:") for item in logical_ids)
        assert len(rows) == 1
        persisted = str(rows[0]["payload_json"])
        assert "A man returns home" not in persisted
        assert "cinematic living room" not in persisted
        assert "slow push in" not in persisted
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_forbidden_scene_dramatic_beat_or_full_shot_spec_claim_is_not_provable(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        service = LegacyImportAntiCorruptionService(writer)
        forbidden = (
            VersionRef(
                logical_id=LogicalId("scene-dramatic-beat:project:film:scene-001:beat-001"),
                version_id=VersionId("beat-v1"),
            ),
            VersionRef(
                logical_id=LogicalId("full-shot-spec:project:film:fake-shot"),
                version_id=VersionId("spec-v1"),
            ),
        )
        result = await service.assess(
            _request(
                _scene_source(),
                version="mapping-v1",
                explicit_target_refs=forbidden,
            )
        )
        assert result.artifact.value.disposition is LegacyImportDisposition.NOT_PROVABLE
        assert result.artifact.value.target_refs == ()
        assert LegacyImportFindingCode.FORBIDDEN_CANONICAL_TARGET in {
            finding.code for finding in result.artifact.value.findings
        }
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_dangling_shot_claim_becomes_not_provable_finding(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        service = LegacyImportAntiCorruptionService(writer)
        missing_shot = VersionRef(
            logical_id=LogicalId("shot-list-item:project:film:missing-proof"),
            version_id=VersionId("shot-v1"),
        )
        result = await service.assess(
            _request(
                _scene_source(),
                version="mapping-v1",
                explicit_target_refs=(missing_shot,),
            )
        )
        assert result.artifact.value.disposition is LegacyImportDisposition.NOT_PROVABLE
        assert LegacyImportFindingCode.TARGET_VERSION_MISSING in {
            finding.code for finding in result.artifact.value.findings
        }
        assert result.artifact.metadata.provenance.source_versions == ()
        assert any(
            ref.startswith("claimed-target:shot-list-item:")
            for ref in result.artifact.metadata.provenance.source_refs
        )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_explicit_exact_shot_and_generation_job_proof_maps_compatibility_only(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        job_repo, job, ir, *_ = await _job_fixture(writer)
        assert await job_repo.get_job(job.generation_job_id) == job

        service = LegacyImportAntiCorruptionService(writer)
        result = await service.assess(
            _request(
                _scene_source(),
                version="mapping-v1",
                explicit_target_refs=(ir.shot_ref,),
                generation_job_id=job.generation_job_id,
                generation_job_revision=job.revision,
            )
        )
        value = result.artifact.value
        assert value.disposition is LegacyImportDisposition.COMPATIBILITY_MAPPED
        assert value.target_refs == (ir.shot_ref,)
        assert value.generation_job_id == job.generation_job_id
        assert value.generation_job_revision == job.revision
        assert value.canonical_project_id == PROJECT_ID
        assert result.artifact.metadata.provenance.source_versions[0].source == ir.shot_ref
        assert any(
            ref == f"{job.generation_job_id.root}@revision:{job.revision}"
            for ref in result.artifact.metadata.provenance.source_refs
        )
        pointer = await service.versions.get_current(value.mapping_id)
        assert pointer is not None
        assert pointer.status is LifecycleState.APPROVED

        outgoing = await service.graph.list_outgoing(ir.shot_ref)
        assert any(edge.dependent_ref == result.artifact.ref for edge in outgoing)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_generation_job_revision_rejects_otherwise_valid_scene_mapping(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, job, ir, *_ = await _job_fixture(writer)
        service = LegacyImportAntiCorruptionService(writer)
        result = await service.assess(
            _request(
                _scene_source(),
                version="mapping-v1",
                explicit_target_refs=(ir.shot_ref,),
                generation_job_id=job.generation_job_id,
                generation_job_revision=job.revision + 1,
            )
        )
        value = result.artifact.value
        assert value.disposition is LegacyImportDisposition.NOT_PROVABLE
        assert value.target_refs == ()
        assert value.generation_job_id is None
        assert LegacyImportFindingCode.GENERATION_JOB_REVISION_MISMATCH in {
            finding.code for finding in value.findings
        }
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_project_story_is_seed_only_and_raw_story_never_becomes_storycore(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        service = LegacyImportAntiCorruptionService(writer)
        result = await service.assess(
            _request(
                _project_source(),
                version="mapping-v1",
                canonical_project_id=PROJECT_ID,
            )
        )
        value = result.artifact.value
        assert value.disposition is LegacyImportDisposition.SEED_ONLY
        assert value.target_refs == ()
        assert LegacyImportFindingCode.PROJECT_STORY_SEED_ONLY in {
            finding.code for finding in value.findings
        }

        reader = SQLiteReadRepository(writer.db_path)
        rows = await reader.fetchall("SELECT logical_id,payload_json FROM studio_semantic_version")
        assert len(rows) == 1
        assert not str(rows[0]["logical_id"]).startswith("story-core:")
        assert "A son returns to sell" not in str(rows[0]["payload_json"])
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_exact_replay_is_idempotent_and_keeps_single_mapping_version(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        service = LegacyImportAntiCorruptionService(writer)
        request = _request(_project_source(), version="mapping-v1")
        first = await service.assess(request)
        replay = await service.assess(request)
        assert replay == first

        reader = SQLiteReadRepository(writer.db_path)
        row = await reader.fetchone(
            "SELECT COUNT(*) AS count FROM studio_semantic_version WHERE logical_id=?",
            (first.artifact.ref.logical_id.root,),
        )
        assert row is not None and row["count"] == 1
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_fake_semantic_row_with_shot_prefix_is_not_valid_shotlistitem_proof(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        service = LegacyImportAntiCorruptionService(writer)
        fake_ref = VersionRef(
            logical_id=LogicalId("shot-list-item:project:film:fake-prefix-only"),
            version_id=VersionId("shot-v1"),
        )
        await service.versions.create_initial(
            metadata=SemanticRecordMetadata(
                logical_id=fake_ref.logical_id,
                version_id=fake_ref.version_id,
                provenance=Provenance(
                    source_refs=("evidence:fake-shot-prefix",),
                    actor_ref="studio:imp080-test",
                    reason="seed malicious prefix-only semantic row",
                    recorded_at=NOW,
                ),
                created_at=NOW,
            ),
            payload={"project_id": PROJECT_ID.root, "not_a_shot_list_item": True},
            status=LifecycleState.APPROVED,
        )

        result = await service.assess(
            _request(
                _scene_source(),
                version="mapping-v1",
                explicit_target_refs=(fake_ref,),
            )
        )
        assert result.artifact.value.disposition is LegacyImportDisposition.NOT_PROVABLE
        assert result.artifact.value.target_refs == ()
        assert LegacyImportFindingCode.TARGET_VERSION_MISSING in {
            finding.code for finding in result.artifact.value.findings
        }
    finally:
        await writer.close()


def test_opaque_runtime_object_is_rejected_instead_of_stringified_into_mapping_evidence():
    class _OpaqueRuntimeObject:
        pass

    with pytest.raises(ValueError, match="deterministically JSON serializable"):
        LegacySourceEvidence.from_legacy(
            {"id": "legacy-scene-opaque", "opaque": _OpaqueRuntimeObject()},
            source_kind=LegacySourceKind.OPERATIONAL_SCENE,
            source_table="scene",
            source_id="legacy-scene-opaque",
            source_schema_version="flowkit-v1",
        )
