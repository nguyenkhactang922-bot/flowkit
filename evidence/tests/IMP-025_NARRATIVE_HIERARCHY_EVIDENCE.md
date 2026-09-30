# IMP-025 — Canonical Narrative Hierarchy Evidence

Date: 2026-09-30
Branch: `chatgpt/IMP-025-narrative-hierarchy`
Base HEAD: `c546378694d97a3b88f8f65bb212548f1040f8fe`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Scope implemented

Canonical narrative truth:
- MacroStoryBeat
- Sequence
- Canonical Scene
- SceneDramaticBeat

Planning/projection only:
- SequencePlan
- SceneBudget
- SceneListManifest
- SceneBreakdownManifest

Authority boundaries:
- no generic persistent Beat canonical entity;
- legacy FlowKit operational Scene is not imported or reused as canonical cinematic Scene;
- manifests store order/refs/budgets only and cannot duplicate narrative truth;
- StructureProfile / DurationBudget constrain planning but cannot rewrite accepted narrative truth;
- exact-version ActiveProductionProfile, StoryCore, StoryGraph, planning and parent refs are pinned in provenance;
- revisions require exact-current predecessors and use immutable successor + CAS current-pointer discipline;
- shared DependencyGraphRepository provides exact-version ancestry/descendant traversal;
- shared InvalidationRepository propagates dependency-reachable invalidation.

## Targeted IMP-025 checkpoint

Durable checkpoint recorded before resume:

`11 passed in 6.39s`

Exit code: 0.

Verified by targeted/negative tests:
- no generic persistent Beat;
- canonical Scene distinct from legacy FlowKit Scene;
- MacroStoryBeat -> Sequence -> Scene -> SceneDramaticBeat persistence;
- bidirectional exact-version ancestry;
- Scene state-change / accepted no-change-purpose gate;
- SceneDramaticBeat resistance-or-reveal + microchange gate;
- no manifest/budget shadow truth;
- stale MacroStoryBeat parent rejection;
- historical non-current predecessor rejection;
- MacroStoryBeat revision invalidation;
- manifest-only revision preserves canonical Scene identity;
- project-prefix collision rejection;
- exact provenance binding.

## Affected regression

Command covered:
- versioning
- invalidation
- topic/domain
- ActiveProductionProfile
- CharacterState
- StoryCore
- structure planning
- narrative hierarchy

Result:

`95 passed in 25.44s`

Exit code: 0.

## Broader Windows regression

First invocation became INTERRUPTED at the bridge boundary. Process inspection found no surviving pytest/uv process and no PASS/FAIL result marker, so only this stage was rerun.

Baseline-compatible Windows command:
- `PYTHONUTF8=1`;
- ignore `tests/unit/test_video_reviewer.py` because ffmpeg is absent on the FileMCP Windows PATH;
- deselect the three previously documented POSIX-path assertions.

Final result:

`555 passed, 3 deselected in 32.71s`

Exit code: 0.

## Frozen Master guard

`FROZEN_MASTER_GUARD=PASS`

Semantic SHA:

`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Exact-head self-review

PASS.

Reviewed:
- no generic persistent Beat class/identity;
- no import/use of legacy FlowKit operational Scene as canonical truth;
- no requests/httpx/socket/subprocess/provider credential authority in canonical module;
- no camera/lens/lighting/provider/prompt authority fields;
- delimiter-aware project-scope gates are used for project-owned child refs;
- revision paths require exact-current predecessors;
- dependency-reachable invalidation uses shared InvalidationRepository;
- bidirectional ancestry uses shared DependencyGraphRepository;
- no TODO/FIXME/NotImplemented placeholders;
- `git diff --check` = PASS.

## Worktree scope

Intentional IMP-025 files:
- `agent/studio/narrative_hierarchy.py`
- `agent/studio/__init__.py`
- `tests/unit/test_studio_narrative_hierarchy.py`
- `evidence/tests/IMP-025_NARRATIVE_HIERARCHY_EVIDENCE.md`
- `CURRENT_HANDOFF.md`
- `PROJECT_STATE.md`
- `tasks/TASK_QUEUE.md`

Pre-existing `_incoming/` remains untracked and outside task scope.

## Local verdict

**IMP-025 = LOCAL VERIFIED**

Remote commit/push/PR/CI/merge/main verification remain pending.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-025 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-025 MAIN VERIFIED — final feature verification

Feature branch:
- `chatgpt/IMP-025-narrative-hierarchy`
- feature commit = `0582bf9d075008ee54fb7a78c1689eb115447e02`

Pull request:
- PR #34 = MERGED
- final exact head = `0582bf9d075008ee54fb7a78c1689eb115447e02`
- PR CI run = `36695592106`
- Python 3.10 = SUCCESS
- Python 3.13 = SUCCESS
- frozen Master baseline step = SUCCESS in both jobs
- full unit tests = SUCCESS in both jobs
- merge commit / verified feature-main SHA = `ce2108a72c2e198ef7a73ef8317195b5f1950b32`

Local final main verification:
- frozen Master guard = PASS
- targeted IMP-025 = 11/11 PASS
- affected regression = 95/95 PASS
- worktree = only pre-existing untracked `_incoming/`

Main push verification:
- workflow run = `36695853857`
- event = push
- head SHA = `ce2108a72c2e198ef7a73ef8317195b5f1950b32`
- conclusion = SUCCESS
- unit (3.10) = SUCCESS
- unit (3.13) = SUCCESS
- Verify frozen Master baseline = SUCCESS in both jobs
- Run unit tests = SUCCESS in both jobs

Final exact-head review:
- no generic persistent Beat authority;
- legacy FlowKit Scene remains execution/compatibility only;
- MacroStoryBeat / Sequence / Scene / SceneDramaticBeat canonical ownership remains explicit;
- manifests/budgets remain projection/planning only;
- exact-current/CAS revision gates and dependency invalidation remain active;
- bidirectional exact-version ancestry uses shared dependency graph;
- no provider/camera/prompt authority leakage;
- final exact-head review = PASS.

IMP-025 = MAIN VERIFIED

NEXT DEPENDENCY-READY TASK = IMP-026 — Dialogue / Setup-Payoff / Screenplay Realization.
