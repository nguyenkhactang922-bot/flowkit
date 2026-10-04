"""IMP-052 GenerationJob four-axis state-machine tests."""

from __future__ import annotations

import aiosqlite
import pytest
from pydantic import ValidationError

from agent.studio import (
    ArtifactState,
    CreativeState,
    DerivedJobStatus,
    GenerationJobAxis,
    GenerationJobCreateRequest,
    GenerationJobIdentityError,
    GenerationJobRepository,
    GenerationJobStateTuple,
    GenerationJobTransitionError,
    GenerationJobTupleError,
    GuardFact,
    ProviderAdapterPrepareRequest,
    ProviderAdapterPreflight,
    ProviderExecutionMode,
    ProviderRemoteLineage,
    ProviderState,
    SchedulerState,
    TRANSITION_RULES,
    TransitionGuardEvidence,
    TransitionOwner,
    derive_job_status,
    resolve_transition_rule,
)
from agent.studio.persistence import CASConflict, FOUNDATION_SCHEMA_VERSION, SQLiteReadRepository, SQLiteWriteOwner
from tests.unit.test_studio_directing import NOW, PROJECT_ID
from tests.unit.test_studio_provider_adapter import _runtime_refs, _selected_route_fixture


def _guard(summary: str = "source-backed transition guard", **facts) -> TransitionGuardEvidence:
    return TransitionGuardEvidence(
        summary=summary,
        evidence_refs=("evidence:imp052",),
        facts=tuple(GuardFact(key=key, value=value) for key, value in facts.items()),
    )


async def _job_fixture(writer: SQLiteWriteOwner):
    _, ir, profile, decision = await _selected_route_fixture(writer, provider_key="flow")
    plan = await ProviderAdapterPreflight(writer).prepare(
        ProviderAdapterPrepareRequest(
            project_id=PROJECT_ID,
            shot_ir_ref=ir.ref,
            routing_decision_ref=decision.ref,
            mode=ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
            runtime_references=_runtime_refs(ir),
            execution_as_of=NOW,
        )
    )
    repo = GenerationJobRepository(writer)
    job = await repo.create_job(
        GenerationJobCreateRequest(
            project_id=PROJECT_ID,
            shot_ir_ref=ir.ref,
            routing_decision_ref=decision.ref,
            provider_profile_ref=profile.ref,
            expected_input_fingerprint=ir.hashes.input_fingerprint,
            execution_plan=plan,
            attempt=1,
            submission_attempt_id="submission-attempt-001",
            local_submission_key="local-submit-001",
            idempotency_key="idempotency-001",
            created_at=NOW,
            actor_ref="studio:imp052-test",
            reason="create canonical generation job fixture",
            correlation_id="run:imp052",
            evidence_refs=("evidence:imp052-create",),
        )
    )
    return repo, job, ir, profile, decision, plan


async def _transition(
    repo: GenerationJobRepository,
    job,
    *,
    axis: GenerationJobAxis,
    command: str,
    owner: TransitionOwner,
    guard: TransitionGuardEvidence | None = None,
    remote: ProviderRemoteLineage | None = None,
):
    return await repo.transition(
        job_id=job.generation_job_id,
        axis=axis,
        command=command,
        owner=owner,
        guard_evidence=guard or _guard(),
        expected_revision=job.revision,
        actor_ref="studio:imp052-test",
        reason=f"test {axis.value} {command}",
        correlation_id="run:imp052",
        recorded_at=NOW,
        remote_lineage=remote,
    )


@pytest.mark.asyncio
async def test_migration_v6_persists_four_axes_and_no_generic_status(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        reader = SQLiteReadRepository(writer.db_path)
        migration = await reader.fetchone(
            "SELECT version,name FROM studio_schema_migration WHERE version=?",
            (FOUNDATION_SCHEMA_VERSION,),
        )
        assert FOUNDATION_SCHEMA_VERSION == 6
        assert migration is not None and migration["name"] == "studio_generation_job_four_axis"
        columns = await reader.fetchall("PRAGMA table_info(studio_generation_job)")
        names = {row["name"] for row in columns}
        assert {"scheduler_state", "provider_state", "artifact_state", "creative_state", "revision"} <= names
        assert "status" not in names
        transitions = await reader.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='studio_generation_job_transition'"
        )
        assert transitions is not None
    finally:
        await writer.close()


