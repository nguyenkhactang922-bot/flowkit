# IMP-023 — StoryCore + CausalStoryGraph + Lock Evidence

Date: 2026-09-30
Branch: `chatgpt/IMP-023-storycore-causal-lock`
Base HEAD: `0bc64459a5cb3a7e084e8e825381d98ba21b7875`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Scope implemented

- one stable `story_core_id` with immutable DRAFT and FROZEN_FOR_STRUCTURE successor versions;
- typed `ConflictModel` and `StakesModel` required by frozen StoryGraph authority;
- typed `CausalStoryGraph` nodes/edges and deterministic causal validation evidence;
- causal gap, orphan cause, missing consequence and illegal directed-cycle blocking findings;
- graph construction from exact StoryCore DRAFT only;
- StoryCore lock gated by exact matching StoryGraph + passing causal validation;
- lock emits immutable successor of the same StoryCore logical identity;
- exact dependency edges for all semantic inputs;
- durable dependency-reachable invalidation on StoryCore/Conflict/Stakes/StoryGraph revisions;
- provider/runtime fields rejected from canonical contracts;
- cross-project story/research references fail closed.

## Exact-head review repair before commit

Initial targeted tests passed, but review found an authority-lineage gap:
- accepted CharacterModelVersion refs were checked as current but were not parsed to prove `story_core_ref` matched the exact StoryCore DRAFT;
- StoryGraph did not prove ConflictModel/StakesModel were derived from its exact StoryCore DRAFT;
- stale StoryGraph versions could reach causal evaluation before current-pointer rejection.

Repair:
- ConflictModel and StoryGraph now parse canonical CharacterModelVersion payloads and require exact StoryCore DRAFT binding;
- ConflictModel relationship refs are parsed as canonical RelationshipState and must belong to the same project;
- StakesModel requires its ConflictModel to bind the same exact StoryCore DRAFT;
- StoryGraph requires ConflictModel + StakesModel to bind the same exact StoryCore DRAFT and exact conflict chain;
- validation rejects a stale StoryGraph version before emitting new validation evidence;
- added three negative tests for those exact cases.

## Targeted IMP-023

Command:

`uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_story_core.py -q`

Result:

`12 passed in 3.69s`

Exit code: 0.

## Affected regression

Covered:
- VersionRepository
- DependencyGraph / Invalidation
- Story Intake
- Research / StoryMaterial
- Character State
- ActiveProductionProfile
- IMP-023 StoryCore

Result:

`77 passed in 9.66s`

Exit code: 0.

## Full Windows regression diagnostic

An unfiltered Windows run exited 1. The observed failures/errors are outside IMP-023:
- the same three pre-existing Windows/POSIX `/tmp` assertion cases in `test_cli_providers.py`;
- this FileMCP environment has no `ffmpeg` executable on PATH, so `test_video_reviewer.py` cannot create its synthetic video fixture; this same environment blocker is already recorded by IMP-022;
- the first diagnostic invocation omitted `PYTHONUTF8=1`, so setup test fixtures writing an em dash with the Windows default encoding were then read as UTF-8. The baseline-compatible Windows command exports `PYTHONUTF8=1`.

IMP-023 does not modify `setup.py`, `test_setup.py`, `video_reviewer.py`, `test_video_reviewer.py`, or `test_cli_providers.py`.

## Largest valid Windows regression

Command shape:
- `PYTHONUTF8=1`
- ignore only `tests/unit/test_video_reviewer.py` because ffmpeg is unavailable;
- deselect only the three previously documented Windows/POSIX-path assertions.

Result:

`523 passed, 3 deselected in 14.96s`

Exit code: 0.

## Frozen Master guard

`FROZEN_MASTER_GUARD=PASS`

Semantic SHA:

`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Static / diff checks

- `python -m py_compile agent/studio/story_core.py tests/unit/test_studio_story_core.py` = PASS
- `git diff --check` = PASS

## Worktree scope

Intentional IMP-023 files:
- `agent/studio/story_core.py`
- `agent/studio/__init__.py`
- `tests/unit/test_studio_story_core.py`
- `evidence/tests/IMP-023_STORYCORE_CAUSAL_LOCK_EVIDENCE.md`
- `CURRENT_HANDOFF.md`
- `PROJECT_STATE.md`
- `tasks/TASK_QUEUE.md`

Pre-existing `_incoming/` remains untracked and is explicitly outside task scope.

## Local verdict

**IMP-023 = LOCAL VERIFIED**

Remote PR/CI/exact-head review/merge/main verification remain pending.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD → COMMIT IMP-023 → PUSH → PR → UBUNTU CI → EXACT-HEAD REVIEW → MERGE MAIN → VERIFY MAIN"
