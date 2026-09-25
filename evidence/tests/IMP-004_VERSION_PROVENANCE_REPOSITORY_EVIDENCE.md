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
