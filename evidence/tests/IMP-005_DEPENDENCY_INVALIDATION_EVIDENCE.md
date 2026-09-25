# IMP-005 — DependencyGraph + Durable InvalidationRecord Evidence

## Task

IMP-005 — DependencyGraph + Durable InvalidationRecord

Branch:
`chatgpt/IMP-005-dependency-invalidation`

Base:
`d88af1be0d812c20038cd970b663d99c821f1467`

Depends:
`IMP-004 = MAIN VERIFIED`

Frozen Master SHA:
`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Implemented scope

Schema migration V3:
- immutable exact-version `studio_dependency_edge`;
- durable `studio_invalidation_record`;
- immutable `studio_invalidation_transition` audit history;
- exact FK bindings to semantic versions and dependency edge truth;
- unresolved/resolved lifecycle constraints;
- immutable cause/source/affected/edge/scope/provenance/repair evidence;
- deterministic dedupe key;
- migration ledger advances V2 → V3.

Repository layer:
- `DependencyGraphRepository`;
- exact-version outgoing/incoming queries;
- deterministic forward/reverse reachability;
- `InvalidationRepository`;
- selective dependency-reachable invalidation;
- deterministic replay/idempotency;
- CAS-protected `UNRESOLVED → RESOLVED`;
- durable transition provenance;
- restart/readback of unresolved invalidations.

Authority preserved:
- DependencyGraph owns edge truth.
- InvalidationRecord records consequences only.
- No provider/model fields added.
- Durable writes use the existing one-writer persistence foundation.
- Dependency lookup occurs outside the invalidation write transaction.
- Frozen Master bytes unchanged.

## Review finding repaired before verification

Initial targeted review found cause mutation was correctly rejected, but SQLite trigger ordering emitted the status-transition error first.

Repair:
- status-transition trigger now runs only when status/revision/resolution fields change;
- cause/binding-only mutation is rejected by the immutable-fields trigger;
- legal CAS resolution remains accepted.

The exact failed test was rerun first and passed before the broader targeted suite.

## Targeted verification

Python 3.13 local isolated environment:

- failed-stage rerun: **1/1 PASS**
- IMP-003 + IMP-004 + IMP-005 targeted cluster: **28/28 PASS**
- frozen Master guard: **PASS**

IMP-005 coverage:
- exact direct/transitive reachability;
- reverse reachability;
- preserved unrelated descendant;
- selective invalidation;
- duplicate change replay idempotency;
- restart replay of unresolved records;
- CAS stale-resolution rejection;
- durable resolution transition history;
- immutable cause and edge truth;
- edge replay/conflict behavior;
- schema V2 → V3 migration history.

## Full local unit regression

Unfiltered Windows:
- **436 PASS / 3 FAIL**

The three failures are the exact pre-existing Windows/POSIX `/tmp` path assertions already documented by IMP-001 through IMP-004.

Clean unaffected regression excluding exactly those three cases:
- **436 PASS / 3 deselected**

## Diff / integrity

- IMP-005 scope `git diff --check`: **PASS**
- frozen Master guard: **PASS**
- frozen SHA unchanged
- `_incoming/` remains untracked and excluded.

## Local verdict

**IMP-005 = LOCAL VERIFIED**

Remote PR/Ubuntu CI/exact-head review/merge/main verification remain pending.


## Remote / Main verification

Fork PR:
- nguyenkhactang922-bot/flowkit#10

Exact PR head:
- af74ea8896ac6df7e328283614df3ef23b0141f8

PR CI:
- workflow run 36166026866
- conclusion: SUCCESS
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

Exact-head review:
- no blocking findings;
- DependencyGraph retained edge authority;
- InvalidationRecord retained consequence-only authority;
- immutable cause/source/affected/edge evidence enforced;
- deterministic dedupe + selective reachability verified;
- one-way CAS lifecycle + durable transition history verified;
- frozen Master bytes unchanged.

Merge:
- main merge commit: 8e07bb1066b0d0b75b5050c005a443ea71b5ee10

Local main verification:
- local HEAD = fork/main = 8e07bb1066b0d0b75b5050c005a443ea71b5ee10
- frozen guard: PASS
- targeted IMP-005 tests: 8/8 PASS

Fork-main push CI:
- workflow run 36166182569
- conclusion: SUCCESS
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

## Final verdict

IMP-005 = MAIN VERIFIED on nguyenkhactang922-bot/flowkit:main at 8e07bb1066b0d0b75b5050c005a443ea71b5ee10.

NEXT_EXACT_ACTION = CLAIM IMP-006 — OBSERVABILITY / ERROR / EVIDENCE CORE
