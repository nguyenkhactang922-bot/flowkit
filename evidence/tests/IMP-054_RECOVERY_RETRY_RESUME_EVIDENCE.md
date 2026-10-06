# IMP-054 Retry / Resume / Remote Ambiguity Recovery Evidence

## Scope
- Migration v8 adds immutable append-only `studio_generation_recovery_event` evidence on the shared SQLiteWriteOwner; GenerationJob remains the sole mutable job-state authority.
- Provider-neutral RecoveryCoordinator orchestrates restart/retry/reconcile decisions through the existing GenerationJob four-axis CAS transition table.
- NO RETRY WITHOUT PROOF: safe requeue requires durable transport-not-dispatched, proven-absent, or verified same-job idempotency evidence.
- Generic timeout/crash/connection loss after possible dispatch is provider ambiguity and must reconcile; it never authorizes blind resubmit.
- RecoveryEvent stores attempt identity, observed job revision, trigger, failure taxonomy, proof kind, decision, provider-profile pin, evidence refs, normalized provider observation and recovered remote lineage.
- Provider transport/reconcile calls remain outside DB transactions.

## Targeted / direct affected verification
```text
Recovery targeted: 10/10 PASS
Latest direct/affected JUnit set: 73 unique tests / 73 PASS / 0 FAIL
```

Targeted coverage proves:
- migration v8 append-only evidence without a second job-status authority;
- crash before submit can requeue only from durable no-dispatch proof;
- crash after possible submit never blind-resubmits and enters ambiguous hold;
- poll timeout can recover the same remote handle and resume existing work;
- proven-absent reconciliation is the only absence path to safe requeue;
- verified same-job idempotency may requeue without allocating a new job;
- RecoveryEvent replay is immutable/idempotent and conflicting replay fails closed;
- cancellation race preserves remote truth when success wins;
- remote-canceled evidence without local cancel intent fails closed;
- restart scan returns only remote/recovery in-flight jobs.

Direct/affected JUnit evidence additionally covers persistence/schema migration, GenerationJob guards/transitions, scheduler recovery interaction, provider routing/reconciliation surfaces and generation-job compatibility.

## Broader valid Windows regression
Broader work was executed in non-overlapping JUnit batches to preserve durable exit/result evidence across FileMCP interruptions.

```text
Latest result per broader testcase: 202 unique tests
PASS: 202
FAIL: 0
```

One earlier broader batch had exactly one stale migration expectation in `test_schema_v4_upgrades_to_latest_and_preserves_history` after schema v8 was introduced. The expectation was updated to include migration v8, and `imp054-brainpack-fix.xml` proves that exact failed test PASS. All other latest broader results are PASS. Provider-routing batch `imp054-broad-e2a.xml` is 13/13 PASS. Zero-length clean-attempt logs are not counted as PASS evidence.

## Static / authority verification
- Frozen Master guard: PASS.
- Frozen semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- `py_compile` on IMP-054 implementation/tests: PASS.
- `git diff --check`: PASS.
- Recovery implementation TODO/FIXME/NotImplemented scan: NONE.
- Recovery implementation direct network/provider-submit leakage scan: NONE.

## Exact review result
- `RecoveryCoordinator` has no competing status store; all mutable state changes use GenerationJobRepository CAS transitions.
- Existing closed transition commands are reused; IMP-054 only hardens proof guards so `transport_not_dispatched` is accepted alongside proven absence / verified same-job idempotency for recovery-safe transitions.
- `RecoveryEventRepository` is append-only at both repository semantics and SQLite trigger level (`no_update`, `no_delete`).
- Recovery attempt identity is deterministic per GenerationJob + recovery attempt, and conflicting replay fails closed.
- `ProviderAdapterRecoveryProbe` never fabricates absence; HANDLE_ONLY adapters without durable handle map ambiguity to `STILL_AMBIGUOUS`.
- A timeout/transport/crash after possible dispatch remains `PROVIDER_AMBIGUITY + RECONCILIATION_REQUIRED` unless stronger evidence exists.
- Safe requeue cannot occur unless provider state has been reconciled to `NOT_SUBMITTED` and scheduler recovery transition receives the same proof facts.
- Recovered remote handles/observations resume the existing canonical job; no new GenerationJob identity is allocated.
- Cancellation-race terminal observations are reconciled through the existing provider-state authority.
- No provider/network operation occurs inside the SQLite write transaction.

RESULT = IMP-054 LOCAL VERIFIED
