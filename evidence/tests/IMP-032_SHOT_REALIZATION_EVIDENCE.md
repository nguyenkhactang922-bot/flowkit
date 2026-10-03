# IMP-032 Shot Eligibility / Full Shot Realization Verification Evidence

Date: 2026-10-03
Task: IMP-032 — ShotEligibilityGate / FullShotSpec / StaticKeyframeSpec / MotionDeltaSpec / ShotDecisionTrace
Branch: `chatgpt/IMP-032-shot-eligibility-fullshotspec`
Base main: `f7ec86c9392be24185d23893cd8b513e281f1c52`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Authority implemented

- `ShotListItem` remains the sole canonical `shot_id` origin; IMP-032 never allocates or rekeys Shot identity.
- `ShotEligibilityGate` is immutable exact-input gate evidence; only exact-current `ELIGIBLE` evidence can authorize `FullShotSpec`.
- Gate evidence binds exact ShotListItem, current Shot NarrativeTrace, ShotListManifest, ActiveProductionProfile, directing/spatial/blocking/cinematography authority, approved StateSnapshot/designation, required reference entities, selected exact ReferenceAssets/content hashes, full ReferenceResolutionTrace hash, and exact eligibility-rule version.
- Required reference/capability preflight evidence is included in the evaluated-input hash; selected references alone cannot make two different preflights appear identical.
- Eligibility rule version is a durable dependency edge. Rule successor/version change selectively invalidates dependent gate evidence and stale rule-bound eligibility cannot authorize new realization.
- ReferenceResolver binding is completed before eligibility promotion; interrupted binding leaves a DRAFT gate and exact replay can recover without fabricating accepted evidence.
- `FullShotSpec` realizes the same shot identity and stores exactly eight semantic layers: L1 SUBJECT, L2 STATE/WARDROBE, L3 ACTION/PERFORMANCE, L4 ENVIRONMENT, L5 TIME/ATMOSPHERE, L6 CAMERA, L7 LIGHTING/STYLE, L8 CONTINUITY.
- Every FullShotSpec semantic field carries FIXED/INHERITED/VARIABLE authority classification plus exact source refs.
- `StaticKeyframeSpec` contains static observable start/keyframe state only.
- `MotionDeltaSpec` contains temporal change only and cannot redefine the static start state.
- `ShotDecisionTrace` is immutable explainability evidence bound to exact FullShotSpec/eligibility/shot authority; generic `cinematic` rationale is rejected.
- Shared `VersionRepository`, `DependencyGraphRepository`, `InvalidationRepository`, `StateSnapshotRepository`, `NarrativeTraceRepository`, `ReferenceResolver`, `DirectingAuthorityRepository`, and `ShotPlanningRepository` remain canonical authority; no shadow truth store was created.
- Canonical transaction contains no provider/runtime/network side effect or provider request syntax.

## Stream-disconnect recovery evidence

On resume, an existing process was found and was not restarted:

```text
uv run --isolated --no-project --python 3.13 ... pytest tests/unit/test_studio_shot_planning.py tests/unit/test_studio_shot_realization.py -q
```

The existing pytest CPU continued increasing, so the task was classified `RUNNING` and monitored. After it exited, no durable stdout/exit/result marker existed; only `.pytest_cache/nodeids` changed and old unrelated `lastfailed` data remained. Per project law that run was classified `INTERRUPTED/UNKNOWN`, not PASS. The last durable checkpoint remained targeted PASS, so execution resumed at affected regression only.

## Targeted tests — final exact local head

