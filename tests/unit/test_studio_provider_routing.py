"""IMP-050 ProviderProfile / CapabilityRegistry / deterministic Router tests."""

from __future__ import annotations

import json
from datetime import timedelta

import pytest
from pydantic import ValidationError

from agent.studio import (
    CapabilitySupport,
    EvidenceReference,
    LifecycleState,
    LogicalId,
    ProviderAvailabilityEvidence,
    ProviderAvailabilityState,
    ProviderCapabilityRoutingRepository,
    ProviderEvidenceFact,
    ProviderFactKind,
    ProviderProfile,
    ProviderRequirement,
    ProviderRouteRequest,
    ProviderRoutingDecision,
    ProviderRoutingGateBlocked,
    ProviderRoutingIdentityError,
    ProviderRoutingRuleSet,
    RequirementDisposition,
    RequirementOperator,
    RoutingVerdict,
    VersionId,
    VersionRef,
    build_provider_routing_provenance,
    provider_profile_logical_id,
    provider_routing_rule_logical_id,
)
from agent.studio.persistence import SQLiteWriteOwner
from tests.unit.test_studio_directing import NOW, PROJECT_ID
from tests.unit.test_studio_production_compiler import _compile_once


def _evidence(name: str) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=f"evidence:imp050:{name}",
        evidence_class="provider-capability-verification",
        locator=f"fixture://imp050/{name}",
        claim_scope=name,
    )


def _fact(
    key: str,
    *,
    value=None,
    support: CapabilitySupport = CapabilitySupport.SUPPORTED,
    kind: ProviderFactKind = ProviderFactKind.CAPABILITY,
    verified_at=None,
    expires_at=None,
) -> ProviderEvidenceFact:
    verified_at = verified_at or (NOW - timedelta(minutes=30))
    expires_at = expires_at or (NOW + timedelta(days=2))
    return ProviderEvidenceFact(
        kind=kind,
        key=key,
        support=support,
        value_json=None if value is None else json.dumps(value, sort_keys=True, separators=(",", ":")),
        evidence=_evidence(key.replace(".", "-")),
        verified_at=verified_at,
        expires_at=expires_at,
    )


def _profile(
    provider_key: str,
    *,
    version: str = "provider-profile-v1",
    surface: str = "video",
    aspect: str | None = "16:9",
    aspect_support: CapabilitySupport = CapabilitySupport.SUPPORTED,
    availability: ProviderAvailabilityState = ProviderAvailabilityState.AVAILABLE,
    verified_at=None,
    expires_at=None,
    extra_facts: tuple[ProviderEvidenceFact, ...] = (),
) -> ProviderProfile:
    verified_at = verified_at or (NOW - timedelta(minutes=30))
    expires_at = expires_at or (NOW + timedelta(days=2))
    facts = (
        _fact(
            "output.aspect_ratio",
            value=aspect if aspect_support is CapabilitySupport.SUPPORTED else None,
            support=aspect_support,
            verified_at=verified_at,
            expires_at=expires_at,
        ),
        *extra_facts,
    )
    return ProviderProfile(
        provider_profile_id=provider_profile_logical_id(
            provider_key,
            surface,
            "global",
            "video-generation",
            "model-v1",
        ),
        profile_version=VersionId(version),
        provider_key=provider_key,
        surface=surface,
        region="global",
        model_family="video-generation",
        model_version="model-v1",
        verified_at=verified_at,
        expires_at=expires_at,
        facts=facts,
        availability=ProviderAvailabilityEvidence(
            state=availability,
            evidence=_evidence(f"availability-{provider_key}"),
            verified_at=verified_at,
            expires_at=expires_at,
            detail=f"fixture availability for {provider_key}",
        ),
    )


def _profile_provenance(profile: ProviderProfile, reason: str):
    return build_provider_routing_provenance(
        profile,
        actor_ref="studio:imp050-test",
        reason=reason,
        recorded_at=NOW,
        source_refs=profile.evidence_ids,
        correlation_id="run:imp050-profile",
    )


