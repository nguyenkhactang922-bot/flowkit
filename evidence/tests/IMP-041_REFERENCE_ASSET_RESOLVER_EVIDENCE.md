# IMP-041 ReferenceAsset / Reference Resolver Evidence

Date: 2026-10-03
Branch: `chatgpt/IMP-041-reference-asset-resolver`
Base main: `80671b9a46b057285e9c1476ae266990e87be6a4`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Resume / source-of-truth classification

- Git root verified: `E:\FlowKit-Studio-Upgrade`.
- Branch verified: `chatgpt/IMP-041-reference-asset-resolver`.
- HEAD remained the claim base `80671b9a46b057285e9c1476ae266990e87be6a4` before implementation commit.
- No active pytest/uv/build process existed at resume; only Notepad had the global law open.
- `agent/studio/reference.py` had materialized before stream loss, while exports/tests/evidence were not yet complete.
- Task classification at resume: `INTERRUPTED`; resumed from the materialized draft instead of restarting IMP-041.

## Frozen authority implemented

IMP-041 implements Master Reference System / FM-005 while preserving existing ownership:

- `ReferenceAsset` is provider-neutral conditioning/evidence, never Entity identity truth or State truth.
- Stable asset logical identity is deterministic by project + canonical Entity logical identity + reference slot; semantic change creates immutable successor versions.
- Exact `EntityVersion` binding and provenance are required; stale/cross-project EntityVersion fails closed.
- `content_hash`, role, slot, MIME type, evidence refs and optional source URI are canonical reference metadata.
- Legacy FlowKit `media_id` / reference URL stay in `LegacyReferenceBinding` compatibility projection; canonical `ReferenceAsset` has no media_id/prompt/provider/state field.
- AGENTS.md UUID rule is enforced: CAMS/base64 media IDs are rejected.
- Resolver checks exact current accepted ActiveProductionProfile, EntityVersion and ReferenceAsset versions.
- Resolver chooses a deterministic minimal subset; extra valid candidates are explicitly rejected as `not_selected_minimal_subset` rather than uploaded blindly.
- Provider projection carries only exact asset/entity refs, role/hash and opaque legacy media/source handle.
- Consumer binding requires exact resolution provenance and revalidates selected ReferenceAsset versions immediately before durable dependency-edge creation.
- `reference_binding` exact-version edges make ReferenceVersion consumers visible to the shared DependencyGraph.
- FM-005 bypass is closed: plain `promote_current()` rejects successor ReferenceAssets. Successors must use `promote_successor_current()`, which durably emits selective invalidation records before moving the current pointer.
- ReferenceVersion invalidation is selective, durable, restart-visible and idempotent through existing InvalidationRepository dedupe keys.
- No Flow client/network/provider/camera/lens/lighting/StateSnapshot authority was imported into the canonical module.

## Targeted verification

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_reference.py -q
```

Final result after FM-005 promotion hardening:

```text
13 passed in 1.92s
exit code 0
```

Coverage includes deterministic identity, hash/role contract, no reference-as-state/provider truth, UUID compatibility, exact EntityVersion provenance/dependency, stale Entity rejection, no-op successor rejection, invalidation-bypass rejection, minimal resolver selection, unsupported required role, stale ReferenceVersion rejection, bind-time race revalidation, exact resolution provenance, selective durable invalidation, invalidation replay idempotency and cross-project authority rejection.

## Affected regression

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_versioning.py tests/unit/test_studio_invalidation.py tests/unit/test_studio_active_profile.py tests/unit/test_studio_entity.py tests/unit/test_studio_reference.py -q
```

Final result:

```text
46 passed in 4.23s
exit code 0
```

## Broader Windows regression

The repo already has documented Windows-only `tests/unit/test_setup.py` default-codepage/UTF-8 fixture failures and known video-review/POSIX-specific exclusions from prior verified tasks. Those known failing cases were not rerun as a new task failure. Largest valid unaffected regression:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit -q --ignore=tests/unit/test_video_reviewer.py --ignore=tests/unit/test_setup.py -k "not test_claude_agy_providers_include_read_the_images_at and not test_single_sheet_wrapper_wording_matches_original_singular_form"
```

Final result:

```text
593 passed, 3 deselected in 36.11s
exit code 0
```

Full Ubuntu Python 3.10/3.13 unit CI remains mandatory at PR exact head before merge.

## Frozen/static/diff checks

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
python -m compileall -q agent/studio/reference.py tests/unit/test_studio_reference.py = PASS
git diff --check = PASS
forbidden canonical runtime/authority import grep = no matches
```

## Local verdict

`IMP-041 = LOCAL VERIFIED`

Remote side-effect guard, commit, push, PR, Ubuntu CI, exact-head review, merge and post-merge main verification are still required before `MAIN VERIFIED`.

NEXT_EXACT_ACTION = `SIDE-EFFECT GUARD -> COMMIT IMP-041 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN`
