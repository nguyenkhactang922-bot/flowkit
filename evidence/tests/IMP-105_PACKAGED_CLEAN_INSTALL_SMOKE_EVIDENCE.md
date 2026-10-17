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