def _rule(version: str = "routing-v1") -> ProviderRoutingRuleSet:
    return ProviderRoutingRuleSet(
        routing_rule_id=provider_routing_rule_logical_id(),
        version_id=VersionId(version),
    )


def _rule_provenance(rule: ProviderRoutingRuleSet):
    return build_provider_routing_provenance(
        rule,
        actor_ref="studio:imp050-test",
        reason="create deterministic provider routing rule",
        recorded_at=NOW,
        source_refs=("frozen-master:provider-router",),
        correlation_id="run:imp050-rule",
    )


def _request(ir, rule, profiles: tuple[ProviderProfile, ...], *, requirements=None, evaluated_at=NOW):
    if requirements is None:
        requirements = (
            ProviderRequirement(
                key="output.aspect_ratio",
                operator=RequirementOperator.EQUALS,
                expected_value_json=json.dumps("16:9"),
                source_refs=(ir.ref,),
            ),
        )
    return ProviderRouteRequest(
        project_id=PROJECT_ID,
        shot_ir_ref=ir.ref,
        active_profile_ref=ir.active_profile_ref,
        routing_rule_ref=rule.ref,
        region="global",
        surface="video",
        candidate_profile_refs=tuple(profile.ref for profile in profiles),
        requirements=requirements,
        evaluated_at=evaluated_at,
        run_correlation_id="run:imp050-route",
    )


async def _route_fixture(writer: SQLiteWriteOwner, *, profiles: tuple[ProviderProfile, ...]):
    compiled = await _compile_once(writer)
    ir = compiled[-1].artifact.value
    repo = ProviderCapabilityRoutingRepository(writer)
    rule = _rule()
    await repo.create_routing_rule(
        rule=rule,
        provenance=_rule_provenance(rule),
        created_at=NOW,
    )
    for profile in profiles:
        await repo.create_profile(
            profile=profile,
            provenance=_profile_provenance(profile, f"create {profile.provider_key} evidence profile"),
            created_at=NOW,
        )
    return repo, ir, rule


