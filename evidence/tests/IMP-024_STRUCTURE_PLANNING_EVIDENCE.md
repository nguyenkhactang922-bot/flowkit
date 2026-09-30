# IMP-024 — StructureProfile / MacroBeatSheet / DurationBudget Evidence

Date: 2026-09-30
Branch: `chatgpt/IMP-024-structure-profile-budget`
Base HEAD: `066ce0f2f0c53943fab2e5147ba8d05f48a02cde`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Scope implemented

- `StructureProfile` as immutable provider-neutral structure/count/runtime planning policy.
- Count constraints are ranges only; there is no universal exact-count field.
- StructureProfile binds exact ActiveProductionProfile, ProjectBootstrapInput and DomainResolution versions.
- StructureProfile validates runtime against canonical ProjectBootstrapInput when a target duration exists.
- StructureProfile format and genre/niche labels are validated against canonical DomainResolution axes to prevent shadow classification truth.
- `DurationBudget` as versioned hierarchical planning allocation with explicit tolerance.
- top-level runtime and every populated parent/child allocation reconcile within the governing tolerance.
- profile-driven count ranges gate populated macro/sequence/scene/SceneDramaticBeat allocation counts.
- optional allocation target refs are exact-version dependencies and same-project canonical refs.
- `MacroBeatSheet` as ordered projection only: MacroStoryBeat ref + order + duration-allocation binding.
- MacroBeatSheet stores no dramatic function/state/cause/consequence content.
- MacroBeatSheet requires FROZEN_FOR_STRUCTURE StoryCore, exact current planning inputs, accepted MacroStoryBeat refs, full top-level allocation coverage and profile count range.
- revisions use immutable successors, exact-current predecessor checks and shared CAS current pointers.
- dependencies use shared DependencyGraphRepository; revisions emit durable dependency-reachable invalidation through InvalidationRepository.
- ActiveProductionProfile dependency edge uses wildcard profile-path binding so any effective profile semantic change invalidates planning.
- no provider/network/runtime transport authority enters canonical planning contracts.

## Targeted tests

Command:

`uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_structure_planning.py -q`

Final result:

`12 passed in 2.33s`

Exit code: 0.

Negative coverage includes:
- false fixed-count precision field rejection;
- cross-project StructureProfile refs;
- canonical format/niche/runtime mismatch rejection;
- parent/child budget overflow;
- profile-driven count-range violation;
- MacroBeatSheet narrative-field leakage rejection;
- cross-project MacroStoryBeat ref rejection;
- non-frozen StoryCore rejection;
- stale StructureProfile rejection;
- historical non-current revision predecessor rejection;
- macro allocation coverage gap rejection.

## Affected regression

Covered:
- VersionRepository
- DependencyGraph / Invalidation
- Topic / Domain Resolution
- ActiveProductionProfile
- StoryCore
- IMP-024 structure planning

Result:

`67 passed in 9.37s`

Exit code: 0.

## Largest valid Windows regression

Environment check:
- `ffmpeg` is not available on the FileMCP Windows PATH.
- this is the same local environment blocker already recorded by earlier verified tasks.
- three existing CLI tests assert POSIX `/tmp` wording/path behavior and are documented as known Windows-only mismatches.

Command shape:
- `PYTHONUTF8=1`
- ignore only `tests/unit/test_video_reviewer.py` because ffmpeg is unavailable locally;
- deselect only the three previously documented Windows/POSIX-path assertions.

Final result:

`540 passed, 3 deselected in 18.62s`

Exit code: 0.

## Frozen Master guard

`FROZEN_MASTER_GUARD=PASS`

Semantic SHA:

`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Static / diff checks

- `python -m py_compile agent/studio/structure_planning.py tests/unit/test_studio_structure_planning.py agent/studio/__init__.py` = PASS
- `git diff --check` = PASS
- provider/runtime keyword audit = no authority leak
- TODO/FIXME/NotImplemented audit = clean

## Exact-head self-review before commit

Review finding repaired before local verification:
- initial StructureProfile pinned project/domain refs but allowed free-text `format_name` and `genre_niche_label`, which could create shadow classification truth.

Repair:
- parse canonical ProjectBootstrapInput and DomainResolution exact versions;
- require target runtime to match canonical project target when present;
- require format from canonical FORMAT axis;
- require genre/niche from canonical GENRE/NICHE axes;
- require allocation and MacroStoryBeat refs to remain same-project;
- add negative tests for those authority boundaries.

## Intentional files

- `agent/studio/structure_planning.py`
- `agent/studio/__init__.py`
- `tests/unit/test_studio_structure_planning.py`
- `evidence/tests/IMP-024_STRUCTURE_PLANNING_EVIDENCE.md`
- `CURRENT_HANDOFF.md`
- `PROJECT_STATE.md`
- `tasks/TASK_QUEUE.md`

Pre-existing `_incoming/` remains untracked and outside task scope.

## Local verdict

**IMP-024 = LOCAL VERIFIED**

Remote commit/push/PR/CI/exact-head review/merge/main verification remain pending.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-024 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"
