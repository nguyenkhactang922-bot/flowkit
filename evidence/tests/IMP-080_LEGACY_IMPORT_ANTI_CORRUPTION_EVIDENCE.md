# IMP-080 Legacy Import Anti-Corruption Evidence

Date: 2026-10-11
Branch: `chatgpt/IMP-080-legacy-import-anti-corruption`
Base main SHA: `35823eeafbf6f0f8a6c6354b9d874d346d432247`

## Scope

IMP-080 adds a bounded, auditable legacy-import anti-corruption boundary without allowing legacy operational data to mint canonical cinematic/story truth.

Frozen authority enforced by this task:
- `Project.story` is seed-only evidence, not canonical Story truth;
- legacy Entity migration delegates to the existing canonical Entity adapter rather than creating a second entity owner;
- operational legacy Scene rows are compatibility/lineage evidence only;
- prompt, image-prompt, video-prompt, narrator prose, display order, chain metadata, media IDs/URLs and provider IDs are derivative evidence and cannot create `Scene`, `SceneDramaticBeat`, `FullShotSpec`, `ShotIR` or other canonical creative truth;
- canonical shot compatibility mapping requires explicit exact-current proof owned by `ShotPlanningRepository`;
- GenerationJob compatibility proof requires the existing canonical job identity plus exact revision/project lineage;
- missing, stale, dangling, forbidden, ambiguous or otherwise unprovable mappings persist explicit `NOT_PROVABLE` findings rather than fabricated target truth;
- durable import evidence stores normalized/digested source facts, rule version, explicit target proof and findings; raw legacy prompt/prose is not promoted to canonical truth.

## Implementation surfaces

- `agent/studio/legacy_import.py`
- `agent/studio/__init__.py` public exports
- `tests/unit/test_studio_legacy_import.py`

No frozen Master, canonical Story/Scene/Shot/State owner, provider adapter, scheduler or artifact lifecycle authority was modified.

## Exact-head review hardening

Two authority/reliability fixes were applied before final verification:

1. **Owner-proof hardening** — a fake generic semantic row whose logical ID merely starts with `shot-list-item:` is no longer sufficient proof. Shot compatibility proof is materialized through the canonical `ShotPlanningRepository`; prefix-only fake rows are rejected as `NOT_PROVABLE`.
2. **Strict durable serialization** — legacy rows must round-trip through deterministic JSON serialization. Opaque runtime objects can no longer be stringified into durable import evidence. Invalid/unserializable rows fail closed.

Because implementation/test bytes changed after earlier green checkpoints, the final exact-head verification chain revalidated only the affected stages required by the law. Earlier green results remain historical evidence, not proof for the changed head.

## Final targeted verification

Final-review JUnit `.tmp/imp080-final-review-targeted.xml`:
- tests: **9**
- failures: **0**
- errors: **0**
- skipped: **0**
- PTY exit: **0**
- pytest summary: `9 passed in 64.19s`

The targeted suite proves:
- prompt/prose non-authority;
- forbidden creative target rejection;
- canonical ShotListItem proof must come through the owning ShotPlanning repository;
- explicit GenerationJob proof requires exact revision/project lineage;
- stale/dangling proof fails closed;
- `Project.story` remains seed-only;
- deterministic replay/provenance binding;
- opaque non-JSON runtime values are rejected instead of silently stringified.

## Final affected-owner regression

Final-review JUnit `.tmp/imp080-final-review-affected.xml`:
- tests: **72**
- failures: **0**
- errors: **0**
- skipped: **0**
- PTY exit: **0**
- pytest summary: `72 passed in 482.25s`

Affected regression covered the reused canonical owners without rerunning IMP-080 targeted tests:
- Entity;
- ShotPlanning;
- GenerationJob;
- VersionRepository;
- DependencyGraph/Invalidation;
- Persistence.

## Final broader valid Windows regression

Final-review JUnit `.tmp/imp080-final-review-broader-valid.xml`:
- tests: **738**
- failures: **0**
- errors: **0**
- skipped: **0**
- JUnit time: **2872.710s**
- PTY exit: **0**
- pytest summary: `738 passed, 3 deselected in 2876.88s (0:47:56)`

The command used the established Windows-valid envelope:
- excluded IMP-080 targeted and the six affected owner suites already proven PASS;
- excluded `test_setup.py` and `test_video_reviewer.py` as established platform/out-of-scope exclusions;
- deselected the three established POSIX-path assertions;
- ran with `PYTHONUTF8=1`.

This broader suite is PASS; the three deselections are explicit envelope exclusions and are not relabeled failures.

## Frozen baseline verification

`python tools/frozen_master_guard.py`:

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
RAW_SHA256=abb08e8114be3ace0d81ceccf8a3dea45c78a6268c64fae4c332d0644fa1e303
```

Frozen semantic SHA is unchanged.

## Final static / authority verification

- `python -m py_compile agent/studio/legacy_import.py tests/unit/test_studio_legacy_import.py`: **PASS**;
- `python -m compileall -q agent/studio/legacy_import.py tests/unit/test_studio_legacy_import.py`: **PASS**;
- canonical public import through isolated `uv` Python 3.13: **PASS** (`LegacyImportAntiCorruptionService`);
- `git diff --check`: **PASS**;
- provider/network/runtime leakage scan in `legacy_import.py`: **CLEAN**;
- TODO/FIXME/NotImplemented scan in the implementation: **CLEAN**.

A prior public-import probe used the nonexistent name `LegacyImportService`; that was a probe-name mistake only. The canonical exported service is `LegacyImportAntiCorruptionService`; no code was changed and no test checkpoint was invalidated by correcting the probe.

## Verification conclusion

`IMP-080 LOCAL VERIFIED` for the current worktree and claimed Legacy Import Anti-Corruption scope. Evidence supports proceeding to exact Git side-effect guard, exact-scope commit, PR exact-head CI/review, merge and post-merge MAIN verification. This file does not claim merge or MAIN VERIFIED.
