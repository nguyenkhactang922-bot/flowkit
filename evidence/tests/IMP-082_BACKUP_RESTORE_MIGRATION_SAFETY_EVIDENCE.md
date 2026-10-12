# IMP-082 Backup / Restore / Migration Safety Evidence

Date: 2026-10-12
Branch: `chatgpt/IMP-082-backup-restore-migration-safety`
Base main SHA: `dbee0bc784bcbf6ccd164069d8399ce61af1f277`

## Scope

IMP-082 adds a verified backup and staged-restore orchestration layer without creating a second persistence/migration authority or overwriting active project data during restore.

Frozen/design authority enforced by this task:
- `ensure_schema_compatibility` remains the only schema/migration owner;
- newer or identity-mismatched migration histories fail closed;
- READY artifact byte authority remains IMP-055 `MATERIALIZE_VALID` evidence;
- a backup is published only after SQLite integrity, contiguous migration history, DB snapshot hash/size, and every required artifact hash/size verify;
- partial backup/restore staging never equals success and is deterministically replaceable on retry;
- restore verifies the source backup, copies into an isolated staging project, migrates only the staged DB, re-verifies DB/artifacts, and never accepts an active-project destination;
- Windows-unsafe backup identifiers and unsafe/symlink root shapes fail closed.

Implementation surfaces:
- `agent/studio/backup_restore.py`
- `agent/studio/__init__.py` public exports
- `tests/unit/test_studio_backup_restore.py`

No Frozen Master, persistence schema version, migration list, GenerationJob state machine, ArtifactLifecycle authority, provider adapter, or active-project promotion path was modified.

## Targeted verification

Final exact-head targeted JUnit `.tmp/imp082-final-targeted.xml`:
- tests: **10**
- failures: **0**
- errors: **0**
- skipped: **0**
- time: **183.804s**

Targeted coverage proves:
- verified DB/schema/artifact backup and exact replay;
- missing required artifact blocks publication;
- artifact and manifest tamper are rejected;
- newer unsupported schema is rejected before successful backup publication;
- staged restore migrates the staged copy while leaving the active older-schema DB untouched;
- interrupted migration rolls back and deterministic resume succeeds;
- stale partial backup is discarded on retry;
- missing canonical migration history blocks backup;
- backup identifiers are Windows-filesystem-safe.

## Affected-owner regression

JUnit `.tmp/imp082-affected.xml`:
- tests: **43**
- failures: **0**
- errors: **0**
- skipped: **0**
- time: **398.151s**

Affected owner scope covered persistence, GenerationJob, and ArtifactLifecycle without rerunning IMP-082 targeted tests.

## Broader valid Windows regression

JUnit `.tmp/imp082-broader-valid.xml`:
- tests: **783**
- failures: **0**
- errors: **0**
- skipped: **0**
- time: **2572.218s**

The run used the established Windows-valid envelope and excluded IMP-082 targeted + affected files already proven PASS together with repository-known Windows-invalid exclusions. Recorded root PID `114276` was absent after completion; durable JUnit therefore classifies the stage PASS, not INTERRUPTED.

## Frozen baseline verification

`python tools/frozen_master_guard.py`:

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
RAW_SHA256=abb08e8114be3ace0d81ceccf8a3dea45c78a6268c64fae4c332d0644fa1e303
```

Frozen semantic SHA is unchanged.

## Final static / authority verification

- `python -m py_compile agent/studio/backup_restore.py tests/unit/test_studio_backup_restore.py`: **PASS**;
- canonical public import: **PASS** for `BackupManifest`, `BackupRestoreService`, `RestoreStageManifest`, and `RestoreStageStatus`;
- `git diff --check`: **PASS**;
- provider/network/runtime leakage review: **CLEAN**; `_TOKEN_RE` is an internal filesystem-safe identifier validator, not a credential surface;
- exact-head review confirms backup publication is verify-then-rename, staged restore has no active-project destination, schema compatibility stays delegated to the existing persistence owner, and required READY artifacts remain bound to canonical path/hash/size evidence.

A prior public-import probe used the nonexistent shorthand `RestoreResult`. The actual exported contract is `RestoreStageManifest` / `RestoreStageStatus`; correcting the probe required no code change and invalidated no test checkpoint.

## Verification conclusion

`IMP-082 LOCAL VERIFIED` for the current worktree and claimed Backup / Restore / Migration Safety scope. Evidence supports proceeding to exact Git side-effect guard, exact-scope commit, PR exact-head CI/review, merge and post-merge MAIN verification. This file does not claim merge or MAIN VERIFIED.
