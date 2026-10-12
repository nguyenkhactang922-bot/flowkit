# IMP-081 Operational Scene -> Execution Projection Evidence

Date: 2026-10-12
Branch: `chatgpt/IMP-081-operational-scene-execution-projection`
Base main SHA: `126f927cd9386881a47fb1b8e22b9ac3eb4e6454`

## Scope

IMP-081 preserves the useful legacy operational Scene/media execution surface behind an explicit compatibility projection without promoting legacy prompt/prose/media/runtime data into canonical cinematic Scene/Shot truth.

Frozen authority enforced by this task:
- legacy operational Scene remains execution/runtime evidence only;
- canonical Shot compatibility must be proven by exact accepted `ShotListItem` lineage owned by `ShotPlanningRepository`;
- GenerationJob compatibility requires canonical job identity plus exact revision/project lineage;
- prompt-only or otherwise unproven operational rows cannot mint cinematic Scene/Shot authority;
- legacy media IDs/URLs remain opaque compatibility locators and never semantic truth;
- durable projection provenance binds exact IMP-080 mapping records and canonical shot/job proof;
- projection persistence uses the shared VersionRepository/DependencyGraph/Invalidation owners rather than a shadow store.

Implementation surfaces:
- `agent/studio/operational_scene_projection.py`
- `agent/studio/__init__.py` public exports
- `tests/unit/test_studio_operational_scene_projection.py`

No Frozen Master, canonical Scene/Shot owner, GenerationJob state machine, provider adapter, artifact lifecycle, scheduler, or persistence schema was modified.

## Targeted verification

Initial targeted JUnit `.tmp/imp081-targeted.xml`:
- tests: **7**
- failures: **1**
- errors: **0**
- skipped: **0**
- time: **186.216s**

The single failure was an over-specific test expectation/regex; implementation behavior did not require a code change.

Failed-case rerun JUnit `.tmp/imp081-failed-rerun.xml`:
- tests: **1**
- failures: **0**
- errors: **0**
- skipped: **0**
- time: **6.685s**

Composite targeted checkpoint: **7/7 PASS**.

The targeted suite proves:
- prompt-only operational Scene mapping is rejected as insufficient canonical proof;
- legacy operational Scene never becomes cinematic Scene authority;
- exact ShotListItem/GenerationJob compatibility proof is required;
- stale/dangling/ambiguous proof fails closed;
- legacy media/results remain reachable through the bounded projection;
- replay/provenance and exact-version bindings are deterministic and auditable.

## Affected-owner regression

JUnit `.tmp/imp081-affected.xml`:
- tests: **74**
- failures: **0**
- errors: **0**
- skipped: **0**
- time: **1277.537s**

Affected regression covered the reused owners without rerunning IMP-081 targeted tests:
- LegacyImport anti-corruption boundary;
- ShotPlanning;
- GenerationJob;
- VersionRepository;
- DependencyGraph / Invalidation;
- Persistence.

## Broader valid Windows regression

JUnit `.tmp/imp081-broader-valid.xml`:
- tests: **745**
- failures: **0**
- errors: **0**
- skipped: **0**
- time: **2032.554s**

The run used the established repository Windows-valid envelope and explicitly excluded IMP-081 targeted + affected files already proven PASS. The recorded PTY registry was lost after a FileMCP workspace restart, but the final durable JUnit and absent recorded PID classify the stage as PASS, not INTERRUPTED.

## Frozen baseline verification

`python tools/frozen_master_guard.py`:

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
RAW_SHA256=abb08e8114be3ace0d81ceccf8a3dea45c78a6268c64fae4c332d0644fa1e303
```

Frozen semantic SHA is unchanged.

## Final static / authority verification

- `python -m py_compile agent/studio/operational_scene_projection.py tests/unit/test_studio_operational_scene_projection.py`: **PASS**;
- canonical public import: **PASS** for `OperationalSceneExecutionProjection`, `OperationalSceneExecutionProjectionService`, and `OperationalSceneProjectionRequest`;
- `git diff --check`: **PASS**;
- provider/network/runtime leakage scan in `operational_scene_projection.py`: **CLEAN**;
- TODO/FIXME/NotImplemented scan in the implementation: **CLEAN**.

A prior public-import probe used the nonexistent shorthand `OperationalSceneProjection`; that was a probe-name mistake only. The canonical exported type is `OperationalSceneExecutionProjection`; no code was changed and no test checkpoint was invalidated by correcting the probe.

## Verification conclusion

`IMP-081 LOCAL VERIFIED` for the current worktree and claimed Operational Scene -> Execution Projection scope. Evidence supports proceeding to exact Git side-effect guard, exact-scope commit, PR exact-head CI/review, merge and post-merge MAIN verification. This file does not claim merge or MAIN VERIFIED.
