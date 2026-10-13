"""IMP-102 true-restart fault-injection acceptance tests.

These tests deliberately close and reopen the SQLite write owner at durable
crash boundaries. Existing IMP-052..055 tests remain the source for their
already-verified unit-level contracts; this module proves cross-boundary replay.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from agent.studio import (
    ArtifactEventKind,
    ArtifactLifecycleService,
    ArtifactState,
    LeaseState,
    ProviderState,
    ReconcileClassification,
    RecoveryCoordinator,
    RecoveryDecision,
    RecoveryProbeOutcome,
    RecoveryProofKind,
    RecoveryTrigger,
    SchedulerRepository,
    SchedulerState,
)
from agent.studio.generation_job import GenerationJobRepository
from agent.studio.persistence import SQLiteWriteOwner
from tests.unit.test_studio_artifact_lifecycle import (
    EVIDENCE as ARTIFACT_EVIDENCE,
    _begin as _begin_artifact,
    _fixture as _artifact_fixture,
)
from tests.unit.test_studio_directing import NOW
from tests.unit.test_studio_recovery import _probe, _submitting_job
from tests.unit.test_studio_scheduler import (
    EVIDENCE as SCHEDULER_EVIDENCE,
    _jobs,
    _policy,
    _ready,
    _register,
)


class _ProbeMustNotRun:
    """Fail the test if durable recovery replay reaches the provider again."""

    def __init__(self) -> None:
        self.calls = 0

    async def reconcile(self, job, *, observed_at):
        self.calls += 1
        raise AssertionError("durable recovery replay must not call the provider probe")


@pytest.mark.asyncio
async def test_imp102_restart_replays_ambiguous_event_without_reprobe_or_duplicate_submit(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "studio.db"
    writer = SQLiteWriteOwner(db_path)
    await writer.start()
    repo = None
    job = None
    persisted_event = None
    probe = _probe(RecoveryProbeOutcome.STILL_AMBIGUOUS)
    attempt_id = "imp102-ambiguous-replay-001"

    try:
        repo, job, _ = await _submitting_job(writer)
        coordinator = RecoveryCoordinator(writer)

        async def crash_after_durable_event(event):
            raise RuntimeError("injected crash after durable recovery event")

        monkeypatch.setattr(coordinator, "_finalize_event", crash_after_durable_event)
        with pytest.raises(RuntimeError, match="after durable recovery event"):
            await coordinator.recover(
                job_id=job.generation_job_id,
                recovery_attempt_id=attempt_id,
                trigger=RecoveryTrigger.SUBMIT_RESPONSE_LOST,
                probe=probe,
                expected_revision=job.revision,
                actor_ref="recovery:imp102-test",
                reason="provider response lost after possible submit",
                correlation_id="run:imp102-ambiguous-replay",
                recorded_at=NOW,
                evidence_refs=("evidence:imp102:ambiguous-submit",),
            )

        events = await coordinator.events.list_for_job(job.generation_job_id)
        assert len(events) == 1
        persisted_event = events[0]
        assert persisted_event.decision is RecoveryDecision.HOLD_AMBIGUOUS
        interrupted = await coordinator.jobs.get_job(job.generation_job_id)
        assert interrupted is not None
        assert interrupted.scheduler_state is SchedulerState.WAITING_RECOVERY
        assert interrupted.provider_state is ProviderState.RECONCILING
        assert probe.calls == 1
    finally:
        await writer.close()

    assert job is not None and persisted_event is not None
    writer2 = SQLiteWriteOwner(db_path)
    await writer2.start()
    try:
        coordinator2 = RecoveryCoordinator(writer2)
        current = await coordinator2.jobs.get_job(job.generation_job_id)
        assert current is not None
        must_not_probe = _ProbeMustNotRun()
        replay = await coordinator2.recover(
            job_id=job.generation_job_id,
            recovery_attempt_id=attempt_id,
            trigger=RecoveryTrigger.SUBMIT_RESPONSE_LOST,
            probe=must_not_probe,
            expected_revision=current.revision,
            actor_ref="recovery:imp102-restart",
            reason="replay persisted ambiguous decision after restart",
            correlation_id="run:imp102-ambiguous-replay-after-restart",
            recorded_at=NOW + timedelta(seconds=1),
            evidence_refs=("evidence:imp102:restart-replay",),
        )

        assert must_not_probe.calls == 0
        assert replay.event == persisted_event
        assert replay.job.scheduler_state is SchedulerState.WAITING_RECOVERY
        assert replay.job.provider_state is ProviderState.AMBIGUOUS_HOLD
        history = await coordinator2.jobs.list_transitions(job.generation_job_id)
        commands = [item.command for item in history]
        assert commands.count("SUBMIT") == 1
        assert commands.count("STILL_AMBIGUOUS") == 1
        assert len(await coordinator2.events.list_for_job(job.generation_job_id)) == 1
    finally:
        await writer2.close()


@pytest.mark.asyncio
async def test_imp102_restart_finishes_safe_requeue_after_provider_proof_was_committed(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "studio.db"
    writer = SQLiteWriteOwner(db_path)
    await writer.start()
    job = None
    persisted_event = None
    probe = _probe(RecoveryProbeOutcome.PROVEN_ABSENT)
    attempt_id = "imp102-safe-requeue-replay-001"

    try:
        _, job, _ = await _submitting_job(writer)
        coordinator = RecoveryCoordinator(writer)
        original_transition = coordinator.jobs.transition

        async def crash_before_scheduler_requeue(**kwargs):
            if kwargs.get("command") == "RECOVERY_PROVEN_SAFE_TO_REQUEUE":
                raise RuntimeError("injected crash between recovery axis commits")
            return await original_transition(**kwargs)

        monkeypatch.setattr(coordinator.jobs, "transition", crash_before_scheduler_requeue)
        with pytest.raises(RuntimeError, match="between recovery axis commits"):
            await coordinator.recover(
                job_id=job.generation_job_id,
                recovery_attempt_id=attempt_id,
                trigger=RecoveryTrigger.PROCESS_CRASH,
                probe=probe,
                expected_revision=job.revision,
                actor_ref="recovery:imp102-test",
                reason="provider lookup proves remote operation absent",
                correlation_id="run:imp102-safe-requeue",
                recorded_at=NOW,
                evidence_refs=("evidence:imp102:proven-absent",),
            )

        current = await coordinator.jobs.get_job(job.generation_job_id)
        assert current is not None
        assert current.provider_state is ProviderState.NOT_SUBMITTED
        assert current.scheduler_state is SchedulerState.WAITING_RECOVERY
        events = await coordinator.events.list_for_job(job.generation_job_id)
        assert len(events) == 1
        persisted_event = events[0]
        assert persisted_event.decision is RecoveryDecision.SAFE_TO_REQUEUE
        assert probe.calls == 1
    finally:
        await writer.close()

    assert job is not None and persisted_event is not None
    writer2 = SQLiteWriteOwner(db_path)
    await writer2.start()
    try:
        coordinator2 = RecoveryCoordinator(writer2)
        current = await coordinator2.jobs.get_job(job.generation_job_id)
        assert current is not None
        must_not_probe = _ProbeMustNotRun()
        replay = await coordinator2.recover(
            job_id=job.generation_job_id,
            recovery_attempt_id=attempt_id,
            trigger=RecoveryTrigger.PROCESS_CRASH,
            probe=must_not_probe,
            expected_revision=current.revision,
            actor_ref="recovery:imp102-restart",
            reason="complete persisted safe-requeue decision after restart",
            correlation_id="run:imp102-safe-requeue-after-restart",
            recorded_at=NOW + timedelta(seconds=1),
            evidence_refs=("evidence:imp102:restart-replay",),
        )

        assert must_not_probe.calls == 0
        assert replay.event == persisted_event
        assert replay.job.provider_state is ProviderState.NOT_SUBMITTED
        assert replay.job.scheduler_state is SchedulerState.QUEUED
        history = await coordinator2.jobs.list_transitions(job.generation_job_id)
        commands = [item.command for item in history]
        assert commands.count("SUBMIT") == 1
        assert commands.count("PROVEN_ABSENT") == 1
        assert commands.count("RECOVERY_PROVEN_SAFE_TO_REQUEUE") == 1
        assert len(await coordinator2.events.list_for_job(job.generation_job_id)) == 1
    finally:
        await writer2.close()


@pytest.mark.asyncio
async def test_imp102_scheduler_restart_requires_no_dispatch_proof_before_requeue(tmp_path):
    db_path = tmp_path / "studio.db"
    writer = SQLiteWriteOwner(db_path)
    await writer.start()
    job = None
    try:
        _, jobs = await _jobs(writer)
        job = jobs[0]
        scheduler = SchedulerRepository(writer)
        await _register(scheduler, job)
        await _ready(scheduler, job)
        claim = await scheduler.claim_next(
            policy=_policy(job),
            worker_id="worker-imp102",
            lease_ttl_seconds=1,
            actor_ref="scheduler:imp102-test",
            reason="short lease for true restart fault injection",
            correlation_id="run:imp102-lease-claim",
            recorded_at=NOW,
            evidence_refs=SCHEDULER_EVIDENCE,
        )
        assert claim is not None
    finally:
        await writer.close()

    assert job is not None
    writer2 = SQLiteWriteOwner(db_path)
    await writer2.start()
    try:
        scheduler2 = SchedulerRepository(writer2)
        restart_time = NOW + timedelta(seconds=2)
        report = await scheduler2.recover_startup(
            recorded_at=restart_time,
            actor_ref="scheduler:imp102-restart",
            reason="expire lease after actual SQLite owner restart",
            correlation_id="run:imp102-lease-restart",
            evidence_refs=("evidence:imp102:lease-restart",),
        )
        assert job.generation_job_id in report.recovery_required_jobs
        stored = await scheduler2.jobs.get_job(job.generation_job_id)
        assert stored is not None
        assert stored.scheduler_state is SchedulerState.CLAIMED
        lease = await scheduler2.get_lease(job.generation_job_id)
        assert lease is not None and lease.state is LeaseState.EXPIRED

        coordinator = RecoveryCoordinator(writer2)
        result = await coordinator.recover_pre_dispatch(
            job_id=job.generation_job_id,
            recovery_attempt_id="imp102-pre-dispatch-restart-001",
            expected_revision=stored.revision,
            actor_ref="recovery:imp102-restart",
            reason="durable evidence proves transport was never dispatched",
            correlation_id="run:imp102-pre-dispatch-proof",
            recorded_at=restart_time,
            evidence_refs=("evidence:imp102:transport-not-dispatched",),
        )
        assert result.event.proof_kind is RecoveryProofKind.TRANSPORT_NOT_DISPATCHED
        assert result.event.decision is RecoveryDecision.SAFE_TO_REQUEUE
        assert result.job.provider_state is ProviderState.NOT_SUBMITTED
        assert result.job.scheduler_state is SchedulerState.QUEUED
        history = await coordinator.jobs.list_transitions(job.generation_job_id)
        assert not any(item.command == "SUBMIT" for item in history)
    finally:
        await writer2.close()


@pytest.mark.asyncio
async def test_imp102_artifact_restart_reconciles_durable_final_events_after_crash(
    tmp_path, monkeypatch
):
    writer, repo, job, service = await _artifact_fixture(tmp_path)
    db_path = writer.db_path
    paths = None
    try:
        _, paths, _ = await _begin_artifact(service, job)
        await service.write_staging_bytes(
            job_id=job.generation_job_id,
            attempt=1,
            data=b"imp102-crash-recovery-artifact",
            actor_ref="studio:imp102-test",
            reason="write bytes before injected state-transition crash",
            correlation_id="run:imp102-artifact-crash",
            recorded_at=NOW,
            evidence_refs=ARTIFACT_EVIDENCE,
        )
        original_transition = service.jobs.transition

        async def crash_before_ready_transition(**kwargs):
            if kwargs.get("command") == "MATERIALIZE_VALID":
                raise RuntimeError("injected crash after durable artifact events")
            return await original_transition(**kwargs)

        monkeypatch.setattr(service.jobs, "transition", crash_before_ready_transition)
        with pytest.raises(RuntimeError, match="after durable artifact events"):
            await service.finalize_materialization(
                job_id=job.generation_job_id,
                attempt=1,
                current_input_fingerprint=job.expected_input_fingerprint,
                actor_ref="studio:imp102-test",
                reason="finalize before injected crash",
                correlation_id="run:imp102-artifact-crash",
                recorded_at=NOW,
                evidence_refs=ARTIFACT_EVIDENCE,
            )

        interrupted = await repo.get_job(job.generation_job_id)
        assert interrupted is not None and interrupted.artifact_state is ArtifactState.STAGING
        assert paths is not None
        final_path = service.absolute_path(paths.final_relative_path)
        assert final_path.is_file()
        assert final_path.read_bytes() == b"imp102-crash-recovery-artifact"
        before = await service.evidence.list_events_for_job(job.generation_job_id)
        assert [item.event_kind for item in before].count(ArtifactEventKind.FINAL_BYTES_WRITTEN) == 1
        assert [item.event_kind for item in before].count(ArtifactEventKind.MATERIALIZE_VALID) == 1
    finally:
        await writer.close()

    assert paths is not None
    writer2 = SQLiteWriteOwner(db_path)
    await writer2.start()
    try:
        service2 = ArtifactLifecycleService(writer2, tmp_path / "artifacts")
        restored = await GenerationJobRepository(writer2).get_job(job.generation_job_id)
        assert restored is not None and restored.artifact_state is ArtifactState.STAGING

        finding = await service2.reconcile_job(
            job_id=job.generation_job_id,
            current_input_fingerprint=restored.expected_input_fingerprint,
            actor_ref="studio:imp102-startup-reconciler",
            correlation_id="run:imp102-artifact-reconcile",
            recorded_at=NOW + timedelta(seconds=1),
            evidence_refs=("evidence:imp102:artifact-restart",),
        )
        assert finding.classification is ReconcileClassification.RECOVERED_READY
        assert finding.resulting_artifact_state is ArtifactState.READY
        final_path = service2.absolute_path(paths.final_relative_path)
        assert final_path.read_bytes() == b"imp102-crash-recovery-artifact"

        replay = await service2.reconcile_job(
            job_id=job.generation_job_id,
            current_input_fingerprint=restored.expected_input_fingerprint,
            actor_ref="studio:imp102-startup-reconciler",
            correlation_id="run:imp102-artifact-reconcile-replay",
            recorded_at=NOW + timedelta(seconds=2),
            evidence_refs=("evidence:imp102:artifact-restart",),
        )
        assert replay.classification is ReconcileClassification.NO_ACTION
        events = await service2.evidence.list_events_for_job(job.generation_job_id)
        assert [item.event_kind for item in events].count(ArtifactEventKind.FINAL_BYTES_WRITTEN) == 1
        assert [item.event_kind for item in events].count(ArtifactEventKind.MATERIALIZE_VALID) == 1
        ready = await service2.jobs.get_job(job.generation_job_id)
        assert ready is not None and ready.artifact_state is ArtifactState.READY
    finally:
        await writer2.close()
