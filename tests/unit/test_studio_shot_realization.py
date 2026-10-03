"""IMP-032 ShotEligibilityGate / FullShotSpec / Static / Motion / Trace tests."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from agent.studio import (
    EligibilityFinding,
    FullShotSpec,
    LegacyReferenceBinding,
    LifecycleState,
    LogicalId,
    MotionDeltaSpec,
    Provenance,
    ReferenceAsset,
    ReferenceAssetRepository,
    ReferenceCandidate,
    ReferenceCapabilityConstraint,
    ReferenceRequirement,
    ReferenceResolveRequest,
    ReferenceResolver,
    SemanticAuthorityClass,
    SemanticRecordMetadata,
    SemanticField,
    SemanticLayerSpec,
    ShotDecision,
    ShotDecisionTrace,
    ShotEligibilityBlocked,
    ShotEligibilityRequest,
    ShotEligibilityVerdict,
    ShotRealizationGateBlocked,
    ShotRealizationIdentityError,
    ShotRealizationRepository,
    ShotSemanticLayer,
    StaticKeyframeSpec,
    VersionId,
    VersionRef,
    build_reference_change_provenance,
    build_reference_provenance,
    build_shot_realization_provenance,
    full_shot_spec_logical_id,
    motion_delta_spec_logical_id,
    reference_asset_logical_id,
    sha256_bytes,
    shot_decision_trace_logical_id,
    shot_eligibility_gate_logical_id,
    static_keyframe_spec_logical_id,
)
from agent.studio.persistence import SQLiteWriteOwner
from tests.unit.test_studio_directing import ENTITY_REF, NOW, PROFILE_REF, PROJECT_ID, _seed_version
from tests.unit.test_studio_shot_planning import _ready


RULE_REF = VersionRef(
    logical_id=LogicalId("shot-eligibility-rule"),
    version_id=VersionId("rule-v1"),
)
MEDIA_ID = "11111111-1111-1111-1111-111111111111"


def _reference_asset(*, version: str = "reference-v1", content: bytes = b"lan-face") -> ReferenceAsset:
    return ReferenceAsset(
        project_id=PROJECT_ID,
        reference_asset_id=reference_asset_logical_id(PROJECT_ID, ENTITY_REF, slot="primary"),
        version_id=VersionId(version),
        entity_ref=ENTITY_REF,
        slot="primary",
        content_hash=sha256_bytes(content),
        role="identity.face",
        mime_type="image/png",
        source_uri="https://example.invalid/lan.png",
        evidence_refs=("evidence:imp032-reference",),
    )


def _reference_provenance(asset: ReferenceAsset, *, reason: str = "seed IMP-032 reference"):
    return build_reference_provenance(
        asset,
        actor_ref="studio:imp032-test",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp032-reference",),
        correlation_id="run:imp032-reference",
    )


async def _approved_reference_and_resolution(writer: SQLiteWriteOwner):
    asset = _reference_asset()
    repo = ReferenceAssetRepository(writer)
    await repo.create_initial(
        asset=asset,
        provenance=_reference_provenance(asset),
        created_at=NOW,
    )
    await repo.promote_current(
        ref=asset.ref,
        expected_revision=0,
        status=LifecycleState.APPROVED,
    )
    resolver = ReferenceResolver(writer)
    request = ReferenceResolveRequest(
        project_id=PROJECT_ID,
        active_profile_ref=PROFILE_REF,
        requirements=(
            ReferenceRequirement(
                entity_ref=ENTITY_REF,
                role="identity.face",
                required=True,
            ),
        ),
        capability=ReferenceCapabilityConstraint(
            max_references=2,
            supported_roles=("identity.face",),
            accepted_mime_types=("image/png",),
            requires_media_id=True,
        ),
    )
    resolution = await resolver.resolve(
        request=request,
        candidates=(
            ReferenceCandidate(
                asset_ref=asset.ref,
                compatibility=LegacyReferenceBinding(
                    asset_ref=asset.ref,
                    entity_ref=ENTITY_REF,
                    legacy_media_id=MEDIA_ID,
                    legacy_reference_image_url="https://example.invalid/lan-legacy.png",
                ),
            ),
        ),
    )
    return asset, resolution


async def _realization_fixture(writer: SQLiteWriteOwner):
    shot_repo, request, _, _, _, _, blocking, _ = await _ready(writer)
    await _seed_version(
        shot_repo.versions,
        RULE_REF,
        {"fixture": "shot-eligibility-rule-v1"},
        status=LifecycleState.APPROVED,
    )
    candidates = tuple(
        candidate.model_copy(update={"subject_refs": (ENTITY_REF,)})
        for candidate in request.candidates
    )
    request = request.model_copy(update={"candidates": candidates})
    expansion = await shot_repo.expand_scene(
        request=request,
        shot_item_version=VersionId("shot-v1"),
        shot_trace_version=VersionId("shot-trace-v1"),
        manifest_version=VersionId("manifest-v1"),
        actor_ref="studio:imp032-test",
        reason="seed canonical shots for IMP-032",
        recorded_at=NOW,
        source_refs=("evidence:imp032-shot",),
        correlation_id="run:imp032-shot",
    )
    asset, resolution = await _approved_reference_and_resolution(writer)
    shot = expansion.shot_items[0].value
    eligibility_request = ShotEligibilityRequest(
        project_id=PROJECT_ID,
        shot_ref=shot.ref,
        shot_list_manifest_ref=expansion.manifest.ref,
        state_snapshot_ref=blocking.state_snapshot_ref,
        reference_resolution=resolution,
        required_reference_entity_refs=(ENTITY_REF,),
        rule_version=RULE_REF,
    )
    return shot_repo, expansion, shot, blocking, asset, resolution, eligibility_request


def _layers(gate, shot) -> tuple[SemanticLayerSpec, ...]:
    reference_ref = gate.reference_evidence[0].asset_ref
    return (
        SemanticLayerSpec(
            layer=ShotSemanticLayer.L1_SUBJECT,
            fields=(
                SemanticField(
                    key="primary_subject",
                    value="Lan is the visible dramatic subject.",
                    authority_class=SemanticAuthorityClass.INHERITED,
                    source_refs=(shot.ref, reference_ref),
                ),
            ),
        ),
        SemanticLayerSpec(
            layer=ShotSemanticLayer.L2_STATE_WARDROBE,
            fields=(
                SemanticField(
                    key="wardrobe_state",
                    value="Preserve the approved cream shirt state.",
                    authority_class=SemanticAuthorityClass.FIXED,
                    source_refs=(gate.state_snapshot_ref, reference_ref),
                ),
            ),
        ),
        SemanticLayerSpec(
            layer=ShotSemanticLayer.L3_ACTION_PERFORMANCE,
            fields=(
                SemanticField(
                    key="performance_action",
                    value="Continue the motivated crossing until attention breaks toward the cassette.",
                    authority_class=SemanticAuthorityClass.INHERITED,
                    source_refs=(shot.ref, gate.directing_intent_ref, gate.blocking_plan_ref),
                ),
            ),
        ),
        SemanticLayerSpec(
            layer=ShotSemanticLayer.L4_ENVIRONMENT,
            fields=(
                SemanticField(
                    key="room_geography",
                    value="Keep the approved door-to-desk geography readable.",
                    authority_class=SemanticAuthorityClass.FIXED,
                    source_refs=(gate.spatial_contract_ref, gate.state_snapshot_ref),
                ),
            ),
        ),
        SemanticLayerSpec(
            layer=ShotSemanticLayer.L5_TIME_ATMOSPHERE,
            fields=(
                SemanticField(
                    key="atmosphere",
                    value="Late-afternoon room state carries contained unease.",
                    authority_class=SemanticAuthorityClass.INHERITED,
                    source_refs=(gate.state_snapshot_ref, gate.cinematography_objective_ref),
                ),
            ),
        ),
        SemanticLayerSpec(
            layer=ShotSemanticLayer.L6_CAMERA,
            fields=(
                SemanticField(
                    key="camera_strategy",
                    value="Frame and move only in response to motivated blocking and reveal timing.",
                    authority_class=SemanticAuthorityClass.INHERITED,
                    source_refs=(
                        gate.cinematography_objective_ref,
                        gate.blocking_plan_ref,
                        gate.directing_intent_ref,
                    ),
                ),
            ),
        ),
        SemanticLayerSpec(
            layer=ShotSemanticLayer.L7_LIGHTING_STYLE,
            fields=(
                SemanticField(
                    key="lighting_style",
                    value="Preserve approved room light while supporting visual isolation.",
                    authority_class=SemanticAuthorityClass.INHERITED,
                    source_refs=(gate.cinematography_objective_ref, gate.active_profile_ref),
                ),
            ),
        ),
        SemanticLayerSpec(
            layer=ShotSemanticLayer.L8_CONTINUITY,
            fields=(
                SemanticField(
                    key="continuity_lock",
                    value="Preserve wardrobe, cassette geography, screen direction and state facts.",
                    authority_class=SemanticAuthorityClass.FIXED,
                    source_refs=(gate.state_snapshot_ref, shot.ref, gate.blocking_plan_ref),
                ),
            ),
        ),
    )


def _full_spec(gate, shot, *, version: str = "full-spec-v1", lighting_suffix: str = "") -> FullShotSpec:
    layers = list(_layers(gate, shot))
    if lighting_suffix:
        index = list(ShotSemanticLayer).index(ShotSemanticLayer.L7_LIGHTING_STYLE)
        layer = layers[index]
        field = layer.fields[0].model_copy(
            update={"value": layer.fields[0].value + lighting_suffix}
        )
        layers[index] = layer.model_copy(update={"fields": (field,)})
    return FullShotSpec(
        project_id=PROJECT_ID,
        full_shot_spec_id=full_shot_spec_logical_id(PROJECT_ID, shot.shot_id),
        version_id=VersionId(version),
        shot_ref=shot.ref,
        eligibility_gate_ref=gate.ref,
        active_profile_ref=gate.active_profile_ref,
        directing_intent_ref=gate.directing_intent_ref,
        spatial_contract_ref=gate.spatial_contract_ref,
        blocking_plan_ref=gate.blocking_plan_ref,
        cinematography_objective_ref=gate.cinematography_objective_ref,
        state_snapshot_ref=gate.state_snapshot_ref,
        approved_state_designation_ref=gate.approved_state_designation_ref,
        reference_evidence=gate.reference_evidence,
        duration_seconds=shot.duration_budget_seconds,
        layers=tuple(layers),
        transition_intent="Cut only after the dramatic microchange is legible.",
        audio_intent="Preserve cassette voice as narrative evidence; no provider-specific mix settings.",
    )


def _provenance(value, reason: str, *, rule_version: VersionRef | None = RULE_REF):
    return build_shot_realization_provenance(
        value,
        actor_ref="studio:imp032-test",
        reason=reason,
        recorded_at=NOW,
        source_refs=("evidence:imp032",),
        rule_version=rule_version,
        correlation_id="run:imp032",
    )


def _static(spec: FullShotSpec, shot, *, version: str = "static-v1") -> StaticKeyframeSpec:
    return StaticKeyframeSpec(
        project_id=PROJECT_ID,
        static_keyframe_spec_id=static_keyframe_spec_logical_id(PROJECT_ID, shot.shot_id),
        version_id=VersionId(version),
        shot_ref=shot.ref,
        full_shot_spec_ref=spec.ref,
        state_snapshot_ref=spec.state_snapshot_ref,
        approved_state_designation_ref=spec.approved_state_designation_ref,
        reference_asset_refs=tuple(item.asset_ref for item in spec.reference_evidence),
        visible_subject_refs=(ENTITY_REF,),
        state_summary="Lan wears the approved cream shirt beside the cassette in the approved room state.",
        composition="Door-to-desk geography and cassette pressure anchor are visible at the keyframe.",
        visible_performance="Lan is mid-crossing with attention not yet fully surrendered to the cassette.",
        environment_state="Late-afternoon interior remains in the approved semantic world state.",
        lighting_state="Approved window light remains stable at the keyframe.",
    )


def _motion(spec: FullShotSpec, static: StaticKeyframeSpec, shot, *, version: str = "motion-v1") -> MotionDeltaSpec:
    return MotionDeltaSpec(
        project_id=PROJECT_ID,
        motion_delta_spec_id=motion_delta_spec_logical_id(PROJECT_ID, shot.shot_id),
        version_id=VersionId(version),
        shot_ref=shot.ref,
        full_shot_spec_ref=spec.ref,
        static_keyframe_spec_ref=static.ref,
        duration_seconds=spec.duration_seconds,
        action_delta="The practical crossing stops as the cassette voice becomes unavoidable.",
        performance_delta="Attention shifts from task focus into contained recognition.",
        blocking_delta="Movement resolves at the desk without changing approved room geography.",
        camera_movement_delta="Camera responds only to the motivated stop and reveal threshold.",
        continuity_requirements=(
            "Do not change wardrobe state.",
            "Do not reverse screen direction or cassette geography.",
        ),
    )


def _decision_trace(spec: FullShotSpec, gate, shot, *, version: str = "decision-v1") -> ShotDecisionTrace:
    sources = {
        ShotSemanticLayer.L1_SUBJECT: (shot.ref,),
        ShotSemanticLayer.L2_STATE_WARDROBE: (gate.state_snapshot_ref,),
        ShotSemanticLayer.L3_ACTION_PERFORMANCE: (gate.directing_intent_ref,),
        ShotSemanticLayer.L4_ENVIRONMENT: (gate.spatial_contract_ref,),
        ShotSemanticLayer.L5_TIME_ATMOSPHERE: (gate.state_snapshot_ref,),
        ShotSemanticLayer.L6_CAMERA: (gate.cinematography_objective_ref,),
        ShotSemanticLayer.L7_LIGHTING_STYLE: (gate.cinematography_objective_ref,),
        ShotSemanticLayer.L8_CONTINUITY: (gate.blocking_plan_ref, gate.state_snapshot_ref),
    }
    return ShotDecisionTrace(
        project_id=PROJECT_ID,
        shot_decision_trace_id=shot_decision_trace_logical_id(PROJECT_ID, shot.shot_id),
        version_id=VersionId(version),
        shot_ref=shot.ref,
        full_shot_spec_ref=spec.ref,
        eligibility_gate_ref=gate.ref,
        decisions=tuple(
            ShotDecision(
                layer=layer,
                decision=f"Resolve {layer.value} from accepted upstream authority.",
                rationale=f"{layer.value} is required to realize the shot's declared dramatic function without inventing parallel truth.",
                source_refs=sources[layer],
                rejected_alternatives=("Unmotivated decorative choice",),
            )
            for layer in ShotSemanticLayer
        ),
    )


async def _eligible_gate(writer: SQLiteWriteOwner):
    _, expansion, shot, blocking, asset, resolution, request = await _realization_fixture(writer)
    repo = ShotRealizationRepository(writer)
    gate_artifact = await repo.evaluate_eligibility(
        request=request,
        gate_version=VersionId("eligibility-v1"),
        actor_ref="studio:imp032-test",
        reason="evaluate exact shot eligibility",
        recorded_at=NOW,
        source_refs=("evidence:imp032-eligibility",),
        correlation_id="run:imp032-eligibility",
    )
    gate = gate_artifact.value
    assert gate.verdict is ShotEligibilityVerdict.ELIGIBLE
    return repo, expansion, shot, blocking, asset, resolution, request, gate


@pytest.mark.asyncio
async def test_full_provider_neutral_realization_preserves_same_shot_id_and_l1_l8(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, _, shot, _, _, _, _, gate = await _eligible_gate(writer)
        spec = _full_spec(gate, shot)
        spec_artifact = await repo.create_full_shot_spec(
            value=spec,
            provenance=_provenance(spec, "create FullShotSpec"),
            created_at=NOW,
        )
        static = _static(spec, shot)
        await repo.create_static_keyframe_spec(
            value=static,
            provenance=_provenance(static, "create StaticKeyframeSpec"),
            created_at=NOW,
        )
        motion = _motion(spec, static, shot)
        await repo.create_motion_delta_spec(
            value=motion,
            provenance=_provenance(motion, "create MotionDeltaSpec"),
            created_at=NOW,
        )
        trace = _decision_trace(spec, gate, shot)
        await repo.create_shot_decision_trace(
            value=trace,
            provenance=_provenance(trace, "create ShotDecisionTrace"),
            created_at=NOW,
        )

        assert gate.required_reference_entity_refs == (ENTITY_REF,)
        assert gate.reference_resolution_hash.startswith("sha256:")
        assert spec_artifact.value.shot_ref.logical_id == shot.shot_id
        assert spec.full_shot_spec_id != shot.shot_id
        assert [layer.layer for layer in spec.layers] == list(ShotSemanticLayer)
        assert len(spec.layers) == 8
        assert static.shot_ref.logical_id == motion.shot_ref.logical_id == trace.shot_ref.logical_id == shot.shot_id
        field_names = set(FullShotSpec.model_fields)
        assert "provider" not in field_names
        assert "prompt" not in field_names
        assert "model" not in field_names
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_rejected_gate_is_persisted_evidence_but_cannot_authorize_full_spec(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, _, shot, _, _, _, request = await _realization_fixture(writer)
        request = request.model_copy(
            update={
                "findings": (
                    EligibilityFinding(
                        code="SPATIAL_FEASIBILITY",
                        blocking=True,
                        message="Required spatial relation cannot be realized without breaking approved geography.",
                        source_refs=(shot.ref,),
                    ),
                )
            }
        )
        repo = ShotRealizationRepository(writer)
        gate_artifact = await repo.evaluate_eligibility(
            request=request,
            gate_version=VersionId("eligibility-rejected-v1"),
            actor_ref="studio:imp032-test",
            reason="persist rejected eligibility evidence",
            recorded_at=NOW,
            source_refs=("evidence:imp032-rejected",),
        )
        gate = gate_artifact.value
        assert gate.verdict is ShotEligibilityVerdict.REJECTED
        pointer = await repo.versions.get_current(gate.logical_id)
        assert pointer is not None and pointer.status is LifecycleState.APPROVED
        spec = _full_spec(gate, shot)
        with pytest.raises(ShotEligibilityBlocked, match="NO ELIGIBILITY PASS"):
            await repo.create_full_shot_spec(
                value=spec,
                provenance=_provenance(spec, "must not realize rejected shot"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_required_reference_gap_becomes_rejected_gate_not_silent_pass(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, _, shot, blocking, _, resolution, request = await _realization_fixture(writer)
        missing = VersionRef(
            logical_id=LogicalId("entity:legacy-char-extra"),
            version_id=VersionId("entity-v1"),
        )
        request = ShotEligibilityRequest(
            project_id=PROJECT_ID,
            shot_ref=shot.ref,
            shot_list_manifest_ref=request.shot_list_manifest_ref,
            state_snapshot_ref=blocking.state_snapshot_ref,
            reference_resolution=resolution,
            required_reference_entity_refs=(ENTITY_REF, missing),
            rule_version=RULE_REF,
        )
        repo = ShotRealizationRepository(writer)
        gate = (
            await repo.evaluate_eligibility(
                request=request,
                gate_version=VersionId("eligibility-missing-ref-v1"),
                actor_ref="studio:imp032-test",
                reason="evaluate missing required reference",
                recorded_at=NOW,
                source_refs=("evidence:imp032-missing-ref",),
            )
        ).value
        assert gate.verdict is ShotEligibilityVerdict.REJECTED
        assert any(item.code == "REFERENCE_MISSING" and item.blocking for item in gate.findings)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_reference_successor_selectively_invalidates_current_gate_and_blocks_realization(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, _, shot, _, asset, _, _, gate = await _eligible_gate(writer)
        ref_repo = ReferenceAssetRepository(writer)
        successor = _reference_asset(version="reference-v2", content=b"lan-face-v2")
        await ref_repo.create_successor(
            asset=successor,
            predecessor=asset.ref,
            provenance=_reference_provenance(successor, reason="reference semantic successor"),
            created_at=NOW,
        )
        change_provenance = build_reference_change_provenance(
            asset,
            successor,
            actor_ref="studio:imp032-test",
            reason="activate new reference version",
            recorded_at=NOW,
            source_refs=("evidence:imp032-reference-change",),
            correlation_id="run:imp032-reference-change",
        )
        pointer = await ref_repo.get_current_pointer(asset.reference_asset_id)
        assert pointer is not None
        result = await ref_repo.promote_successor_current(
            ref=successor.ref,
            expected_revision=pointer.revision,
            invalidation_provenance=change_provenance,
            repair_or_recompute_requirement="re-evaluate shot eligibility from current references",
        )
        assert any(record.affected_object_id == gate.logical_id for record in result.invalidations)
        with pytest.raises(ShotRealizationGateBlocked, match="unresolved durable invalidation"):
            await repo.assert_current_eligible_gate(gate.ref)
        spec = _full_spec(gate, shot)
        with pytest.raises(ShotRealizationGateBlocked):
            await repo.create_full_shot_spec(
                value=spec,
                provenance=_provenance(spec, "stale gate must not realize"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_rule_successor_invalidates_current_gate_and_blocks_realization(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, _, shot, _, _, _, _, gate = await _eligible_gate(writer)
        rule_v2 = VersionRef(
            logical_id=RULE_REF.logical_id,
            version_id=VersionId("rule-v2"),
        )
        provenance = Provenance(
            source_refs=("evidence:imp032-rule-change",),
            actor_ref="studio:imp032-test",
            reason="accept successor ShotEligibility rule version",
            recorded_at=NOW,
            correlation_id="run:imp032-rule-change",
        )
        await repo.versions.create_successor(
            metadata=SemanticRecordMetadata(
                logical_id=rule_v2.logical_id,
                version_id=rule_v2.version_id,
                predecessor=RULE_REF,
                provenance=provenance,
                created_at=NOW,
            ),
            payload={"fixture": "shot-eligibility-rule-v2"},
            supersession_reason=provenance.reason,
        )
        records = await repo.invalidations.create_for_change(
            cause="ShotEligibilityRule revision",
            source_old=RULE_REF,
            source_new=rule_v2,
            provenance=provenance,
            scope="shot_eligibility_descendants",
            repair_or_recompute_requirement="re-evaluate shot eligibility under the current rule version",
        )
        assert any(record.affected_object_id == gate.logical_id for record in records)
        pointer = await repo.versions.get_current(RULE_REF.logical_id)
        assert pointer is not None
        await repo.versions.update_current(
            logical_id=RULE_REF.logical_id,
            version_id=rule_v2.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=pointer.revision,
        )
        with pytest.raises(ShotRealizationGateBlocked, match="not exact current accepted version|unresolved durable invalidation"):
            await repo.assert_current_eligible_gate(gate.ref)
        spec = _full_spec(gate, shot)
        with pytest.raises(ShotRealizationGateBlocked):
            await repo.create_full_shot_spec(
                value=spec,
                provenance=_provenance(spec, "stale rule-bound gate must not realize"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_full_spec_revision_preserves_shot_id_and_selectively_invalidates_derivatives(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, _, shot, _, _, _, _, gate = await _eligible_gate(writer)
        spec_v1 = _full_spec(gate, shot)
        await repo.create_full_shot_spec(
            value=spec_v1,
            provenance=_provenance(spec_v1, "create full spec v1"),
            created_at=NOW,
        )
        static = _static(spec_v1, shot)
        await repo.create_static_keyframe_spec(
            value=static,
            provenance=_provenance(static, "create static v1"),
            created_at=NOW,
        )
        motion = _motion(spec_v1, static, shot)
        await repo.create_motion_delta_spec(
            value=motion,
            provenance=_provenance(motion, "create motion v1"),
            created_at=NOW,
        )
        trace = _decision_trace(spec_v1, gate, shot)
        await repo.create_shot_decision_trace(
            value=trace,
            provenance=_provenance(trace, "create decision trace v1"),
            created_at=NOW,
        )
        pointer = await repo.versions.get_current(spec_v1.logical_id)
        assert pointer is not None
        spec_v2 = _full_spec(
            gate,
            shot,
            version="full-spec-v2",
            lighting_suffix=" Preserve a slightly tighter isolation emphasis within the same accepted strategy.",
        )
        artifact, records = await repo.revise_full_shot_spec(
            value=spec_v2,
            predecessor=spec_v1.ref,
            provenance=_provenance(spec_v2, "revise full spec without rekeying shot"),
            created_at=NOW,
            expected_revision=pointer.revision,
        )
        assert artifact.value.shot_ref == shot.ref
        assert artifact.value.logical_id == spec_v1.logical_id
        affected = {(record.affected_object_id, record.affected_object_version) for record in records}
        assert (static.logical_id, static.version_id) in affected
        assert (motion.logical_id, motion.version_id) in affected
        assert (trace.logical_id, trace.version_id) in affected
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_static_and_motion_contracts_fail_closed_on_cross_shot_or_redefined_start_state(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, expansion, shot, _, _, _, _, gate = await _eligible_gate(writer)
        spec = _full_spec(gate, shot)
        await repo.create_full_shot_spec(
            value=spec,
            provenance=_provenance(spec, "create full spec"),
            created_at=NOW,
        )
        static = _static(spec, shot)
        await repo.create_static_keyframe_spec(
            value=static,
            provenance=_provenance(static, "create static"),
            created_at=NOW,
        )
        static_payload = static.model_dump(mode="python")
        static_payload["movement_delta"] = "forbidden temporal truth"
        with pytest.raises(ValidationError):
            StaticKeyframeSpec.model_validate(static_payload)

        motion = _motion(spec, static, shot)
        motion_payload = motion.model_dump(mode="python")
        motion_payload["start_state_summary"] = "forbidden replacement start state"
        with pytest.raises(ValidationError):
            MotionDeltaSpec.model_validate(motion_payload)

        other_shot = expansion.shot_items[1].value
        cross = motion.model_copy(update={"shot_ref": other_shot.ref})
        with pytest.raises(ShotRealizationGateBlocked, match="same shot"):
            await repo.create_motion_delta_spec(
                value=cross,
                provenance=_provenance(cross, "cross-shot motion must fail"),
                created_at=NOW,
            )
    finally:
        await writer.close()


def test_full_shot_spec_has_exactly_l1_l8_and_no_invented_l9_l12():
    layers = [
        {
            "layer": layer.value,
            "fields": [
                {
                    "key": "fixture",
                    "value": "fixture",
                    "authority_class": "INHERITED",
                    "source_refs": [
                        {
                            "logical_id": "shot-list-item:project:film:fixture",
                            "version_id": "shot-v1",
                        }
                    ],
                }
            ],
        }
        for layer in ShotSemanticLayer
    ]
    assert len(layers) == 8
    layers.append(
        {
            "layer": "L9_AUDIO",
            "fields": layers[0]["fields"],
        }
    )
    with pytest.raises(ValidationError):
        SemanticLayerSpec.model_validate(layers[-1])


@pytest.mark.asyncio
async def test_decision_trace_requires_all_layers_and_rejects_generic_cinematic_rationale(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, _, shot, _, _, _, _, gate = await _eligible_gate(writer)
        spec = _full_spec(gate, shot)
        await repo.create_full_shot_spec(
            value=spec,
            provenance=_provenance(spec, "create full spec"),
            created_at=NOW,
        )
        with pytest.raises(ValidationError, match="generic 'cinematic'"):
            ShotDecision(
                layer=ShotSemanticLayer.L6_CAMERA,
                decision="Use a shot.",
                rationale="cinematic",
                source_refs=(gate.cinematography_objective_ref,),
            )
        trace = _decision_trace(spec, gate, shot)
        payload = trace.model_dump(mode="python")
        payload["decisions"] = payload["decisions"][:-1]
        with pytest.raises(ValidationError, match="at least 8"):
            ShotDecisionTrace.model_validate(payload)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_decision_trace_registers_exact_authority_dependencies(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, _, shot, _, _, _, _, gate = await _eligible_gate(writer)
        spec = _full_spec(gate, shot)
        await repo.create_full_shot_spec(
            value=spec,
            provenance=_provenance(spec, "create full spec"),
            created_at=NOW,
        )
        trace = _decision_trace(spec, gate, shot)
        artifact = await repo.create_shot_decision_trace(
            value=trace,
            provenance=_provenance(trace, "create decision trace"),
            created_at=NOW,
        )
        incoming = await repo.graph.list_incoming(artifact.ref)
        sources = {edge.source_ref for edge in incoming}
        assert gate.cinematography_objective_ref in sources
        assert gate.state_snapshot_ref in sources
        assert gate.blocking_plan_ref in sources
        assert shot.ref in sources
        assert spec.ref in sources
        assert gate.ref in sources
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_full_spec_layer_camera_authority_cannot_self_originate(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, _, shot, _, _, _, _, gate = await _eligible_gate(writer)
        spec = _full_spec(gate, shot)
        layers = list(spec.layers)
        camera_index = list(ShotSemanticLayer).index(ShotSemanticLayer.L6_CAMERA)
        layer = layers[camera_index]
        bad_field = layer.fields[0].model_copy(update={"source_refs": (shot.ref,)})
        layers[camera_index] = layer.model_copy(update={"fields": (bad_field,)})
        bad_spec = spec.model_copy(update={"layers": tuple(layers)})
        with pytest.raises(ShotRealizationGateBlocked, match="L6_CAMERA"):
            await repo.create_full_shot_spec(
                value=bad_spec,
                provenance=_provenance(bad_spec, "camera authority bypass must fail"),
                created_at=NOW,
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_exact_gate_replay_is_idempotent_and_conflicting_replay_fails(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, _, _, _, _, _, request = await _realization_fixture(writer)
        repo = ShotRealizationRepository(writer)
        first = await repo.evaluate_eligibility(
            request=request,
            gate_version=VersionId("eligibility-v1"),
            actor_ref="studio:imp032-test",
            reason="idempotent gate evaluation",
            recorded_at=NOW,
            source_refs=("evidence:imp032-replay",),
            correlation_id="run:imp032-replay",
        )
        replay = await repo.evaluate_eligibility(
            request=request,
            gate_version=VersionId("eligibility-v1"),
            actor_ref="studio:imp032-test",
            reason="idempotent gate evaluation",
            recorded_at=NOW,
            source_refs=("evidence:imp032-replay",),
            correlation_id="run:imp032-replay",
        )
        assert replay.ref == first.ref
        changed_resolution = request.reference_resolution.model_copy(
            update={
                "capability": request.reference_resolution.capability.model_copy(
                    update={"max_references": 3}
                )
            }
        )
        changed_preflight = request.model_copy(
            update={"reference_resolution": changed_resolution}
        )
        with pytest.raises(ShotRealizationIdentityError, match="exact replay conflicts"):
            await repo.evaluate_eligibility(
                request=changed_preflight,
                gate_version=VersionId("eligibility-v1"),
                actor_ref="studio:imp032-test",
                reason="idempotent gate evaluation",
                recorded_at=NOW,
                source_refs=("evidence:imp032-replay",),
                correlation_id="run:imp032-replay",
            )

        conflict = request.model_copy(
            update={
                "findings": (
                    EligibilityFinding(
                        code="DURATION_VIOLATION",
                        blocking=True,
                        message="conflicting replay evidence",
                        source_refs=(request.shot_ref,),
                    ),
                )
            }
        )
        with pytest.raises(ShotRealizationIdentityError, match="exact replay conflicts"):
            await repo.evaluate_eligibility(
                request=conflict,
                gate_version=VersionId("eligibility-v1"),
                actor_ref="studio:imp032-test",
                reason="idempotent gate evaluation",
                recorded_at=NOW,
                source_refs=("evidence:imp032-replay",),
                correlation_id="run:imp032-replay",
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_gate_reference_binding_failure_leaves_draft_and_exact_retry_recovers(tmp_path, monkeypatch):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, _, _, _, _, _, request = await _realization_fixture(writer)
        repo = ShotRealizationRepository(writer)
        original = repo.references.bind_consumer
        calls = {"count": 0}

        async def fail_once(**kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("injected reference binding interruption")
            return await original(**kwargs)

        monkeypatch.setattr(repo.references, "bind_consumer", fail_once)
        with pytest.raises(RuntimeError, match="injected"):
            await repo.evaluate_eligibility(
                request=request,
                gate_version=VersionId("eligibility-recovery-v1"),
                actor_ref="studio:imp032-test",
                reason="recoverable eligibility evaluation",
                recorded_at=NOW,
                source_refs=("evidence:imp032-recovery",),
                correlation_id="run:imp032-recovery",
            )
        gate_id = shot_eligibility_gate_logical_id(
            PROJECT_ID, request.shot_ref.logical_id
        )
        pointer = await repo.versions.get_current(gate_id)
        assert pointer is not None and pointer.status is LifecycleState.DRAFT
        recovered = await repo.evaluate_eligibility(
            request=request,
            gate_version=VersionId("eligibility-recovery-v1"),
            actor_ref="studio:imp032-test",
            reason="recoverable eligibility evaluation",
            recorded_at=NOW,
            source_refs=("evidence:imp032-recovery",),
            correlation_id="run:imp032-recovery",
        )
        pointer = await repo.versions.get_current(recovered.ref.logical_id)
        assert pointer is not None and pointer.status is LifecycleState.APPROVED
        assert recovered.value.verdict is ShotEligibilityVerdict.ELIGIBLE
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_gate_reevaluation_invalidates_existing_full_spec(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        repo, _, shot, _, _, _, request, gate = await _eligible_gate(writer)
        spec = _full_spec(gate, shot)
        await repo.create_full_shot_spec(
            value=spec,
            provenance=_provenance(spec, "create full spec before reevaluation"),
            created_at=NOW,
        )
        pointer = await repo.versions.get_current(gate.logical_id)
        assert pointer is not None
        rejected_request = request.model_copy(
            update={
                "findings": (
                    EligibilityFinding(
                        code="DURATION_VIOLATION",
                        blocking=True,
                        message="Re-evaluation found an unresolved duration feasibility violation.",
                        source_refs=(shot.ref,),
                    ),
                )
            }
        )
        new_gate_artifact, records = await repo.reevaluate_eligibility(
            request=rejected_request,
            gate_version=VersionId("eligibility-v2"),
            predecessor=gate.ref,
            expected_revision=pointer.revision,
            actor_ref="studio:imp032-test",
            reason="re-evaluate shot eligibility",
            recorded_at=NOW,
            source_refs=("evidence:imp032-reevaluation",),
            correlation_id="run:imp032-reevaluation",
        )
        assert new_gate_artifact.value.verdict is ShotEligibilityVerdict.REJECTED
        assert any(record.affected_object_id == spec.logical_id for record in records)
        with pytest.raises(ShotRealizationGateBlocked, match="unresolved durable invalidation"):
            await repo._assert_current_valid(spec.ref, "FullShotSpec", {LifecycleState.APPROVED})
    finally:
        await writer.close()


def test_models_forbid_provider_runtime_request_authority_surfaces():
    forbidden = {"provider", "provider_id", "model", "prompt", "request", "api_key", "endpoint"}
    for model in (
        FullShotSpec,
        StaticKeyframeSpec,
        MotionDeltaSpec,
        ShotDecisionTrace,
    ):
        assert not forbidden.intersection(model.model_fields)