def test_closed_contract_has_exact_62_unique_rows_and_declared_targets():
    assert len(TRANSITION_RULES) == 62
    keys = {rule.key for rule in TRANSITION_RULES}
    assert len(keys) == 62
    by_axis = {axis: 0 for axis in GenerationJobAxis}
    declared = {
        GenerationJobAxis.SCHEDULER: {item.value for item in SchedulerState},
        GenerationJobAxis.PROVIDER: {item.value for item in ProviderState},
        GenerationJobAxis.ARTIFACT: {item.value for item in ArtifactState},
        GenerationJobAxis.CREATIVE: {item.value for item in CreativeState},
    }
    for rule in TRANSITION_RULES:
        by_axis[rule.axis] += 1
        assert rule.from_state in declared[rule.axis]
        assert rule.to_state in declared[rule.axis]
        assert rule.owners
    assert by_axis == {
        GenerationJobAxis.SCHEDULER: 15,
        GenerationJobAxis.PROVIDER: 19,
        GenerationJobAxis.ARTIFACT: 14,
        GenerationJobAxis.CREATIVE: 14,
    }


def test_every_declared_state_is_graph_reachable_from_axis_initial_state():
    cases = (
        (GenerationJobAxis.SCHEDULER, SchedulerState.QUEUED.value, {item.value for item in SchedulerState}),
        (GenerationJobAxis.PROVIDER, ProviderState.NOT_SUBMITTED.value, {item.value for item in ProviderState}),
        (GenerationJobAxis.ARTIFACT, ArtifactState.NONE.value, {item.value for item in ArtifactState}),
        (GenerationJobAxis.CREATIVE, CreativeState.NOT_APPLICABLE.value, {item.value for item in CreativeState}),
    )
    for axis, initial, expected in cases:
        reachable = {initial}
        while True:
            expanded = reachable | {
                rule.to_state
                for rule in TRANSITION_RULES
                if rule.axis is axis and rule.from_state in reachable
            }
            if expanded == reachable:
                break
            reachable = expanded
        assert reachable == expected


def test_every_unspecified_state_command_pair_is_rejected_by_closed_resolver():
    enum_for_axis = {
        GenerationJobAxis.SCHEDULER: SchedulerState,
        GenerationJobAxis.PROVIDER: ProviderState,
        GenerationJobAxis.ARTIFACT: ArtifactState,
        GenerationJobAxis.CREATIVE: CreativeState,
    }
    for axis, state_enum in enum_for_axis.items():
        commands = {rule.command for rule in TRANSITION_RULES if rule.axis is axis}
        legal = {rule.key for rule in TRANSITION_RULES if rule.axis is axis}
        for state in state_enum:
            for command in commands | {"UNSPECIFIED_EVENT"}:
                key = (axis, state.value, command)
                if key in legal:
                    assert resolve_transition_rule(*key) is not None
                else:
                    with pytest.raises(GenerationJobTransitionError, match="unsupported transition"):
                        resolve_transition_rule(*key)


def test_v013_cross_axis_valid_and_invalid_fixtures_are_preserved():
    valid = (
        (SchedulerState.QUEUED, ProviderState.NOT_SUBMITTED, ArtifactState.NONE, CreativeState.NOT_APPLICABLE),
        (SchedulerState.WAITING_RECOVERY, ProviderState.AMBIGUOUS_HOLD, ArtifactState.NONE, CreativeState.NOT_APPLICABLE),
        (SchedulerState.TERMINAL, ProviderState.REMOTE_SUCCEEDED, ArtifactState.READY, CreativeState.QA_FAILED),
        (SchedulerState.TERMINAL, ProviderState.REMOTE_SUCCEEDED, ArtifactState.STALE_RESULT, CreativeState.REJECTED),
        (SchedulerState.TERMINAL, ProviderState.REMOTE_SUCCEEDED, ArtifactState.MISSING, CreativeState.APPROVED),
    )
    for values in valid:
        assert GenerationJobStateTuple(
            scheduler=values[0], provider=values[1], artifact=values[2], creative=values[3]
        )

    invalid = (
        (SchedulerState.TERMINAL, ProviderState.POLLING, ArtifactState.NONE, CreativeState.NOT_APPLICABLE),
        (SchedulerState.RUNNING, ProviderState.NOT_SUBMITTED, ArtifactState.READY, CreativeState.PENDING_QA),
        (SchedulerState.RUNNING, ProviderState.REMOTE_SUCCEEDED, ArtifactState.NONE, CreativeState.QA_RUNNING),
    )
    for values in invalid:
        with pytest.raises(ValidationError):
            GenerationJobStateTuple(
                scheduler=values[0], provider=values[1], artifact=values[2], creative=values[3]
            )


