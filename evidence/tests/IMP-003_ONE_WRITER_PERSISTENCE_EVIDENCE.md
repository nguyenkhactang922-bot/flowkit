# IMP-003 — One-Writer Persistence / Migration Foundation Evidence

## Task

IMP-003 — One-Writer Persistence / Migration Foundation

Branch:
`chatgpt/IMP-003-one-writer-persistence`

Base:
`fc808402788772ba08347bfc5442e9731f8cc901`

Depends:
`IMP-002 = MAIN VERIFIED`

Frozen Master SHA:
`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Implemented scope

Canonical persistence foundation:
- `agent/studio/persistence.py`
- public exports through `agent/studio/__init__.py`

Legacy SQLite connection compatibility:
- `agent/db/schema.py` now applies `PRAGMA synchronous=FULL` in addition to existing WAL + foreign_keys=ON.

Foundation behavior:
- one in-process logical canonical writer per resolved DB path;
- bounded non-blocking write command admission;
- serialized short transactions;
- transaction rollback on command failure;
- separate query-only read repository;
- optimistic revision/CAS helper;
- migration ledger `studio_schema_migration`;
- startup schema compatibility gate rejecting future/identity-mismatched schema versions;
- WAL / synchronous=FULL / foreign_keys=ON verification;
- network/provider-in-transaction context guard;
- legacy CRUD remains compatibility surface; new canonical Studio mutation is routed through the write owner.

## Targeted verification

Python 3.13 local isolated environment.

Targeted Studio primitives + persistence:
- **31/31 PASS**

IMP-003 persistence tests specifically:
- **12/12 PASS**

Covered:
- WAL/FULL/foreign_keys;
- second writer rejection;
- legacy shared connection PRAGMAs;
- serialized writes;
- bounded queue pressure;
- CAS success + stale conflict rejection;
- foreign-key rollback;
- network-in-transaction rejection + rollback;
- separate query-only reads;
- migration idempotency/versioning;
- newer schema rejection;
- migration sequence validation.

Frozen Master guard:
- **PASS**
- canonical SHA unchanged.

## Full local unit regression

Unfiltered Windows run:
- **420 PASS / 3 FAIL**

The three failures are the exact pre-existing Windows/POSIX `/tmp` path assertions documented in IMP-001/IMP-002:
- two parameterized `test_claude_agy_providers_include_read_the_images_at` cases;
- `test_single_sheet_wrapper_wording_matches_original_singular_form`.

No IMP-003 test failed.

Clean unaffected regression excluding exactly those three known platform cases:
- **420 PASS / 3 deselected**

## Diff verification

IMP-003 scope `git diff --check`:
- **PASS**

Unrelated staging:
- `_incoming/` remains untracked and excluded.

## Local verdict

**IMP-003 = LOCAL VERIFIED**

Remote PR/Ubuntu CI/review/merge/main verification remain pending.
