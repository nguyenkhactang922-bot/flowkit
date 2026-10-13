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
