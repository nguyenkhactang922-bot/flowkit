# IMP-002 — Canonical Contract Primitives Evidence

## Task

IMP-002 — Canonical Contract Primitives

Branch:
`chatgpt/IMP-002-canonical-contract-primitives`

Base:
`373f34058c500220a90e18677350310ba61f5317`

Depends:
`IMP-001 = MAIN VERIFIED`

Frozen Master SHA:
`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Implemented scope

New provider-neutral package:
- `agent/studio/__init__.py`
- `agent/studio/primitives.py`

New tests:
- `tests/unit/test_studio_primitives.py`

Primitives:
- `LogicalId`
- `VersionId`
- `VersionRef`
- `SourceVersionBinding`
- `Provenance`
- `LifecycleState`
- `GateVerdict`
- `FindingSeverity`
- `SemanticRecordMetadata`

Authority rules implemented:
- stable logical identity separated from immutable semantic version;
- exact source ID/version bindings;
- immutable provenance;
- generic lifecycle values from frozen Master;
- explicit gate verdict values;
- explicit finding severity value object while blocking disposition remains policy-owned;
- semantic-record metadata is immutable;
- predecessor must remain inside the same logical identity and cannot self-reference the same version;
- canonical primitive schema contains no provider/runtime transport fields.

## Targeted verification

Python:
- 3.13 local isolated environment.

Commands:
- Python compile of new package/tests;
- frozen Master guard;
- targeted `tests/unit/test_studio_primitives.py`.

Result:
- targeted tests: **19/19 PASS**;
- frozen Master guard: **PASS**;
- canonical frozen SHA: unchanged.

## Full local unit regression

Unfiltered Windows run:
- **407 PASS / 3 FAIL**.

The three failures are the exact pre-existing Windows/POSIX `/tmp` path assertions already documented during IMP-001:
- two parameterized `test_claude_agy_providers_include_read_the_images_at` cases;
- `test_single_sheet_wrapper_wording_matches_original_singular_form`.

Observed mismatch:
- Windows `Path("/tmp/...")` renders `\\tmp\\...`;
- tests assert POSIX `/tmp/...`.

No IMP-002 test failed.

Regression excluding exactly those three known platform cases:
- **407 PASS / 3 deselected**.

## Diff / scope verification

`git diff --check` for IMP-002 code/tests/state scope:
- **PASS**.

Expected changed paths:
- `agent/studio/`
- `tests/unit/test_studio_primitives.py`
- `CURRENT_HANDOFF.md`
- `PROJECT_STATE.md`
- `tasks/TASK_QUEUE.md`
- this evidence file.

`_incoming/` remains unrelated/untracked and must not be staged.

## Local verdict

**IMP-002 = LOCAL VERIFIED**

Remote PR/Ubuntu CI/review/merge/main verification remain pending.


## Remote / Main verification

Fork PR:
- nguyenkhactang922-bot/flowkit#4

Final exact PR head:
- 5d73a7ed6c5174f4c3370199a13e50a2e31ec1ce

PR CI:
- workflow run 36117186461
- conclusion: SUCCESS
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

Exact-head review:
- no blocking findings;
- review identified missing OPEN release-gate value before final head;
- repaired on branch before merge;
- provider/runtime token scan of agent/studio/: clean;
- no runtime source outside agent/studio/ changed.

Merge:
- main merge commit: 49a5352fc29c096802ba1d088c5c9739c6be48c3

Local main verification:
- local HEAD = fork/main = 49a5352fc29c096802ba1d088c5c9739c6be48c3
- frozen guard: PASS
- targeted IMP-002 tests: 19/19 PASS

Fork-main push CI:
- workflow run 36117340581
- conclusion: SUCCESS
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

## Final verdict

IMP-002 = MAIN VERIFIED on nguyenkhactang922-bot/flowkit:main at 49a5352fc29c096802ba1d088c5c9739c6be48c3.

NEXT_EXACT_ACTION = CLAIM IMP-003 — ONE-WRITER PERSISTENCE / MIGRATION FOUNDATION
