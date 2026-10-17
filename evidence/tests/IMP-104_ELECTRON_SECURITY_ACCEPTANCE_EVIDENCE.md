# IMP-104 — Electron Security Acceptance Evidence

**Result:** PASS
**Recorded:** 2026-10-17
**Project:** `E:\FlowKit-Studio-Upgrade`
**Claim base:** `1f234046f739e21d6963ef5307025793190f8cfd`
**Scope:** packaged Windows x64 Electron target; negative security boundary tests and native safeStorage/DPAPI proof.

## Frozen authority and scope

- Frozen authority: `docs/design/canonical/MASTER_AI_FILM_STUDIO_FINAL_IMPLEMENTATION_BASELINE_V1.md`, Security §84 and Credential Broker §85.
- Required invariant: Electron Main owns long-lived credentials through safeStorage; Renderer has no long-lived secret access; Utility receives only scoped short-lived leases; project files/logs do not expose long-lived secrets.
- This evidence closes the Frozen Master implementation/release evidence gap for packaged Windows safeStorage. It does not claim a signed release installer or a live-provider E2E.

## Dependency and package provenance

- Node: `v24.15.0`; npm: `11.12.1`.
- Electron: `44.7.0`, MIT; electron-builder: `26.15.3`, MIT; `@electron/asar`: `3.4.1`, MIT.
- `desktop/package-lock.json` audit: 284 dependency entries; all resolved from `https://registry.npmjs.org/`; no missing integrity hashes or license metadata; direct package registry integrity matched the lockfile.
- Official Electron v44.7.0 Windows x64 ZIP: 158,293,649 bytes; SHA-256 `eee30dc8fa1f5ea95490e59f44e46ea68dd24c6e93d22facf70fe5c2d4c2665c`. The value matched the pinned package's `electron/checksums.json`; official GitHub release metadata and HTTP HEAD/content length were checked before install.
- `npm ci --ignore-scripts --no-audit --no-fund` completed with npm debug-log `verbose exit 0` / `info ok`; 284 installed package paths were present. The PowerShell wrapper initially reported exit 1 because its `ErrorActionPreference=Stop` promoted a deprecation warning; the npm operation itself exited 0. This PASS stage was not rerun.
- The Electron installer was run once and exited 0. The runtime marker and executable version were `44.7.0`. Electron-builder used isolated cache paths under `.tmp/imp104`, `--publish never`, and `CSC_IDENTITY_AUTO_DISCOVERY=false`; no other project's cache/process was touched.

## Packaged target identity

- Package command: `node node_modules/electron-builder/out/cli/cli.js --dir --win --x64 --publish never --config.directories.output=E:/FlowKit-Studio-Upgrade/.tmp/imp104/package`.
- Exit marker: `.tmp/imp104/package-final2.exitcode = 0`.
- Output: `.tmp/imp104/package/win-unpacked` (unpacked test package; unsigned by design).
- Inventory: 72 files, 385,484,080 bytes.
- `resources/app.asar`: 80,101 bytes; SHA-256 `E89D20B29C8C83982557034B0D00993B9EEB118716C22F5CF0434ADD67FCFA36`.
- `FlowKit Studio.exe`: 246,302,208 bytes; SHA-256 `B35DD2EFC36F8DF71940F56FFBFAA5D177568B963B128F179D71FBF28F928C27`.
- The packaged ASAR includes main, preload, typed IPC, credential broker, utility bridge/entry and renderer files. It excludes test files, `node_modules`, vault data and signing-key file extensions. The packaged `resources/app` source directory is absent because application code is in `app.asar`.
- Non-fatal builder notices: package author metadata is missing and the default Electron icon is used. Authenticode reports NotSigned, expected for this local test package; no signing/release claim is made.
- Previous package artifacts, including failed attempts, were preserved locally under `.tmp/imp104` rather than overwritten.

## Acceptance test

Command run from `E:\FlowKit-Studio-Upgrade\desktop` with:
- `FLOWKIT_PACKAGED_APP_DIR=E:\FlowKit-Studio-Upgrade\.tmp\imp104\package\win-unpacked`
- `FLOWKIT_SECURITY_ARTIFACT_DIR=E:\FlowKit-Studio-Upgrade\.tmp\imp104`
- `node --test --test-reporter=junit tests/packaged-security-acceptance.test.cjs`

