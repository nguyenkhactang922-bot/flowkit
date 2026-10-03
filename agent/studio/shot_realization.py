"""IMP-032 provider-neutral Shot eligibility and realization boundary.

Canonical authority rules:
- ShotListItem remains the sole origin of canonical shot_id under ADR-0020.
- ShotEligibilityGate is immutable exact-input evidence; only a current ELIGIBLE gate
  may authorize FullShotSpec.
- FullShotSpec realizes the same shot_id with exactly eight semantic layers L1-L8.
- StaticKeyframeSpec is observable start/keyframe state only.
- MotionDeltaSpec is temporal delta from one exact static/start state only.
- ShotDecisionTrace is immutable explainability evidence, never Shot truth.
- State/Reference/Profile/Directing authority is referenced, never copied into a
  competing canonical store.
- Provider/runtime/network request syntax is deliberately absent from this module.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import Enum
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .active_profile import ActiveProductionProfile, ActiveProductionProfileRepository
from .directing import (
    BlockingPlan,
    CinematographyObjective,
    DirectingAuthorityRepository,
    DirectingIntent,
    SceneSpatialDramaticContract,
)
from .invalidation import (
    DependencyGraphRepository,
    InvalidationRecord,
    InvalidationRepository,
)
from .narrative_trace import (
    NarrativeArtifactType,
    NarrativeTraceRepository,
    NarrativeTraceState,
)
from .persistence import SQLiteWriteOwner
from .primitives import (
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    VersionId,
    VersionRef,
)
from .reference import ReferenceAsset, ReferenceResolutionTrace, ReferenceResolver
from .shot_planning import ShotListItem, ShotListManifest, ShotPlanningRepository
from .state_continuity import StateSnapshotRepository
from .versioning import CurrentVersionPointer, VersionRepository


_ACCEPTED = {LifecycleState.APPROVED, LifecycleState.LOCKED}
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")
_GENERIC_CINEMATIC = {
    "cinematic",
    "looks cinematic",
    "make it cinematic",
    "more cinematic",
    "cinematic look",
}


class ShotRealizationError(ValueError):
    """Base IMP-032 error."""


class ShotRealizationIdentityError(ShotRealizationError):
    """Raised when a realization record attempts parallel/contradictory identity."""


class ShotEligibilityBlocked(ShotRealizationError):
    """Raised when exact eligibility authority is missing/stale/invalid."""


class ShotRealizationGateBlocked(ShotRealizationError):
    """Raised when FullShotSpec/static/motion/trace hard gates fail closed."""


class ShotEligibilityVerdict(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    REJECTED = "REJECTED"


class SemanticAuthorityClass(str, Enum):
    FIXED = "FIXED"
    INHERITED = "INHERITED"
    VARIABLE = "VARIABLE"


class ShotSemanticLayer(str, Enum):
    L1_SUBJECT = "L1_SUBJECT"
    L2_STATE_WARDROBE = "L2_STATE_WARDROBE"
    L3_ACTION_PERFORMANCE = "L3_ACTION_PERFORMANCE"
    L4_ENVIRONMENT = "L4_ENVIRONMENT"
    L5_TIME_ATMOSPHERE = "L5_TIME_ATMOSPHERE"
    L6_CAMERA = "L6_CAMERA"
    L7_LIGHTING_STYLE = "L7_LIGHTING_STYLE"
    L8_CONTINUITY = "L8_CONTINUITY"


_LAYER_ORDER = {layer: index for index, layer in enumerate(ShotSemanticLayer)}


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _optional_trimmed(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    return _trimmed(value, label)


def _key(value: str, label: str) -> str:
    normalized = _trimmed(value, label).lower()
    if not _KEY_RE.fullmatch(normalized):
        raise ValueError(
            f"{label} must start with lowercase letter/digit and use only lowercase letters, "
            "digits, '.', '_' or '-'"
        )
    return normalized


def _unique_text(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    normalized = tuple(_trimmed(value, label) for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{label} must not contain duplicates")
    return normalized


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return ref.logical_id.root, ref.version_id.root


def _unique_refs(values: tuple[VersionRef, ...], label: str) -> tuple[VersionRef, ...]:
    keys = [_ref_key(value) for value in values]
    if len(keys) != len(set(keys)):
        raise ValueError(f"{label} must not contain duplicate exact refs")
    return tuple(sorted(values, key=_ref_key))


def _digest(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:32]


def _hash_payload(payload: object) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _project_ref(
    ref: VersionRef,
    *,
    prefix: str,
    project_id: LogicalId,
    label: str,
) -> None:
    base = f"{prefix}{project_id.root}"
    root = ref.logical_id.root
    if root != base and not root.startswith(base + ":"):
        raise ValueError(f"{label} must belong to the same project and use {prefix} identity")


def _active_profile_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"active-profile:{project_id.root}")


def shot_eligibility_gate_logical_id(project_id: LogicalId, shot_id: LogicalId) -> LogicalId:
    return LogicalId(
        f"shot-eligibility-gate:{project_id.root}:" + _digest(project_id.root, shot_id.root)
    )


def full_shot_spec_logical_id(project_id: LogicalId, shot_id: LogicalId) -> LogicalId:
    return LogicalId(
        f"full-shot-spec:{project_id.root}:" + _digest(project_id.root, shot_id.root)
    )


def static_keyframe_spec_logical_id(project_id: LogicalId, shot_id: LogicalId) -> LogicalId:
    return LogicalId(
        f"static-keyframe-spec:{project_id.root}:" + _digest(project_id.root, shot_id.root)
    )


def motion_delta_spec_logical_id(project_id: LogicalId, shot_id: LogicalId) -> LogicalId:
    return LogicalId(
        f"motion-delta-spec:{project_id.root}:" + _digest(project_id.root, shot_id.root)
    )


def shot_decision_trace_logical_id(project_id: LogicalId, shot_id: LogicalId) -> LogicalId:
    return LogicalId(
        f"shot-decision-trace:{project_id.root}:" + _digest(project_id.root, shot_id.root)
    )


class ResolvedReferenceEvidence(BaseModel):
    """Provider-neutral exact ReferenceAsset evidence persisted by IMP-032."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    asset_ref: VersionRef
    entity_ref: VersionRef
    role: str
    content_hash: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        return _trimmed(value, "reference role")

    @field_validator("content_hash")
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("content_hash must be sha256:<64 lowercase hex>")
        return value

    @model_validator(mode="after")
    def validate_refs(self) -> "ResolvedReferenceEvidence":
        if not self.asset_ref.logical_id.root.startswith("reference-asset:"):
            raise ValueError("asset_ref must reference canonical ReferenceAsset")
        if not self.entity_ref.logical_id.root.startswith("entity:"):
            raise ValueError("entity_ref must reference canonical EntityVersion")
        return self


