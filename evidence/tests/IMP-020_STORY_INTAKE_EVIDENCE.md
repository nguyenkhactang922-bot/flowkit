# IMP-020 — Idea / Logline / Premise / Angle / Theme Evidence

## Task

IMP-020 — Canonical Early Story Intake

Branch:
`chatgpt/IMP-020-story-intake-core`

Base:
`c182a8d61261fceee890d4c48efd57240459df74`

Depends:
- IMP-002 MAIN VERIFIED
- IMP-004 MAIN VERIFIED
- IMP-013 MAIN VERIFIED

Frozen Master SHA:
`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Implemented scope

Canonical provider-neutral contracts:
- IdeaContract
- LoglineContract
- PremiseCandidate
- AngleCandidate
- ThemeHypothesis

Canonical behavior:
- stable per-stage logical identity;
- immutable exact semantic versions through VersionRepository;
- exact ActiveProductionProfile binding where policy is consumed;
- exact parent/source version provenance;
- stage-local blocking gates;
- DRAFT candidate creation;
- accepted/current authority only after gate PASS and exact-source readiness;
- stale parent version rejected;
- stale/unlocked ActiveProductionProfile rejected;
- successor versions preserve old accepted bytes/history;
- no silent in-place semantic mutation;
- no provider/runtime fields in canonical story-intake schema.

Legacy compatibility:
- existing FlowKit `project.story` storage path is left intact as compatibility behavior;
- canonical story truth does not read or derive authority from `project.story`;
- canonical models contain no `story` / `project_story` field.

## Review repair before final verification

Local review found that StoryIntakeRepository assumed missing current pointers always raised `CurrentPointerNotFound`, while VersionRepository may return `None`.

Repair:
- exact profile/parent readiness handles typed missing-current failure;
- story `get_current()` now handles both typed missing-current and `None`;
- missing story current returns `None` rather than leaking persistence abstraction.

Failed-stage rerun:
- **1/1 PASS**

## Targeted verification

Python 3.13 local isolated environment.

IMP-020 targeted suite:
- **13/13 PASS**
- 9 test functions, including a 5-stage parameterized blocking-gate matrix.

Covered:
- full Idea → Logline → Premise → Angle → Theme promotion chain;
- stage-local blocking gate for each stage;
- stale parent version rejection;
- stale ActiveProductionProfile rejection;
- immutable successor history/current-pointer behavior;
- cross-project identity rejection;
- exact provenance/source-version enforcement;
- missing-current adapter behavior;
- legacy project.story shadow-authority prohibition.

Frozen Master guard:
- **PASS**
- canonical SHA unchanged.

## Full local unit regression

Unfiltered Windows:
- **507 PASS / 3 FAIL**

The three failures are the exact pre-existing Windows/POSIX `/tmp` path assertions:
- two parameterized `test_claude_agy_providers_include_read_the_images_at` cases;
- `test_single_sheet_wrapper_wording_matches_original_singular_form`.

No IMP-020 test failed.

Clean unaffected regression excluding exactly those three known platform cases:
- **507 PASS / 3 deselected**

## Static / diff verification

- provider/runtime token scan in `agent/studio/story_intake.py`: **none**
- `project.story` references:
  - legacy compatibility persistence path only;
  - canonical module comment documenting non-authority.
- `git diff --check`: **PASS**
- `_incoming/` remains untracked and excluded.

## Local verdict

**IMP-020 = LOCAL VERIFIED**

Remote PR/Ubuntu CI/exact-head review/merge/main verification remain pending.


## Remote / Main verification

Fork PR:
- nguyenkhactang922-bot/flowkit#22

Exact PR head:
- ef423abbbfbd26c3e0e4258e60712138995caf5c

PR CI:
- workflow run 36257856395
- conclusion: SUCCESS
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

Exact-head review:
- no blocking findings;
- frozen Master bytes unchanged;
- no feature source outside agent/studio changed;
- exact-version provenance and pinned ActiveProductionProfile preserved;
- stage-local blockers fail closed;
- stale parent/profile inputs rejected;
- successor versions preserve immutable accepted history;
- legacy project.story remains compatibility-only.

Merge:
- main merge commit: 1ea70be1a6a284009f7c399299c4eab027858d21

Local main verification:
- local HEAD = fork/main = 1ea70be1a6a284009f7c399299c4eab027858d21
- frozen guard: PASS
- targeted IMP-020 tests: 13/13 PASS

Fork-main push CI:
- workflow run 36257937119
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

## Final verdict

IMP-020 = MAIN VERIFIED on nguyenkhactang922-bot/flowkit:main at 1ea70be1a6a284009f7c399299c4eab027858d21.

NEXT_EXACT_ACTION = "READ TASK QUEUE AND CLAIM NEXT DEPENDENCY-READY STORY TASK"
