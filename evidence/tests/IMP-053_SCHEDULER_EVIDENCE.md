# IMP-053 Scheduler / Queue / DAG / Leases / Admission Evidence

## Scope
- Persistence migration v7 on the shared SQLiteWriteOwner.
- GenerationJob.scheduler_state remains the only canonical scheduler-state authority; no competing scheduler status store.
- Immutable scheduler node metadata and immutable dependency DAG edges.
- Durable readiness checkpoints/history, admission evidence, lease/current + lease history and fairness cursor.
- Hierarchical admission: global + provider + model + operation + local-resource + dependency readiness + budget.
- Ordering: priority class -> durable project fairness -> oldest-ready.
- Work authorization requires both legal GenerationJob scheduler transitions and a matching unexpired active lease.
- Restart semantics expire stale leases and hand CLAIMED/RUNNING work to recovery; no blind reset/requeue.

## Targeted
```text
Scheduler targeted: 13/13 PASS
GenerationJob affected: 20/20 PASS
Persistence/schema-upgrade compatibility: 13/13 PASS
```

Scheduler targeted coverage proves:
- migration v7 without duplicate generic/scheduler status authority;
- immutable node replay and DAG cycle/topology rejection;
- dependency wait/release through legal GenerationJob transitions;
- missing-cap fail-closed admission and capacity requeue;
- budget gate without identity mutation;
- lease-required CLAIMED -> RUNNING transition;
- global backpressure and serialized concurrent claims without oversubscription;
- project fairness/no-starvation ordering;
- restart lease expiry requiring recovery, not blind requeue;
- durable readiness recomputation after restart;
- blocked dependency never receives lease/execution.

## Broader valid Windows regression
Previously completed broader modules: `466/466 PASS`.
Production compiler lane: `14/14 PASS`.
Missing-only resume lane was completed without rerunning already-PASS modules:

```text
profile_resolver: 15 PASS
provider_adapter: 18 PASS
provider_routing: 13 PASS
reference: 13 PASS
research_story_material: 13 PASS
screenplay_realization: 12 PASS
shot_planning: 17 PASS
shot_realization: 15 PASS
state_continuity: 16 PASS
story_core: 17 PASS
story_intake + story_quality: 26 PASS
structure_planning + topic_domain + versioning: 36 PASS
Missing-only aggregate: 211/211 PASS
Broader aggregate: 691/691 PASS
```

`shot_realization` first produced JUnit `15/15 PASS` but pytest exited non-zero only during Windows temp-directory cleanup (`PermissionError` on `pytest-current`). The cleanup-only runner issue was isolated; final clean-exit proof was obtained with repo-local `--basetemp` in four non-overlapping batches: `4 + 4 + 4 + 3 = 15/15 PASS`.

## Static / authority verification
- Frozen Master guard: PASS.
- Frozen semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- `compileall`: PASS.
- `git diff --check`: PASS.
- New scheduler/test files trailing-whitespace scan: NONE.
- Scheduler provider/runtime/network import leakage scan: NONE.
- TODO/FIXME/NotImplemented scan in IMP-053 touched implementation/tests: NONE.

## Exact review result
- GenerationJob.scheduler_state remains canonical; SchedulerRepository stores coordination/evidence only.
- Node metadata and DAG edges are immutable and replay-conflict protected.
- DAG readiness is recomputed from exact GenerationJob axes and persisted with CAS/history.
- Admission is fail-closed when any required capacity limit is missing and is evidence-backed.
- Active usage and lease reservation are serialized inside the single-writer transaction, preventing oversubscription races.
- START_WORK requires an active, matching, unexpired lease and a legal GenerationJob CLAIMED state.
- Lease expiry on CLAIMED/RUNNING does not reset paid/possibly-paid work; startup reports those jobs for RecoveryCoordinator ownership.
- Fair ordering is priority -> project round-robin -> oldest-ready and uses durable cursor state.
- Provider/network execution remains outside scheduler DB transactions.

RESULT = IMP-053 LOCAL VERIFIED

## Post-merge main verification - 2026-10-05
- Feature PR #60 merged from exact feature head `fb50900e0faff6693427afe804b6f38c6f7b7e69`.
- Main merge SHA: `ad0ab54d86c9c90817415e1e60defbf357a5c807`.
- PR CI run `37340246714`: SUCCESS on Python 3.10 / 3.13; frozen Master baseline verification succeeded on both jobs.
- Local main was fast-forwarded to exact merge SHA; local frozen Master guard PASS with semantic SHA `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- A local post-merge scheduler targeted run was interrupted by the FileMCP bridge and produced no JUnit/result marker; it is explicitly not counted as PASS evidence.
- Main push workflow `37340889716`: SUCCESS on exact merge SHA, Python 3.10 / 3.13, including frozen Master verification and full unit-test steps.

RESULT = IMP-053 FEATURE MAIN VERIFIED
