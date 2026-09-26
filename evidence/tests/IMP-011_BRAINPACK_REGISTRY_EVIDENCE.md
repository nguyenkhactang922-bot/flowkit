# IMP-011 — BrainPack Registry Evidence

## Task

IMP-011 — BrainPack Registry

Branch:
`chatgpt/IMP-011-brainpack-registry`

Base:
`096ed0109e25390e5ebb2bb1e1eaf146d7c7b5df`

Depends:
`IMP-010 = MAIN VERIFIED`

Frozen Master SHA:
`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Implemented scope

Canonical registry:
- `agent/studio/brainpack.py`
- one `BrainPackRegistryRepository` for all pack families;
- `StoryBrainPackDefinition` is a typed specialization stored in that same registry;
- no parallel Story registry.

Canonical families:
- Knowledge
- Creative
- Story
- Production Style
- Audience
- Format
- Platform
- QA/Rubric
- typed Other family via explicit `custom_family_key`.

Pack definition contract:
- `pack_id + pack_version`;
- exact parent pack-version references;
- typed applicability metadata;
- provider-neutral reusable rules;
- explicit rule HARD/SOFT strength and overrideability metadata;
- source evidence + declared license evidence;
- donor source requires explicit adaptation note and validation;
- exact provenance references;
- optional exact predecessor version.

Registry lifecycle:
- `DRAFT / VALIDATED / FROZEN / DEPRECATED`;
- lifecycle authority is separate from generic creative artifact lifecycle;
- CAS revision protection;
- durable transition history;
- DB trigger blocks illegal/backward jumps;
- definition and parent-edge rows are immutable.

Persistence:
- schema migration V5 `studio_brainpack_registry`;
- immutable definition table;
- immutable exact parent-edge table;
- lifecycle coordination table;
- immutable lifecycle transition history;
- generic SQLite CAS helper extended backward-compatibly with validated composite-scope equality predicates.

Historical migration regression:
- IMP-006 V3→V4 test explicitly pinned to schema V4 so V5 does not alter the meaning of that historical regression.

## Authority invariants verified

- Registry owns reusable pack definitions only.
- No project-specific effective policy fields are present.
- No selection/composition/precedence/conflict/override resolution is performed.
- New pack version does not mutate prior pack lifecycle or any project profile.
- Story specialization uses the same registry.
- Parent inheritance is exact-version and logical cycles are rejected.
- Missing parent/predecessor truth fails closed.
- Missing license/source provenance fails validation.
- Donor content cannot become registry authority without validation/adaptation evidence.
- Provider/runtime keys are rejected recursively inside pack rule values.

## Targeted verification

Python 3.13 isolated environment.

IMP-011 tests:
- **11/11 PASS**

Targeted BrainPack + persistence + observability/migration cluster:
- **33/33 PASS**

Frozen Master guard:
- **PASS**
- canonical SHA unchanged.

## Full local unit regression

Unfiltered Windows:
- **469 PASS / 3 FAIL**

The three failures are the exact pre-existing Windows/POSIX `/tmp` path assertions already documented by prior tasks:
- two parameterized `test_claude_agy_providers_include_read_the_images_at` cases;
- `test_single_sheet_wrapper_wording_matches_original_singular_form`.

No IMP-011 test failed.

Clean unaffected regression excluding exactly those three known platform cases:
- **469 PASS / 3 deselected**

## Static / diff verification

- effective-profile/resolution authority fields absent from BrainPack definition schema;
- provider/runtime strings occur only in the recursive forbidden-key guard;
- `git diff --check` for IMP-011 scope: **PASS**;
- `_incoming/` remains untracked and excluded.

## Local verdict

**IMP-011 = LOCAL VERIFIED**

Remote PR/Ubuntu CI/exact-head review/merge/main verification remain pending.


## Remote / Main verification

Fork PR:
- nguyenkhactang922-bot/flowkit#16

Exact PR head:
- 74f27ad287aa9f87b5acb93bde6d7faebedf1ace

PR CI:
- workflow run 36227308533
- conclusion: SUCCESS
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

Exact-head review:
- no blocking findings;
- frozen Master bytes unchanged;
- no feature source outside agent/studio changed;
- exactly one BrainPackRegistryRepository;
- StoryBrainPackDefinition is a specialization in the same registry;
- definitions/parent edges immutable;
- registry lifecycle separate and CAS/DB guarded;
- source/license/donor validation explicit;
- logical inheritance cycles fail closed;
- registry does not resolve project-effective policy.

Merge:
- main merge commit: e9347bf7b7b8d34418e268d3bdd11538345c172d

Local main verification:
- local HEAD = fork/main = e9347bf7b7b8d34418e268d3bdd11538345c172d
- frozen guard: PASS
- targeted IMP-011 tests: 11/11 PASS

Fork-main push CI:
- workflow run 36227414264
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

## Final verdict

IMP-011 = MAIN VERIFIED on nguyenkhactang922-bot/flowkit:main at e9347bf7b7b8d34418e268d3bdd11538345c172d.

NEXT_EXACT_ACTION = CLAIM IMP-012 — PROFILE RESOLVER
