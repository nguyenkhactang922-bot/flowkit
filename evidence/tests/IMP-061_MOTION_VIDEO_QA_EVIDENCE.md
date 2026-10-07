# IMP-061 Motion / Video QA Evidence

Date: 2026-10-07
Branch: `chatgpt/IMP-061-motion-video-qa`
Base HEAD: `56906ffd2dc4b282a5e8d6802cd939fe1a2b8537`

## Scope

IMP-061 adds provider-neutral, time-bound Motion / Video QA over an actual READY video artifact and exact canonical shot/state/reference lineage. It preserves existing GenerationJob creative-axis authority and artifact lifecycle authority; provider success is not QA success, and Motion QA owns only evaluation evidence/verdict orchestration.

Frozen authority and reviewed invariants enforced by this task:
- QA consumes actual READY `video/*` bytes through the canonical artifact lifecycle rather than treating provider remote success as pass;
- evaluator input binds exact current ShotIR, MotionDeltaSpec, FullShotSpec, StaticKeyframeSpec, StateSnapshot, ActiveProductionProfile and reference lineage;
- Motion findings are time-bound and cover the canonical Motion QA dimensions;
- blocking failed findings cannot be averaged away by an aggregate score;
- evaluator/tool failure is classified through the existing QA_ERROR transition rather than artifact QA_FAILED;
- artifact defects use the existing ARTIFACT_QA_FAILED path;
- evaluator id/version and policy version are persisted in result/provenance;
- visible canonical EntityVersion refs are bound directly in evaluator subject, result provenance and source graph for identity-drift evidence;
- automatic approval is fail-closed by default and only occurs when an explicit versioned policy allows it.

## Implementation surfaces

- `agent/studio/motion_qa.py`
- `agent/studio/__init__.py` exports
- `tests/unit/test_studio_motion_qa.py`

Legacy `agent/services/video_reviewer.py` remains a donor for extraction/time-range ideas only; its weighted score/provider behavior is not canonical Motion QA authority.

## Verified checkpoints

Durable checkpoints already PASS and were not rerun unnecessarily:
- initial targeted Motion QA: **8/8 PASS** via `.tmp/imp061-targeted.xml`;
- exact-head review repair targeted: **8/8 PASS** via `.tmp/imp061-review-targeted.xml`, exit 0;
- affected existing authority regression: **105/105 PASS** via `.tmp/imp061-affected.xml`;
- non-overlapping broader valid Windows regression: **663 PASS / 3 deselected** via `.tmp/imp061-broader-valid.xml`, exit 0;
- Frozen Master guard: **PASS**;
- exact-head static / import / diff / leakage verification: **PASS**.

The first review-targeted command attempt failed before pytest collection because the temporary isolated environment omitted repo requirements. No test case ran and no JUnit was produced. The stage was retried only with the canonical repo dependency command; that corrected run passed 8/8.

## Targeted acceptance proof

The targeted suite verifies the task decomposition acceptance surface, including:
- provider success without a READY local video artifact does not count as QA pass;
- actual `video/mp4` bytes are evaluated through ArtifactLifecycleService materialization;
- findings carry bounded time ranges;
- a blocking motion/continuity/intent defect forces QA failure;
- evaluator failure maps to QA_ERROR;
- non-video artifacts and stale MotionDeltaSpec lineage fail closed;
- result/provenance binds evaluator/policy evidence and canonical source refs;
- direct visible EntityVersion bindings are preserved for identity-drift evidence;
- default policy does not auto-approve.

Review-fix targeted JUnit `.tmp/imp061-review-targeted.xml`:
- tests: **8**
- failures: **0**
- errors: **0**
- skipped: **0**
- final PTY result: **8 passed**, exit 0.

## Affected regression

Existing authority surfaces were verified without rerunning Motion QA targeted tests:
- generation job creative transitions;
- artifact lifecycle;
- shot realization;
- production compiler;
- state continuity;
- reference authority;
- versioning;
- invalidation.

JUnit `.tmp/imp061-affected.xml`:
- tests: **105**
- failures: **0**
- errors: **0**
- skipped: **0**

## Broader valid Windows regression

The established Windows exclusion envelope was retained and all already-PASS IMP-061 targeted/affected files were explicitly ignored to avoid duplicate stage execution.

Command shape used:

```text
uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit -q \
  --ignore=tests/unit/test_studio_generation_job.py \
  --ignore=tests/unit/test_studio_artifact_lifecycle.py \
  --ignore=tests/unit/test_studio_shot_realization.py \
  --ignore=tests/unit/test_studio_production_compiler.py \
  --ignore=tests/unit/test_studio_state_continuity.py \
  --ignore=tests/unit/test_studio_reference.py \
  --ignore=tests/unit/test_studio_versioning.py \
  --ignore=tests/unit/test_studio_invalidation.py \
  --ignore=tests/unit/test_studio_motion_qa.py \
  --ignore=tests/unit/test_setup.py \
  --ignore=tests/unit/test_video_reviewer.py \
  -k "not test_claude_agy_providers_include_read_the_images_at and not test_single_sheet_wrapper_wording_matches_original_singular_form" \
  --basetemp=.tmp/pytest-imp061-broader-valid \
  --junitxml=.tmp/imp061-broader-valid.xml
```

Final JUnit `.tmp/imp061-broader-valid.xml`:
- tests: **663**
- failures: **0**
- errors: **0**
- skipped: **0**

Final PTY result:

```text
663 passed, 3 deselected in 1766.09s (0:29:26)
```

## Frozen baseline verification

`python tools/frozen_master_guard.py`:

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
```

Frozen semantic SHA is unchanged.

## Final static / authority verification

- `python -m py_compile agent/studio/motion_qa.py tests/unit/test_studio_motion_qa.py`: **PASS**;
- `python -m compileall -q agent/studio`: **PASS**;
- public import `MotionQAService`, `MotionQAResult`, `MotionQADimension`: **PASS**;
- `git diff --check`: **PASS**;
- provider/runtime/network leakage scan in `motion_qa.py`: **CLEAN**;
- TODO/NotImplemented scan in IMP-061 implementation: **CLEAN**.

## Verification conclusion

IMP-061 is locally verified for its claimed Motion / Video QA scope. Evidence supports proceeding to Git side-effect guard and exact-scope commit/push/PR lifecycle. This file does not claim merge or MAIN VERIFIED until exact PR-head CI/review/merge and post-merge main verification have completed.
