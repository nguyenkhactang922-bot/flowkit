"""IMP-051 provider adapter anti-corruption tests."""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from agent.services.provider_adapters import FlowVideoProviderAdapter, OmniFlashProviderAdapter
from agent.studio import (
    LogicalId,
    ProviderAdapterGateBlocked,
    ProviderAdapterPrepareRequest,
    ProviderAdapterPreflight,
    ProviderExecutionPlan,
    ProviderExecutionMode,
    ProviderHandleKind,
    ProviderObservationKind,
    ProviderObservationState,
    ProviderProfile,
    ProviderRequirement,
    RequirementOperator,
    ProviderTransportHandle,
    RuntimeReferenceBinding,
    provider_profile_logical_id,
    VersionId,
    VersionRef,
)
from agent.studio.persistence import SQLiteWriteOwner
from tests.unit.test_studio_directing import NOW, PROJECT_ID
from tests.unit.test_studio_provider_routing import (
    _fact,
    _profile,
    _request,
    _route_fixture,
)


_FIXTURE_DURATION_SECONDS = 10
_FLOW_FIXTURE_MODEL = "flow-i2v-model-v1"


def _omni_fixture_model(
    mode: ProviderExecutionMode,
    *,
    duration: int = _FIXTURE_DURATION_SECONDS,
    resolution: str = "720p",
) -> str:
    suffix = "_360p" if resolution == "360p" else ""
    if mode is ProviderExecutionMode.TEXT_TO_VIDEO:
        return f"abra_t2v_{duration}s{suffix}"
    if mode is ProviderExecutionMode.FIRST_FRAME_TO_VIDEO:
        return f"abra_i2v_{duration}s{suffix}"
    if mode is ProviderExecutionMode.FIRST_LAST_FRAME_TO_VIDEO:
        return f"omni_flash_i2v_{duration}s_first_last{suffix}"
    if mode is ProviderExecutionMode.REFERENCES_TO_VIDEO:
        return f"abra_r2v_{duration}s{suffix}"
    raise AssertionError(mode)


def _adapter_profile(
    provider_key: str,
    *,
    mode: ProviderExecutionMode,
    resolution: str,
) -> ProviderProfile:
    model_version = (
        _FLOW_FIXTURE_MODEL
        if provider_key == "flow"
        else _omni_fixture_model(mode, resolution=resolution)
    )
    base = _profile(
        provider_key,
        extra_facts=(
            _fact("execution.mode", value=[item.value for item in ProviderExecutionMode]),
            _fact("output.resolution", value=[resolution]),
        ),
    )
    payload = base.model_dump(mode="python")
    payload["model_version"] = model_version
    payload["provider_profile_id"] = provider_profile_logical_id(
        provider_key,
        base.surface,
        base.region,
        base.model_family,
        model_version,
    )
    return ProviderProfile.model_validate(payload)


async def _selected_route_fixture(
    writer: SQLiteWriteOwner,
    *,
    provider_key: str,
    mode: ProviderExecutionMode = ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
    resolution: str = "720p",
):
    profile = _adapter_profile(
        provider_key,
        mode=mode,
        resolution=resolution,
    )
    repo, ir, rule = await _route_fixture(writer, profiles=(profile,))
    base = _request(ir, rule, (profile,))
    requirements = (
        *base.requirements,
        ProviderRequirement(
            key="execution.mode",
            operator=RequirementOperator.CONTAINS,
            expected_value_json=json.dumps(mode.value),
            source_refs=(ir.ref,),
        ),
        ProviderRequirement(
            key="output.resolution",
            operator=RequirementOperator.CONTAINS,
            expected_value_json=json.dumps(resolution),
            source_refs=(ir.ref,),
        ),
    )
    route_request = type(base).model_validate(
        {**base.model_dump(mode="python"), "requirements": requirements}
    )
    route = await repo.route_initial(
        request=route_request,
        decision_version=VersionId("route-v1"),
        actor_ref="studio:imp051-test",
        reason="select provider for anti-corruption adapter test",
        recorded_at=NOW,
        source_refs=("evidence:imp051-route",),
    )
    return repo, ir, profile, route.value


def _runtime_refs(ir):
    return tuple(
        RuntimeReferenceBinding(
            asset_ref=item.asset_ref,
            content_hash=item.content_hash,
            role=item.role,
            media_id=f"media-{index + 1}",
        )
        for index, item in enumerate(ir.reference_bindings)
    )


