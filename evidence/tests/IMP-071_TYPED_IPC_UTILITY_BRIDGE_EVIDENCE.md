# IMP-071 Typed IPC / Production Utility Bridge Evidence

Date: 2026-10-10
Branch: `chatgpt/IMP-071-typed-ipc-utility-bridge`
Base HEAD: `e21b5132cec0c92eff0e67c22ea4309d359091a2`

## Scope

IMP-071 adds a typed, versioned Electron IPC boundary between low-privilege Renderer, privileged Main, and a dedicated Production Utility process without exposing generic host capabilities to Renderer code.

Security/authority invariants verified:
- Renderer does not receive raw `ipcRenderer`, `fs`, `child_process`, shell, or a generic invoke API.
- Renderer receives only bounded `flowkitHost.productionUtility.getBridgeStatus()` plus version metadata.
- Main validates exact sender `webContents`, main frame, and application origin before dispatch.
- Renderer/Main and Main/Utility messages use strict versioned schemas and exact-key validation.
- Unknown utility capabilities are denied.
- Utility failures/timeouts and contract errors are redacted before crossing back to Renderer.
- Production Utility transport is capability-specific and does not expose unrestricted filesystem/process primitives.
- Electron hardening baseline from IMP-070 remains unchanged (`nodeIntegration=false`, `contextIsolation=true`, `sandbox=true`, `webSecurity=true`).

## Implementation surfaces

- `desktop/ipc-contract.cjs`
- `desktop/ipc-main.cjs`
- `desktop/preload-api.cjs`
- `desktop/preload.cjs`
- `desktop/production-utility-bridge.cjs`
- `desktop/utility-entry.cjs`
- `desktop/main.cjs`
- `desktop/package.json`
- `desktop/tests/ipc-contract.test.cjs`
- `tests/unit/test_electron_host_security.py`

## Targeted verification

Node targeted security + typed IPC suite:
- command payload: `node --test desktop/tests/security-policy.test.cjs desktop/tests/ipc-contract.test.cjs`
- result: **12/12 PASS**
- failures: **0**

The repository `npm run test:security` attempt failed before test execution because the local npm bootstrap was broken. The exact script payload was then executed directly with Node and passed; this is classified as harness-only and not a product/test failure.

Python Electron static-security targeted JUnit `.tmp/imp071-targeted.xml`:
- tests: **7**
- failures: **0**
- errors: **0**
- skipped: **0**
- result: **PASS**

## Affected regression

Affected service-boundary JUnit `.tmp/imp071-affected.xml`:
- tests: **9**
- failures: **0**
- errors: **0**
- skipped: **0**
- result: **PASS**

Covered the existing project/session and upload API boundaries without rerunning targeted Electron files.

## Broader valid Windows regression

Established Windows-valid regression envelope retained the historical platform exclusions and excluded IMP-071 targeted/affected files already locked PASS.

JUnit `.tmp/imp071-broader-valid.xml`:
- tests: **792**
- failures: **0**
- errors: **0**
- skipped: **0**
- duration: **4176.881s**
- result: **PASS**

The prior PTY handle expired after completion; durable JUnit plus absence of the recorded process tree is the source-of-truth final evidence. The broader command was not restarted.

## Frozen baseline verification

`python tools/frozen_master_guard.py`:

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
RAW_SHA256=abb08e8114be3ace0d81ceccf8a3dea45c78a6268c64fae4c332d0644fa1e303
```

Frozen semantic SHA is unchanged.

## Final exact-head static/security review

- `git diff --check`: **PASS**.
- `node --check` on Main/preload/contract/handler/utility/test JS surfaces: **PASS**.
- Renderer API review: only bounded `productionUtility.getBridgeStatus()` is exposed; no raw privileged primitive is returned by `contextBridge`.
- Main IPC review: exact sender + main-frame + origin validation occurs before request validation/dispatch.
- IPC contract review: strict exact-key/version/token/capability validation and redacted error responses.
- Utility bridge review: bounded request timeout, duplicate request-ID rejection, response validation, pending-request cleanup on timeout/exit/close.
- Package wiring review: only the intended typed IPC/Utility modules are included in Electron build files.

## Verification conclusion

IMP-071 is locally verified for its claimed typed IPC / Production Utility bridge scope on the exact working head. Evidence supports proceeding to Git side-effect guard and exact-scope commit/push/PR lifecycle. This file does not claim merge or MAIN VERIFIED until exact PR-head CI/review/merge and post-merge main verification complete.
