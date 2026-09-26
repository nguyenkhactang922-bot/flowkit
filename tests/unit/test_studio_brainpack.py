"""IMP-011 tests for the one canonical BrainPack Registry."""

from __future__ import annotations

from datetime import datetime, timezone

import aiosqlite
import pytest
from pydantic import ValidationError

from agent.studio.brainpack import (
    BrainPackApplicability,
    BrainPackDefinition,
    BrainPackFamily,
    BrainPackInheritanceCycle,
    BrainPackLifecycleError,
    BrainPackLifecycleState,
    BrainPackRef,
    BrainPackRegistryRepository,
    BrainPackRule,
    BrainPackRuleStrength,
    BrainPackSourceEvidence,
    BrainPackSourceKind,
    StoryBrainPackDefinition,
)
from agent.studio.persistence import (
    CASConflict,
    DEFAULT_MIGRATIONS,
    SQLiteWriteOwner,
    ensure_schema_compatibility,
)
from agent.studio.primitives import LogicalId, Provenance, VersionId


NOW = datetime(2026, 9, 26, 8, 0, tzinfo=timezone.utc)


def _provenance(reason: str = "register validated pack") -> Provenance:
    return Provenance(
        source_refs=("source:pack-spec", "license:pack-spec"),
        actor_ref="studio:brainpack-registry",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp011",
    )


def _source(
    *,
    kind: BrainPackSourceKind = BrainPackSourceKind.INTERNAL,
    adaptation_note: str | None = None,
) -> BrainPackSourceEvidence:
    return BrainPackSourceEvidence(
        source_kind=kind,
        source_ref="source:pack-spec",
        license_expression="PROPRIETARY",
        license_evidence_ref="license:pack-spec",
        validated=True,
        adaptation_note=adaptation_note,
    )


def _rule(
    key: str = "tone",
    value="restrained",
    *,
    strength: BrainPackRuleStrength = BrainPackRuleStrength.SOFT,
) -> BrainPackRule:
    return BrainPackRule(
        key=key,
        value=value,
        strength=strength,
        override_allowed=strength is BrainPackRuleStrength.SOFT,
        reason=f"rule for {key}",
    )


def _pack(
    pack_id: str,
    version: str,
    *,
    family: BrainPackFamily = BrainPackFamily.KNOWLEDGE,
    parents: tuple[BrainPackRef, ...] = (),
    predecessor: BrainPackRef | None = None,
) -> BrainPackDefinition:
    return BrainPackDefinition(
        pack_id=LogicalId(pack_id),
        pack_version=VersionId(version),
        family=family,
        name=f"{pack_id} {version}",
        description="Reusable canonical pack definition",
        parents=parents,
        applicability=BrainPackApplicability(domains=("film",)),
        rules=(_rule(),),
        source_evidence=(_source(),),
        provenance=_provenance(),
        created_at=NOW,
        predecessor=predecessor,
    )


def _story_pack(pack_id: str, version: str) -> StoryBrainPackDefinition:
    return StoryBrainPackDefinition(
        pack_id=LogicalId(pack_id),
        pack_version=VersionId(version),
        name="Story craft",
        description="Story specialization in the canonical registry",
        story_dimensions=("premise", "theme", "causality"),
        applicability=BrainPackApplicability(genres=("drama",)),
        rules=(
            _rule(
                "causal_continuity",
                {"required": True},
                strength=BrainPackRuleStrength.HARD,
            ),
        ),
        source_evidence=(_source(),),
        provenance=_provenance(),
        created_at=NOW,
    )


