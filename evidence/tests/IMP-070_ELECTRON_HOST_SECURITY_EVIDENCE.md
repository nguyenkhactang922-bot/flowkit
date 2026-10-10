# IMP-070 Electron Host Shell Security Baseline Evidence

Date: 2026-10-10
Branch: `chatgpt/IMP-070-electron-host-shell-security`
Base HEAD: `39ad22e016ed8e4ad977679989401020183eb459`

## Scope

IMP-070 introduces the target Electron host-shell security baseline without changing the existing React/Vite dashboard or FastAPI/service authority. The task adds a hardened Electron Main shell, a narrow preload surface, a privileged custom `flowkit://app` protocol, restrictive navigation/window/webview policy, a restrictive renderer CSP, and an electron-builder packaging skeleton.

Frozen Security §84 boundaries enforced here:
- `nodeIntegration=false`;
- `contextIsolation=true`;
- `sandbox=true`;
- `webSecurity=true`;
- `allowRunningInsecureContent=false`;
- `experimentalFeatures=false`;
- `webviewTag=false` and drag-drop navigation disabled;
- external/foreign navigation denied;
- all new windows denied;
- webviews denied;
- custom app protocol preferred over `file://`;
- preload exposes no generic `ipcRenderer`, filesystem, process or shell bridge;
- renderer receives no long-lived secret access;
- typed privileged IPC/sender validation remains owned by IMP-071 and is not falsely claimed here.

## Implementation surfaces

- `.gitignore`
- `desktop/main.cjs`
- `desktop/preload.cjs`
- `desktop/security-policy.cjs`
- `desktop/renderer/index.html`
- `desktop/package.json`
- `desktop/package-lock.json`
- `desktop/tests/security-policy.test.cjs`
- `tests/unit/test_electron_host_security.py`

No FastAPI, dashboard, provider, persistence, QA or frozen Master implementation was modified.

## Supply-chain / packaging pins

- Electron: `44.7.0`
- electron-builder: `26.15.3`
- `asar=true`
- Windows target skeleton: `nsis`

Both `package.json` and `package-lock.json` pin the same Electron/electron-builder versions.

## Targeted security proof

Node behavior tests:

```text
node --test desktop/tests/security-policy.test.cjs
3/3 PASS
```

Python static/security targeted JUnit `.tmp/imp070-targeted.xml`:
- tests: **6**
- failures: **0**
- errors: **0**
- skipped: **0**

Targeted proof covers:
- package/security configuration pins;
- explicit BrowserWindow hardening flags;
- custom secure protocol instead of `file://` loading;
- no external-shell call from the host shell;
- no generic privileged preload bridge;
- restrictive renderer CSP;
- denial of foreign navigation, all new windows and webviews;
- renderer path traversal denial.

## Affected service-boundary regression

JUnit `.tmp/imp070-affected.xml`:
- tests: **9**
- failures: **0**
- errors: **0**
- skipped: **0**

Affected regression covers the existing project/session and upload API boundaries to verify the new Electron target shell did not shift current service authority.

## Broader valid Windows regression

JUnit `.tmp/imp070-broader-valid.xml`:
- tests: **792**
- failures: **0**
- errors: **0**
- skipped: **0**

The broader command excluded the already-PASS IMP-070 targeted and affected files plus the repository's established Windows/POSIX-only exclusions. Targeted and affected stages were not rerun inside broader.

## Frozen baseline verification

`python tools/frozen_master_guard.py`:

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
```

Frozen semantic SHA is unchanged.

## Final static / security review

- `node --check` for `main.cjs`, `preload.cjs`, `security-policy.cjs` and security-policy test: **PASS**;
- `package.json` and `package-lock.json` JSON parse/version consistency: **PASS**;
- forbidden-token scan for generic IPC/process/shell and insecure BrowserWindow flags: **CLEAN**;
- `git diff --check`: **PASS**;
- exact-head authority review: existing React/Vite + FastAPI/service authority unchanged; Electron host remains a new target layer;
- no generic IPC capability is introduced in IMP-070; IMP-071 remains the typed IPC owner.

## Verification conclusion

IMP-070 is locally verified for the Electron Host Shell Security Baseline on the final worktree. This evidence supports proceeding to Git side-effect guard and exact-scope commit/push/PR lifecycle. It does not claim packaged Windows enforcement, merge, or MAIN VERIFIED until exact PR-head CI/review/merge and post-merge main verification complete.
