"""IMP-103 offline 300-shot scheduling/admission scale benchmark.

This is a local synthetic benchmark: it creates 300 distinct canonical shot identities
and GenerationJobs, but never submits work to a real provider.
"""

from __future__ import annotations

import asyncio
import json
import tracemalloc
from collections import Counter
from datetime import timedelta
from pathlib import Path
from time import perf_counter

import pytest

from agent.studio import (
    CountRange,
    DurationBudget,
    GenerationJobCreateRequest,
    GenerationJobRepository,
    LifecycleState,
    ProviderAdapterPrepareRequest,
    ProviderAdapterPreflight,
    ProviderCapabilityRoutingRepository,
    ProviderExecutionMode,
    ProviderRequirement,
    ProviderRouteRequest,
    RequirementOperator,
    RuntimeRangeSeconds,
    SchedulerAdmissionPolicy,
    SchedulerNodeRegistration,
    SchedulerRepository,
    ShotBudget,
    ShotEligibilityRequest,
    ShotExpansionRequest,
    ShotPlanningRepository,
    ShotRealizationRepository,
    StructureProfile,
    VersionId,
    VersionRef,
    scheduler_model_capacity_key,
)
from agent.studio.persistence import SQLiteReadRepository, SQLiteWriteOwner, WriteQueueFull
from tests.unit.test_studio_directing import NOW, PROJECT_ID, _create_chain, _seed_version
from tests.unit.test_studio_production_compiler import (
    _compile_request,
    _rule as _compiler_rule,
    _rule_provenance as _compiler_rule_provenance,
)
from tests.unit.test_studio_provider_adapter import _adapter_profile, _runtime_refs
from tests.unit.test_studio_provider_routing import (
    _profile_provenance,
    _request as _routing_request,
    _rule as _routing_rule,
    _rule_provenance as _routing_rule_provenance,
)
from tests.unit.test_studio_shot_planning import (
    DURATION_REF,
    STRUCTURE_REF,
    _budget,
    _candidates,
    _coverage,
    _duration,
    _planning_prov,
    _request,
    _structure,
)
from tests.unit.test_studio_shot_realization import (
    ENTITY_REF,
    RULE_REF,
    _approved_reference_and_resolution,
    _full_spec,
    _motion,
    _provenance,
    _static,
)


EVIDENCE = ("evidence:imp103-scale-benchmark",)
SHOT_COUNT = 300
SCENE_SECONDS = SHOT_COUNT * 10
WRITER_CAPACITY = 64
QUEUE_PROBE_CAPACITY = 32
ADMISSION_CAP = 4


class _ObservedWriteOwner(SQLiteWriteOwner):
    """Observe actual bounded-queue depth without changing writer behavior."""

    def __init__(self, db_path: str | Path, *, max_queue_size: int) -> None:
        super().__init__(db_path, max_queue_size=max_queue_size)
        self.max_observed_queue_size = 0

    def submit(self, operation):
        future = super().submit(operation)
        self.max_observed_queue_size = max(
            self.max_observed_queue_size,
            self.queue_size,
        )
        return future


def _sqlite_footprint(db_path: Path) -> int:
    sidecars = (
        db_path,
        Path(f"{db_path}-wal"),
        Path(f"{db_path}-shm"),
    )
    return sum(path.stat().st_size for path in sidecars if path.exists())


