"""IMP-021 tests for Research Intelligence + StoryMaterial."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    ClaimCertainty,
    ClaimDisposition,
    EvidenceClaim,
    ExternalSourceReference,
    LifecycleState,
    LogicalId,
    ResearchArtifact,
    ResearchBrief,
    ResearchGateBlocked,
    ResearchRepository,
    ResearchToStoryMaterialService,
    SourceKind,
    StoryMaterialKind,
    UnsupportedSynthesis,
    VersionId,
    VersionRef,
    VersionRepository,
    SQLiteWriteOwner,
    SemanticRecordMetadata,
    Provenance,
    build_research_provenance,
)


NOW = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)
PROJECT_ID = LogicalId("project:film")
TOPIC_REF = VersionRef(
    logical_id=LogicalId("topic-resolution:project:film"),
    version_id=VersionId("t1"),
)
DOMAIN_REF = VersionRef(
    logical_id=LogicalId("domain-resolution:project:film"),
    version_id=VersionId("d1"),
)
PROFILE_REF = VersionRef(
    logical_id=LogicalId("active-profile:project:film"),
    version_id=VersionId("p1"),
)


def _seed_provenance(reason: str) -> Provenance:
    return Provenance(
        source_refs=("evidence:seed",),
        actor_ref="studio:test",
        reason=reason,
        recorded_at=NOW,
        correlation_id="run:imp021",
    )


def _metadata(ref: VersionRef, *, predecessor: VersionRef | None = None) -> SemanticRecordMetadata:
    return SemanticRecordMetadata(
        logical_id=ref.logical_id,
        version_id=ref.version_id,
        predecessor=predecessor,
        provenance=_seed_provenance("seed exact canonical source"),
        created_at=NOW,
    )


async def _seed_exact_inputs(writer: SQLiteWriteOwner) -> VersionRepository:
    versions = VersionRepository(writer)
    await versions.create_initial(
        metadata=_metadata(TOPIC_REF),
        payload={"topic": "family homecoming"},
        status=LifecycleState.APPROVED,
    )
    await versions.create_initial(
        metadata=_metadata(DOMAIN_REF),
        payload={"domain": "family drama"},
        status=LifecycleState.APPROVED,
    )
    await versions.create_initial(
        metadata=_metadata(PROFILE_REF),
        payload={"profile": "resolved"},
        status=LifecycleState.LOCKED,
    )
    return versions


def _brief(version: str = "v1", *, profile_ref: VersionRef = PROFILE_REF) -> ResearchBrief:
    return ResearchBrief(
        project_id=PROJECT_ID,
        version_id=VersionId(version),
        topic_ref=TOPIC_REF,
        domain_ref=DOMAIN_REF,
        active_profile_ref=profile_ref,
        factuality_class="grounded-fiction",
        questions=(
            "What legal/practical steps plausibly occur when selling inherited property?",
            "What details make a cassette recording plausible and period-consistent?",
        ),
        perspectives=("seller", "family member"),
        scope="Only evidence needed to constrain the home-sale and cassette story.",
    )


def _source(
    source_id: str = "source:legal-guide",
    *,
    locator: str = "https://example.test/inheritance-guide",
    attribution: str | None = None,
) -> ExternalSourceReference:
    return ExternalSourceReference(
        source_id=source_id,
        kind=SourceKind.OFFICIAL,
        locator=locator,
        title="Inheritance property procedure",
        publisher_or_author="Public authority",
        accessed_at=NOW,
        evidence_locator="section-4",
        attribution=attribution,
    )


def _claim(
    brief_ref: VersionRef,
    *,
    key: str = "sale-step",
    version: str = "v1",
    disposition: ClaimDisposition = ClaimDisposition.SUPPORTED,
    certainty: ClaimCertainty = ClaimCertainty.HIGH,
    confidence: float = 0.9,
    sources: tuple[ExternalSourceReference, ...] | None = None,
    contradicts: tuple[VersionRef, ...] = (),
    attribution_required: bool = False,
    attribution_note: str | None = None,
) -> EvidenceClaim:
    if sources is None:
        sources = (_source(),)
    return EvidenceClaim(
        project_id=PROJECT_ID,
        claim_key=key,
        version_id=VersionId(version),
        research_brief_ref=brief_ref,
        statement="A sale can require proof of inheritance before transfer.",
        disposition=disposition,
        certainty=certainty,
        confidence=confidence,
        scope="property-sale procedure",
        sources=sources,
        contradicts=contradicts,
        attribution_required=attribution_required,
        attribution_note=attribution_note,
    )


def _provenance(value, reason: str) -> Provenance:
    return build_research_provenance(
        value,
        actor_ref="studio:research",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp021",),
        correlation_id="run:imp021",
    )


@pytest.mark.asyncio
async def test_research_brief_and_supported_claim_promote_with_exact_provenance(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_exact_inputs(writer)
        repo = ResearchRepository(writer)

        brief = _brief()
        brief_artifact = await repo.create_initial(
            value=brief,
            provenance=_provenance(brief, "create brief"),
            created_at=NOW,
        )
        await repo.promote(ref=brief_artifact.value.ref, expected_revision=0)

        claim = _claim(brief_artifact.value.ref)
        claim_artifact = await repo.create_initial(
            value=claim,
            provenance=_provenance(claim, "record supported claim"),
            created_at=NOW,
        )
        pointer = await repo.promote(ref=claim_artifact.value.ref, expected_revision=0)

        assert pointer.status is LifecycleState.APPROVED
        stored = await repo.get(claim_artifact.value.ref)
        assert isinstance(stored.value, EvidenceClaim)
        assert stored.metadata.provenance.source_versions == claim.source_bindings()
        assert set(claim.external_source_refs()).issubset(
            set(stored.metadata.provenance.source_refs)
        )
    finally:
        await writer.close()


def test_supported_claim_requires_source_and_provenance_retains_external_refs():
    brief = _brief()
    with pytest.raises(ValidationError, match="supported claim requires"):
        _claim(brief.ref, sources=())

    claim = _claim(brief.ref)
    bad_provenance = Provenance(
        source_versions=claim.source_bindings(),
        source_refs=("evidence:missing-external",),
        actor_ref="studio:test",
        reason="bad provenance",
        recorded_at=NOW,
    )
    with pytest.raises(ValidationError, match="external source refs"):
        ResearchArtifact(
            metadata=SemanticRecordMetadata(
                logical_id=claim.logical_id,
                version_id=claim.version_id,
                provenance=bad_provenance,
                created_at=NOW,
            ),
            value=claim,
        )


@pytest.mark.asyncio
async def test_disputed_claim_is_explicit_and_contradiction_is_exact_versioned(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_exact_inputs(writer)
        repo = ResearchRepository(writer)
        brief = _brief()
        b = await repo.create_initial(
            value=brief,
            provenance=_provenance(brief, "brief"),
            created_at=NOW,
        )
        await repo.promote(ref=b.value.ref, expected_revision=0)

        first = _claim(b.value.ref, key="sale-step-a")
        a = await repo.create_initial(
            value=first,
            provenance=_provenance(first, "claim a"),
            created_at=NOW,
        )
        await repo.promote(ref=a.value.ref, expected_revision=0)

        disputed = _claim(
            b.value.ref,
            key="sale-step-b",
            disposition=ClaimDisposition.DISPUTED,
            certainty=ClaimCertainty.MEDIUM,
            confidence=0.55,
            sources=(
                _source(
                    "source:expert-b",
                    locator="https://example.test/expert-b",
                    attribution="Expert B",
                ),
            ),
            contradicts=(a.value.ref,),
            attribution_required=True,
            attribution_note="Attribute this interpretation to Expert B.",
        )
        d = await repo.create_initial(
            value=disputed,
            provenance=_provenance(disputed, "record disputed claim"),
            created_at=NOW,
        )
        await repo.promote(ref=d.value.ref, expected_revision=0)

        stored = await repo.get(d.value.ref)
        assert stored.value.disposition is ClaimDisposition.DISPUTED
        assert stored.value.contradicts == (a.value.ref,)
        assert stored.value.attribution_required is True
    finally:
        await writer.close()


def test_disputed_and_unsupported_semantics_fail_closed():
    brief = _brief()
    with pytest.raises(ValidationError, match="must require attribution"):
        _claim(
            brief.ref,
            disposition=ClaimDisposition.DISPUTED,
            certainty=ClaimCertainty.MEDIUM,
            confidence=0.5,
        )
    with pytest.raises(ValidationError, match="confidence"):
        _claim(
            brief.ref,
            disposition=ClaimDisposition.UNSUPPORTED,
            certainty=ClaimCertainty.LOW,
            confidence=0.8,
            sources=(),
        )


@pytest.mark.asyncio
async def test_story_material_preserves_disputed_status_and_attribution(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_exact_inputs(writer)
        repo = ResearchRepository(writer)
        service = ResearchToStoryMaterialService(repo)

        brief = _brief()
        b = await repo.create_initial(
            value=brief,
            provenance=_provenance(brief, "brief"),
            created_at=NOW,
        )
        await repo.promote(ref=b.value.ref, expected_revision=0)

        disputed = _claim(
            b.value.ref,
            key="cassette-date",
            disposition=ClaimDisposition.DISPUTED,
            certainty=ClaimCertainty.MEDIUM,
            confidence=0.55,
            sources=(
                _source(
                    "source:archive",
                    locator="https://example.test/archive",
                    attribution="Archive curator",
                ),
            ),
            attribution_required=True,
            attribution_note="Treat date range as disputed and attribute to archive curator.",
        )
        c = await repo.create_initial(
            value=disputed,
            provenance=_provenance(disputed, "disputed claim"),
            created_at=NOW,
        )
        await repo.promote(ref=c.value.ref, expected_revision=0)

        material = await service.build_material(
            project_id=PROJECT_ID,
            material_key="cassette-period-detail",
            version_id=VersionId("v1"),
            active_profile_ref=PROFILE_REF,
            kind=StoryMaterialKind.DETAIL,
            story_need="Use a period-plausible cassette detail without overstating date certainty.",
            content="The cassette format is plausible for the period, while the exact dating stays disputed.",
            allowed_transformations=("paraphrase", "scene-detail"),
            claim_refs=(c.value.ref,),
        )
        assert material.factual_disposition is ClaimDisposition.DISPUTED
        assert material.attribution_required is True
        assert material.attribution_note is not None

        m = await repo.create_initial(
            value=material,
            provenance=_provenance(material, "derive disputed material"),
            created_at=NOW,
        )
        await repo.promote(ref=m.value.ref, expected_revision=0)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_unsupported_claim_cannot_produce_story_material(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_exact_inputs(writer)
        repo = ResearchRepository(writer)
        service = ResearchToStoryMaterialService(repo)

        brief = _brief()
        b = await repo.create_initial(
            value=brief,
            provenance=_provenance(brief, "brief"),
            created_at=NOW,
        )
        await repo.promote(ref=b.value.ref, expected_revision=0)

        unsupported = _claim(
            b.value.ref,
            key="rumor",
            disposition=ClaimDisposition.UNSUPPORTED,
            certainty=ClaimCertainty.LOW,
            confidence=0.2,
            sources=(),
        )
        c = await repo.create_initial(
            value=unsupported,
            provenance=_provenance(unsupported, "record unsupported claim"),
            created_at=NOW,
        )
        await repo.promote(ref=c.value.ref, expected_revision=0)

        with pytest.raises(UnsupportedSynthesis, match="unsupported claim"):
            await service.build_material(
                project_id=PROJECT_ID,
                material_key="rumor-detail",
                version_id=VersionId("v1"),
                active_profile_ref=PROFILE_REF,
                kind=StoryMaterialKind.DETAIL,
                story_need="Need a detail",
                content="Unsupported rumor",
                allowed_transformations=("paraphrase",),
                claim_refs=(c.value.ref,),
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_story_material_rejects_stale_claim_version_at_promotion(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_exact_inputs(writer)
        repo = ResearchRepository(writer)
        service = ResearchToStoryMaterialService(repo)

        brief = _brief()
        b = await repo.create_initial(
            value=brief,
            provenance=_provenance(brief, "brief"),
            created_at=NOW,
        )
        await repo.promote(ref=b.value.ref, expected_revision=0)

        v1 = _claim(b.value.ref, key="sale-step", version="v1")
        c1 = await repo.create_initial(
            value=v1,
            provenance=_provenance(v1, "claim v1"),
            created_at=NOW,
        )
        await repo.promote(ref=c1.value.ref, expected_revision=0)

        material = await service.build_material(
            project_id=PROJECT_ID,
            material_key="sale-pressure",
            version_id=VersionId("v1"),
            active_profile_ref=PROFILE_REF,
            kind=StoryMaterialKind.PRESSURE,
            story_need="Create realistic sale pressure.",
            content="Documentation delays can create practical pressure.",
            allowed_transformations=("causal-pressure",),
            claim_refs=(c1.value.ref,),
        )
        m = await repo.create_initial(
            value=material,
            provenance=_provenance(material, "material from v1"),
            created_at=NOW,
        )

        v2 = EvidenceClaim(
            **{
                **v1.model_dump(),
                "version_id": VersionId("v2"),
                "statement": "A sale normally requires inheritance proof before transfer.",
                "confidence": 0.95,
            }
        )
        c2 = await repo.create_successor(
            value=v2,
            predecessor=c1.value.ref,
            provenance=_provenance(v2, "claim v2"),
            created_at=NOW,
        )
        await repo.promote(ref=c2.value.ref, expected_revision=1)

        with pytest.raises(ResearchGateBlocked, match="not exact current"):
            await repo.promote(ref=m.value.ref, expected_revision=0)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_research_brief_stale_profile_fails_gate(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        versions = await _seed_exact_inputs(writer)
        repo = ResearchRepository(writer)

        profile_v2 = VersionRef(
            logical_id=PROFILE_REF.logical_id,
            version_id=VersionId("p2"),
        )
        await versions.create_successor(
            metadata=_metadata(profile_v2, predecessor=PROFILE_REF),
            payload={"profile": "new"},
            supersession_reason="profile changed",
        )
        await versions.update_current(
            logical_id=profile_v2.logical_id,
            version_id=profile_v2.version_id,
            status=LifecycleState.LOCKED,
            expected_revision=0,
        )

        brief = _brief(profile_ref=PROFILE_REF)
        artifact = await repo.create_initial(
            value=brief,
            provenance=_provenance(brief, "stale brief"),
            created_at=NOW,
        )
        with pytest.raises(ResearchGateBlocked, match="stale/unlocked"):
            await repo.promote(ref=artifact.value.ref, expected_revision=0)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_successor_history_is_immutable_and_current_changes_only_on_promotion(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        await _seed_exact_inputs(writer)
        repo = ResearchRepository(writer)

        v1 = _brief("v1")
        a1 = await repo.create_initial(
            value=v1,
            provenance=_provenance(v1, "brief v1"),
            created_at=NOW,
        )
        await repo.promote(ref=a1.value.ref, expected_revision=0)

        v2 = ResearchBrief(
            **{
                **v1.model_dump(),
                "version_id": VersionId("v2"),
                "questions": v1.questions + ("What details are unnecessary for story truth?",),
            }
        )
        a2 = await repo.create_successor(
            value=v2,
            predecessor=a1.value.ref,
            provenance=_provenance(v2, "brief v2"),
            created_at=NOW,
        )
        current_before = await repo.get_current(v1.logical_id)
        assert current_before.value.ref == a1.value.ref

        await repo.promote(ref=a2.value.ref, expected_revision=1)
        current_after = await repo.get_current(v1.logical_id)
        assert current_after.value.ref == a2.value.ref
        assert (await repo.get(a1.value.ref)).value.questions == v1.questions
    finally:
        await writer.close()


def test_canonical_research_contracts_are_provider_neutral():
    forbidden = {
        "provider_id",
        "provider_name",
        "model_id",
        "model_key",
        "remote_job_id",
        "flow_project_id",
        "google_project_id",
    }
    for model in (ResearchBrief, EvidenceClaim):
        assert set(model.model_fields).isdisjoint(forbidden)
