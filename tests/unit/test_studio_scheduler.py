"""IMP-053 scheduler / DAG / lease / admission tests."""

from __future__ import annotations

import asyncio
from datetime import timedelta

import aiosqlite
import pytest

from agent.studio import (
    DependencyRequirement,
    GenerationJobAxis,
    GenerationJobCreateRequest,
    LeaseState,
    SchedulerAdmissionPolicy,
    SchedulerDependencyError,
    SchedulerIdentityError,
    SchedulerLeaseConflict,
    SchedulerNodeRegistration,
    SchedulerRepository,
    SchedulerState,
    TransitionOwner,
    scheduler_model_capacity_key,
)
from agent.studio.persistence import FOUNDATION_SCHEMA_VERSION, SQLiteReadRepository, SQLiteWriteOwner
from tests.unit.test_studio_directing import NOW, PROJECT_ID
from tests.unit.test_studio_generation_job import _guard, _job_fixture


EVIDENCE = ("evidence:imp053",)


async def _jobs(writer: SQLiteWriteOwner, count: int = 1):
    repo, first, ir, profile, decision, plan = await _job_fixture(writer)
    jobs = [first]
    for index in range(2, count + 1):
        jobs.append(
            await repo.create_job(
                GenerationJobCreateRequest(
                    project_id=PROJECT_ID,
                    shot_ir_ref=ir.ref,
                    routing_decision_ref=decision.ref,
                    provider_profile_ref=profile.ref,
                    expected_input_fingerprint=ir.hashes.input_fingerprint,
                    execution_plan=plan,
                    attempt=index,
                    submission_attempt_id=f"submission-attempt-{index:03d}",
                    local_submission_key=f"local-submit-{index:03d}",
                    idempotency_key=f"idempotency-{index:03d}",
                    created_at=NOW,
                    actor_ref="studio:imp053-test",
                    reason="create additional scheduler fixture job",
                    correlation_id="run:imp053",
                    evidence_refs=EVIDENCE,
                )
            )
        )
    return repo, jobs


async def _register(
    scheduler: SchedulerRepository,
    job,
    *,
    priority: int = 10,
    operation: str = "video.generate",
    resource: str = "remote.flow",
    estimated_cost: int = 100,
):
    return await scheduler.register_node(
        SchedulerNodeRegistration(
            generation_job_id=job.generation_job_id,
            priority_class=priority,
            operation_key=operation,
            local_resource_key=resource,
            estimated_cost_microunits=estimated_cost,
            evidence_refs=EVIDENCE,
        ),
        created_at=NOW,
    )


def _policy(job, *, global_limit: int = 4, budget: int = 10000, spent: int = 0, **overrides):
    values = dict(
        policy_id="scheduler-policy:v1",
        global_limit=global_limit,
        provider_limits={job.provider_key: 4},
        model_limits={scheduler_model_capacity_key(job): 4},
        operation_limits={"video.generate": 4},
        local_resource_limits={"remote.flow": 4},
        budget_limit_microunits=budget,
        budget_spent_microunits=spent,
        evidence_refs=("evidence:imp053-policy",),
    )
    values.update(overrides)
    return SchedulerAdmissionPolicy(**values)


async def _ready(scheduler: SchedulerRepository, job):
    return await scheduler.evaluate_readiness(
        job_id=job.generation_job_id,
        actor_ref="scheduler:imp053-test",
        reason="evaluate dependency readiness",
        correlation_id="run:imp053",
        recorded_at=NOW,
        evidence_refs=EVIDENCE,
    )


