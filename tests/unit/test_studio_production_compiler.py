"""IMP-033 ShotIR / deterministic Production Compiler authority tests."""

from __future__ import annotations

import hashlib
import json

import pytest
from pydantic import ValidationError

from agent.studio import (
    CompileDiagnosticSeverity,
    CompilerRuleSet,
    DependencyGraphRepository,
    LifecycleState,
    LogicalId,
    ProductionCompilerGateBlocked,
    ProductionCompilerIdentityError,
    ProductionCompilerRepository,
    Provenance,
    ProviderNeutralExecutionConstraint,
    ReferenceAssetRepository,
    SemanticRecordMetadata,
    ShotIR,
    ShotIRCompileRequest,
    VersionId,
    VersionRef,
    VersionRepository,
    build_reference_change_provenance,
    build_reference_provenance,
    compiler_rule_logical_id,
    shot_ir_logical_id,
)
from agent.studio.persistence import SQLiteWriteOwner
from tests.unit.test_studio_shot_realization import (
    NOW,
    PROJECT_ID,
    _eligible_gate,
    _full_spec,
    _motion,
    _provenance,
    _static,
)


def _rule(*, version: str = "compiler-v1", static_version: str = "static.v1") -> CompilerRuleSet:
    return CompilerRuleSet(
        compiler_rule_id=compiler_rule_logical_id(),
        version_id=VersionId(version),
        ir_schema_version="shot-ir.v1",
        normalization_version="canonical-json.v1",
        hash_algorithm="sha256",
        static_lowering_version=static_version,
        motion_lowering_version="motion.v1",
    )


def _rule_provenance(reason: str, *, correlation_id: str = "run:imp033-rule") -> Provenance:
    return Provenance(
        source_refs=("frozen-master:imp033",),
        actor_ref="studio:imp033-test",
        reason=reason,
        recorded_at=NOW,
        correlation_id=correlation_id,
    )


def _compile_request(spec, static, motion, rule: CompilerRuleSet, *, ratio: str = "16:9") -> ShotIRCompileRequest:
    return ShotIRCompileRequest(
        project_id=PROJECT_ID,
        full_shot_spec_ref=spec.ref,
        static_keyframe_spec_ref=static.ref,
        motion_delta_spec_ref=motion.ref,
        state_snapshot_ref=spec.state_snapshot_ref,
        approved_state_designation_ref=spec.approved_state_designation_ref,
        active_profile_ref=spec.active_profile_ref,
        reference_asset_refs=tuple(item.asset_ref for item in spec.reference_evidence),
        compiler_rule_ref=rule.ref,
        execution_constraints=(
            ProviderNeutralExecutionConstraint(
                key="output.aspect_ratio",
                value_json=json.dumps(ratio),
                source_refs=(spec.ref,),
            ),
        ),
    )


async def _compiler_fixture(writer: SQLiteWriteOwner):
    realization, _, shot, _, asset, _, _, gate = await _eligible_gate(writer)
    spec = _full_spec(gate, shot)
    await realization.create_full_shot_spec(
        value=spec,
        provenance=_provenance(spec, "create FullShotSpec for IMP-033"),
        created_at=NOW,
    )
    static = _static(spec, shot)
    await realization.create_static_keyframe_spec(
        value=static,
        provenance=_provenance(static, "create StaticKeyframeSpec for IMP-033"),
        created_at=NOW,
    )
    motion = _motion(spec, static, shot)
    await realization.create_motion_delta_spec(
        value=motion,
        provenance=_provenance(motion, "create MotionDeltaSpec for IMP-033"),
        created_at=NOW,
    )

    compiler = ProductionCompilerRepository(writer)
    rule = _rule()
    rule_provenance = _rule_provenance("create canonical IMP-033 compiler rule")
    await compiler.create_rule_set(
        rule_set=rule,
        provenance=rule_provenance,
        created_at=NOW,
    )
    request = _compile_request(spec, static, motion, rule)
    return compiler, realization, shot, asset, gate, spec, static, motion, rule, rule_provenance, request


async def _compile_once(writer: SQLiteWriteOwner, *, ir_version: str = "ir-v1"):
    (
        compiler,
        realization,
        shot,
        asset,
        gate,
        spec,
        static,
        motion,
        rule,
        rule_provenance,
        request,
    ) = await _compiler_fixture(writer)
    result = await compiler.compile_initial(
        request=request,
        ir_version=VersionId(ir_version),
        actor_ref="studio:imp033-test",
        reason="compile deterministic provider-neutral ShotIR",
        recorded_at=NOW,
        source_refs=("evidence:imp033",),
        correlation_id="run:imp033-compile",
    )
    return (
        compiler,
        realization,
        shot,
        asset,
        gate,
        spec,
        static,
        motion,
        rule,
        rule_provenance,
        request,
        result,
    )