async def _bounded_queue_probe(tmp_path: Path) -> dict:
    """Force queue saturation, retry rejected commands, and prove exact persistence."""
    db_path = tmp_path / "imp103-bounded-queue.db"
    owner = _ObservedWriteOwner(db_path, max_queue_size=QUEUE_PROBE_CAPACITY)
    release = asyncio.Event()
    started = asyncio.Event()
    accepted: dict[int, asyncio.Future] = {}
    rejected: list[int] = []
    started_at = perf_counter()

    def insert_row(row_id: int):
        async def command(tx):
            await tx.execute(
                "INSERT INTO imp103_queue_probe(row_id, payload) VALUES (?, ?)",
                (row_id, f"payload-{row_id:03d}"),
            )

        return command

    try:
        await owner.start()

        async def create_probe_table(tx):
            await tx.execute(
                "CREATE TABLE imp103_queue_probe ("
                "row_id INTEGER PRIMARY KEY, payload TEXT NOT NULL)"
            )

        await owner.execute(create_probe_table)

        async def hold_writer(_tx):
            started.set()
            await release.wait()
            return "released"

        blocker = owner.submit(hold_writer)
        await started.wait()

        for row_id in range(SHOT_COUNT):
            try:
                accepted[row_id] = owner.submit(insert_row(row_id))
            except WriteQueueFull:
                rejected.append(row_id)

        peak_while_blocked = owner.max_observed_queue_size
        assert len(accepted) == QUEUE_PROBE_CAPACITY
        assert len(rejected) == SHOT_COUNT - QUEUE_PROBE_CAPACITY
        assert owner.queue_size == QUEUE_PROBE_CAPACITY
        assert peak_while_blocked == QUEUE_PROBE_CAPACITY

        release.set()
        assert await blocker == "released"
        await asyncio.gather(*accepted.values())

        for row_id in rejected:
            await owner.execute(insert_row(row_id))

        reader = SQLiteReadRepository(owner.db_path)
        counts = await reader.fetchone(
            "SELECT COUNT(*) AS total, COUNT(DISTINCT row_id) AS unique_rows "
            "FROM imp103_queue_probe"
        )
        assert counts is not None
        assert int(counts["total"]) == SHOT_COUNT
        assert int(counts["unique_rows"]) == SHOT_COUNT
        assert owner.queue_size == 0

        elapsed = perf_counter() - started_at
        await owner.close()
        return {
            "capacity": QUEUE_PROBE_CAPACITY,
            "peak_depth": peak_while_blocked,
            "accepted_before_backpressure": len(accepted),
            "rejected_and_retried": len(rejected),
            "rows_persisted": int(counts["total"]),
            "unique_rows": int(counts["unique_rows"]),
            "elapsed_seconds": round(elapsed, 4),
            "db_bytes": _sqlite_footprint(db_path),
        }
    finally:
        release.set()
        if owner.running:
            await owner.close()


def _fairness_probe() -> dict:
    """Run the production ordering function over 300 ready shots across 3 projects."""
    projects = ("project:a", "project:b", "project:c")
    ready_since = NOW.isoformat()
    rows = [
        {
            "generation_job_id": f"job:{project.split(':')[1]}-{index:03d}",
            "priority_class": 10,
            "ready_since": ready_since,
            "project_id": project,
        }
        for index in range(100)
        for project in projects
    ]
    ordered = SchedulerRepository._fair_order_rows(rows, {10: "project:a"})
    ordered_projects = [
        f"project:{item.root.split(':')[1].split('-')[0]}"
        for item in ordered
    ]
    counts = Counter(ordered_projects)
    assert len(ordered) == SHOT_COUNT
    assert counts == Counter({project: 100 for project in projects})
    assert ordered_projects[:9] == [
        "project:b",
        "project:c",
        "project:a",
    ] * 3

    gaps: list[int] = []
    for project in projects:
        positions = [
            index for index, actual in enumerate(ordered_projects)
            if actual == project
        ]
        gaps.extend(right - left for left, right in zip(positions, positions[1:]))
    max_interarrival_gap = max(gaps)
    assert max_interarrival_gap == len(projects)
    return {
        "shots": len(ordered),
        "projects": len(projects),
        "shots_per_project": dict(counts),
        "max_interarrival_gap_positions": max_interarrival_gap,
        "starved_projects": 0,
    }


