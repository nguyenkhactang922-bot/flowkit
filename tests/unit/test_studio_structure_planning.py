"""IMP-024 tests for StructureProfile, DurationBudget and MacroBeatSheet."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    ActiveProductionProfile,
    AxisClassification,
    BudgetAllocation,
    BudgetLevel,
    ClassificationAxis,
    CountRange,
    DomainResolution,
    DurationBudget,
    GateVerdict,
    LifecycleState,
    LogicalId,
    MacroBeatSheet,
    MacroBeatSheetEntry,
    ProjectBootstrapInput,
    Provenance,
    RuntimeRangeSeconds,
    SemanticRecordMetadata,
    SQLiteWriteOwner,
    StoryCoreLockManifest,
    StoryCorePhase,
    StoryCoreVersion,
    StructurePlanningGateBlocked,
    StructurePlanningRepository,
    StructureProfile,
    VersionId,
    VersionRef,
    VersionRepository,
    WeightedLabel,
    build_structure_planning_provenance,
)


NOW = datetime(2026, 9, 30, 6, 0, tzinfo=timezone.utc)
PROJECT_ID = LogicalId("project:film")
ACTIVE_PROFILE_REF = VersionRef(
    logical_id=LogicalId("active-profile:project:film"),
    version_id=VersionId("profile-v1"),
)
PROJECT_REF = VersionRef(
    logical_id=LogicalId("project-input:project:film"),
    version_id=VersionId("project-v1"),
)
DOMAIN_REF = VersionRef(
    logical_id=LogicalId("niche-resolution:project:film"),
    version_id=VersionId("domain-v1"),
)
TOPIC_REF = VersionRef(
    logical_id=LogicalId("topic-resolution:project:film"),
    version_id=VersionId("topic-v1"),
)
PROFILE_RESOLUTION_REF = VersionRef(
    logical_id=LogicalId("profile-resolution:project:film"),
    version_id=VersionId("resolution-v1"),
)
RESOLVER_REF = VersionRef(
    logical_id=LogicalId("resolver:profile"),
    version_id=VersionId("resolver-v1"),
)
STORY_CORE_REF = VersionRef(
    logical_id=LogicalId("story-core:project:film"),
    version_id=VersionId("core-frozen-v1"),
)
MACRO_A_REF = VersionRef(
    logical_id=LogicalId("macro-story-beat:project:film:opening"),
    version_id=VersionId("macro-a-v1"),
)
MACRO_B_REF = VersionRef(
    logical_id=LogicalId("macro-story-beat:project:film:turn"),
    version_id=VersionId("macro-b-v1"),
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


def _seed_provenance(reason: str) -> Provenance:
    return Provenance(
        source_refs=("evidence:imp024-seed",),
        actor_ref="studio:test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp024",
    )


def _metadata(
    ref: VersionRef,
    *,
    predecessor: VersionRef | None = None,
) -> SemanticRecordMetadata:
    return SemanticRecordMetadata(
        logical_id=ref.logical_id,
        version_id=ref.version_id,
        predecessor=predecessor,
        provenance=_seed_provenance("seed exact source"),
        created_at=NOW,
    )


async def _seed(
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


def _active_profile() -> ActiveProductionProfile:
    return ActiveProductionProfile(
        profile_id=ACTIVE_PROFILE_REF.logical_id,
        profile_version=ACTIVE_PROFILE_REF.version_id,
        project_id=PROJECT_ID,
        resolver_version=RESOLVER_REF,
        profile_resolution_ref=PROFILE_RESOLUTION_REF,
        resolution_id=LogicalId("resolution:project:film:v1"),
        project_ref=PROJECT_REF,
        topic_ref=TOPIC_REF,
        domain_ref=DOMAIN_REF,
        effective_pack_refs=(),
        policy_entries=(),
        input_fingerprint=_hash_json({"project": PROJECT_ID.root}),
        effective_policy_hash=_hash_json({}),
        resolution_trace_hash=_hash_json({"resolution": "v1"}),
    )


def _project_input() -> ProjectBootstrapInput:
    return ProjectBootstrapInput(
        project_id=PROJECT_ID,
        raw_topic="A man returns home to sell the family house and finds a cassette.",
        project_goals=("short narrative film",),
        language="vi",
        locale="vi-VN",
        target_duration_seconds=120,
        platform_hints=("youtube",),
        format_hints=("short-film",),
        audience_hints=("adult",),
        factuality_mode="fiction",
        source_evidence_refs=("evidence:imp024-project",),
    )


def _weighted(label: str) -> WeightedLabel:
    return WeightedLabel(
        label=label,
        weight=1.0,
        reason=f"IMP-024 fixture classification: {label}",
    )


def _domain_resolution() -> DomainResolution:
    labels = {
        ClassificationAxis.DOMAIN: "storytelling",
        ClassificationAxis.NICHE: "family mystery drama",
        ClassificationAxis.GENRE: "drama",
        ClassificationAxis.AUDIENCE: "adult",
        ClassificationAxis.FORMAT: "short-film",
        ClassificationAxis.PLATFORM: "youtube",
        ClassificationAxis.FACTUALITY: "fiction",
    }
    return DomainResolution(
        project_id=PROJECT_ID,
        topic_resolution_ref=TOPIC_REF,
        registry_metadata_ref=VersionRef(
            logical_id=LogicalId("registry-metadata:canonical"),
            version_id=VersionId("registry-v1"),
        ),
        classifier_rule_version=VersionRef(
            logical_id=LogicalId("rule:domain-classifier"),
            version_id=VersionId("rule-v1"),
        ),
        classifications=tuple(
            AxisClassification(axis=axis, labels=(_weighted(label),))
            for axis, label in labels.items()
        ),
    )


def _frozen_story_core() -> StoryCoreVersion:
    return StoryCoreVersion(
        project_id=PROJECT_ID,
        version_id=STORY_CORE_REF.version_id,
        phase=StoryCorePhase.FROZEN_FOR_STRUCTURE,
        active_profile_ref=ACTIVE_PROFILE_REF,
        idea_ref=VersionRef(
            logical_id=LogicalId("story-idea:project:film"),
            version_id=VersionId("idea-v1"),
        ),
        logline_ref=VersionRef(
            logical_id=LogicalId("story-logline:project:film"),
            version_id=VersionId("logline-v1"),
        ),
        premise_ref=VersionRef(
            logical_id=LogicalId("story-premise:project:film"),
            version_id=VersionId("premise-v1"),
        ),
        angle_ref=VersionRef(
            logical_id=LogicalId("story-angle:project:film"),
            version_id=VersionId("angle-v1"),
        ),
        theme_ref=VersionRef(
            logical_id=LogicalId("story-theme:project:film"),
            version_id=VersionId("theme-v1"),
        ),
        core_goal="Resolve the cassette evidence before deciding the house sale.",
        core_question="Can he face the family truth before the sale deadline?",
        core_conflict="The sale deadline conflicts with the need to investigate.",
        core_stakes="A rushed sale may erase the last chance for truthful closure.",
        lock_manifest=StoryCoreLockManifest(
            draft_ref=VersionRef(
                logical_id=STORY_CORE_REF.logical_id,
                version_id=VersionId("core-draft-v1"),
            ),
            story_graph_ref=VersionRef(
                logical_id=LogicalId("story-graph:project:film"),
                version_id=VersionId("graph-v1"),
            ),
            causal_validation_ref=VersionRef(
                logical_id=LogicalId("story-graph-validation:project:film"),
                version_id=VersionId("validation-v1"),
            ),
            locked_at=NOW,
        ),
    )


async def _seed_context(writer: SQLiteWriteOwner) -> VersionRepository:
    versions = VersionRepository(writer)
    await _seed(
        versions,
        PROJECT_REF,
        status=LifecycleState.DRAFT,
        payload=_project_input().model_dump(mode="json"),
    )
    await _seed(
        versions,
        DOMAIN_REF,
        status=LifecycleState.REVIEW,
        payload=_domain_resolution().model_dump(mode="json"),
    )
    await _seed(
        versions,
        ACTIVE_PROFILE_REF,
        status=LifecycleState.LOCKED,
        payload=_active_profile().model_dump(mode="json"),
    )
    await _seed(
        versions,
        STORY_CORE_REF,
        status=LifecycleState.LOCKED,
        payload=_frozen_story_core().model_dump(mode="json"),
    )
    for ref in (MACRO_A_REF, MACRO_B_REF):
        await _seed(
            versions,
            ref,
            status=LifecycleState.APPROVED,
            payload={"canonical_macro_story_beat": ref.logical_id.root},
        )
    return versions


def _structure_profile(
    version: str = "structure-v1",
    *,
    macro_min: int = 2,
    macro_max: int = 4,
    target_runtime_seconds: int = 120,
    tolerance_seconds: int = 2,
    format_name: str = "short-film",
    genre_niche_label: str = "family mystery drama",
) -> StructureProfile:
    return StructureProfile(
        project_id=PROJECT_ID,
        version_id=VersionId(version),
        active_profile_ref=ACTIVE_PROFILE_REF,
        project_ref=PROJECT_REF,
        domain_ref=DOMAIN_REF,
        format_name=format_name,
        genre_niche_label=genre_niche_label,
        target_runtime_seconds=target_runtime_seconds,
        macro_story_beat_count=CountRange(minimum=macro_min, maximum=macro_max),
        sequence_count=CountRange(minimum=2, maximum=8),
        scene_count=CountRange(minimum=4, maximum=20),
        scene_dramatic_beat_count=CountRange(minimum=6, maximum=40),
        runtime_range_seconds=RuntimeRangeSeconds(minimum=90, maximum=180),
        budget_tolerance_seconds=tolerance_seconds,
    )


def _budget(
    structure_ref: VersionRef,
    version: str = "budget-v1",
    *,
    macro_a_seconds: int = 60,
    macro_b_seconds: int = 60,
    include_children: bool = True,
) -> DurationBudget:
    allocations = [
        BudgetAllocation(
            allocation_id="macro-a",
            level=BudgetLevel.MACRO_STORY_BEAT,
            seconds=macro_a_seconds,
        ),
        BudgetAllocation(
            allocation_id="macro-b",
            level=BudgetLevel.MACRO_STORY_BEAT,
            seconds=macro_b_seconds,
        ),
    ]
    if include_children:
        allocations.extend(
            (
                BudgetAllocation(
                    allocation_id="seq-a1",
                    level=BudgetLevel.SEQUENCE,
                    parent_allocation_id="macro-a",
                    seconds=30,
                ),
                BudgetAllocation(
                    allocation_id="seq-a2",
                    level=BudgetLevel.SEQUENCE,
                    parent_allocation_id="macro-a",
                    seconds=30,
                ),
                BudgetAllocation(
                    allocation_id="seq-b1",
                    level=BudgetLevel.SEQUENCE,
                    parent_allocation_id="macro-b",
                    seconds=40,
                ),
                BudgetAllocation(
                    allocation_id="seq-b2",
                    level=BudgetLevel.SEQUENCE,
                    parent_allocation_id="macro-b",
                    seconds=20,
                ),
                BudgetAllocation(
                    allocation_id="scene-a1",
                    level=BudgetLevel.SCENE,
                    parent_allocation_id="seq-a1",
                    seconds=30,
                ),
                BudgetAllocation(
                    allocation_id="scene-a2",
                    level=BudgetLevel.SCENE,
                    parent_allocation_id="seq-a2",
                    seconds=30,
                ),
                BudgetAllocation(
                    allocation_id="scene-b1",
                    level=BudgetLevel.SCENE,
                    parent_allocation_id="seq-b1",
                    seconds=40,
                ),
                BudgetAllocation(
                    allocation_id="scene-b2",
                    level=BudgetLevel.SCENE,
                    parent_allocation_id="seq-b2",
                    seconds=20,
                ),
                BudgetAllocation(
                    allocation_id="beat-a1-1",
                    level=BudgetLevel.SCENE_DRAMATIC_BEAT,
                    parent_allocation_id="scene-a1",
                    seconds=15,
                ),
                BudgetAllocation(
                    allocation_id="beat-a1-2",
                    level=BudgetLevel.SCENE_DRAMATIC_BEAT,
                    parent_allocation_id="scene-a1",
                    seconds=15,
                ),
                BudgetAllocation(
                    allocation_id="beat-a2-1",
                    level=BudgetLevel.SCENE_DRAMATIC_BEAT,
                    parent_allocation_id="scene-a2",
                    seconds=30,
                ),
                BudgetAllocation(
                    allocation_id="beat-b1-1",
                    level=BudgetLevel.SCENE_DRAMATIC_BEAT,
                    parent_allocation_id="scene-b1",
                    seconds=20,
                ),
                BudgetAllocation(
                    allocation_id="beat-b1-2",
                    level=BudgetLevel.SCENE_DRAMATIC_BEAT,
                    parent_allocation_id="scene-b1",
                    seconds=20,
                ),
                BudgetAllocation(
                    allocation_id="beat-b2-1",
                    level=BudgetLevel.SCENE_DRAMATIC_BEAT,
                    parent_allocation_id="scene-b2",
                    seconds=20,
                ),
                BudgetAllocation(
                    allocation_id="shot-a1-1",
                    level=BudgetLevel.SHOT,
                    parent_allocation_id="beat-a1-1",
                    seconds=15,
                ),
                BudgetAllocation(
                    allocation_id="shot-a1-2",
                    level=BudgetLevel.SHOT,
                    parent_allocation_id="beat-a1-2",
                    seconds=15,
                ),
                BudgetAllocation(
                    allocation_id="shot-a2-1",
                    level=BudgetLevel.SHOT,
                    parent_allocation_id="beat-a2-1",
                    seconds=30,
                ),
                BudgetAllocation(
                    allocation_id="shot-b1-1",
                    level=BudgetLevel.SHOT,
                    parent_allocation_id="beat-b1-1",
                    seconds=20,
                ),
                BudgetAllocation(
                    allocation_id="shot-b1-2",
                    level=BudgetLevel.SHOT,
                    parent_allocation_id="beat-b1-2",
                    seconds=20,
                ),
                BudgetAllocation(
                    allocation_id="shot-b2-1",
                    level=BudgetLevel.SHOT,
                    parent_allocation_id="beat-b2-1",
                    seconds=20,
                ),
            )
        )
    return DurationBudget(
        project_id=PROJECT_ID,
        version_id=VersionId(version),
        active_profile_ref=ACTIVE_PROFILE_REF,
        structure_profile_ref=structure_ref,
        total_seconds=120,
        tolerance_seconds=2,
        allocations=tuple(allocations),
    )


def _sheet(
    structure_ref: VersionRef,
    budget_ref: VersionRef,
    version: str = "sheet-v1",
) -> MacroBeatSheet:
    return MacroBeatSheet(
        project_id=PROJECT_ID,
        version_id=VersionId(version),
        active_profile_ref=ACTIVE_PROFILE_REF,
        story_core_ref=STORY_CORE_REF,
        structure_profile_ref=structure_ref,
        duration_budget_ref=budget_ref,
        entries=(
            MacroBeatSheetEntry(
                order_index=0,
                macro_story_beat_ref=MACRO_A_REF,
                duration_allocation_id="macro-a",
            ),
            MacroBeatSheetEntry(
                order_index=1,
                macro_story_beat_ref=MACRO_B_REF,
                duration_allocation_id="macro-b",
            ),
        ),
    )


def _provenance(value, reason: str) -> Provenance:
    return build_structure_planning_provenance(
        value,
        actor_ref="studio:imp024",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp024",),
        correlation_id="run:imp024",
    )


async def _ready_pipeline(writer: SQLiteWriteOwner):
    versions = await _seed_context(writer)
    repo = StructurePlanningRepository(writer)

    structure = _structure_profile()
    structure_artifact = await repo.create_structure_profile(
        value=structure,
        provenance=_provenance(structure, "create structure profile"),
        created_at=NOW,
    )
    budget = _budget(structure_artifact.ref)
    budget_artifact = await repo.create_duration_budget(
        value=budget,
        provenance=_provenance(budget, "create duration budget"),
        created_at=NOW,
    )
    sheet = _sheet(structure_artifact.ref, budget_artifact.ref)
    sheet_artifact = await repo.create_macro_beat_sheet(
        value=sheet,
        provenance=_provenance(sheet, "create macro beat sheet"),
        created_at=NOW,
    )
    return versions, repo, structure_artifact, budget_artifact, sheet_artifact


@pytest.mark.asyncio
async def test_structure_profile_is_range_policy_and_pins_active_profile_lineage(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_context(writer)
        repo = StructurePlanningRepository(writer)
        structure = _structure_profile()
        artifact = await repo.create_structure_profile(
            value=structure,
            provenance=_provenance(structure, "structure policy"),
            created_at=NOW,
        )

        assert artifact.value.macro_story_beat_count == CountRange(
            minimum=2,
            maximum=4,
        )
        assert artifact.value.runtime_range_seconds.contains(120)
        current = await repo.versions.get_current(artifact.ref.logical_id)
        assert current.version_id == artifact.ref.version_id
        assert current.status is LifecycleState.APPROVED
        assert artifact.metadata.provenance.rule_version == ACTIVE_PROFILE_REF
    finally:
        await writer.close()


def test_structure_profile_rejects_false_precision_and_cross_project_sources():
    payload = _structure_profile().model_dump(mode="python")
    payload["macro_story_beat_count"]["target"] = 3
    with pytest.raises(ValidationError):
        StructureProfile.model_validate(payload)

    payload = _structure_profile().model_dump(mode="python")
    payload["domain_ref"] = VersionRef(
        logical_id=LogicalId("niche-resolution:project:other"),
        version_id=VersionId("domain-v1"),
    )
    with pytest.raises(ValidationError, match="same project"):
        StructureProfile.model_validate(payload)


@pytest.mark.asyncio
async def test_structure_profile_rejects_shadow_format_genre_and_runtime(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_context(writer)
        repo = StructurePlanningRepository(writer)

        wrong_format = _structure_profile(format_name="feature-film")
        with pytest.raises(
            StructurePlanningGateBlocked,
            match="FORMAT axis",
        ):
            await repo.create_structure_profile(
                value=wrong_format,
                provenance=_provenance(wrong_format, "wrong format"),
                created_at=NOW,
            )

        wrong_genre = _structure_profile(genre_niche_label="space opera")
        with pytest.raises(
            StructurePlanningGateBlocked,
            match="GENRE/NICHE axes",
        ):
            await repo.create_structure_profile(
                value=wrong_genre,
                provenance=_provenance(wrong_genre, "wrong niche"),
                created_at=NOW,
            )

        wrong_runtime = _structure_profile(target_runtime_seconds=130)
        with pytest.raises(
            StructurePlanningGateBlocked,
            match="ProjectBootstrapInput",
        ):
            await repo.create_structure_profile(
                value=wrong_runtime,
                provenance=_provenance(wrong_runtime, "wrong runtime"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_structure_profile_rejects_stale_project_and_domain_inputs(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_context(writer)
        repo = StructurePlanningRepository(writer)

        project_v2 = VersionRef(
            logical_id=PROJECT_REF.logical_id,
            version_id=VersionId("project-v2"),
        )
        await versions.create_successor(
            metadata=_metadata(project_v2, predecessor=PROJECT_REF),
            payload=_project_input().model_dump(mode="json"),
            supersession_reason="project input revised",
        )
        await versions.update_current(
            logical_id=project_v2.logical_id,
            version_id=project_v2.version_id,
            status=LifecycleState.DRAFT,
            expected_revision=0,
        )

        stale_project = _structure_profile()
        with pytest.raises(
            StructurePlanningGateBlocked,
            match="ProjectBootstrapInput is not exact current accepted version",
        ):
            await repo.create_structure_profile(
                value=stale_project,
                provenance=_provenance(stale_project, "stale project source"),
                created_at=NOW,
            )
    finally:
        await writer.close()

    writer = SQLiteWriteOwner(tmp_path / "studio-domain.db")
    await writer.start()
    try:
        versions = await _seed_context(writer)
        repo = StructurePlanningRepository(writer)

        domain_v2 = VersionRef(
            logical_id=DOMAIN_REF.logical_id,
            version_id=VersionId("domain-v2"),
        )
        await versions.create_successor(
            metadata=_metadata(domain_v2, predecessor=DOMAIN_REF),
            payload=_domain_resolution().model_dump(mode="json"),
            supersession_reason="domain resolution revised",
        )
        await versions.update_current(
            logical_id=domain_v2.logical_id,
            version_id=domain_v2.version_id,
            status=LifecycleState.REVIEW,
            expected_revision=0,
        )

        stale_domain = _structure_profile()
        with pytest.raises(
            StructurePlanningGateBlocked,
            match="DomainResolution is not exact current accepted version",
        ):
            await repo.create_structure_profile(
                value=stale_domain,
                provenance=_provenance(stale_domain, "stale domain source"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_structure_profile_rejects_domain_topic_lineage_mismatch(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = VersionRepository(writer)
        await _seed(
            versions,
            PROJECT_REF,
            status=LifecycleState.DRAFT,
            payload=_project_input().model_dump(mode="json"),
        )
        wrong_topic = VersionRef(
            logical_id=TOPIC_REF.logical_id,
            version_id=VersionId("topic-other-v1"),
        )
        mismatched_domain = _domain_resolution().model_copy(
            update={"topic_resolution_ref": wrong_topic}
        )
        await _seed(
            versions,
            DOMAIN_REF,
            status=LifecycleState.REVIEW,
            payload=mismatched_domain.model_dump(mode="json"),
        )
        await _seed(
            versions,
            ACTIVE_PROFILE_REF,
            status=LifecycleState.LOCKED,
            payload=_active_profile().model_dump(mode="json"),
        )

        repo = StructurePlanningRepository(writer)
        structure = _structure_profile()
        with pytest.raises(
            StructurePlanningGateBlocked,
            match="exact TopicResolution pinned by ActiveProductionProfile",
        ):
            await repo.create_structure_profile(
                value=structure,
                provenance=_provenance(structure, "mismatched topic lineage"),
                created_at=NOW,
            )
    finally:
        await writer.close()


def test_macro_projection_refs_reject_cross_project_identity():
    structure_ref = VersionRef(
        logical_id=LogicalId("structure-profile:project:film"),
        version_id=VersionId("structure-v1"),
    )
    budget_ref = VersionRef(
        logical_id=LogicalId("duration-budget:project:film"),
        version_id=VersionId("budget-v1"),
    )
    payload = _sheet(structure_ref, budget_ref).model_dump(mode="python")
    payload["entries"][0]["macro_story_beat_ref"] = VersionRef(
        logical_id=LogicalId("macro-story-beat:project:film2:opening"),
        version_id=VersionId("macro-v1"),
    )
    with pytest.raises(ValidationError, match="same project"):
        MacroBeatSheet.model_validate(payload)


def test_duration_budget_rejects_project_prefix_collision_target():
    structure_ref = VersionRef(
        logical_id=LogicalId("structure-profile:project:film"),
        version_id=VersionId("structure-v1"),
    )
    valid = _budget(structure_ref)
    payload = valid.model_dump(mode="python")
    payload["allocations"][0]["target_ref"] = VersionRef(
        logical_id=LogicalId("macro-story-beat:project:film2:opening"),
        version_id=VersionId("macro-v1"),
    )
    with pytest.raises(ValidationError, match="same project"):
        DurationBudget.model_validate(payload)


def test_duration_budget_parent_child_tolerance_passes_and_overflow_fails():
    valid = _budget(
        VersionRef(
            logical_id=LogicalId("structure-profile:project:film"),
            version_id=VersionId("structure-v1"),
        )
    )
    assert valid.reconciliation_verdict is GateVerdict.PASS
    assert sum(item.seconds for item in valid.top_level_allocations()) == 120

    payload = valid.model_dump(mode="python")
    for item in payload["allocations"]:
        if item["allocation_id"] == "seq-a2":
            item["seconds"] = 20
    with pytest.raises(ValidationError, match="BUDGET_RUNTIME_OVERFLOW"):
        DurationBudget.model_validate(payload)


@pytest.mark.asyncio
async def test_duration_budget_rejects_missing_profile_required_levels(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_context(writer)
        repo = StructurePlanningRepository(writer)
        structure = _structure_profile()
        structure_artifact = await repo.create_structure_profile(
            value=structure,
            provenance=_provenance(structure, "structure"),
            created_at=NOW,
        )
        incomplete = _budget(
            structure_artifact.ref,
            include_children=False,
        )
        with pytest.raises(
            StructurePlanningGateBlocked,
            match="SEQUENCE allocation count falls outside StructureProfile range",
        ):
            await repo.create_duration_budget(
                value=incomplete,
                provenance=_provenance(incomplete, "missing required levels"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_duration_budget_uses_structure_profile_ranges_not_universal_counts(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_context(writer)
        repo = StructurePlanningRepository(writer)
        structure = _structure_profile(macro_min=3, macro_max=5)
        structure_artifact = await repo.create_structure_profile(
            value=structure,
            provenance=_provenance(structure, "three-plus macro profile"),
            created_at=NOW,
        )
        budget = _budget(structure_artifact.ref)
        with pytest.raises(
            StructurePlanningGateBlocked,
            match="allocation count falls outside StructureProfile range",
        ):
            await repo.create_duration_budget(
                value=budget,
                provenance=_provenance(budget, "range violation"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_macro_beat_sheet_is_projection_only_and_covers_budget(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _versions, repo, structure, budget, sheet = await _ready_pipeline(writer)

        assert [entry.macro_story_beat_ref for entry in sheet.value.entries] == [
            MACRO_A_REF,
            MACRO_B_REF,
        ]
        assert [entry.duration_allocation_id for entry in sheet.value.entries] == [
            "macro-a",
            "macro-b",
        ]
        assert sheet.value.projection_verdict is GateVerdict.PASS
        assert len(sheet.value.gate_checks) == 3
        assert sheet.value.structure_profile_ref == structure.ref
        assert sheet.value.duration_budget_ref == budget.ref
    finally:
        await writer.close()


def test_macro_beat_sheet_entry_cannot_duplicate_macro_story_beat_truth():
    payload = MacroBeatSheetEntry(
        order_index=0,
        macro_story_beat_ref=MACRO_A_REF,
        duration_allocation_id="macro-a",
    ).model_dump(mode="python")
    payload["dramatic_function"] = "Reveal the mother's hidden truth."
    with pytest.raises(ValidationError):
        MacroBeatSheetEntry.model_validate(payload)


@pytest.mark.asyncio
async def test_macro_beat_sheet_requires_frozen_story_core(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_context(writer)
        repo = StructurePlanningRepository(writer)
        structure = _structure_profile()
        structure_artifact = await repo.create_structure_profile(
            value=structure,
            provenance=_provenance(structure, "structure"),
            created_at=NOW,
        )
        budget = _budget(structure_artifact.ref)
        budget_artifact = await repo.create_duration_budget(
            value=budget,
            provenance=_provenance(budget, "budget"),
            created_at=NOW,
        )

        draft_ref = VersionRef(
            logical_id=STORY_CORE_REF.logical_id,
            version_id=VersionId("core-draft-current"),
        )
        draft = _frozen_story_core().model_copy(
            update={
                "version_id": draft_ref.version_id,
                "phase": StoryCorePhase.DRAFT,
                "lock_manifest": None,
            }
        )
        await versions.create_successor(
            metadata=_metadata(draft_ref, predecessor=STORY_CORE_REF),
            payload=draft.model_dump(mode="json"),
            supersession_reason="reopen story core",
        )
        await versions.update_current(
            logical_id=draft_ref.logical_id,
            version_id=draft_ref.version_id,
            status=LifecycleState.LOCKED,
            expected_revision=0,
        )

        sheet = _sheet(structure_artifact.ref, budget_artifact.ref)
        with pytest.raises(
            StructurePlanningGateBlocked,
            match="FROZEN_FOR_STRUCTURE",
        ):
            await repo.create_macro_beat_sheet(
                value=sheet.model_copy(update={"story_core_ref": draft_ref}),
                provenance=_provenance(
                    sheet.model_copy(update={"story_core_ref": draft_ref}),
                    "draft core sheet",
                ),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_structure_profile_revision_invalidates_budget_and_sheet_and_stale_profile_fails(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _versions, repo, structure_v1, budget_v1, sheet_v1 = await _ready_pipeline(writer)

        structure_v2 = _structure_profile(
            "structure-v2",
            macro_min=2,
            macro_max=5,
            target_runtime_seconds=120,
            tolerance_seconds=2,
        )
        structure_v2_artifact, invalidations = await repo.revise_structure_profile(
            value=structure_v2,
            predecessor=structure_v1.ref,
            provenance=_provenance(structure_v2, "widen macro planning range"),
            created_at=NOW,
            expected_revision=1,
        )
        affected = {
            (item.affected_object_id.root, item.affected_object_version.root)
            for item in invalidations
        }
        assert (
            budget_v1.ref.logical_id.root,
            budget_v1.ref.version_id.root,
        ) in affected
        assert (
            sheet_v1.ref.logical_id.root,
            sheet_v1.ref.version_id.root,
        ) in affected

        stale_budget = _budget(
            structure_v1.ref,
            version="budget-stale",
        )
        with pytest.raises(
            StructurePlanningGateBlocked,
            match="StructureProfile is not exact current accepted version",
        ):
            await repo.create_duration_budget(
                value=stale_budget,
                provenance=_provenance(stale_budget, "stale structure profile"),
                created_at=NOW,
            )

        current = await repo.versions.get_current(structure_v2_artifact.ref.logical_id)
        assert current.version_id == structure_v2_artifact.ref.version_id
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_revision_rejects_historical_noncurrent_predecessor(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_context(writer)
        repo = StructurePlanningRepository(writer)
        structure_v1 = _structure_profile()
        a1 = await repo.create_structure_profile(
            value=structure_v1,
            provenance=_provenance(structure_v1, "v1"),
            created_at=NOW,
        )
        structure_v2 = _structure_profile("structure-v2", macro_max=5)
        await repo.revise_structure_profile(
            value=structure_v2,
            predecessor=a1.ref,
            provenance=_provenance(structure_v2, "v2"),
            created_at=NOW,
            expected_revision=1,
        )
        structure_v3 = _structure_profile("structure-v3", macro_max=6)
        with pytest.raises(
            StructurePlanningGateBlocked,
            match="revision predecessor is not exact current accepted version",
        ):
            await repo.revise_structure_profile(
                value=structure_v3,
                predecessor=a1.ref,
                provenance=_provenance(structure_v3, "stale fork"),
                created_at=NOW,
                expected_revision=2,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_macro_sheet_rejects_budget_allocation_coverage_gap(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_context(writer)
        repo = StructurePlanningRepository(writer)
        structure = _structure_profile(macro_min=1, macro_max=4)
        structure_artifact = await repo.create_structure_profile(
            value=structure,
            provenance=_provenance(structure, "structure"),
            created_at=NOW,
        )
        budget = _budget(structure_artifact.ref)
        budget_artifact = await repo.create_duration_budget(
            value=budget,
            provenance=_provenance(budget, "budget"),
            created_at=NOW,
        )
        incomplete = _sheet(structure_artifact.ref, budget_artifact.ref).model_copy(
            update={
                "entries": (
                    MacroBeatSheetEntry(
                        order_index=0,
                        macro_story_beat_ref=MACRO_A_REF,
                        duration_allocation_id="macro-a",
                    ),
                )
            }
        )
        with pytest.raises(
            StructurePlanningGateBlocked,
            match="cover each top-level macro duration allocation",
        ):
            await repo.create_macro_beat_sheet(
                value=incomplete,
                provenance=_provenance(incomplete, "incomplete projection"),
                created_at=NOW,
            )
    finally:
        await writer.close()
