"""IMP-012 tests for the single canonical Profile Resolver."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

import agent.studio.profile_resolver as profile_module
from agent.studio.brainpack import (
    BrainPackApplicability,
    BrainPackDefinition,
    BrainPackFamily,
    BrainPackLifecycleState,
    BrainPackRef,
    BrainPackRegistryRepository,
    BrainPackRule,
    BrainPackRuleStrength,
    BrainPackSourceEvidence,
    BrainPackSourceKind,
)
from agent.studio.persistence import SQLiteWriteOwner
from agent.studio.primitives import (
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    VersionId,
    VersionRef,
)
from agent.studio.profile_resolver import (
    AuthorityTier,
    ContenderDisposition,
    HardConstraintConflict,
    LocalIntentNotAllowed,
    LocalPolicyIntent,
    OverrideNotAllowed,
    PackCompositionConflict,
    PackNotReadyError,
    PolicyAssertion,
    PolicySourceKind,
    ProfileResolutionRepository,
    ProfileResolver,
    ProfileResolverRequest,
    RequestedProjectOverride,
    ResolutionConflict,
    build_resolution_provenance,
)
from agent.studio.topic_domain import (
    AxisClassification,
    ClassificationAxis,
    DomainResolution,
    DomainResolutionArtifact,
    ProjectBootstrapArtifact,
    ProjectBootstrapInput,
    ProjectConstraint,
    TopicResolution,
    TopicResolutionArtifact,
    WeightedLabel,
)


NOW = datetime(2026, 9, 26, 9, 0, tzinfo=timezone.utc)
RESOLVER_VERSION = VersionRef(
    logical_id=LogicalId("rule:profile-resolver"),
    version_id=VersionId("v1"),
)


def _source_provenance(reason: str = "test source") -> Provenance:
    return Provenance(
        source_refs=("source:test",),
        actor_ref="studio:test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp012",
    )


def _metadata(
    logical_id: str,
    version: str,
    provenance: Provenance,
) -> SemanticRecordMetadata:
    return SemanticRecordMetadata(
        logical_id=LogicalId(logical_id),
        version_id=VersionId(version),
        provenance=provenance,
        created_at=NOW,
    )


def _weighted(label: str) -> WeightedLabel:
    return WeightedLabel(
        label=label,
        weight=1.0,
        reason=f"classified as {label}",
        evidence_refs=(f"evidence:{label}",),
    )


def _inputs(
    *,
    constraints: tuple[ProjectConstraint, ...] = (),
) -> tuple[
    ProjectBootstrapArtifact,
    TopicResolutionArtifact,
    DomainResolutionArtifact,
]:
    project_id = LogicalId("project:resolver")
    project = ProjectBootstrapArtifact(
        metadata=_metadata(
            "project-input:project:resolver",
            "v1",
            Provenance(
                source_refs=("source:brief",),
                actor_ref="studio:test",
                reason="bootstrap",
                recorded_at=NOW,
            ),
        ),
        value=ProjectBootstrapInput(
            project_id=project_id,
            raw_topic="Noir detective returns home",
            project_goals=("tense short film",),
            language="en",
            locale="en-US",
            target_duration_seconds=600,
            platform_hints=("youtube",),
            format_hints=("short-film",),
            audience_hints=("adults",),
            factuality_mode="fictional",
            constraints=constraints,
            source_evidence_refs=("source:brief",),
        ),
    )

    normalizer = VersionRef(
        logical_id=LogicalId("rule:topic-normalizer"),
        version_id=VersionId("v1"),
    )
    topic_classifier = VersionRef(
        logical_id=LogicalId("rule:topic-classifier"),
        version_id=VersionId("v1"),
    )
    topic = TopicResolutionArtifact(
        metadata=_metadata(
            "topic-resolution:project:resolver",
            "v1",
            Provenance(
                source_versions=(
                    SourceVersionBinding(role="project_input", source=project.ref),
                    SourceVersionBinding(
                        role="topic_normalizer_rule",
                        source=normalizer,
                    ),
                    SourceVersionBinding(
                        role="topic_classifier_rule",
                        source=topic_classifier,
                    ),
                ),
                source_refs=("evidence:topic",),
                actor_ref="studio:test",
                reason="topic resolution",
                recorded_at=NOW,
                rule_version=topic_classifier,
            ),
        ),
        value=TopicResolution(
            project_id=project_id,
            normalized_topic="Noir detective returns home",
            weighted_topic_labels=(_weighted("noir"), _weighted("detective")),
            constraints=constraints,
            factuality_mode="fictional",
            normalizer_rule_version=normalizer,
            classifier_rule_version=topic_classifier,
        ),
    )

    registry_metadata = VersionRef(
        logical_id=LogicalId("registry:domain"),
        version_id=VersionId("v1"),
    )
    domain_classifier = VersionRef(
        logical_id=LogicalId("rule:domain-classifier"),
        version_id=VersionId("v1"),
    )
    classifications = (
        AxisClassification(
            axis=ClassificationAxis.DOMAIN,
            labels=(_weighted("film"),),
        ),
        AxisClassification(
            axis=ClassificationAxis.NICHE,
            labels=(_weighted("noir"),),
        ),
        AxisClassification(
            axis=ClassificationAxis.GENRE,
            labels=(_weighted("drama"),),
        ),
        AxisClassification(
            axis=ClassificationAxis.AUDIENCE,
            labels=(_weighted("adults"),),
        ),
        AxisClassification(
            axis=ClassificationAxis.FORMAT,
            labels=(_weighted("short-film"),),
        ),
        AxisClassification(
            axis=ClassificationAxis.PLATFORM,
            labels=(_weighted("youtube"),),
        ),
        AxisClassification(
            axis=ClassificationAxis.FACTUALITY,
            labels=(_weighted("fictional"),),
        ),
    )
    domain = DomainResolutionArtifact(
        metadata=_metadata(
            "niche-resolution:project:resolver",
            "v1",
            Provenance(
                source_versions=(
                    SourceVersionBinding(
                        role="topic_resolution",
                        source=topic.ref,
                    ),
                    SourceVersionBinding(
                        role="registry_metadata",
                        source=registry_metadata,
                    ),
                    SourceVersionBinding(
                        role="domain_classifier_rule",
                        source=domain_classifier,
                    ),
                ),
                source_refs=("evidence:domain",),
                actor_ref="studio:test",
                reason="domain resolution",
                recorded_at=NOW,
                rule_version=domain_classifier,
            ),
        ),
        value=DomainResolution(
            project_id=project_id,
            topic_resolution_ref=topic.ref,
            registry_metadata_ref=registry_metadata,
            classifier_rule_version=domain_classifier,
            classifications=classifications,
            project_constraints=constraints,
        ),
    )
    return project, topic, domain


def _pack_provenance() -> Provenance:
    return Provenance(
        source_refs=("source:pack", "license:pack"),
        actor_ref="studio:test",
        reason="register pack",
        recorded_at=NOW,
    )


def _pack(
    pack_id: str,
    version: str,
    *,
    path: str,
    value,
    strength: BrainPackRuleStrength = BrainPackRuleStrength.SOFT,
    override_allowed: bool = True,
    parents: tuple[BrainPackRef, ...] = (),
    applicability: BrainPackApplicability | None = None,
) -> BrainPackDefinition:
    return BrainPackDefinition(
        pack_id=LogicalId(pack_id),
        pack_version=VersionId(version),
        family=BrainPackFamily.CREATIVE,
        name=f"{pack_id} {version}",
        description="resolver fixture pack",
        parents=parents,
        applicability=applicability or BrainPackApplicability(domains=("film",)),
        rules=(
            BrainPackRule(
                key=path,
                value=value,
                strength=strength,
                override_allowed=override_allowed,
                reason=f"{pack_id} defines {path}",
            ),
        ),
        source_evidence=(
            BrainPackSourceEvidence(
                source_kind=BrainPackSourceKind.INTERNAL,
                source_ref="source:pack",
                license_expression="PROPRIETARY",
                license_evidence_ref="license:pack",
            ),
        ),
        provenance=_pack_provenance(),
        created_at=NOW,
    )


async def _freeze(
    registry: BrainPackRegistryRepository,
    definition: BrainPackDefinition,
) -> None:
    await registry.create(definition)
    await registry.transition_lifecycle(
        ref=definition.ref,
        target=BrainPackLifecycleState.VALIDATED,
        expected_revision=0,
        reason="validated",
        provenance=_pack_provenance(),
    )
    await registry.transition_lifecycle(
        ref=definition.ref,
        target=BrainPackLifecycleState.FROZEN,
        expected_revision=1,
        reason="frozen",
        provenance=_pack_provenance(),
    )


def _request(
    *,
    constraints: tuple[ProjectConstraint, ...] = (),
    packs: tuple[BrainPackRef, ...] = (),
    locked: tuple[PolicyAssertion, ...] = (),
    overrides: tuple[RequestedProjectOverride, ...] = (),
    local: tuple[LocalPolicyIntent, ...] = (),
) -> ProfileResolverRequest:
    project, topic, domain = _inputs(constraints=constraints)
    return ProfileResolverRequest(
        project=project,
        topic=topic,
        domain=domain,
        candidate_pack_refs=packs,
        locked_values=locked,
        requested_overrides=overrides,
        local_intent=local,
    )


@pytest.mark.asyncio
async def test_hard_project_constraint_beats_soft_pack_policy(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        pack = _pack("pack:soft-tone", "v1", path="tone", value="playful")
        await _freeze(registry, pack)

        resolver = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
        )
        result = await resolver.resolve(
            _request(
                constraints=(
                    ProjectConstraint(
                        key="tone",
                        value="serious",
                        hard=True,
                        reason="locked project tone",
                    ),
                ),
                packs=(pack.ref,),
            )
        )

        assert result.effective_policy["tone"] == "serious"
        trace = next(item for item in result.trace.fields if item.path == "tone")
        assert trace.winning_tier is AuthorityTier.HARD_CONSTRAINT
        assert trace.winning_source_kind is PolicySourceKind.PROJECT_HARD_CONSTRAINT
        assert any(
            contender.source_kind is PolicySourceKind.BRAINPACK_POLICY
            and contender.disposition
            is ContenderDisposition.OVERRIDDEN_BY_HIGHER_AUTHORITY
            for contender in trace.contenders
        )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_allowlisted_override_beats_pack_but_cannot_beat_hard_constraint(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        pack = _pack("pack:override", "v1", path="tone", value="playful")
        await _freeze(registry, pack)
        override = RequestedProjectOverride(
            path="tone",
            value="moody",
            reason="project lock",
        )

        resolver = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
            override_allowlist=frozenset({"tone"}),
        )
        soft_result = await resolver.resolve(
            _request(packs=(pack.ref,), overrides=(override,))
        )
        assert soft_result.effective_policy["tone"] == "moody"

        hard_result = await resolver.resolve(
            _request(
                constraints=(
                    ProjectConstraint(
                        key="tone",
                        value="serious",
                        hard=True,
                        reason="hard project requirement",
                    ),
                ),
                packs=(pack.ref,),
                overrides=(override,),
            )
        )
        assert hard_result.effective_policy["tone"] == "serious"

        blocked = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
        )
        with pytest.raises(OverrideNotAllowed):
            await blocked.resolve(
                _request(packs=(pack.ref,), overrides=(override,))
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_locked_fact_outranks_hard_override_pack_soft_and_local_intent(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        pack = _pack("pack:all-tiers", "v1", path="tone", value="pack")
        await _freeze(registry, pack)
        locked_ref = VersionRef(
            logical_id=LogicalId("fact:tone"),
            version_id=VersionId("v1"),
        )
        local_ref = VersionRef(
            logical_id=LogicalId("intent:shot"),
            version_id=VersionId("v1"),
        )
        resolver = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
            override_allowlist=frozenset({"tone"}),
            local_intent_allowlist=frozenset({"tone"}),
        )
        result = await resolver.resolve(
            _request(
                constraints=(
                    ProjectConstraint(
                        key="tone",
                        value="hard",
                        hard=True,
                        reason="hard",
                    ),
                ),
                packs=(pack.ref,),
                locked=(
                    PolicyAssertion(
                        path="tone",
                        value="locked",
                        source_ref=locked_ref,
                        reason="canonical invariant",
                    ),
                ),
                overrides=(
                    RequestedProjectOverride(
                        path="tone",
                        value="override",
                        reason="requested override",
                    ),
                ),
                local=(
                    LocalPolicyIntent(
                        path="tone",
                        value="local",
                        source_ref=local_ref,
                        reason="local downstream intent",
                    ),
                ),
            )
        )
        assert result.effective_policy["tone"] == "locked"
        trace = result.trace.fields[0]
        assert trace.winning_tier is AuthorityTier.LOCKED_CANONICAL
        assert [item.precedence_rank for item in trace.contenders] == sorted(
            item.precedence_rank for item in trace.contenders
        )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_unresolved_hard_hard_conflict_fails_closed(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        hard_pack = _pack(
            "pack:hard",
            "v1",
            path="tone",
            value="pack-hard",
            strength=BrainPackRuleStrength.HARD,
        )
        await _freeze(registry, hard_pack)
        resolver = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
        )
        with pytest.raises(HardConstraintConflict, match="hard-hard"):
            await resolver.resolve(
                _request(
                    constraints=(
                        ProjectConstraint(
                            key="tone",
                            value="project-hard",
                            hard=True,
                            reason="hard project requirement",
                        ),
                    ),
                    packs=(hard_pack.ref,),
                )
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_applicability_selects_only_matching_candidate_pack(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        film = _pack(
            "pack:film",
            "v1",
            path="camera.motion",
            value="restrained",
            applicability=BrainPackApplicability(domains=("film",)),
        )
        docs = _pack(
            "pack:docs",
            "v1",
            path="camera.motion",
            value="handheld",
            applicability=BrainPackApplicability(domains=("documentary",)),
        )
        await _freeze(registry, film)
        await _freeze(registry, docs)

        resolver = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
        )
        result = await resolver.resolve(
            _request(packs=(docs.ref, film.ref))
        )

        assert result.effective_policy["camera.motion"] == "restrained"
        decisions = {item.pack_ref.pack_id.root: item for item in result.trace.pack_selection}
        assert decisions["pack:film"].selected is True
        assert decisions["pack:docs"].selected is False
        assert result.trace.direct_selected_pack_refs == (film.ref,)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_child_pack_can_override_overrideable_parent_rule(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        parent = _pack(
            "pack:parent",
            "v1",
            path="lighting.key",
            value="soft",
            override_allowed=True,
        )
        await _freeze(registry, parent)
        child = _pack(
            "pack:child",
            "v1",
            path="lighting.key",
            value="hard",
            parents=(parent.ref,),
        )
        await _freeze(registry, child)

        resolver = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
        )
        result = await resolver.resolve(_request(packs=(child.ref,)))
        assert result.effective_policy["lighting.key"] == "hard"
        assert result.trace.effective_pack_refs == (child.ref, parent.ref)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_nonoverrideable_parent_rule_blocks_child_override(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        parent = _pack(
            "pack:parent-lock",
            "v1",
            path="lighting.key",
            value="soft",
            override_allowed=False,
        )
        await _freeze(registry, parent)
        child = _pack(
            "pack:child-lock",
            "v1",
            path="lighting.key",
            value="hard",
            parents=(parent.ref,),
        )
        await _freeze(registry, child)

        resolver = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
        )
        with pytest.raises(PackCompositionConflict, match="non-overrideable"):
            await resolver.resolve(_request(packs=(child.ref,)))
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_equal_precedence_pack_conflict_fails_instead_of_last_write_wins(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        a = _pack("pack:a", "v1", path="tone", value="a")
        b = _pack("pack:b", "v1", path="tone", value="b")
        await _freeze(registry, a)
        await _freeze(registry, b)

        resolver = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
        )
        with pytest.raises(ResolutionConflict, match="equal-precedence"):
            await resolver.resolve(_request(packs=(a.ref, b.ref)))
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_candidate_pack_must_be_frozen(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        draft = _pack("pack:draft", "v1", path="tone", value="draft")
        await registry.create(draft)
        resolver = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
        )
        with pytest.raises(PackNotReadyError, match="FROZEN"):
            await resolver.resolve(_request(packs=(draft.ref,)))
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_resolution_is_reproducible_and_candidate_order_independent(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        tone = _pack("pack:tone", "v1", path="tone", value="restrained")
        pace = _pack("pack:pace", "v1", path="pacing", value="slow-burn")
        await _freeze(registry, tone)
        await _freeze(registry, pace)
        resolver = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
        )

        first = await resolver.resolve(_request(packs=(tone.ref, pace.ref)))
        second = await resolver.resolve(_request(packs=(pace.ref, tone.ref)))

        assert first == second
        assert first.trace.input_fingerprint == second.trace.input_fingerprint
        assert first.trace.resolution_id == second.trace.resolution_id
        assert first.trace.effective_policy_hash == second.trace.effective_policy_hash
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_resolution_round_trips_through_immutable_version_repository(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        pack = _pack("pack:persist", "v1", path="tone", value="restrained")
        await _freeze(registry, pack)
        resolver = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
        )
        result = await resolver.resolve(_request(packs=(pack.ref,)))

        provenance = build_resolution_provenance(
            result,
            actor_ref="studio:profile-resolver",
            reason="persist exact deterministic resolution",
            recorded_at=NOW,
            source_refs=("evidence:resolution",),
            correlation_id="run:imp012",
        )
        repository = ProfileResolutionRepository(writer)
        artifact = await repository.create_initial(
            result=result,
            version_id=VersionId("v1"),
            provenance=provenance,
            created_at=NOW,
        )
        restored = await repository.get(artifact.ref)

        assert restored is not None
        assert restored.result == result
        assert restored.metadata.provenance.rule_version == RESOLVER_VERSION
        roles = {
            item.role: item.source
            for item in restored.metadata.provenance.source_versions
        }
        assert roles["project_input"] == result.trace.project_ref
        assert roles["topic_resolution"] == result.trace.topic_ref
        assert roles["domain_resolution"] == result.trace.domain_ref
        assert pack.ref.pack_id == roles["brainpack_000"].logical_id
        assert pack.ref.pack_version == roles["brainpack_000"].version_id
    finally:
        await writer.close()


def test_provider_state_and_nonallowlisted_local_intent_fail_closed():
    with pytest.raises(ValidationError, match="provider/runtime field"):
        RequestedProjectOverride(
            path="camera",
            value={"provider_id": "remote"},
            reason="invalid provider leakage",
        )

    project, topic, domain = _inputs()
    request = ProfileResolverRequest(
        project=project,
        topic=topic,
        domain=domain,
        local_intent=(
            LocalPolicyIntent(
                path="camera.motion",
                value="dolly",
                source_ref=VersionRef(
                    logical_id=LogicalId("intent:shot"),
                    version_id=VersionId("v1"),
                ),
                reason="local request",
            ),
        ),
    )
    assert request.local_intent[0].path == "camera.motion"


@pytest.mark.asyncio
async def test_local_intent_requires_explicit_allowlist(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        resolver = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
        )
        with pytest.raises(LocalIntentNotAllowed):
            await resolver.resolve(
                _request(
                    local=(
                        LocalPolicyIntent(
                            path="camera.motion",
                            value="dolly",
                            source_ref=VersionRef(
                                logical_id=LogicalId("intent:shot"),
                                version_id=VersionId("v1"),
                            ),
                            reason="local request",
                        ),
                    )
                )
            )
    finally:
        await writer.close()


def test_imp012_output_does_not_define_active_profile_or_expose_pack_rules():
    assert not hasattr(profile_module, "ActiveProductionProfile")
    forbidden = {
        "brainpack_definitions",
        "pack_rules",
        "candidate_pack_refs",
        "profile_resolver",
    }
    from agent.studio.profile_resolver import ProfileResolutionResult

    assert set(ProfileResolutionResult.model_fields).isdisjoint(forbidden)


@pytest.mark.asyncio
async def test_resolution_provenance_binds_rejected_candidates_and_losing_sources(
    tmp_path,
):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        selected = _pack(
            "pack:selected",
            "v1",
            path="tone",
            value="pack",
            applicability=BrainPackApplicability(domains=("film",)),
        )
        rejected = _pack(
            "pack:rejected",
            "v1",
            path="camera.motion",
            value="handheld",
            applicability=BrainPackApplicability(domains=("documentary",)),
        )
        await _freeze(registry, selected)
        await _freeze(registry, rejected)

        local_ref = VersionRef(
            logical_id=LogicalId("intent:local"),
            version_id=VersionId("v1"),
        )
        resolver = ProfileResolver(
            registry=registry,
            resolver_version=RESOLVER_VERSION,
            local_intent_allowlist=frozenset({"tone"}),
        )
        result = await resolver.resolve(
            _request(
                packs=(selected.ref, rejected.ref),
                local=(
                    LocalPolicyIntent(
                        path="tone",
                        value="local",
                        source_ref=local_ref,
                        reason="losing lower-authority local intent",
                    ),
                ),
            )
        )
        provenance = build_resolution_provenance(
            result,
            actor_ref="studio:profile-resolver",
            reason="persist all consumed exact sources",
            recorded_at=NOW,
            source_refs=("evidence:resolution",),
        )

        consumed = {
            (item.source.logical_id.root, item.source.version_id.root)
            for item in provenance.source_versions
        }
        assert ("pack:selected", "v1") in consumed
        assert ("pack:rejected", "v1") in consumed
        assert ("intent:local", "v1") in consumed
        assert (
            result.trace.project_ref.logical_id.root,
            result.trace.project_ref.version_id.root,
        ) in consumed
        assert (
            result.trace.topic_ref.logical_id.root,
            result.trace.topic_ref.version_id.root,
        ) in consumed
        assert (
            result.trace.domain_ref.logical_id.root,
            result.trace.domain_ref.version_id.root,
        ) in consumed
    finally:
        await writer.close()
