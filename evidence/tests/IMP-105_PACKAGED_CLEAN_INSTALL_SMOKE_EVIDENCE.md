# IMP-105 — Packaged Clean-Install Smoke Evidence

## Status

- Local acceptance: **PASS**.
- Overall task: **RUNNING** until exact-head commit/PR CI, review, merge, and post-merge main verification are completed.
- Project root: \`E:\FlowKit-Studio-Upgrade\`
- Branch: \`chatgpt/IMP-105-packaged-clean-install-smoke\`
- Base/HEAD at local verification: \`aeae12684dd1e8355d822c556b5fbcc3b52930bc\` (the feature changes remain uncommitted at this checkpoint).

## Packaged target identity

- Electron-builder package command completed with exit code 0; marker: \`.tmp/imp105/package.exitcode\`; log: \`.tmp/imp105/package.log\`.
- Output: \`.tmp/imp105/package/win-unpacked\`; test copy: \`.tmp/imp105/fresh-copy\`.
- Electron runtime: 44.7.0; Windows x64.
- Package executable: \`FlowKit Studio.exe\`, ProductVersion \`0.1.0.0\`, SHA-256 \`A651C18D2C9E4DC477D56D5C990D8FA1BE71AFDCF2E106922646F809A14273B7\`.
- \`resources/app.asar\` SHA-256: \`E0A3B4CAD2FCED38809B59A586A14F897C6AA3775DE2400932698472C4E29ECF\`.
- Package and fresh-copy inventories match exactly: 72 files, 385,486,360 bytes. Their ASAR hashes match exactly.
- Fresh package has no \`resources/app\` unpacked source directory and no top-level \`node_modules\`; the smoke test asserts both are absent.
- Extracted package source matches the current source byte-for-byte for \`main.cjs\`, \`preload.cjs\`, \`security-policy.cjs\`, \`credential-broker.cjs\`, \`ipc-contract.cjs\`, \`ipc-main.cjs\`, \`production-utility-bridge.cjs\`, \`utility-entry.cjs\`, \`renderer/index.html\`, \`renderer/app.js\`, and \`renderer/styles.css\`. Packaged preload SHA-256 = \`69F77E80FBB7BF1C3BE9BF9CD59BAE765C9C955E1E5A734C4EE2EFC651CD9021\`, matching source.

## Runtime acceptance

JUnit: \`.tmp/imp105/packaged-clean-install-smoke-final2.xml\`; exit marker \`.tmp/imp105/packaged-clean-install-smoke-final2.exitcode\` = \`0\`.

- Tests: 1; failures: 0; errors: 0; skipped: 0.
- Fresh first run: PID 108084; app exited cleanly with exit code 0.
- Restart using the same isolated profile: PID 147900; app exited cleanly with exit code 0.
- Renderer reached \`document.readyState=complete\`; title and heading were \`FlowKit Studio\`; expected narrow \`window.flowkitHost\` API keys were present.
- Renderer → IPC → Utility bridge returned \`ok=true\`; UI health badge was \`Utility READY\` / \`ready\`.
- Missing canonical read-model provider failed closed with \`APPLICATION_READ_MODEL_UNAVAILABLE\`; no legacy/fake read model was promoted.
- Each run used isolated \`APPDATA\`, \`LOCALAPPDATA\`, \`TEMP\`, and \`TMP\` roots under \`.tmp/imp105/runtime-user-data\`, in addition to an isolated Chromium \`--user-data-dir\`.
- Both first run and restart confirmed no \`credential-vault-v1.json\` anywhere under the isolated test data tree. The test does not read or modify real user-profile credentials.
- Sanitized structured result: \`.tmp/imp105/clean-install-smoke-result.json\`.
- Per-run logs: \`.tmp/imp105/first-run.stdout.log\`, \`.tmp/imp105/first-run.stderr.log\`, \`.tmp/imp105/restart.stdout.log\`, \`.tmp/imp105/restart.stderr.log\`.

## Schema negative gate

JUnit: \`.tmp/imp105/packaged-clean-install-schema-gate.xml\`; exit marker \`.tmp/imp105/packaged-clean-install-schema-gate.exitcode\` = \`0\`.

- Tests: 1; failures: 0; errors: 0; skipped: 0.
- The packaged credential broker rejects an unsupported vault schema with \`VAULT_CORRUPT\` and leaves the original vault bytes unchanged.

## Final local checks and runtime

- \`node --check desktop/preload.cjs\`: PASS.
- \`node --check desktop/tests/packaged-clean-install-smoke.test.cjs\`: PASS.
- \`git diff --check\`: PASS.
- No FlowKit app/test/electron-builder task process remained after verification.
- The smoke and schema gates were run separately; the smoke gate was not rerun after its final PASS.
- Earlier diagnostic attempts and their failure logs/markers are preserved under local \`.tmp/imp105\`; only the final JUnit/exit-marker pairs above are accepted as PASS evidence.
- All \`.tmp/imp105\` runtime/package artifacts are local-only and must remain excluded from Git.

## Next exact action

Review the exact source/test/evidence/state diff; rerun only syntax checks and \`git diff --check\` if needed (do not rerun the PASS smoke or schema gates). Stage only \`desktop/preload.cjs\`, \`desktop/tests/packaged-clean-install-smoke.test.cjs\`, this evidence file, \`CURRENT_HANDOFF.md\`, \`PROJECT_STATE.md\`, and \`tasks/TASK_QUEUE.md\`; verify the staged file list and cached diff; then commit/push once after checking the remote branch/PR duplicate guard. Verify exact-head CI and review, merge only after required gates pass, verify the resulting main SHA and main push CI, and then claim the next dependency-ready queue task.

## Exact-head CI failure and preload repair — 2026-10-17

- Exact-head PR #98 run 39040021903 completed FAILURE on commit 6747cd54d0978971de062adfaf5a953b2bcc944d; both unit (3.10) and unit (3.13) failed at the same assertion in tests/unit/test_electron_host_security.py::test_preload_exposes_only_bounded_typed_ipc_capability: expected the bounded preload call ipcRenderer.invoke(channel, request).
- Root cause: the sandboxed self-contained desktop/preload.cjs called ipcRenderer.invoke directly with named channel constants and lacked the explicit bounded invoke(channel, request) adapter asserted by the existing security test.
- Repair applied locally in desktop/preload.cjs: add an allowlisted adapter permitting only GET_BRIDGE_STATUS and GET_STUDIO_APPLICATION_READ_MODEL, then route both existing typed calls through it. No generic renderer IPC capability was introduced.
- Post-repair checks: node --check desktop/preload.cjs PASS; git diff --check PASS; a direct static assertion confirms the required call and both channel guards. The local default Python has no pytest installed, so the Python test itself has not been claimed as locally PASS; exact-head CI must re-run it after push.
- Runtime/package caution: the prior packaged smoke/schema evidence predates this preload repair. Package rebuild was attempted through FileMCP, but the execution bridge did not return a durable exit marker/log; process checks found no live build process. Therefore the existing packaged smoke evidence must not be treated as verification of the repaired preload until a fresh package identity + first-run/restart smoke completes.
- Current task status: FAIL at exact-head CI; only the failing preload/security stage is being repaired. Prior independent schema-negative gate is preserved and is not rerun. .tmp/imp105 remains local-only and must not be staged.

NEXT_EXACT_ACTION = "SYNC THIS FAILED-CI/REPAIR CHECKPOINT; VERIFY NODE SYNTAX + DIFF; STAGE ONLY desktop/preload.cjs, evidence/tests/IMP-105_PACKAGED_CLEAN_INSTALL_SMOKE_EVIDENCE.md, CURRENT_HANDOFF.md, PROJECT_STATE.md, tasks/TASK_QUEUE.md; COMMIT/PUSH THE REPAIR ONCE; VERIFY NEW EXACT-HEAD CI; THEN REBUILD THE PACKAGED APP AND RUN ONLY THE IMP-105 CLEAN-INSTALL FIRST-RUN/RESTART SMOKE AGAINST THE NEW SOURCE-PACKAGE IDENTITY; DO NOT RERUN THE UNCHANGED SCHEMA GATE; MERGE ONLY AFTER REQUIRED GATES AND REVIEW; VERIFY MAIN SHA + MAIN PUSH CI; THEN CLAIM NEXT DEPENDENCY-READY TASK.


## Repair commit / remote verification checkpoint — 2026-10-17

- Bounded preload repair committed as 00d93ebe6743106917fba9a0ce192acb0645be1e and pushed to the existing PR #98 branch; remote SHA matches.
- Exact-head CI run 39044322325 was observed IN_PROGRESS for both Python 3.10 and 3.13. Previous failure run 39040021903 applies only to the previous head.
- Repaired-source packaged first-run/restart smoke remains PENDING because the prior package identity was built before the preload repair. Do not claim that old smoke evidence verifies the new preload.
- NEXT_EXACT_ACTION = "WAIT FOR RUN 39044322325 RESULT; IF PASS, REBUILD PACKAGE AND VERIFY CURRENT SOURCE/PACKAGE ASAR IDENTITY, THEN RUN ONLY CLEAN-INSTALL FIRST-RUN/RESTART SMOKE; DO NOT RERUN THE UNCHANGED SCHEMA NEGATIVE GATE; MERGE ONLY AFTER REQUIRED GATES AND REVIEW; VERIFY MAIN SHA + MAIN PUSH CI."


## Repaired-preload package and runtime smoke — 2026-10-17

- Rebuilt the Windows x64 package after the preload repair with command: npm --prefix desktop run pack -- --config.directories.output=../.tmp/imp105/package --config.win.signAndEditExecutable=false. Durable exit marker .tmp/imp105/package-repair-preload.exitcode = 0.
- Repaired package app.asar SHA-256 = AB94F72E5131CB6EAF299368B5580B18B6D4084145EE2473512A3FE34E127E5F; executable SHA-256 = 75A4C2ED24CEF05886A71A4B25E77C7AAC804BAFF3BD0BCEFE0D5249113F7994.
- Extracted packaged preload SHA-256 = 7326915809ba728f8a4d2f4fc225c9b123a72c51344587208742b1622755c837; source preload SHA-256 is identical. PRELOAD_SOURCE_PACKAGE_IDENTITY = PASS.
- Fresh-copy inventory equals retained package: 72 files / 385486593 bytes; ASAR hashes match. No resources/app unpacked source directory and no top-level node_modules.
- Reran only the clean-install first-run/restart test against the repaired package: command used Node test-name filter for “fresh-copy packaged Windows app completes first-run and restart with renderer/IPC/Utility health”; exit marker .tmp/imp105/packaged-clean-install-smoke-repaired.exitcode = 0; tests=1, pass=1, fail=0, skipped=0; duration about 20.2 seconds.
- First run PID 144580 and restart PID 175336 both exited 0. Renderer reached complete; narrow flowkitHost API present; Renderer→IPC→Utility returned ready; missing canonical read model failed closed with APPLICATION_READ_MODEL_UNAVAILABLE; no credential-vault-v1.json was created in isolated user data on either run.
- The unchanged schema-negative gate was not rerun; its earlier PASS remains separate evidence and is not represented as a test of the repaired preload.
- Package build used signAndEditExecutable=false to avoid the local signing/editing stage; runtime and ASAR identity acceptance passed, but this does not claim a signed installer/release artifact.
- Exact-head CI run 39044322325 passed both unit (3.10) and unit (3.13) on repair commit 00d93ebe6743106917fba9a0ce192acb0645be1e. PR #98 remains OPEN pending final state/evidence sync and exact-head verification of the sync commit.

NEXT_EXACT_ACTION = "SYNC THESE REPAIRED-PACKAGE/CI PASS RESULTS INTO CURRENT_HANDOFF, PROJECT_STATE, TASK_QUEUE AND EVIDENCE; REVIEW FULL PR #98 DIFF + REQUIRED REMOTE GATES; STAGE ONLY STATE/EVIDENCE FILES; COMMIT/PUSH ONCE; VERIFY NEW EXACT-HEAD CI; MERGE ONLY AFTER REQUIRED GATES; VERIFY MAIN MERGE SHA + MAIN PUSH CI; THEN CLAIM NEXT DEPENDENCY-READY TASK."


## Post-merge verification — 2026-10-17

- PR #98 exact head: 7763e741213d6134e0d11eeb823f0a66a102809d.
- PR CI run 39045499127: SUCCESS on Python 3.10 and 3.13.
- Merge commit / remote main SHA: 70027edb296ac205e37da3856c020adf6c49c153.
- Main push workflow run 39048887308: SUCCESS on Python 3.10 and 3.13; frozen Master baseline step PASS.
- Repaired package/runtime acceptance evidence remains as documented above; no signed installer claim; unchanged schema-negative gate was not rerun.
- State-sync checkpoint: FileMCP-E tunnel was unavailable after merge (requests were enqueued but tunnel client did not poll). Remote GitHub main/CI verification is complete; local worktree/state bootstrap remains the next exact action after tunnel recovery.
