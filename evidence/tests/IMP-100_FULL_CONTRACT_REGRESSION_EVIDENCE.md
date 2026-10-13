# IMP-100 — Full Contract Regression Evidence

Date: 2026-10-13 (Asia/Ho_Chi_Minh)

## Scope and authority
- Task: SYSTEM ACCEPTANCE LANE / IMP-100 Full Contract Regression.
- Authoritative task definition: `tasks/IMPLEMENTATION_TASK_DECOMPOSITION_V1.md`, goal = run provider-neutral unit/contract/architecture tests; acceptance = zero blocking contract failures.
- Branch: `chatgpt/IMP-100-full-contract-regression`.
- Worktree HEAD during evidence recovery: `4f1267010522b9451a88af6f32fdb4fd5b203c11`.
- Local command scope recorded in the handoff: Windows-valid provider-neutral `tests/unit` under isolated Python 3.13, excluding `test_setup.py`, `test_video_reviewer.py`, and two known POSIX assertions. The original PTY's exact argv and exit code are not recoverable after its session expired; they are not inferred here.
- CI acceptance remains full `tests/unit` on Ubuntu Python 3.10 and 3.13 with no exclusions.

## Durable result
- JUnit: `.tmp/imp100-contract-regression.xml`.
- File size: 118,256 bytes.
- Last write observed: 2026-10-13 01:23:34 local time.
- Parsed complete JUnit summary: **836 tests, 0 failures, 0 errors, 0 skipped**, total test time 6,242.369 seconds.
- XML root: `testsuites`, pytest suite; failure/error testcase query returned none.
- Process check: no matching pytest/IMP-100 process remains.
- PTY: `pty_5c13226282aaf615d2a68d9f5ebcc9a5638e` is expired/unknown to the current FileMCP PTY registry. Therefore its exit code cannot be independently recovered.
- Classification: **JUnit test outcome PASS (836/836)**. PTY exit code is **unavailable**, not fabricated. Do not rerun the completed regression merely to replace expired PTY metadata; retain the durable JUnit and use the required full Linux CI run as an additional independently captured exit-status gate.

## Other verified checks
- `git diff --check`: exit 0.
- No remote branch exists yet for `chatgpt/IMP-100-full-contract-regression`.
- `.tmp/` is local runtime/test evidence and must not be staged wholesale.

## Next
- Run `python tools/frozen_master_guard.py` on the current IMP-100 worktree.
- Then perform exact-worktree static/import/diff review and finalize tracked evidence/state.
- Stage only intentional tracked files, verify the index, commit, push/create PR if supported, obtain full Ubuntu Python 3.10 + 3.13 CI, review/merge only when required gates pass, then verify main.


## Frozen baseline gate
- Command: `python tools/frozen_master_guard.py`
- Exit code: 0
- Result: `FROZEN_MASTER_GUARD=PASS`
- Canonical Master SHA256: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`
- Raw SHA256: `abb08e8114be3ace0d81ceccf8a3dea45c78a6268c64fae4c332d0644fa1e303`


## Exact-worktree static and Git review
- `git diff --check`: exit 0.
- No source or test file changes in the IMP-100 worktree; scope is governance law + handoff/state/queue + this evidence report.
- New tracked evidence candidate verified at `evidence/tests/IMP-100_FULL_CONTRACT_REGRESSION_EVIDENCE.md`.
- `.tmp/` contains runtime/test artifacts and must remain unstaged.
- Side-effect guard before first commit: no IMP-100 commit found in local Git history; local index is expected empty and must be checked immediately before staging; `origin` has no `chatgpt/IMP-100-full-contract-regression` branch; `gh pr list --head chatgpt/IMP-100-full-contract-regression --state all` returned `[]`.


## Git lock recovery note
- A zero-byte `.git/index.lock` blocked the first stage attempt. It was older than 20 minutes, the index was older still, and no live Git/Git-remote/Git-LFS process existed.
- Removed only the stale lock; no index/worktree content was changed by the failed add. Index verified empty afterwards.
