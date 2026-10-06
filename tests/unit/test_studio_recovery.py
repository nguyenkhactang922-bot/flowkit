"""IMP-054 Retry/Resume/Remote Ambiguity recovery tests."""

from __future__ import annotations

import aiosqlite
import pytest

from agent.studio import (
    ErrorClass,
    FOUNDATION_SCHEMA_VERSION,
    GenerationJobAxis,
    GenerationJobCreateRequest,
    ProviderAdapterRecoveryProbe,
    ProviderHandleKind,
    ProviderRemoteLineage,
    ProviderState,
    ProviderObservationKind,
    ProviderObservationState,
    ProviderTransportHandle,
    ProviderTransportObservation,
    RecoveryCoordinator,
    RecoveryDecision,
    RecoveryEventRepository,
    RecoveryGateBlocked,
    RecoveryProbeOutcome,
    RecoveryProbeResult,
    RecoveryProofKind,
    RecoveryTrigger,
    RetryDisposition,
    SchedulerState,
    TransitionOwner,
)
from agent.studio.persistence import SQLiteReadRepository, SQLiteWriteOwner
from tests.unit.test_studio_directing import NOW
from tests.unit.test_studio_generation_job import _guard, _job_fixture, _transition


class FakeProbe:
    def __init__(self, result: RecoveryProbeResult) -> None:
        self.result = result
        self.calls = 0

    async def reconcile(self, job, *, observed_at):
        self.calls += 1
        assert observed_at == self.result.observed_at
        return self.result

class UrlOnlySuccessAdapter:
    async def reconcile(self, handle, *, observed_at):
        assert handle is not None
        return ProviderTransportObservation(
            provider_key="flow",
            kind=ProviderObservationKind.RECONCILE,
            state=ProviderObservationState.SUCCEEDED,
            observed_at=observed_at,
            handle=handle,
            output_url="https://example.invalid/render/result.mp4?secret=do-not-persist",
            retry_safe=False,
        )



def _probe(
    outcome: RecoveryProbeOutcome,
    *,
    handle_id: str | None = None,
    kind: ProviderHandleKind = ProviderHandleKind.OPERATION,
) -> FakeProbe:
    handle = None
    if handle_id is not None:
        handle = ProviderTransportHandle(
            provider_key="flow",
            kind=kind,
            handle_id=handle_id,
        )
    return FakeProbe(
        RecoveryProbeResult(
            outcome=outcome,
            strategy="fixture-reconcile",
            observed_at=NOW,
            evidence_refs=(f"evidence:imp054:{outcome.value.lower()}",),
            handle=handle,
        )
    )


async def _running_job(writer: SQLiteWriteOwner):
    repo, job, *rest = await _job_fixture(writer)
    job = (
        await _transition(
            repo,
            job,
            axis=GenerationJobAxis.SCHEDULER,
            command="CLAIM",
            owner=TransitionOwner.SCHEDULER,
        )
    ).job
    job = (
        await _transition(
            repo,
            job,
            axis=GenerationJobAxis.SCHEDULER,
            command="START_WORK",
            owner=TransitionOwner.SCHEDULER,
        )
    ).job
    return repo, job, rest


async def _submitting_job(writer: SQLiteWriteOwner):
    repo, job, rest = await _running_job(writer)
    job = (
        await _transition(
            repo,
            job,
            axis=GenerationJobAxis.PROVIDER,
            command="SUBMIT",
            owner=TransitionOwner.PROVIDER_ADAPTER,
            guard=_guard(side_effect_boundary_ready=True),
        )
    ).job
    return repo, job, rest


async def _polling_job(writer: SQLiteWriteOwner, *, operation_id: str = "op-001"):
    repo, job, rest = await _submitting_job(writer)
    job = (
        await _transition(
            repo,
            job,
            axis=GenerationJobAxis.PROVIDER,
            command="ACCEPTED_HANDLE",
            owner=TransitionOwner.PROVIDER_ADAPTER,
            remote=ProviderRemoteLineage(provider_operation_id=operation_id),
        )
    ).job
    job = (
        await _transition(
            repo,
            job,
            axis=GenerationJobAxis.PROVIDER,
            command="START_POLL",
            owner=TransitionOwner.PROVIDER_ADAPTER,
        )
    ).job
    return repo, job, rest


