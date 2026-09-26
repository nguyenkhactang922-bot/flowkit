"""IMP-010 tests for Project / Topic / Domain Resolution."""

from __future__ import annotations

import inspect
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    AmbiguityItem,
    AxisClassification,
    ClassificationAxis,
    ClassificationTraceItem,
    DomainClassifierOutput,
    DomainResolution,
    DomainResolutionArtifact,
    DomainResolutionService,
    HardConstraintViolation,
    LifecycleState,
    LogicalId,
    ProjectBootstrapArtifact,
    ProjectBootstrapInput,
    ProjectConstraint,
    ProjectTopicDomainRepository,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    SQLiteWriteOwner,
    TopicClassifierOutput,
    TopicResolution,
    TopicResolutionArtifact,
    TopicResolutionService,
    UnsupportedFactualityClass,
    VersionId,
    VersionRef,
    WeightedLabel,
)

NOW = datetime(2026, 9, 26, 2, 30, tzinfo=timezone.utc)
PROJECT_ID = LogicalId("project:alpha")
NORMALIZER = VersionRef(
    logical_id=LogicalId("rule:topic-normalizer"),
    version_id=VersionId("v1"),
)
TOPIC_CLASSIFIER = VersionRef(
    logical_id=LogicalId("rule:topic-classifier"),
    version_id=VersionId("v2"),
)
DOMAIN_CLASSIFIER = VersionRef(
    logical_id=LogicalId("rule:domain-classifier"),
    version_id=VersionId("v3"),
)
REGISTRY_METADATA = VersionRef(
    logical_id=LogicalId("registry-metadata:bootstrap"),
    version_id=VersionId("v1"),
)
SUPPORTED_FACTUALITY = frozenset({"factual", "fiction", "mixed"})


def _label(
    label: str,
    weight: float,
    reason: str = "classifier evidence",
) -> WeightedLabel:
    return WeightedLabel(
        label=label,
        weight=weight,
        reason=reason,
        evidence_refs=(f"evidence:{label.lower().replace(' ', '-')}",),
    )


def _bootstrap(
    *,
    factuality_mode: str = "factual",
    constraints: tuple[ProjectConstraint, ...] = (),
) -> ProjectBootstrapInput:
    return ProjectBootstrapInput(
        project_id=PROJECT_ID,
        raw_topic="  How   coffee\tworks  ",
        project_goals=("explain clearly",),
        language="en",
        locale="en-US",
        target_duration_seconds=600,
        platform_hints=("YouTube",),
        format_hints=("long-form",),
        audience_hints=("general audience",),
        factuality_mode=factuality_mode,
        constraints=constraints,
        source_evidence_refs=("user-input:project-alpha",),
    )


def _topic_output(
    *,
    ambiguous: bool = True,
    derived_constraints: tuple[ProjectConstraint, ...] = (),
) -> TopicClassifierOutput:
    ambiguity = (
        (
            AmbiguityItem(
                axis="topic",
                candidates=(
                    _label("coffee science", 0.62),
                    _label("food education", 0.58),
                ),
                reason="topic spans science and food education",
            ),
        )
        if ambiguous
        else ()
    )
    return TopicClassifierOutput(
        weighted_labels=(
            _label("coffee science", 0.62),
            _label("food education", 0.58),
        ),
        ambiguity_detected=ambiguous,
        ambiguity_set=ambiguity,
        derived_constraints=derived_constraints,
        evidence_refs=("evidence:topic-classifier-run",),
    )


def _topic_service() -> TopicResolutionService:
    return TopicResolutionService(
        normalizer_rule_version=NORMALIZER,
        classifier_rule_version=TOPIC_CLASSIFIER,
        supported_factuality_modes=SUPPORTED_FACTUALITY,
    )


def _bootstrap_artifact(
    *,
    constraints: tuple[ProjectConstraint, ...] = (),
    factuality_mode: str = "factual",
) -> ProjectBootstrapArtifact:
    return _topic_service().build_bootstrap_artifact(
        value=_bootstrap(
            constraints=constraints,
            factuality_mode=factuality_mode,
        ),
        version_id=VersionId("v1"),
        actor_ref="studio:project-intake",
        reason="accept project bootstrap input",
        created_at=NOW,
        correlation_id="corr:imp010",
    )