def _replace_plan(plan: ProviderExecutionPlan, **updates) -> ProviderExecutionPlan:
    payload = {
        name: getattr(plan, name)
        for name in ProviderExecutionPlan.model_fields
    }
    payload.update(updates)
    payload["plan_hash"] = "sha256:" + "0" * 64
    draft = ProviderExecutionPlan.model_construct(**payload)
    payload["plan_hash"] = draft.compute_hash()
    return ProviderExecutionPlan.model_validate(payload)


@pytest.mark.asyncio
async def test_preflight_consumes_exact_current_shot_ir_and_selected_route_without_mutating_truth(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, profile, decision = await _selected_route_fixture(writer, provider_key="flow")
        preflight = ProviderAdapterPreflight(writer)
        plan = await preflight.prepare(
            ProviderAdapterPrepareRequest(
                project_id=PROJECT_ID,
                shot_ir_ref=ir.ref,
                routing_decision_ref=decision.ref,
                mode=ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
                runtime_references=_runtime_refs(ir),
                execution_as_of=NOW,
            )
        )
        assert plan.shot_ir_ref == ir.ref
        assert plan.routing_decision_ref == decision.ref
        assert plan.provider_profile_ref == profile.ref
        assert plan.provider_key == "flow"
        assert plan.duration_seconds == ir.motion_delta.duration_seconds
        assert "L1_SUBJECT" in plan.prompt
        assert "MOTION_CAMERA" in plan.prompt
        assert plan.plan_hash.startswith("sha256:")
        current_ir = await preflight.compiler.get_shot_ir(ir.ref)
        assert current_ir is not None and current_ir.value == ir
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_preflight_rejects_runtime_reference_hash_drift(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, _, decision = await _selected_route_fixture(writer, provider_key="flow")
        refs = list(_runtime_refs(ir))
        if not refs:
            pytest.skip("fixture ShotIR has no references")
        refs[0] = refs[0].model_copy(update={"content_hash": "sha256:" + "f" * 64})
        with pytest.raises(ProviderAdapterGateBlocked, match="content hash mismatch"):
            await ProviderAdapterPreflight(writer).prepare(
                ProviderAdapterPrepareRequest(
                    project_id=PROJECT_ID,
                    shot_ir_ref=ir.ref,
                    routing_decision_ref=decision.ref,
                    mode=ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
                    runtime_references=tuple(refs),
                    execution_as_of=NOW,
                )
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_preflight_rejects_stale_provider_evidence_at_execution_time(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, _, decision = await _selected_route_fixture(writer, provider_key="flow")
        with pytest.raises(ProviderAdapterGateBlocked, match="stale"):
            await ProviderAdapterPreflight(writer).prepare(
                ProviderAdapterPrepareRequest(
                    project_id=PROJECT_ID,
                    shot_ir_ref=ir.ref,
                    routing_decision_ref=decision.ref,
                    mode=ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
                    runtime_references=_runtime_refs(ir),
                    execution_as_of=NOW + timedelta(days=5),
                )
            )
    finally:
        await writer.close()


class _FlowStub:
    def __init__(self):
        self.submit_calls = 0
        self.poll_calls = 0
        self.raise_on_submit = False
        self.transport_model = _FLOW_FIXTURE_MODEL
        self.model_calls = []
        self.last_submit_kwargs = None

    def _batch_video_model(self, tier, gen_type, aspect_ratio):
        self.model_calls.append((tier, gen_type, aspect_ratio))
        return self.transport_model

    async def generate_video(self, **kwargs):
        self.submit_calls += 1
        self.last_submit_kwargs = kwargs
        if self.raise_on_submit:
            raise TimeoutError("submit connection dropped after send")
        return {
            "status": 200,
            "data": {"operations": [{"operation": {"name": "op-123"}, "status": "PENDING"}]},
        }

    async def check_video_status(self, operations):
        self.poll_calls += 1
        return {
            "status": 200,
            "data": {
                "operations": [
                    {
                        "operation": {"name": "op-123"},
                        "status": "MEDIA_GENERATION_STATUS_SUCCESSFUL",
                        "media": {"media_id": "media-final", "url": "https://example.invalid/video"},
                    }
                ]
            },
        }


def _flow_adapter(stub: _FlowStub, profile: ProviderProfile, ir, *, resolution: str = "720p"):
    return FlowVideoProviderAdapter(
        provider_key="flow",
        flow_client=stub,
        runtime_project_id="flow-project-1",
        dialect_bindings={
            (profile.model_version, ir.motion_delta.duration_seconds, resolution): "PAYGATE_TIER_TWO"
        },
    )


@pytest.mark.asyncio
async def test_flow_adapter_supported_submit_poll_and_cancel_is_explicitly_unsupported(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, profile, decision = await _selected_route_fixture(writer, provider_key="flow")
        plan = await ProviderAdapterPreflight(writer).prepare(
            ProviderAdapterPrepareRequest(
                project_id=PROJECT_ID,
                shot_ir_ref=ir.ref,
                routing_decision_ref=decision.ref,
                mode=ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
                runtime_references=_runtime_refs(ir),
                execution_as_of=NOW,
            )
        )
        stub = _FlowStub()
        adapter = _flow_adapter(stub, profile, ir)
        submitted = await adapter.submit(plan, observed_at=NOW)
        assert submitted.state is ProviderObservationState.ACCEPTED
        assert submitted.handle is not None
        assert submitted.handle.kind is ProviderHandleKind.OPERATION
        polled = await adapter.poll(submitted.handle, observed_at=NOW)
        assert polled.state is ProviderObservationState.SUCCEEDED
        assert polled.output_media_id == "media-final"
        cancelled = await adapter.cancel(submitted.handle, observed_at=NOW)
        assert cancelled.state is ProviderObservationState.UNSUPPORTED
        assert stub.submit_calls == 1
        assert stub.poll_calls == 1
        assert stub.model_calls == [
            ("PAYGATE_TIER_TWO", "frame_2_video", "VIDEO_ASPECT_RATIO_LANDSCAPE")
        ]
        assert stub.last_submit_kwargs["user_paygate_tier"] == "PAYGATE_TIER_TWO"
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_flow_adapter_blocks_hidden_degraded_fallback_before_transport(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, profile, decision = await _selected_route_fixture(
            writer,
            provider_key="flow",
            mode=ProviderExecutionMode.REFERENCES_TO_VIDEO,
        )
        plan = await ProviderAdapterPreflight(writer).prepare(
            ProviderAdapterPrepareRequest(
                project_id=PROJECT_ID,
                shot_ir_ref=ir.ref,
                routing_decision_ref=decision.ref,
                mode=ProviderExecutionMode.REFERENCES_TO_VIDEO,
                runtime_references=_runtime_refs(ir),
                execution_as_of=NOW,
            )
        )
        stub = _FlowStub()
        adapter = _flow_adapter(stub, profile, ir)
        result = await adapter.submit(plan, observed_at=NOW)
        assert result.state is ProviderObservationState.UNSUPPORTED
        assert result.side_effect_may_have_occurred is False
        assert stub.submit_calls == 0
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_flow_submit_timeout_after_possible_send_is_ambiguous_and_never_retry_safe(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, profile, decision = await _selected_route_fixture(writer, provider_key="flow")
        plan = await ProviderAdapterPreflight(writer).prepare(
            ProviderAdapterPrepareRequest(
                project_id=PROJECT_ID,
                shot_ir_ref=ir.ref,
                routing_decision_ref=decision.ref,
                mode=ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
                runtime_references=_runtime_refs(ir),
                execution_as_of=NOW,
            )
        )
        stub = _FlowStub()
        stub.raise_on_submit = True
        result = await _flow_adapter(stub, profile, ir).submit(plan, observed_at=NOW)
        assert result.state is ProviderObservationState.AMBIGUOUS
        assert result.side_effect_may_have_occurred is True
        assert result.retry_safe is False
    finally:
        await writer.close()


class _OmniStub:
    def __init__(self):
        self.submit_calls = 0
        self.poll_calls = 0
        self.first_last_kwargs = None

    async def text(self, **kwargs):
        self.submit_calls += 1
        return {
            "status": 200,
            "data": {
                "workflows": [
                    {"name": "wf-1", "primary_media_id": "media-1", "project_id": "omni-project"}
                ]
            },
        }

    async def first(self, **kwargs):
        self.submit_calls += 1
        return {"status": 200, "data": {"operations": [{"operation": {"name": "op-1"}}]}}

    async def first_last(self, **kwargs):
        self.submit_calls += 1
        self.first_last_kwargs = kwargs
        return {"status": 200, "data": {"operations": [{"operation": {"name": "op-2"}}]}}


    async def refs(self, **kwargs):
        self.submit_calls += 1
        return {"status": 200, "data": {"operations": [{"operation": {"name": "op-3"}}]}}

    async def workflow_poll(self, workflows, include_encoded_video=False, project_id=""):
        self.poll_calls += 1
        return {
            "status": "COMPLETED",
            "workflows": [
                {
                    "name": workflows[0]["name"],
                    "done": True,
                    "media": {"media_id": "media-1", "url": "https://example.invalid/omni"},
                }
            ],
        }

    async def operation_poll(self, operations):
        self.poll_calls += 1
        return {
            "status": 200,
            "data": {
                "operations": [
                    {
                        "operation": {"name": operations[0]["operation"]["name"]},
                        "status": "PENDING",
                    }
                ]
            },
        }


def _omni_adapter(stub: _OmniStub) -> OmniFlashProviderAdapter:
    supported_models = frozenset(
        _omni_fixture_model(mode, duration=duration, resolution=resolution)
        for mode in ProviderExecutionMode
        for duration in (4, 6, 8, 10)
        for resolution in ("360p", "720p")
    )
    return OmniFlashProviderAdapter(
        provider_key="omni-flash",
        runtime_project_id="omni-project",
        supported_model_versions=supported_models,
        text_submit=stub.text,
        first_submit=stub.first,
        first_last_submit=stub.first_last,
        references_submit=stub.refs,
        workflow_poll=stub.workflow_poll,
        operation_poll=stub.operation_poll,
    )


@pytest.mark.asyncio
async def test_omni_workflow_reconcile_polls_existing_handle_and_never_resubmits(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, profile, decision = await _selected_route_fixture(
            writer,
            provider_key="omni-flash",
            mode=ProviderExecutionMode.TEXT_TO_VIDEO,
        )
        draft = ProviderExecutionPlan.model_construct(
            project_id=PROJECT_ID,
            shot_ir_ref=ir.ref,
            routing_decision_ref=decision.ref,
            provider_profile_ref=profile.ref,
            provider_key="omni-flash",
            surface=profile.surface,
            model_family=profile.model_family,
            model_version=profile.model_version,
            mode=ProviderExecutionMode.TEXT_TO_VIDEO,
            prompt="provider-neutral text-only transport fixture",
            duration_seconds=ir.motion_delta.duration_seconds,
            aspect_ratio="16:9",
            resolution="720p",
            runtime_references=(),
            plan_hash="sha256:" + "0" * 64,
        )
        payload = draft.model_dump(mode="python")
        payload["plan_hash"] = draft.compute_hash()
        plan = ProviderExecutionPlan.model_validate(payload)
        stub = _OmniStub()
        adapter = _omni_adapter(stub)
        submitted = await adapter.submit(plan, observed_at=NOW)
        assert submitted.state is ProviderObservationState.ACCEPTED
        assert submitted.handle is not None and submitted.handle.kind is ProviderHandleKind.WORKFLOW
        assert stub.submit_calls == 1
        reconciled = await adapter.reconcile(submitted.handle, observed_at=NOW)
        assert reconciled.kind is ProviderObservationKind.RECONCILE
        assert reconciled.state is ProviderObservationState.SUCCEEDED
        assert stub.submit_calls == 1
        assert stub.poll_calls == 1
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_reconcile_without_handle_is_ambiguous_not_resubmitted():
    stub = _OmniStub()
    result = await _omni_adapter(stub).reconcile(None, observed_at=NOW)
    assert result.state is ProviderObservationState.AMBIGUOUS
    assert result.retry_safe is False
    assert stub.submit_calls == 0


@pytest.mark.asyncio
async def test_omni_cancel_is_explicitly_unsupported_without_transport_call():
    stub = _OmniStub()
    handle = ProviderTransportHandle(
        provider_key="omni-flash",
        kind=ProviderHandleKind.OPERATION,
        handle_id="op-x",
    )
    result = await _omni_adapter(stub).cancel(handle, observed_at=NOW)
    assert result.state is ProviderObservationState.UNSUPPORTED
    assert stub.submit_calls == 0 and stub.poll_calls == 0


def _direct_omni_plan(runtime_references, *, mode: ProviderExecutionMode) -> ProviderExecutionPlan:
    duration = 8
    resolution = "720p"
    model_version = _omni_fixture_model(mode, duration=duration, resolution=resolution)
    draft = ProviderExecutionPlan.model_construct(
        project_id=PROJECT_ID,
        shot_ir_ref=VersionRef(
            logical_id=LogicalId("shot-ir:project:film:role-fixture"),
            version_id=VersionId("ir-v1"),
        ),
        routing_decision_ref=VersionRef(
            logical_id=LogicalId("provider-route:project:film:role-fixture"),
            version_id=VersionId("route-v1"),
        ),
        provider_profile_ref=VersionRef(
            logical_id=provider_profile_logical_id(
                "omni-flash", "omni-flash", "global", "veo", model_version
            ),
            version_id=VersionId("profile-v1"),
        ),
        provider_key="omni-flash",
        surface="omni-flash",
        model_family="veo",
        model_version=model_version,
        mode=mode,
        prompt="provider-neutral role mapping fixture",
        duration_seconds=duration,
        aspect_ratio="16:9",
        resolution=resolution,
        runtime_references=tuple(runtime_references),
        plan_hash="sha256:" + "0" * 64,
    )
    payload = draft.model_dump(mode="python")
    payload["plan_hash"] = draft.compute_hash()
    return ProviderExecutionPlan.model_validate(payload)


@pytest.mark.asyncio
async def test_preflight_rejects_runtime_reference_role_drift(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, _, decision = await _selected_route_fixture(writer, provider_key="flow")
        refs = list(_runtime_refs(ir))
        if not refs:
            pytest.skip("fixture ShotIR has no references")
        refs[0] = refs[0].model_copy(update={"role": refs[0].role + ".drift"})
        with pytest.raises(ProviderAdapterGateBlocked, match="role mismatch"):
            await ProviderAdapterPreflight(writer).prepare(
                ProviderAdapterPrepareRequest(
                    project_id=PROJECT_ID,
                    shot_ir_ref=ir.ref,
                    routing_decision_ref=decision.ref,
                    mode=ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
                    runtime_references=tuple(refs),
                    execution_as_of=NOW,
                )
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_provider_execution_plan_rejects_duplicate_exact_reference_assets(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, _, decision = await _selected_route_fixture(writer, provider_key="flow")
        plan = await ProviderAdapterPreflight(writer).prepare(
            ProviderAdapterPrepareRequest(
                project_id=PROJECT_ID,
                shot_ir_ref=ir.ref,
                routing_decision_ref=decision.ref,
                mode=ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
                runtime_references=_runtime_refs(ir),
                execution_as_of=NOW,
            )
        )
        if not plan.runtime_references:
            pytest.skip("fixture ShotIR has no references")
        payload = plan.model_dump(mode="python")
        payload["runtime_references"] = (
            plan.runtime_references[0],
            plan.runtime_references[0],
        )
        with pytest.raises(ValueError, match="must not duplicate exact ReferenceAsset refs"):
            ProviderExecutionPlan.model_validate(payload)
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_omni_first_last_uses_explicit_roles_not_sorted_asset_order():
    end_ref = RuntimeReferenceBinding(
        asset_ref=VersionRef(
            logical_id=LogicalId("reference-asset:a-end"),
            version_id=VersionId("ref-v1"),
        ),
        content_hash="sha256:" + "a" * 64,
        role="frame.end",
        media_id="media-end",
    )
    start_ref = RuntimeReferenceBinding(
        asset_ref=VersionRef(
            logical_id=LogicalId("reference-asset:z-start"),
            version_id=VersionId("ref-v1"),
        ),
        content_hash="sha256:" + "b" * 64,
        role="frame.start",
        media_id="media-start",
    )
    plan = _direct_omni_plan(
        (end_ref, start_ref),
        mode=ProviderExecutionMode.FIRST_LAST_FRAME_TO_VIDEO,
    )
    stub = _OmniStub()
    result = await _omni_adapter(stub).submit(plan, observed_at=NOW)
    assert result.state is ProviderObservationState.ACCEPTED
    assert stub.first_last_kwargs is not None
    assert stub.first_last_kwargs["start_image_media_id"] == "media-start"
    assert stub.first_last_kwargs["end_image_media_id"] == "media-end"
    assert stub.submit_calls == 1


@pytest.mark.asyncio
async def test_omni_first_last_without_explicit_start_end_roles_is_unsupported():
    first = RuntimeReferenceBinding(
        asset_ref=VersionRef(
            logical_id=LogicalId("reference-asset:a"),
            version_id=VersionId("ref-v1"),
        ),
        content_hash="sha256:" + "c" * 64,
        role="identity.face",
        media_id="media-a",
    )
    second = RuntimeReferenceBinding(
        asset_ref=VersionRef(
            logical_id=LogicalId("reference-asset:b"),
            version_id=VersionId("ref-v1"),
        ),
        content_hash="sha256:" + "d" * 64,
        role="identity.full_body",
        media_id="media-b",
    )
    plan = _direct_omni_plan(
        (first, second),
        mode=ProviderExecutionMode.FIRST_LAST_FRAME_TO_VIDEO,
    )
    stub = _OmniStub()
    result = await _omni_adapter(stub).submit(plan, observed_at=NOW)
    assert result.state is ProviderObservationState.UNSUPPORTED
    assert result.side_effect_may_have_occurred is False
    assert stub.submit_calls == 0


@pytest.mark.asyncio
async def test_preflight_rejects_runtime_mode_not_proven_by_exact_route(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, _, decision = await _selected_route_fixture(writer, provider_key="flow")
        with pytest.raises(ProviderAdapterGateBlocked, match="execution.mode"):
            await ProviderAdapterPreflight(writer).prepare(
                ProviderAdapterPrepareRequest(
                    project_id=PROJECT_ID,
                    shot_ir_ref=ir.ref,
                    routing_decision_ref=decision.ref,
                    mode=ProviderExecutionMode.REFERENCES_TO_VIDEO,
                    runtime_references=_runtime_refs(ir),
                    execution_as_of=NOW,
                )
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_preflight_rejects_runtime_resolution_not_proven_by_exact_route(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, _, decision = await _selected_route_fixture(writer, provider_key="flow")
        with pytest.raises(ProviderAdapterGateBlocked, match="output.resolution"):
            await ProviderAdapterPreflight(writer).prepare(
                ProviderAdapterPrepareRequest(
                    project_id=PROJECT_ID,
                    shot_ir_ref=ir.ref,
                    routing_decision_ref=decision.ref,
                    mode=ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
                    runtime_references=_runtime_refs(ir),
                    resolution="1080p",
                    execution_as_of=NOW,
                )
            )
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_flow_adapter_blocks_actual_transport_model_mismatch_before_side_effect(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, profile, decision = await _selected_route_fixture(writer, provider_key="flow")
        plan = await ProviderAdapterPreflight(writer).prepare(
            ProviderAdapterPrepareRequest(
                project_id=PROJECT_ID,
                shot_ir_ref=ir.ref,
                routing_decision_ref=decision.ref,
                mode=ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
                runtime_references=_runtime_refs(ir),
                execution_as_of=NOW,
            )
        )
        stub = _FlowStub()
        stub.transport_model = "different-live-flow-model"
        result = await _flow_adapter(stub, profile, ir).submit(plan, observed_at=NOW)
        assert result.state is ProviderObservationState.UNSUPPORTED
        assert result.side_effect_may_have_occurred is False
        assert stub.submit_calls == 0
        assert stub.model_calls
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_flow_adapter_blocks_unbound_duration_resolution_before_side_effect(tmp_path):
    writer = SQLiteWriteOwner(tmp_path / "studio.db")
    await writer.start()
    try:
        _, ir, profile, decision = await _selected_route_fixture(writer, provider_key="flow")
        plan = await ProviderAdapterPreflight(writer).prepare(
            ProviderAdapterPrepareRequest(
                project_id=PROJECT_ID,
                shot_ir_ref=ir.ref,
                routing_decision_ref=decision.ref,
                mode=ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
                runtime_references=_runtime_refs(ir),
                execution_as_of=NOW,
            )
        )
        drifted = _replace_plan(plan, duration_seconds=plan.duration_seconds - 2)
        stub = _FlowStub()
        result = await _flow_adapter(stub, profile, ir).submit(drifted, observed_at=NOW)
        assert result.state is ProviderObservationState.UNSUPPORTED
        assert result.side_effect_may_have_occurred is False
        assert stub.submit_calls == 0
        assert stub.model_calls == []
    finally:
        await writer.close()


@pytest.mark.asyncio
async def test_omni_adapter_blocks_mode_model_lowering_mismatch_before_side_effect():
    plan = _direct_omni_plan((), mode=ProviderExecutionMode.TEXT_TO_VIDEO)
    wrong_but_supported_model = _omni_fixture_model(
        ProviderExecutionMode.FIRST_FRAME_TO_VIDEO,
        duration=plan.duration_seconds,
        resolution=plan.resolution,
    )
    drifted = _replace_plan(plan, model_version=wrong_but_supported_model)
    stub = _OmniStub()
    result = await _omni_adapter(stub).submit(drifted, observed_at=NOW)
    assert result.state is ProviderObservationState.UNSUPPORTED
    assert result.side_effect_may_have_occurred is False
    assert stub.submit_calls == 0