@pytest.mark.asyncio
async def test_one_registry_stores_canonical_families_and_story_specialization(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        knowledge = _pack("pack:knowledge", "v1")
        story = _story_pack("pack:story", "v1")

        assert await registry.create(knowledge) == knowledge
        assert await registry.create(story) == story

        all_definitions = await registry.list_definitions()
        assert [item.ref for item in all_definitions] == [
            knowledge.ref,
            story.ref,
        ]

        story_definitions = await registry.list_definitions(
            family=BrainPackFamily.STORY
        )
        assert len(story_definitions) == 1
        assert isinstance(story_definitions[0], StoryBrainPackDefinition)
        assert story_definitions[0].ref == story.ref
    finally:
        await writer.close()


def test_story_family_requires_typed_specialization_not_parallel_generic_shape():
    with pytest.raises(ValidationError, match="Story family must use"):
        BrainPackDefinition(
            pack_id=LogicalId("pack:story"),
            pack_version=VersionId("v1"),
            family=BrainPackFamily.STORY,
            name="Story",
            description="Invalid generic story pack",
            rules=(_rule(),),
            source_evidence=(_source(),),
            provenance=_provenance(),
            created_at=NOW,
        )


def test_source_license_and_donor_adaptation_are_required():
    with pytest.raises(ValidationError):
        BrainPackSourceEvidence(
            source_kind=BrainPackSourceKind.INTERNAL,
            source_ref="source:pack-spec",
            license_expression="",
            license_evidence_ref="license:pack-spec",
        )

    with pytest.raises(ValidationError, match="adaptation_note"):
        _source(kind=BrainPackSourceKind.DONOR)

    donor = _source(
        kind=BrainPackSourceKind.DONOR,
        adaptation_note="Adapted and validated against canonical pack schema",
    )
    assert donor.validated is True

    with pytest.raises(ValidationError, match="provenance must include"):
        BrainPackDefinition(
            pack_id=LogicalId("pack:bad-provenance"),
            pack_version=VersionId("v1"),
            family=BrainPackFamily.KNOWLEDGE,
            name="Bad",
            description="Missing source/license provenance refs",
            rules=(_rule(),),
            source_evidence=(_source(),),
            provenance=Provenance(
                source_refs=("evidence:other",),
                actor_ref="studio:test",
                reason="bad provenance",
                recorded_at=NOW,
            ),
            created_at=NOW,
        )


def test_rules_are_provider_neutral_and_other_family_is_typed():
    with pytest.raises(ValidationError, match="provider/runtime field"):
        _rule(value={"nested": {"provider_id": "remote"}})

    with pytest.raises(ValidationError, match="custom_family_key"):
        BrainPackDefinition(
            pack_id=LogicalId("pack:other"),
            pack_version=VersionId("v1"),
            family=BrainPackFamily.OTHER,
            name="Other",
            description="Missing typed custom family",
            rules=(_rule(),),
            source_evidence=(_source(),),
            provenance=_provenance(),
            created_at=NOW,
        )


@pytest.mark.asyncio
async def test_exact_parent_refs_and_logical_inheritance_cycle_detection(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        a1 = _pack("pack:a", "v1")
        await registry.create(a1)

        b1 = _pack(
            "pack:b",
            "v1",
            parents=(a1.ref,),
        )
        await registry.create(b1)

        a2 = _pack(
            "pack:a",
            "v2",
            predecessor=a1.ref,
            parents=(b1.ref,),
        )
        with pytest.raises(BrainPackInheritanceCycle):
            await registry.create(a2)

        missing_parent = BrainPackRef(
            pack_id=LogicalId("pack:missing"),
            pack_version=VersionId("v99"),
        )
        child = _pack(
            "pack:child",
            "v1",
            parents=(missing_parent,),
        )
        with pytest.raises(Exception, match="not found"):
            await registry.create(child)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_pack_definition_and_parent_edges_are_database_immutable(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        parent = _pack("pack:parent", "v1")
        child = _pack("pack:child", "v1", parents=(parent.ref,))
        await registry.create(parent)
        await registry.create(child)

        async def mutate_definition(tx):
            await tx.execute(
                """
                UPDATE studio_brainpack_definition
                SET family='CREATIVE'
                WHERE pack_id='pack:child' AND pack_version='v1'
                """
            )

        with pytest.raises(aiosqlite.IntegrityError, match="immutable"):
            await writer.execute(mutate_definition)

        async def mutate_parent(tx):
            await tx.execute(
                """
                UPDATE studio_brainpack_parent
                SET parent_pack_version='v999'
                WHERE pack_id='pack:child' AND pack_version='v1'
                """
            )

        with pytest.raises(aiosqlite.IntegrityError, match="immutable"):
            await writer.execute(mutate_parent)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_lifecycle_is_separate_cas_guarded_and_audited(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        pack = _pack("pack:lifecycle", "v1")
        await registry.create(pack)

        draft = await registry.get_lifecycle(pack.ref)
        assert draft.state is BrainPackLifecycleState.DRAFT
        assert draft.revision == 0

        validated = await registry.transition_lifecycle(
            ref=pack.ref,
            target=BrainPackLifecycleState.VALIDATED,
            expected_revision=0,
            reason="schema and policy validation passed",
            provenance=_provenance("validate pack"),
        )
        assert validated.revision == 1

        with pytest.raises(CASConflict):
            await registry.transition_lifecycle(
                ref=pack.ref,
                target=BrainPackLifecycleState.FROZEN,
                expected_revision=0,
                reason="stale attempt",
                provenance=_provenance("stale"),
            )

        frozen = await registry.transition_lifecycle(
            ref=pack.ref,
            target=BrainPackLifecycleState.FROZEN,
            expected_revision=1,
            reason="approved for reuse",
            provenance=_provenance("freeze pack"),
        )
        assert frozen.revision == 2

        with pytest.raises(BrainPackLifecycleError):
            await registry.transition_lifecycle(
                ref=pack.ref,
                target=BrainPackLifecycleState.VALIDATED,
                expected_revision=2,
                reason="illegal backtrack",
                provenance=_provenance("backtrack"),
            )

        deprecated = await registry.transition_lifecycle(
            ref=pack.ref,
            target=BrainPackLifecycleState.DEPRECATED,
            expected_revision=2,
            reason="superseded by newer pack version",
            provenance=_provenance("deprecate"),
        )
        assert deprecated.revision == 3

        history = await registry.lifecycle_history(pack.ref)
        assert [item.to_state for item in history] == [
            BrainPackLifecycleState.VALIDATED,
            BrainPackLifecycleState.FROZEN,
            BrainPackLifecycleState.DEPRECATED,
        ]
        assert [item.to_revision for item in history] == [1, 2, 3]
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_database_rejects_direct_illegal_lifecycle_jump(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        pack = _pack("pack:guard", "v1")
        await registry.create(pack)

        async def illegal_jump(tx):
            await tx.execute(
                """
                UPDATE studio_brainpack_lifecycle
                SET lifecycle_state='FROZEN', revision=revision+1
                WHERE pack_id='pack:guard' AND pack_version='v1'
                """
            )

        with pytest.raises(aiosqlite.IntegrityError, match="illegal"):
            await writer.execute(illegal_jump)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_successor_version_does_not_mutate_prior_registry_lifecycle(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        registry = BrainPackRegistryRepository(writer)
        v1 = _pack("pack:versioned", "v1")
        await registry.create(v1)
        await registry.transition_lifecycle(
            ref=v1.ref,
            target=BrainPackLifecycleState.VALIDATED,
            expected_revision=0,
            reason="validated",
            provenance=_provenance(),
        )
        await registry.transition_lifecycle(
            ref=v1.ref,
            target=BrainPackLifecycleState.FROZEN,
            expected_revision=1,
            reason="frozen",
            provenance=_provenance(),
        )

        v2 = _pack(
            "pack:versioned",
            "v2",
            predecessor=v1.ref,
        )
        await registry.create(v2)

        assert (await registry.get_lifecycle(v1.ref)).state is BrainPackLifecycleState.FROZEN
        assert (await registry.get_lifecycle(v2.ref)).state is BrainPackLifecycleState.DRAFT
    finally:
        await writer.close()


def test_registry_contract_does_not_own_effective_project_policy():
    forbidden = {
        "project_id",
        "active_production_profile",
        "effective_policy",
        "resolution_trace",
        "project_overrides",
        "selected_pack_stack",
    }
    definition_fields = set(BrainPackDefinition.model_fields)
    assert definition_fields.isdisjoint(forbidden)


@pytest.mark.asyncio
async def test_schema_v4_upgrades_to_v5_and_preserves_history(tmp_path):
    db_path = tmp_path / "studio.db"
    assert await ensure_schema_compatibility(
        db_path,
        supported_version=4,
        migrations=DEFAULT_MIGRATIONS[:4],
    ) == 4

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
            (5, "studio_brainpack_registry"),
        ]
    finally:
        await writer.close()
