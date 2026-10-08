# IMP-062 Continuity QA + Sequence QA Evidence

Date: 2026-10-08
Branch: `chatgpt/IMP-062-continuity-sequence-qa`
Base HEAD: `742a50a76920003f598207f117b6919606d7c760`

## Scope

IMP-062 adds provider-neutral cross-boundary Continuity QA and Sequence QA without creating a second Story/Shot/State authority. The implementation consumes exact accepted canonical versions, persists immutable versioned QA evidence, registers dependency edges, fails closed on stale/invalidation/authority-scope conflicts, and keeps evaluator/tool failure as review evidence.

Frozen authority enforced by this task:
- Continuity QA binds exact ContinuityLedger, StateSnapshot, Reference/approved-artifact lineage, Scene/Shot lineage and accepted shot-QA evidence;
- canonical state contradiction outranks visual similarity and forces Continuity QA failure;
- Sequence QA binds exact Sequence/Scene/ordered Shot lineage, accepted shot-QA evidence, Continuity QA and Setup/Payoff refs;
- individual shot PASS cannot imply Sequence PASS;
- transition findings may only bind adjacent ordered shots;
- blocking cross-sequence defects cannot be averaged away by an aggregate score;
- evaluator id/version, policy version, exact source versions and finding evidence are pinned in provenance;
- evaluator/tool failure persists immutable `EVALUATOR_ERROR` evidence rather than fabricating a PASS/FAIL verdict;
- automatic approval is fail-closed by default and occurs only when an explicit versioned policy enables it.

## Implementation surfaces

- `agent/studio/continuity_sequence_qa.py`
- `agent/studio/__init__.py` exports
- `tests/unit/test_studio_continuity_sequence_qa.py`

No frozen Master, StateSnapshot/ContinuityLedger authority, Story authority, Shot authority, provider adapter, scheduler or artifact lifecycle implementation was modified.

## Review hardening

Exact-head review identified one false-PASS/authority risk before commit: `CrossBoundaryQAPolicy.auto_approve_pass` initially defaulted to `True`. Static/Motion QA already use fail-closed default approval, and Frozen Continuity QA ordering places QA before approval/propagation. The default was changed to `False` and a targeted negative test proves that a PASS result under the default policy remains in `REVIEW`.

Because implementation/test bytes changed after the earlier green checkpoints, only the affected verification stages were revalidated on the final review head; prior PASS stages were not reused as proof for the changed head.

## Final exact-head targeted proof

Final review targeted JUnit `.tmp/imp062-final-review-targeted.xml`:
- tests: **9**
- failures: **0**
- errors: **0**
- skipped: **0**
- PTY: `pty_58496ada0927c77cfaf0c7d63da5d8146f53`
- exit code: **0**
- final result: **9 passed in 50.42s**

The targeted suite proves:
- canonical StateSnapshot contradiction beats perfect visual similarity;
- adjacent-shot continuity drift is localized to exact shot pairs and blocks;
- blocking Sequence coverage defects cannot be hidden by per-shot PASS;
- stale shot-QA versions fail closed before evaluator execution;
- evaluator failure persists immutable review evidence;
- source versions/provenance/dependency edges are pinned;
- transition localization must bind adjacent ordered shots;
- versioned policy may explicitly allow `NOT_EVALUATED` without forced review;
- default policy does **not** auto-approve a PASS result.

## Final affected authority regression

Final review affected JUnit `.tmp/imp062-final-review-affected.xml`:
- tests: **89**
- failures: **0**
- errors: **0**
- skipped: **0**

Affected authority regression covered the reused canonical surfaces without rerunning IMP-062 targeted tests:
- Static QA;
- Motion QA;
- State continuity;
- Narrative hierarchy;
- Shot planning;
- Screenplay realization / Setup-Payoff;
- dependency invalidation;
- semantic versioning.

## Final broader valid Windows regression

The established Windows-valid exclusion envelope was retained, while the IMP-062 targeted file and eight already-PASS affected files were explicitly excluded to avoid duplicate stage execution. Known platform-specific exclusions remained unchanged.

Final JUnit `.tmp/imp062-final-review-broader.xml`:
- tests: **687**
- failures: **0**
- errors: **0**
- skipped: **0**

Final PTY `pty_adf6814d27dd1a18c065fee42ea64390a1a2`:

```text
687 passed, 3 deselected in 2222.43s (0:37:02)
```

Exit code: **0**.

## Frozen baseline verification

`python tools/frozen_master_guard.py`:

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
```

Frozen semantic SHA is unchanged.

## Final static / authority verification

- `python -m py_compile agent/studio/continuity_sequence_qa.py tests/unit/test_studio_continuity_sequence_qa.py`: **PASS**;
- public import through the canonical isolated `uv` environment: **PASS**;
- explicit assertion `CrossBoundaryQAPolicy(policy_version='x').auto_approve_pass is False`: **PASS**;
- `git diff --check`: **PASS**;
- provider/runtime/network leakage scan in `continuity_sequence_qa.py`: **CLEAN**;
- TODO/NotImplemented scan in IMP-062 implementation: **CLEAN**.

## Verification conclusion

IMP-062 is locally verified for its claimed Continuity QA + Sequence QA scope on the final review head. Evidence supports proceeding to Git side-effect guard and exact-scope commit/push/PR lifecycle. This file does not claim merge or MAIN VERIFIED until exact PR-head CI/review/merge and post-merge main verification complete.