JUnit artifact: `.tmp/imp104/packaged-security-test-dpapi.xml`
Exit marker: `.tmp/imp104/packaged-security-test-dpapi.exitcode = 0`

- Tests: 2
- Passed: 2
- Failed: 0
- Skipped: 0
- Duration: 2.78 seconds

The packaged-ASAR test exercised the exact packaged modules and asserted:
- hardened BrowserWindow preferences (Node integration off, context isolation and sandbox on, web security on, insecure content/experimental features/webview/drag navigation off);
- the narrow `flowkitHost` preload surface with no raw IPC/safeStorage/credential-broker exposure;
- packaged CSP directives;
- exclusion of tests, node_modules, vault data and key files;
- denial of external/file/javascript/data URLs, renderer path traversal, navigation, popups and webview attachment;
- rejection of unknown utility capability and unexpected request fields;
- rejection of untrusted renderer sender/origin;
- exact renderer API shape and redacted IPC failure envelopes.

The packaged Windows runtime test launched the packaged executable with `--flowkit-security-self-test` and an isolated `--user-data-dir`. This mode exits before creating a BrowserWindow, IPC handler, Utility process or credential broker. The report at `.tmp/imp104/runtime-user-data/flowkit-security-self-test.json` records:
- Electron `44.7.0`, platform `win32`;
- safeStorage encryption available;
- synthetic in-memory encrypt/decrypt round-trip passed;
- ciphertext differs from the synthetic plaintext;
- no credential vault file before or after;
- no synthetic canary or ciphertext included in the report.

Electron 44's `getSelectedStorageBackend()` API is Linux-only and is not exposed on this Windows runtime; the test does **not** claim that API returned `dpapi`. Instead, safeStorage initialization created Chromium `Local State` with `os_crypt.encrypted_key`; the decoded key envelope starts with `DPAPI`. The test used Windows `ProtectedData.Unprotect` under the current user to decrypt the DPAPI-protected blob, verified the decrypted key length is 32 bytes, and emitted only `DPAPI_PROOF=PASS` (no key bytes or plaintext were printed). The temporary DPAPI blob was deleted after successful verification; no vault file exists.

## Failed-attempt diagnosis and correction

- First acceptance attempt: the packaged Electron builder had stripped build/devDependency fields from packaged `package.json`; the test incorrectly assumed those fields were present. Corrected the test to verify actual packaged ASAR topology and app metadata.
- Second attempt: the test tried to pass the `v10` safeStorage AES-GCM payload directly to DPAPI. That is not the DPAPI-protected key envelope. Corrected the test to inspect Chromium `Local State`'s `os_crypt.encrypted_key`, strip its `DPAPI` prefix, and verify the native DPAPI unwrap.
- Final exact packaged acceptance run: PASS 2/2. No IMP-070..073 PASS suite was rerun, and the Frozen Master guard was not rerun during this acceptance pass.

## Limits and next action

This proves the packaged Windows Electron security boundary and native DPAPI-protected safeStorage key path for a synthetic canary. It does not prove code signing, an NSIS installer, live-provider workflows, or a production credential's lifecycle. Keep all `.tmp/imp104` runtime/package artifacts local-only; commit only the reusable test, minimal Main self-test mode, lockfile/package metadata and this sanitized evidence document.

**NEXT_EXACT_ACTION:** review the exact source/test/evidence diff, run only `node --check` on changed JS plus `git diff --check`, then commit/push IMP-104 changes, create PR if absent, wait for exact-head CI, review, merge only after required gates, and verify main push CI.

## GitHub PR CI

- PR #97: https://github.com/nguyenkhactang922-bot/flowkit/pull/97
- Run `39008584808` completed `success` on exact PR head `39cd33d5421b5ee922cec7880b1bb80f9c713b74` at 2026-10-17 06:11:51Z.
- Both jobs `unit (3.10)` and `unit (3.13)` completed `success`; each passed setup, dependency installation, Frozen Master baseline verification and unit tests. The unit-test step took about 5m38s / 6m16s respectively but completed successfully; no cancellation/restart was performed.
- The run emitted a non-blocking GitHub Actions notice that `actions/checkout@v4` and `actions/setup-python@v5` still target Node.js 20 while the runner forces Node.js 24. This warning did not fail either job.
- This green run applies to head `39cd33d5421b5ee922cec7880b1bb80f9c713b74`. A subsequent state/evidence sync commit will produce a new head; that head must receive its own successful CI before merge.
