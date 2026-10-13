# IMP-101 — Migration Dry Run Evidence

Date: 2026-10-13 (Asia/Ho_Chi_Minh)

## Scope and authority

- Task: IMP-101 — Migration Dry Run.
- Authoritative decomposition: `tasks/IMPLEMENTATION_TASK_DECOMPOSITION_V1.md`, lines 369–372.
- Goal: representative legacy DB/project migration into canonical mapping evidence.
- Acceptance: no silent narrative inference, restart-safe execution, durable evidence retained.
- Branch: `chatgpt/IMP-101-migration-dry-run`.
- Base / worktree HEAD at start of this resumed validation: `0c0d977edfc0edfa374d9bc009631516700dab34`.
- No local `flow_agent.db` was present. The integration test creates a temporary SQLite DB from the repository's `agent/db/schema.py` schema and a synthetic fixture; this evidence does **not** claim a live-user migration.
- Implementation writes mapping evidence to a separate staging DB, opens source DB read-only, fingerprints the source snapshot, rejects changed-source resume, and does not create StoryCore/SceneDramaticBeat/FullShotSpec/ShotIR targets.

## Test evidence

### IMP-101 targeted integration tests

- Exact command recorded in the durable task state:

  `uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_migration_dry_run.py -q --junitxml=.tmp/imp101-targeted-final2.xml --basetemp=.tmp/pytest-imp101-targeted-final2`

- Result recorded from the completed run: **3/3 PASS**, exit code 0.
- JUnit: `.tmp/imp101-targeted-final2.xml`.
- Earlier failed-attempt JUnit files are retained separately and are not overwritten.

### Affected regression files

The prior durable handoff records these files as having been executed **individually**, under isolated Python 3.13, each with its own JUnit and basetemp. Their earlier PTY command text is no longer available in the current FileMCP runtime, so this report does not invent a full argv for those runs.

| Test file | JUnit evidence | Verified JUnit result | Exit metadata |
|---|---|---:|---|
| `tests/unit/test_studio_legacy_import.py` | `.tmp/imp101-legacy-import.xml` | **9/9 PASS** | Handoff records exit 0 |
| `tests/unit/test_studio_operational_scene_projection.py` | `.tmp/imp101-projection.xml` | **7/7 PASS** | Handoff records exit 0 |
| `tests/unit/test_studio_backup_restore.py` | `.tmp/imp101-backup-restore.xml` | **10/10 PASS** | Handoff records exit 0 |
| `tests/unit/test_studio_persistence.py` | `.tmp/imp101-persistence.xml` | **12/12 PASS**, 0 failures, 0 errors, 0 skipped; suite time 20.237s | Process/PTY exit code unavailable; not inferred from JUnit |

- Runtime verification found no matching IMP-101 pytest/uv process remaining.
- Sum of test executions represented above: **41 test cases across five file-level runs**.
- The earlier combined affected run without a complete JUnit remains classified INTERRUPTED; the per-file JUnit evidence above is the valid recovery evidence. Do not rerun the targeted or affected files merely to replace unavailable historical PTY metadata.
- Do not rerun IMP-100's completed 836-test regression, frozen guard from IMP-100, or its completed CI.

## Static and frozen-baseline gates

| Command | Result |
|---|---|
| `python tools/frozen_master_guard.py` | **PASS**, exit 0 |
| `python -m compileall -q agent/studio/migration_dry_run.py tests/unit/test_studio_migration_dry_run.py` | **PASS**, exit 0 |
| `git diff --check` | **PASS**, exit 0 |

Frozen Master evidence:
- Canonical semantic SHA-256: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- Raw SHA-256: `abb08e8114be3ace0d81ceccf8a3dea45c78a6268c64fae4c332d0644fa1e303`.
- Guard output: `FROZEN_MASTER_GUARD=PASS`.

## Contract review and limits

