# IMP-030 — Audience / Directing / Spatial / Blocking / Cinematography Evidence

Date: 2026-10-03
Branch: `chatgpt/IMP-030-directing-spatial-cinematography`
Base main: `6ecc99275fe953f65fb1c7f64158e5f438d655a8`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Authority implemented

- `AudienceExperienceTarget` is beat-scoped viewer-effect authority and binds exact current `SceneDramaticBeat` + CURRENT `NarrativeTrace`.
- `DirectingIntent` is beat-scoped performance/reveal/staging authority and requires exact LOCKED `ScriptLock`, `AudienceExperienceTarget`, canonical Scene participation, performance-state lineage and pinned LOCKED `ActiveProductionProfile`.
- `SceneSpatialDramaticContract` is scene-scoped spatial baseline from exact Scene + Beat set + approved/propagatable `StateSnapshot`; it owns zones/anchors/sightlines/dramatic constraints, never camera authority.
- Spatial participants must be canonical Scene participants. Entity-backed anchors must be authorized by the canonical Scene or exact approved StateSnapshot. `location_entity_ref`, when used, must be a canonical `LOCATION` EntityVersion.
- `BlockingPlan` owns actor/object spatial execution and may only move entities declared by the exact `SceneSpatialDramaticContract`.
- `CinematographyObjective` is provider-neutral visual-language translation and requires exact Audience + Directing + Spatial + Blocking + Profile authority; visual decisions carry exact decision-basis refs and cannot self-author narrative intent.
- ActiveProductionProfile dependencies use `PROFILE_PATH:*` edges so existing path-selective invalidation remains effective.
- Revisions create immutable successors, exact dependency edges and durable dependency-reachable invalidation before current-pointer CAS.
- Existing FlowKit prompt/camera/provider runtime remains downstream compatibility only; no runtime/provider transport import enters canonical directing authority.

## Review hardening

Independent exact review caught and fixed authority gaps that tests initially did not expose:

1. same-project ActorDirection/performance-state entities were required to be declared by canonical Scene;
2. spatial participants were required to be declared by canonical Scene;
3. Blocking entities were required to be declared by the exact SpatialContract;
4. entity-backed Spatial anchors were required to come from canonical Scene or approved StateSnapshot;
5. `location_entity_ref` was constrained to canonical `EntityKind.LOCATION`.

These fixes prevent directing/spatial/camera layers from inventing upstream participants, props or locations merely because an EntityVersion exists in the same project.

## Targeted verification

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_directing.py -q
```

Final result after review hardening:

```text
18 passed in 12.32s
exit code 0
```

Coverage includes exact narrative trace, ScriptLock/profile lineage, approved State propagation, camera hard-gate bypass negatives, Scene participant authority, Spatial anchor/location authority, Blocking ownership, exact provenance/dependency edges, revision/CAS/invalidation behavior and non-self-originating cinematography decision basis.

## Affected regression

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_versioning.py tests/unit/test_studio_invalidation.py tests/unit/test_studio_active_profile.py tests/unit/test_studio_entity.py tests/unit/test_studio_character_state.py tests/unit/test_studio_narrative_hierarchy.py tests/unit/test_studio_narrative_trace.py tests/unit/test_studio_story_quality.py tests/unit/test_studio_state_continuity.py tests/unit/test_studio_directing.py -q
```

Final result:

```text
117 passed in 36.19s
exit code 0
```

## Broader Windows regression

Known repository Windows-only exclusions remain unchanged (`tests/unit/test_setup.py`, `tests/unit/test_video_reviewer.py` and two pre-existing platform-specific selections). Largest valid unaffected regression:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit -q --ignore=tests/unit/test_video_reviewer.py --ignore=tests/unit/test_setup.py -k "not test_claude_agy_providers_include_read_the_images_at and not test_single_sheet_wrapper_wording_matches_original_singular_form"
```

Final result:

```text
627 passed, 3 deselected in 71.55s
exit code 0
```

Full Ubuntu Python 3.10/3.13 CI remains mandatory at PR exact head before merge.

## Frozen/static gates

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
compileall=PASS
git diff --check=PASS
forbidden runtime/provider imports=NONE
TODO/FIXME/NotImplemented=NONE
```

## Local decision

IMP-030 is **LOCAL VERIFIED**. Git side effects remain gated by duplicate checks, PR exact-head Ubuntu CI, exact-head review, merge verification and post-merge main verification.


## Main verification

Feature commit `e6ff93f23550d4f650ac3461410f974e56fdfcc6` merged via PR #46 as main merge commit `3dc15e029d6cfb2e3736ee443a72cbbda504c726`.

- PR CI run `37111493909`: Python 3.10 SUCCESS, Python 3.13 SUCCESS, exact feature head.
- Post-merge frozen Master guard: PASS, semantic SHA unchanged.
- Post-merge targeted: `18 passed`.
- Post-merge affected regression: `117 passed`.
- Main push workflow `37111589949`: SUCCESS on exact merge SHA.

IMP-030 feature implementation is **MAIN VERIFIED**. Governance-only state synchronization remains separate from feature authority/code.
