# IMP-022 — Character Psychology / Relationship / Knowledge Evidence

Date: 2026-09-29

Task: **IMP-022 — Character Psychology / Relationship / Knowledge**

Branch:
`chatgpt/IMP-022-character-state`

Base HEAD:
`67cb0462c4e67f1dad3f02078358a35722e0a95c`

Dependencies:
- IMP-020 = MAIN VERIFIED
- IMP-021 = MAIN VERIFIED
- IMP-040 = MAIN VERIFIED

Frozen Master authority:
`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

Authority read:
- frozen Master §18 Character Psychology
- frozen Master §19 Relationship State
- frozen Master §20 Knowledge / Belief State
- FR-039 Character Psychology
- FR-040 Knowledge/Relationship
- historical V0.16 CharacterModelVersion / CharacterKnowledgeState / RelationshipState contracts
- frozen implementation dependency graph and IMP-022 decomposition

## Implemented scope

New provider-neutral module:
- `agent/studio/character_state.py`

Canonical contracts:
- `CharacterModelVersion`
- `VoiceRegister`
- `RelationshipState`
- `CharacterKnowledgeState`
- `KnowledgeItem`
- `ObjectiveTruth`
- `CharacterEpistemicState`
- `AudienceEpistemicState`
- `CharacterStateArtifact`
- `CharacterStateRepository`

Persistence / authority:
- shared immutable `VersionRepository` only
- exact source-version provenance
- exact-version dependency edges through `DependencyGraphRepository`
- no second canonical Entity store
- no visual/reference/provider fields in dramatic state
- semantic successors preserve accepted history
- current-pointer mutation remains CAS-controlled by VersionRepository

## Character Psychology

`CharacterModelVersion` binds:
- exact canonical `EntityVersion`
- exact `ActiveProductionProfile`
- exact StoryCore when available
- canonical early-story intake refs for pre-core construction
- exact StoryMaterial refs
- optional exact RelationshipState context

Psychology includes:
- role
- external want
- internal need
- fear
- formative pressure
- mistaken belief
- values
- contradictions
- strengths
- flaws/defenses
- secrets
- social/private self
- preferred tactics
- boundaries
- decision style
- voice registers
- arc hypothesis

Two-phase cycle-safe rule:
- pre-StoryCore psychology may be persisted only as DRAFT;
- promotion to APPROVED requires an exact current StoryCore binding;
- after StoryCore draft exists, a successor CharacterModelVersion binds that exact StoryCore and may pass the promotion gate;
- no second StoryCore identity is created.

This implements IMP-022 before IMP-023 without bypassing the frozen Master ordering rule.

## Relationship State

`RelationshipState`:
- derives one stable logical identity from project + canonical participant identities;
- participant order is normalized;
- semantic versions may bind newer EntityVersion versions without changing relationship identity;
- every state has causal/baseline evidence;
- non-initial state requires exact predecessor, exact +1 chronology and delta summary;
- claims cannot silently reset between story times.

## Knowledge / Belief State

`KnowledgeItem` separates:
- objective truth
- objective evidence
- character acquisition evidence
- inference basis
- character epistemic state: KNOWS / BELIEVES / SUSPECTS / MISUNDERSTANDS / UNKNOWN
- audience epistemic state

Hard gates:
- KNOWS requires objective truth TRUE and acquisition evidence;
- known objective truth requires exact objective evidence;
- BELIEVES / SUSPECTS require acquisition or inference basis;
- MISUNDERSTANDS cannot masquerade as objective truth and requires evidence/basis;
- UNKNOWN cannot carry character acquisition/inference evidence;
- audience KNOWS requires exact evidence;
- stale objective/acquisition/inference versions fail promotion.

`CharacterKnowledgeState`:
- has stable character identity;
- explicit story-time ordinal;
- non-initial state requires exact predecessor and causal change event;
- successor chronology advances exactly one step.

## Durable invalidation

Every exact source binding is registered in the existing durable DependencyGraph.
Duplicate semantic roles pointing at the same exact source are coalesced into one
edge while retaining combined dependency reason.

Test proof:
- changing canonical EntityVersion from v1 → v2 produces a durable
  InvalidationRecord affecting the exact dependent RelationshipState version.

## Tests

### Targeted IMP-022

Command:

`PYTHONUTF8=1 uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_character_state.py -q`

Result:

```text
11 passed in 1.55s
```

Coverage includes:
- pre-core psychology DRAFT gate;
- StoryCore-bound psychology successor promotion;
- visual/provider authority separation;
- stable relationship identity;
- relationship causal chronology;
- skipped chronology rejection;
- impossible knowledge rejection;
- false KNOWS rejection;
- objective-vs-belief/audience separation;
- knowledge chronology;
- stale objective evidence rejection;
- stale EntityVersion rejection;
- durable dependency invalidation;
- cross-project EntityVersion rejection;
- order-independent relationship identity.

### Affected regression cluster

Command covers:
- IMP-022 character state
- EntityVersion
- VersionRepository
- dependency invalidation
- Research/StoryMaterial
- Story Intake

Result:

```text
60 passed in 4.78s
```

### Largest valid local unaffected regression

The unfiltered Windows run was environment-blocked in two pre-existing areas:
1. this FileMCP execution environment has no `ffmpeg` executable on PATH, so
   `tests/unit/test_video_reviewer.py` cannot create its synthetic fixture;
2. the same three pre-existing Windows/POSIX path assertions in
   `tests/unit/test_cli_providers.py` still expect `/tmp` while Windows renders
   `\\tmp`.

IMP-022 does not touch those surfaces.

Command excluded only the environment-blocked video-reviewer module plus the
three exact known POSIX-path cases.

Result:

```text
509 passed, 3 deselected in 11.22s
```

Ubuntu CI remains the full dependency-complete gate because the workflow installs ffmpeg.

### Static / baseline checks

```text
python -m compileall -q agent/studio/character_state.py agent/studio/__init__.py
PASS

