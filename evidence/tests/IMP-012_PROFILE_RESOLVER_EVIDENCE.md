# IMP-012 — Profile Resolver Evidence

## Task

IMP-012 — Profile Resolver

Branch:
`chatgpt/IMP-012-profile-resolver`

Base:
`5b4edba7ef1a7c9da61cb6acc4de75592440d9f3`

Depends:
- IMP-011 BrainPack Registry = MAIN VERIFIED
- IMP-005 DependencyGraph / Invalidation = MAIN VERIFIED

Frozen Master SHA:
`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Implemented scope

Canonical provider-neutral resolver:
- `agent/studio/profile_resolver.py`
- public exports through `agent/studio/__init__.py`

Authority precedence:
1. locked canonical facts / invariants;
2. hard constraints;
3. allowlisted project overrides;
4. inherited BrainPack policy;
5. soft preferences;
6. allowlisted local downstream intent.

Resolver inputs:
- exact ProjectBootstrapArtifact version;
- exact TopicResolutionArtifact version;
- exact DomainResolutionArtifact version;
- exact BrainPack versions from the one canonical registry;
- canonical locked facts/invariants with exact source versions;
- requested project overrides;
- local intent where explicitly allowlisted;
- explicit resolver version.

Resolver outputs:
- `ProfileResolutionResult`;
- immutable `ResolutionTrace`;
- deterministic `resolution_id` and input fingerprint;
- effective policy hash;
- per-field contender/winner/precedence/source/version/reason trace.

IMP-012 intentionally does **not** define or persist `ActiveProductionProfile`.
IMP-013 owns that immutable downstream snapshot.

## Selection / composition rules

- candidate BrainPacks are exact-version inputs;
- direct and inherited packs must be `FROZEN`;
- direct candidates are filtered against exact Topic/Domain applicability;
- inherited parents are followed by exact version;
- child may override an inherited ancestor rule only when the ancestor rule allows override;
- same-specificity inherited conflicts fail closed;
- conflicting selected packs at the same precedence fail instead of last-write-wins;
- hard BrainPack rule and hard project constraint conflict fails as unresolved hard-hard conflict;
- non-allowlisted project overrides fail closed;
- non-allowlisted local intent fails closed;
- lower authority cannot break locked facts or hard constraints.

## Determinism

The input fingerprint binds:
- resolver version;
- override/local-intent allowlists;
- exact project/topic/domain versions;
- sorted candidate BrainPack versions;
- locked facts and exact source versions;
- requested overrides;
- local intent and exact source versions.

Candidate input ordering therefore does not change the result.

## Provenance review finding repaired before final verification

Local semantic review found that the first provenance builder bound effective packs and winning sources, but not every exact input that had been consumed during the decision.

That was hardened before commit.

Final provenance now binds:
- project input;
- topic resolution;
- domain resolution;
- all evaluated candidate BrainPack versions, including applicability-rejected candidates;
- all inherited/effective BrainPack versions;
- every exact source version appearing in field contenders, including losing contenders.

A dedicated regression test verifies rejected candidates and losing sources remain present in persisted provenance.

## Persistence

`ProfileResolutionRepository` reuses the immutable `VersionRepository`:
- logical identity: `profile-resolution:{project_id}`;
- immutable semantic versions;
- exact resolver-version provenance;
- exact consumed source-version bindings;
- current coordination status uses the existing repository primitives.

No new persistence stack and no provider state are introduced.

## Targeted verification

Python 3.13 isolated environment.

Before provenance hardening:
- targeted IMP-012 = 14/14 PASS.

After provenance hardening:
- targeted IMP-012 = **15/15 PASS**.

Frozen Master guard:
- **PASS**
- canonical SHA unchanged.

Coverage includes:
- hard > soft;
- allowlisted override;
- hard blocks override;
- locked fact outranks all lower authority;
- hard-hard conflict fail-closed;
- exact applicability selection;
- inherited override rules;
- non-overrideable parent protection;
- equal-precedence conflict rejection;
- FROZEN pack gate;
- deterministic candidate-order-independent resolution;
- immutable repository round-trip;
- exact provenance;
- rejected candidate + losing contender provenance;
- provider-state rejection;
- local-intent allowlist;
- no ActiveProductionProfile authority leakage.

## Full local unit regression

Final unfiltered Windows run:
- **484 PASS / 3 FAIL**

The three failures are the exact pre-existing Windows/POSIX `/tmp` assertions already documented by prior tasks:
- two parameterized `test_claude_agy_providers_include_read_the_images_at` cases;
- `test_single_sheet_wrapper_wording_matches_original_singular_form`.

No IMP-012 test failed.

Final clean unaffected regression excluding exactly those three known cases:
- **484 PASS / 3 deselected**

## Static / diff verification

- no `ActiveProductionProfile` class or output contract in IMP-012;
- references to ActiveProductionProfile occur only in explanatory docstrings stating that IMP-013 owns it;
- provider/model names occur only in the recursive forbidden-key guard;
- frozen Master file diff: none;
- `git diff --check`: **PASS**;
- `_incoming/` remains untracked and excluded.

## Local verdict

**IMP-012 = LOCAL VERIFIED**

Remote PR/Ubuntu CI/exact-head review/merge/main verification remain pending.


## Remote / Main verification

Fork PR:
- nguyenkhactang922-bot/flowkit#18

Exact PR head:
- dcea5c5338284b4bfb90d503cee39364450e70c1

PR CI:
- workflow run 36234288304
- conclusion: SUCCESS
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

Exact-head review:
- no blocking findings;
- frozen Master bytes unchanged;
- no feature source outside agent/studio changed;
- canonical precedence ladder enforced;
- equal-rank and hard-hard conflicts fail closed;
- project/local overrides are allowlisted;
- candidate and inherited BrainPacks must be exact-version FROZEN inputs;
- ResolutionTrace preserves exact source/version/precedence/reason evidence;
- resolver identity is deterministic and resolver-version-sensitive;
- persisted provenance binds selected, rejected, inherited and losing consumed sources;
- IMP-012 does not define ActiveProductionProfile or downstream re-resolution authority.

Merge:
- main merge commit: 99e50aa186222d8ecaefc1db479b15d3343af1b2

Local main verification:
- local HEAD = fork/main = 99e50aa186222d8ecaefc1db479b15d3343af1b2
- frozen guard: PASS
- targeted IMP-012 tests: 15/15 PASS

Fork-main push CI:
- workflow run 36234468266
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

## Final verdict

IMP-012 = MAIN VERIFIED on nguyenkhactang922-bot/flowkit:main at 99e50aa186222d8ecaefc1db479b15d3343af1b2.

NEXT_EXACT_ACTION = CLAIM IMP-013 — ACTIVEPRODUCTIONPROFILE
