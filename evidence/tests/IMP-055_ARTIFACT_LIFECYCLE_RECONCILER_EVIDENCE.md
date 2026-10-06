# IMP-055 Artifact Lifecycle / Store / Reconciler Evidence

Date: 2026-10-07
Branch: `chatgpt/IMP-055-artifact-lifecycle-reconciler`
Base HEAD: `ffeecd49eacc4019bbc63f4a5cb45293d9a4e97d`

## Scope

IMP-055 implements staged immutable artifact bytes + append-only materialization/reconciliation evidence over the existing `GenerationJob.artifact_state` authority. It does not create a competing lifecycle/current-state store and does not place creative approval semantics on the artifact axis.

Frozen authority used by this task:
- artifact states: `NONE / STAGING / READY / STALE_RESULT / QUARANTINED / MISSING / CORRUPT / ARCHIVED`;
- legal materialization path: `NONE -> STAGING -> READY` only after byte/hash/input-lineage validation;
- stale input produces `STALE_RESULT` and never auto-activates;
- startup reconciliation must fail closed for staging/final crash windows, orphan final bytes, missing bytes and corrupt bytes;
- Frozen Master semantic SHA previously verified by the task: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.

## Implementation evidence

Implemented surfaces:
- `agent/studio/artifact_lifecycle.py`
- `agent/studio/persistence.py` migration v9: `studio_generation_artifact_evidence`
- `agent/studio/__init__.py` exports
- `tests/unit/test_studio_artifact_lifecycle.py`
- affected migration/recovery expectations in `tests/unit/test_studio_brainpack.py` and `tests/unit/test_studio_recovery.py`

Persistence properties verified by tests:
- immutable deterministic artifact identity;
- append-only artifact event evidence;
- no artifact/creative/current-state shadow column in the new evidence tables;
- deterministic storage key and artifact IDs;
- immutable staged/final byte/hash/size evidence;
- creative axis remains independent.

## Verified test checkpoints

Durable checkpoints that were already PASS and were not rerun unnecessarily:
- targeted artifact lifecycle: **10/10 PASS** via `.tmp/imp055-targeted-a.xml` + `.tmp/imp055-targeted-b-resume.xml`;
- affected recovery regression: **11/11 PASS** via `.tmp/imp055-recovery-resume.xml`;
- affected persistence / GenerationJob regression: **32/32 PASS** via `.tmp/imp055-affected-core.xml`;
- broader batch A unaffected cases: **35 PASS**;
- remaining non-overlapping broader batch: **166/166 PASS** via `.tmp/imp055-broad-rest.xml`;
- stale migration-history expectation after schema v9: exact failed testcase rerun **1/1 PASS** via `.tmp/imp055-broad-a-fix.xml`.

## Full broader unit run classification

Command captured in durable state:

`uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit -q --basetemp=.tmp/pytest-imp055-broader --junitxml=.tmp/imp055-broader.xml`

Final JUnit `.tmp/imp055-broader.xml`:
- tests: **803**
- failures: **7**
- errors: **22**
- skipped: **0**

The broader execution is therefore recorded as **FAIL** and is not relabeled as PASS.

Failure/error classification from the final JUnit:
- `tests.unit.test_cli_providers.TestAnalyzeCliPromptBranching`: 3 failures — Windows path separator expectation (`\\tmp` vs `/tmp`); `tests/unit/test_cli_providers.py` is unchanged by IMP-055.
- `tests.unit.test_setup*`: 10 failures/errors — UTF-8 decoding failures while setup scans existing generated/skill inputs; `tests/unit/test_setup.py` and `setup.py` are unchanged by IMP-055.
- `tests.unit.test_video_reviewer*`: 15 errors — `FileNotFoundError [WinError 2]`; runtime check confirms `ffmpeg` is not on PATH; `tests/unit/test_video_reviewer.py` is unchanged by IMP-055.
- `tests.unit.test_studio_brainpack::test_schema_v4_upgrades_to_latest_and_preserves_history`: 1 failure from an already-collected stale test snapshot missing migration v9.

The task-related stale migration failure is explained by runtime timestamps:
- full broader basetemp created: **2026-10-06 23:26:53**;
- current `tests/unit/test_studio_brainpack.py` migration-v9 expectation written: **2026-10-06 23:27:11**;
- exact current-state rerun JUnit `.tmp/imp055-broad-a-fix.xml`: **1/1 PASS** at **23:27:36**.

Therefore the final full-run JUnit retained an older collected copy of that test, while the current test/source state has independent exact PASS evidence. The full suite was not restarted.

## Exact-head review repair

Self-review found a crash-recovery idempotency defect in `_append_or_verify`: a crash after durable `FINAL_BYTES_WRITTEN` / `MATERIALIZE_VALID` evidence but before the GenerationJob artifact-state transition could cause startup retry to conflict solely because the audit envelope (`actor_ref`, reason, correlation ID, timestamp/evidence refs) changed.

Repair:
- replay verification now delegates to `ArtifactEvidenceRepository.append_event`, which compares immutable materialization semantics while preserving the first durable audit envelope;
- deterministic event identity and immutable byte/path/hash/input facts remain conflict-checked;
- no new mutable status authority was introduced.

New fault-injection proof:
- `test_startup_replays_durable_final_events_after_crash_before_job_state_transition`
- `.tmp/imp055-review-fix.xml`: **1/1 PASS**.

Directly affected existing regression subset after the repair:
- happy materialization;
- stale late result;
- READY missing/corrupt reconciliation;
- missing-byte recovery;
- archive + append-only evidence.

`.tmp/imp055-review-affected.xml`: **5/5 PASS**.

## Static / authority verification after review repair

- `python -m py_compile` on IMP-055 implementation + affected tests: **PASS**.
- `python -m compileall -q agent/studio`: **PASS**.
- TODO/FIXME/NotImplemented scan on artifact lifecycle/persistence: **CLEAN**.
- direct provider/network-submit leakage scan in artifact lifecycle: **CLEAN**.
- `git diff --check`: **PASS**.
- Frozen Master + freeze manifest: **UNCHANGED** after the previously verified frozen guard PASS.

## Review conclusion

IMP-055 local implementation is **VERIFIED for its claimed scope** with targeted, affected, crash-recovery, migration, static and authority evidence. The one task-related broad failure was a stale-collected test and has exact current-state PASS evidence. The remaining 28 broad-run failures/errors are unchanged Windows/environment/setup/video-reviewer surfaces and are recorded explicitly rather than hidden.

This evidence supports proceeding to side-effect guard -> exact-scope commit/push/PR/CI/review. It does **not** claim the entire Windows `tests/unit` suite is green.
