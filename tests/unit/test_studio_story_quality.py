"""IMP-027 tests for independent critique, repair, quality gate and ScriptLock."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    CritiqueFinding,
    CritiqueKind,
    FindingDisposition,
    FindingSeverity,
    GateVerdict,
    LifecycleState,
    LogicalId,
    QualityGateCheck,
    QualityHardGate,
    RepairMode,
    ResponsibleLayer,
    RootCauseLocalization,
    ScriptApprovalPolicy,
    ScriptLockManifest,
    SQLiteWriteOwner,
    StoryQualityGateBlocked,
    StoryQualityIdentityError,
    StoryQualityRepository,
    StoryQualityResult,
    StoryRepairPlan,
    VersionId,
    VersionRef,
    build_story_quality_provenance,
    locked_refs_digest,
)
from tests.unit.test_studio_screenplay_realization import (
    BEAT_1_REF,
    PROFILE_REF,
    SCENE_REF,
    _metadata,
    _ready_pipeline,
    _seed,
)
from tests.unit.test_studio_structure_planning import (
    STORY_CORE_REF,
    _frozen_story_core,
)


NOW = datetime(2026, 9, 30, 10, 45, tzinfo=timezone.utc)


def _provenance(value, reason: str):
    return build_story_quality_provenance(
        value,
        actor_ref="studio:imp027",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp027",),
        correlation_id="run:imp027",
    )


def _hard_gates(
    *,
    causality: GateVerdict = GateVerdict.PASS,
) -> tuple[QualityGateCheck, ...]:
    return (
        QualityGateCheck(
            gate=QualityHardGate.FACTUAL_CONTRADICTION,
            verdict=GateVerdict.PASS,
        ),
        QualityGateCheck(
            gate=QualityHardGate.CAUSALITY_BREAK,
            verdict=causality,
        ),
        QualityGateCheck(
            gate=QualityHardGate.IDENTITY_STATE_CONTRADICTION,
            verdict=GateVerdict.PASS,
        ),
        QualityGateCheck(
            gate=QualityHardGate.MISSING_CRITICAL_PAYOFF,
            verdict=GateVerdict.PASS,
        ),
    )


async def _seed_story_core(versions) -> None:
    await _seed(
        versions,
        STORY_CORE_REF,
        status=LifecycleState.LOCKED,
        payload=_frozen_story_core().model_dump(mode="json"),
    )


async def _upstream(writer: SQLiteWriteOwner):
    (
        versions,
        _screenplay_repo,
        _dialogue,
        setup,
        screenplay_scene,
        screenplay,
    ) = await _ready_pipeline(writer)
    await _seed_story_core(versions)
    return versions, setup, screenplay_scene, screenplay


def _finding(
    screenplay_ref: VersionRef,
    scene_ref: VersionRef,
    version: str = "finding-v1",
    *,
    finding_key: str = "causality-001",
    kind: CritiqueKind = CritiqueKind.CAUSALITY_BREAK,
    severity: FindingSeverity = FindingSeverity.BLOCKER,
    disposition: FindingDisposition = FindingDisposition.OPEN,
    resolution_ref: VersionRef | None = None,
    critic_role: str = "independent-causality-critic",
    generator_role: str = "screenplay-generator",
) -> CritiqueFinding:
    return CritiqueFinding(
        project_id=LogicalId("project:film"),
        finding_key=finding_key,
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        story_core_ref=STORY_CORE_REF,
        full_screenplay_ref=screenplay_ref,
        location_ref=screenplay_ref,
        evidence_refs=(scene_ref,),
        critic_role=critic_role,
        generator_role=generator_role,
        kind=kind,
        severity=severity,
        disposition=disposition,
        summary="The screenplay conclusion skips the causal decision that earns the payoff.",
        rationale="The accepted screenplay scene is evidence of the visible causal gap.",
        resolution_ref=resolution_ref,
    )


def _root(
    finding_ref: VersionRef,
    visible_ref: VersionRef,
    responsible_ref: VersionRef,
    preserve_ref: VersionRef,
    version: str = "root-v1",
) -> RootCauseLocalization:
    return RootCauseLocalization(
        project_id=LogicalId("project:film"),
        finding_key="causality-001",
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        finding_ref=finding_ref,
        visible_location_ref=visible_ref,
        responsible_artifact_ref=responsible_ref,
        responsible_layer=ResponsibleLayer.SCREENPLAY_SCENE,
        preserve_refs=(preserve_ref,),
        invalidation_scope_candidate_refs=(visible_ref,),
        diagnosis=(
            "The visible full-screenplay gap originates in the exact screenplay-scene "
            "realization; the accepted setup/payoff link is preserved."
        ),
    )


def _repair(
    root_ref: VersionRef,
    responsible_ref: VersionRef,
    preserve_ref: VersionRef,
    version: str = "repair-v1",
) -> StoryRepairPlan:
    return StoryRepairPlan(
        project_id=LogicalId("project:film"),
        repair_key="causality-repair-001",
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        root_cause_ref=root_ref,
        mode=RepairMode.LINE_EXCHANGE,
        target_refs=(responsible_ref,),
        preserve_refs=(preserve_ref,),
        regression_obligations=(
            "Preserve the accepted cassette setup/payoff linkage.",
            "Preserve the canonical Scene and StoryCore identities.",
        ),
        expected_resolution=(
            "Restore the missing causal decision without changing preserved story truth."
        ),
    )


def _quality(
    screenplay_ref: VersionRef,
    finding_ref: VersionRef,
    repair_ref: VersionRef | None,
    version: str = "quality-v1",
    *,
    verdict: GateVerdict = GateVerdict.PASS,
    aggregate_score: float | None = 98.0,
    causality_gate: GateVerdict = GateVerdict.PASS,
) -> StoryQualityResult:
    return StoryQualityResult(
        project_id=LogicalId("project:film"),
        quality_key="main",
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        story_core_ref=STORY_CORE_REF,
        full_screenplay_ref=screenplay_ref,
        finding_refs=(finding_ref,),
        repair_plan_refs=() if repair_ref is None else (repair_ref,),
        hard_gate_checks=_hard_gates(causality=causality_gate),
        aggregate_score=aggregate_score,
        verdict=verdict,
    )


def _lock(
    screenplay_ref: VersionRef,
    quality_ref: VersionRef,
    version: str = "script-lock-v1",
    *,
    approval_policy: ScriptApprovalPolicy = ScriptApprovalPolicy.AUTOMATED_PASS_ALLOWED,
    approval_ref: VersionRef | None = None,
) -> ScriptLockManifest:
    locked_refs = (STORY_CORE_REF, screenplay_ref)
    return ScriptLockManifest(
        project_id=LogicalId("project:film"),
        version_id=VersionId(version),
        active_profile_ref=PROFILE_REF,
        story_core_ref=STORY_CORE_REF,
        full_screenplay_ref=screenplay_ref,
        quality_result_ref=quality_ref,
        approval_policy=approval_policy,
        approval_ref=approval_ref,
        locked_refs=locked_refs,
        locked_versions_digest=locked_refs_digest(locked_refs),
    )


async def _resolved_pipeline(writer: SQLiteWriteOwner):
    versions, setup, screenplay_scene, screenplay = await _upstream(writer)
    repo = StoryQualityRepository(writer)

    finding_v1 = _finding(screenplay.ref, screenplay_scene.ref)
    finding_a1 = await repo.create_critique_finding(
        value=finding_v1,
        provenance=_provenance(finding_v1, "independent critique"),
        created_at=NOW,
    )

    root = _root(
        finding_a1.ref,
        screenplay.ref,
        screenplay_scene.ref,
        setup.ref,
    )
    root_a = await repo.create_root_cause(
        value=root,
        provenance=_provenance(root, "localize earliest responsible layer"),
        created_at=NOW,
    )

    repair = _repair(root_a.ref, screenplay_scene.ref, setup.ref)
    repair_a = await repo.create_repair_plan(
        value=repair,
        provenance=_provenance(repair, "targeted repair plan"),
        created_at=NOW,
    )

    finding_v2 = _finding(
        screenplay.ref,
        screenplay_scene.ref,
        version="finding-v2",
        disposition=FindingDisposition.RESOLVED,
        resolution_ref=repair_a.ref,
    )
    finding_a2, _ = await repo.revise_critique_finding(
        value=finding_v2,
        predecessor=finding_a1.ref,
        provenance=_provenance(finding_v2, "resolve finding via repair plan"),
        created_at=NOW,
        expected_revision=1,
    )

    quality = _quality(screenplay.ref, finding_a2.ref, repair_a.ref)
    quality_a = await repo.create_quality_result(
        value=quality,
        provenance=_provenance(quality, "story quality pass"),
        created_at=NOW,
    )

    return (
        versions,
        repo,
        setup,
        screenplay_scene,
        screenplay,
        finding_a1,
        finding_a2,
        root_a,
        repair_a,
        quality_a,
    )


@pytest.mark.asyncio
async def test_resolved_blocker_can_pass_quality_and_create_exact_script_lock(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        (
            _versions,
            repo,
            _setup,
            _scene,
            screenplay,
            _finding_v1,
            _finding_v2,
            _root,
            _repair,
            quality,
        ) = await _resolved_pipeline(writer)

        lock = _lock(screenplay.ref, quality.ref)
        lock_a = await repo.create_script_lock(
            value=lock,
            provenance=_provenance(lock, "explicit script lock"),
            created_at=NOW,
        )

        current = await repo.versions.get_current(lock_a.ref.logical_id)
        assert current.version_id == lock_a.ref.version_id
        assert current.status is LifecycleState.LOCKED

        ancestors = {
            (item.object_id.root, item.version_id.root)
            for item in await repo.trace_ancestors(lock_a.ref)
        }
        assert (quality.ref.logical_id.root, quality.ref.version_id.root) in ancestors
        assert (screenplay.ref.logical_id.root, screenplay.ref.version_id.root) in ancestors
        assert (STORY_CORE_REF.logical_id.root, STORY_CORE_REF.version_id.root) in ancestors
    finally:
        await writer.close()


def test_critic_role_isolation_and_subjective_disagreement_not_blocker():
    screenplay_ref = VersionRef(
        logical_id=LogicalId("screenplay:project:film:main"),
        version_id=VersionId("screenplay-v1"),
    )
    scene_ref = VersionRef(
        logical_id=LogicalId("screenplay-scene:project:film:scene-1"),
        version_id=VersionId("screenplay-scene-v1"),
    )
    with pytest.raises(ValidationError, match="isolated"):
        _finding(
            screenplay_ref,
            scene_ref,
            critic_role="same-role",
            generator_role="same-role",
        )

    with pytest.raises(ValidationError, match="subjective disagreement"):
        _finding(
            screenplay_ref,
            scene_ref,
            kind=CritiqueKind.SUBJECTIVE_DISAGREEMENT,
            severity=FindingSeverity.BLOCKER,
        )


@pytest.mark.asyncio
async def test_open_blocker_cannot_be_averaged_away_by_high_score(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _versions, _setup, screenplay_scene, screenplay = await _upstream(writer)
        repo = StoryQualityRepository(writer)
        finding = _finding(screenplay.ref, screenplay_scene.ref)
        finding_a = await repo.create_critique_finding(
            value=finding,
            provenance=_provenance(finding, "blocking critique"),
            created_at=NOW,
        )

        quality = _quality(
            screenplay.ref,
            finding_a.ref,
            None,
            verdict=GateVerdict.PASS,
            aggregate_score=99.9,
        )
        with pytest.raises(
            StoryQualityGateBlocked,
            match="unresolved BLOCKER finding forces",
        ):
            await repo.create_quality_result(
                value=quality,
                provenance=_provenance(quality, "false pass attempt"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_root_cause_must_be_visible_source_or_exact_ancestor(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions, setup, screenplay_scene, screenplay = await _upstream(writer)
        repo = StoryQualityRepository(writer)
        finding = _finding(screenplay.ref, screenplay_scene.ref)
        finding_a = await repo.create_critique_finding(
            value=finding,
            provenance=_provenance(finding, "critique"),
            created_at=NOW,
        )

        unrelated = VersionRef(
            logical_id=LogicalId("screenplay-scene:project:film:unrelated"),
            version_id=VersionId("unrelated-v1"),
        )
        await _seed(
            versions,
            unrelated,
            status=LifecycleState.APPROVED,
            payload={"unrelated": True},
        )
        root = _root(finding_a.ref, screenplay.ref, unrelated, setup.ref)
        with pytest.raises(
            StoryQualityGateBlocked,
            match="responsible artifact must be visible defect source or exact ancestor",
        ):
            await repo.create_root_cause(
                value=root,
                provenance=_provenance(root, "bad root cause"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_repair_plan_cannot_drop_diagnosed_preserve_set(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _versions, setup, screenplay_scene, screenplay = await _upstream(writer)
        repo = StoryQualityRepository(writer)
        finding = _finding(screenplay.ref, screenplay_scene.ref)
        finding_a = await repo.create_critique_finding(
            value=finding,
            provenance=_provenance(finding, "critique"),
            created_at=NOW,
        )
        root = _root(
            finding_a.ref,
            screenplay.ref,
            screenplay_scene.ref,
            setup.ref,
        )
        root_a = await repo.create_root_cause(
            value=root,
            provenance=_provenance(root, "root cause"),
            created_at=NOW,
        )
        repair = _repair(root_a.ref, screenplay_scene.ref, setup.ref).model_copy(
            update={"preserve_refs": ()}
        )
        with pytest.raises(
            StoryQualityGateBlocked,
            match="exact diagnosed preserve set",
        ):
            await repo.create_repair_plan(
                value=repair,
                provenance=_provenance(repair, "drop preserve set"),
                created_at=NOW,
            )
    finally:
        await writer.close()


def test_hard_gate_fail_forces_quality_fail_even_with_high_score():
    screenplay_ref = VersionRef(
        logical_id=LogicalId("screenplay:project:film:main"),
        version_id=VersionId("screenplay-v1"),
    )
    finding_ref = VersionRef(
        logical_id=LogicalId("critique-finding:project:film:causality-001"),
        version_id=VersionId("finding-v1"),
    )
    with pytest.raises(ValidationError, match="hard-gate FAIL forces"):
        _quality(
            screenplay_ref,
            finding_ref,
            None,
            verdict=GateVerdict.PASS,
            aggregate_score=100.0,
            causality_gate=GateVerdict.FAIL,
        )


@pytest.mark.asyncio
async def test_script_lock_rejects_non_pass_quality(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _versions, _setup, screenplay_scene, screenplay = await _upstream(writer)
        repo = StoryQualityRepository(writer)
        finding = _finding(screenplay.ref, screenplay_scene.ref)
        finding_a = await repo.create_critique_finding(
            value=finding,
            provenance=_provenance(finding, "blocking critique"),
            created_at=NOW,
        )
        quality = _quality(
            screenplay.ref,
            finding_a.ref,
            None,
            verdict=GateVerdict.FAIL,
            causality_gate=GateVerdict.FAIL,
        )
        quality_a = await repo.create_quality_result(
            value=quality,
            provenance=_provenance(quality, "quality fail"),
            created_at=NOW,
        )
        lock = _lock(screenplay.ref, quality_a.ref)
        with pytest.raises(
            StoryQualityGateBlocked,
            match="requires StoryQualityResult PASS",
        ):
            await repo.create_script_lock(
                value=lock,
                provenance=_provenance(lock, "illegal lock"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_quality_revision_invalidates_existing_script_lock(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        (
            _versions,
            repo,
            _setup,
            _scene,
            screenplay,
            _finding_v1,
            finding_v2,
            _root,
            repair,
            quality_v1,
        ) = await _resolved_pipeline(writer)

        lock = _lock(screenplay.ref, quality_v1.ref)
        lock_a = await repo.create_script_lock(
            value=lock,
            provenance=_provenance(lock, "script lock"),
            created_at=NOW,
        )

        quality_v2 = _quality(
            screenplay.ref,
            finding_v2.ref,
            repair.ref,
            version="quality-v2",
            verdict=GateVerdict.PASS,
            aggregate_score=99.0,
        )
        quality_a2, invalidations = await repo.revise_quality_result(
            value=quality_v2,
            predecessor=quality_v1.ref,
            provenance=_provenance(quality_v2, "quality evidence successor"),
            created_at=NOW,
            expected_revision=1,
        )
        assert quality_a2.ref.version_id == VersionId("quality-v2")
        affected = {
            (item.affected_object_id.root, item.affected_object_version.root)
            for item in invalidations
        }
        assert (
            lock_a.ref.logical_id.root,
            lock_a.ref.version_id.root,
        ) in affected
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_revision_rejects_historical_noncurrent_predecessor(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _versions, _setup, screenplay_scene, screenplay = await _upstream(writer)
        repo = StoryQualityRepository(writer)
        finding_v1 = _finding(
            screenplay.ref,
            screenplay_scene.ref,
            kind=CritiqueKind.STRUCTURAL_WEAKNESS,
            severity=FindingSeverity.MAJOR,
        )
        a1 = await repo.create_critique_finding(
            value=finding_v1,
            provenance=_provenance(finding_v1, "v1"),
            created_at=NOW,
        )
        finding_v2 = _finding(
            screenplay.ref,
            screenplay_scene.ref,
            version="finding-v2",
            kind=CritiqueKind.STRUCTURAL_WEAKNESS,
            severity=FindingSeverity.MAJOR,
        )
        await repo.revise_critique_finding(
            value=finding_v2,
            predecessor=a1.ref,
            provenance=_provenance(finding_v2, "v2"),
            created_at=NOW,
            expected_revision=1,
        )
        finding_v3 = _finding(
            screenplay.ref,
            screenplay_scene.ref,
            version="finding-v3",
            kind=CritiqueKind.STRUCTURAL_WEAKNESS,
            severity=FindingSeverity.MAJOR,
        )
        with pytest.raises(
            StoryQualityGateBlocked,
            match="revision predecessor is not exact current accepted version",
        ):
            await repo.revise_critique_finding(
                value=finding_v3,
                predecessor=a1.ref,
                provenance=_provenance(finding_v3, "stale fork"),
                created_at=NOW,
                expected_revision=2,
            )
    finally:
        await writer.close()


def test_project_prefix_collision_is_rejected():
    screenplay_ref = VersionRef(
        logical_id=LogicalId("screenplay:project:film2:main"),
        version_id=VersionId("screenplay-v1"),
    )
    scene_ref = VersionRef(
        logical_id=LogicalId("screenplay-scene:project:film:scene-1"),
        version_id=VersionId("screenplay-scene-v1"),
    )
    with pytest.raises(ValidationError, match="same project"):
        _finding(screenplay_ref, scene_ref)


def test_root_cause_responsible_ref_project_prefix_collision_is_rejected():
    finding_ref = VersionRef(
        logical_id=LogicalId("critique-finding:project:film:causality-001"),
        version_id=VersionId("finding-v1"),
    )
    visible_ref = VersionRef(
        logical_id=LogicalId("screenplay:project:film:main"),
        version_id=VersionId("screenplay-v1"),
    )
    responsible_ref = VersionRef(
        logical_id=LogicalId("screenplay-scene:project:film2:scene-1"),
        version_id=VersionId("screenplay-scene-v1"),
    )
    preserve_ref = VersionRef(
        logical_id=LogicalId("setup-payoff-link:project:film:cassette-message"),
        version_id=VersionId("setup-payoff-v1"),
    )
    with pytest.raises(ValidationError, match="same project"):
        _root(finding_ref, visible_ref, responsible_ref, preserve_ref)


def test_human_lock_policy_requires_explicit_approval_ref():
    screenplay_ref = VersionRef(
        logical_id=LogicalId("screenplay:project:film:main"),
        version_id=VersionId("screenplay-v1"),
    )
    quality_ref = VersionRef(
        logical_id=LogicalId("story-quality:project:film:main"),
        version_id=VersionId("quality-v1"),
    )
    with pytest.raises(ValidationError, match="requires approval_ref"):
        _lock(
            screenplay_ref,
            quality_ref,
            approval_policy=ScriptApprovalPolicy.HUMAN_APPROVAL_REQUIRED,
        )


@pytest.mark.asyncio
async def test_provenance_must_match_exact_declared_sources(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _versions, _setup, screenplay_scene, screenplay = await _upstream(writer)
        repo = StoryQualityRepository(writer)
        finding = _finding(
            screenplay.ref,
            screenplay_scene.ref,
            kind=CritiqueKind.STRUCTURAL_WEAKNESS,
            severity=FindingSeverity.MAJOR,
        )
        bad = _provenance(finding, "bad provenance").model_copy(
            update={"source_versions": ()}
        )
        with pytest.raises(
            StoryQualityIdentityError,
            match="exactly match declared source bindings",
        ):
            await repo.create_critique_finding(
                value=finding,
                provenance=bad,
                created_at=NOW,
            )
    finally:
        await writer.close()