def _topic_artifact(
    *,
    constraints: tuple[ProjectConstraint, ...] = (),
    ambiguous: bool = True,
) -> TopicResolutionArtifact:
    service = _topic_service()
    bootstrap = service.build_bootstrap_artifact(
        value=_bootstrap(constraints=constraints),
        version_id=VersionId("v1"),
        actor_ref="studio:project-intake",
        reason="accept project bootstrap input",
        created_at=NOW,
        correlation_id="corr:imp010",
    )
    return service.resolve(
        project_input=bootstrap,
        version_id=VersionId("v1"),
        classification=_topic_output(ambiguous=ambiguous),
        actor_ref="studio:topic-intelligence",
        reason="resolve normalized topic",
        created_at=NOW,
        correlation_id="corr:imp010",
    )


def _axis(
    axis: ClassificationAxis,
    *labels: str,
    unknown: bool = False,
) -> AxisClassification:
    return AxisClassification(
        axis=axis,
        labels=tuple(
            _label(label, max(0.1, 0.9 - index * 0.1))
            for index, label in enumerate(labels)
        ),
        unknown=unknown,
    )


def _domain_output(
    *,
    platform: str = "YouTube",
    niches: tuple[str, ...] = ("coffee education",),
    unknown_niche: bool = False,
    ambiguous: bool = False,
) -> DomainClassifierOutput:
    classifications = (
        _axis(ClassificationAxis.DOMAIN, "education"),
        _axis(
            ClassificationAxis.NICHE,
            *niches,
            unknown=unknown_niche,
        ),
        _axis(ClassificationAxis.GENRE, "explainer"),
        _axis(ClassificationAxis.AUDIENCE, "general audience"),
        _axis(ClassificationAxis.FORMAT, "long-form"),
        _axis(ClassificationAxis.PLATFORM, platform),
        _axis(ClassificationAxis.FACTUALITY, "factual"),
    )
    ambiguity_trace = (
        (
            AmbiguityItem(
                axis="niche",
                candidates=(
                    _label("coffee education", 0.61),
                    _label("food science", 0.59),
                ),
                reason="hybrid niche boundary remains unresolved",
            ),
        )
        if ambiguous
        else ()
    )
    return DomainClassifierOutput(
        classifications=classifications,
        ambiguity_detected=ambiguous,
        ambiguity_trace=ambiguity_trace,
        classification_trace=(
            ClassificationTraceItem(
                axis=ClassificationAxis.DOMAIN,
                decision="education",
                reason="topic intent is explanatory",
                evidence_refs=("evidence:domain-trace",),
            ),
        ),
        evidence_refs=("evidence:domain-classifier-run",),
    )


def _domain_service() -> DomainResolutionService:
    return DomainResolutionService(
        classifier_rule_version=DOMAIN_CLASSIFIER,
        supported_factuality_modes=SUPPORTED_FACTUALITY,
    )


def test_topic_contract_cannot_represent_profile_dependency_or_provider_state():
    signature = inspect.signature(TopicResolutionService.resolve)
    assert "active_production_profile" not in signature.parameters
    assert "profile_resolver" not in signature.parameters

    forbidden = {
        "provider",
        "provider_id",
        "model",
        "model_id",
        "flow_project_id",
        "tool_name",
        "user_paygate_tier",
        "active_production_profile",
        "profile_resolver",
    }
    for model in (ProjectBootstrapInput, TopicResolution, DomainResolution):
        assert set(model.model_fields).isdisjoint(forbidden)

    with pytest.raises(ValidationError):
        ProjectBootstrapInput(
            **_bootstrap().model_dump(mode="python"),
            flow_project_id="legacy-flow-id",
        )


def test_topic_resolution_normalizes_multi_label_and_explicit_ambiguity():
    bootstrap = _bootstrap_artifact()
    topic = _topic_service().resolve(
        project_input=bootstrap,
        version_id=VersionId("v1"),
        classification=_topic_output(ambiguous=True),
        actor_ref="studio:topic-intelligence",
        reason="resolve normalized topic",
        created_at=NOW,
        correlation_id="corr:imp010",
    )

    assert topic.value.normalized_topic == "How coffee works"
    assert [item.label for item in topic.value.weighted_topic_labels] == [
        "coffee science",
        "food education",
    ]
    assert len(topic.value.ambiguity_set) == 1
    assert "niche" not in TopicResolution.model_fields

    bindings = {
        item.role: item.source
        for item in topic.metadata.provenance.source_versions
    }
    assert bindings == {
        "project_input": bootstrap.ref,
        "topic_normalizer_rule": NORMALIZER,
        "topic_classifier_rule": TOPIC_CLASSIFIER,
    }
    assert topic.metadata.provenance.rule_version == TOPIC_CLASSIFIER


