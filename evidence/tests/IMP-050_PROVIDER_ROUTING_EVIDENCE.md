# IMP-050 Provider Capability Registry / Provider Router Evidence

Date: 2026-10-04
Branch: `chatgpt/IMP-050-capability-provider-router`
Base HEAD: `9c6c8a68df6eba566e86aea680d6a892a815eb26`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Implemented boundary

- Evidence-versioned `ProviderProfile` identity = provider + surface + region + model family + model version + profile version.
- Capability/limit/cost/recovery facts require explicit evidence refs, verified_at and expires_at; UNKNOWN is never guessed.
- Deterministic provider-neutral Router consumes exact current `ShotIR`, locked `ActiveProductionProfile`, routing rule version and candidate ProviderProfile versions.
- Provider routing cannot mutate/weaken ShotIR intent or silently drop execution constraints.
- Unsupported/UNKNOWN capability yields ineligible candidate unless an explicit degradable requirement is explicitly allowed by project profile policy.
- No eligible provider yields persisted `NO_ELIGIBLE_PROVIDER` evidence; no hidden fallback.
- Deterministic selection orders eligible candidates by fewest degradations then exact provider-profile identity/version.
- Cost/budget, availability and recovery/reconcile capability are evidence gates.
- ProviderProfile/routing-rule successors use shared dependency/invalidation truth and selectively invalidate dependent routing/lowering outputs before current-pointer advancement.
- Selected route execution requires current accepted route/profile/ShotIR/profile/rule authority and unresolved-invalidation-free inputs.
- Execution freshness is fail-closed: `assert_selected_route(..., as_of=<explicit execution timestamp>)` requires an explicit timezone-aware execution timestamp; it never reuses the historical routing timestamp or reads an implicit wall clock.
- No provider call, transport payload, secret, credential or provider-specific adapter lowering occurs in IMP-050 canonical persistence/routing transactions. IMP-051 owns adapter anti-corruption/lowering.

## Targeted tests

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_provider_routing.py -q
```

Final exact-head result:

```text
13 passed
```

Coverage includes:
- profile evidence/provenance and UNKNOWN-not-guessed;
- deterministic fresh-provider selection;
- candidate-order independence;
- unsupported/UNKNOWN no-hidden-fallback;
- stale ProviderProfile rejection;
- ShotIR constraint omission/weakening rejection;
- explicit degradation policy only;
- cost/budget + recovery evidence gates;
- ProviderProfile successor invalidation;
- execution-time evidence expiry rejection;
- exact route replay/idempotency + conflicting reuse rejection;
- no transport/secret fields;
- degraded availability requires explicit policy;
- execution assertion requires explicit `as_of` timestamp.

## Affected regression

Scope:
- provider routing;
- production compiler / ShotIR;
- ActiveProductionProfile;
- dependency invalidation;
- versioning/current pointers;
- observability/evidence;
- persistence.

Final exact-head result:

```text
75 passed
```

## Broader valid Windows regression

Established exclusion envelope retained exactly:
- ignore `tests/unit/test_setup.py`;
- ignore `tests/unit/test_video_reviewer.py`;
- deselect `test_claude_agy_providers_include_read_the_images_at`;
- deselect `test_single_sheet_wrapper_wording_matches_original_singular_form`.

Exact-head batch results:

```text
347 passed, 3 deselected
91 passed
104 passed
58 passed
32 passed
54 passed
```

Aggregate:

```text
686 passed, 3 deselected
```

## Frozen / static gates

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
python -m compileall = PASS
git diff --check = PASS
provider/runtime/network import leakage = NONE
TODO/FIXME/NotImplemented = NONE
```

## Exact-head self-review

- Verified ProviderProfile identity contains provider/surface/region/model family/model version plus immutable profile version.
- Verified evidence freshness is bounded by all capability facts and availability evidence.
- Verified routing cannot omit or weaken ShotIR execution constraints.
- Verified candidate current-pointer and unresolved-invalidation checks precede selection.
- Verified routing remains side-effect-free and provider-neutral; adapter execution is outside this boundary.
- Verified route decision provenance/dependency edges pin exact ShotIR, ActiveProductionProfile, routing rule and ProviderProfile versions.
- Verified profile/rule/route successor invalidation is durable before current-pointer advancement.
- Verified execution freshness cannot silently fall back to the historical routing timestamp; caller must provide explicit execution `as_of`.

## Verdict

`IMP-050 = LOCAL VERIFIED`

NEXT_EXACT_ACTION = `SIDE-EFFECT GUARD -> STAGE EXACT IMP-050 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC`
