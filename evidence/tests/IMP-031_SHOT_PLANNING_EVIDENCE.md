# IMP-031 Shot Planning Verification Evidence

Date: 2026-10-03
Task: IMP-031 — ShotExpansion / ShotListManifest / ShotListItem
Branch: `chatgpt/IMP-031-shot-expansion`
Base main: `2da4d431fd52269cd79039a2f9bb6cf0bd940c91`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Authority implemented

- ADR-0020 preserved: `ShotListItem` is the sole canonical `shot_id` origin.
- `ShotExpansion` is stateless and candidates have no `shot_id` or version.
- `CoverageStrategy` and `ShotBudget` are planning prerequisites in the same Shot Planning boundary; neither owns narrative or Shot truth.
- `ShotListManifest` is ordered refs-only projection and cannot carry copied shot dramatic/basic-intent payload.
- Immediate canonical narrative parent of a ShotListItem is exact current `SceneDramaticBeat`; inherited Scene/Sequence/Macro/Story context remains in `NarrativeTrace`.
- Public ShotListItem creation always creates its exact Shot NarrativeTrace; item revision advances the same trace lineage to the successor item version.
- CoverageStrategy must cover the exact current SceneDramaticBeat set reachable from the exact Scene.
- exact ScriptLock / directing / blocking / cinematography / coverage / shot budget / duration budget / locked profile versions are hard-gated.
- current-pointer validity plus unresolved durable invalidation is checked before consumption.
- IMP-031 can persist ShotListItem only as `PLANNED`; `ELIGIBLE` remains owned by IMP-032 ShotEligibilityGate.
- accepted revisions follow immutable successor → dependency edges → durable invalidation → current-pointer CAS.
- no provider/runtime/network imports or side effects exist in canonical shot planning.

## Targeted tests

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_shot_planning.py -q
```

Final result after exact-head self-review hardening:

```text
15 passed in 32.33s
```

Covered:
- candidate schema has no Shot identity surface;
- deterministic one-time ShotListItem `shot_id` origin;
- exact CURRENT Shot NarrativeTrace and why-exists root ancestry;
- no direct canonical Scene→Shot parent edge;
- manifest refs-only/no shadow shot truth;
- required coverage and semantic redundancy rejection;
- budget reconciliation before identity allocation;
- premature `ELIGIBLE` rejection before IMP-032;
- stale parent NarrativeTrace rejection;
- unresolved durable invalidation rejection while current pointer remains unchanged;
- parallel/reused shot identity rejection;
- duplicate/dangling/stale manifest member rejection;
- exact ScriptLock lineage across DirectingIntent and expansion;
- CoverageStrategy successor selective invalidation;
- CoverageStrategy exact current SceneDramaticBeat-set coverage;
- impossible shot-budget precision rejection;
- ShotListItem revision advances exact shot trace successor.

Initial test execution notes:
- direct system `python.exe` had no pytest and executed zero tests;
- non-isolated `uv run pytest` also had no pytest executable and executed zero tests;
- first correct isolated targeted run was 13 PASS / 1 FAIL because the invalidation fixture referenced a non-persisted source-new version; the production FK correctly rejected it;
- fixture was repaired by persisting the immutable successor without promoting the current pointer; no production change was made for that fixture failure.

## Affected regression

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_versioning.py tests/unit/test_studio_invalidation.py tests/unit/test_studio_active_profile.py tests/unit/test_studio_structure_planning.py tests/unit/test_studio_narrative_hierarchy.py tests/unit/test_studio_narrative_trace.py tests/unit/test_studio_story_quality.py tests/unit/test_studio_state_continuity.py tests/unit/test_studio_directing.py tests/unit/test_studio_shot_planning.py -q
```

Final result:

```text
128 passed in 81.89s
```

## Broader valid Windows regression

Uses the same established Windows exclusion envelope as prior MAIN VERIFIED tasks:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit -q --ignore=tests/unit/test_video_reviewer.py --ignore=tests/unit/test_setup.py -k "not test_claude_agy_providers_include_read_the_images_at and not test_single_sheet_wrapper_wording_matches_original_singular_form"
```

Final result:

```text
642 passed, 3 deselected in 106.25s
```

## Static / frozen gates

- `python tools/frozen_master_guard.py` = PASS
- semantic SHA unchanged = `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`
- `python -m compileall -q agent/studio/shot_planning.py tests/unit/test_studio_shot_planning.py` = PASS
- `git diff --check` = PASS
- provider/runtime/network import scan = NONE
- TODO/FIXME/NotImplemented scan = NONE

## Exact-head self-review repairs before commit

Review caught and repaired before LOCAL VERIFIED:
1. blocked caller-supplied `ELIGIBLE` state before IMP-032;
2. enforced exact ScriptLock match through DirectingIntent → ShotExpansion;
3. removed direct canonical Scene→Shot dependency edge;
4. removed dummy placeholder expansion context from CoverageStrategy validation;
5. required CoverageStrategy to cover exact current SceneDramaticBeat set;
6. made ShotListItem creation always create exact shot NarrativeTrace;
7. made ShotListItem revision advance the same trace identity to the successor shot version.

## Verdict

`IMP-031 = LOCAL VERIFIED`

Next: side-effect guard → exact-scope commit → push → PR → Ubuntu CI Python 3.10/3.13 → exact-head review → merge main → post-merge verification → MAIN VERIFIED.


## PR #48 Exact-Head Review Hardening — 2026-10-03

Review after initial PR CI found a crash-recovery gap at the ShotListItem/NarrativeTrace boundary: a process interruption after ShotListItem persistence/current-pointer promotion but before NarrativeTrace completion could leave an accepted ShotListItem without a current exact shot trace. The same ordering risk existed for ShotListItem revision before trace-successor completion.

Hardening applied:
- exact replay of an already-persisted identical ShotListItem is idempotent and repairs a missing exact NarrativeTrace;
- conflicting payload/version replay still fails closed and cannot allocate a parallel/reused shot identity;
- consumers fail closed unless the ShotListItem has the exact CURRENT NarrativeTrace;
- exact replay of an already-persisted identical ShotListManifest is idempotent; conflicting manifest replay still fails closed;
- fault-injection tests cover interruption after initial ShotListItem write and interruption after ShotListItem revision pointer advance.

Verification on the review-fix worktree:
- targeted: `17 passed in 33.95s`;
- affected regression: `130 passed in 73.03s`;
- broader valid Windows regression: `644 passed, 3 deselected in 110.11s`;
- frozen Master guard: PASS, semantic SHA unchanged `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`;
- compileall: PASS;
- `git diff --check`: PASS;
- provider/runtime/network import scan: NONE;
- TODO/FIXME/NotImplemented scan: NONE.

`IMP-031 review-fix = LOCAL VERIFIED`

Next: commit review-fix -> push exact new head to PR #48 -> wait for fresh Ubuntu CI on that head -> exact-head merge guard -> merge -> verify main.
