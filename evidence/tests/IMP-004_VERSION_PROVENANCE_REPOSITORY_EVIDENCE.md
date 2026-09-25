# IMP-004 — Version / Provenance Repository Primitives Evidence

## Task

IMP-004 — Version / Provenance Repository Primitives

Branch:
`chatgpt/IMP-004-version-provenance-repository`

Base:
`0e284bed36aa6335d561b0cbe4a7ee304356933a`

Depends:
`IMP-003 = MAIN VERIFIED`

Frozen Master SHA:
`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Implemented scope

Schema migration V2:
- `studio_semantic_version`
- `studio_supersession`
- `studio_current_pointer`
- DB triggers preventing UPDATE/DELETE of immutable semantic versions.

Repository:
- `agent/studio/versioning.py`
- immutable semantic version append/readback;
- canonical JSON payload hashing;
- content-hash validation;
- typed provenance persistence/readback;
- explicit predecessor requirement for successors;
- durable supersession history;
- current pointer/lifecycle status stored separately;
- current pointer/status update protected by optimistic CAS revision;
- restart/readback across writer restart.

Migration behavior:
- existing Studio schema V1 upgrades to V2 through the same migration ledger;
- future schema still fails closed through compatibility gate.

## Targeted verification

Python 3.13 local isolated environment.

Combined Studio primitives + persistence + versioning:
- **39/39 PASS**

IMP-004 versioning tests:
- **8/8 PASS**

Covered:
- initial version provenance + pointer separation;
- approved semantic version DB-level immutability;
- successor preserves predecessor bytes;
- durable supersession history;
- pointer switch via CAS;
- stale CAS rejection;
- restart/readback;
- missing predecessor rejection;
- payload content-hash mismatch rejection;
- V1 → V2 migration upgrade.

Frozen Master guard:
- **PASS**
- canonical frozen SHA unchanged.

## Full local unit regression

Unfiltered Windows:
- **428 PASS / 3 FAIL**

The three failures are the exact known Windows/POSIX `/tmp` assertions from prior tasks.

No IMP-004 test failed.

Clean unaffected regression excluding exactly those three known platform cases:
- **428 PASS / 3 deselected**

## Diff verification

IMP-004 scope `git diff --check`:
- **PASS**

`_incoming/` remains untracked and excluded.

## Local verdict

**IMP-004 = LOCAL VERIFIED**

Remote PR/Ubuntu CI/review/merge/main verification remain pending.


## Remote / Main verification

Fork PR:
- nguyenkhactang922-bot/flowkit#8

Exact PR head:
- 22d6b341b459518e29764118d5bff992ab575776

PR CI:
- workflow run 36123423488
- conclusion: SUCCESS
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

Exact-head review:
- no blocking findings;
- immutable semantic rows protected by DB no-update/no-delete triggers;
- current pointer/lifecycle state stored separately and revision-CAS protected;
- successor creation records durable predecessor/supersession provenance;
- successor creation does not silently change current pointer;
- schema V1→V2 migration preserves migration ledger;
- frozen Master bytes unchanged.

Merge:
- main merge commit: a5299e88195f8feaf94c1ddf9016ea31af01b84f

Local main verification:
- local HEAD = fork/main = a5299e88195f8feaf94c1ddf9016ea31af01b84f
- frozen guard: PASS
- targeted IMP-004 tests: 8/8 PASS

Fork-main push CI:
- workflow run 36163372531
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

## Final verdict

IMP-004 = MAIN VERIFIED on nguyenkhactang922-bot/flowkit:main at a5299e88195f8feaf94c1ddf9016ea31af01b84f.

NEXT_EXACT_ACTION = CLAIM IMP-005 — DEPENDENCYGRAPH + DURABLE INVALIDATIONRECORD