- Source SQLite is opened with URI `mode=ro` and `PRAGMA query_only=ON`; source file hash is asserted unchanged in the integration test.
- Manifest checkpoints are atomically written and bound to source fingerprint, table hashes, target schema, and rule version.
- Restart/replay verifies persisted mappings, repairs the tested manifest-checkpoint-loss window idempotently, and refuses a changed source snapshot.
- Report and manifest omit raw story/prompt sentinel strings; staging mapping payload/provenance also exclude those sentinels.
- This is a dry-run/classification boundary, not a live production migration, and it does not authorize external provider/API side effects.
- The persistence JUnit result is PASS; its process exit code is unavailable. No claim is made that the missing exit metadata was recovered.

## Git / remote side-effect guard

- Local index was empty at inspection; no staged changes existed.
- Intended task files are the migration module, targeted test, synthetic fixture, this evidence file, and the three governance state files.
- Local `.tmp/` contains runtime/test artifacts and must remain unstaged.
- Remote branch search for `chatgpt/IMP-101-migration-dry-run` returned no branch; GitHub PR search for IMP-101 returned no PR at the time of inspection.
- No commit, push, PR, or merge is claimed by this evidence section; each must be verified after execution.

## Next

- Finish exact-file review, inspect the staged diff, and commit only the seven intended files.
- Push the task branch once, verify remote HEAD, create a PR only if absent, inspect CI on the exact PR head, obtain review, merge only after required gates pass, then checkout/pull main and verify the merge commit.
- After MAIN VERIFIED, read the queue and automatically claim the next dependency-ready task (IMP-102 only if its dependencies are satisfied).


## Git commit checkpoint
- Implementation/evidence/state commit: `ff332976a0f396c92845f178c325b8d1c381b55b` — `feat(studio): add restart-safe migration dry run`.
- Parent/base SHA: `0c0d977edfc0edfa374d9bc009631516700dab34`.
- Commit contains exactly the seven intended files; `git diff HEAD^ HEAD --check` passed (exit 0); `.tmp/` is not committed.
- Post-commit worktree has only untracked `.tmp/` test/runtime artifacts.
- Remote branch and PR were absent at the last pre-push check; push and PR are not yet claimed complete.
- NEXT_EXACT_ACTION = `COMMIT POST-COMMIT STATE/EVIDENCE SYNC -> RECHECK REMOTE BRANCH/PR -> PUSH ONCE -> VERIFY REMOTE HEAD -> CREATE PR ONLY IF ABSENT`


## Branch push checkpoint
- `git push --set-upstream origin chatgpt/IMP-101-migration-dry-run` completed with exit 0.
- Local HEAD and remote branch SHA verified equal: `7f1186634c621050e5d114d17cef2feb50dfc393`.
- Upstream `origin/chatgpt/IMP-101-migration-dry-run` is configured; GitHub branch search confirms the branch exists.
- GitHub PR search for IMP-101 returned no PR at this checkpoint; PR creation remains pending and will be guarded by another search.
- NEXT_EXACT_ACTION = `COMMIT PUSH-CHECKPOINT STATE/EVIDENCE SYNC -> PUSH THE NEW STATE HEAD ONCE -> VERIFY REMOTE HEAD -> RECHECK PR SEARCH -> CREATE PR ONLY IF ABSENT`


## Pull request checkpoint
- Created PR #91: https://github.com/nguyenkhactang922-bot/flowkit/pull/91.
- PR head at creation: `4d93ee5bf922cf7802d68e75d51973921a8fb137`; base main: `0c0d977edfc0edfa374d9bc009631516700dab34`.
- PR is open and not merged. GitHub reported `mergeable=false` at creation; exact-head CI and review are still pending verification.
- Do not merge until required checks/review are verified against the current exact PR head.
- NEXT_EXACT_ACTION = `COMMIT PR-CREATION STATE/EVIDENCE SYNC -> PUSH STATE HEAD -> FETCH PR #91 CURRENT HEAD AND WORKFLOW RUNS/JOBS -> REVIEW EXACT HEAD/REQUIRED CHECKS; DO NOT MERGE WHILE GATES ARE PENDING`


