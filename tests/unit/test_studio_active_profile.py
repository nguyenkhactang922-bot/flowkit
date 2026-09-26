"""IMP-013 tests for immutable ActiveProductionProfile snapshots."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    ActiveProductionProfileBinding,
    ActiveProductionProfileDependencyBinder,
    ActiveProductionProfileInvalidationService,
    ActiveProductionProfileRepository,
    AuthorityTier,
    ContenderDisposition,
    DependencyGraphRepository,
    DependencyInvalidationError,
    DependencyReachability,
    FieldResolutionTrace,
    InvalidationRepository,
    LogicalId,
    PolicySourceKind,
    ProfileResolutionArtifact,
    ProfileResolutionResult,
    Provenance,
    ResolutionContender,
    ResolutionTrace,
    SemanticRecordMetadata,
    SQLiteWriteOwner,
    VersionId,
    VersionRef,
    VersionRepository,
    build_active_profile_provenance,
    build_resolution_provenance,
    diff_active_profiles,
    materialize_active_profile,
)
from agent.studio.primitives import LifecycleState


NOW = datetime(2026, 9, 26, 10, 30, tzinfo=timezone.utc)
RESOLVER = VersionRef(
    logical_id=LogicalId("resolver:profile"),
    version_id=VersionId("v1"),
)


def _canonical_json(value) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _hash_json(value) -> str:
    return "sha256:" + hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


def _ref(logical: str, version: str = "v1") -> VersionRef:
    return VersionRef(logical_id=LogicalId(logical), version_id=VersionId(version))


def _base_provenance(reason: str) -> Provenance:
    return Provenance(
        source_refs=("evidence:imp013",),
        actor_ref="studio:test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp013",
    )


def _field(
    path: str,
    value,
    *,
    source: VersionRef,
    tier: AuthorityTier = AuthorityTier.HARD_CONSTRAINT,
    kind: PolicySourceKind = PolicySourceKind.PROJECT_HARD_CONSTRAINT,
    rank: int = 1,
) -> FieldResolutionTrace:
    contender = ResolutionContender(
        path=path,
        value=value,
        tier=tier,
        precedence_rank=rank,
        source_kind=kind,
        source_ref=source,
        reason=f"source for {path}",
        disposition=ContenderDisposition.SELECTED,
    )
    return FieldResolutionTrace(
        path=path,
        value=value,
        winning_tier=tier,
        precedence_rank=rank,
        winning_source_kind=kind,
        winning_source_ref=source,
        resolution_reason=f"resolved {path}",
        contenders=(contender,),
    )


def _resolution_artifact(
    *,
    resolution_version: str,
    tone="serious",
    camera="dolly",
    tone_source: VersionRef | None = None,
    camera_source: VersionRef | None = None,
    resolver_version: VersionRef = RESOLVER,
) -> ProfileResolutionArtifact:
    project_id = LogicalId("project:film")
    project_ref = _ref("project-input:film")
    topic_ref = _ref("topic-resolution:film")
    domain_ref = _ref("domain-resolution:film")
    tone_source = tone_source or topic_ref
    camera_source = camera_source or topic_ref
    effective = {
        "camera.motion": camera,
        "tone": tone,
    }
    fields = (
        _field("camera.motion", camera, source=camera_source),
        _field("tone", tone, source=tone_source),
    )
    trace = ResolutionTrace(
        resolution_id=LogicalId(f"resolution:{resolution_version}"),
        resolver_version=resolver_version,
        project_id=project_id,
        project_ref=project_ref,
        topic_ref=topic_ref,
        domain_ref=domain_ref,
        pack_selection=(),
        direct_selected_pack_refs=(),
        effective_pack_refs=(),
        fields=fields,
        input_fingerprint=_hash_json(
            {
                "resolution_version": resolution_version,
                "tone": tone,
                "camera": camera,
                "resolver": (
                    resolver_version.logical_id.root,
                    resolver_version.version_id.root,
                ),
            }
        ),
        effective_policy_hash=_hash_json(effective),
    )
    result = ProfileResolutionResult(
        project_id=project_id,
        effective_policy=effective,
        trace=trace,
    )
    provenance = build_resolution_provenance(
        result,
        actor_ref="studio:profile-resolver",
        reason="persist resolver output",
        recorded_at=NOW,
        source_refs=("evidence:resolver",),
        correlation_id="run:imp013",
    )
    return ProfileResolutionArtifact(
        metadata=SemanticRecordMetadata(
            logical_id=LogicalId("profile-resolution:project:film"),
            version_id=VersionId(resolution_version),
            provenance=provenance,
            created_at=NOW,
        ),
        result=result,
    )


def _profile_artifact_inputs(
    *,
    resolution_version: str,
    profile_version: str,
    tone="serious",
    camera="dolly",
    tone_source: VersionRef | None = None,
    camera_source: VersionRef | None = None,
):
    resolution = _resolution_artifact(
        resolution_version=resolution_version,
        tone=tone,
        camera=camera,
        tone_source=tone_source,
        camera_source=camera_source,
    )
    profile = materialize_active_profile(
        resolution,
        profile_version=VersionId(profile_version),
    )
    provenance = build_active_profile_provenance(
        profile,
        actor_ref="studio:active-profile",
        reason="pin exact resolver output",
        recorded_at=NOW,
        source_refs=("evidence:profile",),
        correlation_id="run:imp013",
    )
    return resolution, profile, provenance


def _semantic_metadata(logical: str) -> SemanticRecordMetadata:
    return SemanticRecordMetadata(
        logical_id=LogicalId(logical),
        version_id=VersionId("v1"),
        provenance=_base_provenance(f"create {logical}"),
        created_at=NOW,
    )


def test_snapshot_is_deeply_immutable_and_pins_exact_resolution():
    resolution, profile, _ = _profile_artifact_inputs(
        resolution_version="v1",
        profile_version="p1",
        tone={"mode": "serious", "tags": ["restrained"]},
    )

    assert profile.profile_resolution_ref == resolution.ref
    assert profile.resolver_version == RESOLVER
    assert profile.profile_id == LogicalId("active-profile:project:film")
    assert profile.profile_version == VersionId("p1")

    decoded = profile.effective_policy
    decoded["tone"]["tags"].append("mutated")
    assert profile.effective_policy["tone"]["tags"] == ["restrained"]

    with pytest.raises(ValidationError):
        profile.profile_version = VersionId("p2")


def test_policy_entries_pin_winning_path_provenance_and_trace_hash():
    resolution, profile, _ = _profile_artifact_inputs(
        resolution_version="v1",
        profile_version="p1",
    )
    assert [entry.path for entry in profile.policy_entries] == [
        "camera.motion",
        "tone",
    ]
    assert profile.path_provenance["tone"].winning_source_ref == resolution.result.trace.topic_ref
    assert profile.path_provenance["tone"].winning_tier is AuthorityTier.HARD_CONSTRAINT
    assert profile.resolution_trace_hash == _hash_json(
        resolution.result.trace.model_dump(mode="json")
    )


@pytest.mark.asyncio
async def test_profile_versions_persist_immutable_and_pin_current_explicitly(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo = ActiveProductionProfileRepository(writer)
        _, p1, prov1 = _profile_artifact_inputs(
            resolution_version="v1",
            profile_version="p1",
        )
        a1 = await repo.create_initial(
            profile=p1,
            provenance=prov1,
            created_at=NOW,
        )
        assert (await repo.get_current(p1.project_id)).ref == a1.ref

        _, p2, prov2 = _profile_artifact_inputs(
            resolution_version="v2",
            profile_version="p2",
            tone="warmer",
        )
        a2 = await repo.create_successor(
            profile=p2,
            predecessor=a1.ref,
            provenance=prov2,
            created_at=NOW,
        )

        # Creating a successor does not silently switch the pinned current profile.
        assert (await repo.get_current(p1.project_id)).ref == a1.ref
        old_roundtrip = await repo.get(a1.ref)
        assert old_roundtrip is not None
        assert old_roundtrip.profile.effective_policy["tone"] == "serious"

        pointer = await repo.pin_current(
            profile_ref=a2.ref,
            expected_revision=0,
        )
        assert pointer.version_id == VersionId("p2")
        assert pointer.status is LifecycleState.LOCKED
        assert pointer.revision == 1
        assert (await repo.get_current(p1.project_id)).ref == a2.ref
    finally:
        await writer.close()


def test_changed_path_delta_includes_value_and_provenance_changes():
    _, p1, _ = _profile_artifact_inputs(
        resolution_version="v1",
        profile_version="p1",
    )
    _, p2, _ = _profile_artifact_inputs(
        resolution_version="v2",
        profile_version="p2",
        tone="warmer",
        camera_source=_ref("fact:camera", "v7"),
    )

    delta = diff_active_profiles(p1, p2)
    assert delta.value_changed_paths == ("tone",)
    assert delta.provenance_changed_paths == ("camera.motion",)
    assert delta.changed_paths == ("camera.motion", "tone")


def test_same_effective_paths_produce_empty_delta_even_for_new_profile_version():
    _, p1, _ = _profile_artifact_inputs(
        resolution_version="v1",
        profile_version="p1",
    )
    _, p2, _ = _profile_artifact_inputs(
        resolution_version="v2",
        profile_version="p2",
    )
    delta = diff_active_profiles(p1, p2)
    assert delta.changed_paths == ()


def test_downstream_binding_exposes_only_exact_profile_ref_and_paths():
    _, profile, _ = _profile_artifact_inputs(
        resolution_version="v1",
        profile_version="p1",
    )
    binding = ActiveProductionProfileBinding(
        profile_ref=profile.ref,
        required_paths=("tone", "camera.motion", "tone"),
    )
    assert binding.profile_ref == profile.ref
    assert binding.required_paths == ("camera.motion", "tone")
    assert set(ActiveProductionProfileBinding.model_fields) == {
        "profile_ref",
        "required_paths",
    }


@pytest.mark.asyncio
async def test_selective_profile_path_invalidation_preserves_unrelated_branch(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        profiles = ActiveProductionProfileRepository(writer)
        versions = VersionRepository(writer)
        graph = DependencyGraphRepository(writer)
        invalidations = InvalidationRepository(writer, graph)
        binder = ActiveProductionProfileDependencyBinder(graph)
        service = ActiveProductionProfileInvalidationService(
            graph,
            invalidations,
        )

        _, p1, prov1 = _profile_artifact_inputs(
            resolution_version="v1",
            profile_version="p1",
        )
        a1 = await profiles.create_initial(
            profile=p1,
            provenance=prov1,
            created_at=NOW,
        )
        _, p2, prov2 = _profile_artifact_inputs(
            resolution_version="v2",
            profile_version="p2",
            tone="warmer",
        )
        a2 = await profiles.create_successor(
            profile=p2,
            predecessor=a1.ref,
            provenance=prov2,
            created_at=NOW,
        )

        for logical in (
            "artifact:tone",
            "artifact:camera",
            "artifact:tone-child",
            "artifact:whole-profile",
        ):
            await versions.create_initial(
                metadata=_semantic_metadata(logical),
                payload={"logical": logical},
            )

        tone_ref = _ref("artifact:tone")
        camera_ref = _ref("artifact:camera")
        child_ref = _ref("artifact:tone-child")
        whole_ref = _ref("artifact:whole-profile")

        await binder.bind(
            profile=p1,
            dependent=tone_ref,
            path="tone",
            reason="story tone depends on profile tone",
            provenance=_base_provenance("bind tone"),
            created_at=NOW,
        )
        await binder.bind(
            profile=p1,
            dependent=camera_ref,
            path="camera.motion",
            reason="camera branch depends on motion policy",
            provenance=_base_provenance("bind camera"),
            created_at=NOW,
        )
        await binder.bind(
            profile=p1,
            dependent=whole_ref,
            path="*",
            reason="whole-profile consumer",
            provenance=_base_provenance("bind whole profile"),
            created_at=NOW,
        )
        await graph.create_edge(
            source=tone_ref,
            dependent=child_ref,
            edge_type="DERIVES_FROM",
            dependency_reason="child derives from tone artifact",
            provenance=_base_provenance("bind child"),
            created_at=NOW,
        )

        result = await service.invalidate_change(
            old=p1,
            new=p2,
            provenance=_base_provenance("profile changed"),
            repair_or_recompute_requirement="recompute affected profile dependents",
        )

        assert result.change_set.changed_paths == ("tone",)
        affected = {
            (record.affected_object_id.root, record.affected_object_version.root)
            for record in result.invalidations
        }
        assert affected == {
            ("artifact:tone", "v1"),
            ("artifact:tone-child", "v1"),
            ("artifact:whole-profile", "v1"),
        }
        assert ("artifact:camera", "v1") not in affected
        assert len(await invalidations.list_unresolved()) == 3
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_no_changed_paths_create_no_invalidation_records(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        profiles = ActiveProductionProfileRepository(writer)
        graph = DependencyGraphRepository(writer)
        invalidations = InvalidationRepository(writer, graph)
        service = ActiveProductionProfileInvalidationService(graph, invalidations)

        _, p1, prov1 = _profile_artifact_inputs(
            resolution_version="v1",
            profile_version="p1",
        )
        a1 = await profiles.create_initial(
            profile=p1,
            provenance=prov1,
            created_at=NOW,
        )
        _, p2, prov2 = _profile_artifact_inputs(
            resolution_version="v2",
            profile_version="p2",
        )
        await profiles.create_successor(
            profile=p2,
            predecessor=a1.ref,
            provenance=prov2,
            created_at=NOW,
        )

        result = await service.invalidate_change(
            old=p1,
            new=p2,
            provenance=_base_provenance("profile re-materialized"),
            repair_or_recompute_requirement="no-op when effective paths unchanged",
        )
        assert result.change_set.changed_paths == ()
        assert result.invalidations == ()
        assert await invalidations.list_unresolved() == []
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_profile_path_binder_rejects_unknown_path(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        profiles = ActiveProductionProfileRepository(writer)
        versions = VersionRepository(writer)
        graph = DependencyGraphRepository(writer)
        binder = ActiveProductionProfileDependencyBinder(graph)

        _, p1, prov1 = _profile_artifact_inputs(
            resolution_version="v1",
            profile_version="p1",
        )
        await profiles.create_initial(
            profile=p1,
            provenance=prov1,
            created_at=NOW,
        )
        await versions.create_initial(
            metadata=_semantic_metadata("artifact:unknown"),
            payload={"kind": "unknown"},
        )

        with pytest.raises(ValueError, match="does not exist"):
            await binder.bind(
                profile=p1,
                dependent=_ref("artifact:unknown"),
                path="lighting.nonexistent",
                reason="bad dependency",
                provenance=_base_provenance("bad bind"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_selective_invalidation_rejects_forged_reachability_plan(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        profiles = ActiveProductionProfileRepository(writer)
        versions = VersionRepository(writer)
        graph = DependencyGraphRepository(writer)
        invalidations = InvalidationRepository(writer, graph)

        _, p1, prov1 = _profile_artifact_inputs(
            resolution_version="v1",
            profile_version="p1",
        )
        a1 = await profiles.create_initial(
            profile=p1,
            provenance=prov1,
            created_at=NOW,
        )
        _, p2, prov2 = _profile_artifact_inputs(
            resolution_version="v2",
            profile_version="p2",
            tone="warmer",
        )
        a2 = await profiles.create_successor(
            profile=p2,
            predecessor=a1.ref,
            provenance=prov2,
            created_at=NOW,
        )

        await versions.create_initial(
            metadata=_semantic_metadata("artifact:unrelated-source"),
            payload={"kind": "unrelated-source"},
        )
        await versions.create_initial(
            metadata=_semantic_metadata("artifact:forged-victim"),
            payload={"kind": "forged-victim"},
        )
        unrelated = _ref("artifact:unrelated-source")
        victim = _ref("artifact:forged-victim")
        edge = await graph.create_edge(
            source=unrelated,
            dependent=victim,
            edge_type="DERIVES_FROM",
            dependency_reason="unrelated durable edge",
            provenance=_base_provenance("bind unrelated edge"),
            created_at=NOW,
        )

        forged = DependencyReachability(
            object_id=victim.logical_id,
            version_id=victim.version_id,
            via_edge_id=edge.edge_id,
            via_edge_type=edge.edge_type,
            dependency_reason=edge.dependency_reason,
            depth=1,
            path_edge_ids=(edge.edge_id,),
        )

        with pytest.raises(
            DependencyInvalidationError,
            match="does not start from/continue",
        ):
            await invalidations.create_for_change(
                cause="ACTIVE_PRODUCTION_PROFILE_CHANGED",
                source_old=a1.ref,
                source_new=a2.ref,
                provenance=_base_provenance("forged selective plan"),
                scope="ACTIVE_PROFILE_PATHS:tone",
                repair_or_recompute_requirement="must fail closed",
                reachable=(forged,),
            )

        assert await invalidations.list_unresolved() == []
    finally:
        await writer.close()
