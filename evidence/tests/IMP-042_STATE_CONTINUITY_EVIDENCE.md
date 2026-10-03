# IMP-042 StateSnapshot / ContinuityLedger / ApprovedEndState Evidence

Date: 2026-10-03
Task: IMP-042
Branch: `chatgpt/IMP-042-state-continuity`
Base main: `55ba8d747db11c52417d6d9dfe1b67a807de604e`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Authority / implementation boundary

Implemented `agent/studio/state_continuity.py` under frozen sections 58-61 + 62/63 rules:

- `StateSnapshot` is the only canonical semantic continuity/world-state payload owner.
- `StateFact` accepts State Engine-owned observable/semantic continuity namespaces and rejects execution/provider/media keys recursively from JSON payload.
- Story-owned `character-model:`, `relationship:`, and `character-knowledge:` artifacts are exact-version context refs only; their payload is not copied into StateSnapshot.
- `StateDelta` is payload-free and stores only fact identity + before/after hashes.
- `ApprovedEndStateDesignation` is refs/provenance only and never duplicates snapshot facts.
- only exact-current APPROVED/LOCKED StateSnapshot with current approved designation + current QA/policy/outcome evidence can propagate.
- `ContinuityLedger` owns versioned continuity constraints/findings/propagation links only; StateSnapshot remains semantic authority.
- continuity constraints/findings must reference fact keys that exist in exact bound StateSnapshots.
- finding `responsible_ref` values become exact provenance/dependency bindings.
- legacy parent-scene/media chaining is modeled only as `LegacyMediaChainConditioning`; UUID media IDs never become canonical State facts.
- StateSnapshot successor approval creates durable selective invalidations before moving the current pointer, while excluding the replacement snapshot itself from invalidation reachability.
- ContinuityLedger successors cannot use plain promotion; `promote_successor_current()` emits durable dependent invalidations first.
- ApprovedEndState revocation creates immutable designation successor history, emits durable invalidations, sets the designation current pointer INVALIDATED, and blocks further propagation of that snapshot.
- shared `VersionRepository`, `DependencyGraphRepository`, and `InvalidationRepository` are reused; no second state/dependency truth store was introduced.

## Targeted verification

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_state_continuity.py -q
```

First run after initial implementation:

```text
12 passed, 1 failed
```

The single failure was a test-only ordering assumption (`StateSnapshot` intentionally sorts StateFact identities deterministically). Production logic was unchanged; the assertion was corrected to select the wardrobe fact by namespace.

Final result after authority/revocation hardening:

```text
16 passed in 5.85s
exit code 0
```

Coverage includes:
- generated/media/provider payload rejected from StateSnapshot, including nested JSON keys;
- legacy media-chain compatibility accepts canonical UUID media IDs only and does not enter State authority;
- payload-free StateDelta;
- Story-owned character/relationship/knowledge state remains reference-only;
- DRAFT snapshot cannot propagate;
- exact QA/policy/outcome approval creates refs-only ApprovedEndState designation;
- stale QA blocks approval;
- exact StateSnapshot provenance required;
- subject EntityVersion must be current and belong to project;
- no-op StateSnapshot successor rejected;
- ContinuityLedger consumes approved/designated StateSnapshot only and contains no state payload;
- consumer binding requires exact ledger + StateSnapshot provenance;
- StateSnapshot successor invalidation is selective and replacement snapshot is not self-invalidated;
- unknown StateFact references in continuity evidence are rejected;
- ContinuityLedger successor cannot bypass durable invalidation;
- ApprovedEndState revocation invalidates bound continuity descendants and blocks propagation.

## Affected regression

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_versioning.py tests/unit/test_studio_invalidation.py tests/unit/test_studio_entity.py tests/unit/test_studio_reference.py tests/unit/test_studio_character_state.py tests/unit/test_studio_state_continuity.py -q
```

Final result:

```text
65 passed in 11.78s
exit code 0
```

## Broader Windows regression

Known repo Windows-only `tests/unit/test_setup.py` codepage/UTF-8 failures and existing video-review/POSIX-specific exclusions were not relabeled as task failures. Largest valid unaffected regression used the same exclusion envelope as prior MAIN VERIFIED tasks:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit -q --ignore=tests/unit/test_video_reviewer.py --ignore=tests/unit/test_setup.py -k "not test_claude_agy_providers_include_read_the_images_at and not test_single_sheet_wrapper_wording_matches_original_singular_form"
```

Final result:

```text
609 passed, 3 deselected in 47.87s
exit code 0
```

Full Ubuntu Python 3.10/3.13 unit CI remains mandatory at PR exact head before merge.

## Frozen / static / diff checks

An initial guard invocation used the wrong nonexistent path `scripts/check_frozen_master.py`; it was an invocation error, not a design failure, and no test stage was rerun because of it. Correct repository guard:

```text
python tools/frozen_master_guard.py --repo-root .
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
```

Additional checks:

```text
python -m compileall -q agent/studio/state_continuity.py agent/studio/__init__.py tests/unit/test_studio_state_continuity.py = PASS
git diff --check = PASS
forbidden canonical runtime/provider import scan = NONE
TODO/FIXME/NotImplemented scan = NONE
```

## Local verdict

`IMP-042 = LOCAL VERIFIED`

Remote side-effect guard, commit, push, PR, Ubuntu CI, exact-head review, merge and post-merge main verification are still required before `MAIN VERIFIED`.

NEXT_EXACT_ACTION = `SIDE-EFFECT GUARD -> COMMIT IMP-042 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN`


## MAIN VERIFIED

Feature PR #44:
- final exact head: `b0ce693b28ac9e9b00135b3a938ee73852b3f3bf`
- Ubuntu CI run `37108150194`: Python 3.10 SUCCESS + Python 3.13 SUCCESS + frozen guard SUCCESS
- exact-head review: PASS
- merged at `22c9975f8296bb40d5e82cc3c698a2e7fc38b062`

Post-merge main verification:
- local main HEAD = `22c9975f8296bb40d5e82cc3c698a2e7fc38b062`
- worktree clean
- frozen Master guard PASS / semantic SHA unchanged
- targeted IMP-042 = 16/16 PASS
- affected regression = 65/65 PASS
- main push workflow `37108250205` SUCCESS on exact merge SHA, including Python 3.10/3.13 unit CI + frozen guard

Feature implementation verdict: **IMP-042 = MAIN VERIFIED**.

Governance-only state synchronization remains to be merged and verified before claiming the next dependency-ready task.