@pytest.mark.asyncio
async def test_migration_v7_adds_scheduler_coordination_without_second_status(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        assert FOUNDATION_SCHEMA_VERSION == 7
        reader = SQLiteReadRepository(writer.db_path)
        migration = await reader.fetchone(
            "SELECT name FROM studio_schema_migration WHERE version=7"
        )
        assert migration is not None
        assert migration["name"] == "studio_scheduler_dag_leases_admission"
        tables = await reader.fetchall(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'studio_scheduler_%'"
        )
        names = {row["name"] for row in tables}
        assert {
            "studio_scheduler_node",
            "studio_scheduler_dependency",
            "studio_scheduler_checkpoint",
            "studio_scheduler_checkpoint_history",
            "studio_scheduler_lease",
            "studio_scheduler_lease_history",
            "studio_scheduler_admission",
            "studio_scheduler_fairness_cursor",
        } <= names
        node_columns = {
            row["name"] for row in await reader.fetchall("PRAGMA table_info(studio_scheduler_node)")
        }
        assert "status" not in node_columns
        assert "scheduler_state" not in node_columns
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_scheduler_node_exact_replay_is_idempotent_and_conflict_fails(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, jobs = await _jobs(writer)
        scheduler = SchedulerRepository(writer)
        first = await _register(scheduler, jobs[0])
        second = await _register(scheduler, jobs[0])
        assert first == second
        with pytest.raises(SchedulerIdentityError, match="immutable metadata"):
            await _register(scheduler, jobs[0], priority=11)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_dependency_gate_blocks_then_releases_through_legal_job_transitions(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        jobs_repo, jobs = await _jobs(writer, 2)
        upstream, downstream = jobs
        scheduler = SchedulerRepository(writer)
        await _register(scheduler, upstream)
        await _register(scheduler, downstream)
        edge = await scheduler.add_dependency(
            upstream_job_id=upstream.generation_job_id,
            downstream_job_id=downstream.generation_job_id,
            requirement=DependencyRequirement.SCHEDULER_TERMINAL,
            evidence_refs=EVIDENCE,
            created_at=NOW,
        )
        blocked = await _ready(scheduler, downstream)
        assert blocked.dependency_ready is False
        assert blocked.blocked_dependency_ids == (edge.dependency_edge_id,)
        waiting = await jobs_repo.get_job(downstream.generation_job_id)
        assert waiting is not None and waiting.scheduler_state is SchedulerState.WAITING_DEPENDENCY

        result = await jobs_repo.transition(
            job_id=upstream.generation_job_id,
            axis=GenerationJobAxis.SCHEDULER,
            command="CANCEL_BEFORE_SIDE_EFFECT",
            owner=TransitionOwner.SCHEDULER,
            guard_evidence=_guard(),
            expected_revision=upstream.revision,
            actor_ref="scheduler:imp053-test",
            reason="finish upstream before side effect",
            correlation_id="run:imp053-upstream",
            recorded_at=NOW,
        )
        assert result.job.scheduler_state is SchedulerState.TERMINAL
        ready = await _ready(scheduler, downstream)
        assert ready.dependency_ready is True
        released = await jobs_repo.get_job(downstream.generation_job_id)
        assert released is not None and released.scheduler_state is SchedulerState.QUEUED

        reader = SQLiteReadRepository(writer.db_path)
        history = await reader.fetchall(
            "SELECT to_revision,dependency_ready FROM studio_scheduler_checkpoint_history WHERE generation_job_id=? ORDER BY to_revision",
            (downstream.generation_job_id.root,),
        )
        assert [int(row["dependency_ready"]) for row in history] == [0, 1]
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_dag_cycle_is_rejected_and_topology_is_immutable(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, jobs = await _jobs(writer, 2)
        first, second = jobs
        scheduler = SchedulerRepository(writer)
        await _register(scheduler, first)
        await _register(scheduler, second)
        edge = await scheduler.add_dependency(
            upstream_job_id=first.generation_job_id,
            downstream_job_id=second.generation_job_id,
            requirement=DependencyRequirement.SCHEDULER_TERMINAL,
            evidence_refs=EVIDENCE,
            created_at=NOW,
        )
        with pytest.raises(SchedulerDependencyError, match="cycle"):
            await scheduler.add_dependency(
                upstream_job_id=second.generation_job_id,
                downstream_job_id=first.generation_job_id,
                requirement=DependencyRequirement.SCHEDULER_TERMINAL,
                evidence_refs=EVIDENCE,
                created_at=NOW,
            )

        async def mutate(tx):
            await tx.execute(
                "UPDATE studio_scheduler_dependency SET requirement='ARTIFACT_READY' WHERE dependency_edge_id=?",
                (edge.dependency_edge_id,),
            )

        with pytest.raises(aiosqlite.IntegrityError, match="immutable"):
            await writer.execute(mutate)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_admission_missing_cap_blocks_and_capacity_available_requeues(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        jobs_repo, jobs = await _jobs(writer)
        job = jobs[0]
        scheduler = SchedulerRepository(writer)
        await _register(scheduler, job)
        await _ready(scheduler, job)

        missing_provider = _policy(job, provider_limits={})
        blocked = await scheduler.evaluate_admission(
            job_id=job.generation_job_id,
            policy=missing_provider,
            actor_ref="scheduler:imp053-test",
            reason="missing cap must fail closed",
            correlation_id="run:imp053-admission-block",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        assert blocked.admitted is False
        assert "MISSING_PROVIDER_CAPACITY" in blocked.reasons
        waiting = await jobs_repo.get_job(job.generation_job_id)
        assert waiting is not None and waiting.scheduler_state is SchedulerState.WAITING_CAPACITY

        admitted = await scheduler.evaluate_admission(
            job_id=job.generation_job_id,
            policy=_policy(job),
            actor_ref="scheduler:imp053-test",
            reason="capacity now available",
            correlation_id="run:imp053-admission-pass",
            recorded_at=NOW + timedelta(seconds=1),
            evidence_refs=EVIDENCE,
        )
        assert admitted.admitted is True
        queued = await jobs_repo.get_job(job.generation_job_id)
        assert queued is not None and queued.scheduler_state is SchedulerState.QUEUED
        checkpoint = await scheduler.get_checkpoint(job.generation_job_id)
        assert checkpoint is not None
        assert checkpoint.last_admission_decision_id == admitted.decision_id
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_budget_gate_stops_new_submission_without_mutating_job_identity(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, jobs = await _jobs(writer)
        job = jobs[0]
        scheduler = SchedulerRepository(writer)
        await _register(scheduler, job, estimated_cost=500)
        await _ready(scheduler, job)
        decision = await scheduler.evaluate_admission(
            job_id=job.generation_job_id,
            policy=_policy(job, budget=1000, spent=600),
            actor_ref="scheduler:imp053-test",
            reason="budget boundary",
            correlation_id="run:imp053-budget",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        assert decision.admitted is False
        assert "BUDGET_CAPACITY" in decision.reasons
        stored = await scheduler.jobs.get_job(job.generation_job_id)
        assert stored is not None
        assert stored.shot_ir_ref == job.shot_ir_ref
        assert stored.provider_profile_ref == job.provider_profile_ref
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_claim_requires_hierarchical_admission_and_active_lease_before_start(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, jobs = await _jobs(writer)
        job = jobs[0]
        scheduler = SchedulerRepository(writer)
        await _register(scheduler, job)
        await _ready(scheduler, job)
        claim = await scheduler.claim_next(
            policy=_policy(job),
            worker_id="worker-a",
            lease_ttl_seconds=30,
            actor_ref="scheduler:imp053-test",
            reason="claim admitted work",
            correlation_id="run:imp053-claim",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        assert claim is not None
        assert claim.admission.admitted is True
        assert claim.job.scheduler_state is SchedulerState.CLAIMED
        assert claim.lease.state is LeaseState.ACTIVE

        with pytest.raises(SchedulerLeaseConflict, match="mismatch"):
            await scheduler.start_work(
                job_id=job.generation_job_id,
                lease_token="lease-wrong",
                worker_id="worker-a",
                actor_ref="worker:imp053-test",
                reason="wrong lease must fail",
                correlation_id="run:imp053-start-bad",
                recorded_at=NOW + timedelta(seconds=1),
                evidence_refs=EVIDENCE,
            )
        running = await scheduler.start_work(
            job_id=job.generation_job_id,
            lease_token=claim.lease.lease_token,
            worker_id="worker-a",
            actor_ref="worker:imp053-test",
            reason="start under matching lease",
            correlation_id="run:imp053-start",
            recorded_at=NOW + timedelta(seconds=1),
            evidence_refs=EVIDENCE,
        )
        assert running.scheduler_state is SchedulerState.RUNNING

        renewed = await scheduler.renew_lease(
            job_id=job.generation_job_id,
            lease_token=claim.lease.lease_token,
            worker_id="worker-a",
            lease_ttl_seconds=60,
            actor_ref="worker:imp053-test",
            reason="renew active work lease",
            correlation_id="run:imp053-renew",
            recorded_at=NOW + timedelta(seconds=2),
            evidence_refs=EVIDENCE,
        )
        assert renewed.revision == claim.lease.revision + 1
        released = await scheduler.release_lease(
            job_id=job.generation_job_id,
            lease_token=claim.lease.lease_token,
            worker_id="worker-a",
            actor_ref="worker:imp053-test",
            reason="release work lease",
            correlation_id="run:imp053-release",
            recorded_at=NOW + timedelta(seconds=3),
            evidence_refs=EVIDENCE,
        )
        assert released.state is LeaseState.RELEASED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_global_backpressure_blocks_second_job_until_capacity_frees(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, jobs = await _jobs(writer, 2)
        first, second = jobs
        scheduler = SchedulerRepository(writer)
        for job in jobs:
            await _register(scheduler, job)
            await _ready(scheduler, job)
        policy = _policy(first, global_limit=1)
        claim = await scheduler.claim_next(
            policy=policy,
            worker_id="worker-a",
            lease_ttl_seconds=30,
            actor_ref="scheduler:imp053-test",
            reason="consume only global slot",
            correlation_id="run:imp053-capacity-claim",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        assert claim is not None
        blocked = await scheduler.evaluate_admission(
            job_id=second.generation_job_id,
            policy=policy,
            actor_ref="scheduler:imp053-test",
            reason="second job sees backpressure",
            correlation_id="run:imp053-capacity-block",
            recorded_at=NOW + timedelta(seconds=1),
            evidence_refs=EVIDENCE,
        )
        assert blocked.admitted is False
        assert "GLOBAL_CAPACITY" in blocked.reasons
        await scheduler.release_lease(
            job_id=claim.job.generation_job_id,
            lease_token=claim.lease.lease_token,
            worker_id=claim.lease.worker_id,
            actor_ref="scheduler:imp053-test",
            reason="free global slot",
            correlation_id="run:imp053-capacity-release",
            recorded_at=NOW + timedelta(seconds=2),
            evidence_refs=EVIDENCE,
        )
        admitted = await scheduler.evaluate_admission(
            job_id=second.generation_job_id,
            policy=policy,
            actor_ref="scheduler:imp053-test",
            reason="capacity restored",
            correlation_id="run:imp053-capacity-restored",
            recorded_at=NOW + timedelta(seconds=3),
            evidence_refs=EVIDENCE,
        )
        assert admitted.admitted is True
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_serialized_concurrent_claims_cannot_oversubscribe_global_cap(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, jobs = await _jobs(writer, 2)
        scheduler = SchedulerRepository(writer)
        for job in jobs:
            await _register(scheduler, job)
            await _ready(scheduler, job)
        policy = _policy(jobs[0], global_limit=1)

        async def claim(worker):
            return await scheduler.claim_next(
                policy=policy,
                worker_id=worker,
                lease_ttl_seconds=30,
                actor_ref="scheduler:imp053-test",
                reason="concurrent serialized claim",
                correlation_id=f"run:imp053-{worker}",
                recorded_at=NOW,
                evidence_refs=EVIDENCE,
            )

        results = await asyncio.gather(claim("worker-a"), claim("worker-b"))
        claimed = [item for item in results if item is not None]
        assert len(claimed) == 1
        reader = SQLiteReadRepository(writer.db_path)
        active = await reader.fetchall(
            "SELECT generation_job_id FROM studio_scheduler_lease WHERE state='ACTIVE' AND expires_at>?",
            (NOW.isoformat(),),
        )
        assert len(active) == 1
    finally:
        await writer.close()


def test_fair_order_is_priority_then_project_round_robin_then_oldest_ready():
    rows = [
        {"generation_job_id": "job:a1", "priority_class": 10, "ready_since": "2026-10-05T00:00:00+00:00", "project_id": "project:a"},
        {"generation_job_id": "job:a2", "priority_class": 10, "ready_since": "2026-10-05T00:01:00+00:00", "project_id": "project:a"},
        {"generation_job_id": "job:b1", "priority_class": 10, "ready_since": "2026-10-05T00:00:30+00:00", "project_id": "project:b"},
        {"generation_job_id": "job:b2", "priority_class": 10, "ready_since": "2026-10-05T00:02:00+00:00", "project_id": "project:b"},
        {"generation_job_id": "job:critical", "priority_class": 0, "ready_since": "2026-10-05T00:05:00+00:00", "project_id": "project:z"},
    ]
    ordered = SchedulerRepository._fair_order_rows(rows, {10: "project:a"})
    assert [item.root for item in ordered] == [
        "job:critical",
        "job:b1",
        "job:a1",
        "job:b2",
        "job:a2",
    ]


@pytest.mark.asyncio
async def test_restart_expires_claimed_lease_but_requires_recovery_not_blind_requeue(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, jobs = await _jobs(writer)
        job = jobs[0]
        scheduler = SchedulerRepository(writer)
        await _register(scheduler, job)
        await _ready(scheduler, job)
        claim = await scheduler.claim_next(
            policy=_policy(job),
            worker_id="worker-a",
            lease_ttl_seconds=1,
            actor_ref="scheduler:imp053-test",
            reason="short lease for restart test",
            correlation_id="run:imp053-restart-claim",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        assert claim is not None
        report = await scheduler.recover_startup(
            recorded_at=NOW + timedelta(seconds=2),
            actor_ref="scheduler:imp053-test",
            reason="restart recovery scan",
            correlation_id="run:imp053-restart",
            evidence_refs=EVIDENCE,
        )
        assert job.generation_job_id in report.recovery_required_jobs
        assert job.generation_job_id not in report.expired_idle_leases
        stored = await scheduler.jobs.get_job(job.generation_job_id)
        assert stored is not None and stored.scheduler_state is SchedulerState.CLAIMED
        lease = await scheduler.get_lease(job.generation_job_id)
        assert lease is not None and lease.state is LeaseState.EXPIRED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_restart_recomputes_missing_readiness_checkpoint_durably(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, jobs = await _jobs(writer)
        job = jobs[0]
        scheduler = SchedulerRepository(writer)
        await _register(scheduler, job)
        assert await scheduler.get_checkpoint(job.generation_job_id) is None
        report = await scheduler.recover_startup(
            recorded_at=NOW,
            actor_ref="scheduler:imp053-test",
            reason="restart recomputes readiness",
            correlation_id="run:imp053-restart-ready",
            evidence_refs=EVIDENCE,
        )
        assert job.generation_job_id in report.reevaluated_jobs
        checkpoint = await scheduler.get_checkpoint(job.generation_job_id)
        assert checkpoint is not None and checkpoint.dependency_ready is True
        reader = SQLiteReadRepository(writer.db_path)
        history = await reader.fetchall(
            "SELECT * FROM studio_scheduler_checkpoint_history WHERE generation_job_id=?",
            (job.generation_job_id.root,),
        )
        assert len(history) == 1
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_blocked_dependency_never_gets_lease_or_execution(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, jobs = await _jobs(writer, 2)
        upstream, downstream = jobs
        scheduler = SchedulerRepository(writer)
        await _register(scheduler, upstream)
        await _register(scheduler, downstream)
        await scheduler.add_dependency(
            upstream_job_id=upstream.generation_job_id,
            downstream_job_id=downstream.generation_job_id,
            requirement=DependencyRequirement.SCHEDULER_TERMINAL,
            evidence_refs=EVIDENCE,
            created_at=NOW,
        )
        await _ready(scheduler, downstream)
        claim = await scheduler.claim_next(
            policy=_policy(downstream),
            worker_id="worker-a",
            lease_ttl_seconds=30,
            actor_ref="scheduler:imp053-test",
            reason="blocked dependency must not execute",
            correlation_id="run:imp053-blocked-claim",
            recorded_at=NOW,
            evidence_refs=EVIDENCE,
        )
        assert claim is None
        assert await scheduler.get_lease(downstream.generation_job_id) is None
    finally:
        await writer.close()