## Exact PR head and CI observation
- PR #91 was verified OPEN and unmerged; exact head at this observation: `cf1a5835c12ee54a4c8ddb4d44ff03e96f410158`; base main SHA `0c0d977edfc0edfa374d9bc009631516700dab34`.
- Workflow run `38368157340` (`tests`, run #195) was `pending` for that exact head. The combined status endpoint returned no statuses; no PASS is claimed.
- No review submissions or inline review threads were returned at this observation.
- The following state-sync commit will move PR head. Always fetch the current head and matching CI after push; do not transfer this pending result to a different SHA.
- NEXT_EXACT_ACTION = `COMMIT/PUSH PR HEAD + CI PENDING STATE SYNC -> FETCH PR #91 NEW CURRENT HEAD -> FETCH WORKFLOW RUNS/JOBS FOR THAT EXACT SHA -> REVIEW EXACT PR DIFF AND MONITOR UNTIL REQUIRED GATES COMPLETE`


## Review finding — manifest integrity fail-closed requirement
- Exact PR head reviewed: `21fba3246956cf7f440aa67f49f027bb222f3f26`, PR #91.
- Finding: the runner's resume validation did not verify manifest `total_records`, source integrity/FK summary fields, complete checkpoint set coverage/uniqueness, or that each mapping artifact's actual source identity hashes to its manifest checkpoint key. A tampered complete manifest could under-report records or rebind a mapping and potentially report a false acceptance PASS.
- Status: review gate FAIL; PR must not merge until fixed and validated on a new exact PR head. Existing test JUnit checkpoints remain recorded but do not close this newly identified case.
- Old-head workflow run `38368452247` was in progress; it is not evidence for the future fix head.
- NEXT_EXACT_ACTION = `HARDEN IMP-101 MANIFEST IDENTITY/CHECKPOINT SET AND ARTIFACT SOURCE-KEY VALIDATION -> ADD NEGATIVE TESTS FOR TAMPERED COMPLETE MANIFEST/REBOUND MAPPING -> RERUN ONLY tests/unit/test_studio_migration_dry_run.py -> DIFF-CHECK AND PUSH FIX; THEN VERIFY CI ON THE NEW EXACT PR HEAD`


## Manifest integrity hardening checkpoint
- Finding closed in code: `_validate_manifest_identity` now validates `source_integrity_check`, `source_foreign_key_violations`, `context_only_tables`, and `total_records`; validates checkpoint type/source membership/uniqueness; and requires COMPLETE checkpoint coverage to equal the current source key set.
- `_summary_from_artifact` now recomputes the source key from the persisted mapping's source kind/table/ID and rejects a manifest checkpoint that rebinds the artifact to another source record.
- Added tests for missing checkpoint, missing checkpoint with a tampered total, duplicate checkpoint, source-key rebinding, and a tampered foreign-key summary.
- Command: `uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_migration_dry_run.py -q --junitxml=.tmp/imp101-manifest-hardening.xml --basetemp=.tmp/pytest-imp101-manifest-hardening`.
- Result: **8/8 PASS**, exit 0, 0 failures/errors/skips; complete JUnit suite time 35.915s.
- `python -m compileall -q agent/studio/migration_dry_run.py tests/unit/test_studio_migration_dry_run.py` exit 0; `git diff --check` exit 0.
- Frozen Master guard PASS from the same unchanged frozen Master SHA; no frozen baseline file changed.
- The pending old-head CI run `38368452247` is for SHA `21fba3246956cf7f440aa67f49f027bb222f3f26` and does not validate this fix. Do not merge; push the fix and verify CI for the new exact PR head.
- NEXT_EXACT_ACTION = `VERIFY THE SIX-FILE FIX/STATE DIFF -> STAGE ONLY THE SIX INTENDED FILES (EXCLUDE .tmp) -> STAGED DIFF-CHECK -> COMMIT FIX + STATE/EVIDENCE -> PUSH AND VERIFY NEW PR HEAD/CI`