@pytest.mark.asyncio
async def test_migration_v8_adds_append_only_recovery_evidence_without_new_job_status(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        assert FOUNDATION_SCHEMA_VERSION == 8
        reader = SQLiteReadRepository(writer.db_path)
        migration = await reader.fetchone(
            "SELECT name FROM studio_schema_migration WHERE version=8"
        )
        assert migration is not None
        assert migration["name"] == "studio_generation_recovery_evidence"
        table = await reader.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='studio_generation_recovery_event'"
        )
        assert table is not None
        columns = await reader.fetchall("PRAGMA table_info(studio_generation_job)")
        assert "status" not in {row["name"] for row in columns}
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_crash_before_submit_proves_no_dispatch_and_requeues_without_submit(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, _ = await _running_job(writer)
        coordinator = RecoveryCoordinator(writer)
        result = await coordinator.recover_pre_dispatch(
            job_id=job.generation_job_id,
            recovery_attempt_id="recovery-before-submit-001",
            expected_revision=job.revision,
            actor_ref="recovery:imp054-test",
            reason="process crashed before provider submit transition",
            correlation_id="run:imp054-before-submit",
            recorded_at=NOW,
            evidence_refs=("evidence:transport-never-dispatched",),
        )
        assert result.event.proof_kind is RecoveryProofKind.TRANSPORT_NOT_DISPATCHED
        assert result.event.decision is RecoveryDecision.SAFE_TO_REQUEUE
        assert result.event.failure.error_class is ErrorClass.PROVIDER_TRANSPORT
        assert result.event.failure.retry_disposition is RetryDisposition.RETRYABLE
        assert result.job.provider_state is ProviderState.NOT_SUBMITTED
        assert result.job.scheduler_state is SchedulerState.QUEUED
        history = await repo.list_transitions(job.generation_job_id)
        assert [item.command for item in history].count("SUBMIT") == 0

        replay = await coordinator.recover_pre_dispatch(
            job_id=job.generation_job_id,
            recovery_attempt_id="recovery-before-submit-001",
            expected_revision=job.revision,
            actor_ref="ignored-on-exact-replay",
            reason="exact replay should reuse proof",
            correlation_id="run:imp054-before-submit-replay",
            recorded_at=NOW,
            evidence_refs=("evidence:ignored",),
        )
        assert replay.event == result.event
        assert len(await coordinator.events.list_for_job(job.generation_job_id)) == 1
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_crash_after_possible_submit_never_blind_resubmits_and_enters_ambiguous_hold(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, _ = await _submitting_job(writer)
        probe = _probe(RecoveryProbeOutcome.STILL_AMBIGUOUS)
        result = await RecoveryCoordinator(writer).recover(
            job_id=job.generation_job_id,
            recovery_attempt_id="recovery-ambiguous-001",
            trigger=RecoveryTrigger.SUBMIT_RESPONSE_LOST,
            probe=probe,
            expected_revision=job.revision,
            actor_ref="recovery:imp054-test",
            reason="response lost after possible paid submit",
            correlation_id="run:imp054-ambiguous",
            recorded_at=NOW,
            evidence_refs=("evidence:submit-response-lost",),
        )
        assert probe.calls == 1
        assert result.job.scheduler_state is SchedulerState.WAITING_RECOVERY
        assert result.job.provider_state is ProviderState.AMBIGUOUS_HOLD
        assert result.event.decision is RecoveryDecision.HOLD_AMBIGUOUS
        assert result.event.failure.error_class is ErrorClass.PROVIDER_AMBIGUITY
        assert result.event.failure.retry_disposition is RetryDisposition.RECONCILIATION_REQUIRED
        history = await repo.list_transitions(job.generation_job_id)
        commands = [item.command for item in history]
        assert commands.count("SUBMIT") == 1
        assert "ACCEPTANCE_AMBIGUOUS" in commands
        assert "BEGIN_RECONCILE" in commands
        assert "STILL_AMBIGUOUS" in commands
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_poll_timeout_recovers_same_handle_and_resumes_existing_work(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, job, _ = await _polling_job(writer, operation_id="op-recovered")
        probe = _probe(RecoveryProbeOutcome.RECOVERED_ACTIVE_POLL, handle_id="op-recovered")
        result = await RecoveryCoordinator(writer).recover(
            job_id=job.generation_job_id,
            recovery_attempt_id="recovery-poll-timeout-001",
            trigger=RecoveryTrigger.POLL_TIMEOUT,
            probe=probe,
            expected_revision=job.revision,
            actor_ref="recovery:imp054-test",
            reason="poll timeout requires same-operation reconciliation",
            correlation_id="run:imp054-poll-timeout",
            recorded_at=NOW,
            evidence_refs=("evidence:poll-timeout",),
        )
        assert result.event.proof_kind is RecoveryProofKind.RECOVERED_ACTIVE_POLL
        assert result.event.decision is RecoveryDecision.RESUME_EXISTING
        assert result.job.provider_state is ProviderState.POLLING
        assert result.job.scheduler_state is SchedulerState.RUNNING
        assert result.job.provider_operation_id == "op-recovered"
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_reconciliation_proven_absent_is_only_then_safe_to_requeue(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, job, _ = await _submitting_job(writer)
        probe = _probe(RecoveryProbeOutcome.PROVEN_ABSENT)
        result = await RecoveryCoordinator(writer).recover(
            job_id=job.generation_job_id,
            recovery_attempt_id="recovery-absent-001",
            trigger=RecoveryTrigger.PROCESS_CRASH,
            probe=probe,
            expected_revision=job.revision,
            actor_ref="recovery:imp054-test",
            reason="provider lookup proves no remote operation exists",
            correlation_id="run:imp054-absent",
            recorded_at=NOW,
            evidence_refs=("evidence:provider-listing-negative",),
        )
        assert result.event.proof_kind is RecoveryProofKind.PROVEN_ABSENT
        assert result.job.provider_state is ProviderState.NOT_SUBMITTED
        assert result.job.scheduler_state is SchedulerState.QUEUED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_verified_same_job_idempotency_allows_requeue_but_never_allocates_new_job(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, job, _ = await _submitting_job(writer)
        original_job_id = job.generation_job_id
        probe = _probe(RecoveryProbeOutcome.VERIFIED_SAME_JOB_IDEMPOTENCY)
        result = await RecoveryCoordinator(writer).recover(
            job_id=job.generation_job_id,
            recovery_attempt_id="recovery-idempotent-001",
            trigger=RecoveryTrigger.SUBMIT_RESPONSE_LOST,
            probe=probe,
            expected_revision=job.revision,
            actor_ref="recovery:imp054-test",
            reason="server evidence proves same key maps to same paid job",
            correlation_id="run:imp054-idempotent",
            recorded_at=NOW,
            evidence_refs=("evidence:server-idempotency-contract",),
        )
        assert result.event.proof_kind is RecoveryProofKind.VERIFIED_SAME_JOB_IDEMPOTENCY
        assert result.job.generation_job_id == original_job_id
        assert result.job.idempotency_key == "idempotency-001"
        assert result.job.provider_state is ProviderState.NOT_SUBMITTED
        assert result.job.scheduler_state is SchedulerState.QUEUED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_recovery_event_is_append_only_and_conflicting_attempt_replay_fails_closed(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, job, _ = await _running_job(writer)
        coordinator = RecoveryCoordinator(writer)
        result = await coordinator.recover_pre_dispatch(
            job_id=job.generation_job_id,
            recovery_attempt_id="recovery-immutable-001",
            expected_revision=job.revision,
            actor_ref="recovery:imp054-test",
            reason="append immutable recovery proof",
            correlation_id="run:imp054-immutable",
            recorded_at=NOW,
            evidence_refs=("evidence:no-dispatch",),
        )
        async with aiosqlite.connect(writer.db_path) as db:
            with pytest.raises(aiosqlite.IntegrityError, match="append-only"):
                await db.execute(
                    "UPDATE studio_generation_recovery_event SET reason='rewrite' WHERE recovery_event_id=?",
                    (result.event.recovery_event_id,),
                )
        assert len(await RecoveryEventRepository(writer).list_for_job(job.generation_job_id)) == 1
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_cancellation_race_remote_success_wins_over_local_cancel_intent(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, _ = await _polling_job(writer, operation_id="op-cancel-race")
        job = (
            await _transition(
                repo,
                job,
                axis=GenerationJobAxis.PROVIDER,
                command="REQUEST_CANCEL",
                owner=TransitionOwner.PROVIDER_ADAPTER,
                guard=_guard(cancel_supported=True),
            )
        ).job
        probe = _probe(RecoveryProbeOutcome.REMOTE_SUCCEEDED, handle_id="op-cancel-race")
        result = await RecoveryCoordinator(writer).recover(
            job_id=job.generation_job_id,
            recovery_attempt_id="recovery-cancel-race-001",
            trigger=RecoveryTrigger.CANCELLATION_RACE,
            probe=probe,
            expected_revision=job.revision,
            actor_ref="recovery:imp054-test",
            reason="provider completed before cancellation became terminal",
            correlation_id="run:imp054-cancel-race",
            recorded_at=NOW,
            evidence_refs=("evidence:remote-success-after-cancel",),
        )
        assert result.job.provider_state is ProviderState.REMOTE_SUCCEEDED
        assert result.job.scheduler_state is SchedulerState.RUNNING
        history = await repo.list_transitions(job.generation_job_id)
        assert history[-1].command == "REMOTE_SUCCESS_WON_RACE"
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_remote_canceled_without_local_cancel_intent_fails_closed(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, _ = await _polling_job(writer, operation_id="op-provider-canceled")
        probe = _probe(RecoveryProbeOutcome.REMOTE_CANCELED, handle_id="op-provider-canceled")
        coordinator = RecoveryCoordinator(writer)
        with pytest.raises(RecoveryGateBlocked, match="prior local CANCEL_REQUESTED"):
            await coordinator.recover(
                job_id=job.generation_job_id,
                recovery_attempt_id="recovery-provider-canceled-001",
                trigger=RecoveryTrigger.POLL_TIMEOUT,
                probe=probe,
                expected_revision=job.revision,
                actor_ref="recovery:imp054-test",
                reason="provider reports cancellation without local cancellation intent",
                correlation_id="run:imp054-provider-canceled",
                recorded_at=NOW,
                evidence_refs=("evidence:provider-canceled-without-local-intent",),
            )
        current = await repo.get_job(job.generation_job_id)
        assert current is not None
        assert current.provider_state is ProviderState.RECONCILING
        assert current.provider_state is not ProviderState.REMOTE_CANCELED
        assert await coordinator.events.list_for_job(job.generation_job_id) == []
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_startup_scan_finds_only_remote_or_recovery_inflight_jobs(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, untouched, _, _, _, plan = await _job_fixture(writer)
        polling = await repo.create_job(
            GenerationJobCreateRequest(
                project_id=untouched.project_id,
                shot_ir_ref=untouched.shot_ir_ref,
                routing_decision_ref=untouched.routing_decision_ref,
                provider_profile_ref=untouched.provider_profile_ref,
                expected_input_fingerprint=untouched.expected_input_fingerprint,
                execution_plan=plan,
                attempt=2,
                submission_attempt_id="submission-attempt-startup-002",
                local_submission_key="local-submit-startup-002",
                idempotency_key="idempotency-startup-002",
                created_at=NOW,
                actor_ref="studio:imp054-test",
                reason="create second job without reseeding semantic fixtures",
                correlation_id="run:imp054-startup-scan",
                evidence_refs=("evidence:imp054-startup-create",),
            )
        )
        for axis, command, owner, guard, remote in (
            (GenerationJobAxis.SCHEDULER, "CLAIM", TransitionOwner.SCHEDULER, None, None),
            (GenerationJobAxis.SCHEDULER, "START_WORK", TransitionOwner.SCHEDULER, None, None),
            (
                GenerationJobAxis.PROVIDER,
                "SUBMIT",
                TransitionOwner.PROVIDER_ADAPTER,
                _guard(side_effect_boundary_ready=True),
                None,
            ),
            (
                GenerationJobAxis.PROVIDER,
                "ACCEPTED_HANDLE",
                TransitionOwner.PROVIDER_ADAPTER,
                None,
                ProviderRemoteLineage(provider_operation_id="op-startup"),
            ),
            (
                GenerationJobAxis.PROVIDER,
                "START_POLL",
                TransitionOwner.PROVIDER_ADAPTER,
                None,
                None,
            ),
        ):
            polling = (
                await _transition(
                    repo,
                    polling,
                    axis=axis,
                    command=command,
                    owner=owner,
                    guard=guard,
                    remote=remote,
                )
            ).job

        candidates = await RecoveryCoordinator(writer).list_startup_candidates()
        ids = {job.generation_job_id for job in candidates}
        assert polling.generation_job_id in ids
        assert untouched.generation_job_id not in ids
        assert await repo.get_job(untouched.generation_job_id) == untouched
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_provider_adapter_recovery_probe_reconstructs_workflow_handle_from_request_lineage(tmp_path):
    class CaptureAdapter:
        def __init__(self, provider_key: str) -> None:
            self.provider_key = provider_key
            self.handle = None

        async def reconcile(self, handle, *, observed_at):
            self.handle = handle
            assert handle is not None
            return ProviderTransportObservation(
                provider_key=self.provider_key,
                kind=ProviderObservationKind.RECONCILE,
                state=ProviderObservationState.PENDING,
                observed_at=observed_at,
                handle=handle,
                retry_safe=False,
            )

    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, _ = await _submitting_job(writer)
        job = (
            await _transition(
                repo,
                job,
                axis=GenerationJobAxis.PROVIDER,
                command="ACCEPTED_HANDLE",
                owner=TransitionOwner.PROVIDER_ADAPTER,
                remote=ProviderRemoteLineage(provider_request_id="workflow-001"),
            )
        ).job
        adapter = CaptureAdapter(job.provider_key)
        result = await ProviderAdapterRecoveryProbe(adapter).reconcile(job, observed_at=NOW)
        assert adapter.handle is not None
        assert adapter.handle.kind is ProviderHandleKind.WORKFLOW
        assert adapter.handle.handle_id == "workflow-001"
        assert result.handle == adapter.handle
        assert result.outcome is RecoveryProbeOutcome.RECOVERED_ACTIVE_POLL
    finally:
        await writer.close()
