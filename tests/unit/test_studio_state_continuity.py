"""IMP-042 StateSnapshot / ContinuityLedger / ApprovedEndState tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    ContinuityConstraint,
    ContinuityLedger,
    ContinuityLedgerRepository,
    EntityKind,
    EntityVersion,
    InvalidationRepository,
    LegacyMediaChainConditioning,
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    StateApprovalBlocked,
    StateContinuityError,
    StateFact,
    StateFactNamespace,
    StatePropagationBlocked,
    StateSnapshot,
    StateSnapshotRepository,
    VersionId,
    VersionRef,
    VersionRepository,
    build_continuity_binding_provenance,
    build_continuity_ledger_provenance,
    build_state_snapshot_provenance,
    continuity_ledger_logical_id,
    derive_state_delta,
    state_snapshot_logical_id,
)
from agent.studio.persistence import SQLiteWriteOwner


NOW = datetime(2026, 10, 3, 7, 30, tzinfo=timezone.utc)
PROJECT_ID = LogicalId("project:film")
OTHER_PROJECT_ID = LogicalId("project:other")
SCOPE_KEY = "timeline:shot-001"
ENTITY_REF = VersionRef(
    logical_id=LogicalId("entity:legacy-char-001"),
    version_id=VersionId("entity-v1"),
)
CHANGE_V1 = VersionRef(
    logical_id=LogicalId("scene-dramatic-beat:project:film:beat-001"),
    version_id=VersionId("beat-v1"),
)
CHANGE_V2 = VersionRef(
    logical_id=LogicalId("scene-dramatic-beat:project:film:beat-002"),
    version_id=VersionId("beat-v1"),
)
OUTCOME_V1 = VersionRef(
    logical_id=LogicalId("artifact:project:film:shot-001"),
    version_id=VersionId("artifact-v1"),
)
OUTCOME_V2 = VersionRef(
    logical_id=LogicalId("artifact:project:film:shot-002"),
    version_id=VersionId("artifact-v1"),
)
QA_V1 = VersionRef(
    logical_id=LogicalId("qa-result:project:film:shot-001"),
    version_id=VersionId("qa-v1"),
)
QA_V2 = VersionRef(
    logical_id=LogicalId("qa-result:project:film:shot-002"),
    version_id=VersionId("qa-v1"),
)
POLICY_REF = VersionRef(
    logical_id=LogicalId("approval-policy:project:film"),
    version_id=VersionId("policy-v1"),
)
REFERENCE_REF = VersionRef(
    logical_id=LogicalId("reference-asset:project:film:test"),
    version_id=VersionId("reference-v1"),
)
APPROVED_ARTIFACT_REF = VersionRef(
    logical_id=LogicalId("artifact:project:film:approved"),
    version_id=VersionId("artifact-v1"),
)


def _seed_provenance(reason: str = "IMP-042 fixture") -> Provenance:
    return Provenance(
        source_refs=("evidence:imp042-fixture",),
        actor_ref="studio:imp042-test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp042-test",
    )


async def _seed_version(
    versions: VersionRepository,
    ref: VersionRef,
    payload: dict,
    *,
    status: LifecycleState = LifecycleState.APPROVED,
) -> None:
    await versions.create_initial(
        metadata=SemanticRecordMetadata(
            logical_id=ref.logical_id,
            version_id=ref.version_id,
            provenance=_seed_provenance(),
            created_at=NOW,
        ),
        payload=payload,
        status=status,
    )


async def _seed_common(writer: SQLiteWriteOwner) -> VersionRepository:
    versions = VersionRepository(writer)
    entity = EntityVersion(
        entity_id=ENTITY_REF.logical_id,
        version_id=ENTITY_REF.version_id,
        kind=EntityKind.CHARACTER,
        name="Lan",
        project_ids=(PROJECT_ID,),
        description="canonical identity only",
    )
    await _seed_version(versions, ENTITY_REF, entity.model_dump(mode="json"))
    for ref in (
        CHANGE_V1,
        CHANGE_V2,
        OUTCOME_V1,
        OUTCOME_V2,
        QA_V1,
        QA_V2,
        POLICY_REF,
        REFERENCE_REF,
        APPROVED_ARTIFACT_REF,
    ):
        await _seed_version(versions, ref, {"fixture": ref.logical_id.root})
    return versions


def _fact(value: str = "cream blouse") -> StateFact:
    return StateFact(
        namespace=StateFactNamespace.WARDROBE,
        key="upper_body",
        value_json=f'{{"description":"{value}"}}',
        subject_ref=ENTITY_REF,
    )


def _snapshot(
    *,
    version: str = "state-v1",
    previous: VersionRef | None = None,
    story_time: str = "T+00:00",
    value: str = "cream blouse",
    change_ref: VersionRef = CHANGE_V1,
    outcome_ref: VersionRef = OUTCOME_V1,
    context_refs: tuple[VersionRef, ...] = (),
) -> StateSnapshot:
    return StateSnapshot(
        project_id=PROJECT_ID,
        state_snapshot_id=state_snapshot_logical_id(PROJECT_ID, SCOPE_KEY),
        version_id=VersionId(version),
        scope_key=SCOPE_KEY,
        story_time=story_time,
        facts=(
            _fact(value),
            StateFact(
                namespace=StateFactNamespace.ENVIRONMENT,
                key="weather",
                value_json='{"condition":"clear"}',
            ),
        ),
        previous_snapshot_ref=previous,
        source_outcome_ref=outcome_ref,
        change_refs=(change_ref,),
        context_state_refs=context_refs,
    )


async def _create_candidate(
    repo: StateSnapshotRepository,
    snapshot: StateSnapshot,
):
    return await repo.create_initial(
        snapshot=snapshot,
        provenance=build_state_snapshot_provenance(
            snapshot,
            actor_ref="studio:imp042-test",
            reason="create candidate canonical state",
            recorded_at=NOW,
        ),
        created_at=NOW,
    )


async def _approve(
    repo: StateSnapshotRepository,
    snapshot: StateSnapshot,
    *,
    expected_revision: int,
    qa_ref: VersionRef = QA_V1,
    outcome_ref: VersionRef = OUTCOME_V1,
    designation_version: str = "approval-v1",
):
    return await repo.approve_end_state(
        snapshot_ref=snapshot.ref,
        designation_version=VersionId(designation_version),
        qa_result_ref=qa_ref,
        approval_policy_ref=POLICY_REF,
        source_outcome_ref=outcome_ref,
        actor_ref="approval:test",
        reason="QA-approved canonical end state",
        recorded_at=NOW,
        expected_snapshot_revision=expected_revision,
        correlation_id="run:imp042-approval",
    )


async def _create_approved_initial(writer: SQLiteWriteOwner):
    await _seed_common(writer)
    repo = StateSnapshotRepository(writer)
    snapshot = _snapshot()
    await _create_candidate(repo, snapshot)
    approved = await _approve(repo, snapshot, expected_revision=0)
    return repo, snapshot, approved


def _ledger(snapshot: StateSnapshot, designation_ref: VersionRef) -> ContinuityLedger:
    return ContinuityLedger(
        project_id=PROJECT_ID,
        continuity_ledger_id=continuity_ledger_logical_id(PROJECT_ID, "sequence:001"),
        version_id=VersionId("ledger-v1"),
        scope_key="sequence:001",
        state_snapshot_refs=(snapshot.ref,),
        approval_designation_refs=(designation_ref,),
        reference_asset_refs=(REFERENCE_REF,),
        approved_artifact_refs=(APPROVED_ARTIFACT_REF,),
        constraints=(
            ContinuityConstraint(
                constraint_key="wardrobe.identity",
                fact_keys=(snapshot.facts[0].fact_key,),
            ),
        ),
    )


def test_state_snapshot_rejects_media_provider_payload_and_canonicalizes_json():
    fact = _fact()
    assert fact.value_json == '{"description":"cream blouse"}'

    with pytest.raises(ValidationError, match="execution/provider/media"):
        StateFact(
            namespace=StateFactNamespace.ENVIRONMENT,
            key="media_id",
            value_json='"11111111-1111-1111-1111-111111111111"',
        )
    with pytest.raises(ValidationError, match="cannot enter StateSnapshot payload"):
        StateFact(
            namespace=StateFactNamespace.ENVIRONMENT,
            key="weather",
            value_json='{"nested":{"image_url":"https://example.invalid/x.png"}}',
        )

    snapshot = _snapshot()
    payload = snapshot.model_dump(mode="json")
    payload["parent_scene_id"] = "legacy-scene"
    with pytest.raises(ValidationError):
        StateSnapshot.model_validate(payload)


def test_legacy_media_chain_is_compatibility_only_and_requires_uuid_media_ids():
    conditioning = LegacyMediaChainConditioning(
        parent_scene_id="legacy-scene-001",
        source_image_media_id="11111111-1111-1111-1111-111111111111",
        end_scene_media_id="22222222-2222-2222-2222-222222222222",
    )
    assert conditioning.parent_scene_id == "legacy-scene-001"
    assert "parent_scene_id" not in StateSnapshot.model_fields
    assert "source_image_media_id" not in StateSnapshot.model_fields

    with pytest.raises(ValidationError, match="UUID media ID"):
        LegacyMediaChainConditioning(source_image_media_id="CAMS-not-a-uuid")


def test_state_delta_is_payload_free_and_hashes_changed_facts():
    old = _snapshot()
    new = _snapshot(
        version="state-v2",
        previous=old.ref,
        story_time="T+00:08",
        value="dark raincoat",
        change_ref=CHANGE_V2,
        outcome_ref=OUTCOME_V2,
    )
    delta = derive_state_delta(old, new)
    assert len(delta.changes) == 1
    wardrobe_key = next(fact.fact_key for fact in old.facts if fact.namespace is StateFactNamespace.WARDROBE)
    assert delta.changes[0].fact_key == wardrobe_key
    encoded = delta.model_dump_json()
    assert "cream blouse" not in encoded
    assert "dark raincoat" not in encoded
    assert "sha256:" in encoded


def test_story_owned_state_is_reference_only_and_wrong_prefix_is_rejected():
    refs = (
        VersionRef(logical_id=LogicalId("character-model:entity:legacy-char-001"), version_id=VersionId("v1")),
        VersionRef(logical_id=LogicalId("relationship:pair-001"), version_id=VersionId("v1")),
        VersionRef(logical_id=LogicalId("character-knowledge:entity:legacy-char-001"), version_id=VersionId("v1")),
    )
    snapshot = _snapshot(context_refs=refs)
    assert snapshot.context_state_refs == tuple(sorted(refs, key=lambda ref: (ref.logical_id.root, ref.version_id.root)))

    with pytest.raises(ValidationError, match="Story-owned"):
        _snapshot(
            context_refs=(
                VersionRef(logical_id=LogicalId("state-snapshot:shadow"), version_id=VersionId("v1")),
            )
        )


@pytest.mark.asyncio
async def test_candidate_state_remains_draft_and_cannot_propagate_without_qa_approval(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_common(writer)
        repo = StateSnapshotRepository(writer)
        snapshot = _snapshot()
        artifact = await _create_candidate(repo, snapshot)
        pointer = await repo.get_current_pointer(snapshot.state_snapshot_id)
        assert artifact.ref == snapshot.ref
        assert pointer is not None and pointer.status is LifecycleState.DRAFT
        with pytest.raises(StatePropagationBlocked, match="APPROVED/LOCKED"):
            await repo.assert_propagatable(snapshot.ref)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_approval_designation_makes_exact_snapshot_propagatable_without_copying_state_payload(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, snapshot, approval = await _create_approved_initial(writer)
        assert approval.snapshot_pointer.status is LifecycleState.APPROVED
        assert approval.designation.value.state_snapshot_ref == snapshot.ref
        assert "facts" not in approval.designation.value.model_dump(mode="json")
        resolved = await repo.assert_propagatable(snapshot.ref)
        assert resolved.ref == approval.designation.ref
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_qa_evidence_blocks_state_approval(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_common(writer)
        repo = StateSnapshotRepository(writer)
        snapshot = _snapshot()
        await _create_candidate(repo, snapshot)
        await versions.update_current(
            logical_id=QA_V1.logical_id,
            version_id=QA_V1.version_id,
            status=LifecycleState.SUPERSEDED,
            expected_revision=0,
        )
        with pytest.raises(StateContinuityError, match="QA result is not exact current"):
            await _approve(repo, snapshot, expected_revision=0)
        pointer = await repo.get_current_pointer(snapshot.state_snapshot_id)
        assert pointer is not None and pointer.status is LifecycleState.DRAFT
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_snapshot_provenance_must_exactly_bind_sources(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_common(writer)
        repo = StateSnapshotRepository(writer)
        snapshot = _snapshot()
        wrong = Provenance(
            source_refs=("evidence:wrong",),
            actor_ref="studio:test",
            reason="missing exact snapshot bindings",
            recorded_at=NOW,
        )
        with pytest.raises(StateContinuityError, match="exactly bind"):
            await repo.create_initial(snapshot=snapshot, provenance=wrong, created_at=NOW)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_subject_entity_must_be_real_current_entity_in_same_project(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = VersionRepository(writer)
        wrong_entity = EntityVersion(
            entity_id=ENTITY_REF.logical_id,
            version_id=ENTITY_REF.version_id,
            kind=EntityKind.CHARACTER,
            name="Lan",
            project_ids=(OTHER_PROJECT_ID,),
        )
        await _seed_version(versions, ENTITY_REF, wrong_entity.model_dump(mode="json"))
        for ref in (CHANGE_V1, OUTCOME_V1):
            await _seed_version(versions, ref, {"fixture": ref.logical_id.root})
        repo = StateSnapshotRepository(writer)
        snapshot = _snapshot()
        with pytest.raises(StateContinuityError, match="does not belong to project"):
            await _create_candidate(repo, snapshot)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_successor_requires_exact_current_accepted_predecessor_and_real_change(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, old, _ = await _create_approved_initial(writer)
        no_op = _snapshot(
            version="state-v2",
            previous=old.ref,
        )
        with pytest.raises(StateContinuityError, match="requires semantic change"):
            await repo.create_successor(
                snapshot=no_op,
                predecessor=old.ref,
                provenance=build_state_snapshot_provenance(
                    no_op,
                    actor_ref="studio:test",
                    reason="no-op state successor",
                    recorded_at=NOW,
                ),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_continuity_ledger_consumes_only_approved_state_and_keeps_refs_only(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, snapshot, approval = await _create_approved_initial(writer)
        ledger_repo = ContinuityLedgerRepository(writer)
        ledger = _ledger(snapshot, approval.designation.ref)
        artifact = await ledger_repo.create_initial(
            ledger=ledger,
            provenance=build_continuity_ledger_provenance(
                ledger,
                actor_ref="continuity:test",
                reason="materialize continuity constraints",
                recorded_at=NOW,
            ),
            created_at=NOW,
        )
        payload = artifact.value.model_dump(mode="json")
        assert "facts" not in payload
        assert "state_payload" not in payload
        pointer = await VersionRepository(writer).get_current(ledger.continuity_ledger_id)
        assert pointer is not None and pointer.status is LifecycleState.DRAFT
        promoted = await ledger_repo.promote_current(
            ref=artifact.ref,
            expected_revision=pointer.revision,
        )
        assert promoted.status is LifecycleState.APPROVED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_continuity_consumer_requires_exact_ledger_and_state_provenance(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_common(writer)
        state_repo = StateSnapshotRepository(writer)
        snapshot = _snapshot()
        await _create_candidate(state_repo, snapshot)
        approval = await _approve(state_repo, snapshot, expected_revision=0)

        ledger_repo = ContinuityLedgerRepository(writer)
        ledger = _ledger(snapshot, approval.designation.ref)
        artifact = await ledger_repo.create_initial(
            ledger=ledger,
            provenance=build_continuity_ledger_provenance(
                ledger,
                actor_ref="continuity:test",
                reason="create ledger",
                recorded_at=NOW,
            ),
            created_at=NOW,
        )
        await ledger_repo.promote_current(ref=artifact.ref, expected_revision=0)
        consumer = VersionRef(
            logical_id=LogicalId("full-shot-spec:project:film:shot-002"),
            version_id=VersionId("spec-v1"),
        )
        await _seed_version(versions, consumer, {"fixture": "consumer"})

        with pytest.raises(StatePropagationBlocked, match="exactly bind"):
            await ledger_repo.bind_consumer(
                ledger_ref=artifact.ref,
                consumer_ref=consumer,
                provenance=_seed_provenance("wrong consumer binding"),
                created_at=NOW,
            )

        exact = build_continuity_binding_provenance(
            ledger_ref=artifact.ref,
            state_snapshot_refs=ledger.state_snapshot_refs,
            actor_ref="continuity:test",
            reason="bind continuity authority",
            recorded_at=NOW,
        )
        await ledger_repo.bind_consumer(
            ledger_ref=artifact.ref,
            consumer_ref=consumer,
            provenance=exact,
            created_at=NOW,
        )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_approved_state_successor_selectively_invalidates_bound_descendants_not_replacement(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_common(writer)
        state_repo = StateSnapshotRepository(writer)
        old = _snapshot()
        await _create_candidate(state_repo, old)
        old_approval = await _approve(state_repo, old, expected_revision=0)

        ledger_repo = ContinuityLedgerRepository(writer)
        ledger = _ledger(old, old_approval.designation.ref)
        ledger_artifact = await ledger_repo.create_initial(
            ledger=ledger,
            provenance=build_continuity_ledger_provenance(
                ledger,
                actor_ref="continuity:test",
                reason="bind old state continuity",
                recorded_at=NOW,
            ),
            created_at=NOW,
        )
        await ledger_repo.promote_current(ref=ledger_artifact.ref, expected_revision=0)

        consumer = VersionRef(
            logical_id=LogicalId("full-shot-spec:project:film:shot-002"),
            version_id=VersionId("spec-v1"),
        )
        unrelated = VersionRef(
            logical_id=LogicalId("full-shot-spec:project:film:unrelated"),
            version_id=VersionId("spec-v1"),
        )
        await _seed_version(versions, consumer, {"fixture": "bound consumer"})
        await _seed_version(versions, unrelated, {"fixture": "unrelated"})
        binding_provenance = build_continuity_binding_provenance(
            ledger_ref=ledger_artifact.ref,
            state_snapshot_refs=ledger.state_snapshot_refs,
            actor_ref="continuity:test",
            reason="bind old state to consumer",
            recorded_at=NOW,
        )
        await ledger_repo.bind_consumer(
            ledger_ref=ledger_artifact.ref,
            consumer_ref=consumer,
            provenance=binding_provenance,
            created_at=NOW,
        )

        new = _snapshot(
            version="state-v2",
            previous=old.ref,
            story_time="T+00:08",
            value="dark raincoat",
            change_ref=CHANGE_V2,
            outcome_ref=OUTCOME_V2,
        )
        await state_repo.create_successor(
            snapshot=new,
            predecessor=old.ref,
            provenance=build_state_snapshot_provenance(
                new,
                actor_ref="studio:test",
                reason="accepted canonical state change",
                recorded_at=NOW,
            ),
            created_at=NOW,
        )
        pointer = await state_repo.get_current_pointer(old.state_snapshot_id)
        assert pointer is not None and pointer.version_id == old.version_id
        result = await _approve(
            state_repo,
            new,
            expected_revision=pointer.revision,
            qa_ref=QA_V2,
            outcome_ref=OUTCOME_V2,
            designation_version="approval-v2",
        )

        affected = {
            (record.affected_object_id.root, record.affected_object_version.root)
            for record in result.invalidations
        }
        assert (ledger_artifact.ref.logical_id.root, ledger_artifact.ref.version_id.root) in affected
        assert (consumer.logical_id.root, consumer.version_id.root) in affected
        assert (unrelated.logical_id.root, unrelated.version_id.root) not in affected
        assert (new.ref.logical_id.root, new.ref.version_id.root) not in affected

        unresolved = await InvalidationRepository(writer).list_unresolved()
        assert any(record.affected_object_id == consumer.logical_id for record in unresolved)
        assert not any(
            record.affected_object_id == new.ref.logical_id
            and record.affected_object_version == new.ref.version_id
            for record in unresolved
        )
        assert (await state_repo.assert_propagatable(new.ref)).value.state_snapshot_ref == new.ref
        with pytest.raises(StatePropagationBlocked):
            await state_repo.assert_propagatable(old.ref)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_continuity_ledger_rejects_unknown_state_fact_reference(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, snapshot, approval = await _create_approved_initial(writer)
        ledger_repo = ContinuityLedgerRepository(writer)
        ledger = _ledger(snapshot, approval.designation.ref).model_copy(
            update={
                "constraints": (
                    ContinuityConstraint(
                        constraint_key="missing.fact",
                        fact_keys=("wardrobe:entity:legacy-char-001:not_real",),
                    ),
                )
            }
        )
        with pytest.raises(StatePropagationBlocked, match="unknown StateFact"):
            await ledger_repo.create_initial(
                ledger=ledger,
                provenance=build_continuity_ledger_provenance(
                    ledger,
                    actor_ref="continuity:test",
                    reason="invalid fact reference",
                    recorded_at=NOW,
                ),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_continuity_successor_cannot_bypass_selective_invalidation(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_common(writer)
        state_repo = StateSnapshotRepository(writer)
        snapshot = _snapshot()
        await _create_candidate(state_repo, snapshot)
        approval = await _approve(state_repo, snapshot, expected_revision=0)

        ledger_repo = ContinuityLedgerRepository(writer)
        first = _ledger(snapshot, approval.designation.ref)
        first_artifact = await ledger_repo.create_initial(
            ledger=first,
            provenance=build_continuity_ledger_provenance(
                first,
                actor_ref="continuity:test",
                reason="initial continuity ledger",
                recorded_at=NOW,
            ),
            created_at=NOW,
        )
        await ledger_repo.promote_current(ref=first_artifact.ref, expected_revision=0)

        consumer = VersionRef(
            logical_id=LogicalId("full-shot-spec:project:film:ledger-consumer"),
            version_id=VersionId("spec-v1"),
        )
        await _seed_version(versions, consumer, {"fixture": "ledger consumer"})
        await ledger_repo.bind_consumer(
            ledger_ref=first_artifact.ref,
            consumer_ref=consumer,
            provenance=build_continuity_binding_provenance(
                ledger_ref=first_artifact.ref,
                state_snapshot_refs=first.state_snapshot_refs,
                actor_ref="continuity:test",
                reason="bind initial ledger consumer",
                recorded_at=NOW,
            ),
            created_at=NOW,
        )

        second = first.model_copy(
            update={
                "version_id": VersionId("ledger-v2"),
                "constraints": (
                    ContinuityConstraint(
                        constraint_key="environment.weather",
                        fact_keys=(next(f.fact_key for f in snapshot.facts if f.namespace is StateFactNamespace.ENVIRONMENT),),
                    ),
                ),
            }
        )
        second_artifact = await ledger_repo.create_successor(
            ledger=second,
            predecessor=first_artifact.ref,
            provenance=build_continuity_ledger_provenance(
                second,
                actor_ref="continuity:test",
                reason="revise continuity constraints",
                recorded_at=NOW,
            ),
            created_at=NOW,
        )
        with pytest.raises(StateContinuityError, match="promote_successor_current"):
            await ledger_repo.promote_current(
                ref=second_artifact.ref,
                expected_revision=1,
            )

        from agent.studio import build_continuity_change_provenance

        pointer, invalidations = await ledger_repo.promote_successor_current(
            ref=second_artifact.ref,
            expected_revision=1,
            invalidation_provenance=build_continuity_change_provenance(
                previous_ref=first_artifact.ref,
                successor_ref=second_artifact.ref,
                actor_ref="continuity:test",
                reason="activate revised continuity ledger",
                recorded_at=NOW,
            ),
            repair_or_recompute_requirement="recompute continuity-dependent consumer",
        )
        assert pointer.version_id == VersionId("ledger-v2")
        assert any(record.affected_object_id == consumer.logical_id for record in invalidations)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_revoking_approved_end_state_invalidates_bound_continuity_and_blocks_propagation(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, snapshot, approval = await _create_approved_initial(writer)
        ledger_repo = ContinuityLedgerRepository(writer)
        ledger = _ledger(snapshot, approval.designation.ref)
        ledger_artifact = await ledger_repo.create_initial(
            ledger=ledger,
            provenance=build_continuity_ledger_provenance(
                ledger,
                actor_ref="continuity:test",
                reason="ledger before approval revocation",
                recorded_at=NOW,
            ),
            created_at=NOW,
        )
        await ledger_repo.promote_current(ref=ledger_artifact.ref, expected_revision=0)

        state_repo = StateSnapshotRepository(writer)
        designation_pointer = await VersionRepository(writer).get_current(
            approval.designation.value.approval_record_id
        )
        assert designation_pointer is not None
        revoked = await state_repo.revoke_end_state(
            state_snapshot_ref=snapshot.ref,
            revocation_version=VersionId("approval-revoked-v2"),
            expected_designation_revision=designation_pointer.revision,
            actor_ref="approval:test",
            reason="QA approval revoked",
            recorded_at=NOW,
        )
        assert any(
            record.affected_object_id == ledger_artifact.ref.logical_id
            and record.affected_object_version == ledger_artifact.ref.version_id
            for record in revoked.invalidations
        )
        with pytest.raises(StatePropagationBlocked, match="lacks current approved"):
            await state_repo.assert_propagatable(snapshot.ref)
    finally:
        await writer.close()
