# IMP-006 — Observability / Error / Evidence Core Evidence

## Task

IMP-006 — Observability / Error / Evidence Core

Branch:
`chatgpt/IMP-006-observability-error-evidence`

Base:
`77c828f04c1a40027dbf7f0172121d9582e1c8d8`

Depends:
`IMP-004 = MAIN VERIFIED`

Frozen Master SHA:
`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Implemented scope

Provider-neutral observability/error/evidence core:
- `agent/studio/observability.py`
- public exports through `agent/studio/__init__.py`
- schema migration V4 through `agent/studio/persistence.py`

Contracts:
- typed `CorrelationId`
- async/sync correlation propagation via context variable
- exact frozen `ErrorClass` taxonomy
- typed `RetryDisposition`
- provider ambiguity requires reconciliation before retry
- immutable `StudioErrorRecord`
- typed `EvidenceReference`
- immutable structured `EvidenceEvent`
- `DECISION` / `FAILURE` event distinction
- recursive deterministic secret/token redaction
- append-only `EvidenceEventRepository`
- event authority explicitly fixed to `EVIDENCE_ONLY`

Schema V4:
- `studio_evidence_event`
- correlation index
- DB triggers reject UPDATE/DELETE
- no current-pointer table or current-state transition API

Authority invariants:
- event/log evidence never becomes current-state authority
- generic `FAILED` error code rejected
- provider ambiguity cannot be collapsed to normal retry
- user-safe message/details/evidence metadata/provenance are redacted before persistence
- exact source-version/evidence references can be retained with provenance
- frozen Master bytes unchanged

## Test / verification evidence

Python 3.13 isolated environment.

Targeted IMP-006:
- **10/10 PASS**

Cross-layer Studio V1→V4:
- **57/57 PASS**

Full Windows unit regression:
- **446 PASS / 3 FAIL**

The three failures are the exact pre-existing Windows/POSIX `/tmp` assertions already documented by earlier IMP tasks:
- two parameterized `test_claude_agy_providers_include_read_the_images_at` cases
- `test_single_sheet_wrapper_wording_matches_original_singular_form`

No IMP-006 test failed.

Clean unaffected regression excluding exactly those three cases:
- **446 PASS / 3 deselected**

Frozen Master guard:
- **PASS**
- canonical SHA unchanged

Diff check:
- **PASS**

## Failure/interrupt handling

- First cross-layer wildcard invocation failed because PowerShell passed `test_studio_*.py` literally to pytest. This was an invocation failure, not a code/test failure.
- A subsequent cross-layer call timed out at the bridge; process verification showed no remaining test process, so only that interrupted stage was resumed.
- Full regression also encountered one bridge timeout; process verification showed no running test, then only the full-regression stage was resumed.
- No PASS was claimed from a timed-out command.

## Event-vs-current-state proof

A canonical semantic version was persisted with current lifecycle `DRAFT`.
A separate evidence event with decision code `APPROVED` was appended.
After event persistence:
- canonical current pointer remained exactly unchanged
- lifecycle remained `DRAFT`
- revision remained `0`

This proves the event/evidence repository is not current-state authority.

## Secret redaction proof

Tests inject representative secrets through:
- Authorization/Bearer
- api_key
- access_token
- password
- cookie
- client_secret
- token query/string material

Persistable error/event payloads contain `[REDACTED]` and do not contain the raw fixture secret values.

## Local verdict

**IMP-006 = LOCAL VERIFIED**

Remote PR/Ubuntu CI/exact-head review/merge/main verification remain pending.
