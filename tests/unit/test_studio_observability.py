"""IMP-006 tests for observability / error / evidence core."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import aiosqlite
import pytest
from pydantic import ValidationError

from agent.studio import (
    CorrelationId,
    ErrorClass,
    EvidenceEvent,
    EvidenceEventConflict,
    EvidenceEventKind,
    EvidenceEventRepository,
    EvidenceReference,
    LifecycleState,
    LogicalId,
    Provenance,
    RetryDisposition,
    SemanticRecordMetadata,
    SourceVersionBinding,
    SQLiteWriteOwner,
    StudioErrorRecord,
    VersionId,
    VersionRef,
    VersionRepository,
    correlation_scope,
    current_correlation_id,
    redact_secrets,
    redact_text,
)
from agent.studio.persistence import DEFAULT_MIGRATIONS, ensure_schema_compatibility


NOW = datetime(2026, 9, 26, 0, 30, tzinfo=timezone.utc)
CORR = CorrelationId("corr:imp006")


def _provenance(reason: str = "observability evidence") -> Provenance:
    return Provenance(
        source_refs=("evidence:imp006",),
        actor_ref="studio:test",
        reason=reason,
        recorded_at=NOW,
        correlation_id=CORR.root,
    )


def _source_binding() -> SourceVersionBinding:
    return SourceVersionBinding(
        role="subject",
        source=VersionRef(
            logical_id=LogicalId("story:obs"),
            version_id=VersionId("v1"),
        ),
    )


def _decision_event(
    *,
    event_id: str = "event:decision-1",
    reason: str = "gate accepted",
) -> EvidenceEvent:
    return EvidenceEvent(
        event_id=event_id,
        event_kind=EvidenceEventKind.DECISION,
        correlation_id=CORR,
        responsible_boundary="studio:test-boundary",
        occurred_at=NOW,
        source_versions=(_source_binding(),),
        input_refs=(_source_binding().source,),
        output_refs=(),
        evidence_refs=(
            EvidenceReference(
                evidence_id="evidence:test-result-1",
                evidence_class="runtime_test",
                locator="evidence/tests/imp006.txt",
                claim_scope="targeted contract behavior",
            ),
        ),
        provenance=_provenance(),
        decision_code="GATE_PASS",
        reason=reason,
        attributes={"result": "pass"},
    )


def _error(
    *,
    retryability: RetryDisposition = RetryDisposition.RECONCILIATION_REQUIRED,
) -> StudioErrorRecord:
    return StudioErrorRecord(
        error_id="error:provider-ambiguity-1",
        error_code="PROVIDER_SUBMISSION_AMBIGUOUS",
        error_class=ErrorClass.PROVIDER_AMBIGUITY,
        retryability=retryability,
        responsible_boundary="generation:provider-adapter",
        evidence=(
            EvidenceReference(
                evidence_id="evidence:provider-response-1",
                evidence_class="provider_response",
                locator="request.log?token=supersecret",
                metadata={"Authorization": "Bearer abcdefghijklmnop"},
            ),
        ),
        user_safe_message="Provider result is uncertain; token=supersecret",
        correlation_id=CORR,
        source_versions=(_source_binding(),),
        provenance=_provenance("classify provider ambiguity"),
        occurred_at=NOW,
        details={
            "access_token": "supersecret",
            "nested": {"password": "hunter2"},
            "message": "Authorization: Bearer abcdefghijklmnop",
        },
    )


def test_recursive_secret_redaction_is_deterministic_and_preserves_safe_fields():
    value = {
        "Authorization": "Bearer abcdefghijklmnop",
        "nested": {
            "api_key": "secret-api-key",
            "X-API-Key": "vendor-secret-key",
            "X-Access-Token": "vendor-access-token",
            "safe": "keep-me",
        },
        "message": "token=abc123 password:topsecret Bearer zyxwvutsrqpon",
        "items": [{"cookie": "session-cookie"}, "client_secret=inline-secret"],
    }

    first = redact_secrets(value)
    second = redact_secrets(value)
    serialized = json.dumps(first, sort_keys=True)

    assert first == second
    assert first["Authorization"] == "[REDACTED]"
    assert first["nested"]["api_key"] == "[REDACTED]"
    assert first["nested"]["X-API-Key"] == "[REDACTED]"
    assert first["nested"]["X-Access-Token"] == "[REDACTED]"
    assert first["nested"]["safe"] == "keep-me"
    assert "secret-api-key" not in serialized
    assert "vendor-secret-key" not in serialized
    assert "vendor-access-token" not in serialized
    assert "topsecret" not in serialized
    assert "session-cookie" not in serialized
    assert "inline-secret" not in serialized
    assert "zyxwvutsrqpon" not in serialized


def test_redact_text_handles_bearer_and_inline_key_value_secrets():
    value = "Authorization: Bearer abcdefghijklmnop; refresh_token=refresh123"
    redacted = redact_text(value)

    assert "abcdefghijklmnop" not in redacted
    assert "refresh123" not in redacted
    assert "[REDACTED]" in redacted


@pytest.mark.asyncio
async def test_correlation_scope_propagates_across_async_tasks_and_resets():
    async def child():
        await asyncio.sleep(0)
        return current_correlation_id(required=True)

    assert current_correlation_id() is None
    with correlation_scope(CORR) as bound:
        assert bound == CORR
        assert current_correlation_id(required=True) == CORR
        assert await asyncio.create_task(child()) == CORR

    assert current_correlation_id() is None


def test_provider_ambiguity_cannot_be_collapsed_to_normal_retry():
    with pytest.raises(ValidationError, match="reconciliation"):
        _error(retryability=RetryDisposition.RETRYABLE)

    error = _error()
    payload = error.model_dump(mode="json")
    serialized = json.dumps(payload, sort_keys=True)

    assert error.retryability is RetryDisposition.RECONCILIATION_REQUIRED
    assert "supersecret" not in serialized
    assert "hunter2" not in serialized
    assert "abcdefghijklmnop" not in serialized
    assert error.evidence[0].metadata["Authorization"] == "[REDACTED]"


def test_generic_failed_error_code_is_rejected():
    with pytest.raises(ValidationError, match="generic error code"):
        StudioErrorRecord(
            error_id="error:generic",
            error_code="FAILED",
            error_class=ErrorClass.QA,
            retryability=RetryDisposition.NOT_RETRYABLE,
            responsible_boundary="qa:gate",
            evidence=(),
            user_safe_message="QA failed",
            correlation_id=CORR,
            source_versions=(),
            provenance=_provenance("qa error"),
            occurred_at=NOW,
        )


def test_failure_event_requires_matching_typed_error_and_correlation():
    error = _error()
    event = EvidenceEvent(
        event_id="event:failure-1",
        event_kind=EvidenceEventKind.FAILURE,
        correlation_id=CORR,
        responsible_boundary="generation:provider-adapter",
        occurred_at=NOW,
        source_versions=(_source_binding(),),
        provenance=_provenance("record failure"),
        reason="provider result ambiguous",
        error=error,
        attributes={"Authorization": "Bearer anothersecret"},
    )
    serialized = event.model_dump_json()

    assert event.authority_scope == "EVIDENCE_ONLY"
    assert "anothersecret" not in serialized
    assert "supersecret" not in serialized

    with pytest.raises(ValidationError, match="match event correlation"):
        EvidenceEvent(
            event_id="event:failure-bad-correlation",
            event_kind=EvidenceEventKind.FAILURE,
            correlation_id=CorrelationId("corr:different"),
            responsible_boundary="generation:provider-adapter",
            occurred_at=NOW,
            provenance=Provenance(
                source_refs=("evidence:imp006",),
                actor_ref="studio:test",
                reason="record failure",
                recorded_at=NOW,
                correlation_id="corr:different",
            ),
            reason="provider result ambiguous",
            error=error,
        )


@pytest.mark.asyncio
async def test_evidence_event_repository_is_append_only_and_restart_readable(tmp_path):
    db_path = tmp_path / "studio.db"
    writer = SQLiteWriteOwner(db_path)
    await writer.start()
    repo = EvidenceEventRepository(writer)
    event = _decision_event()

    try:
        assert await repo.append(event) == event
        assert await repo.append(event) == event
        loaded = await repo.get(event.event_id)
        assert loaded == event
        assert await repo.list_by_correlation(CORR) == [event]

        async def illegal_update(tx):
            await tx.execute(
                """
                UPDATE studio_evidence_event
                SET responsible_boundary='rewritten'
                WHERE event_id=?
                """,
                (event.event_id,),
            )

        with pytest.raises(aiosqlite.IntegrityError, match="append-only"):
            await writer.execute(illegal_update)
    finally:
        await writer.close()

    writer2 = SQLiteWriteOwner(db_path)
    await writer2.start()
    try:
        repo2 = EvidenceEventRepository(writer2)
        assert await repo2.get(event.event_id) == event
        assert await repo2.list_by_correlation(CORR) == [event]
    finally:
        await writer2.close()


@pytest.mark.asyncio
async def test_event_identity_conflict_is_rejected(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    repo = EvidenceEventRepository(writer)
    try:
        await repo.append(_decision_event())
        with pytest.raises(EvidenceEventConflict):
            await repo.append(
                _decision_event(reason="different immutable evidence")
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_event_evidence_does_not_mutate_canonical_current_state(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    versions = VersionRepository(writer)
    events = EvidenceEventRepository(writer)

    try:
        metadata = SemanticRecordMetadata(
            logical_id=LogicalId("story:obs"),
            version_id=VersionId("v1"),
            provenance=_provenance("create story version"),
            created_at=NOW,
        )
        await versions.create_initial(
            metadata=metadata,
            payload={"title": "Canonical story"},
            status=LifecycleState.DRAFT,
        )
        before = await versions.get_current(LogicalId("story:obs"))
        assert before is not None
        assert before.status is LifecycleState.DRAFT
        assert before.revision == 0

        # This event claims only that a gate evaluator observed PASS. It must
        # never silently promote current canonical lifecycle state.
        await events.append(
            EvidenceEvent(
                event_id="event:observed-approval",
                event_kind=EvidenceEventKind.DECISION,
                correlation_id=CORR,
                responsible_boundary="qa:story-gate",
                occurred_at=NOW,
                source_versions=(_source_binding(),),
                input_refs=(_source_binding().source,),
                provenance=_provenance("observe story gate"),
                decision_code="APPROVED",
                reason="gate evaluator observed pass",
                attributes={"status": "APPROVED"},
            )
        )

        after = await versions.get_current(LogicalId("story:obs"))
        assert after == before
        assert after.status is LifecycleState.DRAFT
        assert after.revision == 0
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_schema_v3_upgrades_to_v4_and_preserves_migration_history(tmp_path):
    db_path = tmp_path / "studio.db"
    assert await ensure_schema_compatibility(
        db_path,
        supported_version=3,
        migrations=DEFAULT_MIGRATIONS[:3],
    ) == 3

    writer = SQLiteWriteOwner(db_path)
    await writer.start()
    try:
        async with aiosqlite.connect(str(db_path)) as db:
            rows = await (
                await db.execute(
                    "SELECT version, name FROM studio_schema_migration ORDER BY version"
                )
            ).fetchall()
        assert rows == [
            (1, "studio_persistence_foundation"),
            (2, "studio_version_provenance_repository"),
            (3, "studio_dependency_invalidation"),
            (4, "studio_observability_evidence"),
        ]
    finally:
        await writer.close()
