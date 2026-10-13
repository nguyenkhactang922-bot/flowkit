# IMP-102 Failure / Recovery Fault Injection Evidence

## Authority and acceptance
- Task: `IMP-102 Failure / Recovery Fault Injection`.
- Authoritative task definition: `tasks/IMPLEMENTATION_TASK_DECOMPOSITION_V1.md`.
- Goal: crash/restart/provider ambiguity/artifact failure proof.
- Acceptance: no blind duplicate submit; all outcomes reconciled deterministically.
- Frozen authority: `docs/design/canonical/MASTER_AI_FILM_STUDIO_FINAL_IMPLEMENTATION_BASELINE_V1_FREEZE_MANIFEST.md`, sections 69-71 of the frozen Master. Semantic SHA-256 after CRLF-to-LF normalization: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.

## Existing verified evidence retained
- IMP-052 GenerationJob four-axis state machine and generic reopen/history tests.
- IMP-053 scheduler lease expiry and recovery-required tests.
- IMP-054 pre-dispatch proof, ambiguous submit hold, same-handle recovery, proven-absent/idempotency proof and append-only recovery event tests.
- Provider-adapter tests prove timeout after possible send is ambiguous/non-retry-safe and reconcile-without-handle does not submit.
- IMP-055 artifact crash windows, stale-result, missing/corrupt bytes and orphan quarantine tests.
- IMP-100 provider-neutral contract regression evidence.
- These prior PASS checkpoints are not rerun for chat recovery.

## Coverage gap and planned fault injection
Existing tests inject several crash points but generally keep the original writer/service instance open. Add four focused true-restart tests in `tests/unit/test_studio_failure_recovery_fault_injection.py`:
1. Ambiguous recovery event persists, finalization crashes, database writer closes/reopens, same attempt replay reaches AMBIGUOUS_HOLD without a second provider probe or SUBMIT.
2. Proven-absent recovery persists, crash occurs between provider NOT_SUBMITTED and scheduler requeue transitions, writer closes/reopens, same event replay reaches QUEUED deterministically without a second SUBMIT.
3. Scheduler claim lease expires across writer close/reopen; startup requires recovery and requeue is allowed only with transport-not-dispatched proof; no SUBMIT transition exists.
4. Artifact final bytes/events persist before the job-state transition crashes; writer and artifact service close/reopen; reconciliation reaches READY exactly once and a second reconciliation is NO_ACTION.

No production-code defect is asserted yet. First run only the new test module and change production code only if a concrete failure is demonstrated.

## Runtime limitation
- `http://127.0.0.1:8100/health` was unreachable during bootstrap. No live provider or production E2E action is planned in this task. Live API/E2E evidence must remain unclaimed until the service returns `extension_connected: true`.

NEXT_EXACT_ACTION = "ADD THE FOUR TRUE-RESTART FAULT-INJECTION TESTS IN tests/unit/test_studio_failure_recovery_fault_injection.py USING EXISTING FIXTURE HELPERS -> RUN ONLY THAT NEW TEST MODULE WITH JUNIT EVIDENCE -> FIX ONLY ANY PROVEN FAILURE"


## Execution result - 2026-10-13 23:02 +07

- Exact command: `uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_failure_recovery_fault_injection.py -q --junitxml=.tmp/imp102-targeted.xml --basetemp=.tmp/pytest-imp102-targeted`.
- Process exit code 0; **4 passed, 0 failures, 0 errors, 0 skipped** in 71.38s. JUnit: `.tmp/imp102-targeted.xml` (4 tests, 0 failures/errors/skips).
- Passing cases:
  - `test_imp102_restart_replays_ambiguous_event_without_reprobe_or_duplicate_submit`
  - `test_imp102_restart_finishes_safe_requeue_after_provider_proof_was_committed`
  - `test_imp102_scheduler_restart_requires_no_dispatch_proof_before_requeue`
  - `test_imp102_artifact_restart_reconciles_durable_final_events_after_crash`
- `python -m py_compile tests/unit/test_studio_failure_recovery_fault_injection.py`: exit 0.
- `git diff --check`: exit 0.
- These are new true-restart tests that close/reopen the SQLite writer around durable recovery/artifact crash windows. They verify deterministic replay, proof-gated requeue, no second SUBMIT, and idempotent artifact reconciliation. No production implementation file changed.
- Existing IMP-052..055/IMP-100 PASS checkpoints and Frozen Master guard PASS are retained and were not rerun. No live provider/E2E evidence is claimed; localhost:8100/health was unreachable at bootstrap.


## Commit checkpoint - 2026-10-13 23:07 +07

- Commit: `ddcfb9550e7ccb1fae87199f570507dcbc020008`; parent: `51a54667f6bd65137bf9293a6a8e922e8d3bb381`.
- Message: `test(studio): prove recovery replay across restarts`.
- Exact commit file list: CURRENT_HANDOFF.md, PROJECT_STATE.md, tasks/TASK_QUEUE.md, evidence/tests/IMP-101_MIGRATION_DRY_RUN_EVIDENCE.md, evidence/tests/IMP-102_FAILURE_RECOVERY_FAULT_INJECTION_EVIDENCE.md, tests/unit/test_studio_failure_recovery_fault_injection.py.
- `git diff HEAD^ HEAD --check` PASS; `.tmp/` excluded.
