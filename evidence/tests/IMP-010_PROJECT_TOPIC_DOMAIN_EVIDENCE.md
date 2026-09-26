# IMP-010 — Project / Topic / Domain Resolution Evidence

## Task

IMP-010 — Project / Topic / Domain Resolution

Branch:
`chatgpt/IMP-010-project-topic-domain`

Base:
`1c22e61bbe34538317f8f83df092482b62ec1ede`

Depends:
- IMP-004 = MAIN VERIFIED
- IMP-006 = MAIN VERIFIED

Frozen Master SHA:
`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Implemented scope

Provider-neutral canonical contracts/services:
- `ProjectBootstrapInput`
- `ProjectConstraint`
- `TopicClassifierOutput`
- `TopicResolution`
- `DomainClassifierOutput`
- `DomainResolution`
- ambiguity/weighted-label/classification-trace primitives
- typed artifacts binding exact `SemanticRecordMetadata`
- `TopicResolutionService`
- `DomainResolutionService`
- `ProjectTopicDomainRepository` adapter over immutable `VersionRepository`

Authority invariants:
- Project domain owns bootstrap/project intent only.
- Topic Intelligence owns normalized topic labels/ambiguity/constraints only.
- Topic != niche.
- Topic resolution has no `ProfileResolver` / `ActiveProductionProfile` input.
- Domain/Niche/Genre Resolution owns topic-derived classification only.
- Domain resolution does not emit the effective BrainPack stack.
- project hard constraints outrank classifier-derived soft preferences.
- unknown niche is explicit.
- hybrid niches are allowed.
- provider/FlowKit-specific fields are forbidden by canonical Pydantic contracts.
- exact topic normalizer/classifier, domain classifier, project input, topic resolution, and registry metadata versions are bound in provenance.
- persistence reuses the generic immutable `VersionRepository`; no parallel truth store is introduced.

Canonical identity verification:
- Master requires `topic_resolution_id/version`.
- Master requires `niche_resolution_id/version`.
- implementation logical prefixes `topic-resolution:` and `niche-resolution:` align with that authority.

## Targeted verification

Python 3.13 local isolated environment:

- compile new module/tests/export surface: PASS
- frozen Master guard: PASS
- targeted IMP-010 tests: **12/12 PASS**

Targeted coverage:
- canonical contracts cannot represent profile dependency/provider state;
- topic normalization + multi-label + explicit ambiguity;
- detected ambiguity cannot be silently omitted;
- unsupported factuality rejected;
- hard project constraints block derived override;
- domain classification obeys hard axis constraints;
- explicit unknown niche + hybrid niche preservation;
- exact topic/registry/classifier rule provenance;
- cross-project topic provenance rejection;
- VersionRepository round trip;
- every canonical classification axis exactly once;
- bootstrap source evidence required.

## Full local unit regression

Unfiltered Windows run:
- **458 PASS / 3 FAIL**

The three failures are the exact pre-existing Windows/POSIX `/tmp` path assertions documented from IMP-001 onward:
- two parameterized `test_claude_agy_providers_include_read_the_images_at` cases;
- `test_single_sheet_wrapper_wording_matches_original_singular_form`.

No IMP-010 test failed.

A separate clean-regression rerun was attempted, but the local bridge/launcher failed before producing completion artifacts. It is not claimed as PASS and is not needed to reinterpret the completed unfiltered result above.

## Static / scope verification

- provider-specific canonical field token scan: none
- `ActiveProductionProfile/ProfileResolver` runtime dependency scan: none
  - the only text occurrence is the module docstring explicitly stating the prohibition
- `git diff --check`: PASS
- frozen Master bytes unchanged
- `_incoming/` remains untracked and excluded

## Local verdict

**IMP-010 = LOCAL VERIFIED**

Remote PR / Ubuntu CI / exact-head review / merge / main verification remain pending.


## Remote / Main verification

Fork PR:
- nguyenkhactang922-bot/flowkit#14

Exact PR head:
- 6dca6a53bc5733aa9cd93cfd0c13ad15e279543e

PR CI:
- workflow run 36225161135
- conclusion: SUCCESS
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

Exact-head review:
- no blocking findings;
- no ProfileResolver/ActiveProductionProfile dependency in Topic contracts;
- provider-specific canonical fields absent;
- hard project constraints outrank soft classifier preferences;
- ambiguity/unknown/hybrid semantics explicit;
- exact project/topic/rule/registry version provenance bound;
- persistence reuses immutable VersionRepository;
- frozen Master bytes unchanged.

Merge:
- main merge commit: ed5fb0ff0aff746b3991c52f32b282fdec7e444a

Local main verification:
- local HEAD = fork/main = ed5fb0ff0aff746b3991c52f32b282fdec7e444a
- frozen guard: PASS
- targeted IMP-010 tests: 12/12 PASS

Fork-main push CI:
- workflow run 36225238363
- Python 3.10 frozen guard + full unit suite: SUCCESS
- Python 3.13 frozen guard + full unit suite: SUCCESS

## Final verdict

IMP-010 = MAIN VERIFIED on nguyenkhactang922-bot/flowkit:main at ed5fb0ff0aff746b3991c52f32b282fdec7e444a.

NEXT_EXACT_ACTION = CLAIM IMP-011 — BRAINPACK REGISTRY