@pytest.mark.asyncio
async def test_provider_profile_requires_exact_evidence_provenance_and_unknown_is_not_guessed(tmp_path):
    with pytest.raises(ValidationError, match="cannot carry guessed"):
        _fact(
            "feature.reference_images",
            support=CapabilitySupport.UNKNOWN,
            value=True,
        )

    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo = ProviderCapabilityRoutingRepository(writer)
        profile = _profile("provider-a")
        bad = build_provider_routing_provenance(
            profile,
            actor_ref="studio:imp050-test",
            reason="missing evidence on purpose",
            recorded_at=NOW,
            source_refs=(profile.evidence_ids[0],),
        )
        with pytest.raises(ProviderRoutingGateBlocked, match="missing evidence refs"):
            await repo.create_profile(profile=profile, provenance=bad, created_at=NOW)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_router_selects_fresh_supported_profile_and_persists_exact_evidence(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        profile = _profile("provider-a")
        repo, ir, rule = await _route_fixture(writer, profiles=(profile,))
        request = _request(ir, rule, (profile,))
        artifact = await repo.route_initial(
            request=request,
            decision_version=VersionId("route-v1"),
            actor_ref="studio:imp050-test",
            reason="route exact ShotIR deterministically",
            recorded_at=NOW,
            source_refs=("evidence:imp050-routing",),
        )
        decision = artifact.value
        assert isinstance(decision, ProviderRoutingDecision)
        assert decision.verdict is RoutingVerdict.SELECTED
        assert decision.selected_profile_ref == profile.ref
        assert decision.shot_ir_ref == ir.ref
        assert decision.active_profile_ref == ir.active_profile_ref
        assert decision.routing_rule_ref == rule.ref
        assert decision.candidate_evaluations[0].eligible is True
        assert decision.candidate_evaluations[0].requirement_evaluations[0].disposition is RequirementDisposition.SATISFIED
        assert artifact.metadata.provenance.source_versions == decision.source_bindings()
        with pytest.raises(TypeError, match="as_of"):
            await repo.assert_selected_route(artifact.ref)
        asserted = await repo.assert_selected_route(artifact.ref, as_of=NOW)
        assert asserted == decision
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_router_selection_is_deterministic_independent_of_candidate_input_order(tmp_path):
    async def run(path, reverse: bool):
        writer = SQLiteWriteOwner(path)
        await writer.start()
        try:
            a = _profile("provider-a")
            b = _profile("provider-b")
            profiles = (b, a) if reverse else (a, b)
            repo, ir, rule = await _route_fixture(writer, profiles=profiles)
            artifact = await repo.route_initial(
                request=_request(ir, rule, profiles),
                decision_version=VersionId("route-v1"),
                actor_ref="studio:imp050-test",
                reason="prove deterministic routing",
                recorded_at=NOW,
                source_refs=("evidence:imp050-determinism",),
            )
            return artifact.value
        finally:
            await writer.close()

    first = await run(tmp_path / "a.db", False)
    second = await run(tmp_path / "b.db", True)
    assert first.selected_profile_ref == second.selected_profile_ref
    assert first.decision_hash == second.decision_hash
    assert first.candidate_profile_refs == second.candidate_profile_refs


@pytest.mark.asyncio
async def test_unsupported_or_unknown_required_capability_produces_no_hidden_fallback(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        unsupported = _profile(
            "provider-a",
            aspect_support=CapabilitySupport.UNSUPPORTED,
            aspect=None,
        )
        unknown = _profile(
            "provider-b",
            aspect_support=CapabilitySupport.UNKNOWN,
            aspect=None,
        )
        repo, ir, rule = await _route_fixture(writer, profiles=(unsupported, unknown))
        artifact = await repo.route_initial(
            request=_request(ir, rule, (unsupported, unknown)),
            decision_version=VersionId("route-v1"),
            actor_ref="studio:imp050-test",
            reason="persist no-eligible-provider evidence",
            recorded_at=NOW,
            source_refs=("evidence:imp050-no-provider",),
        )
        decision = artifact.value
        assert decision.verdict is RoutingVerdict.NO_ELIGIBLE_PROVIDER
        assert decision.selected_profile_ref is None
        assert all(not item.eligible for item in decision.candidate_evaluations)
        with pytest.raises(ProviderRoutingGateBlocked, match="no eligible selected provider"):
            await repo.assert_selected_route(artifact.ref, as_of=NOW)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_stale_provider_profile_is_ineligible_even_if_capability_matches(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        stale = _profile(
            "provider-a",
            verified_at=NOW - timedelta(days=3),
            expires_at=NOW - timedelta(days=1),
        )
        repo, ir, rule = await _route_fixture(writer, profiles=(stale,))
        decision = (
            await repo.route_initial(
                request=_request(ir, rule, (stale,)),
                decision_version=VersionId("route-v1"),
                actor_ref="studio:imp050-test",
                reason="reject stale provider evidence",
                recorded_at=NOW,
                source_refs=("evidence:imp050-stale",),
            )
        ).value
        assert decision.verdict is RoutingVerdict.NO_ELIGIBLE_PROVIDER
        assert "stale/not-yet-valid" in " ".join(decision.candidate_evaluations[0].rejection_reasons)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_router_rejects_omitted_or_weakened_shot_ir_execution_constraint(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        profile = _profile("provider-a")
        repo, ir, rule = await _route_fixture(writer, profiles=(profile,))
        omitted = _request(ir, rule, (profile,), requirements=())
        with pytest.raises(ProviderRoutingGateBlocked, match="omitted ShotIR execution constraints"):
            await repo.route_initial(
                request=omitted,
                decision_version=VersionId("route-v1"),
                actor_ref="studio:imp050-test",
                reason="must not omit compiler constraint",
                recorded_at=NOW,
            )

        weakened = _request(
            ir,
            rule,
            (profile,),
            requirements=(
                ProviderRequirement(
                    key="output.aspect_ratio",
                    operator=RequirementOperator.EQUALS,
                    expected_value_json=json.dumps("9:16"),
                    source_refs=(ir.ref,),
                ),
            ),
        )
        with pytest.raises(ProviderRoutingGateBlocked, match="weakens or changes"):
            await repo.route_initial(
                request=weakened,
                decision_version=VersionId("route-v2"),
                actor_ref="studio:imp050-test",
                reason="must not weaken compiler constraint",
                recorded_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_degradation_requires_explicit_policy_key(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        compiled = await _compile_once(writer)
        ir = compiled[-1].artifact.value
        repo = ProviderCapabilityRoutingRepository(writer)
        profile = _profile(
            "provider-a",
            extra_facts=(
                _fact(
                    "feature.reference_images",
                    support=CapabilitySupport.UNSUPPORTED,
                ),
            ),
        )
        request = _request(
            ir,
            _rule(),
            (profile,),
            requirements=(
                ProviderRequirement(
                    key="feature.reference_images",
                    operator=RequirementOperator.SUPPORTED,
                    degradable=True,
                    source_refs=(ir.ref,),
                ),
            ),
        )
        strict_policy = {
            "allowed_provider_keys": (),
            "allow_degradation_keys": (),
            "allow_degraded_availability": False,
            "max_cost_micros": None,
            "currency": None,
            "require_reconcile": False,
        }
        strict = repo._evaluate_candidate(profile=profile, request=request, policy=strict_policy)
        assert strict.eligible is False
        assert strict.requirement_evaluations[0].disposition is RequirementDisposition.UNSUPPORTED

        explicit_policy = {
            **strict_policy,
            "allow_degradation_keys": ("feature.reference_images",),
        }
        degraded = repo._evaluate_candidate(profile=profile, request=request, policy=explicit_policy)
        assert degraded.eligible is True
        assert degraded.degradation_keys == ("feature.reference_images",)
        assert degraded.requirement_evaluations[0].disposition is RequirementDisposition.DEGRADED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_budget_and_recovery_capability_are_evidence_gates(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        compiled = await _compile_once(writer)
        ir = compiled[-1].artifact.value
        repo = ProviderCapabilityRoutingRepository(writer)
        profile = _profile(
            "provider-a",
            extra_facts=(
                _fact("cost.estimated_micros", value=20, kind=ProviderFactKind.COST),
                _fact("cost.currency", value="usd", kind=ProviderFactKind.COST),
                _fact("recovery.reconcile", value=True, kind=ProviderFactKind.RECOVERY),
            ),
        )
        request = _request(ir, _rule(), (profile,))
        policy = {
            "allowed_provider_keys": (),
            "allow_degradation_keys": (),
            "allow_degraded_availability": False,
            "max_cost_micros": 30,
            "currency": "usd",
            "require_reconcile": True,
        }
        allowed = repo._evaluate_candidate(profile=profile, request=request, policy=policy)
        assert allowed.eligible is True
        keys = {item.key: item.disposition for item in allowed.requirement_evaluations}
        assert keys["cost.estimated_micros"] is RequirementDisposition.SATISFIED
        assert keys["cost.currency"] is RequirementDisposition.SATISFIED
        assert keys["recovery.reconcile"] is RequirementDisposition.SATISFIED

        too_expensive = _profile(
            "provider-b",
            extra_facts=(
                _fact("cost.estimated_micros", value=50, kind=ProviderFactKind.COST),
                _fact("cost.currency", value="usd", kind=ProviderFactKind.COST),
                _fact("recovery.reconcile", value=True, kind=ProviderFactKind.RECOVERY),
            ),
        )
        denied = repo._evaluate_candidate(profile=too_expensive, request=request, policy=policy)
        assert denied.eligible is False
        assert any(reason.startswith("budget:") for reason in denied.rejection_reasons)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_provider_profile_successor_invalidates_dependent_route_before_execution(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        first = _profile("provider-a", version="provider-profile-v1")
        repo, ir, rule = await _route_fixture(writer, profiles=(first,))
        route = await repo.route_initial(
            request=_request(ir, rule, (first,)),
            decision_version=VersionId("route-v1"),
            actor_ref="studio:imp050-test",
            reason="create route dependent on provider evidence",
            recorded_at=NOW,
            source_refs=("evidence:imp050-route-dependency",),
        )
        pointer = await repo.versions.get_current(first.logical_id)
        assert pointer is not None
        second = _profile(
            "provider-a",
            version="provider-profile-v2",
            aspect="9:16",
        )
        _, records = await repo.revise_profile(
            profile=second,
            predecessor=first.ref,
            provenance=_profile_provenance(second, "refresh provider evidence"),
            created_at=NOW + timedelta(minutes=1),
            expected_revision=pointer.revision,
        )
        assert any(
            record.affected_object_id == route.ref.logical_id
            and record.affected_object_version == route.ref.version_id
            for record in records
        )
        with pytest.raises(ProviderRoutingGateBlocked, match="unresolved invalidation"):
            await repo.assert_selected_route(route.ref, as_of=NOW + timedelta(minutes=1))
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_selected_route_fails_closed_when_profile_evidence_expires_before_submit(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        profile = _profile(
            "provider-a",
            expires_at=NOW + timedelta(minutes=5),
        )
        repo, ir, rule = await _route_fixture(writer, profiles=(profile,))
        route = await repo.route_initial(
            request=_request(ir, rule, (profile,)),
            decision_version=VersionId("route-v1"),
            actor_ref="studio:imp050-test",
            reason="route while evidence is fresh",
            recorded_at=NOW,
            source_refs=("evidence:imp050-expiry",),
        )
        await repo.assert_selected_route(route.ref, as_of=NOW + timedelta(minutes=4))
        with pytest.raises(ProviderRoutingGateBlocked, match="stale at execution time"):
            await repo.assert_selected_route(route.ref, as_of=NOW + timedelta(minutes=6))
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_exact_route_replay_is_idempotent_but_conflicting_version_reuse_fails(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        profile = _profile("provider-a")
        repo, ir, rule = await _route_fixture(writer, profiles=(profile,))
        request = _request(ir, rule, (profile,))
        kwargs = dict(
            request=request,
            decision_version=VersionId("route-v1"),
            actor_ref="studio:imp050-test",
            reason="idempotent route evaluation",
            recorded_at=NOW,
            source_refs=("evidence:imp050-replay",),
        )
        first = await repo.route_initial(**kwargs)
        second = await repo.route_initial(**kwargs)
        assert first == second

        conflict_request = request.model_copy(
            update={"run_correlation_id": "run:imp050-route-conflict"}
        )
        with pytest.raises(ProviderRoutingIdentityError, match="exact replay conflicts"):
            await repo.route_initial(
                request=conflict_request,
                decision_version=VersionId("route-v1"),
                actor_ref="studio:imp050-test",
                reason="idempotent route evaluation",
                recorded_at=NOW,
                source_refs=("evidence:imp050-replay",),
            )
    finally:
        await writer.close()


def test_provider_routing_contract_has_no_transport_or_secret_fields():
    forbidden = {
        "rpc_id",
        "endpoint",
        "request_payload",
        "cookie",
        "credential",
        "api_key",
        "session_id",
        "upload_slot",
    }
    assert forbidden.isdisjoint(ProviderProfile.model_fields)
    assert forbidden.isdisjoint(ProviderRoutingDecision.model_fields)


@pytest.mark.asyncio
async def test_degraded_availability_requires_explicit_policy(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        compiled = await _compile_once(writer)
        ir = compiled[-1].artifact.value
        repo = ProviderCapabilityRoutingRepository(writer)
        profile = _profile(
            "provider-a",
            availability=ProviderAvailabilityState.DEGRADED,
        )
        request = _request(ir, _rule(), (profile,))
        strict_policy = {
            "allowed_provider_keys": (),
            "allow_degradation_keys": (),
            "allow_degraded_availability": False,
            "max_cost_micros": None,
            "currency": None,
            "require_reconcile": False,
        }
        strict = repo._evaluate_candidate(profile=profile, request=request, policy=strict_policy)
        assert strict.eligible is False
        assert any("DEGRADED" in reason for reason in strict.rejection_reasons)

        explicit = repo._evaluate_candidate(
            profile=profile,
            request=request,
            policy={**strict_policy, "allow_degraded_availability": True},
        )
        assert explicit.eligible is True
        assert explicit.degradation_keys == ("availability",)
    finally:
        await writer.close()