git diff --check
PASS

FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
NEWLINE_NORMALIZED=CRLF_TO_LF
```

Provider/visual token scan of the new canonical module found no:
- provider_id/provider_name/model_id/model_key/remote_job_id
- media_id/reference_image_url/image_prompt

## Local verdict

**IMP-022 = LOCAL VERIFIED**

This is not MAIN VERIFIED yet. Commit, push, PR, Ubuntu CI, exact-head review,
merge and main verification remain required.


## Exact-head review finding and repair

Review of initial PR head
`3d14a9d1a4d47e73a311630f5c23d390a7514854`
found three hardening gaps before merge:

1. objective evidence refs in KnowledgeItem were proven to exist but were not
   rechecked as exact-current accepted versions at promotion;
2. character-specific psychology/knowledge gates validated canonical EntityVersion
   identity/project linkage but did not explicitly reject non-CHARACTER EntityKind;
3. missing exact sources were detected only after the semantic version insert,
   which could leave a recoverable but avoidable DRAFT if dependency-edge
   materialization then failed.

Repair:
- objective evidence, acquisition evidence and inference basis are all exact-current
  gated at promotion;
- CharacterModelVersion and CharacterKnowledgeState require EntityKind.CHARACTER;
  RelationshipState remains allowed to relate canonical dramatic entities;
- all declared source versions are preflighted before semantic version persistence;
- durable dependency-edge registration remains fail-closed before promotion.

Post-repair verification:
- targeted IMP-022 = **11/11 PASS**
- affected regression cluster = **60/60 PASS**
- largest valid local unaffected regression = **509 PASS / 3 deselected**
- compile = PASS
- frozen Master guard = PASS
- git diff --check = PASS

No blocking review finding remains locally. Updated PR head must rerun Ubuntu CI.