class EligibilityFinding(BaseModel):
    """Provider-neutral eligibility finding; blocking disposition is explicit evidence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    blocking: bool
    message: str
    source_refs: tuple[VersionRef, ...] = Field(min_length=1)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        value = _trimmed(value, "finding code").upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", value):
            raise ValueError("finding code must be uppercase underscore token")
        return value

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        return _trimmed(value, "finding message")

    @field_validator("source_refs")
    @classmethod
    def normalize_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        return _unique_refs(values, "finding source_refs")


class ShotEligibilityGate(BaseModel):
    """Immutable exact-input verdict/evidence for one existing canonical shot_id."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    shot_eligibility_gate_id: LogicalId
    version_id: VersionId
    shot_ref: VersionRef
    shot_narrative_trace_ref: VersionRef
    shot_list_manifest_ref: VersionRef
    active_profile_ref: VersionRef
    directing_intent_ref: VersionRef
    spatial_contract_ref: VersionRef
    blocking_plan_ref: VersionRef
    cinematography_objective_ref: VersionRef
    state_snapshot_ref: VersionRef
    approved_state_designation_ref: VersionRef
    reference_evidence: tuple[ResolvedReferenceEvidence, ...] = ()
    required_reference_entity_refs: tuple[VersionRef, ...] = ()
    reference_resolution_hash: str
    rule_version: VersionRef
    evaluated_input_hash: str
    verdict: ShotEligibilityVerdict
    findings: tuple[EligibilityFinding, ...] = ()

    @field_validator("reference_evidence")
    @classmethod
    def normalize_reference_evidence(
        cls,
        values: tuple[ResolvedReferenceEvidence, ...],
    ) -> tuple[ResolvedReferenceEvidence, ...]:
        refs = [_ref_key(item.asset_ref) for item in values]
        if len(refs) != len(set(refs)):
            raise ValueError("reference_evidence must not duplicate exact ReferenceAsset refs")
        return tuple(sorted(values, key=lambda item: _ref_key(item.asset_ref)))

    @field_validator("findings")
    @classmethod
    def normalize_findings(
        cls,
        values: tuple[EligibilityFinding, ...],
    ) -> tuple[EligibilityFinding, ...]:
        keys = [(value.code, value.message) for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("eligibility findings must not duplicate code/message")
        return tuple(sorted(values, key=lambda item: (item.code, item.message)))

    @field_validator("required_reference_entity_refs")
    @classmethod
    def normalize_required_reference_entities(
        cls, values: tuple[VersionRef, ...]
    ) -> tuple[VersionRef, ...]:
        values = _unique_refs(values, "required_reference_entity_refs")
        for ref in values:
            if not ref.logical_id.root.startswith("entity:"):
                raise ValueError("required_reference_entity_refs must reference EntityVersion")
        return values

    @field_validator("evaluated_input_hash", "reference_resolution_hash")
    @classmethod
    def validate_input_hash(cls, value: str, info) -> str:
        if not _SHA256_RE.fullmatch(value):
            raise ValueError(f"{info.field_name} must be sha256:<64 lowercase hex>")
        return value

    @model_validator(mode="after")
    def validate_authority(self) -> "ShotEligibilityGate":
        _project_ref(
            self.shot_ref,
            prefix="shot-list-item:",
            project_id=self.project_id,
            label="shot_ref",
        )
        if not self.shot_narrative_trace_ref.logical_id.root.startswith("narrative-trace:"):
            raise ValueError("shot_narrative_trace_ref must reference NarrativeTrace")
        _project_ref(
            self.shot_list_manifest_ref,
            prefix="shot-list-manifest:",
            project_id=self.project_id,
            label="shot_list_manifest_ref",
        )
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        for ref, prefix, label in (
            (self.directing_intent_ref, "directing-intent:", "directing_intent_ref"),
            (self.spatial_contract_ref, "scene-spatial-contract:", "spatial_contract_ref"),
            (self.blocking_plan_ref, "blocking-plan:", "blocking_plan_ref"),
            (
                self.cinematography_objective_ref,
                "cinematography-objective:",
                "cinematography_objective_ref",
            ),
            (self.state_snapshot_ref, "state-snapshot:", "state_snapshot_ref"),
            (
                self.approved_state_designation_ref,
                "approved-end-state:",
                "approved_state_designation_ref",
            ),
        ):
            _project_ref(ref, prefix=prefix, project_id=self.project_id, label=label)
        expected = shot_eligibility_gate_logical_id(
            self.project_id,
            self.shot_ref.logical_id,
        )
        if self.shot_eligibility_gate_id != expected:
            raise ValueError(f"shot_eligibility_gate_id must be {expected.root}")
        blocking = any(item.blocking for item in self.findings)
        if self.verdict is ShotEligibilityVerdict.ELIGIBLE and blocking:
            raise ValueError("ELIGIBLE verdict cannot contain blocking findings")
        if self.verdict is ShotEligibilityVerdict.REJECTED and not blocking:
            raise ValueError("REJECTED verdict requires at least one blocking finding")
        allowed = {_ref_key(binding.source) for binding in self.source_bindings()}
        if any(
            _ref_key(ref) not in allowed
            for finding in self.findings
            for ref in finding.source_refs
        ):
            raise ValueError("eligibility finding may cite declared evaluated inputs only")
        expected_hash = self.compute_evaluated_input_hash()
        if self.evaluated_input_hash != expected_hash:
            raise ValueError("evaluated_input_hash does not match exact evaluated inputs")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.shot_eligibility_gate_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="shot_list_item", source=self.shot_ref),
            SourceVersionBinding(role="shot_narrative_trace", source=self.shot_narrative_trace_ref),
            SourceVersionBinding(role="shot_list_manifest", source=self.shot_list_manifest_ref),
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="directing_intent", source=self.directing_intent_ref),
            SourceVersionBinding(role="scene_spatial_dramatic_contract", source=self.spatial_contract_ref),
            SourceVersionBinding(role="blocking_plan", source=self.blocking_plan_ref),
            SourceVersionBinding(
                role="cinematography_objective",
                source=self.cinematography_objective_ref,
            ),
            SourceVersionBinding(role="state_snapshot", source=self.state_snapshot_ref),
            SourceVersionBinding(
                role="approved_state_designation",
                source=self.approved_state_designation_ref,
            ),
            SourceVersionBinding(role="eligibility_rule", source=self.rule_version),
        ]
        values.extend(
            SourceVersionBinding(role=f"required_reference_entity_{index:03d}", source=ref)
            for index, ref in enumerate(self.required_reference_entity_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"selected_reference_{index:03d}", source=item.asset_ref)
            for index, item in enumerate(self.reference_evidence)
        )
        return tuple(values)

    def compute_evaluated_input_hash(self) -> str:
        return _hash_payload(
            {
                "source_bindings": [
                    {
                        "role": binding.role,
                        "logical_id": binding.source.logical_id.root,
                        "version_id": binding.source.version_id.root,
                    }
                    for binding in self.source_bindings()
                ],
                "reference_evidence": [item.model_dump(mode="json") for item in self.reference_evidence],
                "reference_resolution_hash": self.reference_resolution_hash,
                "rule_version": self.rule_version.model_dump(mode="json"),
            }
        )


class SemanticField(BaseModel):
    """One FullShotSpec semantic field with explicit authority class + provenance refs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    value: str
    authority_class: SemanticAuthorityClass
    source_refs: tuple[VersionRef, ...] = Field(min_length=1)

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        return _key(value, "semantic field key")

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        return _trimmed(value, "semantic field value")

    @field_validator("source_refs")
    @classmethod
    def normalize_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        return _unique_refs(values, "semantic field source_refs")


class SemanticLayerSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    layer: ShotSemanticLayer
    fields: tuple[SemanticField, ...] = Field(min_length=1)

    @field_validator("fields")
    @classmethod
    def normalize_fields(cls, values: tuple[SemanticField, ...]) -> tuple[SemanticField, ...]:
        keys = [value.key for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("semantic layer field keys must be unique")
        return tuple(sorted(values, key=lambda value: value.key))


class FullShotSpec(BaseModel):
    """Complete provider-neutral realization of one existing canonical shot_id."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    full_shot_spec_id: LogicalId
    version_id: VersionId
    shot_ref: VersionRef
    eligibility_gate_ref: VersionRef
    active_profile_ref: VersionRef
    directing_intent_ref: VersionRef
    spatial_contract_ref: VersionRef
    blocking_plan_ref: VersionRef
    cinematography_objective_ref: VersionRef
    state_snapshot_ref: VersionRef
    approved_state_designation_ref: VersionRef
    reference_evidence: tuple[ResolvedReferenceEvidence, ...] = ()
    duration_seconds: int = Field(gt=0)
    layers: tuple[SemanticLayerSpec, ...] = Field(min_length=8, max_length=8)
    transition_intent: str | None = None
    audio_intent: str | None = None

    @field_validator("reference_evidence")
    @classmethod
    def normalize_reference_evidence(
        cls,
        values: tuple[ResolvedReferenceEvidence, ...],
    ) -> tuple[ResolvedReferenceEvidence, ...]:
        refs = [_ref_key(item.asset_ref) for item in values]
        if len(refs) != len(set(refs)):
            raise ValueError("FullShotSpec reference_evidence must be unique")
        return tuple(sorted(values, key=lambda item: _ref_key(item.asset_ref)))

    @field_validator("transition_intent", "audio_intent")
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return _optional_trimmed(value, info.field_name)

    @field_validator("layers")
    @classmethod
    def normalize_layers(
        cls,
        values: tuple[SemanticLayerSpec, ...],
    ) -> tuple[SemanticLayerSpec, ...]:
        layers = [value.layer for value in values]
        if len(layers) != len(set(layers)) or set(layers) != set(ShotSemanticLayer):
            raise ValueError("FullShotSpec must contain exactly one of each canonical semantic layer L1-L8")
        return tuple(sorted(values, key=lambda value: _LAYER_ORDER[value.layer]))

    @model_validator(mode="after")
    def validate_authority(self) -> "FullShotSpec":
        _project_ref(
            self.shot_ref,
            prefix="shot-list-item:",
            project_id=self.project_id,
            label="shot_ref",
        )
        _project_ref(
            self.eligibility_gate_ref,
            prefix="shot-eligibility-gate:",
            project_id=self.project_id,
            label="eligibility_gate_ref",
        )
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        expected = full_shot_spec_logical_id(self.project_id, self.shot_ref.logical_id)
        if self.full_shot_spec_id != expected:
            raise ValueError(f"full_shot_spec_id must be {expected.root}")
        allowed = {_ref_key(binding.source) for binding in self.source_bindings()}
        for layer in self.layers:
            for field in layer.fields:
                if any(_ref_key(ref) not in allowed for ref in field.source_refs):
                    raise ValueError(
                        f"{layer.layer.value} field {field.key} may cite declared FullShotSpec inputs only"
                    )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.full_shot_spec_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="shot_list_item", source=self.shot_ref),
            SourceVersionBinding(role="shot_eligibility_gate", source=self.eligibility_gate_ref),
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="directing_intent", source=self.directing_intent_ref),
            SourceVersionBinding(role="scene_spatial_dramatic_contract", source=self.spatial_contract_ref),
            SourceVersionBinding(role="blocking_plan", source=self.blocking_plan_ref),
            SourceVersionBinding(
                role="cinematography_objective",
                source=self.cinematography_objective_ref,
            ),
            SourceVersionBinding(role="state_snapshot", source=self.state_snapshot_ref),
            SourceVersionBinding(
                role="approved_state_designation",
                source=self.approved_state_designation_ref,
            ),
        ]
        values.extend(
            SourceVersionBinding(role=f"selected_reference_{index:03d}", source=item.asset_ref)
            for index, item in enumerate(self.reference_evidence)
        )
        return tuple(values)