@pytest.mark.asyncio
async def test_imp103_300_shot_scale_benchmark(tmp_path):
    """Measure canonical 300-shot setup, bounded admission/claims, and persistence."""
    db_path = tmp_path / "imp103-300-shot-scale.db"
    owner = _ObservedWriteOwner(db_path, max_queue_size=WRITER_CAPACITY)
    setup_started = perf_counter()
    print("IMP103_PROGRESS=setup_start shots=300", flush=True)
    phase_seconds: dict[str, float] = {}
    jobs = []
    claimed_ids: set[str] = set()

    try:
        await owner.start()
        (
            _directing_repo,
            trace_ref,
            _unused_profile,
            _unused_scene,
            _unused_entity,
            directing,
            _unused_context,
            blocking,
            cine,
        ) = await _create_chain(owner)
        versions = _directing_repo.versions

        structure_base = _structure()
        duration_base = _duration()
        structure_ref = VersionRef(
            logical_id=STRUCTURE_REF.logical_id,
            version_id=VersionId("structure-v300"),
        )
        duration_ref = VersionRef(
            logical_id=DURATION_REF.logical_id,
            version_id=VersionId("duration-v300"),
        )
        structure_payload = structure_base.model_dump(mode="python")
        structure_payload.update(
            {
                "version_id": structure_ref.version_id,
                "target_runtime_seconds": SCENE_SECONDS,
                "runtime_range_seconds": RuntimeRangeSeconds(
                    minimum=SCENE_SECONDS,
                    maximum=SCENE_SECONDS,
                ),
            }
        )
        structure_long = StructureProfile.model_validate(structure_payload)
        duration_payload = duration_base.model_dump(mode="python")
        duration_payload.update(
            {
                "version_id": duration_ref.version_id,
                "structure_profile_ref": structure_ref,
                "total_seconds": SCENE_SECONDS,
                "allocations": tuple(
                    item.model_copy(update={"seconds": SCENE_SECONDS})
                    for item in duration_base.allocations
                ),
            }
        )
        duration_long = DurationBudget.model_validate(duration_payload)
        await _seed_version(
            versions,
            structure_ref,
            structure_long.model_dump(mode="json"),
        )
        await _seed_version(
            versions,
            duration_ref,
            duration_long.model_dump(mode="json"),
        )
        await _seed_version(
            versions,
            RULE_REF,
            {"fixture": "shot-eligibility-rule-v1"},
        )

        planning = ShotPlanningRepository(owner)
        coverage_base = _coverage(blocking.ref, cine.ref)
        coverage_payload = coverage_base.model_dump(mode="python")
        coverage_payload.update(
            {
                "version_id": VersionId("coverage-v300"),
                "duration_budget_ref": duration_ref,
                "requirements": tuple(
                    item.model_copy(update={"maximum_shots": SHOT_COUNT // 2})
                    for item in coverage_base.requirements
                ),
            }
        )
        coverage = type(coverage_base).model_validate(coverage_payload)
        await planning.create_coverage_strategy(
            value=coverage,
            provenance=_planning_prov(
                coverage,
                "create deterministic 300-shot scale coverage",
            ),
            created_at=NOW,
        )

        budget_base = _budget(
            coverage.ref,
            version="shot-budget-v300",
        )
        budget_payload = budget_base.model_dump(mode="python")
        budget_payload.update(
            {
                "structure_profile_ref": structure_ref,
                "duration_budget_ref": duration_ref,
                "shot_count_range": CountRange(
                    minimum=SHOT_COUNT,
                    maximum=SHOT_COUNT,
                ),
                "shot_duration_range_seconds": RuntimeRangeSeconds(
                    minimum=10,
                    maximum=10,
                ),
                "scene_duration_seconds": SCENE_SECONDS,
                "rationale": "300 distinct ten-second shots form the deterministic scale workload.",
            }
        )
        budget = ShotBudget.model_validate(budget_payload)
        await planning.create_shot_budget(
            value=budget,
            provenance=_planning_prov(
                budget,
                "create deterministic 300-shot scale budget",
            ),
            created_at=NOW,
        )

        templates = {item.coverage_key: item for item in _candidates()}
        candidates = []
        for index in range(SHOT_COUNT):
            key = "action" if index % 2 == 0 else "reaction"
            template = templates[key]
            ordinal = index + 1
            candidates.append(
                template.model_copy(
                    update={
                        "shot_key": f"scale-shot-{ordinal:03d}",
                        "duration_seconds": 10,
                        "dramatic_function": (
                            f"{template.dramatic_function} scale variation {ordinal:03d}"
                        ),
                        "basic_shot_intent": (
                            f"{template.basic_shot_intent} scale variation {ordinal:03d}"
                        ),
                        "reason_for_exist": (
                            f"{template.reason_for_exist} scale item {ordinal:03d}"
                        ),
                        "subject_refs": (ENTITY_REF,),
                    }
                )
            )

        request_base = _request(
            trace_ref,
            directing.ref,
            blocking.ref,
            cine.ref,
            candidates=tuple(candidates),
        )
        request_payload = request_base.model_dump(mode="python")
        request_payload.update(
            {
                "duration_budget_ref": duration_ref,
                "coverage_strategy_ref": coverage.ref,
                "shot_budget_ref": budget.ref,
            }
        )
        request = ShotExpansionRequest.model_validate(request_payload)

        planning_started = perf_counter()
        print("IMP103_PROGRESS=shot_expansion_start", flush=True)
        expansion = await planning.expand_scene(
            request=request,
            shot_item_version=VersionId("shot-v300"),
            shot_trace_version=VersionId("shot-trace-v300"),
            manifest_version=VersionId("manifest-v300"),
            actor_ref="studio:imp103-benchmark",
            reason="expand deterministic 300-shot benchmark workload",
            recorded_at=NOW,
            source_refs=EVIDENCE,
            correlation_id="run:imp103-expand",
        )
        phase_seconds["planning_and_expansion"] = perf_counter() - planning_started
        assert len(expansion.shot_items) == SHOT_COUNT
        assert len({item.value.shot_id.root for item in expansion.shot_items}) == SHOT_COUNT
        print("IMP103_PROGRESS=shot_expansion_complete shots=300", flush=True)

        asset, resolution = await _approved_reference_and_resolution(owner)
        realization = ShotRealizationRepository(owner)
        realized: list[tuple[object, object, object, object]] = []
        realization_started = perf_counter()
        print("IMP103_PROGRESS=realization_start", flush=True)
        for index, item_artifact in enumerate(expansion.shot_items, start=1):
            shot = item_artifact.value
            eligibility_request = ShotEligibilityRequest(
                project_id=PROJECT_ID,
                shot_ref=item_artifact.ref,
                shot_list_manifest_ref=expansion.manifest.ref,
                state_snapshot_ref=blocking.state_snapshot_ref,
                reference_resolution=resolution,
                required_reference_entity_refs=(ENTITY_REF,),
                rule_version=RULE_REF,
            )
            gate_artifact = await realization.evaluate_eligibility(
                request=eligibility_request,
                gate_version=VersionId("eligibility-v300"),
                actor_ref="studio:imp103-benchmark",
                reason="evaluate exact synthetic shot eligibility",
                recorded_at=NOW,
                source_refs=EVIDENCE,
                correlation_id=f"run:imp103-gate-{index:03d}",
            )
            gate = gate_artifact.value
            spec = _full_spec(gate, shot)
            await realization.create_full_shot_spec(
                value=spec,
                provenance=_provenance(spec, "create IMP-103 benchmark FullShotSpec"),
                created_at=NOW,
            )
            static = _static(spec, shot)
            await realization.create_static_keyframe_spec(
                value=static,
                provenance=_provenance(static, "create IMP-103 benchmark StaticKeyframeSpec"),
                created_at=NOW,
            )
            motion = _motion(spec, static, shot)
            await realization.create_motion_delta_spec(
                value=motion,
                provenance=_provenance(motion, "create IMP-103 benchmark MotionDeltaSpec"),
                created_at=NOW,
            )
            realized.append((shot, spec, static, motion))
        phase_seconds["eligibility_and_realization"] = perf_counter() - realization_started
        print("IMP103_PROGRESS=realization_complete shots=300", flush=True)

        compiler = __import__(
            "agent.studio.production_compiler",
            fromlist=["ProductionCompilerRepository"],
        ).ProductionCompilerRepository(owner)
        compiler_rule = _compiler_rule()
        await compiler.create_rule_set(
            rule_set=compiler_rule,
            provenance=_compiler_rule_provenance(
                "create deterministic IMP-103 benchmark compiler rule"
            ),
            created_at=NOW,
        )
        compiler_started = perf_counter()
        print("IMP103_PROGRESS=compiler_start", flush=True)
        shot_irs = []
        for index, (_shot, spec, static, motion) in enumerate(realized, start=1):
            result = await compiler.compile_initial(
                request=_compile_request(spec, static, motion, compiler_rule),
                ir_version=VersionId("ir-v300"),
                actor_ref="studio:imp103-benchmark",
                reason="compile distinct synthetic scale ShotIR",
                recorded_at=NOW,
                source_refs=EVIDENCE,
                correlation_id=f"run:imp103-compile-{index:03d}",
            )
            shot_irs.append(result.artifact.value)
            if index % 25 == 0 or index == SHOT_COUNT:
                print(f"IMP103_PROGRESS=compiler completed={index}/{SHOT_COUNT}", flush=True)
        phase_seconds["compiler"] = perf_counter() - compiler_started
        print("IMP103_PROGRESS=compiler_complete shots=300", flush=True)
        assert len({item.shot_ref.logical_id.root for item in shot_irs}) == SHOT_COUNT

        mode = ProviderExecutionMode.FIRST_FRAME_TO_VIDEO
        profile = _adapter_profile("flow", mode=mode, resolution="720p")
        routing = ProviderCapabilityRoutingRepository(owner)
        await routing.create_profile(
            profile=profile,
            provenance=_profile_provenance(
                profile,
                "deterministic synthetic profile for offline scale benchmark",
            ),
            created_at=NOW,
        )
        routing_rule = _routing_rule()
        await routing.create_routing_rule(
            rule=routing_rule,
            provenance=_routing_rule_provenance(routing_rule),
            created_at=NOW,
        )
        preflight = ProviderAdapterPreflight(owner)
        job_repo = GenerationJobRepository(owner)
        jobs_started = perf_counter()
        print("IMP103_PROGRESS=routing_and_job_creation_start", flush=True)
        for index, ir in enumerate(shot_irs, start=1):
            base_route_request = _routing_request(ir, routing_rule, (profile,))
            requirements = (
                *base_route_request.requirements,
                ProviderRequirement(
                    key="execution.mode",
                    operator=RequirementOperator.CONTAINS,
                    expected_value_json=json.dumps(mode.value),
                    source_refs=(ir.ref,),
                ),
                ProviderRequirement(
                    key="output.resolution",
                    operator=RequirementOperator.CONTAINS,
                    expected_value_json=json.dumps("720p"),
                    source_refs=(ir.ref,),
                ),
            )
            route_request = ProviderRouteRequest.model_validate(
                {
                    **base_route_request.model_dump(mode="python"),
                    "requirements": requirements,
                    "run_correlation_id": f"run:imp103-route-{index:03d}",
                }
            )
            decision = await routing.route_initial(
                request=route_request,
                decision_version=VersionId("route-v300"),
                actor_ref="studio:imp103-benchmark",
                reason="route deterministic synthetic benchmark shot",
                recorded_at=NOW,
                source_refs=EVIDENCE,
            )
            plan = await preflight.prepare(
                ProviderAdapterPrepareRequest(
                    project_id=PROJECT_ID,
                    shot_ir_ref=ir.ref,
                    routing_decision_ref=decision.ref,
                    mode=mode,
                    runtime_references=_runtime_refs(ir),
                    execution_as_of=NOW,
                )
            )
            job = await job_repo.create_job(
                GenerationJobCreateRequest(
                    project_id=PROJECT_ID,
                    shot_ir_ref=ir.ref,
                    routing_decision_ref=decision.ref,
                    provider_profile_ref=profile.ref,
                    expected_input_fingerprint=ir.hashes.input_fingerprint,
                    execution_plan=plan,
                    attempt=1,
                    submission_attempt_id=f"imp103-submission-{index:03d}",
                    local_submission_key=f"imp103-local-submit-{index:03d}",
                    idempotency_key=f"imp103-idempotency-{index:03d}",
                    created_at=NOW,
                    actor_ref="studio:imp103-benchmark",
                    reason="create canonical synthetic GenerationJob",
                    correlation_id=f"run:imp103-job-{index:03d}",
                    evidence_refs=EVIDENCE,
                )
            )
            jobs.append(job)
            if index % 25 == 0 or index == SHOT_COUNT:
                print(f"IMP103_PROGRESS=jobs_created={index}/{SHOT_COUNT}", flush=True)
        phase_seconds["routing_preflight_and_job_creation"] = perf_counter() - jobs_started
        print("IMP103_PROGRESS=jobs_complete shots=300", flush=True)
        assert len({job.generation_job_id.root for job in jobs}) == SHOT_COUNT
        assert len({job.shot_id.root for job in jobs}) == SHOT_COUNT

        scheduler = SchedulerRepository(owner)
        tracemalloc.start()
        scheduler_started = perf_counter()
        print("IMP103_PROGRESS=scheduler_queue_setup_start", flush=True)
        for scheduler_index, job in enumerate(jobs, start=1):
            await scheduler.register_node(
                SchedulerNodeRegistration(
                    generation_job_id=job.generation_job_id,
                    priority_class=10,
                    operation_key="video.generate",
                    local_resource_key="remote.flow",
                    estimated_cost_microunits=100,
                    evidence_refs=EVIDENCE,
                ),
                created_at=NOW,
            )
            await scheduler.evaluate_readiness(
                job_id=job.generation_job_id,
                actor_ref="scheduler:imp103-benchmark",
                reason="evaluate no-dependency readiness for scale workload",
                correlation_id=f"run:imp103-ready-{job.generation_job_id.root.rsplit(':', 1)[-1]}",
                recorded_at=NOW,
                evidence_refs=EVIDENCE,
            )
            if scheduler_index % 25 == 0 or scheduler_index == SHOT_COUNT:
                print(f"IMP103_PROGRESS=scheduler_nodes_ready={scheduler_index}/{SHOT_COUNT}", flush=True)
        phase_seconds["scheduler_queue_setup"] = perf_counter() - scheduler_started
        print("IMP103_PROGRESS=scheduler_queue_setup_complete nodes=300", flush=True)
        setup_seconds = perf_counter() - setup_started
        _, scheduler_setup_peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.reset_peak()

        policy = SchedulerAdmissionPolicy(
            policy_id="scheduler-policy:imp103-v1",
            global_limit=ADMISSION_CAP,
            provider_limits={jobs[0].provider_key: ADMISSION_CAP},
            model_limits={scheduler_model_capacity_key(jobs[0]): ADMISSION_CAP},
            operation_limits={"video.generate": ADMISSION_CAP},
            local_resource_limits={"remote.flow": ADMISSION_CAP},
            budget_limit_microunits=100_000,
            budget_spent_microunits=0,
            evidence_refs=("evidence:imp103-admission-policy",),
        )
        claim_started = perf_counter()
        print("IMP103_PROGRESS=scheduler_claim_start", flush=True)
        concurrent_time = NOW + timedelta(seconds=1)

        async def concurrent_claim(worker_index: int):
            return await scheduler.claim_next(
                policy=policy,
                worker_id=f"worker-{worker_index:02d}",
                lease_ttl_seconds=3600,
                actor_ref="scheduler:imp103-benchmark",
                reason="concurrent hierarchical admission probe",
                correlation_id=f"run:imp103-concurrent-claim-{worker_index:02d}",
                recorded_at=concurrent_time,
                evidence_refs=EVIDENCE,
            )

        concurrent_results = await asyncio.gather(
            *(concurrent_claim(index) for index in range(8))
        )
        concurrent_claims = [item for item in concurrent_results if item is not None]
        assert len(concurrent_claims) == ADMISSION_CAP
        for claim in concurrent_claims:
            claimed_ids.add(claim.job.generation_job_id.root)

        reader = SQLiteReadRepository(owner.db_path)
        active_during_probe = await reader.fetchone(
            "SELECT COUNT(*) AS n FROM studio_scheduler_lease "
            "WHERE state='ACTIVE' AND expires_at>?",
            (concurrent_time.isoformat(),),
        )
        assert active_during_probe is not None
        assert int(active_during_probe["n"]) == ADMISSION_CAP

        for claim in concurrent_claims:
            await scheduler.release_lease(
                job_id=claim.job.generation_job_id,
                lease_token=claim.lease.lease_token,
                worker_id=claim.lease.worker_id,
                actor_ref="scheduler:imp103-benchmark",
                reason="release benchmark claim without provider side effect",
                correlation_id=f"run:imp103-release-{claim.job.generation_job_id.root.rsplit(':', 1)[-1]}",
                recorded_at=NOW + timedelta(seconds=2),
                evidence_refs=EVIDENCE,
            )

        clock_seconds = 3
        while len(claimed_ids) < SHOT_COUNT:
            claim = await scheduler.claim_next(
                policy=policy,
                worker_id=f"worker-{len(claimed_ids) % ADMISSION_CAP:02d}",
                lease_ttl_seconds=3600,
                actor_ref="scheduler:imp103-benchmark",
                reason="drain deterministic scale queue",
                correlation_id=f"run:imp103-drain-{len(claimed_ids):03d}",
                recorded_at=NOW + timedelta(seconds=clock_seconds),
                evidence_refs=EVIDENCE,
            )
            assert claim is not None, "a queued shot was starved or lost"
            job_id = claim.job.generation_job_id.root
            assert job_id not in claimed_ids, "scheduler returned a duplicate claim"
            claimed_ids.add(job_id)
            if len(claimed_ids) % 25 == 0:
                print(f"IMP103_PROGRESS=claims_completed={len(claimed_ids)}/{SHOT_COUNT}", flush=True)
            await scheduler.release_lease(
                job_id=claim.job.generation_job_id,
                lease_token=claim.lease.lease_token,
                worker_id=claim.lease.worker_id,
                actor_ref="scheduler:imp103-benchmark",
                reason="release benchmark claim without provider side effect",
                correlation_id=f"run:imp103-release-{len(claimed_ids):03d}",
                recorded_at=NOW + timedelta(seconds=clock_seconds + 1),
                evidence_refs=EVIDENCE,
            )
            clock_seconds += 2

        claim_seconds = perf_counter() - claim_started
        _, scheduler_claim_peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print("IMP103_PROGRESS=scheduler_claims_complete claims=300", flush=True)

        job_summary = await reader.fetchone(
            "SELECT COUNT(*) AS total_jobs, "
            "COUNT(DISTINCT generation_job_id) AS unique_jobs, "
            "COUNT(DISTINCT shot_id) AS unique_shots, "
            "SUM(CASE WHEN scheduler_state='QUEUED' THEN 1 ELSE 0 END) AS queued_jobs, "
            "SUM(CASE WHEN scheduler_state='CLAIMED' THEN 1 ELSE 0 END) AS claimed_jobs "
            "FROM studio_generation_job"
        )
        node_summary = await reader.fetchone(
            "SELECT COUNT(*) AS n FROM studio_scheduler_node"
        )
        checkpoint_summary = await reader.fetchone(
            "SELECT COUNT(*) AS n FROM studio_scheduler_checkpoint"
        )
        admission_summary = await reader.fetchone(
            "SELECT COUNT(*) AS n FROM studio_scheduler_admission"
        )
        lease_summary = await reader.fetchone(
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN state='ACTIVE' THEN 1 ELSE 0 END) AS active "
            "FROM studio_scheduler_lease"
        )
        lease_history_summary = await reader.fetchone(
            "SELECT COUNT(*) AS n FROM studio_scheduler_lease_history"
        )
        assert job_summary is not None
        assert node_summary is not None
        assert checkpoint_summary is not None
        assert admission_summary is not None
        assert lease_summary is not None
        assert lease_history_summary is not None
        assert int(job_summary["total_jobs"]) == SHOT_COUNT
        assert int(job_summary["unique_jobs"]) == SHOT_COUNT
        assert int(job_summary["unique_shots"]) == SHOT_COUNT
        assert int(job_summary["queued_jobs"]) == 0
        assert int(job_summary["claimed_jobs"]) == SHOT_COUNT
        assert int(node_summary["n"]) == SHOT_COUNT
        assert int(checkpoint_summary["n"]) == SHOT_COUNT
        assert int(admission_summary["n"]) >= SHOT_COUNT
        assert int(lease_summary["total"]) == SHOT_COUNT
        assert int(lease_summary["active"] or 0) == 0
        assert int(lease_history_summary["n"]) == SHOT_COUNT * 2
        assert len(claimed_ids) == SHOT_COUNT
        assert owner.max_observed_queue_size <= WRITER_CAPACITY

        fairness = _fairness_probe()
        await owner.close()
        main_db_bytes = _sqlite_footprint(db_path)
        print("IMP103_PROGRESS=bounded_queue_probe_start", flush=True)
        queue_metrics = await _bounded_queue_probe(tmp_path)
        print("IMP103_PROGRESS=bounded_queue_probe_complete rows=300", flush=True)

        results = {
            "task": "IMP-103",
            "mode": "offline_synthetic_no_provider_calls",
            "shots": SHOT_COUNT,
            "distinct_shot_ids": int(job_summary["unique_shots"]),
            "distinct_generation_jobs": int(job_summary["unique_jobs"]),
            "phase_seconds": {
                key: round(value, 4) for key, value in phase_seconds.items()
            },
            "total_setup_seconds": round(setup_seconds, 4),
            "setup_shots_per_second": round(SHOT_COUNT / setup_seconds, 3),
            "claim_seconds": round(claim_seconds, 4),
            "claims_per_second": round(SHOT_COUNT / claim_seconds, 3),
            "tracemalloc_scheduler_setup_peak_bytes": scheduler_setup_peak_bytes,
            "tracemalloc_scheduler_claim_peak_bytes": scheduler_claim_peak_bytes,
            "writer_queue": {
                "capacity": WRITER_CAPACITY,
                "peak_depth": owner.max_observed_queue_size,
            },
            "hierarchical_admission": {
                "global_provider_model_operation_resource_cap": ADMISSION_CAP,
                "concurrent_claims_requested": 8,
                "concurrent_claims_admitted": len(concurrent_claims),
                "max_active_leases_during_probe": int(active_during_probe["n"]),
            },
            "persistence": {
                "generation_jobs": int(job_summary["total_jobs"]),
                "scheduler_nodes": int(node_summary["n"]),
                "readiness_checkpoints": int(checkpoint_summary["n"]),
                "admission_decisions": int(admission_summary["n"]),
                "lease_rows": int(lease_summary["total"]),
                "lease_history_rows": int(lease_history_summary["n"]),
                "queued_after_claims": int(job_summary["queued_jobs"]),
                "active_leases_after_release": int(lease_summary["active"] or 0),
                "sqlite_footprint_bytes": main_db_bytes,
            },
            "fairness": fairness,
            "bounded_queue_stress": queue_metrics,
        }
        print("IMP103_BENCHMARK_RESULT=" + json.dumps(results, sort_keys=True), flush=True)
        assert results["setup_shots_per_second"] > 0
        assert results["claims_per_second"] > 0
        assert queue_metrics["rows_persisted"] == SHOT_COUNT
        assert queue_metrics["peak_depth"] == QUEUE_PROBE_CAPACITY
    finally:
        if owner.running:
            await owner.close()
        if tracemalloc.is_tracing():
            tracemalloc.stop()
