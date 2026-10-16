# IMP-103 — 300-Shot Scale Benchmark Evidence

**Result:** PASS (local benchmark; not yet MAIN VERIFIED)
**Date:** 2026-10-15 (+07)
**Repository:** `E:\FlowKit-Studio-Upgrade`
**Branch:** `chatgpt/IMP-103-300-shot-scale-benchmark`
**HEAD/base at validation:** `01f9f9939515d87065eb4ea9143981ace5770d42`
**Authority:** Frozen implementation-design Master §95, NFR-009, PERF-001, PERF-002. Frozen Master was not edited.

## Runtime evidence

- Command: `.tmp/imp053-test-venv/Scripts/python.exe -m pytest -q --capture=tee-sys --basetemp=.tmp/imp103-pytest-resume5 tests/performance/test_imp103_300_shot_scale.py --junitxml=.tmp/imp103-benchmark-resume5.xml`
- Combined log: `.tmp/imp103-benchmark-resume5.log`
- JUnit: `.tmp/imp103-benchmark-resume5.xml`
- Final marker: `FINAL_EXIT_CODE=0`
- JUnit result: **1 test, 1 passed, 0 failures, 0 errors, 0 skipped**; elapsed test time 2,424.814 s.
- The benchmark emitted `IMP103_BENCHMARK_RESULT` and all acceptance assertions completed.
- Previously passing fast contract test `tests/unit/test_imp103_scale_contract.py::test_300_ready_rows_round_robin_three_projects_without_starvation` remains PASS from `.tmp/imp103-targeted.xml`; it was deliberately not rerun.
- The interrupted resume4 attempt and failing resume3 attempt remain preserved as historical diagnostics; they are not used as the final result.
- Post-run process check found no active IMP-103/pytest process. Temporary run artifacts remain under local-only `.tmp/` and must not be committed.

## Measured benchmark result

| Metric | Observed result |
|---|---:|
| Distinct canonical shots | 300 |
| Distinct generation jobs | 300 |
| Total setup time | 2,305.7494 s |
| Setup throughput | 0.130 shots/s |
| Scheduler claim phase | 94.5568 s |
| Scheduler claims throughput | 3.173 claims/s |
| Planning + expansion phase | 473.4574 s |
| Eligibility + realization phase | 1,056.6784 s |
| Compiler phase | 598.9656 s |
| Routing/preflight/job creation | 141.4808 s |
| Scheduler queue setup | 29.5878 s |
| Tracemalloc scheduler-setup peak | 74,495 bytes |
| Tracemalloc scheduler-claim peak | 2,097,731 bytes |
| Main SQLite footprint | 110,415,872 bytes |
| Writer queue configured capacity / peak | 64 / 7 |

### Integrity, fairness, queue and admission

- **Shot/job integrity:** 300 distinct shot IDs and 300 distinct GenerationJob IDs; 300 jobs claimed, 0 queued after claim drain; 300 scheduler nodes and 300 readiness checkpoints.
- **Fairness:** 3 projects with 100 shots each; maximum inter-arrival gap 3 positions; 0 starved projects.
- **Bounded writer-queue stress:** capacity 32; peak depth 32; 32 accepted before backpressure; 268 rejected then retried; 300 persisted rows and 300 unique rows; probe duration 20.0165 s.
- **Hierarchical admission:** 8 concurrent claims requested, 4 admitted; global/provider/model/operation/resource cap = 4; maximum active leases during probe = 4.
- **Persistence and cleanup:** 1,500 admission decisions; 300 lease rows; 600 lease-history rows; 0 active leases after release; 0 queued jobs after claims. The harness closes the write owner in its `finally` cleanup path.
- **Writer queue depth stayed within configured capacity** and all benchmark assertions passed.

## Frozen baseline and scope guard

- `python tools/frozen_master_guard.py`: **exit 0, FROZEN_MASTER_GUARD=PASS**.
- Normalized frozen Master SHA-256: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287` (matches manifest).
- `git diff --check`: exit 0 at validation.
- Production source was not changed for IMP-103; implementation additions are the offline performance harness and the fast 300-row fairness contract test.
- Mode is `offline_synthetic_no_provider_calls`. This evidence does **not** claim live-provider, production E2E, or a production throughput SLA. The measured throughput is recorded as observed, not compared with an invented absolute SLA.

## Git lifecycle status

- Local feature branch exists at the verified main base SHA shown above.
- At evidence creation, no remote feature branch and no PR for `chatgpt/IMP-103-300-shot-scale-benchmark` were found.
- Status is **LOCAL BENCHMARK VERIFIED / PR LIFECYCLE PENDING**. Do not mark MAIN VERIFIED until the intended files are committed, pushed, exact-head CI/review gates pass, the PR is merged, and main is verified.