class StaticKeyframeSpec(BaseModel):
    """Observable start/keyframe state; intentionally contains no temporal delta field."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    static_keyframe_spec_id: LogicalId
    version_id: VersionId
    shot_ref: VersionRef
    full_shot_spec_ref: VersionRef
    state_snapshot_ref: VersionRef
    approved_state_designation_ref: VersionRef
    reference_asset_refs: tuple[VersionRef, ...] = ()
    visible_subject_refs: tuple[VersionRef, ...] = ()
    state_summary: str
    composition: str
    visible_performance: str
    environment_state: str
    lighting_state: str

    @field_validator("reference_asset_refs", "visible_subject_refs")
    @classmethod
    def normalize_refs(cls, values: tuple[VersionRef, ...], info) -> tuple[VersionRef, ...]:
        return _unique_refs(values, info.field_name)

    @field_validator(
        "state_summary",
        "composition",
        "visible_performance",
        "environment_state",
        "lighting_state",
    )
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_authority(self) -> "StaticKeyframeSpec":
        _project_ref(
            self.shot_ref,
            prefix="shot-list-item:",
            project_id=self.project_id,
            label="shot_ref",
        )
        _project_ref(
            self.full_shot_spec_ref,
            prefix="full-shot-spec:",
            project_id=self.project_id,
            label="full_shot_spec_ref",
        )
        expected = static_keyframe_spec_logical_id(self.project_id, self.shot_ref.logical_id)
        if self.static_keyframe_spec_id != expected:
            raise ValueError(f"static_keyframe_spec_id must be {expected.root}")
        for ref in self.reference_asset_refs:
            if not ref.logical_id.root.startswith("reference-asset:"):
                raise ValueError("reference_asset_refs must reference canonical ReferenceAsset")
        for ref in self.visible_subject_refs:
            if not ref.logical_id.root.startswith("entity:"):
                raise ValueError("visible_subject_refs must reference canonical EntityVersion")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.static_keyframe_spec_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="shot_list_item", source=self.shot_ref),
            SourceVersionBinding(role="full_shot_spec", source=self.full_shot_spec_ref),
            SourceVersionBinding(role="state_snapshot", source=self.state_snapshot_ref),
            SourceVersionBinding(
                role="approved_state_designation",
                source=self.approved_state_designation_ref,
            ),
        ]
        values.extend(
            SourceVersionBinding(role=f"reference_asset_{index:03d}", source=ref)
            for index, ref in enumerate(self.reference_asset_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"visible_subject_{index:03d}", source=ref)
            for index, ref in enumerate(self.visible_subject_refs)
        )
        return tuple(values)


class MotionDeltaSpec(BaseModel):
    """Temporal delta from one exact static/start state; never start-state authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    motion_delta_spec_id: LogicalId
    version_id: VersionId
    shot_ref: VersionRef
    full_shot_spec_ref: VersionRef
    static_keyframe_spec_ref: VersionRef
    duration_seconds: int = Field(gt=0)
    action_delta: str
    performance_delta: str
    blocking_delta: str
    camera_movement_delta: str
    continuity_requirements: tuple[str, ...] = Field(min_length=1)

    @field_validator(
        "action_delta",
        "performance_delta",
        "blocking_delta",
        "camera_movement_delta",
    )
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("continuity_requirements")
    @classmethod
    def normalize_requirements(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _unique_text(values, "continuity_requirements")

    @model_validator(mode="after")
    def validate_authority(self) -> "MotionDeltaSpec":
        _project_ref(
            self.shot_ref,
            prefix="shot-list-item:",
            project_id=self.project_id,
            label="shot_ref",
        )
        _project_ref(
            self.full_shot_spec_ref,
            prefix="full-shot-spec:",
            project_id=self.project_id,
            label="full_shot_spec_ref",
        )
        _project_ref(
            self.static_keyframe_spec_ref,
            prefix="static-keyframe-spec:",
            project_id=self.project_id,
            label="static_keyframe_spec_ref",
        )
        expected = motion_delta_spec_logical_id(self.project_id, self.shot_ref.logical_id)
        if self.motion_delta_spec_id != expected:
            raise ValueError(f"motion_delta_spec_id must be {expected.root}")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.motion_delta_spec_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return (
            SourceVersionBinding(role="shot_list_item", source=self.shot_ref),
            SourceVersionBinding(role="full_shot_spec", source=self.full_shot_spec_ref),
            SourceVersionBinding(role="static_keyframe_spec", source=self.static_keyframe_spec_ref),
        )


class ShotDecision(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    layer: ShotSemanticLayer
    decision: str
    rationale: str
    source_refs: tuple[VersionRef, ...] = Field(min_length=1)
    rejected_alternatives: tuple[str, ...] = ()

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, value: str) -> str:
        return _trimmed(value, "shot decision")

    @field_validator("rationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        value = _trimmed(value, "shot decision rationale")
        if value.lower().rstrip(".!?") in _GENERIC_CINEMATIC:
            raise ValueError("generic 'cinematic' is never sufficient ShotDecisionTrace rationale")
        return value

    @field_validator("source_refs")
    @classmethod
    def normalize_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        return _unique_refs(values, "shot decision source_refs")

    @field_validator("rejected_alternatives")
    @classmethod
    def normalize_alternatives(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _unique_text(values, "rejected_alternatives")


class ShotDecisionTrace(BaseModel):
    """Explainability evidence for one exact FullShotSpec version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    shot_decision_trace_id: LogicalId
    version_id: VersionId
    shot_ref: VersionRef
    full_shot_spec_ref: VersionRef
    eligibility_gate_ref: VersionRef
    decisions: tuple[ShotDecision, ...] = Field(min_length=8, max_length=8)

    @field_validator("decisions")
    @classmethod
    def normalize_decisions(cls, values: tuple[ShotDecision, ...]) -> tuple[ShotDecision, ...]:
        layers = [value.layer for value in values]
        if len(layers) != len(set(layers)) or set(layers) != set(ShotSemanticLayer):
            raise ValueError("ShotDecisionTrace must explain each canonical semantic layer L1-L8")
        return tuple(sorted(values, key=lambda value: _LAYER_ORDER[value.layer]))

    @model_validator(mode="after")
    def validate_authority(self) -> "ShotDecisionTrace":
        _project_ref(
            self.shot_ref,
            prefix="shot-list-item:",
            project_id=self.project_id,
            label="shot_ref",
        )
        _project_ref(
            self.full_shot_spec_ref,
            prefix="full-shot-spec:",
            project_id=self.project_id,
            label="full_shot_spec_ref",
        )
        _project_ref(
            self.eligibility_gate_ref,
            prefix="shot-eligibility-gate:",
            project_id=self.project_id,
            label="eligibility_gate_ref",
        )
        expected = shot_decision_trace_logical_id(self.project_id, self.shot_ref.logical_id)
        if self.shot_decision_trace_id != expected:
            raise ValueError(f"shot_decision_trace_id must be {expected.root}")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.shot_decision_trace_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="shot_list_item", source=self.shot_ref),
            SourceVersionBinding(role="full_shot_spec", source=self.full_shot_spec_ref),
            SourceVersionBinding(role="shot_eligibility_gate", source=self.eligibility_gate_ref),
        ]
        top_level = {_ref_key(binding.source) for binding in values}
        decision_refs = {
            _ref_key(ref): ref
            for decision in self.decisions
            for ref in decision.source_refs
            if _ref_key(ref) not in top_level
        }
        values.extend(
            SourceVersionBinding(role=f"decision_source_{index:03d}", source=decision_refs[key])
            for index, key in enumerate(sorted(decision_refs))
        )
        return tuple(values)


ShotRealizationValue: TypeAlias = (
    ShotEligibilityGate
    | FullShotSpec
    | StaticKeyframeSpec
    | MotionDeltaSpec
    | ShotDecisionTrace
)


class ShotRealizationArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: ShotRealizationValue

    @model_validator(mode="after")
    def validate_artifact(self) -> "ShotRealizationArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("shot realization artifact logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("shot realization artifact version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError("shot realization provenance must exactly bind declared sources")
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(
            logical_id=self.metadata.logical_id,
            version_id=self.metadata.version_id,
        )


class ShotEligibilityRequest(BaseModel):
    """Provider-neutral preflight inputs; carries no output identity except version intent."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    project_id: LogicalId
    shot_ref: VersionRef
    shot_list_manifest_ref: VersionRef
    state_snapshot_ref: VersionRef
    reference_resolution: ReferenceResolutionTrace
    required_reference_entity_refs: tuple[VersionRef, ...] = ()
    rule_version: VersionRef
    findings: tuple[EligibilityFinding, ...] = ()

    @field_validator("required_reference_entity_refs")
    @classmethod
    def normalize_required_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        values = _unique_refs(values, "required_reference_entity_refs")
        for ref in values:
            if not ref.logical_id.root.startswith("entity:"):
                raise ValueError("required_reference_entity_refs must reference EntityVersion")
        return values

    @field_validator("findings")
    @classmethod
    def normalize_findings(
        cls,
        values: tuple[EligibilityFinding, ...],
    ) -> tuple[EligibilityFinding, ...]:
        return tuple(sorted(values, key=lambda item: (item.code, item.message)))

    @model_validator(mode="after")
    def validate_project(self) -> "ShotEligibilityRequest":
        _project_ref(
            self.shot_ref,
            prefix="shot-list-item:",
            project_id=self.project_id,
            label="shot_ref",
        )
        _project_ref(
            self.shot_list_manifest_ref,
            prefix="shot-list-manifest:",
            project_id=self.project_id,
            label="shot_list_manifest_ref",
        )
        if self.reference_resolution.project_id != self.project_id:
            raise ValueError("reference_resolution belongs to different project")
        return self



def build_shot_realization_provenance(
    value: ShotRealizationValue,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    rule_version: VersionRef | None = None,
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=value.source_bindings(),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        rule_version=rule_version,
        correlation_id=correlation_id,
    )


class ShotRealizationRepository:
    """Exact-version IMP-032 repository and hard-gate coordinator."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)
        self.shots = ShotPlanningRepository(writer)
        self.traces = NarrativeTraceRepository(writer)
        self.directing = DirectingAuthorityRepository(writer)
        self.states = StateSnapshotRepository(writer)
        self.references = ReferenceResolver(writer)
        self.profiles = ActiveProductionProfileRepository(writer)

    async def evaluate_eligibility(
        self,
        *,
        request: ShotEligibilityRequest,
        gate_version: VersionId,
        actor_ref: str,
        reason: str,
        recorded_at: datetime,
        source_refs: tuple[str, ...] = (),
        correlation_id: str | None = None,
    ) -> ShotRealizationArtifact:
        context = await self._resolve_eligibility_context(request)
        evidence: tuple[ResolvedReferenceEvidence, ...] = context["reference_evidence"]
        findings = self._merge_builtin_findings(
            request=request,
            shot=context["shot"],
            state=context["state"],
            reference_evidence=evidence,
        )
        verdict = (
            ShotEligibilityVerdict.REJECTED
            if any(item.blocking for item in findings)
            else ShotEligibilityVerdict.ELIGIBLE
        )
        draft = ShotEligibilityGate.model_construct(
            project_id=request.project_id,
            shot_eligibility_gate_id=shot_eligibility_gate_logical_id(
                request.project_id,
                request.shot_ref.logical_id,
            ),
            version_id=gate_version,
            shot_ref=request.shot_ref,
            shot_narrative_trace_ref=context["shot_trace_ref"],
            shot_list_manifest_ref=request.shot_list_manifest_ref,
            active_profile_ref=context["shot"].active_profile_ref,
            directing_intent_ref=context["shot"].directing_intent_ref,
            spatial_contract_ref=context["spatial"].ref,
            blocking_plan_ref=context["shot"].blocking_plan_ref,
            cinematography_objective_ref=context["shot"].cinematography_objective_ref,
            state_snapshot_ref=request.state_snapshot_ref,
            approved_state_designation_ref=context["designation_ref"],
            reference_evidence=evidence,
            required_reference_entity_refs=request.required_reference_entity_refs,
            reference_resolution_hash=_hash_payload(
                request.reference_resolution.model_dump(mode="json")
            ),
            rule_version=request.rule_version,
            evaluated_input_hash="sha256:" + "0" * 64,
            verdict=verdict,
            findings=findings,
        )
        gate = ShotEligibilityGate.model_validate(
            {
                **draft.model_dump(mode="python"),
                "evaluated_input_hash": draft.compute_evaluated_input_hash(),
            }
        )
        provenance = build_shot_realization_provenance(
            gate,
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=recorded_at,
            source_refs=source_refs,
            rule_version=request.rule_version,
            correlation_id=correlation_id,
        )
        artifact = await self._ensure_initial_draft(
            value=gate,
            provenance=provenance,
            created_at=recorded_at,
            label="ShotEligibilityGate",
        )
        await self._bind_reference_resolution(
            resolution=request.reference_resolution,
            consumer_ref=artifact.ref,
            actor_ref=actor_ref,
            reason=f"{reason}: bind exact reference resolution",
            recorded_at=recorded_at,
            source_refs=source_refs,
            rule_version=request.rule_version,
            correlation_id=correlation_id,
        )
        await self._promote_exact_current(
            artifact.ref,
            status=LifecycleState.APPROVED,
            label="ShotEligibilityGate",
        )
        return artifact

    async def reevaluate_eligibility(
        self,
        *,
        request: ShotEligibilityRequest,
        gate_version: VersionId,
        predecessor: VersionRef,
        expected_revision: int,
        actor_ref: str,
        reason: str,
        recorded_at: datetime,
        source_refs: tuple[str, ...] = (),
        correlation_id: str | None = None,
    ) -> tuple[ShotRealizationArtifact, tuple[InvalidationRecord, ...]]:
        context = await self._resolve_eligibility_context(request)
        evidence: tuple[ResolvedReferenceEvidence, ...] = context["reference_evidence"]
        findings = self._merge_builtin_findings(
            request=request,
            shot=context["shot"],
            state=context["state"],
            reference_evidence=evidence,
        )
        verdict = (
            ShotEligibilityVerdict.REJECTED
            if any(item.blocking for item in findings)
            else ShotEligibilityVerdict.ELIGIBLE
        )
        draft = ShotEligibilityGate.model_construct(
            project_id=request.project_id,
            shot_eligibility_gate_id=shot_eligibility_gate_logical_id(
                request.project_id,
                request.shot_ref.logical_id,
            ),
            version_id=gate_version,
            shot_ref=request.shot_ref,
            shot_narrative_trace_ref=context["shot_trace_ref"],
            shot_list_manifest_ref=request.shot_list_manifest_ref,
            active_profile_ref=context["shot"].active_profile_ref,
            directing_intent_ref=context["shot"].directing_intent_ref,
            spatial_contract_ref=context["spatial"].ref,
            blocking_plan_ref=context["shot"].blocking_plan_ref,
            cinematography_objective_ref=context["shot"].cinematography_objective_ref,
            state_snapshot_ref=request.state_snapshot_ref,
            approved_state_designation_ref=context["designation_ref"],
            reference_evidence=evidence,
            required_reference_entity_refs=request.required_reference_entity_refs,
            reference_resolution_hash=_hash_payload(
                request.reference_resolution.model_dump(mode="json")
            ),
            rule_version=request.rule_version,
            evaluated_input_hash="sha256:" + "0" * 64,
            verdict=verdict,
            findings=findings,
        )
        gate = ShotEligibilityGate.model_validate(
            {
                **draft.model_dump(mode="python"),
                "evaluated_input_hash": draft.compute_evaluated_input_hash(),
            }
        )
        provenance = build_shot_realization_provenance(
            gate,
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=recorded_at,
            source_refs=source_refs,
            rule_version=request.rule_version,
            correlation_id=correlation_id,
        )
        artifact, records = await self._ensure_successor_draft(
            value=gate,
            predecessor=predecessor,
            provenance=provenance,
            created_at=recorded_at,
            expected_revision=expected_revision,
            label="ShotEligibilityGate",
            cause="SHOT_ELIGIBILITY_REEVALUATED",
            scope="shot_realization_descendants",
            repair="Rebuild FullShotSpec/static/motion/decision trace from the current eligibility evidence.",
            before_promote=lambda: self._bind_reference_resolution(
                resolution=request.reference_resolution,
                consumer_ref=gate.ref,
                actor_ref=actor_ref,
                reason=f"{reason}: bind exact reference resolution",
                recorded_at=recorded_at,
                source_refs=source_refs,
                rule_version=request.rule_version,
                correlation_id=correlation_id,
            ),
        )
        return artifact, records

    async def create_full_shot_spec(
        self,
        *,
        value: FullShotSpec,
        provenance: Provenance,
        created_at: datetime,
    ) -> ShotRealizationArtifact:
        await self._assert_full_shot_spec_inputs(value)
        return await self._create_approved(value, provenance, created_at, "FullShotSpec")

    async def revise_full_shot_spec(
        self,
        *,
        value: FullShotSpec,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ShotRealizationArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_full_shot_spec_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="FullShotSpec",
            cause="FULL_SHOT_SPEC_REVISED",
            scope="static_motion_trace_ir_descendants",
            repair="Recompute dependent StaticKeyframeSpec/MotionDeltaSpec/ShotDecisionTrace/ShotIR.",
        )

    async def create_static_keyframe_spec(
        self,
        *,
        value: StaticKeyframeSpec,
        provenance: Provenance,
        created_at: datetime,
    ) -> ShotRealizationArtifact:
        await self._assert_static_inputs(value)
        return await self._create_approved(value, provenance, created_at, "StaticKeyframeSpec")

    async def revise_static_keyframe_spec(
        self,
        *,
        value: StaticKeyframeSpec,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ShotRealizationArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_static_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="StaticKeyframeSpec",
            cause="STATIC_KEYFRAME_SPEC_REVISED",
            scope="motion_ir_descendants",
            repair="Recompute dependent MotionDeltaSpec/ShotIR from the current static start state.",
        )

    async def create_motion_delta_spec(
        self,
        *,
        value: MotionDeltaSpec,
        provenance: Provenance,
        created_at: datetime,
    ) -> ShotRealizationArtifact:
        await self._assert_motion_inputs(value)
        return await self._create_approved(value, provenance, created_at, "MotionDeltaSpec")

    async def revise_motion_delta_spec(
        self,
        *,
        value: MotionDeltaSpec,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ShotRealizationArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_motion_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="MotionDeltaSpec",
            cause="MOTION_DELTA_SPEC_REVISED",
            scope="motion_ir_descendants",
            repair="Recompute dependent ShotIR/video compilation from the current motion delta.",
        )

    async def create_shot_decision_trace(
        self,
        *,
        value: ShotDecisionTrace,
        provenance: Provenance,
        created_at: datetime,
    ) -> ShotRealizationArtifact:
        await self._assert_decision_trace_inputs(value)
        return await self._create_approved(value, provenance, created_at, "ShotDecisionTrace")

    async def revise_shot_decision_trace(
        self,
        *,
        value: ShotDecisionTrace,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ShotRealizationArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_decision_trace_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="ShotDecisionTrace",
            cause="SHOT_DECISION_TRACE_REVISED",
            scope="explainability_consumers",
            repair="Refresh explainability/QA consumers from the current ShotDecisionTrace.",
        )

    async def get_eligibility_gate(self, ref: VersionRef) -> ShotRealizationArtifact | None:
        return await self._get_typed(ref, ShotEligibilityGate, "shot-eligibility-gate:")

    async def get_full_shot_spec(self, ref: VersionRef) -> ShotRealizationArtifact | None:
        return await self._get_typed(ref, FullShotSpec, "full-shot-spec:")

    async def get_static_keyframe_spec(self, ref: VersionRef) -> ShotRealizationArtifact | None:
        return await self._get_typed(ref, StaticKeyframeSpec, "static-keyframe-spec:")

    async def get_motion_delta_spec(self, ref: VersionRef) -> ShotRealizationArtifact | None:
        return await self._get_typed(ref, MotionDeltaSpec, "motion-delta-spec:")

    async def get_shot_decision_trace(self, ref: VersionRef) -> ShotRealizationArtifact | None:
        return await self._get_typed(ref, ShotDecisionTrace, "shot-decision-trace:")

    async def assert_current_eligible_gate(self, ref: VersionRef) -> ShotEligibilityGate:
        await self._assert_current_valid(ref, "ShotEligibilityGate", _ACCEPTED)
        artifact = await self.get_eligibility_gate(ref)
        if artifact is None:
            raise ShotEligibilityBlocked("ShotEligibilityGate exact version does not exist")
        gate = artifact.value
        assert isinstance(gate, ShotEligibilityGate)
        await self._assert_gate_sources_current(gate)
        if gate.verdict is not ShotEligibilityVerdict.ELIGIBLE:
            raise ShotEligibilityBlocked("NO ELIGIBILITY PASS -> NO FULL SHOT SPEC")
        return gate

    async def _resolve_eligibility_context(self, request: ShotEligibilityRequest) -> dict:
        await self._assert_profile(request.project_id, request.reference_resolution.active_profile_ref)
        shot_artifact = await self.shots.get_shot_list_item(request.shot_ref)
        if shot_artifact is None:
            raise ShotEligibilityBlocked("ShotListItem exact version does not exist")
        await self._assert_current_valid(request.shot_ref, "ShotListItem", _ACCEPTED)
        shot = shot_artifact.value
        assert isinstance(shot, ShotListItem)
        if shot.project_id != request.project_id:
            raise ShotEligibilityBlocked("ShotListItem belongs to different project")
        if request.reference_resolution.active_profile_ref != shot.active_profile_ref:
            raise ShotEligibilityBlocked("reference resolution/profile does not match ShotListItem")

        shot_trace = await self.traces.get_current_trace(
            artifact_type=NarrativeArtifactType.SHOT_LIST_ITEM,
            traced_ref=shot.ref,
        )
        if (
            shot_trace is None
            or shot_trace.value.traced_ref != shot.ref
            or await self.traces.trace_state(shot_trace.ref) is not NarrativeTraceState.CURRENT
        ):
            raise ShotEligibilityBlocked("ShotListItem lacks exact CURRENT NarrativeTrace")

        await self._assert_current_valid(
            request.shot_list_manifest_ref,
            "ShotListManifest",
            _ACCEPTED,
        )
        manifest_artifact = await self.shots.get_manifest(request.shot_list_manifest_ref)
        if manifest_artifact is None:
            raise ShotEligibilityBlocked("ShotListManifest exact version does not exist")
        manifest = manifest_artifact.value
        assert isinstance(manifest, ShotListManifest)
        if shot.ref not in manifest.ordered_shot_refs:
            raise ShotEligibilityBlocked("ShotListItem is not a member of exact current ShotListManifest")
        if manifest.project_id != request.project_id or manifest.active_profile_ref != shot.active_profile_ref:
            raise ShotEligibilityBlocked("ShotListManifest lineage/profile mismatch")

        directing_artifact = await self.directing.get_directing_intent(shot.directing_intent_ref)
        blocking_artifact = await self.directing.get_blocking_plan(shot.blocking_plan_ref)
        cine_artifact = await self.directing.get_cinematography_objective(
            shot.cinematography_objective_ref
        )
        if directing_artifact is None or blocking_artifact is None or cine_artifact is None:
            raise ShotEligibilityBlocked("Shot directing/blocking/cinematography authority is missing")
        directing = directing_artifact.value
        blocking = blocking_artifact.value
        cine = cine_artifact.value
        assert isinstance(directing, DirectingIntent)
        assert isinstance(blocking, BlockingPlan)
        assert isinstance(cine, CinematographyObjective)
        await self._assert_current_valid(directing.ref, "DirectingIntent", _ACCEPTED)
        await self._assert_current_valid(blocking.ref, "BlockingPlan", _ACCEPTED)
        await self._assert_current_valid(cine.ref, "CinematographyObjective", _ACCEPTED)
        spatial_artifact = await self.directing.get_spatial_contract(blocking.spatial_contract_ref)
        if spatial_artifact is None:
            raise ShotEligibilityBlocked("SceneSpatialDramaticContract exact version is missing")
        spatial = spatial_artifact.value
        assert isinstance(spatial, SceneSpatialDramaticContract)
        await self._assert_current_valid(spatial.ref, "SceneSpatialDramaticContract", _ACCEPTED)
        if (
            directing.ref != shot.directing_intent_ref
            or blocking.directing_intent_ref != directing.ref
            or blocking.scene_dramatic_beat_ref != shot.parent_scene_dramatic_beat_ref
            or cine.directing_intent_ref != directing.ref
            or cine.blocking_plan_ref != blocking.ref
            or cine.spatial_contract_ref != spatial.ref
            or spatial.scene_ref != shot.scene_ref
            or any(
                ref != shot.active_profile_ref
                for ref in (
                    directing.active_profile_ref,
                    blocking.active_profile_ref,
                    cine.active_profile_ref,
                    spatial.active_profile_ref,
                )
            )
        ):
            raise ShotEligibilityBlocked("dramatic/directing/spatial/cinematography lineage mismatch")

        if request.state_snapshot_ref != blocking.state_snapshot_ref:
            raise ShotEligibilityBlocked("eligibility StateSnapshot must equal exact BlockingPlan state")
        designation = await self.states.assert_propagatable(request.state_snapshot_ref)
        if (
            designation.ref != blocking.approved_state_designation_ref
            or designation.ref != spatial.approved_state_designation_ref
            or request.state_snapshot_ref != spatial.state_snapshot_ref
        ):
            raise ShotEligibilityBlocked("approved StateSnapshot/designation lineage mismatch")
        state_artifact = await self.states.get_version(request.state_snapshot_ref)
        if state_artifact is None:
            raise ShotEligibilityBlocked("StateSnapshot exact version disappeared")

        reference_evidence = await self._assert_reference_resolution(
            request.reference_resolution,
            required_entities=request.required_reference_entity_refs,
        )
        return {
            "shot": shot,
            "shot_trace_ref": shot_trace.ref,
            "manifest": manifest,
            "directing": directing,
            "spatial": spatial,
            "blocking": blocking,
            "cine": cine,
            "state": state_artifact.value,
            "designation_ref": designation.ref,
            "reference_evidence": reference_evidence,
        }

    def _merge_builtin_findings(
        self,
        *,
        request: ShotEligibilityRequest,
        shot: ShotListItem,
        state,
        reference_evidence: tuple[ResolvedReferenceEvidence, ...],
    ) -> tuple[EligibilityFinding, ...]:
        findings = list(request.findings)
        declared_sources = {
            _ref_key(request.shot_ref),
            _ref_key(request.shot_list_manifest_ref),
            _ref_key(request.state_snapshot_ref),
            *(_ref_key(item.asset_ref) for item in reference_evidence),
        }
        if any(
            _ref_key(ref) not in declared_sources
            for finding in findings
            for ref in finding.source_refs
        ):
            raise ShotEligibilityBlocked("provider-neutral finding cites undeclared request evidence")

        state_subjects = {
            _ref_key(fact.subject_ref)
            for fact in state.facts
            if fact.subject_ref is not None
        }
        missing_state_subjects = [
            ref for ref in shot.subject_refs if _ref_key(ref) not in state_subjects
        ]
        if missing_state_subjects:
            findings.append(
                EligibilityFinding(
                    code="STATE_BREAK",
                    blocking=True,
                    message="Shot subject lacks approved semantic StateSnapshot coverage.",
                    source_refs=(request.shot_ref, request.state_snapshot_ref),
                )
            )
        selected_entities = {_ref_key(item.entity_ref) for item in reference_evidence}
        missing_refs = [
            ref
            for ref in request.required_reference_entity_refs
            if _ref_key(ref) not in selected_entities
        ]
        if missing_refs:
            findings.append(
                EligibilityFinding(
                    code="REFERENCE_MISSING",
                    blocking=True,
                    message="Required subject reference coverage is missing.",
                    source_refs=(request.shot_ref,),
                )
            )
        unique = {(item.code, item.message, item.blocking): item for item in findings}
        return tuple(sorted(unique.values(), key=lambda item: (item.code, item.message)))

    async def _assert_reference_resolution(
        self,
        resolution: ReferenceResolutionTrace,
        *,
        required_entities: tuple[VersionRef, ...],
    ) -> tuple[ResolvedReferenceEvidence, ...]:
        await self._assert_profile(resolution.project_id, resolution.active_profile_ref)
        unresolved = {
            (record.affected_object_id.root, record.affected_object_version.root)
            for record in await self.invalidations.list_unresolved()
        }
        evidence: list[ResolvedReferenceEvidence] = []
        for selected in resolution.selected:
            stored = await self.versions.get_version(selected.asset_ref)
            if stored is None:
                raise ShotEligibilityBlocked("selected ReferenceAsset exact version does not exist")
            asset = ReferenceAsset.model_validate(stored.payload)
            pointer = await self.versions.get_current(asset.reference_asset_id)
            if (
                pointer is None
                or pointer.version_id != asset.version_id
                or pointer.status not in _ACCEPTED
                or _ref_key(asset.ref) in unresolved
            ):
                raise ShotEligibilityBlocked("selected ReferenceAsset is stale/unapproved/invalidated")
            if asset.project_id != resolution.project_id:
                raise ShotEligibilityBlocked("selected ReferenceAsset belongs to different project")
            if (
                asset.entity_ref != selected.entity_ref
                or asset.role != selected.role
                or asset.content_hash != selected.content_hash
            ):
                raise ShotEligibilityBlocked("reference resolution projection contradicts canonical ReferenceAsset")
            evidence.append(
                ResolvedReferenceEvidence(
                    asset_ref=asset.ref,
                    entity_ref=asset.entity_ref,
                    role=asset.role,
                    content_hash=asset.content_hash,
                )
            )
        selected_entities = {_ref_key(item.entity_ref) for item in evidence}
        for ref in required_entities:
            if _ref_key(ref) not in selected_entities:
                # This becomes a persisted REJECTED finding in _merge_builtin_findings;
                # no hard exception here because the evaluated input set is otherwise valid.
                continue
        return tuple(sorted(evidence, key=lambda item: _ref_key(item.asset_ref)))

    async def _bind_reference_resolution(
        self,
        *,
        resolution: ReferenceResolutionTrace,
        consumer_ref: VersionRef,
        actor_ref: str,
        reason: str,
        recorded_at: datetime,
        source_refs: tuple[str, ...],
        rule_version: VersionRef,
        correlation_id: str | None,
    ) -> None:
        provenance = Provenance(
            source_versions=resolution.source_bindings(),
            source_refs=source_refs or ("evidence:shot-reference-resolution",),
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=recorded_at,
            rule_version=rule_version,
            correlation_id=correlation_id,
        )
        await self.references.bind_consumer(
            resolution=resolution,
            consumer_ref=consumer_ref,
            provenance=provenance,
            created_at=recorded_at,
        )

    async def _assert_full_shot_spec_inputs(self, value: FullShotSpec) -> None:
        gate = await self.assert_current_eligible_gate(value.eligibility_gate_ref)
        await self._assert_current_valid(value.shot_ref, "ShotListItem", _ACCEPTED)
        shot_artifact = await self.shots.get_shot_list_item(value.shot_ref)
        if shot_artifact is None:
            raise ShotRealizationGateBlocked("ShotListItem exact version does not exist")
        shot = shot_artifact.value
        assert isinstance(shot, ShotListItem)
        if (
            gate.shot_ref != value.shot_ref
            or gate.active_profile_ref != value.active_profile_ref
            or gate.directing_intent_ref != value.directing_intent_ref
            or gate.spatial_contract_ref != value.spatial_contract_ref
            or gate.blocking_plan_ref != value.blocking_plan_ref
            or gate.cinematography_objective_ref != value.cinematography_objective_ref
            or gate.state_snapshot_ref != value.state_snapshot_ref
            or gate.approved_state_designation_ref != value.approved_state_designation_ref
            or gate.reference_evidence != value.reference_evidence
        ):
            raise ShotRealizationGateBlocked("FullShotSpec exact inputs do not match current eligible gate")
        if value.duration_seconds != shot.duration_budget_seconds:
            raise ShotRealizationGateBlocked("FullShotSpec duration must equal ShotListItem duration budget")
        await self._assert_profile(value.project_id, value.active_profile_ref)
        designation = await self.states.assert_propagatable(value.state_snapshot_ref)
        if designation.ref != value.approved_state_designation_ref:
            raise ShotRealizationGateBlocked("FullShotSpec StateSnapshot designation is stale/mismatched")
        await self._assert_reference_evidence_current(value.reference_evidence)
        self._assert_layer_authority(value)

    def _assert_layer_authority(self, value: FullShotSpec) -> None:
        references = tuple(item.asset_ref for item in value.reference_evidence)
        required: dict[ShotSemanticLayer, set[tuple[str, str]]] = {
            ShotSemanticLayer.L1_SUBJECT: {_ref_key(value.shot_ref), *(_ref_key(ref) for ref in references)},
            ShotSemanticLayer.L2_STATE_WARDROBE: {
                _ref_key(value.state_snapshot_ref),
                *(_ref_key(ref) for ref in references),
            },
            ShotSemanticLayer.L3_ACTION_PERFORMANCE: {
                _ref_key(value.shot_ref),
                _ref_key(value.directing_intent_ref),
                _ref_key(value.blocking_plan_ref),
            },
            ShotSemanticLayer.L4_ENVIRONMENT: {
                _ref_key(value.spatial_contract_ref),
                _ref_key(value.state_snapshot_ref),
            },
            ShotSemanticLayer.L5_TIME_ATMOSPHERE: {
                _ref_key(value.state_snapshot_ref),
                _ref_key(value.active_profile_ref),
                _ref_key(value.cinematography_objective_ref),
            },
            ShotSemanticLayer.L6_CAMERA: {
                _ref_key(value.cinematography_objective_ref),
                _ref_key(value.blocking_plan_ref),
                _ref_key(value.directing_intent_ref),
                _ref_key(value.spatial_contract_ref),
            },
            ShotSemanticLayer.L7_LIGHTING_STYLE: {
                _ref_key(value.cinematography_objective_ref),
                _ref_key(value.active_profile_ref),
            },
            ShotSemanticLayer.L8_CONTINUITY: {
                _ref_key(value.state_snapshot_ref),
                _ref_key(value.shot_ref),
                _ref_key(value.spatial_contract_ref),
                _ref_key(value.blocking_plan_ref),
            },
        }
        for layer in value.layers:
            accepted = required[layer.layer]
            for field in layer.fields:
                if not any(_ref_key(ref) in accepted for ref in field.source_refs):
                    raise ShotRealizationGateBlocked(
                        f"{layer.layer.value} field {field.key} lacks its required canonical authority"
                    )

    async def _assert_static_inputs(self, value: StaticKeyframeSpec) -> None:
        spec = await self._assert_current_full_spec(value.full_shot_spec_ref)
        if spec.shot_ref != value.shot_ref:
            raise ShotRealizationGateBlocked("StaticKeyframeSpec shot_id differs from FullShotSpec")
        if (
            spec.state_snapshot_ref != value.state_snapshot_ref
            or spec.approved_state_designation_ref != value.approved_state_designation_ref
        ):
            raise ShotRealizationGateBlocked("StaticKeyframeSpec state differs from FullShotSpec")
        allowed_assets = {_ref_key(item.asset_ref) for item in spec.reference_evidence}
        if any(_ref_key(ref) not in allowed_assets for ref in value.reference_asset_refs):
            raise ShotRealizationGateBlocked("StaticKeyframeSpec cites reference outside FullShotSpec")
        shot_artifact = await self.shots.get_shot_list_item(value.shot_ref)
        if shot_artifact is None:
            raise ShotRealizationGateBlocked("StaticKeyframeSpec ShotListItem is missing")
        shot = shot_artifact.value
        assert isinstance(shot, ShotListItem)
        if any(ref not in shot.subject_refs for ref in value.visible_subject_refs):
            raise ShotRealizationGateBlocked("StaticKeyframeSpec visible subject is not a ShotListItem subject")
        await self.states.assert_propagatable(value.state_snapshot_ref)
        await self._assert_reference_evidence_current(
            tuple(item for item in spec.reference_evidence if item.asset_ref in value.reference_asset_refs)
        )

    async def _assert_motion_inputs(self, value: MotionDeltaSpec) -> None:
        spec = await self._assert_current_full_spec(value.full_shot_spec_ref)
        await self._assert_current_valid(
            value.static_keyframe_spec_ref,
            "StaticKeyframeSpec",
            _ACCEPTED,
        )
        static_artifact = await self.get_static_keyframe_spec(value.static_keyframe_spec_ref)
        if static_artifact is None:
            raise ShotRealizationGateBlocked("MotionDeltaSpec exact StaticKeyframeSpec is missing")
        static = static_artifact.value
        assert isinstance(static, StaticKeyframeSpec)
        if (
            spec.shot_ref != value.shot_ref
            or static.shot_ref != value.shot_ref
            or static.full_shot_spec_ref != spec.ref
        ):
            raise ShotRealizationGateBlocked("MotionDeltaSpec must preserve same shot/full-spec/static lineage")
        if value.duration_seconds != spec.duration_seconds:
            raise ShotRealizationGateBlocked("MotionDeltaSpec duration must equal FullShotSpec duration")

    async def _assert_decision_trace_inputs(self, value: ShotDecisionTrace) -> None:
        spec = await self._assert_current_full_spec(value.full_shot_spec_ref)
        if spec.shot_ref != value.shot_ref or spec.eligibility_gate_ref != value.eligibility_gate_ref:
            raise ShotRealizationGateBlocked("ShotDecisionTrace must bind exact FullShotSpec/gate/shot lineage")
        gate = await self.assert_current_eligible_gate(value.eligibility_gate_ref)
        allowed = {_ref_key(binding.source) for binding in spec.source_bindings()}
        allowed.update(_ref_key(binding.source) for binding in gate.source_bindings())
        for decision in value.decisions:
            if any(_ref_key(ref) not in allowed for ref in decision.source_refs):
                raise ShotRealizationGateBlocked(
                    f"ShotDecisionTrace {decision.layer.value} cites undeclared authority"
                )

    async def _assert_current_full_spec(self, ref: VersionRef) -> FullShotSpec:
        await self._assert_current_valid(ref, "FullShotSpec", _ACCEPTED)
        artifact = await self.get_full_shot_spec(ref)
        if artifact is None:
            raise ShotRealizationGateBlocked("FullShotSpec exact version does not exist")
        spec = artifact.value
        assert isinstance(spec, FullShotSpec)
        await self._assert_full_shot_spec_inputs(spec)
        return spec

    async def _assert_gate_sources_current(self, gate: ShotEligibilityGate) -> None:
        for binding in gate.source_bindings():
            await self._assert_current_valid(
                binding.source,
                f"ShotEligibilityGate source {binding.role}",
                _ACCEPTED,
            )
        if await self.traces.trace_state(gate.shot_narrative_trace_ref) is not NarrativeTraceState.CURRENT:
            raise ShotEligibilityBlocked("ShotEligibilityGate NarrativeTrace is not CURRENT")
        await self._assert_profile(gate.project_id, gate.active_profile_ref)
        designation = await self.states.assert_propagatable(gate.state_snapshot_ref)
        if designation.ref != gate.approved_state_designation_ref:
            raise ShotEligibilityBlocked("ShotEligibilityGate approved state designation is stale")
        await self._assert_reference_evidence_current(gate.reference_evidence)

    async def _assert_profile(self, project_id: LogicalId, ref: VersionRef) -> ActiveProductionProfile:
        if ref.logical_id != _active_profile_id(project_id):
            raise ShotEligibilityBlocked("ActiveProductionProfile belongs to different project")
        await self._assert_current_valid(ref, "ActiveProductionProfile", {LifecycleState.LOCKED})
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise ShotEligibilityBlocked("ActiveProductionProfile exact version does not exist")
        try:
            profile = ActiveProductionProfile.model_validate(stored.payload)
        except Exception as exc:
            raise ShotEligibilityBlocked("ActiveProductionProfile payload is invalid") from exc
        if profile.project_id != project_id:
            raise ShotEligibilityBlocked("ActiveProductionProfile payload belongs to different project")
        return profile

    async def _assert_reference_evidence_current(
        self,
        evidence: tuple[ResolvedReferenceEvidence, ...],
    ) -> None:
        for item in evidence:
            await self._assert_current_valid(item.asset_ref, "ReferenceAsset", _ACCEPTED)
            stored = await self.versions.get_version(item.asset_ref)
            if stored is None:
                raise ShotRealizationGateBlocked("ReferenceAsset exact version disappeared")
            asset = ReferenceAsset.model_validate(stored.payload)
            if (
                asset.entity_ref != item.entity_ref
                or asset.role != item.role
                or asset.content_hash != item.content_hash
            ):
                raise ShotRealizationGateBlocked("Reference evidence contradicts canonical ReferenceAsset")

    async def _assert_current_valid(
        self,
        ref: VersionRef,
        label: str,
        allowed_statuses: set[LifecycleState],
    ) -> CurrentVersionPointer:
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise ShotRealizationGateBlocked(f"{label} exact version does not exist")
        pointer = await self.versions.get_current(ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != ref.version_id
            or pointer.status not in allowed_statuses
        ):
            raise ShotRealizationGateBlocked(f"{label} is not exact current accepted version")
        for record in await self.invalidations.list_unresolved():
            if (
                record.affected_object_id == ref.logical_id
                and record.affected_object_version == ref.version_id
            ):
                raise ShotRealizationGateBlocked(f"{label} has unresolved durable invalidation")
        return pointer

    async def _get_typed(self, ref: VersionRef, model, prefix: str) -> ShotRealizationArtifact | None:
        if not ref.logical_id.root.startswith(prefix):
            raise ShotRealizationIdentityError(f"expected {prefix.rstrip(':')} ref")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = model.model_validate(stored.payload)
        return ShotRealizationArtifact(metadata=stored.metadata, value=value)

    def _assert_provenance(self, value: ShotRealizationValue, provenance: Provenance) -> None:
        if provenance.source_versions != value.source_bindings():
            raise ShotRealizationGateBlocked(
                "shot realization provenance must exactly bind declared source versions"
            )

    async def _register_dependencies(
        self,
        artifact: ShotRealizationArtifact,
    ) -> None:
        for binding in artifact.value.source_bindings():
            await self.graph.create_edge(
                source=binding.source,
                dependent=artifact.ref,
                edge_type="shot_realization_source",
                dependency_reason=f"shot_realization_source:{binding.role}",
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _ensure_initial_draft(
        self,
        *,
        value: ShotRealizationValue,
        provenance: Provenance,
        created_at: datetime,
        label: str,
    ) -> ShotRealizationArtifact:
        self._assert_provenance(value, provenance)
        current = await self.versions.get_current(value.logical_id)
        if current is None:
            metadata = SemanticRecordMetadata(
                logical_id=value.logical_id,
                version_id=value.version_id,
                provenance=provenance,
                created_at=created_at,
            )
            stored = await self.versions.create_initial(
                metadata=metadata,
                payload=value.model_dump(mode="json"),
                status=LifecycleState.DRAFT,
            )
            artifact = ShotRealizationArtifact(metadata=stored.metadata, value=value)
        else:
            if current.version_id != value.version_id:
                raise ShotRealizationIdentityError(
                    f"{label} logical identity already has a different current version"
                )
            stored = await self.versions.get_version(value.ref)
            if stored is None:
                raise ShotRealizationIdentityError(f"{label} current version payload is missing")
            existing = ShotRealizationArtifact(
                metadata=stored.metadata,
                value=type(value).model_validate(stored.payload),
            )
            if existing.value != value or existing.metadata.provenance != provenance:
                raise ShotRealizationIdentityError(
                    f"{label} exact replay conflicts with persisted immutable evidence"
                )
            artifact = existing
        await self._register_dependencies(artifact)
        return artifact

    async def _promote_exact_current(
        self,
        ref: VersionRef,
        *,
        status: LifecycleState,
        label: str,
    ) -> CurrentVersionPointer:
        pointer = await self.versions.get_current(ref.logical_id)
        if pointer is None or pointer.version_id != ref.version_id:
            raise ShotRealizationIdentityError(f"{label} current pointer changed during promotion")
        if pointer.status == status:
            return pointer
        if pointer.status is not LifecycleState.DRAFT:
            raise ShotRealizationIdentityError(
                f"{label} can promote only its exact DRAFT replay/current version"
            )
        return await self.versions.update_current(
            logical_id=ref.logical_id,
            version_id=ref.version_id,
            status=status,
            expected_revision=pointer.revision,
        )

    async def _create_approved(
        self,
        value: ShotRealizationValue,
        provenance: Provenance,
        created_at: datetime,
        label: str,
    ) -> ShotRealizationArtifact:
        artifact = await self._ensure_initial_draft(
            value=value,
            provenance=provenance,
            created_at=created_at,
            label=label,
        )
        await self._promote_exact_current(
            artifact.ref,
            status=LifecycleState.APPROVED,
            label=label,
        )
        await self._assert_current_valid(artifact.ref, label, _ACCEPTED)
        return artifact

    async def _ensure_successor_draft(
        self,
        *,
        value: ShotRealizationValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
        label: str,
        cause: str,
        scope: str,
        repair: str,
        before_promote=None,
    ) -> tuple[ShotRealizationArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise ShotRealizationIdentityError(f"{label} successor must preserve logical identity")
        self._assert_provenance(value, provenance)
        current = await self.versions.get_current(value.logical_id)
        if current is None:
            raise ShotRealizationIdentityError(f"{label} current pointer is missing")
        replay_after_promote = current.version_id == value.version_id
        if replay_after_promote:
            if current.status not in _ACCEPTED or current.revision != expected_revision + 1:
                raise ShotRealizationIdentityError(f"{label} successor replay revision/state mismatch")
        elif (
            current.version_id != predecessor.version_id
            or current.status not in _ACCEPTED
            or current.revision != expected_revision
        ):
            raise ShotRealizationIdentityError(
                f"{label} successor requires exact current accepted predecessor/revision"
            )

        stored = await self.versions.get_version(value.ref)
        if stored is None:
            metadata = SemanticRecordMetadata(
                logical_id=value.logical_id,
                version_id=value.version_id,
                predecessor=predecessor,
                provenance=provenance,
                created_at=created_at,
            )
            stored = await self.versions.create_successor(
                metadata=metadata,
                payload=value.model_dump(mode="json"),
                supersession_reason=provenance.reason,
            )
        artifact = ShotRealizationArtifact(
            metadata=stored.metadata,
            value=type(value).model_validate(stored.payload),
        )
        if artifact.value != value or artifact.metadata.provenance != provenance:
            raise ShotRealizationIdentityError(
                f"{label} successor exact replay conflicts with persisted immutable evidence"
            )
        await self._register_dependencies(artifact)
        if before_promote is not None:
            await before_promote()
        records = await self.invalidations.create_for_change(
            cause=cause,
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope=scope,
            repair_or_recompute_requirement=repair,
        )
        if not replay_after_promote:
            await self.versions.update_current(
                logical_id=value.logical_id,
                version_id=value.version_id,
                status=LifecycleState.APPROVED,
                expected_revision=expected_revision,
            )
        await self._assert_current_valid(artifact.ref, label, _ACCEPTED)
        return artifact, tuple(records)

    async def _revise_approved(
        self,
        *,
        value: ShotRealizationValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
        label: str,
        cause: str,
        scope: str,
        repair: str,
    ) -> tuple[ShotRealizationArtifact, tuple[InvalidationRecord, ...]]:
        previous = await self.versions.get_version(predecessor)
        if previous is None:
            raise ShotRealizationIdentityError(f"{label} predecessor exact version does not exist")
        previous_payload = dict(previous.payload)
        current_payload = value.model_dump(mode="json")
        previous_payload.pop("version_id", None)
        current_payload.pop("version_id", None)
        if previous_payload == current_payload:
            raise ShotRealizationIdentityError(f"{label} successor requires semantic/source change")
        return await self._ensure_successor_draft(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label=label,
            cause=cause,
            scope=scope,
            repair=repair,
        )
