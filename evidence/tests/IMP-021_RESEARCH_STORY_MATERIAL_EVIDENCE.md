# IMP-021 — Research Intelligence + StoryMaterial Evidence

Date: 2026-09-29

Task: **IMP-021 — Research Intelligence + StoryMaterial**

Branch:
`chatgpt/IMP-021-research-story-material`

Base HEAD:
`1e957e900a4d9d5387cdfc8d88a96c7b836d5e7b`

Dependencies:
- IMP-020 = MAIN VERIFIED
- IMP-006 = MAIN VERIFIED

Frozen Master authority:
`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Authority implemented

Frozen Master §16 Research Intelligence and §17 Research → Story Material plus FR-036, FR-037, NFR-016.

Canonical provider-neutral boundaries implemented:
- `ResearchBrief`
- `ExternalSourceReference`
- `EvidenceClaim`
- `ClaimDisposition`
- `ClaimCertainty`
- `ClaimSupportBinding`
- `StoryMaterial`
- `ResearchArtifact`
- `ResearchRepository`
- `ResearchToStoryMaterialService`

## Acceptance coverage

- exact ResearchBrief identity/version and exact Topic/Domain/ActiveProductionProfile bindings
- exact EvidenceClaim source/version provenance
- external source locator + evidence-locator retained in immutable claim payload
- supported claims require source evidence
- disputed claims require attributed source evidence and explicit attribution
- unsupported/disputed status cannot be silently upgraded
- exact contradiction refs are versioned
- StoryMaterial carries exact EvidenceClaim version support
- unsupported claims fail closed before StoryMaterial production
- StoryMaterial cannot alter source factual disposition
- stale/non-current EvidenceClaim support fails promotion
- stale/unlocked ActiveProductionProfile fails promotion
- immutable historical versions; semantic change creates successor
- provider-specific fields are absent from canonical research contracts

## Files

New:
- `agent/studio/research_story_material.py`
- `tests/unit/test_studio_research_story_material.py`

Modified:
- `agent/studio/__init__.py`
- governance/state files for task claim and verification

## Frozen Master guard

Command:
`python tools/frozen_master_guard.py`

Result:

```text
FROZEN_MASTER_GUARD=PASS
MASTER=docs/design/canonical/MASTER_AI_FILM_STUDIO_FINAL_IMPLEMENTATION_BASELINE_V1.md
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
RAW_SHA256=abb08e8114be3ace0d81ceccf8a3dea45c78a6268c64fae4c332d0644fa1e303
NEWLINE_NORMALIZED=CRLF_TO_LF
```

The Windows raw SHA differs only by the already-verified CRLF checkout transformation; canonical LF SHA remains the frozen authority.

## Targeted tests

Command:

`PYTHONUTF8=1 uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_research_story_material.py -q`

Result:

```text
10 passed in 2.86s
```

## Full Windows unit regression

Command:

`PYTHONUTF8=1 uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit -q`

Result:

```text
3 failed, 517 passed
```

The three failures are the exact pre-existing Windows/POSIX-path characterization cases already recorded by earlier MAIN VERIFIED tasks:
- `test_claude_agy_providers_include_read_the_images_at[claude-_run_claude_cli]`
- `test_claude_agy_providers_include_read_the_images_at[agy-_run_agy_cli]`
- `test_single_sheet_wrapper_wording_matches_original_singular_form`

All fail only because Windows `Path("/tmp/...")` renders as `\\tmp\\...` while those tests assert POSIX `/tmp/...`. IMP-021 does not touch that surface.

## Unaffected regression

Command:

`PYTHONUTF8=1 uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit -q -k "not test_claude_agy_providers_include_read_the_images_at and not test_single_sheet_wrapper_wording_matches_original_singular_form"`

Result:

```text
517 passed, 3 deselected in 34.74s
```

## Diff hygiene

`git diff --check` = PASS.

## Local verdict

**IMP-021 = LOCAL VERIFIED**

Evidence supports the local implementation claim only. Commit/push/PR/Ubuntu CI/exact-head review/merge/main verification remain separate gates.


## Exact-head review finding and repair

Pre-merge exact-head review found one authority gap:
- `ResearchBrief` accepted arbitrary `domain_ref` logical IDs and did not require TopicResolution/DomainResolution to be the exact current accepted versions.
- the original test fixture used `domain-resolution:...`, while the canonical DomainResolution identity from `topic_domain.py` is `niche-resolution:...`.

Repair:
- `ResearchBrief` now requires canonical same-project `topic-resolution:<project>` and `niche-resolution:<project>` identities;
- promotion requires exact current APPROVED/LOCKED TopicResolution and DomainResolution versions;
- stale Topic/Domain inputs fail closed;
- tests now cover cross-project/wrong-authority IDs and stale Topic/Domain versions.

Post-repair targeted result:

```text
13 passed in 1.64s
```

Post-repair full Windows unit result:

```text
3 failed, 520 passed
```

The same three pre-existing Windows/POSIX-path assertions are the only failures.

Post-repair unaffected regression:

```text
520 passed, 3 deselected in 40.24s
```

Frozen Master guard remains PASS and `git diff --check` remains PASS.

**Post-review local verdict: IMP-021 = LOCAL VERIFIED**


## Remote / Main verification

Fork PR:
- nguyenkhactang922-bot/flowkit#24

Final exact PR head:
- 9e39583e8d5b794c30880f69c1d01ecbcf0499ee

Updated-head PR CI:
- workflow run 36543849753
- Python 3.10 unit = SUCCESS
- Python 3.13 unit = SUCCESS
- frozen Master guard = SUCCESS in CI
- full unit suite = SUCCESS in CI

Exact-head review:
- first review found missing canonical/current TopicResolution + DomainResolution enforcement;
- repair commit 9e39583e8d5b794c30880f69c1d01ecbcf0499ee closed that authority gap;
- post-repair targeted tests = 13/13 PASS;
- post-repair Windows unaffected regression = 520 PASS / 3 known POSIX-path cases deselected;
- canonical ResearchBrief / EvidenceClaim / StoryMaterial identity and exact-version provenance preserved;
- supported/disputed/unsupported semantics fail closed as designed;
- StoryMaterial cannot elevate factual authority;
- provider-specific canonical fields absent;
- frozen Master canonical SHA unchanged;
- no blocking findings remained on final exact head.

Merge:
- PR #24 merge commit = 6370e1174b111a69c08f842224f335db42d160ad
- mergedAt = 2026-09-29T08:39:00Z

Local main verification:
- local HEAD = fork/main = 6370e1174b111a69c08f842224f335db42d160ad
- frozen Master guard = PASS
- targeted IMP-021 = 13/13 PASS

Fork-main push CI:
- workflow run 36544062680
- head SHA = 6370e1174b111a69c08f842224f335db42d160ad
- Python 3.10 unit = SUCCESS
- Python 3.13 unit = SUCCESS
- Verify frozen Master baseline = SUCCESS
- Run unit tests = SUCCESS

## Final verdict

**IMP-021 = MAIN VERIFIED** on `nguyenkhactang922-bot/flowkit:main` at:

`6370e1174b111a69c08f842224f335db42d160ad`

NEXT_EXACT_ACTION = "READ TASK QUEUE / DEPENDENCY GRAPH AND CLAIM NEXT DEPENDENCY-READY TASK"