Command:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_shot_realization.py -q
```

Final result after exact-head self-review hardening:

```text
15 passed in 52.57s
```

Coverage includes:
- same canonical shot_id through detailed realization and FullShotSpec revision;
- exact L1-L8 only / no invented semantic L9-L12;
- rejected gate persists evidence but cannot authorize FullShotSpec;
- missing required reference becomes blocking rejection;
- exact reference successor invalidates gate and blocks stale realization;
- exact eligibility-rule successor invalidates gate and blocks stale realization;
- StaticKeyframeSpec / MotionDeltaSpec separation;
- ShotDecisionTrace exact layer coverage and non-generic rationale;
- field-level camera authority cannot self-originate outside declared sources;
- exact gate replay idempotency/conflict rejection;
- reference-binding interruption leaves DRAFT and exact retry recovers;
- gate re-evaluation selectively invalidates existing realization descendants;
- ReferenceResolutionTrace requirement/capability evidence participates in the gate hash.

## Affected regression — final exact local head

Affected direct-authority regression was executed in bounded batches to preserve explicit exit evidence:

```text
77 passed in 10.47s
60 passed in 20.43s
17 passed in 31.98s
```

Aggregate:

```text
154 passed
```

Scope covers primitives/persistence/versioning/invalidation/ActiveProductionProfile/entity/reference, character/state continuity, NarrativeTrace, directing authority, and ShotPlanning. Targeted IMP-032 tests are recorded separately above and were not redundantly counted in the 154.

## Broader valid Windows regression — final exact local head

Same established exclusion envelope as prior MAIN VERIFIED tasks:

- ignore `tests/unit/test_video_reviewer.py`;
- ignore `tests/unit/test_setup.py`;
- deselect `test_claude_agy_providers_include_read_the_images_at`;
- deselect `test_single_sheet_wrapper_wording_matches_original_singular_form`.

The suite was split into bounded batches only to stay inside the execution-bridge 120-second call limit; coverage/exclusions were not weakened.

Final batches:

```text
347 passed, 3 deselected in 2.92s
91 passed in 21.71s
111 passed in 38.56s
48 passed in 60.07s
62 passed in 9.47s
```

Aggregate:

```text
659 passed, 3 deselected
```

This is exactly +15 PASS versus the IMP-031 review-fix baseline `644 passed, 3 deselected`, matching the 15 IMP-032 targeted tests.

## Frozen / static gates — final exact local head

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
```

Additional checks:
- `python -m compileall -q agent/studio/shot_realization.py agent/studio/__init__.py tests/unit/test_studio_shot_realization.py` = PASS;
- `git diff --check` = PASS;
- provider/runtime/network import leakage scan = NONE;
- TODO/FIXME/NotImplemented scan = NONE.

## Exact-head self-review repairs before commit

1. Reused the same canonical ActiveProductionProfile payload/current validation pattern as IMP-031 instead of depending on fixture-specific `ActiveProductionProfileArtifact` metadata reconstruction.
2. Preserved strict gate input-hash validation while fixing the gate factory to construct only a temporary internal pre-hash object, compute the exact hash, then fully validate the canonical gate.
3. Persisted required-reference entity refs plus the complete ReferenceResolutionTrace hash so requirement/capability preflight evidence is not collapsed into selected-reference-only evidence.
4. Added exact eligibility-rule version to ShotEligibilityGate dependency bindings after Frozen §49 review showed rule/version changes must invalidate prior eligibility; added a rule-successor invalidation test.
5. Confirmed ShotDecisionTrace dependency registration includes exact decision-source authority, not only shot/spec/gate refs.

## Verdict

`IMP-032 = LOCAL VERIFIED`

Next: side-effect guard → stage exact IMP-032 scope → commit → push → PR → Ubuntu CI Python 3.10/3.13 → exact-head review → merge main → post-merge verification → governance sync → MAIN VERIFIED → claim next dependency-ready task.


## Feature MAIN VERIFIED — 2026-10-03

- feature PR: #50
- exact final PR head: `78464d03f5dc2a537ddbcce470a59cce71404a1f`
- implementation commit: `6e96978bc9596bc4838492532dacabc7c56f1a53`
- PR checkpoint state commit: `78464d03f5dc2a537ddbcce470a59cce71404a1f`
- PR CI run: `37138187600` SUCCESS on Python 3.10 and 3.13, including frozen Master verification
- exact merge SHA: `bd9ac71117912e5f1f4771eaf2cf128dcb5739a8`
- post-merge targeted: `15 passed in 63.22s`
- post-merge affected regression: `154 passed` (`77 + 60 + 17`)
- post-merge frozen Master guard: PASS, semantic SHA unchanged `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`
- push-main workflow: `37138380626` SUCCESS on exact merge SHA, Python 3.10 and 3.13

`IMP-032 feature implementation = MAIN VERIFIED`

Next: governance-only state sync -> governance PR/CI/merge -> verify governance main -> read DAG/queue -> claim next dependency-ready task.
