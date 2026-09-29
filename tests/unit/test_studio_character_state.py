"""IMP-022 tests for character psychology, relationship and knowledge state."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    AudienceEpistemicState,
    CanonicalEntityRepository,
    CharacterEpistemicState,
    CharacterKnowledgeState,
    CharacterModelVersion,
    CharacterStateGateBlocked,
    CharacterStateIdentityError,
    CharacterStateRepository,
    EntityKind,
    InvalidationRepository,
    KnowledgeItem,
    LegacyEntitySnapshot,
    LifecycleState,
    LogicalId,
    ObjectiveTruth,
    Provenance,
    RelationshipState,
    SQLiteWriteOwner,
    SemanticRecordMetadata,
    VersionId,
    VersionRef,
    VersionRepository,
    build_character_state_provenance,
    entity_logical_id,
)


NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
PROJECT_ID = LogicalId("project:film")
PROFILE_REF = VersionRef(
    logical_id=LogicalId("active-profile:project:film"),
    version_id=VersionId("p1"),
)
PREMISE_REF = VersionRef(
    logical_id=LogicalId("story-premise:project:film"),
    version_id=VersionId("premise-v1"),
)
MATERIAL_REF = VersionRef(
    logical_id=LogicalId("story-material:project:film:inheritance-pressure"),
    version_id=VersionId("material-v1"),
)
STORY_CORE_REF = VersionRef(
    logical_id=LogicalId("story-core:project:film"),
    version_id=VersionId("core-v1"),
)
EVENT_REF = VersionRef(
    logical_id=LogicalId("story-event:project:film:reveal-001"),
    version_id=VersionId("event-v1"),
)


def _seed_provenance(reason: str) -> Provenance:
    return Provenance(
        source_refs=("evidence:imp022-seed",),
        actor_ref="studio:test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp022",
    )


def _metadata(ref: VersionRef, *, predecessor: VersionRef | None = None) -> SemanticRecordMetadata:
    return SemanticRecordMetadata(
        logical_id=ref.logical_id,
        version_id=ref.version_id,
        predecessor=predecessor,
        provenance=_seed_provenance("seed canonical source"),
        created_at=NOW,
    )


async def _seed_generic(
    versions: VersionRepository,
    ref: VersionRef,
    *,
    status: LifecycleState,
    payload: dict | None = None,
) -> None:
    await versions.create_initial(
        metadata=_metadata(ref),
        payload=payload or {"seed": ref.logical_id.root},
        status=status,
    )


async def _seed_entity(
    writer: SQLiteWriteOwner,
    legacy_id: str,
    name: str,
) -> VersionRef:
    repo = CanonicalEntityRepository(writer)
    result = await repo.create_initial_from_legacy(
        snapshot=LegacyEntitySnapshot(
            id=legacy_id,
            name=name,
            entity_type=EntityKind.CHARACTER,
            project_ids=(PROJECT_ID,),
            description=f"{name} visual compatibility description",
            image_prompt=f"{name} visual prompt",
            media_id=f"legacy-media-{legacy_id}",
        ),
        version_id=VersionId("entity-v1"),
        actor_ref="studio:test",
        reason="seed canonical entity",
        recorded_at=NOW,
        correlation_id="run:imp022",
    )
    await repo.promote_current(
        ref=result.artifact.ref,
        expected_revision=0,
        status=LifecycleState.APPROVED,
    )
    return result.artifact.ref


async def _seed_context(writer: SQLiteWriteOwner):
    versions = VersionRepository(writer)
    alice = await _seed_entity(writer, "alice", "Alice")
    bob = await _seed_entity(writer, "bob", "Bob")
    await _seed_generic(
        versions,
        PROFILE_REF,
        status=LifecycleState.LOCKED,
        payload={"profile": "family-drama"},
    )
    await _seed_generic(
        versions,
        PREMISE_REF,
        status=LifecycleState.APPROVED,
        payload={"premise": "A daughter returns to sell the family home."},
    )
    await _seed_generic(
        versions,
        MATERIAL_REF,
        status=LifecycleState.APPROVED,
        payload={"material": "Inheritance paperwork creates time pressure."},
    )
    await _seed_generic(
        versions,
        EVENT_REF,
        status=LifecycleState.APPROVED,
        payload={"event": "A cassette reveals a hidden family decision."},
    )
    return versions, alice, bob


def _psychology(
    character_ref: VersionRef,
    *,
    version: str = "psych-v1",
    story_core_ref: VersionRef | None = None,
) -> CharacterModelVersion:
    return CharacterModelVersion(
        project_id=PROJECT_ID,
        character_ref=character_ref,
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        story_core_ref=story_core_ref,
        story_context_refs=(PREMISE_REF,),
        story_material_refs=(MATERIAL_REF,),
        role="protagonist",
        external_want="Sell the inherited family house and return to city life.",
        internal_need="Face why she has avoided grieving her mother.",
        fear="Being pulled back into obligations she escaped.",
        formative_pressure="She learned to solve family problems by leaving.",
        mistaken_belief="Distance is the only way to remain independent.",
        values=("independence", "truth"),
        contradictions=("wants closure but avoids evidence of the past",),
        strengths=("decisive",),
        flaws_or_defenses=("emotional avoidance",),
        secrets=("she ignored her mother's last call",),
        social_mask="practical and composed",
        private_self="guilty and uncertain",
        preferred_tactics=("control the schedule", "change the subject"),
        boundaries=("will not discuss the final hospital week",),
        decision_style="acts quickly under practical pressure, delays emotional choices",
        arc_hypothesis="control -> confrontation -> chosen responsibility",
    )


def _relationship(
    a: VersionRef,
    b: VersionRef,
    *,
    version: str = "rel-v1",
    ordinal: int = 0,
    previous: VersionRef | None = None,
    causes: tuple[VersionRef, ...] = (EVENT_REF,),
    trust: float = 0.2,
    delta_summary: str | None = None,
) -> RelationshipState:
    return RelationshipState(
        project_id=PROJECT_ID,
        participant_refs=(b, a),
        version_id=VersionId(version),
        sequence_ordinal=ordinal,
        story_time=f"T{ordinal}",
        previous_state_ref=previous,
        change_cause_refs=causes,
        public_relation="siblings cooperating on the sale",
        private_relation="resentful but mutually protective",
        trust=trust,
        power_balance="older sibling controls paperwork; younger sibling controls family access",
        debts=("unfinished caregiving resentment",),
        resentments=("one sibling left town",),
        dependencies=("must agree before sale",),
        secrets_between_them=("mother recorded separate messages",),
        current_pressure="sale deadline",
        delta_summary=delta_summary,
    )


def _knowledge(
    character_ref: VersionRef,
    *,
    version: str,
    ordinal: int,
    previous: VersionRef | None,
    change_events: tuple[VersionRef, ...],
    items: tuple[KnowledgeItem, ...],
) -> CharacterKnowledgeState:
    return CharacterKnowledgeState(
        project_id=PROJECT_ID,
        character_ref=character_ref,
        version_id=VersionId(version),
        sequence_ordinal=ordinal,
        story_time=f"T{ordinal}",
        previous_state_ref=previous,
        change_event_refs=change_events,
        items=items,
    )


def _provenance(value, reason: str) -> Provenance:
    return build_character_state_provenance(
        value,
        actor_ref="studio:character-state",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp022",),
        correlation_id="run:imp022",
    )


@pytest.mark.asyncio
async def test_precore_character_model_stays_draft_until_storycore_binding(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions, alice, _ = await _seed_context(writer)
        repo = CharacterStateRepository(writer)

        v1 = _psychology(alice)
        a1 = await repo.create_initial(
            value=v1,
            provenance=_provenance(v1, "pre-core psychology"),
            created_at=NOW,
        )
        with pytest.raises(CharacterStateGateBlocked, match="remains DRAFT"):
            await repo.promote(ref=a1.ref, expected_revision=0)

        await _seed_generic(
            versions,
            STORY_CORE_REF,
            status=LifecycleState.DRAFT,
            payload={"story_core": "draft"},
        )
        v2 = _psychology(
            alice,
            version="psych-v2",
            story_core_ref=STORY_CORE_REF,
        )
        a2 = await repo.create_successor(
            value=v2,
            predecessor=a1.ref,
            provenance=_provenance(v2, "bind exact StoryCore draft"),
            created_at=NOW,
        )
        pointer = await repo.promote(ref=a2.ref, expected_revision=0)

        assert pointer.status is LifecycleState.APPROVED
        assert pointer.version_id == VersionId("psych-v2")
        assert (await repo.get(a1.ref)).value.story_core_ref is None
        assert (await repo.get(a2.ref)).value.story_core_ref == STORY_CORE_REF
    finally:
        await writer.close()


def test_character_model_is_dramatic_not_visual_or_provider_truth():
    forbidden = {
        "media_id",
        "reference_image_url",
        "image_prompt",
        "provider_id",
        "provider_name",
        "model_id",
        "model_key",
        "remote_job_id",
    }
    assert set(CharacterModelVersion.model_fields).isdisjoint(forbidden)
    assert set(RelationshipState.model_fields).isdisjoint(forbidden)
    assert set(CharacterKnowledgeState.model_fields).isdisjoint(forbidden)


@pytest.mark.asyncio
async def test_relationship_state_has_stable_identity_and_strict_causal_chronology(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, alice, bob = await _seed_context(writer)
        repo = CharacterStateRepository(writer)

        v1 = _relationship(alice, bob)
        assert tuple(ref.logical_id.root for ref in v1.participant_refs) == tuple(
            sorted((alice.logical_id.root, bob.logical_id.root))
        )
        a1 = await repo.create_initial(
            value=v1,
            provenance=_provenance(v1, "relationship baseline"),
            created_at=NOW,
        )
        await repo.promote(ref=a1.ref, expected_revision=0)

        v2 = _relationship(
            alice,
            bob,
            version="rel-v2",
            ordinal=1,
            previous=a1.ref,
            causes=(EVENT_REF,),
            trust=0.5,
            delta_summary="The cassette reveal makes avoidance harder but increases honesty.",
        )
        a2 = await repo.create_successor(
            value=v2,
            predecessor=a1.ref,
            provenance=_provenance(v2, "relationship changed by reveal"),
            created_at=NOW,
        )
        pointer = await repo.promote(ref=a2.ref, expected_revision=1)

        assert pointer.version_id == VersionId("rel-v2")
        assert a1.value.logical_id == a2.value.logical_id
        assert (await repo.get(a1.ref)).value.trust == 0.2
        assert (await repo.get(a2.ref)).value.trust == 0.5
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_relationship_successor_rejects_skipped_chronology(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, alice, bob = await _seed_context(writer)
        repo = CharacterStateRepository(writer)
        v1 = _relationship(alice, bob)
        a1 = await repo.create_initial(
            value=v1,
            provenance=_provenance(v1, "baseline"),
            created_at=NOW,
        )

        bad = _relationship(
            alice,
            bob,
            version="rel-v3",
            ordinal=2,
            previous=a1.ref,
            causes=(EVENT_REF,),
            delta_summary="illegal skipped state",
        )
        with pytest.raises(CharacterStateIdentityError, match="advance by exactly one"):
            await repo.create_successor(
                value=bad,
                predecessor=a1.ref,
                provenance=_provenance(bad, "invalid chronology"),
                created_at=NOW,
            )
    finally:
        await writer.close()


def test_impossible_knowledge_and_false_knowledge_fail_closed():
    with pytest.raises(ValidationError, match="without acquisition evidence"):
        KnowledgeItem(
            claim_key="cassette-location",
            content="The cassette is under the floorboard.",
            objective_truth=ObjectiveTruth.TRUE,
            character_state=CharacterEpistemicState.KNOWS,
            objective_evidence_refs=(EVENT_REF,),
        )

    with pytest.raises(ValidationError, match="objective_truth=TRUE"):
        KnowledgeItem(
            claim_key="wrong-fact",
            content="The buyer already owns the house.",
            objective_truth=ObjectiveTruth.FALSE,
            character_state=CharacterEpistemicState.KNOWS,
            objective_evidence_refs=(EVENT_REF,),
            source_event_refs=(EVENT_REF,),
        )

    belief = KnowledgeItem(
        claim_key="mother-intent",
        content="Mother intended the cassette as an apology.",
        objective_truth=ObjectiveTruth.UNKNOWN,
        character_state=CharacterEpistemicState.BELIEVES,
        inference_basis_refs=(EVENT_REF,),
        audience_state=AudienceEpistemicState.SUSPECTS,
    )
    assert belief.character_state is CharacterEpistemicState.BELIEVES


@pytest.mark.asyncio
async def test_knowledge_state_transition_preserves_objective_vs_belief_truth(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, alice, _ = await _seed_context(writer)
        repo = CharacterStateRepository(writer)

        initial_item = KnowledgeItem(
            claim_key="cassette-location",
            content="The cassette location is not known yet.",
            objective_truth=ObjectiveTruth.TRUE,
            character_state=CharacterEpistemicState.UNKNOWN,
            objective_evidence_refs=(EVENT_REF,),
            audience_state=AudienceEpistemicState.KNOWS,
        )
        v1 = _knowledge(
            alice,
            version="know-v1",
            ordinal=0,
            previous=None,
            change_events=(),
            items=(initial_item,),
        )
        a1 = await repo.create_initial(
            value=v1,
            provenance=_provenance(v1, "initial knowledge"),
            created_at=NOW,
        )
        await repo.promote(ref=a1.ref, expected_revision=0)

        revealed = KnowledgeItem(
            claim_key="cassette-location",
            content="The cassette is hidden beneath the old radio cabinet.",
            objective_truth=ObjectiveTruth.TRUE,
            character_state=CharacterEpistemicState.KNOWS,
            objective_evidence_refs=(EVENT_REF,),
            source_event_refs=(EVENT_REF,),
            audience_state=AudienceEpistemicState.KNOWS,
        )
        v2 = _knowledge(
            alice,
            version="know-v2",
            ordinal=1,
            previous=a1.ref,
            change_events=(EVENT_REF,),
            items=(revealed,),
        )
        a2 = await repo.create_successor(
            value=v2,
            predecessor=a1.ref,
            provenance=_provenance(v2, "cassette reveal"),
            created_at=NOW,
        )
        pointer = await repo.promote(ref=a2.ref, expected_revision=1)

        assert pointer.version_id == VersionId("know-v2")
        assert (await repo.get(a1.ref)).value.items[0].character_state is CharacterEpistemicState.UNKNOWN
        assert (await repo.get(a2.ref)).value.items[0].character_state is CharacterEpistemicState.KNOWS
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_objective_evidence_blocks_knowledge_promotion(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions, alice, _ = await _seed_context(writer)
        repo = CharacterStateRepository(writer)

        item = KnowledgeItem(
            claim_key="cassette-location",
            content="The cassette exists under the old radio cabinet.",
            objective_truth=ObjectiveTruth.TRUE,
            character_state=CharacterEpistemicState.UNKNOWN,
            objective_evidence_refs=(EVENT_REF,),
            audience_state=AudienceEpistemicState.KNOWS,
        )
        state = _knowledge(
            alice,
            version="know-v1",
            ordinal=0,
            previous=None,
            change_events=(),
            items=(item,),
        )
        artifact = await repo.create_initial(
            value=state,
            provenance=_provenance(state, "knowledge based on event v1"),
            created_at=NOW,
        )

        event_v2 = VersionRef(
            logical_id=EVENT_REF.logical_id,
            version_id=VersionId("event-v2"),
        )
        await versions.create_successor(
            metadata=_metadata(event_v2, predecessor=EVENT_REF),
            payload={"event": "revised reveal evidence"},
            supersession_reason="event evidence revised",
        )
        await versions.update_current(
            logical_id=event_v2.logical_id,
            version_id=event_v2.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )

        with pytest.raises(CharacterStateGateBlocked, match="knowledge evidence"):
            await repo.promote(ref=artifact.ref, expected_revision=0)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_entity_version_blocks_relationship_promotion(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, alice, bob = await _seed_context(writer)
        state_repo = CharacterStateRepository(writer)
        entity_repo = CanonicalEntityRepository(writer)

        relationship = _relationship(alice, bob)
        artifact = await state_repo.create_initial(
            value=relationship,
            provenance=_provenance(relationship, "baseline relationship"),
            created_at=NOW,
        )

        successor = await entity_repo.create_successor_from_legacy(
            snapshot=LegacyEntitySnapshot(
                id="alice",
                name="Alice Updated",
                entity_type=EntityKind.CHARACTER,
                project_ids=(PROJECT_ID,),
                description="Updated semantic character compatibility description",
            ),
            version_id=VersionId("entity-v2"),
            predecessor=alice,
            actor_ref="studio:test",
            reason="entity semantic update",
            recorded_at=NOW,
            correlation_id="run:imp022",
        )
        await entity_repo.promote_current(
            ref=successor.artifact.ref,
            expected_revision=1,
            status=LifecycleState.APPROVED,
        )

        with pytest.raises(CharacterStateGateBlocked, match="EntityVersion"):
            await state_repo.promote(ref=artifact.ref, expected_revision=0)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_entity_version_change_materializes_relationship_invalidation(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, alice, bob = await _seed_context(writer)
        state_repo = CharacterStateRepository(writer)
        entity_repo = CanonicalEntityRepository(writer)

        relationship = _relationship(alice, bob)
        artifact = await state_repo.create_initial(
            value=relationship,
            provenance=_provenance(relationship, "baseline relationship"),
            created_at=NOW,
        )
        await state_repo.promote(ref=artifact.ref, expected_revision=0)

        successor = await entity_repo.create_successor_from_legacy(
            snapshot=LegacyEntitySnapshot(
                id="alice",
                name="Alice Updated",
                entity_type=EntityKind.CHARACTER,
                project_ids=(PROJECT_ID,),
                description="Updated canonical entity semantics",
            ),
            version_id=VersionId("entity-v2"),
            predecessor=alice,
            actor_ref="studio:test",
            reason="entity semantic update",
            recorded_at=NOW,
            correlation_id="run:imp022",
        )
        await entity_repo.promote_current(
            ref=successor.artifact.ref,
            expected_revision=1,
            status=LifecycleState.APPROVED,
        )

        invalidations = await InvalidationRepository(writer).create_for_change(
            cause="entity semantic version changed",
            source_old=alice,
            source_new=successor.artifact.ref,
            provenance=_seed_provenance("invalidate character dependents"),
            scope="relationship descendants",
            repair_or_recompute_requirement="re-evaluate relationship against new entity version",
        )

        affected = {
            (item.affected_object_id.root, item.affected_object_version.root)
            for item in invalidations
        }
        assert (artifact.ref.logical_id.root, artifact.ref.version_id.root) in affected
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_character_psychology_rejects_non_character_entity_kind(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = VersionRepository(writer)
        entity_repo = CanonicalEntityRepository(writer)
        location = await entity_repo.create_initial_from_legacy(
            snapshot=LegacyEntitySnapshot(
                id="family-house",
                name="Family House",
                entity_type=EntityKind.LOCATION,
                project_ids=(PROJECT_ID,),
                description="Canonical location entity, not a dramatic character.",
            ),
            version_id=VersionId("entity-v1"),
            actor_ref="studio:test",
            reason="seed non-character entity",
            recorded_at=NOW,
            correlation_id="run:imp022",
        )
        await entity_repo.promote_current(
            ref=location.artifact.ref,
            expected_revision=0,
            status=LifecycleState.APPROVED,
        )
        await _seed_generic(
            versions,
            PROFILE_REF,
            status=LifecycleState.LOCKED,
            payload={"profile": "family-drama"},
        )
        await _seed_generic(
            versions,
            PREMISE_REF,
            status=LifecycleState.APPROVED,
        )
        await _seed_generic(
            versions,
            MATERIAL_REF,
            status=LifecycleState.APPROVED,
        )
        await _seed_generic(
            versions,
            STORY_CORE_REF,
            status=LifecycleState.DRAFT,
        )

        model = _psychology(
            location.artifact.ref,
            story_core_ref=STORY_CORE_REF,
        )
        repo = CharacterStateRepository(writer)
        artifact = await repo.create_initial(
            value=model,
            provenance=_provenance(model, "reject non-character entity"),
            created_at=NOW,
        )

        with pytest.raises(
            CharacterStateGateBlocked,
            match="EntityKind.CHARACTER",
        ):
            await repo.promote(ref=artifact.ref, expected_revision=0)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_missing_exact_source_rejected_before_semantic_persistence(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, alice, bob = await _seed_context(writer)
        missing_event = VersionRef(
            logical_id=LogicalId("story-event:project:film:missing"),
            version_id=VersionId("event-v1"),
        )
        relationship = _relationship(
            alice,
            bob,
            causes=(missing_event,),
        )
        repo = CharacterStateRepository(writer)

        with pytest.raises(CharacterStateGateBlocked, match="missing exact source"):
            await repo.create_initial(
                value=relationship,
                provenance=_provenance(
                    relationship,
                    "missing source must fail before persistence",
                ),
                created_at=NOW,
            )

        assert await repo.get(relationship.ref) is None
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_character_state_rejects_entity_from_other_project(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = VersionRepository(writer)
        other_project = LogicalId("project:other")
        entity_repo = CanonicalEntityRepository(writer)
        imported = await entity_repo.create_initial_from_legacy(
            snapshot=LegacyEntitySnapshot(
                id="outsider",
                name="Outsider",
                entity_type=EntityKind.CHARACTER,
                project_ids=(other_project,),
            ),
            version_id=VersionId("entity-v1"),
            actor_ref="studio:test",
            reason="seed outsider",
            recorded_at=NOW,
        )
        await entity_repo.promote_current(
            ref=imported.artifact.ref,
            expected_revision=0,
            status=LifecycleState.APPROVED,
        )
        await _seed_generic(
            versions,
            PROFILE_REF,
            status=LifecycleState.LOCKED,
            payload={"profile": "family-drama"},
        )
        await _seed_generic(
            versions,
            PREMISE_REF,
            status=LifecycleState.APPROVED,
        )
        await _seed_generic(
            versions,
            MATERIAL_REF,
            status=LifecycleState.APPROVED,
        )
        await _seed_generic(
            versions,
            STORY_CORE_REF,
            status=LifecycleState.DRAFT,
        )

        model = _psychology(
            imported.artifact.ref,
            story_core_ref=STORY_CORE_REF,
        )
        repo = CharacterStateRepository(writer)
        artifact = await repo.create_initial(
            value=model,
            provenance=_provenance(model, "wrong project model"),
            created_at=NOW,
        )
        with pytest.raises(CharacterStateGateBlocked, match="does not belong"):
            await repo.promote(ref=artifact.ref, expected_revision=0)
    finally:
        await writer.close()


def test_relationship_identity_is_order_independent():
    alice = VersionRef(
        logical_id=entity_logical_id("alice"),
        version_id=VersionId("entity-v1"),
    )
    bob = VersionRef(
        logical_id=entity_logical_id("bob"),
        version_id=VersionId("entity-v1"),
    )
    left = _relationship(alice, bob)
    right = _relationship(bob, alice)
    assert left.logical_id == right.logical_id
    assert left.participant_refs == right.participant_refs
