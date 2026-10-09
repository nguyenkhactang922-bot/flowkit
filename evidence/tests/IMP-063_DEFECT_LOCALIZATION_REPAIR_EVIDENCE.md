# IMP-063 Defect Localization + Targeted Production Repair Evidence

Date: 2026-10-09
Branch: `chatgpt/IMP-063-defect-localization-repair`
Base HEAD: `7e9b30e0d2ab2785279642762feaefa3b2946a19`

## Scope

IMP-063 adds provider-neutral production defect localization and minimum-scope repair planning without creating a second Story/Shot/State/QA authority. It reuses exact-version QA evidence, VersionRepository, DependencyGraph and InvalidationRepository.

Frozen authority enforced by this task:
- a defect must originate from one exact persisted FAIL finding;
- defect identity pins stable `defect_code`, registry version and detector/evaluator version;
- visible manifestation layer is not automatically the responsible repair layer;
- responsible source must be the cited finding source or an exact ancestor, and also an ancestor of the manifested QA result;
- repair plans preserve the exact diagnosed preserve set;
- repair modes constrain patch scope to the diagnosed dependency path;
- invalidation is selective and limited to strict dependency descendants of patched sources;
- every repair plan must declare re-QA for the originating QA family;
- provenance pins registry/detector/planner version evidence;
- implementation performs no provider/network side effects.

## Implementation surfaces

- `agent/studio/production_repair.py`
- `agent/studio/__init__.py` exports
- `tests/unit/test_studio_production_repair.py`

No frozen Master, QA evaluator implementation, provider adapter, scheduler, artifact lifecycle, Story authority, Shot authority or State authority was modified.

## Review hardening

Final review found an earliest-responsible-layer gap: a downstream manifestation artifact that was connected to the QA result could still be selected even when the QA finding's own `source_refs` pointed to an earlier canonical source. The gate was hardened so `responsible_ref` must be a cited finding source or an exact ancestor of a cited finding source. A negative regression test proves that a connected-but-too-late manifestation layer is rejected.

Because implementation/test bytes changed after earlier green checkpoints, the final exact-head verification chain was re-run only for the affected stages. Earlier PASS checkpoints were retained as historical evidence, not reused as proof for the changed head.

## Final exact-head targeted proof

Full targeted JUnit `.tmp/imp063-final2-targeted.xml`:
- tests: **9**
- failures: **1**
- errors: **0**
- skipped: **0**
- the single failure was `test_wrong_layer_localization_rejected_even_when_identity_prefix_is_valid` and was only an assertion-message mismatch: expected `dependency ancestor`, actual hardened gate message `responsible_ref must be a cited finding source or exact ancestor of one`.

The test expectation was corrected without product-code change, and the failed case alone was rerun in `.tmp/imp063-final2-failed-rerun.xml`:
- tests: **1**
- failures: **0**
- errors: **0**
- skipped: **0**

Composite exact-head targeted result: **9/9 PASS**.

The targeted suite proves:
- exact QA FAIL finding + stable defect code localization;
- registry/detector provenance is mandatory;
- wrong-layer localization is rejected;
- connected but downstream manifestation layer is rejected;
- responsible-layer identity mismatch fails before persistence;
- RepairPlan preserve set cannot drift from diagnosis;
- originating QA family recheck is mandatory;
- valid minimum-scope repair plan persists without provider side effect;
- stale QA result cannot be reused for new localization.

## Final affected authority regression

JUnit `.tmp/imp063-final2-affected.xml`:
- tests: **55**
- failures: **0**
- errors: **0**
- skipped: **0**

Affected regression covered the reused authority surfaces without rerunning IMP-063 targeted tests:
- semantic versioning;
- dependency graph / invalidation;
- story-quality root-cause / repair donor semantics;
- Static QA;
- Motion QA;
- Continuity/Sequence QA.

## Final broader valid Windows regression

The prior broader run was correctly classified INTERRUPTED after a FileMCP workspace restart because its PID/PTy disappeared without a final JUnit marker. Only the broader stage was resumed with a new JUnit/basetemp; targeted and affected PASS checkpoints were preserved and not rerun.

Final resumed JUnit `.tmp/imp063-final2-broader-resume1.xml`:
- tests: **730**
- failures: **0**
- errors: **0**
- skipped: **0**
- time: **3129.477s**

Recorded resumed root PID `77848` was absent after completion. Final result: **730/730 PASS**.

## Frozen baseline verification

`python tools/frozen_master_guard.py`:

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
```

Frozen semantic SHA is unchanged.

## Final static / authority verification

- `python -m py_compile agent/studio/production_repair.py tests/unit/test_studio_production_repair.py`: **PASS**;
- `python -m compileall` for IMP-063 implementation/test: **PASS**;
- public import through the canonical isolated `uv` environment: **PASS**;
- `git diff --check`: **PASS**;
- provider/runtime/network leakage scan in `production_repair.py`: **CLEAN**;
- TODO/FIXME/NotImplemented scan in IMP-063 implementation: **CLEAN**.

## Verification conclusion

IMP-063 is locally verified for its claimed Defect Localization + Targeted Production Repair scope on the final review head. Evidence supports proceeding to Git side-effect guard and exact-scope commit/push/PR lifecycle. This file does not claim merge or MAIN VERIFIED until exact PR-head CI/review/merge and post-merge main verification complete.
