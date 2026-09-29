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