def test_detected_ambiguity_cannot_be_silently_omitted():
    with pytest.raises(ValidationError, match="ambiguity"):
        TopicClassifierOutput(
            weighted_labels=(_label("coffee science", 0.7),),
            ambiguity_detected=True,
            ambiguity_set=(),
        )

    with pytest.raises(ValidationError, match="ambiguity"):
        DomainClassifierOutput(
            classifications=_domain_output().classifications,
            ambiguity_detected=True,
            ambiguity_trace=(),
        )


def test_unsupported_factuality_class_is_rejected_before_topic_acceptance():
    bootstrap = _bootstrap_artifact(factuality_mode="unsupported-class")
    with pytest.raises(UnsupportedFactualityClass):
        _topic_service().resolve(
            project_input=bootstrap,
            version_id=VersionId("v1"),
            classification=_topic_output(),
            actor_ref="studio:topic-intelligence",
            reason="resolve normalized topic",
            created_at=NOW,
        )


def test_hard_project_constraint_blocks_topic_derived_override():
    locked = ProjectConstraint(
        key="platform",
        value="YouTube",
        hard=True,
        reason="project lock",
    )
    bootstrap = _bootstrap_artifact(constraints=(locked,))
    classifier = _topic_output(
        derived_constraints=(
            ProjectConstraint(
                key="platform",
                value="TikTok",
                hard=False,
                reason="soft classifier preference",
            ),
        )
    )

    with pytest.raises(HardConstraintViolation, match="locked project value"):
        _topic_service().resolve(
            project_input=bootstrap,
            version_id=VersionId("v1"),
            classification=classifier,
            actor_ref="studio:topic-intelligence",
            reason="resolve normalized topic",
            created_at=NOW,
        )


def test_domain_resolution_enforces_hard_axis_constraints():
    locked = ProjectConstraint(
        key="platform",
        value="YouTube",
        hard=True,
        reason="project lock",
    )
    topic = _topic_artifact(constraints=(locked,))

    with pytest.raises(HardConstraintViolation, match="platform"):
        _domain_service().resolve(
            topic=topic,
            registry_metadata_ref=REGISTRY_METADATA,
            version_id=VersionId("v1"),
            classification=_domain_output(platform="TikTok"),
            actor_ref="studio:domain-resolver",
            reason="resolve domain context",
            created_at=NOW,
        )

    resolved = _domain_service().resolve(
        topic=topic,
        registry_metadata_ref=REGISTRY_METADATA,
        version_id=VersionId("v1"),
        classification=_domain_output(platform="YouTube"),
        actor_ref="studio:domain-resolver",
        reason="resolve domain context",
        created_at=NOW,
    )
    assert [
        item.label
        for item in resolved.value.axis(ClassificationAxis.PLATFORM).labels
    ] == ["YouTube"]


def test_unknown_niche_is_explicit_and_hybrid_niche_is_not_collapsed():
    with pytest.raises(ValidationError, match="explicitly unknown"):
        AxisClassification(
            axis=ClassificationAxis.NICHE,
            labels=(),
            unknown=False,
        )

    unknown = _domain_service().resolve(
        topic=_topic_artifact(ambiguous=False),
        registry_metadata_ref=REGISTRY_METADATA,
        version_id=VersionId("v1"),
        classification=_domain_output(
            niches=(),
            unknown_niche=True,
        ),
        actor_ref="studio:domain-resolver",
        reason="resolve unknown niche",
        created_at=NOW,
    )
    niche_axis = unknown.value.axis(ClassificationAxis.NICHE)
    assert niche_axis.unknown is True
    assert niche_axis.labels == ()

    hybrid = _domain_service().resolve(
        topic=_topic_artifact(ambiguous=False),
        registry_metadata_ref=REGISTRY_METADATA,
        version_id=VersionId("v1"),
        classification=_domain_output(
            niches=("coffee education", "food science"),
        ),
        actor_ref="studio:domain-resolver",
        reason="resolve hybrid niche",
        created_at=NOW,
    )
    assert [item.label for item in hybrid.value.axis(ClassificationAxis.NICHE).labels] == [
        "coffee education",
        "food science",
    ]


def test_domain_resolution_binds_exact_topic_registry_and_rule_versions():
    topic = _topic_artifact(ambiguous=False)
    domain = _domain_service().resolve(
        topic=topic,
        registry_metadata_ref=REGISTRY_METADATA,
        version_id=VersionId("v1"),
        classification=_domain_output(),
        actor_ref="studio:domain-resolver",
        reason="resolve domain context",
        created_at=NOW,
        correlation_id="corr:imp010",
    )

    bindings = {
        item.role: item.source
        for item in domain.metadata.provenance.source_versions
    }
    assert bindings == {
        "topic_resolution": topic.ref,
        "registry_metadata": REGISTRY_METADATA,
        "domain_classifier_rule": DOMAIN_CLASSIFIER,
    }
    assert domain.value.topic_resolution_ref == topic.ref
    assert domain.value.registry_metadata_ref == REGISTRY_METADATA
    assert "effective_pack_stack" not in DomainResolution.model_fields
    assert "active_production_profile" not in DomainResolution.model_fields


