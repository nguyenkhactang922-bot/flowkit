# IMP-073 Renderer / Dashboard Adaptation Evidence

Date: 2026-10-11
Branch: `chatgpt/IMP-073-renderer-dashboard-adaptation`
Base main SHA: `9368a1ce4696e80752bb830481b7c0735da05756`

## Scope

IMP-073 adapts the Electron renderer and existing React/Vite dashboard to consume a typed, versioned Studio application read model without creating UI-owned Story/Shot/State/Profile truth.

The implementation keeps the Renderer/Application boundary narrow:
- exactly eight Frozen Master §93 view sections;
- typed/allowlisted preload -> Main -> Production Utility capability;
- strict sender/origin/frame/request/response validation;
- no generic IPC invoke, raw `ipcRenderer`, filesystem/process/shell capability or secret accessor in renderer APIs;
- canonical read-model absence fails closed with redacted `APPLICATION_READ_MODEL_UNAVAILABLE`;
- legacy React/Vite `/api/*` data is explicitly `LEGACY_COMPATIBILITY`, never canonical Studio authority.

## Review repairs

1. React changed-file lint found synchronous `setState` inside `useEffect` in `StudioReadModelPanel.tsx`. The component was changed to keep an asynchronous `{ projectId, model, error }` load state and derive loading from project identity.
2. Exact-head authority/security review found that a schema-valid canonical response could be accepted for the wrong project. Successful Studio read-model responses are now bound to the requested `projectId` at Production Utility bridge, Main, and preload validation boundaries. Two negative tests prove wrong-project responses fail closed.

## Dashboard verification

Changed-file ESLint:

```text
npx eslint src/pages/ProjectDetailPage.tsx src/api/studioReadModel.ts src/components/studio/StudioReadModelPanel.tsx
PASS / exit 0
```

A direct `npm.cmd run build` retry failed before TypeScript/Vite execution because the locally materialized `node_modules/npm/bin/npm-prefix.js` and `npm-cli.js` were absent. This is classified as a local npm-wrapper/bootstrap failure, not a product build failure.

The exact build payload was then executed from materialized local binaries:

```text
node node_modules/typescript/bin/tsc -b
node node_modules/vite/bin/vite.js build
PASS / exit 0
2058 modules transformed
built in 9.94s
```

Non-fatal warnings only:
- future Vite native-config warning for `__dirname`;
- existing chunk-size warning above 500 kB.

## Desktop security / IPC verification

Affected desktop files passed `node --check`.

Canonical direct targeted command from `desktop/`:

```text
node --test tests/security-policy.test.cjs tests/ipc-contract.test.cjs tests/credential-broker.test.cjs
```

Result after exact-head review repair:

```text
tests 27
pass 27
fail 0
cancelled 0
skipped 0
todo 0
```

Coverage includes:
- renderer secret/credential denial and safeStorage broker invariants;
- narrow allowlisted IPC surface and invalid sender/origin/frame rejection;
- strict Studio read-model schema/version validation;
- all eight required §93 view sections;
- provider/internal field rejection;
- redacted error envelopes;
- canonical provider absence fail-closed;
- wrong-project canonical response rejection at contract and Utility bridge boundaries;
- no generic renderer invoke primitives.

## Exact-head static / security review

```text
git diff --check
PASS
```

Renderer leakage scan over Electron renderer/preload and dashboard Studio surfaces:

```text
no raw ipcRenderer
no child_process/fs/shell/process.env/safeStorage/credential-broker exposure
no generic:invoke / generic.invoke
PASS
```

The Production Utility still fails closed when no canonical application read-model provider is installed. Repository search found no stronger canonical provider implementation to wire at this task boundary; no DB/provider-internal shortcut or fake canonical snapshot was introduced.

## Frozen baseline verification

```text
python tools/frozen_master_guard.py
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
RAW_SHA256=abb08e8114be3ace0d81ceccf8a3dea45c78a6268c64fae4c332d0644fa1e303
```

## Local verdict

`IMP-073 LOCAL VERIFIED` for the current worktree, subject to Git exact-scope commit, PR exact-head CI/review, merge, and post-merge MAIN verification.
