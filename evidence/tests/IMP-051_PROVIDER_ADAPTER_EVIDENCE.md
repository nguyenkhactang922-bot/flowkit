# IMP-051 Flow / Omni ProviderAdapter Anti-Corruption Evidence

Date: 2026-10-04
Branch: `chatgpt/IMP-051-provider-adapter-anti-corruption`
Base HEAD: `0f8f1387f5aa9b3aacd5efe3ef240f1666306a98`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Implemented boundary

- Added provider-neutral `ProviderAdapterPreflight`, `ProviderExecutionPlan`, runtime reference bindings, provider transport handles/observations and `ProviderAdapterPort` under `agent.studio`.
- Canonical preflight consumes exact-current `ShotIR` + SELECTED `ProviderRoutingDecision` / exact `ProviderProfile`; it does not create or mutate Story/Shot/State/ShotIR/Router/GenerationJob truth.
- Runtime ReferenceAsset media IDs remain ephemeral; exact asset refs/content hashes/roles must match ShotIR bindings before transport.
- Execution mode and resolution must be proven by the exact routing decision requirements; there is no hidden degradation/fallback.
- Concrete Flow/Omni request dialects are confined to `agent.services.provider_adapters`; the neutral studio module imports no service/provider payload types.
- Flow compatibility adapter supports only the explicitly proven first-frame transport tuple/model mapping; unsupported modes fail before provider submit.
- Omni compatibility adapter lowers only explicitly supported model/mode/duration/resolution tuples and validates reference cardinality/roles.
- Submit exceptions / malformed submit results after possible side effect normalize to `AMBIGUOUS`, `retry_safe=false`; no automatic resubmit authority is created.
- Poll/reconcile normalize provider observations only; reconcile never resubmits.
- Cancel remains explicit `UNSUPPORTED` for current Flow/Omni transports because no proven cancel API exists.
- `IMP-052`, not IMP-051, remains owner of durable GenerationJob state/attempt/CAS semantics.

## Targeted tests

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_provider_adapter.py -q
```

Final result:

```text
18 passed
```

Coverage includes exact-current ShotIR/routing/profile preflight, reference hash drift, evidence expiry, unsupported modes/model tuples, Flow/Omni lowering, ambiguous submit semantics, poll normalization, no-fake-cancel, reconcile-never-resubmit and handle/provider mismatch behavior.

## Affected regression

Exact dependency/transport results:

```text
Provider Routing: 13 passed
Production Compiler / ShotIR: 14 passed
Omni Flash compatibility: 28 passed
Flow compatibility/session/batch/upload/throttle: 131 passed
```

Aggregate affected regression:

```text
186 passed
```

## Broader valid Windows regression

Established exclusion envelope retained:
- ignore `tests/unit/test_setup.py`;
- ignore `tests/unit/test_video_reviewer.py`;
- deselect `test_claude_agy_providers_include_read_the_images_at` (2 parametrized cases);
- deselect `test_single_sheet_wrapper_wording_matches_original_singular_form`.

Broader batches, excluding `test_studio_provider_adapter.py`, `test_studio_provider_routing.py`, and `test_studio_production_compiler.py` because those exact files already PASS in targeted/affected stages:

```text
205 passed, 3 deselected
142 passed
78 passed
54 passed
15 passed
38 passed
17 passed
15 passed
16 passed
79 passed
```

Aggregate broader-valid result:

```text
659 passed, 3 deselected
```

Complete valid unit-file coverage across targeted/affected + broader without double-counting the three separately executed canonical files:

```text
704 passed, 3 deselected
```

## Frozen / static gates

```text
python -m py_compile provider_adapter/service/test = PASS
python -m compileall -q agent/studio agent/services = PASS
git diff --check = PASS
FROZEN_MASTER_GUARD = PASS
FROZEN_SEMANTIC_SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
agent.studio provider adapter import leakage into agent.services = NONE (docstring mention only)
TODO/FIXME/NotImplementedError = NONE
```

## Exact-head self-review

- Verified neutral preflight is side-effect free and provider transport is outside canonical DB transactions.
- Verified exact selected route pins requested ShotIR and exact ProviderProfile; runtime mode/resolution must be proven by route requirements.
- Verified runtime references exactly match ShotIR binding set/hash/role before transport.
- Verified Flow dialect mapping is explicit and actual legacy model mapping must equal selected ProviderProfile model version.
- Verified Omni model key is deterministic from mode/duration/resolution and must equal selected ProviderProfile model version.
- Verified current Omni donor reports workflow `done=true` only when a valid Flow content URL was resolved; adapter does not infer success from a generic provider flag outside that donor contract.
- Verified transport exceptions after possible submission are `AMBIGUOUS` and cannot authorize retry.
- Verified reconcile does not resubmit and cancel is not synthesized.
- Verified normalized observations remain runtime evidence and do not become GenerationJob authority.

## Verdict

`IMP-051 = LOCAL VERIFIED`

NEXT_EXACT_ACTION = `SYNC STATE -> SIDE-EFFECT GUARD -> STAGE EXACT IMP-051 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC`


## Main verification / governance sync — 2026-10-04

- Feature PR: `#56`
- Feature head: `ed7aff78e0cb35a7d5a44080777683d204d9d38c`
- Main merge SHA: `6f60c32d73ee447f638fd17775382d420807bdb1`
- PR CI run: `37216700657` SUCCESS Python 3.10 / 3.13 exact feature head
- Post-merge targeted: `18/18 PASS`
- Post-merge affected regression: `186/186 PASS`
- Frozen Master guard: PASS / `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`
- Main push workflow: `37216924329` SUCCESS exact merge SHA

`IMP-051 = MAIN VERIFIED`

NEXT_EXACT_ACTION = `COMMIT/PUSH/PR/MERGE IMP-051 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK`
