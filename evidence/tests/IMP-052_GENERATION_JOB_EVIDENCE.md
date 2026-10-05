# IMP-052 GenerationJob Four-Axis State Machine Evidence

## Scope
- Persistence migration v6 on shared SQLiteWriteOwner.
- Canonical GenerationJob with four orthogonal axes only: scheduler/provider/artifact/creative.
- Exact closed 62-row transition relation: scheduler 15 + provider 19 + artifact 14 + creative 14.
- Optimistic CAS revision, append-only transition history, immutable identity/input pins and durable provider remote lineage.
- Deterministic derived UI status only; no canonical generic status.
- NO RETRY WITHOUT PROOF recovery guards.

## Targeted
```text
20 passed
```
Covers exact 62 rows, all-state reachability, unspecified-transition rejection, V0.13 tuple fixtures, owner guard, immutable identity, CAS, remote-lineage binding, recovery and no-blind-resubmit behavior.

## Affected regression
```text
GenerationJob: 20 passed
Persistence/schema/CAS: 12 passed
Provider routing: 13 passed
Production compiler / ShotIR: 14 passed
Provider adapter: 18 passed
Aggregate affected: 77 passed
```

## Broader valid Windows regression
Established exclusion envelope retained: ignore `tests/unit/test_setup.py`, ignore `tests/unit/test_video_reviewer.py`, deselect two parametrized `test_claude_agy_providers_include_read_the_images_at` cases and `test_single_sheet_wrapper_wording_matches_original_singular_form`. Exact affected files above were excluded to avoid duplicate stage execution.

```text
205 passed, 3 deselected
142 passed
78 passed
95 passed
65 passed
62 passed
Aggregate broader: 647 passed, 3 deselected
```

Complete valid-unit coverage without double-counting affected files:
```text
724 passed, 3 deselected
```

## Static / authority verification
- Frozen Master guard: PASS.
- Frozen semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- `py_compile`, `compileall`, `git diff --check`: PASS.
- GenerationJob transition table import-time count: 62 unique rows = 15 scheduler + 19 provider + 14 artifact + 14 creative.
- `agent.studio.generation_job` provider/runtime/network import leakage scan: NONE.
- TODO/FIXME/NotImplementedError scan: NONE.
- Migration-regression test updated from hard-coded v5 latest history to v6 latest history; rerun batch PASS 78/78.

## Review result
- Identity/input pins are immutable in both typed contract and SQLite trigger.
- Provider request/operation lineage can be established but not rebound.
- Every transition changes exactly one axis, increments revision once, validates full target tuple, and appends immutable evidence in the same DB transaction.
- Transition ownership is explicit.
- `SUBMIT`, `PROVEN_ABSENT`, and safe recovery/requeue are proof-gated.
- Generic status remains derived UI evidence only.

RESULT = IMP-052 LOCAL VERIFIED

## Post-merge main verification - 2026-10-05
- Feature PR #58 merged from exact feature head `5e56cb9dffc0ab7239549f6e3ced67bfc77ec57e`.
- Main merge SHA: `657424f6db4e53ec5fa2d4122efa06aaf47e156f`.
- PR CI run `37223076071`: SUCCESS on Python 3.10 / 3.13.
- Local post-merge targeted GenerationJob verification: 20/20 PASS with durable per-batch exit codes.
- Local frozen Master guard: PASS; semantic SHA `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- Main push workflow `37223369097`: SUCCESS on exact merge SHA, including frozen Master guard and full unit-test steps on Python 3.10 / 3.13.
- A local provider-routing regression attempt was interrupted by the FileMCP bridge and is not counted as PASS evidence; exact-main CI is the authoritative post-merge regression evidence.

RESULT = IMP-052 FEATURE MAIN VERIFIED