@pytest.mark.asyncio
async def test_create_job_pins_exact_upstream_identity_and_initial_tuple(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, ir, profile, decision, plan = await _job_fixture(writer)
        assert job.shot_ir_ref == ir.ref
        assert job.routing_decision_ref == decision.ref
        assert job.provider_profile_ref == profile.ref
        assert job.expected_input_fingerprint == ir.hashes.input_fingerprint
        assert job.execution_plan_hash == plan.plan_hash
        assert job.state_tuple == GenerationJobStateTuple(
            scheduler=SchedulerState.QUEUED,
            provider=ProviderState.NOT_SUBMITTED,
            artifact=ArtifactState.NONE,
            creative=CreativeState.NOT_APPLICABLE,
        )
        assert job.revision == 0
        assert job.derived_status is DerivedJobStatus.WAITING
        loaded = await repo.get_job(job.generation_job_id)
        assert loaded == job
        replay = await repo.create_job(
            GenerationJobCreateRequest(
                project_id=PROJECT_ID,
                shot_ir_ref=ir.ref,
                routing_decision_ref=decision.ref,
                provider_profile_ref=profile.ref,
                expected_input_fingerprint=ir.hashes.input_fingerprint,
                execution_plan=plan,
                attempt=1,
                submission_attempt_id="submission-attempt-001",
                local_submission_key="local-submit-001",
                idempotency_key="idempotency-001",
                created_at=NOW,
                actor_ref="studio:imp052-test",
                reason="create canonical generation job fixture",
                correlation_id="run:imp052",
                evidence_refs=("evidence:imp052-create",),
            )
        )
        assert replay == job
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_job_creation_rejects_wrong_input_fingerprint(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, profile, decision = await _selected_route_fixture(writer, provider_key="flow")
        plan = await ProviderAdapterPreflight(writer).prepare(
            ProviderAdapterPrepareRequest(
                project_id=PROJECT_ID,
                shot_ir_ref=ir.ref,
                routing_decision_ref=decision.ref,
                mode=ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
                runtime_references=_runtime_refs(ir),
                execution_as_of=NOW,
            )
        )
        repo = GenerationJobRepository(writer)
        with pytest.raises(GenerationJobIdentityError, match="fingerprint"):
            await repo.create_job(
                GenerationJobCreateRequest(
                    project_id=PROJECT_ID,
                    shot_ir_ref=ir.ref,
                    routing_decision_ref=decision.ref,
                    provider_profile_ref=profile.ref,
                    expected_input_fingerprint="sha256:" + "f" * 64,
                    execution_plan=plan,
                    attempt=1,
                    submission_attempt_id="submission-wrong",
                    local_submission_key="local-wrong",
                    created_at=NOW,
                    actor_ref="studio:imp052-test",
                    reason="reject fingerprint drift",
                    correlation_id="run:imp052-wrong",
                    evidence_refs=("evidence:wrong",),
                )
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_legal_transition_changes_exactly_one_axis_and_appends_history(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, *_ = await _job_fixture(writer)
        result = await _transition(
            repo,
            job,
            axis=GenerationJobAxis.SCHEDULER,
            command="EVALUATE_DEPENDENCIES",
            owner=TransitionOwner.SCHEDULER,
        )
        assert result.job.scheduler_state is SchedulerState.WAITING_DEPENDENCY
        assert result.job.provider_state is job.provider_state
        assert result.job.artifact_state is job.artifact_state
        assert result.job.creative_state is job.creative_state
        assert result.job.revision == 1
        history = await repo.list_transitions(job.generation_job_id)
        assert history == [result.transition]
        assert history[0].from_revision == 0 and history[0].to_revision == 1
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_wrong_owner_and_unspecified_transition_leave_job_unchanged(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, *_ = await _job_fixture(writer)
        with pytest.raises(GenerationJobTransitionError, match="owner"):
            await _transition(
                repo,
                job,
                axis=GenerationJobAxis.SCHEDULER,
                command="CLAIM",
                owner=TransitionOwner.PROVIDER_ADAPTER,
            )
        with pytest.raises(GenerationJobTransitionError, match="unsupported"):
            await _transition(
                repo,
                job,
                axis=GenerationJobAxis.SCHEDULER,
                command="START_WORK",
                owner=TransitionOwner.SCHEDULER,
            )
        assert await repo.get_job(job.generation_job_id) == job
        assert await repo.list_transitions(job.generation_job_id) == []
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_cas_rejected_without_partial_transition_history(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, *_ = await _job_fixture(writer)
        first = await _transition(
            repo,
            job,
            axis=GenerationJobAxis.SCHEDULER,
            command="EVALUATE_DEPENDENCIES",
            owner=TransitionOwner.SCHEDULER,
        )
        with pytest.raises(CASConflict, match="stale GenerationJob revision"):
            await repo.transition(
                job_id=job.generation_job_id,
                axis=GenerationJobAxis.SCHEDULER,
                command="DEPENDENCIES_READY",
                owner=TransitionOwner.SCHEDULER,
                guard_evidence=_guard(),
                expected_revision=0,
                actor_ref="studio:imp052-test",
                reason="stale writer",
                correlation_id="run:stale",
                recorded_at=NOW,
            )
        assert (await repo.get_job(job.generation_job_id)).revision == 1
        assert await repo.list_transitions(job.generation_job_id) == [first.transition]
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_db_trigger_rejects_immutable_input_rewrite(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, job, *_ = await _job_fixture(writer)

        async def mutate(tx):
            await tx.execute(
                """
                UPDATE studio_generation_job
                SET expected_input_fingerprint=?, scheduler_state='WAITING_DEPENDENCY', revision=revision+1
                WHERE generation_job_id=?
                """,
                ("sha256:" + "9" * 64, job.generation_job_id.root),
            )

        with pytest.raises(aiosqlite.IntegrityError, match="immutable identity"):
            await writer.execute(mutate)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_no_blind_resubmit_after_ambiguous_submit_without_reconciliation_proof(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, *_ = await _job_fixture(writer)
        job = (await _transition(repo, job, axis=GenerationJobAxis.SCHEDULER, command="CLAIM", owner=TransitionOwner.SCHEDULER)).job
        job = (await _transition(repo, job, axis=GenerationJobAxis.SCHEDULER, command="START_WORK", owner=TransitionOwner.SCHEDULER)).job
        job = (await _transition(
            repo, job, axis=GenerationJobAxis.PROVIDER, command="SUBMIT",
            owner=TransitionOwner.PROVIDER_ADAPTER,
            guard=_guard(side_effect_boundary_ready=True),
        )).job
        job = (await _transition(
            repo, job, axis=GenerationJobAxis.PROVIDER, command="ACCEPTANCE_AMBIGUOUS",
            owner=TransitionOwner.PROVIDER_ADAPTER,
        )).job
        assert job.provider_state is ProviderState.UNKNOWN_REMOTE_STATE
        with pytest.raises(GenerationJobTransitionError, match="unsupported"):
            await _transition(
                repo, job, axis=GenerationJobAxis.PROVIDER, command="SUBMIT",
                owner=TransitionOwner.PROVIDER_ADAPTER,
                guard=_guard(side_effect_boundary_ready=True),
            )
        job = (await _transition(
            repo, job, axis=GenerationJobAxis.PROVIDER, command="BEGIN_RECONCILE",
            owner=TransitionOwner.RECOVERY_COORDINATOR,
        )).job
        with pytest.raises(GenerationJobTransitionError, match="absence/idempotency proof"):
            await _transition(
                repo, job, axis=GenerationJobAxis.PROVIDER, command="PROVEN_ABSENT",
                owner=TransitionOwner.RECOVERY_COORDINATOR,
            )
        job = (await _transition(
            repo, job, axis=GenerationJobAxis.PROVIDER, command="PROVEN_ABSENT",
            owner=TransitionOwner.RECOVERY_COORDINATOR,
            guard=_guard(proven_absent=True),
        )).job
        assert job.provider_state is ProviderState.NOT_SUBMITTED
        job = (await _transition(
            repo, job, axis=GenerationJobAxis.PROVIDER, command="SUBMIT",
            owner=TransitionOwner.PROVIDER_ADAPTER,
            guard=_guard(side_effect_boundary_ready=True),
        )).job
        assert job.provider_state is ProviderState.SUBMITTING
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_remote_lineage_is_durable_and_cannot_be_rebound(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, *_ = await _job_fixture(writer)
        job = (await _transition(repo, job, axis=GenerationJobAxis.SCHEDULER, command="CLAIM", owner=TransitionOwner.SCHEDULER)).job
        job = (await _transition(repo, job, axis=GenerationJobAxis.SCHEDULER, command="START_WORK", owner=TransitionOwner.SCHEDULER)).job
        job = (await _transition(
            repo, job, axis=GenerationJobAxis.PROVIDER, command="SUBMIT",
            owner=TransitionOwner.PROVIDER_ADAPTER,
            guard=_guard(side_effect_boundary_ready=True),
        )).job
        job = (await _transition(
            repo, job, axis=GenerationJobAxis.PROVIDER, command="ACCEPTED_HANDLE",
            owner=TransitionOwner.PROVIDER_ADAPTER,
            remote=ProviderRemoteLineage(provider_operation_id="op-001"),
        )).job
        assert job.provider_operation_id == "op-001"
        job = (await _transition(
            repo, job, axis=GenerationJobAxis.PROVIDER, command="RECOVERY_SCAN",
            owner=TransitionOwner.RECOVERY_COORDINATOR,
        )).job
        with pytest.raises(GenerationJobTransitionError, match="cannot be rebound"):
            await _transition(
                repo, job, axis=GenerationJobAxis.PROVIDER, command="RECOVERED_HANDLE",
                owner=TransitionOwner.RECOVERY_COORDINATOR,
                remote=ProviderRemoteLineage(provider_operation_id="op-002"),
            )
        assert (await repo.get_job(job.generation_job_id)).provider_operation_id == "op-001"
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_scheduler_safe_requeue_requires_reconciliation_proof(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, *_ = await _job_fixture(writer)
        job = (await _transition(repo, job, axis=GenerationJobAxis.SCHEDULER, command="CLAIM", owner=TransitionOwner.SCHEDULER)).job
        job = (await _transition(repo, job, axis=GenerationJobAxis.SCHEDULER, command="LEASE_OR_RESTART_RECOVERY", owner=TransitionOwner.RECOVERY_COORDINATOR)).job
        with pytest.raises(GenerationJobTransitionError, match="absence/idempotency proof"):
            await _transition(
                repo, job, axis=GenerationJobAxis.SCHEDULER,
                command="RECOVERY_PROVEN_SAFE_TO_REQUEUE",
                owner=TransitionOwner.RECOVERY_COORDINATOR,
            )
        job = (await _transition(
            repo, job, axis=GenerationJobAxis.SCHEDULER,
            command="RECOVERY_PROVEN_SAFE_TO_REQUEUE",
            owner=TransitionOwner.RECOVERY_COORDINATOR,
            guard=_guard(verified_same_job_idempotency=True),
        )).job
        assert job.scheduler_state is SchedulerState.QUEUED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_cross_axis_target_is_validated_before_commit(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, *_ = await _job_fixture(writer)
        # Build scheduler RUNNING and durable remote handle/polling state legally.
        job = (await _transition(repo, job, axis=GenerationJobAxis.SCHEDULER, command="CLAIM", owner=TransitionOwner.SCHEDULER)).job
        job = (await _transition(repo, job, axis=GenerationJobAxis.SCHEDULER, command="START_WORK", owner=TransitionOwner.SCHEDULER)).job
        job = (await _transition(repo, job, axis=GenerationJobAxis.PROVIDER, command="SUBMIT", owner=TransitionOwner.PROVIDER_ADAPTER, guard=_guard(side_effect_boundary_ready=True))).job
        job = (await _transition(repo, job, axis=GenerationJobAxis.PROVIDER, command="ACCEPTED_HANDLE", owner=TransitionOwner.PROVIDER_ADAPTER, remote=ProviderRemoteLineage(provider_operation_id="op-001"))).job
        job = (await _transition(repo, job, axis=GenerationJobAxis.PROVIDER, command="START_POLL", owner=TransitionOwner.PROVIDER_ADAPTER)).job
        with pytest.raises(GenerationJobTransitionError, match="scheduler cannot terminate"):
            await _transition(
                repo, job, axis=GenerationJobAxis.SCHEDULER,
                command="SCHEDULER_WORK_COMPLETE",
                owner=TransitionOwner.SCHEDULER,
            )
        assert (await repo.get_job(job.generation_job_id)).scheduler_state is SchedulerState.RUNNING
    finally:
        await writer.close()


def test_derived_status_is_projection_only_and_deterministic():
    assert derive_job_status(GenerationJobStateTuple(
        scheduler=SchedulerState.WAITING_RECOVERY,
        provider=ProviderState.AMBIGUOUS_HOLD,
        artifact=ArtifactState.NONE,
        creative=CreativeState.NOT_APPLICABLE,
    )) is DerivedJobStatus.AMBIGUOUS
    assert derive_job_status(GenerationJobStateTuple(
        scheduler=SchedulerState.RUNNING,
        provider=ProviderState.SUBMITTING,
        artifact=ArtifactState.NONE,
        creative=CreativeState.NOT_APPLICABLE,
    )) is DerivedJobStatus.GENERATING
    assert derive_job_status(GenerationJobStateTuple(
        scheduler=SchedulerState.TERMINAL,
        provider=ProviderState.REMOTE_SUCCEEDED,
        artifact=ArtifactState.MISSING,
        creative=CreativeState.APPROVED,
    )) is DerivedJobStatus.MISSING_ARTIFACT
    assert derive_job_status(GenerationJobStateTuple(
        scheduler=SchedulerState.TERMINAL,
        provider=ProviderState.REMOTE_SUCCEEDED,
        artifact=ArtifactState.READY,
        creative=CreativeState.APPROVED,
    )) is DerivedJobStatus.APPROVED


@pytest.mark.asyncio
async def test_restart_reopens_exact_axes_and_append_only_history(tmp_path):
    db_path = tmp_path / "studio.db"
    writer = SQLiteWriteOwner(db_path)
    await writer.start()
    repo, job, *_ = await _job_fixture(writer)
    job = (await _transition(
        repo, job, axis=GenerationJobAxis.SCHEDULER,
        command="EVALUATE_CAPACITY" if False else "EVALUATE_ADMISSION",
        owner=TransitionOwner.SCHEDULER,
    )).job
    await writer.close()

    writer2 = SQLiteWriteOwner(db_path)
    await writer2.start()
    try:
        repo2 = GenerationJobRepository(writer2)
        restored = await repo2.get_job(job.generation_job_id)
        assert restored == job
        history = await repo2.list_transitions(job.generation_job_id)
        assert len(history) == 1
        assert history[0].to_state == SchedulerState.WAITING_CAPACITY.value
    finally:
        await writer2.close()


@pytest.mark.asyncio
async def test_exact_create_replay_after_state_advance_returns_current_job(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, ir, profile, decision, plan = await _job_fixture(writer)
        advanced = (await _transition(
            repo,
            job,
            axis=GenerationJobAxis.SCHEDULER,
            command="EVALUATE_DEPENDENCIES",
            owner=TransitionOwner.SCHEDULER,
        )).job
        replay = await repo.create_job(
            GenerationJobCreateRequest(
                project_id=PROJECT_ID,
                shot_ir_ref=ir.ref,
                routing_decision_ref=decision.ref,
                provider_profile_ref=profile.ref,
                expected_input_fingerprint=ir.hashes.input_fingerprint,
                execution_plan=plan,
                attempt=1,
                submission_attempt_id="submission-attempt-001",
                local_submission_key="local-submit-001",
                idempotency_key="idempotency-001",
                created_at=NOW,
                actor_ref="studio:imp052-test",
                reason="create canonical generation job fixture",
                correlation_id="run:imp052",
                evidence_refs=("evidence:imp052-create",),
            )
        )
        assert replay == advanced
        assert replay.revision == 1
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_remote_lineage_cannot_be_injected_by_non_provider_axis(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, *_ = await _job_fixture(writer)
        with pytest.raises(GenerationJobTransitionError, match="remote provider lineage"):
            await _transition(
                repo,
                job,
                axis=GenerationJobAxis.SCHEDULER,
                command="EVALUATE_DEPENDENCIES",
                owner=TransitionOwner.SCHEDULER,
                remote=ProviderRemoteLineage(provider_operation_id="op-injected"),
            )
        assert await repo.get_job(job.generation_job_id) == job
        assert await repo.list_transitions(job.generation_job_id) == []
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_transition_history_is_database_append_only(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, job, *_ = await _job_fixture(writer)
        result = await _transition(
            repo,
            job,
            axis=GenerationJobAxis.SCHEDULER,
            command="EVALUATE_DEPENDENCIES",
            owner=TransitionOwner.SCHEDULER,
        )

        async def update_history(tx):
            await tx.execute(
                "UPDATE studio_generation_job_transition SET reason='tampered' WHERE transition_id=?",
                (result.transition.transition_id,),
            )

        async def delete_history(tx):
            await tx.execute(
                "DELETE FROM studio_generation_job_transition WHERE transition_id=?",
                (result.transition.transition_id,),
            )

        with pytest.raises(aiosqlite.IntegrityError, match="append-only"):
            await writer.execute(update_history)
        with pytest.raises(aiosqlite.IntegrityError, match="append-only"):
            await writer.execute(delete_history)
        assert await repo.list_transitions(job.generation_job_id) == [result.transition]
    finally:
        await writer.close()
