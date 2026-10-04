"""IMP-051 provider adapter anti-corruption contracts and canonical preflight.

This module is intentionally provider neutral.  It validates exact-current
ShotIR + ProviderRoutingDecision authority and produces an ephemeral derivative
execution plan.  Concrete Flow/Omni transports live under ``agent.services``.
No provider request/response payload becomes canonical Studio truth here.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .primitives import LogicalId, VersionRef
from .production_compiler import ProductionCompilerRepository, ShotIR
from .provider_routing import (
    ProviderCapabilityRoutingRepository,
    ProviderProfile,
    ProviderRoutingDecision,
    ProviderRoutingGateBlocked,
    RequirementOperator,
)
from .persistence import SQLiteWriteOwner


def _trimmed(value: str, label: str) -> str:
    value = str(value).strip()
    if not value:
        raise ValueError(f"{label} must be non-empty")
    return value


def _canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(value) -> str:
    raw = _canonical_json(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return ref.logical_id.root, ref.version_id.root


class ProviderAdapterError(ValueError):
    """Base IMP-051 anti-corruption error."""


class ProviderAdapterGateBlocked(ProviderAdapterError):
    """Canonical preflight failed before any remote side effect."""


class ProviderAdapterUnsupported(ProviderAdapterError):
    """Requested provider/mode is explicitly unsupported."""


class ProviderExecutionMode(str, Enum):
    TEXT_TO_VIDEO = "TEXT_TO_VIDEO"
    FIRST_FRAME_TO_VIDEO = "FIRST_FRAME_TO_VIDEO"
    FIRST_LAST_FRAME_TO_VIDEO = "FIRST_LAST_FRAME_TO_VIDEO"
    REFERENCES_TO_VIDEO = "REFERENCES_TO_VIDEO"


class ProviderHandleKind(str, Enum):
    OPERATION = "OPERATION"
    WORKFLOW = "WORKFLOW"


class ProviderObservationKind(str, Enum):
    SUBMIT = "SUBMIT"
    POLL = "POLL"
    CANCEL = "CANCEL"
    RECONCILE = "RECONCILE"


class ProviderObservationState(str, Enum):
    ACCEPTED = "ACCEPTED"
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"


class RuntimeReferenceBinding(BaseModel):
    """Ephemeral provider media binding for one exact canonical ReferenceAsset."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    asset_ref: VersionRef
    content_hash: str
    role: str
    media_id: str

    @field_validator("role", "media_id")
    @classmethod
    def normalize_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("content_hash")
    @classmethod
    def validate_hash(cls, value: str) -> str:
        value = str(value).strip().lower()
        if not value.startswith("sha256:") or len(value) != 71:
            raise ValueError("content_hash must be sha256:<64 lowercase hex>")
        try:
            int(value[7:], 16)
        except ValueError as exc:
            raise ValueError("content_hash must be sha256:<64 lowercase hex>") from exc
        return value


