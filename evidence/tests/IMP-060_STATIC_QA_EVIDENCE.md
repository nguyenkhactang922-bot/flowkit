# IMP-060 Static QA Evidence

Date: 2026-10-07
Branch: `chatgpt/IMP-060-static-qa`
Base HEAD: `71e4a36ae79472daf6ceb3faed3a3e248638b510`

## Scope

IMP-060 adds provider-neutral Static QA over an actual READY image artifact and canonical shot/state/reference expectations. It preserves existing GenerationJob creative authority and artifact lifecycle authority; Static QA records QA evidence and cannot silently create provider/runtime authority or average away blocking defects.

Frozen authority and reviewed policy requirements enforced by this task:
- Static QA consumes exact current canonical inputs, including loaded ShotIR + `qa_expectations`, FullShotSpec / StaticKeyframeSpec lineage, StateSnapshot lineage, ActiveProductionProfile and ReferenceAsset / resolution lineage;
- finding provenance binds the canonical source refs used by each finding;
- evaluator response identity/version must match the evaluator port identity/version;
- evaluator version, policy version and finding evidence are persisted in QA provenance;
- any BLOCKING failed finding forces overall QA failure independent of aggregate score;
- evaluator failure is classified as QA_ERROR rather than artifact QA_FAILED;
- automatic approval is fail-closed by default and requires an explicit versioned policy to enable it.

## Implementation surfaces

- `agent/studio/static_qa.py`
- `agent/studio/__init__.py` exports
- `tests/unit/test_studio_static_qa.py`

The implementation is intentionally provider-neutral and does not submit provider/network work.

## Verified checkpoints

Durable checkpoints already PASS and not rerun unnecessarily:
- initial targeted effective checkpoint: **7/7 PASS**;
- affected existing regression: **105/105 PASS** via `.tmp/imp060-affected.xml`;
- exact-head review repair targeted: **9/9 PASS** via `.tmp/imp060-review-targeted.xml`, exit 0;
- exact-head static/diff review: **PASS**;
- non-overlapping broader valid Windows regression: **654 PASS / 3 deselected** via `.tmp/imp060-broader-valid.xml`, exit 0;
- Frozen Master guard: **PASS**.

## Exact-head review repair proof

The review repair closed only the Static QA gaps found on the current head:
- evaluator receives the exact loaded ShotIR and `qa_expectations`, not only a reference;
- QA lineage pins exact ShotIR/static/full/state/profile/reference versions;
- ActiveProductionProfile and finding-level canonical source bindings are direct provenance;
- evaluator id/version response mismatch fails closed;
- evaluator/policy/finding evidence is present in provenance;
- default auto-approval is disabled/fail-closed.

Review-fix targeted JUnit `.tmp/imp060-review-targeted.xml`:
- tests: **9**
- failures: **0**
- errors: **0**
- skipped: **0**
- final PTY result: `9 passed in 180.40s`.

## Broader valid Windows regression

The established Windows exclusion envelope was retained, and all already-PASS IMP-060 affected files were explicitly ignored to avoid duplicate stage execution.

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
  --ignore=tests/unit/test_studio_static_qa.py \
  --ignore=tests/unit/test_setup.py \
  --ignore=tests/unit/test_video_reviewer.py \
  -k "not test_claude_agy_providers_include_read_the_images_at and not test_single_sheet_wrapper_wording_matches_original_singular_form" \
  --basetemp=.tmp/pytest-imp060-broader-valid \
  --junitxml=.tmp/imp060-broader-valid.xml
```

Final JUnit `.tmp/imp060-broader-valid.xml`:
- tests: **654**
- failures: **0**
- errors: **0**
- skipped: **0**

Final PTY result:

```text
654 passed, 3 deselected in 1755.69s (0:29:15)
```

## Frozen baseline verification

`python tools/frozen_master_guard.py`:

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
```

Frozen semantic SHA is unchanged.

## Final static / authority verification

- `python -m py_compile agent/studio/static_qa.py tests/unit/test_studio_static_qa.py`: **PASS**;
- `python -m compileall -q agent/studio`: **PASS**;
- `import agent.studio` + `import agent.studio.static_qa`: **PASS**;
- `git diff --check`: **PASS**;
- provider/runtime/network leakage scan in `static_qa.py`: **CLEAN**;
- TODO/FIXME/NotImplementedError scan in IMP-060 implementation/tests: **CLEAN**.

## Verification conclusion

IMP-060 is locally verified for its claimed Static QA scope. The evidence supports proceeding to the Git side-effect guard and exact-scope commit/push/PR lifecycle. It does not claim merge or MAIN VERIFIED until exact PR head CI/review/merge and post-merge main verification have completed.