@pytest.mark.asyncio
async def test_compile_preserves_canonical_shot_id_and_emits_provider_neutral_ir(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        data = await _compile_once(writer)
        shot = data[2]
        spec = data[5]
        static = data[6]
        motion = data[7]
        result = data[-1]
        ir = result.artifact.value
        assert isinstance(ir, ShotIR)
        assert ir.shot_ref.logical_id == shot.shot_id
        assert ir.shot_ir_id == shot_ir_logical_id(PROJECT_ID, shot.shot_id)
        assert ir.shot_ir_id != shot.shot_id
        assert ir.full_shot_spec_ref == spec.ref
        assert ir.static_keyframe_spec_ref == static.ref
        assert ir.motion_delta_spec_ref == motion.ref
        assert ir.semantic_layers == spec.layers
        assert ir.static_state.state_summary == static.state_summary
        assert ir.motion_delta.action_delta == motion.action_delta
        assert all(item.severity is not CompileDiagnosticSeverity.BLOCKER for item in ir.diagnostics)

        forbidden = {
            "provider",
            "provider_profile",
            "model",
            "prompt",
            "request_id",
            "upload_slot",
            "credential",
        }
        assert forbidden.isdisjoint(ShotIR.model_fields)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_compile_binds_every_exact_canonical_input_and_reference_hash(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        data = await _compile_once(writer)
        spec = data[5]
        static = data[6]
        motion = data[7]
        rule = data[8]
        result = data[-1]
        ir = result.artifact.value
        bindings = {(item.role, item.source) for item in ir.source_bindings()}
        for role, ref in (
            ("shot_list_item", spec.shot_ref),
            ("full_shot_spec", spec.ref),
            ("shot_eligibility_gate", spec.eligibility_gate_ref),
            ("static_keyframe_spec", static.ref),
            ("motion_delta_spec", motion.ref),
            ("state_snapshot", spec.state_snapshot_ref),
            ("approved_state_designation", spec.approved_state_designation_ref),
            ("active_production_profile", spec.active_profile_ref),
            ("compiler_rule", rule.ref),
        ):
            assert (role, ref) in bindings
        assert [item.asset_ref for item in ir.reference_bindings] == [
            item.asset_ref for item in spec.reference_evidence
        ]
        assert [item.content_hash for item in ir.reference_bindings] == [
            item.content_hash for item in spec.reference_evidence
        ]
        assert result.artifact.metadata.provenance.source_versions == ir.source_bindings()
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_compile_hashes_and_payload_are_deterministic_across_fresh_databases(tmp_path):
    async def run(path):
        writer = SQLiteWriteOwner(path)
        await writer.start()
        try:
            result = (await _compile_once(writer))[-1]
            ir = result.artifact.value
            return (
                ir.model_dump(mode="json"),
                result.hashes,
                result.artifact.metadata.content_hash,
            )
        finally:
            await writer.close()

    payload_a, hashes_a, content_a = await run(tmp_path / "a.db")
    payload_b, hashes_b, content_b = await run(tmp_path / "b.db")
    assert payload_a == payload_b
    assert hashes_a == hashes_b
    assert content_a == content_b
    assert hashes_a.input_fingerprint.startswith("sha256:")
    assert hashes_a.semantic_ir_hash.startswith("sha256:")
    assert hashes_a.static_request_hash.startswith("sha256:")
    assert hashes_a.motion_request_hash.startswith("sha256:")


@pytest.mark.asyncio
async def test_metadata_content_hash_is_full_immutable_shot_ir_payload_hash(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        result = (await _compile_once(writer))[-1]
        payload = result.artifact.value.model_dump(mode="json")
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        expected = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        assert result.artifact.metadata.content_hash == expected
    finally:
        await writer.close()


def test_provider_specific_execution_constraint_keys_fail_closed():
    with pytest.raises(ValidationError, match="provider/runtime-specific"):
        ProviderNeutralExecutionConstraint(
            key="provider.model",
            value_json='"veo"',
        )
    with pytest.raises(ValidationError, match="provider/runtime-specific"):
        ProviderNeutralExecutionConstraint(
            key="output.settings",
            value_json='{"upload_slot": 1}',
        )


@pytest.mark.asyncio
async def test_exact_compile_replay_is_idempotent_and_conflicting_replay_fails(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        data = await _compiler_fixture(writer)
        compiler = data[0]
        request = data[-1]
        kwargs = dict(
            request=request,
            ir_version=VersionId("ir-v1"),
            actor_ref="studio:imp033-test",
            reason="idempotent compile",
            recorded_at=NOW,
            source_refs=("evidence:imp033-replay",),
            correlation_id="run:imp033-replay",
        )
        first = await compiler.compile_initial(**kwargs)
        second = await compiler.compile_initial(**kwargs)
        assert second.artifact == first.artifact
        assert second.hashes == first.hashes

        changed = request.model_copy(
            update={
                "execution_constraints": (
                    ProviderNeutralExecutionConstraint(
                        key="output.aspect_ratio",
                        value_json='"9:16"',
                        source_refs=(data[5].ref,),
                    ),
                )
            }
        )
        with pytest.raises(ProductionCompilerIdentityError, match="exact replay conflicts"):
            await compiler.compile_initial(
                request=changed,
                ir_version=VersionId("ir-v1"),
                actor_ref="studio:imp033-test",
                reason="idempotent compile",
                recorded_at=NOW,
                source_refs=("evidence:imp033-replay",),
                correlation_id="run:imp033-replay",
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_compile_rejects_stale_full_shot_spec(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        data = await _compiler_fixture(writer)
        compiler, realization, shot, _, gate, spec, _, _, _, _, request = data
        pointer = await realization.versions.get_current(spec.logical_id)
        assert pointer is not None
        successor = _full_spec(
            gate,
            shot,
            version="full-spec-v2",
            lighting_suffix=" Preserve the same authority with refined emphasis.",
        )
        await realization.revise_full_shot_spec(
            value=successor,
            predecessor=spec.ref,
            provenance=_provenance(successor, "revise FullShotSpec before stale compile"),
            created_at=NOW,
            expected_revision=pointer.revision,
        )
        with pytest.raises(ProductionCompilerGateBlocked, match="FullShotSpec"):
            await compiler.compile_initial(
                request=request,
                ir_version=VersionId("ir-stale-v1"),
                actor_ref="studio:imp033-test",
                reason="reject stale FullShotSpec",
                recorded_at=NOW,
                source_refs=("evidence:imp033-stale",),
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_reference_successor_makes_old_compile_lineage_unusable(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        data = await _compiler_fixture(writer)
        compiler, _, _, asset, _, _, _, _, _, _, request = data
        refs = ReferenceAssetRepository(writer)
        pointer = await refs.get_current_pointer(asset.reference_asset_id)
        assert pointer is not None
        successor = asset.model_copy(
            update={
                "version_id": VersionId("reference-v2"),
                "content_hash": "sha256:" + "b" * 64,
            }
        )
        await refs.create_successor(
            asset=successor,
            predecessor=asset.ref,
            provenance=build_reference_provenance(
                successor,
                actor_ref="studio:imp033-test",
                reason="revise reference before compile",
                recorded_at=NOW,
                source_refs=("evidence:imp033-reference",),
            ),
            created_at=NOW,
        )
        await refs.promote_successor_current(
            ref=successor.ref,
            expected_revision=pointer.revision,
            invalidation_provenance=build_reference_change_provenance(
                asset,
                successor,
                actor_ref="studio:imp033-test",
                reason="activate reference successor",
                recorded_at=NOW,
                source_refs=("evidence:imp033-reference",),
            ),
            repair_or_recompute_requirement="Re-evaluate shot realization and recompile ShotIR.",
        )
        with pytest.raises(ProductionCompilerGateBlocked):
            await compiler.compile_initial(
                request=request,
                ir_version=VersionId("ir-reference-stale-v1"),
                actor_ref="studio:imp033-test",
                reason="reject stale reference lineage",
                recorded_at=NOW,
                source_refs=("evidence:imp033-reference-stale",),
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_recompile_preserves_ir_identity_and_selectively_invalidates_downstream(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        data = await _compile_once(writer)
        compiler = data[0]
        spec = data[5]
        request = data[10]
        first = data[-1]
        old_ir = first.artifact.value
        pointer = await compiler.versions.get_current(old_ir.logical_id)
        assert pointer is not None

        consumer_ref = VersionRef(
            logical_id=LogicalId("provider-lowering-placeholder:project:film:shot-001"),
            version_id=VersionId("consumer-v1"),
        )
        consumer_prov = Provenance(
            source_refs=("evidence:imp033-consumer",),
            actor_ref="studio:imp033-test",
            reason="seed downstream compiler consumer",
            recorded_at=NOW,
        )
        stored = await VersionRepository(writer).create_initial(
            metadata=SemanticRecordMetadata(
                logical_id=consumer_ref.logical_id,
                version_id=consumer_ref.version_id,
                provenance=consumer_prov,
                created_at=NOW,
            ),
            payload={"fixture": "downstream"},
            status=LifecycleState.APPROVED,
        )
        assert stored.metadata.logical_id == consumer_ref.logical_id
        await DependencyGraphRepository(writer).create_edge(
            source=old_ir.ref,
            dependent=consumer_ref,
            edge_type="provider_lowering_input",
            dependency_reason="downstream lowering consumes exact ShotIR",
            provenance=consumer_prov,
            created_at=NOW,
        )

        changed_request = request.model_copy(
            update={
                "execution_constraints": (
                    ProviderNeutralExecutionConstraint(
                        key="output.aspect_ratio",
                        value_json='"9:16"',
                        source_refs=(spec.ref,),
                    ),
                )
            }
        )
        second, records = await compiler.recompile_successor(
            request=changed_request,
            ir_version=VersionId("ir-v2"),
            predecessor=old_ir.ref,
            expected_revision=pointer.revision,
            actor_ref="studio:imp033-test",
            reason="recompile after neutral execution constraint change",
            recorded_at=NOW,
            source_refs=("evidence:imp033-recompile",),
            correlation_id="run:imp033-recompile",
        )
        new_ir = second.artifact.value
        assert new_ir.logical_id == old_ir.logical_id
        assert new_ir.shot_ref == old_ir.shot_ref
        assert new_ir.hashes != old_ir.hashes
        assert any(
            record.affected_object_id == consumer_ref.logical_id
            and record.affected_object_version == consumer_ref.version_id
            for record in records
        )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_compiler_rule_revision_invalidates_old_ir_and_changes_request_hashes(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        data = await _compile_once(writer)
        compiler = data[0]
        rule = data[8]
        request = data[10]
        first = data[-1]
        old_ir = first.artifact.value
        rule_pointer = await compiler.versions.get_current(rule.logical_id)
        ir_pointer = await compiler.versions.get_current(old_ir.logical_id)
        assert rule_pointer is not None and ir_pointer is not None

        rule2 = _rule(version="compiler-v2", static_version="static.v2")
        _, rule_records = await compiler.revise_rule_set(
            rule_set=rule2,
            predecessor=rule.ref,
            provenance=_rule_provenance(
                "revise canonical compiler lowering rules",
                correlation_id="run:imp033-rule-v2",
            ),
            created_at=NOW,
            expected_revision=rule_pointer.revision,
        )
        assert any(
            record.affected_object_id == old_ir.logical_id
            and record.affected_object_version == old_ir.version_id
            for record in rule_records
        )

        request2 = request.model_copy(update={"compiler_rule_ref": rule2.ref})
        second, _ = await compiler.recompile_successor(
            request=request2,
            ir_version=VersionId("ir-v2"),
            predecessor=old_ir.ref,
            expected_revision=ir_pointer.revision,
            actor_ref="studio:imp033-test",
            reason="recompile after compiler rule revision",
            recorded_at=NOW,
            source_refs=("evidence:imp033-rule-recompile",),
            correlation_id="run:imp033-rule-recompile",
        )
        new_ir = second.artifact.value
        assert new_ir.compiler_rule_ref == rule2.ref
        assert new_ir.hashes.input_fingerprint != old_ir.hashes.input_fingerprint
        assert new_ir.hashes.static_request_hash != old_ir.hashes.static_request_hash
        assert new_ir.hashes.motion_request_hash != old_ir.hashes.motion_request_hash
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_old_compiler_rule_ref_is_rejected_after_rule_revision(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        data = await _compiler_fixture(writer)
        compiler = data[0]
        rule = data[8]
        request = data[-1]
        pointer = await compiler.versions.get_current(rule.logical_id)
        assert pointer is not None
        rule2 = _rule(version="compiler-v2", static_version="static.v2")
        await compiler.revise_rule_set(
            rule_set=rule2,
            predecessor=rule.ref,
            provenance=_rule_provenance(
                "revise compiler before stale rule compile",
                correlation_id="run:imp033-rule-stale",
            ),
            created_at=NOW,
            expected_revision=pointer.revision,
        )
        with pytest.raises(ProductionCompilerGateBlocked, match="CompilerRuleSet"):
            await compiler.compile_initial(
                request=request,
                ir_version=VersionId("ir-stale-rule-v1"),
                actor_ref="studio:imp033-test",
                reason="reject stale compiler rule",
                recorded_at=NOW,
                source_refs=("evidence:imp033-stale-rule",),
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_rule_initial_creation_recovers_from_interruption_before_lock(tmp_path, monkeypatch):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        compiler = ProductionCompilerRepository(writer)
        rule = _rule()
        provenance = _rule_provenance("recover compiler rule initial create")
        original = compiler._promote_exact_current
        calls = {"count": 0}

        async def fail_once(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("injected rule promotion interruption")
            return await original(*args, **kwargs)

        monkeypatch.setattr(compiler, "_promote_exact_current", fail_once)
        with pytest.raises(RuntimeError, match="injected"):
            await compiler.create_rule_set(
                rule_set=rule,
                provenance=provenance,
                created_at=NOW,
            )
        artifact = await compiler.create_rule_set(
            rule_set=rule,
            provenance=provenance,
            created_at=NOW,
        )
        pointer = await compiler.versions.get_current(rule.logical_id)
        assert pointer is not None
        assert pointer.version_id == rule.version_id
        assert pointer.status is LifecycleState.LOCKED
        assert artifact.value == rule
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_shot_ir_initial_compile_recovers_from_interruption_before_promotion(tmp_path, monkeypatch):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        data = await _compiler_fixture(writer)
        compiler = data[0]
        request = data[-1]
        original = compiler._promote_exact_current
        calls = {"count": 0}

        async def fail_once(ref, *, status, label):
            if label == "ShotIR" and calls["count"] == 0:
                calls["count"] += 1
                raise RuntimeError("injected ShotIR promotion interruption")
            return await original(ref, status=status, label=label)

        monkeypatch.setattr(compiler, "_promote_exact_current", fail_once)
        kwargs = dict(
            request=request,
            ir_version=VersionId("ir-recovery-v1"),
            actor_ref="studio:imp033-test",
            reason="recover exact ShotIR compile",
            recorded_at=NOW,
            source_refs=("evidence:imp033-recovery",),
            correlation_id="run:imp033-recovery",
        )
        with pytest.raises(RuntimeError, match="injected"):
            await compiler.compile_initial(**kwargs)
        result = await compiler.compile_initial(**kwargs)
        pointer = await compiler.versions.get_current(result.artifact.value.logical_id)
        assert pointer is not None
        assert pointer.version_id == result.artifact.value.version_id
        assert pointer.status is LifecycleState.APPROVED
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_static_reference_pin_mismatch_fails_closed_before_ir_persistence(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        data = await _compiler_fixture(writer)
        compiler, realization, shot, _, _, spec, static, motion, _, _, request = data
        static_pointer = await realization.versions.get_current(static.logical_id)
        motion_pointer = await realization.versions.get_current(motion.logical_id)
        assert static_pointer is not None and motion_pointer is not None

        static2 = _static(spec, shot, version="static-v2").model_copy(
            update={"reference_asset_refs": ()}
        )
        await realization.revise_static_keyframe_spec(
            value=static2,
            predecessor=static.ref,
            provenance=_provenance(static2, "revise static to omit required reference"),
            created_at=NOW,
            expected_revision=static_pointer.revision,
        )
        motion2 = _motion(spec, static2, shot, version="motion-v2")
        await realization.revise_motion_delta_spec(
            value=motion2,
            predecessor=motion.ref,
            provenance=_provenance(motion2, "revise motion for new static"),
            created_at=NOW,
            expected_revision=motion_pointer.revision,
        )
        bad_request = request.model_copy(
            update={
                "static_keyframe_spec_ref": static2.ref,
                "motion_delta_spec_ref": motion2.ref,
            }
        )
        with pytest.raises(
            ProductionCompilerGateBlocked,
            match="StaticKeyframeSpec ReferenceAsset pins",
        ):
            await compiler.compile_initial(
                request=bad_request,
                ir_version=VersionId("ir-bad-static-v1"),
                actor_ref="studio:imp033-test",
                reason="reject incomplete static reference pins",
                recorded_at=NOW,
                source_refs=("evidence:imp033-bad-static",),
            )
    finally:
        await writer.close()