def test_cross_project_topic_provenance_is_rejected():
    topic = _topic_artifact(ambiguous=False)
    wrong = topic.metadata.provenance.model_copy(
        update={
            "source_versions": (
                SourceVersionBinding(
                    role="project_input",
                    source=VersionRef(
                        logical_id=LogicalId("project-input:project:other"),
                        version_id=VersionId("v1"),
                    ),
                ),
                SourceVersionBinding(
                    role="topic_normalizer_rule",
                    source=NORMALIZER,
                ),
                SourceVersionBinding(
                    role="topic_classifier_rule",
                    source=TOPIC_CLASSIFIER,
                ),
            )
        }
    )
    bad_metadata = topic.metadata.model_copy(update={"provenance": wrong})

    with pytest.raises(ValidationError, match="another project"):
        TopicResolutionArtifact(
            metadata=bad_metadata,
            value=topic.value,
        )


@pytest.mark.asyncio
async def test_project_topic_domain_round_trip_through_version_repository(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    repo = ProjectTopicDomainRepository(writer)

    try:
        bootstrap = _bootstrap_artifact(
            constraints=(
                ProjectConstraint(
                    key="platform",
                    value="YouTube",
                    hard=True,
                    reason="project lock",
                ),
            )
        )
        topic = _topic_service().resolve(
            project_input=bootstrap,
            version_id=VersionId("v1"),
            classification=_topic_output(ambiguous=False),
            actor_ref="studio:topic-intelligence",
            reason="resolve normalized topic",
            created_at=NOW,
            correlation_id="corr:imp010",
        )
        domain = _domain_service().resolve(
            topic=topic,
            registry_metadata_ref=REGISTRY_METADATA,
            version_id=VersionId("v1"),
            classification=_domain_output(platform="YouTube"),
            actor_ref="studio:domain-resolver",
            reason="resolve domain context",
            created_at=NOW,
            correlation_id="corr:imp010",
        )

        await repo.save_project_input(
            bootstrap,
            status=LifecycleState.APPROVED,
        )
        await repo.save_topic(topic, status=LifecycleState.REVIEW)
        await repo.save_domain(domain, status=LifecycleState.REVIEW)

        loaded_bootstrap = await repo.get_project_input(bootstrap.ref)
        loaded_topic = await repo.get_topic(topic.ref)
        loaded_domain = await repo.get_domain(domain.ref)

        assert loaded_bootstrap is not None
        assert loaded_bootstrap.value == bootstrap.value
        assert loaded_bootstrap.metadata.provenance == bootstrap.metadata.provenance

        assert loaded_topic is not None
        assert loaded_topic.value == topic.value
        assert loaded_topic.metadata.provenance == topic.metadata.provenance

        assert loaded_domain is not None
        assert loaded_domain.value == domain.value
        assert loaded_domain.metadata.provenance == domain.metadata.provenance

        project_pointer = await repo.versions.get_current(
            bootstrap.metadata.logical_id
        )
        topic_pointer = await repo.versions.get_current(topic.metadata.logical_id)
        domain_pointer = await repo.versions.get_current(domain.metadata.logical_id)

        assert project_pointer is not None
        assert project_pointer.status is LifecycleState.APPROVED
        assert topic_pointer is not None
        assert topic_pointer.status is LifecycleState.REVIEW
        assert domain_pointer is not None
        assert domain_pointer.status is LifecycleState.REVIEW
    finally:
        await writer.close()


def test_domain_classifier_requires_every_canonical_axis_once():
    incomplete = tuple(
        item
        for item in _domain_output().classifications
        if item.axis is not ClassificationAxis.GENRE
    )
    with pytest.raises(ValidationError, match="each canonical classification axis"):
        DomainClassifierOutput(classifications=incomplete)


def test_project_bootstrap_requires_source_evidence_for_provenance():
    with pytest.raises(ValidationError, match="source evidence"):
        ProjectBootstrapInput(
            project_id=PROJECT_ID,
            raw_topic="coffee",
            language="en",
            factuality_mode="factual",
            source_evidence_refs=(),
        )