class ProviderAdapterPrepareRequest(BaseModel):
    """Ephemeral execution intent; does not create GenerationJob authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    shot_ir_ref: VersionRef
    routing_decision_ref: VersionRef
    mode: ProviderExecutionMode
    runtime_references: tuple[RuntimeReferenceBinding, ...] = ()
    resolution: str = "720p"
    execution_as_of: datetime

    @field_validator("resolution")
    @classmethod
    def normalize_resolution(cls, value: str) -> str:
        return _trimmed(value, "resolution").lower()

    @field_validator("runtime_references")
    @classmethod
    def normalize_refs(
        cls, values: tuple[RuntimeReferenceBinding, ...]
    ) -> tuple[RuntimeReferenceBinding, ...]:
        keys = [_ref_key(value.asset_ref) for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("runtime_references must not duplicate exact ReferenceAsset refs")
        return tuple(sorted(values, key=lambda value: (_ref_key(value.asset_ref), value.role)))

    @model_validator(mode="after")
    def validate_request(self) -> "ProviderAdapterPrepareRequest":
        if self.execution_as_of.tzinfo is None:
            raise ValueError("execution_as_of must be timezone-aware")
        if not self.shot_ir_ref.logical_id.root.startswith("shot-ir:"):
            raise ValueError("shot_ir_ref must reference ShotIR")
        if not self.routing_decision_ref.logical_id.root.startswith("provider-route:"):
            raise ValueError("routing_decision_ref must reference ProviderRoutingDecision")
        return self


class ProviderExecutionPlan(BaseModel):
    """Provider-neutral derivative plan consumed by concrete adapters."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    shot_ir_ref: VersionRef
    routing_decision_ref: VersionRef
    provider_profile_ref: VersionRef
    provider_key: str
    surface: str
    model_family: str
    model_version: str
    mode: ProviderExecutionMode
    prompt: str
    duration_seconds: int = Field(gt=0)
    aspect_ratio: str
    resolution: str
    runtime_references: tuple[RuntimeReferenceBinding, ...] = ()
    plan_hash: str

    @field_validator(
        "provider_key",
        "surface",
        "model_family",
        "model_version",
        "prompt",
        "aspect_ratio",
        "resolution",
    )
    @classmethod
    def normalize_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("runtime_references")
    @classmethod
    def normalize_runtime_refs(
        cls, values: tuple[RuntimeReferenceBinding, ...]
    ) -> tuple[RuntimeReferenceBinding, ...]:
        keys = [_ref_key(value.asset_ref) for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("runtime_references must not duplicate exact ReferenceAsset refs")
        return tuple(sorted(values, key=lambda value: (_ref_key(value.asset_ref), value.role)))

    @model_validator(mode="after")
    def validate_hash(self) -> "ProviderExecutionPlan":
        if self.plan_hash != self.compute_hash():
            raise ValueError("plan_hash does not match exact derivative execution plan")
        return self

    def compute_hash(self) -> str:
        return _hash(self.model_dump(mode="json", exclude={"plan_hash"}))


class ProviderTransportHandle(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_key: str
    kind: ProviderHandleKind
    handle_id: str
    project_handle: str | None = None
    primary_media_id: str | None = None

    @field_validator("provider_key", "handle_id")
    @classmethod
    def normalize_required(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("project_handle", "primary_media_id")
    @classmethod
    def normalize_optional(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        return _trimmed(value, info.field_name)


class ProviderTransportObservation(BaseModel):
    """Normalized runtime evidence; never canonical GenerationJob state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_key: str
    kind: ProviderObservationKind
    state: ProviderObservationState
    observed_at: datetime
    handle: ProviderTransportHandle | None = None
    output_media_id: str | None = None
    output_url: str | None = None
    error_class: str | None = None
    message: str | None = None
    side_effect_may_have_occurred: bool = False
    retry_safe: bool = False

    @field_validator("provider_key")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        return _trimmed(value, "provider_key")

    @field_validator("output_media_id", "output_url", "error_class", "message")
    @classmethod
    def normalize_optional(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_safety(self) -> "ProviderTransportObservation":
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if self.state is ProviderObservationState.AMBIGUOUS and self.retry_safe:
            raise ValueError("AMBIGUOUS observation can never authorize retry")
        if self.side_effect_may_have_occurred and self.retry_safe:
            raise ValueError("possible remote side effect cannot be marked retry_safe")
        if self.state in {ProviderObservationState.ACCEPTED, ProviderObservationState.PENDING} and self.handle is None:
            raise ValueError("accepted/pending observation requires provider handle")
        if self.state is ProviderObservationState.SUCCEEDED and not (
            self.output_media_id or self.output_url
        ):
            raise ValueError("SUCCEEDED observation requires output media evidence")
        return self


@runtime_checkable
class ProviderAdapterPort(Protocol):
    provider_key: str

    async def submit(self, plan: ProviderExecutionPlan, *, observed_at: datetime) -> ProviderTransportObservation:
        ...

    async def poll(
        self,
        handle: ProviderTransportHandle,
        *,
        observed_at: datetime,
    ) -> ProviderTransportObservation:
        ...

    async def cancel(
        self,
        handle: ProviderTransportHandle,
        *,
        observed_at: datetime,
    ) -> ProviderTransportObservation:
        ...

    async def reconcile(
        self,
        handle: ProviderTransportHandle | None,
        *,
        observed_at: datetime,
    ) -> ProviderTransportObservation:
        ...


class ProviderAdapterPreflight:
    """Side-effect-free canonical guard before any provider transport call."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.routing = ProviderCapabilityRoutingRepository(writer)
        self.compiler = ProductionCompilerRepository(writer)

    async def prepare(self, request: ProviderAdapterPrepareRequest) -> ProviderExecutionPlan:
        try:
            decision = await self.routing.assert_selected_route(
                request.routing_decision_ref,
                as_of=request.execution_as_of,
            )
        except ProviderRoutingGateBlocked as exc:
            raise ProviderAdapterGateBlocked(str(exc)) from exc

        if decision.project_id != request.project_id:
            raise ProviderAdapterGateBlocked("routing decision belongs to a different project")
        if decision.shot_ir_ref != request.shot_ir_ref:
            raise ProviderAdapterGateBlocked("routing decision does not bind exact requested ShotIR")
        if decision.selected_profile_ref is None:
            raise ProviderAdapterGateBlocked("routing decision has no selected ProviderProfile")

        self._assert_routing_pin(decision, key="execution.mode", value=request.mode.value)
        self._assert_routing_pin(decision, key="output.resolution", value=request.resolution)

        ir_artifact = await self.compiler.get_shot_ir(request.shot_ir_ref)
        if ir_artifact is None:
            raise ProviderAdapterGateBlocked("ShotIR exact version does not exist")
        shot_ir = ir_artifact.value
        if not isinstance(shot_ir, ShotIR):
            raise ProviderAdapterGateBlocked("ShotIR payload type mismatch")
        if shot_ir.project_id != request.project_id:
            raise ProviderAdapterGateBlocked("ShotIR belongs to a different project")

        profile_artifact = await self.routing.get_provider_profile(decision.selected_profile_ref)
        if profile_artifact is None:
            raise ProviderAdapterGateBlocked("selected ProviderProfile exact version does not exist")
        profile = profile_artifact.value
        if not isinstance(profile, ProviderProfile):
            raise ProviderAdapterGateBlocked("selected provider profile payload type mismatch")

        runtime_map = {_ref_key(item.asset_ref): item for item in request.runtime_references}
        ir_ref_map = {_ref_key(item.asset_ref): item for item in shot_ir.reference_bindings}
        if set(runtime_map) != set(ir_ref_map):
            missing = sorted(set(ir_ref_map) - set(runtime_map))
            extra = sorted(set(runtime_map) - set(ir_ref_map))
            raise ProviderAdapterGateBlocked(
                f"runtime reference set must exactly match ShotIR bindings; missing={missing} extra={extra}"
            )
        for key, binding in ir_ref_map.items():
            runtime = runtime_map[key]
            if runtime.content_hash != binding.content_hash:
                raise ProviderAdapterGateBlocked(
                    f"runtime reference content hash mismatch for {binding.asset_ref.logical_id.root}"
                )
            if runtime.role != binding.role:
                raise ProviderAdapterGateBlocked(
                    f"runtime reference role mismatch for {binding.asset_ref.logical_id.root}"
                )

        aspect_ratio = self._constraint_value(shot_ir, "output.aspect_ratio", default="16:9")
        prompt = self._render_prompt(shot_ir)
        plan = ProviderExecutionPlan.model_construct(
            project_id=request.project_id,
            shot_ir_ref=shot_ir.ref,
            routing_decision_ref=decision.ref,
            provider_profile_ref=profile.ref,
            provider_key=profile.provider_key,
            surface=profile.surface,
            model_family=profile.model_family,
            model_version=profile.model_version,
            mode=request.mode,
            prompt=prompt,
            duration_seconds=shot_ir.motion_delta.duration_seconds,
            aspect_ratio=str(aspect_ratio),
            resolution=request.resolution,
            runtime_references=request.runtime_references,
            plan_hash="sha256:" + "0" * 64,
        )
        payload = plan.model_dump(mode="python")
        payload["plan_hash"] = plan.compute_hash()
        return ProviderExecutionPlan.model_validate(payload)

    @staticmethod
    def _assert_routing_pin(
        decision: ProviderRoutingDecision,
        *,
        key: str,
        value: str,
    ) -> None:
        matches = [requirement for requirement in decision.requirements if requirement.key == key]
        if not any(
            requirement.operator in {RequirementOperator.EQUALS, RequirementOperator.CONTAINS}
            and requirement.expected_value == value
            for requirement in matches
        ):
            raise ProviderAdapterGateBlocked(
                f"runtime {key}={value!r} was not proven by exact routing requirements"
            )

    @staticmethod
    def _constraint_value(shot_ir: ShotIR, key: str, *, default):
        for item in shot_ir.execution_constraints:
            if item.key == key:
                return json.loads(item.value_json)
        return default

    @staticmethod
    def _render_prompt(shot_ir: ShotIR) -> str:
        lines: list[str] = []
        for layer in shot_ir.semantic_layers:
            fields = "; ".join(f"{field.key}: {field.value}" for field in layer.fields)
            lines.append(f"{layer.layer.value} | {fields}")
        lines.extend(
            [
                f"STATIC_STATE | {shot_ir.static_state.state_summary}",
                f"COMPOSITION | {shot_ir.static_state.composition}",
                f"VISIBLE_PERFORMANCE | {shot_ir.static_state.visible_performance}",
                f"ENVIRONMENT_STATE | {shot_ir.static_state.environment_state}",
                f"LIGHTING_STATE | {shot_ir.static_state.lighting_state}",
                f"MOTION_ACTION | {shot_ir.motion_delta.action_delta}",
                f"MOTION_PERFORMANCE | {shot_ir.motion_delta.performance_delta}",
                f"MOTION_BLOCKING | {shot_ir.motion_delta.blocking_delta}",
                f"MOTION_CAMERA | {shot_ir.motion_delta.camera_movement_delta}",
                "CONTINUITY | " + "; ".join(shot_ir.motion_delta.continuity_requirements),
            ]
        )
        return "\n".join(lines)
