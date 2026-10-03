# IMP-028 NarrativeTrace Evidence

Date: 2026-10-03
Branch: `chatgpt/IMP-028-narrative-trace`
Base main: `229ccfb227e748f594fb1f9e8d53040095910c9e`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Source-of-truth resume

- Restored repo root: `E:\FlowKit-Studio-Upgrade`.
- Git main at bootstrap: `229ccfb227e748f594fb1f9e8d53040095910c9e`.
- PR #39 verified `MERGED`; merge commit is the same main SHA.
- No active IMP-028 test/build process existed.
- No remote `chatgpt/IMP-028-narrative-trace` branch existed before claim.
- Therefore stale state text asking to commit/push/merge IMP-027 governance was not retried.

## Frozen authority implemented

IMP-028 implements frozen Master §62A without creating a second narrative truth store:

- immutable `NarrativeTraceRecord` versions stored through shared `VersionRepository`;
- stable trace logical identity + explicit `trace_version`;
- exact traced/root/parent/source version bindings and exact provenance;
- structural parent rules for StoryCore → MacroStoryBeat → Sequence → Scene → SceneDramaticBeat → ShotListItem;
- reverse and forward traversal through the existing `DependencyGraphRepository`;
- bottom-up `why_exists` query;
- `TRACE_MISSING_PARENT`, `TRACE_ORPHAN_ARTIFACT`, `TRACE_CYCLE`, stale-source, and contradictory-parent fail-closed gates;
- cycle detection is explicit DFS because the generic dependency reachability traversal intentionally suppresses revisits rather than reporting cycles;
- NarrativeTrace registers `narrative_trace_source` exact-version dependency edges so §63 durable invalidation can reach trace evidence;
- source supersession derives `INVALIDATED` trace state while historical trace versions remain auditable;
- no provider/network/camera/lens/lighting/runtime authority was introduced.

## Targeted verification

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_narrative_trace.py -q
```

Final result:

```text
13 passed in 2.16s
exit code 0
```

Coverage includes:

- project-prefix collision rejection;
- exact top-down and bottom-up traversal;
- why-exists explanation;
- multiple exact MacroStoryBeat parents for Sequence;
- `TRACE_MISSING_PARENT`;
- `TRACE_ORPHAN_ARTIFACT`;
- contradictory parent graph truth;
- `TRACE_CYCLE`;
- stale exact source fail-closed;
- source supersession → `INVALIDATED` state;
- durable §63 invalidation propagation through `narrative_trace_source` edge;
- immutable trace successor / `SUPERSEDED` prior trace;
- exact provenance binding;
- StoryCore canonical-parent rejection.

## Affected regression

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_versioning.py tests/unit/test_studio_invalidation.py tests/unit/test_studio_story_core.py tests/unit/test_studio_structure_planning.py tests/unit/test_studio_narrative_hierarchy.py tests/unit/test_studio_screenplay_realization.py tests/unit/test_studio_story_quality.py tests/unit/test_studio_narrative_trace.py -q
```

Final result:

```text
98 passed in 22.02s
exit code 0
```

## Broader Windows regression

The first broad run exposed pre-existing Windows-codepage failures in `tests/unit/test_setup.py`: fixture files containing an em dash were written as byte `0x97` by the Windows default encoding and then read explicitly as UTF-8. Result:

```text
3 failed, 582 passed, 3 deselected, 7 errors
```

No IMP-028 change touches `setup.py`, `tests/unit/test_setup.py`, or `skills/`; `git diff -- setup.py tests/unit/test_setup.py skills` is empty.

Largest valid unaffected Windows regression:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit -q --ignore=tests/unit/test_video_reviewer.py --ignore=tests/unit/test_setup.py -k "not test_claude_agy_providers_include_read_the_images_at and not test_single_sheet_wrapper_wording_matches_original_singular_form"
```

Final result:

```text
580 passed, 3 deselected in 32.13s
exit code 0
```

The repository PR CI runs the full unit suite on Ubuntu/Python 3.10 and 3.13, so the complete cross-platform gate remains mandatory before merge.

## Frozen Master / static / diff checks

Final checks:

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
python -m compileall ... = PASS
git diff --check = PASS
FORBIDDEN_RUNTIME_IMPORT=NONE
out-of-scope setup/skills diff = empty
```

## Exact-head review finding repaired before commit

Review found that the initial implementation read shared DependencyGraph lineage but did not register dependencies from exact trace sources to the trace record. That would prevent §63 invalidation from reaching trace evidence. Repair:

- register grouped exact-source → trace edges with `edge_type = narrative_trace_source`;
- keep canonical traversal clean by filtering traversal results to canonical narrative artifact types;
- verify durable invalidation records include the trace version after source supersession.

All targeted, affected, broader-unaffected, frozen, compile and diff checks were rerun after this repair.

## Local verdict

`IMP-028 = LOCAL VERIFIED`

Remote PR CI / exact-head review / merge / final main verification remain required before `MAIN VERIFIED`.

NEXT_EXACT_ACTION = `SIDE-EFFECT GUARD -> COMMIT IMP-028 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE -> VERIFY MAIN`


### PR exact-head review hardening

PR #40 exact-head review found a transitive invalidation gap: a trace could remain `CURRENT` when an ancestor version change produced a durable unresolved §63 `InvalidationRecord` for that trace while all direct source pointers were still current. The repository now consults durable unresolved invalidation records in `trace_state()`. Added a transitive MacroStoryBeat → Sequence → Scene → NarrativeTrace test. Post-fix verification: targeted 13/13 PASS, affected 98/98 PASS, broader unaffected Windows 580 PASS / 3 deselected, frozen guard PASS.
