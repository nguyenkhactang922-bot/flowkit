"""IMP-055 Artifact lifecycle/store/startup reconciler fault-injection tests."""

from __future__ import annotations

import os
from datetime import timedelta

import aiosqlite
import pytest

from agent.studio import (
    ArtifactEventKind,
    ArtifactLifecycleBlocked,
    ArtifactLifecycleService,
    ArtifactState,
    CreativeState,
    FOUNDATION_SCHEMA_VERSION,
    ReconcileClassification,
    artifact_storage_key,
)
from agent.studio.persistence import SQLiteReadRepository, SQLiteWriteOwner
from tests.unit.test_studio_directing import NOW
from tests.unit.test_studio_generation_job import _guard, _job_fixture


EVIDENCE = ("evidence:imp055",)


def _different_fingerprint(value: str) -> str:
    replacement = "0" if value[-1] != "0" else "1"
    return value[:-1] + replacement


async def _fixture(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    repo, job, *_ = await _job_fixture(writer)
    service = ArtifactLifecycleService(writer, tmp_path / "artifacts")
    return writer, repo, job, service


async def _begin(service: ArtifactLifecycleService, job, *, attempt: int = 1):
    return await service.begin_materialization(
        job_id=job.generation_job_id,
        attempt=attempt,
        extension="png",
        media_type="image/png",
        guard_evidence=_guard(local_result_eligible=True),
        actor_ref="studio:imp055-test",
        reason="begin canonical artifact materialization",
        correlation_id="run:imp055",
        recorded_at=NOW,
        evidence_refs=EVIDENCE,
    )


async def _ready(service: ArtifactLifecycleService, job, data: bytes = b"artifact-bytes-v1"):
    identity, paths, staging_job = await _begin(service, job)
    await service.write_staging_bytes(
        job_id=job.generation_job_id,
        attempt=1,
        data=data,
        actor_ref="studio:imp055-test",
        reason="write staged artifact bytes",
        correlation_id="run:imp055",
        recorded_at=NOW,
        evidence_refs=EVIDENCE,
    )
    ready = await service.finalize_materialization(
        job_id=job.generation_job_id,
        attempt=1,
        current_input_fingerprint=job.expected_input_fingerprint,
        actor_ref="studio:imp055-test",
        reason="finalize validated artifact bytes",
        correlation_id="run:imp055",
        recorded_at=NOW,
        evidence_refs=EVIDENCE,
    )
    return identity, paths, staging_job, ready


@pytest.mark.asyncio
async def test_migration_v9_adds_immutable_identity_and_append_only_evidence_without_shadow_status(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        assert FOUNDATION_SCHEMA_VERSION == 9
        reader = SQLiteReadRepository(writer.db_path)
        migration = await reader.fetchone("SELECT name FROM studio_schema_migration WHERE version=9")
        assert migration is not None
        assert migration["name"] == "studio_generation_artifact_evidence"
        identity_columns = {
            row["name"] for row in await reader.fetchall("PRAGMA table_info(studio_generation_artifact_identity)")
        }
        event_columns = {
            row["name"] for row in await reader.fetchall("PRAGMA table_info(studio_generation_artifact_event)")
        }
        assert {"artifact_id", "generation_job_id", "storage_key"} <= identity_columns
        assert {"artifact_event_id", "event_kind", "content_sha256", "byte_count"} <= event_columns
        assert not ({"status", "state", "creative_state", "artifact_state"} & identity_columns)
        assert not ({"status", "state", "creative_state", "artifact_state"} & event_columns)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_happy_materialization_reaches_ready_without_touching_creative_axis(tmp_path):
    writer, _, job, service = await _fixture(tmp_path)
    try:
        identity, paths, _, ready = await _ready(service, job)
        assert ready.artifact_state is ArtifactState.READY
        assert ready.creative_state is job.creative_state is CreativeState.NOT_APPLICABLE
        assert service.absolute_path(paths.final_relative_path).read_bytes() == b"artifact-bytes-v1"
        events = await service.evidence.list_events_for_job(job.generation_job_id)
        assert {event.event_kind for event in events} == {
            ArtifactEventKind.BEGIN_MATERIALIZE,
            ArtifactEventKind.STAGING_BYTES_WRITTEN,
            ArtifactEventKind.FINAL_BYTES_WRITTEN,
            ArtifactEventKind.MATERIALIZE_VALID,
        }
        assert len(events) == 4
        assert identity.generation_job_id == job.generation_job_id
        assert all("APPROV" not in event.event_kind.value for event in events)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_begin_and_staging_write_replay_ignore_audit_envelope_but_keep_first_evidence(tmp_path):
    writer, _, job, service = await _fixture(tmp_path)
    try:
        identity, paths, staging = await _begin(service, job)
        second_identity, second_paths, second_staging = await service.begin_materialization(
            job_id=job.generation_job_id,
            attempt=1,
            extension="png",
            media_type="image/png",
            guard_evidence=_guard(local_result_eligible=True),
            actor_ref="studio:retry",
            reason="safe retry with a new audit envelope",
            correlation_id="run:imp055-retry",
            recorded_at=NOW + timedelta(seconds=5),
            evidence_refs=("evidence:retry",),
        )
        assert second_identity == identity
        assert second_paths == paths
        assert second_staging.revision == staging.revision
        first = await service.write_staging_bytes(
            job_id=job.generation_job_id,
            attempt=1,
            data=b"same-bytes",
            actor_ref="studio:first",
            reason="first write",
            correlation_id="run:first",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        replay = await service.write_staging_bytes(
            job_id=job.generation_job_id,
            attempt=1,
            data=b"same-bytes",
            actor_ref="studio:retry",
            reason="retry write",
            correlation_id="run:retry",
            recorded_at=NOW + timedelta(seconds=10),
            evidence_refs=("evidence:retry",),
        )
        assert replay == first
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_finalize_refuses_unrecorded_staging_bytes_then_explicit_resume_recovers(tmp_path):
    writer, repo, job, service = await _fixture(tmp_path)
    try:
        _, paths, _ = await _begin(service, job)
        staging = service.absolute_path(paths.staging_relative_path)
        staging.parent.mkdir(parents=True, exist_ok=True)
        staging.write_bytes(b"bytes-written-before-crash")
        with pytest.raises(ArtifactLifecycleBlocked, match="STAGING_BYTES_WRITTEN"):
            await service.finalize_materialization(
                job_id=job.generation_job_id,
                attempt=1,
                current_input_fingerprint=job.expected_input_fingerprint,
                actor_ref="studio:imp055-test",
                reason="must not trust undurable staged bytes",
                correlation_id="run:imp055",
                recorded_at=NOW,
                evidence_refs=EVIDENCE,
            )
        current = await repo.get_job(job.generation_job_id)
        assert current is not None and current.artifact_state is ArtifactState.STAGING
        finding = await service.reconcile_job(
            job_id=job.generation_job_id,
            current_input_fingerprint=job.expected_input_fingerprint,
            actor_ref="studio:reconciler",
            correlation_id="run:reconcile",
            recorded_at=NOW + timedelta(seconds=1),
        )
        assert finding.classification is ReconcileClassification.STAGING_PRESENT
        await service.write_staging_bytes(
            job_id=job.generation_job_id,
            attempt=1,
            data=b"bytes-written-before-crash",
            actor_ref="studio:resume",
            reason="resume staging evidence after crash",
            correlation_id="run:resume",
            recorded_at=NOW + timedelta(seconds=2),
            evidence_refs=EVIDENCE,
        )
        ready = await service.finalize_materialization(
            job_id=job.generation_job_id,
            attempt=1,
            current_input_fingerprint=job.expected_input_fingerprint,
            actor_ref="studio:resume",
            reason="resume finalization",
            correlation_id="run:resume",
            recorded_at=NOW + timedelta(seconds=3),
            evidence_refs=EVIDENCE,
        )
        assert ready.artifact_state is ArtifactState.READY
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_startup_repairs_crash_after_atomic_rename_before_final_event(tmp_path):
    writer, _, job, service = await _fixture(tmp_path)
    try:
        _, paths, _ = await _begin(service, job)
        await service.write_staging_bytes(
            job_id=job.generation_job_id,
            attempt=1,
            data=b"rename-crash-bytes",
            actor_ref="studio:imp055-test",
            reason="write before injected rename crash",
            correlation_id="run:imp055",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        staging = service.absolute_path(paths.staging_relative_path)
        final = service.absolute_path(paths.final_relative_path)
        final.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staging, final)
        finding = await service.reconcile_job(
            job_id=job.generation_job_id,
            current_input_fingerprint=job.expected_input_fingerprint,
            actor_ref="studio:reconciler",
            correlation_id="run:reconcile",
            recorded_at=NOW + timedelta(seconds=1),
        )
        assert finding.classification is ReconcileClassification.RECOVERED_READY
        assert finding.resulting_artifact_state is ArtifactState.READY
        assert final.read_bytes() == b"rename-crash-bytes"
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_startup_replays_durable_final_events_after_crash_before_job_state_transition(tmp_path, monkeypatch):
    writer, repo, job, service = await _fixture(tmp_path)
    try:
        _, paths, _ = await _begin(service, job)
        await service.write_staging_bytes(
            job_id=job.generation_job_id,
            attempt=1,
            data=b"final-event-crash-bytes",
            actor_ref="studio:first-attempt",
            reason="write bytes before injected transition crash",
            correlation_id="run:first-attempt",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        original_transition = service.jobs.transition

        async def crash_after_evidence(**kwargs):
            if kwargs.get("command") == "MATERIALIZE_VALID":
                raise RuntimeError("injected crash after durable final events")
            return await original_transition(**kwargs)

        monkeypatch.setattr(service.jobs, "transition", crash_after_evidence)
        with pytest.raises(RuntimeError, match="injected crash"):
            await service.finalize_materialization(
                job_id=job.generation_job_id,
                attempt=1,
                current_input_fingerprint=job.expected_input_fingerprint,
                actor_ref="studio:first-attempt",
                reason="finalize before injected transition crash",
                correlation_id="run:first-attempt",
                recorded_at=NOW,
                evidence_refs=EVIDENCE,
            )

        current = await repo.get_job(job.generation_job_id)
        assert current is not None and current.artifact_state is ArtifactState.STAGING
        assert service.absolute_path(paths.final_relative_path).is_file()
        before = await service.evidence.list_events_for_job(job.generation_job_id)
        assert [item.event_kind for item in before].count(ArtifactEventKind.FINAL_BYTES_WRITTEN) == 1
        assert [item.event_kind for item in before].count(ArtifactEventKind.MATERIALIZE_VALID) == 1

        monkeypatch.setattr(service.jobs, "transition", original_transition)
        finding = await service.reconcile_job(
            job_id=job.generation_job_id,
            current_input_fingerprint=job.expected_input_fingerprint,
            actor_ref="studio:startup-reconciler",
            correlation_id="run:startup-reconcile",
            recorded_at=NOW + timedelta(seconds=1),
        )
        assert finding.classification is ReconcileClassification.RECOVERED_READY
        assert finding.resulting_artifact_state is ArtifactState.READY
        after = await service.evidence.list_events_for_job(job.generation_job_id)
        assert [item.event_kind for item in after].count(ArtifactEventKind.FINAL_BYTES_WRITTEN) == 1
        assert [item.event_kind for item in after].count(ArtifactEventKind.MATERIALIZE_VALID) == 1
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_late_result_never_becomes_ready_or_creative_approved(tmp_path):
    writer, _, job, service = await _fixture(tmp_path)
    try:
        await _begin(service, job)
        await service.write_staging_bytes(
            job_id=job.generation_job_id,
            attempt=1,
            data=b"stale-result",
            actor_ref="studio:imp055-test",
            reason="write stale late result",
            correlation_id="run:imp055",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        stale = await service.finalize_materialization(
            job_id=job.generation_job_id,
            attempt=1,
            current_input_fingerprint=_different_fingerprint(job.expected_input_fingerprint),
            actor_ref="studio:imp055-test",
            reason="detect stale late result",
            correlation_id="run:imp055",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        assert stale.artifact_state is ArtifactState.STALE_RESULT
        assert stale.creative_state is job.creative_state is CreativeState.NOT_APPLICABLE
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_ready_missing_and_corrupt_bytes_transition_on_startup_reconcile(tmp_path):
    writer, _, job, service = await _fixture(tmp_path)
    try:
        _, paths, _, ready = await _ready(service, job)
        final = service.absolute_path(paths.final_relative_path)
        final.unlink()
        missing = await service.reconcile_job(
            job_id=job.generation_job_id,
            current_input_fingerprint=job.expected_input_fingerprint,
            actor_ref="studio:reconciler",
            correlation_id="run:missing",
            recorded_at=NOW + timedelta(seconds=1),
        )
        assert missing.classification is ReconcileClassification.MISSING
        assert missing.resulting_artifact_state is ArtifactState.MISSING
        assert ready.creative_state is CreativeState.NOT_APPLICABLE
    finally:
        await writer.close()

    writer2, _, job2, service2 = await _fixture(tmp_path / "corrupt-case")
    try:
        _, paths2, _, _ = await _ready(service2, job2)
        service2.absolute_path(paths2.final_relative_path).write_bytes(b"tampered-bytes")
        corrupt = await service2.reconcile_job(
            job_id=job2.generation_job_id,
            current_input_fingerprint=job2.expected_input_fingerprint,
            actor_ref="studio:reconciler",
            correlation_id="run:corrupt",
            recorded_at=NOW + timedelta(seconds=1),
        )
        assert corrupt.classification is ReconcileClassification.CORRUPT
        assert corrupt.resulting_artifact_state is ArtifactState.CORRUPT
    finally:
        await writer2.close()


@pytest.mark.asyncio
async def test_missing_bytes_can_recover_on_new_attempt_and_return_ready(tmp_path):
    writer, _, job, service = await _fixture(tmp_path)
    try:
        _, paths, _, _ = await _ready(service, job)
        service.absolute_path(paths.final_relative_path).unlink()
        finding = await service.reconcile_job(
            job_id=job.generation_job_id,
            current_input_fingerprint=job.expected_input_fingerprint,
            actor_ref="studio:reconciler",
            correlation_id="run:missing",
            recorded_at=NOW + timedelta(seconds=1),
        )
        assert finding.resulting_artifact_state is ArtifactState.MISSING
        _, recover_paths, staging = await service.recover_bytes(
            job_id=job.generation_job_id,
            attempt=2,
            extension="png",
            media_type="image/png",
            actor_ref="studio:reconciler",
            reason="authorized byte recovery",
            correlation_id="run:recover",
            recorded_at=NOW + timedelta(seconds=2),
            evidence_refs=EVIDENCE,
        )
        assert staging.artifact_state is ArtifactState.STAGING
        await service.write_staging_bytes(
            job_id=job.generation_job_id,
            attempt=2,
            data=b"recovered-bytes",
            actor_ref="studio:reconciler",
            reason="write recovered bytes",
            correlation_id="run:recover",
            recorded_at=NOW + timedelta(seconds=3),
            evidence_refs=EVIDENCE,
        )
        ready = await service.finalize_materialization(
            job_id=job.generation_job_id,
            attempt=2,
            current_input_fingerprint=job.expected_input_fingerprint,
            actor_ref="studio:reconciler",
            reason="validate recovered bytes",
            correlation_id="run:recover",
            recorded_at=NOW + timedelta(seconds=4),
            evidence_refs=EVIDENCE,
        )
        assert ready.artifact_state is ArtifactState.READY
        assert service.absolute_path(recover_paths.final_relative_path).read_bytes() == b"recovered-bytes"
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_orphan_final_is_quarantined_and_interrupted_transition_is_idempotently_completed(tmp_path, monkeypatch):
    writer, _, job, service = await _fixture(tmp_path)
    try:
        key = artifact_storage_key(job.generation_job_id)
        final = service.artifact_root / "objects" / key / "attempt-0001.png"
        final.parent.mkdir(parents=True, exist_ok=True)
        final.write_bytes(b"orphan-final")

        original_transition = service.jobs.transition
        calls = {"count": 0}

        async def fail_once(**kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("injected crash after durable orphan evidence")
            return await original_transition(**kwargs)

        monkeypatch.setattr(service.jobs, "transition", fail_once)
        with pytest.raises(RuntimeError, match="injected crash"):
            await service.reconcile_job(
                job_id=job.generation_job_id,
                current_input_fingerprint=job.expected_input_fingerprint,
                actor_ref="studio:reconciler",
                correlation_id="run:orphan-first",
                recorded_at=NOW,
            )
        recovered = await service.reconcile_job(
            job_id=job.generation_job_id,
            current_input_fingerprint=job.expected_input_fingerprint,
            actor_ref="studio:reconciler-retry",
            correlation_id="run:orphan-retry",
            recorded_at=NOW + timedelta(seconds=1),
        )
        assert recovered.classification is ReconcileClassification.QUARANTINED_ORPHAN
        assert recovered.resulting_artifact_state is ArtifactState.QUARANTINED
        loaded = await service.jobs.get_job(job.generation_job_id)
        assert loaded is not None
        assert loaded.creative_state is job.creative_state is CreativeState.NOT_APPLICABLE
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_archive_is_artifact_axis_only_and_evidence_tables_are_append_only(tmp_path):
    writer, _, job, service = await _fixture(tmp_path)
    try:
        identity, _, _, ready = await _ready(service, job)
        archived = await service.archive(
            job_id=job.generation_job_id,
            attempt=1,
            actor_ref="studio:imp055-test",
            reason="retention archive",
            correlation_id="run:archive",
            recorded_at=NOW + timedelta(seconds=1),
            evidence_refs=EVIDENCE,
        )
        assert archived.artifact_state is ArtifactState.ARCHIVED
        assert archived.creative_state is ready.creative_state is CreativeState.NOT_APPLICABLE

        async def mutate(tx):
            await tx.execute(
                "UPDATE studio_generation_artifact_identity SET reason=? WHERE artifact_id=?",
                ("illegal mutation", identity.artifact_id.root),
            )

        with pytest.raises(aiosqlite.IntegrityError, match="immutable"):
            await writer.execute(mutate)
    finally:
        await writer.close()
