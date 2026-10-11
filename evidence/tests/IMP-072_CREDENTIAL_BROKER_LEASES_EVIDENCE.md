# IMP-072 Credential Broker / safeStorage / Leases Evidence

Date: 2026-10-11
Branch: `chatgpt/IMP-072-credential-broker-leases`
Base HEAD: `021cdb068944f69059099b432767cffab4c67e9c`

## Scope and authority

IMP-072 implements the Host Security Broker credential boundary defined by Frozen Master §85 and ADR-0016 without expanding Renderer privilege or moving long-lived secret authority into Production Utility/provider code.

Verified authority invariants:
- Electron Main / Host Security Broker owns long-lived secret lifecycle and Electron `safeStorage` access.
- Renderer receives no plaintext secret, decrypt method, generic credential channel or raw broker capability.
- Persistent vault content contains encrypted credential payload plus metadata only; project/domain persistence is not used for secret bytes.
- Production Utility is a temporary lease consumer, not a credential vault owner.
- Main authorizes exact Utility provider/operation scope and keeps the Utility session token internal to the bridge.
- Lease identity pins utility instance, credential identity/version, provider, operation, correlation and bounded TTL; lease redemption is single-use.
- Credential rotation/revocation and Utility exit/bridge close invalidate outstanding authorization.
- Linux `basic_text` safeStorage backend and unavailable encryption fail closed.
- Browser/session credentials remain provider-specific compatibility concerns and are not generalized into long-lived API-key project truth.

## Implementation surfaces

- `desktop/credential-broker.cjs`
- `desktop/production-utility-bridge.cjs`
- `desktop/main.cjs`
- `desktop/package.json`
- `desktop/tests/credential-broker.test.cjs`
- `tests/unit/test_electron_host_security.py`

## Exact-head review finding and repair

The first locally-green implementation instantiated `SafeStorageCredentialBroker` in Main but did not yet provide an actual trusted Production Utility lease-consumer path. Frozen Master §85 and ADR-0016 require Production Utility to receive only scoped short-lived leases, so this was treated as a real pre-commit review defect rather than accepted because tests were green.

Repair applied:
- Main injects the Credential Broker into `ProductionUtilityBridge`.
- Main owns Utility instance/session identity and never exposes the session token to Renderer.
- Main must explicitly authorize provider/operation scope before credential messages are accepted.
- Internal Main↔Utility child transport supports typed lease issue and one-use redeem messages.
- Lease issue response is metadata-only; plaintext appears only after authorized redemption and only on the trusted child transport.
- Wrong operation/provider/session, replay, expiry, revoke and stale-after-rotation paths fail closed.
- Utility exit/bridge close revokes its broker session and outstanding leases.
- Renderer API and Renderer IPC allowlist remain unchanged and secret-free.

## Targeted Node security verification

Canonical direct command after the review repair:

```text
node --test tests/security-policy.test.cjs tests/ipc-contract.test.cjs tests/credential-broker.test.cjs
```

Run from `desktop/`.

Result:
- tests: **22**
- pass: **22**
- fail: **0**
- skipped: **0**

Coverage includes existing Electron hardening/typed IPC tests plus credential broker vault/metadata behavior, Renderer denial, provider/operation/session scope denial, expiry, replay, Utility revoke, credential revoke, rotation invalidation, insecure backend denial and the trusted Production Utility internal lease transport.

A prior `npm run test:security` invocation did **not execute tests** because the local `desktop/node_modules/npm` bootstrap was broken (`npm-cli.js` / `npm-prefix.js` missing). The exact package-script payload was therefore executed directly with Node and passed 22/22. The npm failure is classified as a local harness invocation failure, not a product/test failure.

## Python Electron security targeted verification

Exact-review-head JUnit `.tmp/imp072-review-targeted.xml`:
- tests: **9**
- failures: **0**
- errors: **0**
- skipped: **0**
- duration: **1.878s**
- PTY exit: **0**
- result: **PASS**

The targeted Python gate statically verifies package inclusion, Main safeStorage/broker ownership, broker injection into Production Utility bridge, internal lease issue/redeem transport markers, and absence of Renderer credential/secret capability.

## Affected service-boundary regression

Earlier exact-task affected JUnit `.tmp/imp072-affected.xml`:
- tests: **9**
- failures: **0**
- errors: **0**
- skipped: **0**
- result: **PASS**

This checkpoint is retained after the exact-head review repair because the repair changes only Electron Main/bridge/security-test surfaces and does not modify the backend project/session/upload boundaries exercised by this stage.

## Broader valid Windows regression

JUnit `.tmp/imp072-broader-valid.xml`:
- tests: **792**
- failures: **0**
- errors: **0**
- skipped: **0**
- duration: **3799.249s**
- result: **PASS**

The recorded broader PID `98584` was absent after completion, no matching pytest process remained, and the durable JUnit contained zero failing/error cases. The stage was therefore classified PASS and was not restarted after its PTY handle disappeared.

This checkpoint is retained after the exact-head review repair because the Windows-valid broader envelope explicitly excluded `tests/unit/test_electron_host_security.py` and Python unit regression does not execute the desktop Node security tests. The changed desktop lease-transport boundary was instead revalidated by the 22/22 Node security suite and 9/9 Python Electron targeted gate above.

## Frozen baseline and static verification

Final exact-review-head `python tools/frozen_master_guard.py`:

```text
FROZEN_MASTER_GUARD=PASS
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
RAW_SHA256=abb08e8114be3ace0d81ceccf8a3dea45c78a6268c64fae4c332d0644fa1e303
```

Additional static gates:
- `git diff --check`: **PASS**.
- `node --check desktop/credential-broker.cjs`: **PASS**.
- `node --check desktop/production-utility-bridge.cjs`: **PASS**.
- `node --check desktop/main.cjs`: **PASS**.
- `python -m py_compile tests/unit/test_electron_host_security.py`: **PASS**.

## Evidence limitation / claim discipline

This evidence proves the local implementation contract and isolated Electron security boundary behavior available in the repository environment. It does **not** claim packaged target-Windows `safeStorage`/DPAPI live proof, real provider credential use, production provider networking, or release acceptance. Frozen Master §85 explicitly leaves packaged target-runtime safeStorage proof to later implementation/release evidence.

## Verification conclusion

IMP-072 is locally verified for the claimed Credential Broker / safeStorage / scoped lease boundary on the exact working head. Renderer secret authority remains denied; Main owns long-lived secret lifecycle; trusted Production Utility has a fail-closed scoped short-lived lease-consumer path. Evidence supports proceeding to Git side-effect guard and exact-scope commit/push/PR lifecycle. Merge and MAIN VERIFIED are not claimed by this file until exact PR-head CI/review/merge and post-merge main verification complete.
