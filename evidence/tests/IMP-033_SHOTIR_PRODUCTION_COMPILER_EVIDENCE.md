# IMP-033 ShotIR / Production Compiler Verification Evidence

Date: 2026-10-04
Task: IMP-033 — ShotIR / Production Compiler
Branch: `chatgpt/IMP-033-shotir-production-compiler`
Base main: `2f47dc6354e6c5e7a1a0bce7afe9b8e176a6c332`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Authority implemented

- `ShotIR` preserves the existing canonical `shot_id`; IMP-033 does not allocate/rekey Shot identity.
- `ShotIR` binds exact FullShotSpec, ShotEligibilityGate, StaticKeyframeSpec, MotionDeltaSpec, approved StateSnapshot/designation, locked ActiveProductionProfile, exact ReferenceAsset versions/content hashes, and exact CompilerRuleSet version.
- `ShotIR` carries normalized provider-neutral semantic layers, static state, motion delta, execution constraints, QA expectations, diagnostics and deterministic compile fingerprints.
- Provider/model/runtime request IDs, upload slots, credentials, API keys and provider request field names are rejected from canonical execution-constraint authority.
- Production Compiler is deterministic lowering only; it owns no Story/Directing/State/Reference/Shot truth.
- ProviderProfile/capability/routing remains downstream (IMP-050); provider adapter lowering remains downstream (IMP-051).
- Exact current-pointer plus unresolved durable invalidation checks block stale FullShotSpec, StaticKeyframeSpec, MotionDeltaSpec, StateSnapshot, ReferenceAsset, ActiveProductionProfile and CompilerRuleSet inputs.
- Recompile preserves ShotIR logical identity, creates immutable successor evidence and invalidates downstream compiled-request/generation descendants before current-pointer advancement.
- Initial rule/IR creation is replay-safe across interruption before LOCK/APPROVED promotion.
- Shared VersionRepository, DependencyGraphRepository and InvalidationRepository remain the only lifecycle/dependency/invalidation truth.

## Resume / source-of-truth evidence

On resume, repo/Git/state showed IMP-032 already MAIN VERIFIED and IMP-033 already claimed/audited. `production_compiler.py` and its targeted tests had materialized but no IMP-033 result marker existed and no pytest process was alive. Therefore execution resumed at targeted tests instead of redoing authority/audit or IMP-032.

## Targeted tests

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_production_compiler.py -q
```

Result:

```text
14 passed in 78.26s
```

Coverage includes:
- canonical shot identity preservation and provider-neutral IR;
- exact source/reference hash bindings;
- deterministic payload/hashes across fresh databases;
- metadata content hash equals immutable ShotIR payload hash;
- provider-specific execution constraint keys fail closed;
- idempotent exact replay and conflict rejection;
- stale FullShotSpec rejection;
- ReferenceAsset successor invalidates old compile lineage;
- ShotIR successor preserves identity and selectively invalidates downstream;
- CompilerRuleSet revision invalidates old IR and changes request fingerprints;
- stale compiler-rule ref rejection;
- interrupted rule creation recovery before LOCK;
- interrupted initial ShotIR compile recovery before APPROVED promotion;
- StaticKeyframeSpec reference-pin mismatch rejection before persistence.

## Affected regression

Bounded batches with explicit exit evidence:

```text
77 passed in 6.47s
60 passed in 23.43s
17 passed in 41.27s
15 passed in 58.77s
```

Aggregate:

```text
169 passed
```

Scope covers shared primitives/persistence/versioning/invalidation/profile/entity/reference plus character/state continuity, NarrativeTrace/directing, ShotPlanning and ShotRealization authority.

## Broader valid Windows regression

Established exclusion envelope retained exactly:
- ignore `tests/unit/test_setup.py`;
- ignore `tests/unit/test_video_reviewer.py`;
- deselect `test_claude_agy_providers_include_read_the_images_at`;
- deselect `test_single_sheet_wrapper_wording_matches_original_singular_form`.

Exact-head batches/results:

```text
347 passed, 3 deselected in 4.66s
126 passed in 9.80s
142 passed in 38.54s
12 passed in 3.72s
17 passed in 41.27s
15 passed in 58.77s
14 passed in 78.26s
```

Aggregate:

```text
673 passed, 3 deselected
```

This is exactly +14 PASS versus the IMP-032 baseline `659 passed, 3 deselected`, matching the 14 new IMP-033 targeted tests.

## Frozen / static gates

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
python -m compileall = PASS
git diff --check = PASS
provider/runtime/network import leakage = NONE
TODO/FIXME/NotImplemented = NONE
```

Provider-related tokens in `production_compiler.py` occur only in explicit provider-neutral documentation, diagnostics, and deny-list guards; there is no provider/runtime/network import or provider request authority.

## Exact-head self-review

- Verified same-shot identity and exact FullShotSpec/static/motion lineage.
- Verified approved StateSnapshot/designation and locked profile are current and unresolved-invalidation free.
- Verified ReferenceAsset content/role/entity exact pins.
- Verified deterministic hashes are derived from canonical normalized payload only.
- Verified compile provenance exactly equals ShotIR source bindings.
- Verified successor dependency registration + durable downstream invalidation precedes current-pointer advancement.
- Verified interruption replay paths are fail-closed/idempotent.
- Verified IMP-050/IMP-051 provider capability/routing/adapter ownership is not absorbed by IMP-033.

## Verdict

`IMP-033 = LOCAL VERIFIED`

Next: side-effect guard → stage exact IMP-033 scope → commit → push → PR → Ubuntu CI Python 3.10/3.13 → exact-head review → merge main → post-merge verification → governance sync → MAIN VERIFIED → claim next dependency-ready task.
