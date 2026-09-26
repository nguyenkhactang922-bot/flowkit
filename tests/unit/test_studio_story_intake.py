"""IMP-020 tests for canonical Idea/Logline/Premise/Angle/Theme intake."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    AngleCandidate,
    GateVerdict,
    IdeaContract,
    LifecycleState,
    LoglineContract,
    LogicalId,
    PremiseCandidate,
    Provenance,
    SemanticRecordMetadata,
    SQLiteWriteOwner,
    StoryIntakeArtifact,
    StoryIntakeGateBlocked,
    StoryIntakeRepository,
    StoryIntakeStage,
    StoryIntakeValue,
    ThemeHypothesis,
    VersionId,
    VersionRef,
    VersionRepository,
    build_story_intake_provenance,
)


NOW = datetime(2026, 9, 26, 16, 0, tzinfo=timezone.utc)
PROJECT_ID = LogicalId("project:film")
PROJECT_REF = VersionRef(
    logical_id=LogicalId("project-input:film"),
    version_id=VersionId("v1"),
)
TOPIC_REF = VersionRef(
    logical_id=LogicalId("topic-resolution:film"),
    version_id=VersionId("v1"),
)
PROFILE_REF = VersionRef(
    logical_id=LogicalId("active-profile:project:film"),
    version_id=VersionId("p1"),
)


def _provenance(reason: str, *, rule_version: VersionRef | None = None) -> Provenance:
    return Provenance(
        source_refs=("evidence:imp020",),
        actor_ref="studio:test",
        reason=reason,
        recorded_at=NOW,
        rule_version=rule_version,
        correlation_id="run:imp020",
    )


def _metadata(ref: VersionRef, *, predecessor: VersionRef | None = None) -> SemanticRecordMetadata:
    return SemanticRecordMetadata(
        logical_id=ref.logical_id,
        version_id=ref.version_id,
        predecessor=predecessor,
        provenance=_provenance("seed exact source"),
        created_at=NOW,
    )


async def _seed_exact_sources(writer: SQLiteWriteOwner) -> VersionRepository:
    versions = VersionRepository(writer)
    await versions.create_initial(
        metadata=_metadata(PROJECT_REF),
        payload={"project": "film"},
        status=LifecycleState.LOCKED,
    )
    await versions.create_initial(
        metadata=_metadata(TOPIC_REF),
        payload={"topic": "return home"},
        status=LifecycleState.APPROVED,
    )
    await versions.create_initial(
        metadata=_metadata(PROFILE_REF),
        payload={"profile": "resolved"},
        status=LifecycleState.LOCKED,
    )
    return versions


def _idea(
    version: str = "v1",
    *,
    policy_compatible: bool = True,
    factuality_compatible: bool = True,
    profile_ref: VersionRef = PROFILE_REF,
) -> IdeaContract:
    return IdeaContract(
        project_id=PROJECT_ID,
        version_id=VersionId(version),
        active_profile_ref=profile_ref,
        project_ref=PROJECT_REF,
        topic_ref=TOPIC_REF,
        proposition="A man returns home to sell the family house.",
        intent="Explore grief through a concrete irreversible decision.",
        scope="One homecoming and the decision around the inherited house.",
        context="Contemporary family drama.",
        premise_potential="The sale forces buried family truth into action.",
        distinctness="A cassette left by his mother changes the practical decision.",
        policy_compatible=policy_compatible,
        factuality_compatible=factuality_compatible,
    )


def _logline(
    idea_ref: VersionRef,
    *,
    version: str = "v1",
    causal_chain_explicit: bool = True,
    locked_fact_conflict: bool = False,
    unsupported_factual_claim: bool = False,
) -> LoglineContract:
    return LoglineContract(
        project_id=PROJECT_ID,
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        idea_ref=idea_ref,
        text=(
            "Returning to sell his late mother's house, a guarded son finds her "
            "cassette and must choose between closing the sale and confronting "
            "the truth that could change his family."
        ),
        protagonist="A guarded adult son returning to his hometown.",
        drive="Sell the inherited house and leave quickly.",
        conflict="The cassette makes emotional closure incompatible with a clean sale.",
        stakes="He may lose both the house's meaning and his last chance to reconcile.",
        causal_chain_explicit=causal_chain_explicit,
        locked_fact_conflict=locked_fact_conflict,
        unsupported_factual_claim=unsupported_factual_claim,
    )


def _premise(
    idea_ref: VersionRef,
    logline_ref: VersionRef,
    *,
    version: str = "v1",
    causal_development_supported: bool = True,
    topic_restatement_only: bool = False,
) -> PremiseCandidate:
    return PremiseCandidate(
        project_id=PROJECT_ID,
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        idea_ref=idea_ref,
        logline_ref=logline_ref,
        statement=(
            "Trying to dispose of a painful inheritance forces a son to engage "
            "with the evidence of care he had chosen not to see."
        ),
        causal_engine=(
            "Each practical step toward the sale exposes another consequence of "
            "the mother's recorded message, making retreat progressively costlier."
        ),
        conflict_potential="External sale pressure collides with internal grief avoidance.",
        novelty="The emotional reveal is carried by a mundane inherited recording.",
        causal_development_supported=causal_development_supported,
        topic_restatement_only=topic_restatement_only,
    )


def _angle(
    premise_ref: VersionRef,
    *,
    version: str = "v1",
    factuality_compatible: bool = True,
    locked_fact_conflict: bool = False,
) -> AngleCandidate:
    return AngleCandidate(
        project_id=PROJECT_ID,
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        premise_ref=premise_ref,
        perspective="Treat the house sale as a sequence of irreversible practical choices.",
        differentiation="Grief is shown through logistics rather than explanatory monologues.",
        audience_promise="Every practical action reveals a deeper emotional cost.",
        factuality_compatible=factuality_compatible,
        locked_fact_conflict=locked_fact_conflict,
    )


def _theme(
    premise_ref: VersionRef,
    angle_ref: VersionRef,
    *,
    version: str = "v1",
    causal_truth_compatible: bool = True,
    didactic_repetition_risk: bool = False,
) -> ThemeHypothesis:
    return ThemeHypothesis(
        project_id=PROJECT_ID,
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        premise_ref=premise_ref,
        angle_ref=angle_ref,
        thematic_question="Can closure be honest if it requires erasing what still matters?",
        hypothesis="Letting go becomes meaningful only after the truth is faced.",
        integration_principle=(
            "Express theme through choices about objects, rooms, sale steps and the cassette."
        ),
        causal_truth_compatible=causal_truth_compatible,
        didactic_repetition_risk=didactic_repetition_risk,
    )


def _story_provenance(value: StoryIntakeValue, reason: str) -> Provenance:
    return build_story_intake_provenance(
        value,
        actor_ref="studio:story-intake",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp020",),
        correlation_id="run:imp020",
    )


@pytest.mark.asyncio
async def test_full_story_intake_chain_promotes_exact_current_versions(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_exact_sources(writer)
        repo = StoryIntakeRepository(writer)

        idea = _idea()
        idea_artifact = await repo.create_initial(
            value=idea,
            provenance=_story_provenance(idea, "create idea"),
            created_at=NOW,
        )
        idea_pointer = await repo.promote(ref=idea_artifact.ref, expected_revision=0)
        assert idea_pointer.status is LifecycleState.APPROVED

        logline = _logline(idea_artifact.ref)
        logline_artifact = await repo.create_initial(
            value=logline,
            provenance=_story_provenance(logline, "create logline"),
            created_at=NOW,
        )
        await repo.promote(ref=logline_artifact.ref, expected_revision=0)

        premise = _premise(idea_artifact.ref, logline_artifact.ref)
        premise_artifact = await repo.create_initial(
            value=premise,
            provenance=_story_provenance(premise, "create premise"),
            created_at=NOW,
        )
        await repo.promote(ref=premise_artifact.ref, expected_revision=0)

        angle = _angle(premise_artifact.ref)
        angle_artifact = await repo.create_initial(
            value=angle,
            provenance=_story_provenance(angle, "create angle"),
            created_at=NOW,
        )
        await repo.promote(ref=angle_artifact.ref, expected_revision=0)

        theme = _theme(premise_artifact.ref, angle_artifact.ref)
        theme_artifact = await repo.create_initial(
            value=theme,
            provenance=_story_provenance(theme, "create theme"),
            created_at=NOW,
        )
        await repo.promote(ref=theme_artifact.ref, expected_revision=0)

        assert (await repo.get_current(stage=StoryIntakeStage.IDEA, project_id=PROJECT_ID)).ref == idea_artifact.ref
        assert (await repo.get_current(stage=StoryIntakeStage.LOGLINE, project_id=PROJECT_ID)).ref == logline_artifact.ref
        assert (await repo.get_current(stage=StoryIntakeStage.PREMISE, project_id=PROJECT_ID)).ref == premise_artifact.ref
        assert (await repo.get_current(stage=StoryIntakeStage.ANGLE, project_id=PROJECT_ID)).ref == angle_artifact.ref
        assert (await repo.get_current(stage=StoryIntakeStage.THEME, project_id=PROJECT_ID)).ref == theme_artifact.ref
    finally:
        await writer.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("factory", "code"),
    [
        (lambda: _idea(policy_compatible=False), "IDEA_POLICY_CONFLICT"),
        (
            lambda: _logline(_idea().ref, causal_chain_explicit=False),
            "LOGLINE_CAUSALITY_MISSING",
        ),
        (
            lambda: _premise(_idea().ref, _logline(_idea().ref).ref, topic_restatement_only=True),
            "PREMISE_TOPIC_RESTATEMENT",
        ),
        (
            lambda: _angle(_premise(_idea().ref, _logline(_idea().ref).ref).ref, locked_fact_conflict=True),
            "ANGLE_LOCKED_FACT_CONFLICT",
        ),
        (
            lambda: _theme(
                _premise(_idea().ref, _logline(_idea().ref).ref).ref,
                _angle(_premise(_idea().ref, _logline(_idea().ref).ref).ref).ref,
                didactic_repetition_risk=True,
            ),
            "THEME_DIDACTIC_REPETITION",
        ),
    ],
)
async def test_stage_local_blocking_gates_fail_closed(factory, code, tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_exact_sources(writer)
        repo = StoryIntakeRepository(writer)
        value = factory()
        artifact = await repo.create_initial(
            value=value,
            provenance=_story_provenance(value, "create blocked candidate"),
            created_at=NOW,
        )
        gate = repo.gates.evaluate(value)
        assert gate.verdict is GateVerdict.FAIL
        assert code in {finding.code for finding in gate.findings}

        with pytest.raises(StoryIntakeGateBlocked, match=code):
            await repo.promote(ref=artifact.ref, expected_revision=0)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_parent_version_blocks_downstream_promotion(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_exact_sources(writer)
        repo = StoryIntakeRepository(writer)

        idea_v1 = _idea("v1")
        a1 = await repo.create_initial(
            value=idea_v1,
            provenance=_story_provenance(idea_v1, "idea v1"),
            created_at=NOW,
        )
        await repo.promote(ref=a1.ref, expected_revision=0)

        idea_v2 = _idea("v2")
        a2 = await repo.create_successor(
            value=idea_v2,
            predecessor=a1.ref,
            provenance=_story_provenance(idea_v2, "idea v2"),
            created_at=NOW,
        )
        await repo.promote(ref=a2.ref, expected_revision=1)

        stale_logline = _logline(a1.ref)
        logline_artifact = await repo.create_initial(
            value=stale_logline,
            provenance=_story_provenance(stale_logline, "stale logline"),
            created_at=NOW,
        )
        with pytest.raises(StoryIntakeGateBlocked, match="not exact current accepted"):
            await repo.promote(ref=logline_artifact.ref, expected_revision=0)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_active_profile_blocks_promotion(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_exact_sources(writer)
        repo = StoryIntakeRepository(writer)

        profile_v2 = VersionRef(
            logical_id=PROFILE_REF.logical_id,
            version_id=VersionId("p2"),
        )
        await versions.create_successor(
            metadata=_metadata(profile_v2, predecessor=PROFILE_REF),
            payload={"profile": "new resolved"},
            supersession_reason="profile changed",
        )
        await versions.update_current(
            logical_id=profile_v2.logical_id,
            version_id=profile_v2.version_id,
            status=LifecycleState.LOCKED,
            expected_revision=0,
        )

        idea = _idea(profile_ref=PROFILE_REF)
        artifact = await repo.create_initial(
            value=idea,
            provenance=_story_provenance(idea, "idea using stale profile"),
            created_at=NOW,
        )
        with pytest.raises(StoryIntakeGateBlocked, match="stale/unlocked"):
            await repo.promote(ref=artifact.ref, expected_revision=0)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_successor_preserves_old_bytes_until_new_version_is_promoted(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_exact_sources(writer)
        repo = StoryIntakeRepository(writer)

        v1 = _idea("v1")
        a1 = await repo.create_initial(
            value=v1,
            provenance=_story_provenance(v1, "idea v1"),
            created_at=NOW,
        )
        await repo.promote(ref=a1.ref, expected_revision=0)

        v2 = IdeaContract(
            **{
                **v1.model_dump(),
                "version_id": VersionId("v2"),
                "proposition": "A son returns to sell the house but the cassette changes his plan.",
            }
        )
        a2 = await repo.create_successor(
            value=v2,
            predecessor=a1.ref,
            provenance=_story_provenance(v2, "idea v2"),
            created_at=NOW,
        )

        assert (await repo.get(a1.ref)).value.proposition == v1.proposition
        assert (await repo.get_current(stage=StoryIntakeStage.IDEA, project_id=PROJECT_ID)).ref == a1.ref

        await repo.promote(ref=a2.ref, expected_revision=1)
        assert (await repo.get_current(stage=StoryIntakeStage.IDEA, project_id=PROJECT_ID)).ref == a2.ref
        assert (await repo.get(a1.ref)).value.proposition == v1.proposition
    finally:
        await writer.close()


def test_exact_project_identity_and_profile_binding_fail_closed():
    other_project = LogicalId("project:other")
    with pytest.raises(ValidationError, match="same project"):
        LoglineContract(
            project_id=PROJECT_ID,
            version_id=VersionId("v1"),
            active_profile_ref=PROFILE_REF,
            idea_ref=VersionRef(
                logical_id=LogicalId("story-idea:project:other"),
                version_id=VersionId("v1"),
            ),
            text="A complete but invalid cross-project logline.",
            protagonist="Person",
            drive="Act",
            conflict="Resistance",
            stakes="Loss",
        )

    with pytest.raises(ValidationError, match="ActiveProductionProfile"):
        IdeaContract(
            project_id=PROJECT_ID,
            version_id=VersionId("v1"),
            active_profile_ref=VersionRef(
                logical_id=LogicalId(f"active-profile:{other_project.root}"),
                version_id=VersionId("p1"),
            ),
            project_ref=PROJECT_REF,
            topic_ref=TOPIC_REF,
            proposition="Proposition",
            intent="Intent",
            scope="Scope",
            context="Context",
            premise_potential="Potential",
            distinctness="Distinct",
        )


def test_artifact_provenance_must_exactly_bind_inputs_and_profile_rule_version():
    idea = _idea()
    wrong = Provenance(
        source_versions=(),
        source_refs=("evidence:wrong",),
        actor_ref="studio:test",
        reason="wrong provenance",
        recorded_at=NOW,
        rule_version=PROFILE_REF,
    )
    with pytest.raises(ValidationError, match="exactly bind"):
        StoryIntakeArtifact(
            metadata=SemanticRecordMetadata(
                logical_id=idea.logical_id,
                version_id=idea.version_id,
                provenance=wrong,
                created_at=NOW,
            ),
            value=idea,
        )


@pytest.mark.asyncio
async def test_missing_story_current_returns_none_not_repository_exception(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo = StoryIntakeRepository(writer)
        assert (
            await repo.get_current(
                stage=StoryIntakeStage.THEME,
                project_id=PROJECT_ID,
            )
            is None
        )
    finally:
        await writer.close()


def test_canonical_story_intake_has_no_legacy_project_story_field():
    for model in (
        IdeaContract,
        LoglineContract,
        PremiseCandidate,
        AngleCandidate,
        ThemeHypothesis,
    ):
        assert "story" not in model.model_fields
        assert "project_story" not in model.model_fields
