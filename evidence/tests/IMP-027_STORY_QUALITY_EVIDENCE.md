# IMP-027 — Story Critique / Root Cause / Repair / Quality Gate / ScriptLock Evidence

Date: 2026-09-30
Branch: `chatgpt/IMP-027-story-quality-lock`
Base HEAD: `fd1ef88f42e53ce34e356821eea44ec7fe64b27f`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Canonical scope

Implemented provider-neutral, versioned contracts and repository for:
- CritiqueFinding
- RootCauseLocalization
- StoryRepairPlan
- StoryQualityResult
- ScriptLockManifest

Authority boundaries:
- critique roles produce evidence, not hidden story authority;
- subjective disagreement cannot auto-escalate to BLOCKER;
- hard critique kinds remain BLOCKER severity;
- unresolved BLOCKER cannot be averaged away by aggregate score;
- root cause must point to visible exact source or exact dependency ancestor;
- repair plans preserve the diagnosed preserve set;
- ScriptLock requires exact accepted upstream refs and PASS quality;
- lock creation never rewrites StoryCore / narrative hierarchy / screenplay realization.

## Targeted tests

Initial checkpoint:
- 12/12 PASS.

Final exact-worktree result after project-scope hardening:
- `13 passed in 6.02s`
- exit code 0.

Covered:
- critic/generator role isolation;
- subjective disagreement non-blocker behavior;
- hard-gate critique severity;
- aggregate score cannot override open BLOCKER;
- exact root-cause ancestry;
- preserve-set discipline;
- hard gate FAIL forces quality FAIL;
- ScriptLock requires PASS quality;
- resolved blocker can produce exact immutable lock;
- quality revision invalidates dependent ScriptLock;
- historical non-current predecessor rejection;
- project-prefix collision rejection;
- responsible root-cause ref same-project authority enforcement;
- provenance/human-approval preconditions.

## Affected regression

First affected run found one test-fixture authority mismatch only:
- fixture used `story-material:...` with `ResponsibleLayer.SCREENPLAY_SCENE`;
- production schema correctly rejected it before the intended ancestor gate;
- fixture was corrected to an unrelated same-authority `screenplay-scene:...` ref.

Final affected result:
- `127 passed in 26.64s`
- exit code 0.

## Broader Windows regression

One broader invocation became INTERRUPTED at the FileMCP bridge boundary.
Process inspection found no surviving pytest/uv process and no PASS/FAIL marker.
Only the broader stage was rerun.

Final largest-valid Windows result:
- `580 passed, 3 deselected in 33.93s`
- exit code 0.

Known environment exclusions remain unchanged:
- `tests/unit/test_video_reviewer.py` ignored locally because ffmpeg is absent on the FileMCP Windows PATH;
- three previously documented POSIX-path assertions deselected.

## Frozen Master / static review

- `FROZEN_MASTER_GUARD=PASS`
- semantic SHA unchanged: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`
- `git diff --check` = PASS
- no requests/httpx/socket/subprocess/provider credential authority in canonical module
- no TODO/FIXME/NotImplemented placeholders
- exact-current revision gates present
- shared dependency invalidation and ancestry traversal present
- responsible artifact authority uses delimiter-aware same-project checks
- unresolved BLOCKER and hard-gate FAIL remain dominant over aggregate score

## Local verdict

**IMP-027 = LOCAL VERIFIED**

Remote commit/push/PR/CI/merge/main verification remain pending.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-027 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-027 MAIN VERIFIED — final feature verification

Feature branch:
- `chatgpt/IMP-027-story-quality-lock`
- feature commit = `fb607fdaa6ede42e03be3ff4c8bc188542cf2497`

Pull request:
- PR #38 = MERGED
- final exact head = `fb607fdaa6ede42e03be3ff4c8bc188542cf2497`
- PR CI run = `36708712848`
- Python 3.10 = SUCCESS
- Python 3.13 = SUCCESS
- frozen Master baseline step = SUCCESS in both jobs
- full unit tests = SUCCESS in both jobs
- merge commit / verified feature-main SHA = `8399fe76a4c7e7dc08010b6f442ef64a0d09bb4c`

Local final main verification:
- frozen Master guard = PASS
- targeted IMP-027 = 13/13 PASS
- affected regression = 127/127 PASS
- worktree = only pre-existing untracked `_incoming/`

Main push verification:
- workflow run = `36708995131`
- event = push
- head SHA = `8399fe76a4c7e7dc08010b6f442ef64a0d09bb4c`
- conclusion = SUCCESS
- unit (3.10) = SUCCESS
- unit (3.13) = SUCCESS
- Verify frozen Master baseline = SUCCESS in both jobs
- Run unit tests = SUCCESS in both jobs

Final exact-head review:
- hard blockers cannot be averaged away;
- root cause requires visible source or exact ancestor;
- responsible artifact uses delimiter-aware same-project authority;
- repair preserve-set remains exact;
- hard-gate FAIL dominates aggregate score;
- ScriptLock requires PASS quality and exact-current accepted lineage;
- exact-current/CAS revision gates and dependency invalidation remain active;
- no provider/camera/render authority leakage;
- final exact-head review = PASS.

IMP-027 = MAIN VERIFIED

NEXT DEPENDENCY-READY TASK = IMP-028 — NarrativeTrace.
