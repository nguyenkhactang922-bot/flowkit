"""IMP-041 ReferenceAsset / Reference Resolver tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    EntityKind,
    EntityVersion,
    InvalidationRepository,
    LegacyEntityBinding,
    LegacyReferenceBinding,
    LifecycleState,
    LogicalId,
    Provenance,
    ReferenceAsset,
    ReferenceAssetInvalidationService,
    ReferenceAssetRepository,
    ReferenceCandidate,
    ReferenceCapabilityConstraint,
    ReferenceContractError,
    ReferenceRequirement,
    ReferenceResolveRequest,
    ReferenceResolutionBlocked,
    ReferenceResolver,
    SemanticRecordMetadata,
    SQLiteWriteOwner,
    VersionId,
    VersionRef,
    VersionRepository,
    build_reference_change_provenance,
    build_reference_provenance,
    build_reference_resolution_provenance,
    reference_asset_logical_id,
    sha256_bytes,
)


NOW = datetime(2026, 10, 3, 6, 30, tzinfo=timezone.utc)
PROJECT_ID = LogicalId("project:film")
OTHER_PROJECT_ID = LogicalId("project:other")
ENTITY_V1 = VersionRef(
    logical_id=LogicalId("entity:legacy-char-001"),
    version_id=VersionId("entity-v1"),
)
PROFILE_REF = VersionRef(
    logical_id=LogicalId("active-profile:project:film"),
    version_id=VersionId("profile-v1"),
)
MEDIA_ID_A = "11111111-1111-1111-1111-111111111111"
MEDIA_ID_B = "22222222-2222-2222-2222-222222222222"


def _seed_provenance(reason: str = "IMP-041 test seed") -> Provenance:
    return Provenance(
        source_refs=("evidence:imp041-test",),
        actor_ref="studio:imp041-test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp041-test",
    )


def _metadata(
    ref: VersionRef,
    *,
    predecessor: VersionRef | None = None,
    reason: str = "IMP-041 test seed",
) -> SemanticRecordMetadata:
    return SemanticRecordMetadata(
        logical_id=ref.logical_id,
        version_id=ref.version_id,
        predecessor=predecessor,
        provenance=_seed_provenance(reason),
        created_at=NOW,
    )


async def _seed_version(
    versions: VersionRepository,
    ref: VersionRef,
    payload: dict,
    *,
    status: LifecycleState = LifecycleState.APPROVED,
) -> None:
    await versions.create_initial(
        metadata=_metadata(ref),
        payload=payload,
        status=status,
    )


def _entity(
    ref: VersionRef = ENTITY_V1,
    *,
    project_ids: tuple[LogicalId, ...] = (PROJECT_ID,),
    name: str = "Lan",
) -> EntityVersion:
    return EntityVersion(
        entity_id=ref.logical_id,
        version_id=ref.version_id,
        kind=EntityKind.CHARACTER,
        name=name,
        project_ids=project_ids,
        description="Canonical character identity description.",
    )


async def _seed_entity_and_profile(
    writer: SQLiteWriteOwner,
) -> VersionRepository:
    versions = VersionRepository(writer)
    await _seed_version(
        versions,
        ENTITY_V1,
        _entity().model_dump(mode="json"),
        status=LifecycleState.APPROVED,
    )
    await _seed_version(
        versions,
        PROFILE_REF,
        {"fixture": "approved active profile"},
        status=LifecycleState.APPROVED,
    )
    return versions


def _asset(
    *,
    version: str = "ref-v1",
    slot: str = "primary",
    role: str = "identity.face",
    entity_ref: VersionRef = ENTITY_V1,
    project_id: LogicalId = PROJECT_ID,
    content: bytes = b"reference-one",
) -> ReferenceAsset:
    return ReferenceAsset(
        project_id=project_id,
        reference_asset_id=reference_asset_logical_id(
            project_id,
            entity_ref,
            slot=slot,
        ),
        version_id=VersionId(version),
        entity_ref=entity_ref,
        slot=slot,
        content_hash=sha256_bytes(content),
        role=role,
        mime_type="image/png",
        source_uri="https://example.invalid/reference.png",
        evidence_refs=("evidence:reference-reviewed",),
    )


def _asset_provenance(asset: ReferenceAsset, reason: str = "create reference") -> Provenance:
    return build_reference_provenance(
        asset,
        actor_ref="studio:imp041",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp041",),
        correlation_id="run:imp041",
    )


def _change_provenance(
    old: ReferenceAsset,
    new: ReferenceAsset,
    reason: str = "activate reference successor",
) -> Provenance:
    return build_reference_change_provenance(
        old,
        new,
        actor_ref="studio:imp041",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp041-change",),
        correlation_id="run:imp041-change",
    )


def _legacy_binding(
    asset: ReferenceAsset,
    *,
    media_id: str = MEDIA_ID_A,
) -> LegacyReferenceBinding:
    return LegacyReferenceBinding(
        asset_ref=asset.ref,
        entity_ref=asset.entity_ref,
        legacy_media_id=media_id,
        legacy_reference_image_url="https://example.invalid/legacy-reference.png",
    )


async def _create_approved_asset(
    repo: ReferenceAssetRepository,
    asset: ReferenceAsset,
) -> None:
    await repo.create_initial(
        asset=asset,
        provenance=_asset_provenance(asset),
        created_at=NOW,
    )
    await repo.promote_current(
        ref=asset.ref,
        expected_revision=0,
        status=LifecycleState.APPROVED,
    )


async def _supersede_entity(
    versions: VersionRepository,
    *,
    version: str = "entity-v2",
) -> VersionRef:
    new_ref = VersionRef(
        logical_id=ENTITY_V1.logical_id,
        version_id=VersionId(version),
    )
    new_entity = _entity(new_ref, name="Lan successor")
    await versions.create_successor(
        metadata=_metadata(
            new_ref,
            predecessor=ENTITY_V1,
            reason="entity semantic successor",
        ),
        payload=new_entity.model_dump(mode="json"),
        supersession_reason="entity semantic successor",
    )
    pointer = await versions.get_current(ENTITY_V1.logical_id)
    assert pointer is not None
    await versions.update_current(
        logical_id=new_ref.logical_id,
        version_id=new_ref.version_id,
        status=LifecycleState.APPROVED,
        expected_revision=pointer.revision,
    )
    return new_ref


def _request(
    *,
    requirements: tuple[ReferenceRequirement, ...],
    max_references: int = 4,
    supported_roles: tuple[str, ...] = ("identity.face", "identity.full_body"),
) -> ReferenceResolveRequest:
    return ReferenceResolveRequest(
        project_id=PROJECT_ID,
        active_profile_ref=PROFILE_REF,
        requirements=requirements,
        capability=ReferenceCapabilityConstraint(
            max_references=max_references,
            supported_roles=supported_roles,
            accepted_mime_types=("image/png",),
            requires_media_id=True,
        ),
    )


def test_reference_identity_is_stable_by_entity_slot_and_not_state_truth():
    v1 = _asset(version="ref-v1", slot="primary")
    entity_v2 = VersionRef(
        logical_id=ENTITY_V1.logical_id,
        version_id=VersionId("entity-v2"),
    )
    stable = reference_asset_logical_id(PROJECT_ID, entity_v2, slot="primary")
    alternate = reference_asset_logical_id(PROJECT_ID, ENTITY_V1, slot="alternate")

    assert stable == v1.reference_asset_id
    assert alternate != v1.reference_asset_id
    assert v1.content_hash == sha256_bytes(b"reference-one")
    assert "media_id" not in ReferenceAsset.model_fields
    assert "state" not in ReferenceAsset.model_fields
    assert "state_snapshot" not in ReferenceAsset.model_fields
    assert "prompt" not in ReferenceAsset.model_fields
    assert "provider" not in ReferenceAsset.model_fields
    assert "model" not in ReferenceAsset.model_fields

    with pytest.raises(ValidationError, match="deterministic project/entity/slot"):
        ReferenceAsset(
            **{
                **v1.model_dump(mode="python"),
                "reference_asset_id": LogicalId("reference-asset:project:film:forged"),
            }
        )


def test_legacy_reference_binding_enforces_uuid_and_preserves_entity_compatibility():
    asset = _asset()
    entity_binding = LegacyEntityBinding(
        legacy_entity_id="legacy-char-001",
        canonical_ref=ENTITY_V1,
        project_ids=(PROJECT_ID,),
        legacy_media_id=MEDIA_ID_A,
        legacy_reference_image_url="https://example.invalid/entity-ref.png",
    )
    binding = LegacyReferenceBinding.from_entity_binding(
        entity_binding,
        asset_ref=asset.ref,
    )
    assert binding.entity_ref == ENTITY_V1
    assert binding.legacy_media_id == MEDIA_ID_A

    with pytest.raises(ValidationError, match="UUID format"):
        LegacyReferenceBinding(
            asset_ref=asset.ref,
            entity_ref=ENTITY_V1,
            legacy_media_id="CAMS-not-a-uuid",
        )


def test_reference_asset_requires_exact_entity_provenance():
    asset = _asset()
    assert _asset_provenance(asset).source_versions == asset.source_bindings()
    wrong = Provenance(
        source_refs=("evidence:wrong",),
        actor_ref="studio:imp041",
        reason="wrong provenance",
        recorded_at=NOW,
    )
    assert wrong.source_versions != asset.source_bindings()


@pytest.mark.asyncio
async def test_reference_persists_and_registers_exact_entity_dependency(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_entity_and_profile(writer)
        repo = ReferenceAssetRepository(writer)
        asset = _asset()
        artifact = await repo.create_initial(
            asset=asset,
            provenance=_asset_provenance(asset),
            created_at=NOW,
        )
        pointer = await repo.get_current_pointer(asset.reference_asset_id)
        assert pointer is not None and pointer.status is LifecycleState.DRAFT
        await repo.promote_current(
            ref=artifact.ref,
            expected_revision=pointer.revision,
            status=LifecycleState.APPROVED,
        )
        incoming = await repo.graph.list_incoming(artifact.ref)
        assert len(incoming) == 1
        assert incoming[0].source_ref == ENTITY_V1
        assert incoming[0].edge_type == "reference_entity_version"
        loaded = await repo.get_version(artifact.ref)
        assert loaded == artifact
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_entity_blocks_reference_promotion(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_entity_and_profile(writer)
        repo = ReferenceAssetRepository(writer)
        asset = _asset()
        artifact = await repo.create_initial(
            asset=asset,
            provenance=_asset_provenance(asset),
            created_at=NOW,
        )
        await _supersede_entity(versions)
        with pytest.raises(ReferenceContractError, match="not exact current"):
            await repo.promote_current(
                ref=artifact.ref,
                expected_revision=0,
                status=LifecycleState.APPROVED,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_reference_successor_requires_real_semantic_change(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_entity_and_profile(writer)
        repo = ReferenceAssetRepository(writer)
        first = _asset(version="ref-v1")
        await _create_approved_asset(repo, first)

        no_op = first.model_copy(update={"version_id": VersionId("ref-v2")})
        with pytest.raises(ReferenceContractError, match="requires semantic"):
            await repo.create_successor(
                asset=no_op,
                predecessor=first.ref,
                provenance=_asset_provenance(no_op, "no-op successor"),
                created_at=NOW,
            )

        changed = first.model_copy(
            update={
                "version_id": VersionId("ref-v2-real"),
                "role": "identity.full_body",
            }
        )
        successor = await repo.create_successor(
            asset=changed,
            predecessor=first.ref,
            provenance=_asset_provenance(changed, "role changed"),
            created_at=NOW,
        )
        assert successor.metadata.predecessor == first.ref
        old = await repo.get_version(first.ref)
        assert old is not None and old.value.role == "identity.face"
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_successor_cannot_bypass_required_invalidation_promotion(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_entity_and_profile(writer)
        repo = ReferenceAssetRepository(writer)
        first = _asset(version="ref-v1")
        await _create_approved_asset(repo, first)
        second = first.model_copy(
            update={
                "version_id": VersionId("ref-v2"),
                "content_hash": sha256_bytes(b"changed"),
            }
        )
        await repo.create_successor(
            asset=second,
            predecessor=first.ref,
            provenance=_asset_provenance(second, "successor"),
            created_at=NOW,
        )
        pointer = await repo.get_current_pointer(first.reference_asset_id)
        assert pointer is not None
        with pytest.raises(ReferenceContractError, match="must use promote_successor_current"):
            await repo.promote_current(
                ref=second.ref,
                expected_revision=pointer.revision,
                status=LifecycleState.APPROVED,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_resolver_selects_minimal_deterministic_subset(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_entity_and_profile(writer)
        repo = ReferenceAssetRepository(writer)
        primary = _asset(version="primary-v1", slot="primary", content=b"primary")
        alternate = _asset(version="alternate-v1", slot="alternate", content=b"alternate")
        await _create_approved_asset(repo, primary)
        await _create_approved_asset(repo, alternate)

        resolver = ReferenceResolver(writer)
        request = _request(
            requirements=(ReferenceRequirement(entity_ref=ENTITY_V1, role="identity.face"),)
        )
        candidates = (
            ReferenceCandidate(asset_ref=alternate.ref, compatibility=_legacy_binding(alternate, media_id=MEDIA_ID_B)),
            ReferenceCandidate(asset_ref=primary.ref, compatibility=_legacy_binding(primary, media_id=MEDIA_ID_A)),
        )
        resolution = await resolver.resolve(request=request, candidates=candidates)

        expected = min((primary.ref, alternate.ref), key=lambda ref: (ref.logical_id.root, ref.version_id.root))
        assert len(resolution.selected) == 1
        assert resolution.selected[0].asset_ref == expected
        assert resolution.candidate_refs == tuple(sorted((primary.ref, alternate.ref), key=lambda ref: (ref.logical_id.root, ref.version_id.root)))
        assert any(item.reason == "not_selected_minimal_subset" for item in resolution.rejected)
        assert len(resolution.source_bindings()) == 3
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_resolver_blocks_unsupported_required_role(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_entity_and_profile(writer)
        resolver = ReferenceResolver(writer)
        request = _request(
            requirements=(ReferenceRequirement(entity_ref=ENTITY_V1, role="identity.face"),),
            supported_roles=("identity.full_body",),
        )
        with pytest.raises(ReferenceResolutionBlocked, match="unsupported by capability"):
            await resolver.resolve(request=request, candidates=())
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_reference_is_not_resolved_after_successor_becomes_current(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_entity_and_profile(writer)
        repo = ReferenceAssetRepository(writer)
        first = _asset(version="ref-v1")
        await _create_approved_asset(repo, first)
        second = first.model_copy(
            update={
                "version_id": VersionId("ref-v2"),
                "content_hash": sha256_bytes(b"replacement"),
            }
        )
        await repo.create_successor(
            asset=second,
            predecessor=first.ref,
            provenance=_asset_provenance(second, "replace reference bytes"),
            created_at=NOW,
        )
        pointer = await repo.get_current_pointer(first.reference_asset_id)
        assert pointer is not None
        await repo.promote_successor_current(
            ref=second.ref,
            expected_revision=pointer.revision,
            invalidation_provenance=_change_provenance(first, second),
            repair_or_recompute_requirement="recompute consumers for reference successor",
            status=LifecycleState.APPROVED,
        )

        resolver = ReferenceResolver(writer)
        request = _request(
            requirements=(ReferenceRequirement(entity_ref=ENTITY_V1, role="identity.face"),)
        )
        stale = ReferenceCandidate(asset_ref=first.ref, compatibility=_legacy_binding(first))
        with pytest.raises(ReferenceResolutionBlocked, match="missing required reference coverage"):
            await resolver.resolve(request=request, candidates=(stale,))
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_binding_requires_exact_resolution_provenance_and_revalidates_race(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_entity_and_profile(writer)
        consumer_ref = VersionRef(
            logical_id=LogicalId("shot-ir:project:film:shot-001"),
            version_id=VersionId("ir-v1"),
        )
        await _seed_version(versions, consumer_ref, {"fixture": "consumer"})

        repo = ReferenceAssetRepository(writer)
        first = _asset(version="ref-v1")
        await _create_approved_asset(repo, first)
        resolver = ReferenceResolver(writer)
        request = _request(
            requirements=(ReferenceRequirement(entity_ref=ENTITY_V1, role="identity.face"),)
        )
        resolution = await resolver.resolve(
            request=request,
            candidates=(ReferenceCandidate(asset_ref=first.ref, compatibility=_legacy_binding(first)),),
        )

        wrong = Provenance(
            source_refs=("evidence:wrong",),
            actor_ref="studio:imp041",
            reason="wrong binding provenance",
            recorded_at=NOW,
        )
        with pytest.raises(ReferenceContractError, match="exactly match"):
            await resolver.bind_consumer(
                resolution=resolution,
                consumer_ref=consumer_ref,
                provenance=wrong,
                created_at=NOW,
            )

        second = first.model_copy(
            update={
                "version_id": VersionId("ref-v2"),
                "content_hash": sha256_bytes(b"replacement-race"),
            }
        )
        await repo.create_successor(
            asset=second,
            predecessor=first.ref,
            provenance=_asset_provenance(second, "replace before bind"),
            created_at=NOW,
        )
        pointer = await repo.get_current_pointer(first.reference_asset_id)
        assert pointer is not None
        await repo.promote_successor_current(
            ref=second.ref,
            expected_revision=pointer.revision,
            invalidation_provenance=_change_provenance(first, second),
            repair_or_recompute_requirement="recompute consumers for reference successor",
            status=LifecycleState.APPROVED,
        )

        exact = build_reference_resolution_provenance(
            resolution,
            actor_ref="studio:imp041",
            reason="bind exact reference decision",
            recorded_at=NOW,
        )
        with pytest.raises(ReferenceContractError, match="no longer exact current"):
            await resolver.bind_consumer(
                resolution=resolution,
                consumer_ref=consumer_ref,
                provenance=exact,
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_reference_version_change_invalidates_only_bound_consumers(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_entity_and_profile(writer)
        bound_consumer = VersionRef(
            logical_id=LogicalId("shot-ir:project:film:bound"),
            version_id=VersionId("ir-v1"),
        )
        unrelated_consumer = VersionRef(
            logical_id=LogicalId("shot-ir:project:film:unrelated"),
            version_id=VersionId("ir-v1"),
        )
        await _seed_version(versions, bound_consumer, {"fixture": "bound"})
        await _seed_version(versions, unrelated_consumer, {"fixture": "unrelated"})

        repo = ReferenceAssetRepository(writer)
        old = _asset(version="ref-v1")
        await _create_approved_asset(repo, old)
        resolver = ReferenceResolver(writer)
        request = _request(
            requirements=(ReferenceRequirement(entity_ref=ENTITY_V1, role="identity.face"),)
        )
        resolution = await resolver.resolve(
            request=request,
            candidates=(ReferenceCandidate(asset_ref=old.ref, compatibility=_legacy_binding(old)),),
        )
        binding_provenance = build_reference_resolution_provenance(
            resolution,
            actor_ref="studio:imp041",
            reason="bind selected reference to consumer",
            recorded_at=NOW,
        )
        await resolver.bind_consumer(
            resolution=resolution,
            consumer_ref=bound_consumer,
            provenance=binding_provenance,
            created_at=NOW,
        )

        new = old.model_copy(
            update={
                "version_id": VersionId("ref-v2"),
                "content_hash": sha256_bytes(b"new-approved-reference"),
            }
        )
        await repo.create_successor(
            asset=new,
            predecessor=old.ref,
            provenance=_asset_provenance(new, "approved reference replacement"),
            created_at=NOW,
        )
        pointer = await repo.get_current_pointer(old.reference_asset_id)
        assert pointer is not None
        change_provenance = _change_provenance(
            old,
            new,
            "invalidate old reference consumers",
        )
        promotion = await repo.promote_successor_current(
            ref=new.ref,
            expected_revision=pointer.revision,
            invalidation_provenance=change_provenance,
            repair_or_recompute_requirement="recompile/regenerate/re-QA bound descendants",
            status=LifecycleState.APPROVED,
        )
        records = promotion.invalidations

        # Replaying the same accepted change is idempotent by deterministic dedupe.
        service = ReferenceAssetInvalidationService(writer)
        replayed = await service.invalidate_change(
            old=old,
            new=new,
            provenance=change_provenance,
            repair_or_recompute_requirement="recompile/regenerate/re-QA bound descendants",
        )
        assert {record.invalidation_id for record in replayed} == {
            record.invalidation_id for record in records
        }
        assert any(
            record.affected_object_id == bound_consumer.logical_id
            and record.affected_object_version == bound_consumer.version_id
            and record.dependency_edge_type == "reference_binding"
            for record in records
        )
        assert not any(
            record.affected_object_id == unrelated_consumer.logical_id
            for record in records
        )

        unresolved = await InvalidationRepository(writer).list_unresolved()
        assert {record.invalidation_id for record in records}.issubset(
            {record.invalidation_id for record in unresolved}
        )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_wrong_project_entity_cannot_become_reference_authority(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = VersionRepository(writer)
        await _seed_version(
            versions,
            ENTITY_V1,
            _entity(project_ids=(OTHER_PROJECT_ID,)).model_dump(mode="json"),
        )
        repo = ReferenceAssetRepository(writer)
        asset = _asset()
        with pytest.raises(ReferenceContractError, match="does not belong to project"):
            await repo.create_initial(
                asset=asset,
                provenance=_asset_provenance(asset),
                created_at=NOW,
            )
    finally:
        await writer.close()
