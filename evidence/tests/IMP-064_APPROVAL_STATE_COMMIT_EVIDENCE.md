# IMP-064 Approval / Canonical State Commit Evidence

Date: 2026-10-09
Branch: `chatgpt/IMP-064-approval-state-commit`
Base HEAD: `83303da08c89106dc45d9d3addc92db23e787724`

## Scope

IMP-064 adds an explicit provider-neutral QA/approval -> canonical StateSnapshot commit boundary without creating a second state authority. `ApprovalStateCommitService` validates exact typed QA, durable creative approval, policy/outcome authority and snapshot CAS, then delegates the canonical commit to the existing `StateSnapshotRepository`.

Frozen authority enforced by this task:
- `NO QA APPROVAL -> NO CANONICAL STATE COMMIT`;
- technical/provider completion is not semantic approval;
- Static/Motion QA evidence must be exact current typed `COMPLETED/PASS` evidence;
- human approval of a REVIEW QA result requires durable latest creative command `HUMAN_APPROVE`;
- interrupted `QA_PASS_AND_AUTO_APPROVE` cannot be reinterpreted as human approval;
- StateSnapshot remains the only canonical state payload; ApprovedEndState is designation/reference evidence only;
- candidate StateSnapshot, QA, approval policy and source outcome are exact-version current authority;
- StateSnapshot CAS revision protects stale candidate commits;
- no provider/network side effect occurs in the commit boundary.

## Implementation surfaces

- `agent/studio/approval_state_commit.py`
- `agent/studio/state_continuity.py`
- `agent/studio/__init__.py`
- `tests/unit/test_studio_approval_state_commit.py`

No frozen Master, provider adapter, scheduler, artifact lifecycle or QA evaluator implementation was modified.

## Review hardening

Exact-head review found two approval-boundary issues during implementation:

1. A valid explicit `HUMAN_APPROVE` path left the typed QA current pointer at `REVIEW`, so State Commit could not consume otherwise valid human-approved PASS evidence. The boundary now CAS-promotes the exact current REVIEW QA pointer only for the explicit human-approval path.
2. That promotion originally depended only on GenerationJob being APPROVED/LOCKED. This could mask a crash after durable `QA_PASS_AND_AUTO_APPROVE` but before QA-pointer finalization. The final hardening requires the latest durable creative approval command to be `HUMAN_APPROVE` before REVIEW -> APPROVED promotion. Interrupted automatic approval therefore fails closed and must recover in the QA stage.

Because implementation/test bytes changed after earlier green checkpoints, the final exact-head verification chain was rerun only for affected stages. Earlier PASS checkpoints remain historical evidence only.

## Final exact-head targeted proof

JUnit `.tmp/imp064-final-review-targeted.xml`:
- tests: **7**
- failures: **0**
- errors: **0**
- skipped: **0**
- PTY exit: **0**

Targeted proof covers:
- provider success without QA approval cannot commit canonical state;
- Static QA PASS + authorized automatic approval commits exact StateSnapshot designation;
- Motion QA PASS is typed approval evidence for state commit;
- stale StateSnapshot CAS revision is rejected without designation;
- free-form QA payload cannot substitute for typed QA evidence;
- explicit HUMAN_APPROVE may promote exact REVIEW QA and commit state;
- interrupted auto-approval cannot be reinterpreted as human approval.

## Final affected authority regression

JUnit `.tmp/imp064-final-review-affected.xml`:
- tests: **69**
- failures: **0**
- errors: **0**
- skipped: **0**

Affected regression covered:
- `state_continuity` canonical StateSnapshot / ApprovedEndState authority;
- GenerationJob creative transition history;
- Static QA;
- Motion QA;
- semantic versioning/CAS;
- dependency invalidation.

## Final broader valid Windows regression

JUnit `.tmp/imp064-final-review-broader.xml`:
- tests: **725**
- failures: **0**
- errors: **0**
- skipped: **0**
- deselected: **3**
- PTY exit: **0**

The broader command excluded the IMP-064 targeted file, the six already-PASS affected authority files, and the repository's established Windows/POSIX-only exclusions. Targeted and affected checkpoints were not rerun inside broader.

## Frozen baseline verification

`python tools/frozen_master_guard.py`:

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
```

Frozen semantic SHA is unchanged.

## Final static / authority verification

- `py_compile` / `compileall` for IMP-064 implementation and targeted test: **PASS**;
- public import through canonical isolated `uv` environment: **PASS**;
- `git diff --check`: **PASS**;
- provider/runtime/network leakage scan: **CLEAN**;
- TODO/FIXME/NotImplemented scan: **CLEAN**;
- GenerationJob transition history is ordered by durable `to_revision`, so latest approval-command checks are deterministic;
- canonical state persistence remains owned by `StateSnapshotRepository`; no shadow state store was introduced.

## Verification conclusion

IMP-064 is locally verified for Approval / Canonical State Commit on the final review head. Evidence supports proceeding to Git side-effect guard and exact-scope commit/push/PR lifecycle. This file does not claim merge or MAIN VERIFIED until exact PR-head CI/review/merge and post-merge main verification complete.
