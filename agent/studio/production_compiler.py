"""IMP-033 provider-neutral ShotIR and deterministic Production Compiler.

This module implements the frozen Master §55 / §64 boundary:
canonical, exact-version shot realization inputs are lowered into immutable
provider-neutral ShotIR. Provider capability selection and provider-specific
request lowering remain downstream (IMP-050/051).
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import Enum
from typing import Any, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .active_profile import ActiveProductionProfile
from .invalidation import (
    DependencyGraphRepository,
    InvalidationRecord,
    InvalidationRepository,
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
from .reference import ReferenceAsset, ReferenceAssetRepository
from .shot_realization import (
    FullShotSpec,
    MotionDeltaSpec,
    ResolvedReferenceEvidence,
    SemanticAuthorityClass,
    SemanticField,
    SemanticLayerSpec,
    ShotRealizationRepository,
    ShotSemanticLayer,
    StaticKeyframeSpec,
)
from .state_continuity import StateSnapshotRepository
from .versioning import CurrentPointerNotFound, CurrentVersionPointer, VersionRepository


_ACCEPTED = {LifecycleState.APPROVED, LifecycleState.LOCKED}
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_.:-]{1,127}$")
_FORBIDDEN_CONSTRAINT_KEYS = {
    "provider",
    "provider_profile",
    "provider_profile_id",
    "provider_profile_version",
    "model",
    "model_family",
    "model_version",
    "rpc",
    "rpc_id",
    "request_id",
    "remote_request_id",
    "upload",
    "upload_slot",
    "media_id",
    "api_key",
    "credential",
    "credential_id",
    "paygate",
    "paygate_tier",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    raw = _canonical_json(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return ref.logical_id.root, ref.version_id.root


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{label} must not contain leading/trailing whitespace")
    return value


def _token(value: str, label: str) -> str:
    value = _trimmed(value, label).lower()
    if not _TOKEN_RE.fullmatch(value):
        raise ValueError(f"{label} must be a normalized lowercase token")
    return value


def _unique_refs(values: tuple[VersionRef, ...], label: str) -> tuple[VersionRef, ...]:
    keys = [_ref_key(value) for value in values]
    if len(keys) != len(set(keys)):
        raise ValueError(f"{label} must not contain duplicate exact refs")
    return tuple(sorted(values, key=_ref_key))


def _project_ref(ref: VersionRef, *, project_id: LogicalId, prefix: str, label: str) -> None:
    root = ref.logical_id.root
    if not root.startswith(prefix) or project_id.root not in root:
        raise ValueError(f"{label} must reference {prefix.rstrip(':')} for this project")


def _active_profile_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"active-profile:{project_id.root}")


def compiler_rule_logical_id() -> LogicalId:
    return LogicalId("production-compiler-rule:canonical")


def shot_ir_logical_id(project_id: LogicalId, shot_id: LogicalId) -> LogicalId:
    raw = f"{project_id.root}\0{shot_id.root}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:32]
    return LogicalId(f"shot-ir:{project_id.root}:{digest}")


class ProductionCompilerError(ValueError):
    """Base IMP-033 compiler error."""


class ProductionCompilerIdentityError(ProductionCompilerError):
    """Immutable identity/version invariant failed."""


class ProductionCompilerGateBlocked(ProductionCompilerError):
    """Compilation cannot proceed from stale/invalid authority."""


class CompileDiagnosticSeverity(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    BLOCKER = "BLOCKER"


class CompilerRuleSet(BaseModel):
    """Versioned deterministic compiler semantics; never creative/provider policy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    compiler_rule_id: LogicalId
    version_id: VersionId
    ir_schema_version: str = "shot-ir.v1"
    normalization_version: str = "canonical-json.v1"
    hash_algorithm: str = "sha256"
    static_lowering_version: str = "static.v1"
    motion_lowering_version: str = "motion.v1"

    @field_validator(
        "ir_schema_version",
        "normalization_version",
        "hash_algorithm",
        "static_lowering_version",
        "motion_lowering_version",
    )
    @classmethod
    def validate_tokens(cls, value: str, info) -> str:
        return _token(value, info.field_name)

    @model_validator(mode="after")
    def validate_identity(self) -> "CompilerRuleSet":
        if self.compiler_rule_id != compiler_rule_logical_id():
            raise ValueError("compiler_rule_id must be production-compiler-rule:canonical")
        if self.hash_algorithm != "sha256":
            raise ValueError("IMP-033 canonical compiler supports sha256 fingerprints only")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.compiler_rule_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return ()


class ProviderNeutralExecutionConstraint(BaseModel):
    """Typed canonical-json constraint with no provider/model/runtime vocabulary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    value_json: str
    source_refs: tuple[VersionRef, ...] = ()

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        value = _token(value, "execution constraint key")
        parts = {part for part in re.split(r"[.:-]", value) if part}
        if parts & _FORBIDDEN_CONSTRAINT_KEYS:
            raise ValueError("execution constraint key contains provider/runtime-specific authority")
        return value

    @field_validator("value_json")
    @classmethod
    def canonicalize_value(cls, value: str) -> str:
        value = _trimmed(value, "execution constraint value_json")
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("execution constraint value_json must be valid JSON") from exc

        def walk(item: Any) -> None:
            if isinstance(item, dict):
                for key, child in item.items():
                    normalized = str(key).strip().lower()
                    parts = {part for part in re.split(r"[.:-]", normalized) if part}
                    if parts & _FORBIDDEN_CONSTRAINT_KEYS:
                        raise ValueError(
                            "execution constraint JSON contains provider/runtime-specific field"
                        )
                    walk(child)
            elif isinstance(item, list):
                for child in item:
                    walk(child)

        walk(parsed)
        return _canonical_json(parsed)

    @field_validator("source_refs")
    @classmethod
    def normalize_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        return _unique_refs(values, "execution constraint source_refs")


class CompileDiagnostic(BaseModel):
    """Deterministic compiler evidence, never upstream semantic authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    severity: CompileDiagnosticSeverity
    message: str
    source_refs: tuple[VersionRef, ...] = Field(min_length=1)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        value = _trimmed(value, "compile diagnostic code").upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", value):
            raise ValueError("compile diagnostic code must be uppercase underscore token")
        return value

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        return _trimmed(value, "compile diagnostic message")

    @field_validator("source_refs")
    @classmethod
    def normalize_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        return _unique_refs(values, "compile diagnostic source_refs")


class IRReferenceBinding(BaseModel):
    """Provider-neutral exact ReferenceAsset binding carried into ShotIR."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: str
    asset_ref: VersionRef
    entity_ref: VersionRef
    content_hash: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        return _trimmed(value, "reference role")

    @field_validator("content_hash")
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if not _HASH_RE.fullmatch(value):
            raise ValueError("reference content_hash must be sha256:<64 lowercase hex>")
        return value

    @model_validator(mode="after")
    def validate_refs(self) -> "IRReferenceBinding":
        if not self.asset_ref.logical_id.root.startswith("reference-asset:"):
            raise ValueError("asset_ref must reference canonical ReferenceAsset")
        if not self.entity_ref.logical_id.root.startswith("entity:"):
            raise ValueError("entity_ref must reference canonical EntityVersion")
        return self


class IRStaticState(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    state_summary: str
    composition: str
    visible_performance: str
    environment_state: str
    lighting_state: str
    visible_subject_refs: tuple[VersionRef, ...] = ()

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

    @field_validator("visible_subject_refs")
    @classmethod
    def normalize_subjects(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        values = _unique_refs(values, "visible_subject_refs")
        for ref in values:
            if not ref.logical_id.root.startswith("entity:"):
                raise ValueError("visible_subject_refs must reference canonical EntityVersion")
        return values


class IRMotionDelta(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

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
        normalized = tuple(_trimmed(value, "continuity requirement") for value in values)
        if len(normalized) != len(set(normalized)):
            raise ValueError("continuity_requirements must be unique")
        return normalized


class IRQAExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    expectation: str
    source_refs: tuple[VersionRef, ...] = Field(min_length=1)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        value = _trimmed(value, "QA expectation code").upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", value):
            raise ValueError("QA expectation code must be uppercase underscore token")
        return value

    @field_validator("expectation")
    @classmethod
    def validate_expectation(cls, value: str) -> str:
        return _trimmed(value, "QA expectation")

    @field_validator("source_refs")
    @classmethod
    def normalize_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        return _unique_refs(values, "QA expectation source_refs")


class CompileHashes(BaseModel):
    """Durable provider-neutral fingerprints for downstream request lowering."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input_fingerprint: str
    semantic_ir_hash: str
    static_request_hash: str
    motion_request_hash: str

    @field_validator(
        "input_fingerprint",
        "semantic_ir_hash",
        "static_request_hash",
        "motion_request_hash",
    )
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if not _HASH_RE.fullmatch(value):
            raise ValueError("compile hashes must be sha256:<64 lowercase hex>")
        return value


class ShotIR(BaseModel):
    """Immutable provider-neutral executable representation of one canonical shot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    shot_ir_id: LogicalId
    version_id: VersionId
    shot_ref: VersionRef
    full_shot_spec_ref: VersionRef
    eligibility_gate_ref: VersionRef
    static_keyframe_spec_ref: VersionRef
    motion_delta_spec_ref: VersionRef
    state_snapshot_ref: VersionRef
    approved_state_designation_ref: VersionRef
    active_profile_ref: VersionRef
    compiler_rule_ref: VersionRef
    reference_bindings: tuple[IRReferenceBinding, ...] = ()
    semantic_layers: tuple[SemanticLayerSpec, ...] = Field(min_length=8, max_length=8)
    static_state: IRStaticState
    motion_delta: IRMotionDelta
    execution_constraints: tuple[ProviderNeutralExecutionConstraint, ...] = ()
    qa_expectations: tuple[IRQAExpectation, ...] = Field(min_length=3)
    diagnostics: tuple[CompileDiagnostic, ...] = Field(min_length=2)
    hashes: CompileHashes

    @field_validator("reference_bindings")
    @classmethod
    def normalize_reference_bindings(
        cls,
        values: tuple[IRReferenceBinding, ...],
    ) -> tuple[IRReferenceBinding, ...]:
        refs = [_ref_key(value.asset_ref) for value in values]
        if len(refs) != len(set(refs)):
            raise ValueError("reference_bindings must not duplicate exact ReferenceAsset refs")
        return tuple(sorted(values, key=lambda value: (_ref_key(value.asset_ref), value.role)))

    @field_validator("semantic_layers")
    @classmethod
    def normalize_layers(cls, values: tuple[SemanticLayerSpec, ...]) -> tuple[SemanticLayerSpec, ...]:
        layers = [value.layer for value in values]
        if len(layers) != len(set(layers)) or set(layers) != set(ShotSemanticLayer):
            raise ValueError("ShotIR must contain exactly one of each FullShotSpec semantic layer L1-L8")
        order = {layer: index for index, layer in enumerate(ShotSemanticLayer)}
        return tuple(sorted(values, key=lambda value: order[value.layer]))

    @field_validator("execution_constraints")
    @classmethod
    def normalize_constraints(
        cls,
        values: tuple[ProviderNeutralExecutionConstraint, ...],
    ) -> tuple[ProviderNeutralExecutionConstraint, ...]:
        keys = [value.key for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("execution_constraints keys must be unique")
        return tuple(sorted(values, key=lambda value: value.key))

    @field_validator("qa_expectations")
    @classmethod
    def normalize_expectations(
        cls,
        values: tuple[IRQAExpectation, ...],
    ) -> tuple[IRQAExpectation, ...]:
        keys = [value.code for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("qa_expectations codes must be unique")
        return tuple(sorted(values, key=lambda value: value.code))

    @field_validator("diagnostics")
    @classmethod
    def normalize_diagnostics(
        cls,
        values: tuple[CompileDiagnostic, ...],
    ) -> tuple[CompileDiagnostic, ...]:
        keys = [(value.code, value.message) for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("diagnostics must not duplicate code/message")
        if any(value.severity is CompileDiagnosticSeverity.BLOCKER for value in values):
            raise ValueError("persisted accepted ShotIR cannot contain BLOCKER diagnostics")
        return tuple(sorted(values, key=lambda value: (value.severity.value, value.code)))

    @model_validator(mode="after")
    def validate_authority(self) -> "ShotIR":
        if not self.shot_ref.logical_id.root.startswith("shot-list-item:"):
            raise ValueError("shot_ref must reference canonical ShotListItem")
        _project_ref(
            self.full_shot_spec_ref,
            project_id=self.project_id,
            prefix="full-shot-spec:",
            label="full_shot_spec_ref",
        )
        _project_ref(
            self.static_keyframe_spec_ref,
            project_id=self.project_id,
            prefix="static-keyframe-spec:",
            label="static_keyframe_spec_ref",
        )
        _project_ref(
            self.motion_delta_spec_ref,
            project_id=self.project_id,
            prefix="motion-delta-spec:",
            label="motion_delta_spec_ref",
        )
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        if self.compiler_rule_ref.logical_id != compiler_rule_logical_id():
            raise ValueError("compiler_rule_ref must bind canonical Production Compiler rule set")
        expected = shot_ir_logical_id(self.project_id, self.shot_ref.logical_id)
        if self.shot_ir_id != expected:
            raise ValueError(f"shot_ir_id must be {expected.root}")
        expected_hashes = self.compute_hashes()
        if self.hashes != expected_hashes:
            raise ValueError("ShotIR compile hashes do not match canonical deterministic payload")
        declared = {_ref_key(binding.source) for binding in self.source_bindings()}
        for constraint in self.execution_constraints:
            if any(_ref_key(ref) not in declared for ref in constraint.source_refs):
                raise ValueError("execution constraint may cite declared ShotIR sources only")
        for expectation in self.qa_expectations:
            if any(_ref_key(ref) not in declared for ref in expectation.source_refs):
                raise ValueError("QA expectation may cite declared ShotIR sources only")
        for diagnostic in self.diagnostics:
            if any(_ref_key(ref) not in declared for ref in diagnostic.source_refs):
                raise ValueError("compile diagnostic may cite declared ShotIR sources only")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.shot_ir_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="shot_list_item", source=self.shot_ref),
            SourceVersionBinding(role="full_shot_spec", source=self.full_shot_spec_ref),
            SourceVersionBinding(role="shot_eligibility_gate", source=self.eligibility_gate_ref),
            SourceVersionBinding(role="static_keyframe_spec", source=self.static_keyframe_spec_ref),
            SourceVersionBinding(role="motion_delta_spec", source=self.motion_delta_spec_ref),
            SourceVersionBinding(role="state_snapshot", source=self.state_snapshot_ref),
            SourceVersionBinding(
                role="approved_state_designation",
                source=self.approved_state_designation_ref,
            ),
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="compiler_rule", source=self.compiler_rule_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"reference_asset_{index:03d}", source=value.asset_ref)
            for index, value in enumerate(self.reference_bindings)
        )
        return tuple(values)

    def _input_hash_payload(self) -> dict[str, Any]:
        return {
            "source_bindings": [
                {
                    "role": binding.role,
                    "logical_id": binding.source.logical_id.root,
                    "version_id": binding.source.version_id.root,
                }
                for binding in self.source_bindings()
            ],
            "reference_bindings": [value.model_dump(mode="json") for value in self.reference_bindings],
            "execution_constraints": [
                value.model_dump(mode="json") for value in self.execution_constraints
            ],
        }

    def _semantic_hash_payload(self) -> dict[str, Any]:
        return {
            "shot_id": self.shot_ref.logical_id.root,
            "semantic_layers": [value.model_dump(mode="json") for value in self.semantic_layers],
            "static_state": self.static_state.model_dump(mode="json"),
            "motion_delta": self.motion_delta.model_dump(mode="json"),
            "references": [value.model_dump(mode="json") for value in self.reference_bindings],
            "constraints": [value.model_dump(mode="json") for value in self.execution_constraints],
            "qa": [value.model_dump(mode="json") for value in self.qa_expectations],
        }

    def _static_hash_payload(self) -> dict[str, Any]:
        return {
            "shot_id": self.shot_ref.logical_id.root,
            "full_shot_spec_ref": self.full_shot_spec_ref.model_dump(mode="json"),
            "static_keyframe_spec_ref": self.static_keyframe_spec_ref.model_dump(mode="json"),
            "compiler_rule_ref": self.compiler_rule_ref.model_dump(mode="json"),
            "state_snapshot_ref": self.state_snapshot_ref.model_dump(mode="json"),
            "static_state": self.static_state.model_dump(mode="json"),
            "references": [value.model_dump(mode="json") for value in self.reference_bindings],
            "constraints": [value.model_dump(mode="json") for value in self.execution_constraints],
        }

    def _motion_hash_payload(self) -> dict[str, Any]:
        return {
            "shot_id": self.shot_ref.logical_id.root,
            "full_shot_spec_ref": self.full_shot_spec_ref.model_dump(mode="json"),
            "static_keyframe_spec_ref": self.static_keyframe_spec_ref.model_dump(mode="json"),
            "motion_delta_spec_ref": self.motion_delta_spec_ref.model_dump(mode="json"),
            "compiler_rule_ref": self.compiler_rule_ref.model_dump(mode="json"),
            "motion_delta": self.motion_delta.model_dump(mode="json"),
            "constraints": [value.model_dump(mode="json") for value in self.execution_constraints],
        }

    def compute_hashes(self) -> CompileHashes:
        return CompileHashes(
            input_fingerprint=_sha256(self._input_hash_payload()),
            semantic_ir_hash=_sha256(self._semantic_hash_payload()),
            static_request_hash=_sha256(self._static_hash_payload()),
            motion_request_hash=_sha256(self._motion_hash_payload()),
        )


CompilerValue: TypeAlias = CompilerRuleSet | ShotIR


class ProductionCompilerArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: CompilerValue

    @model_validator(mode="after")
    def validate_artifact(self) -> "ProductionCompilerArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("compiler artifact logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("compiler artifact version identity mismatch")
        if isinstance(self.value, ShotIR):
            if self.metadata.provenance.source_versions != self.value.source_bindings():
                raise ValueError("ShotIR provenance must exactly bind declared source versions")
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(
            logical_id=self.metadata.logical_id,
            version_id=self.metadata.version_id,
        )


class ShotIRCompileRequest(BaseModel):
    """Pinned provider-neutral compiler inputs; contains no provider routing choice."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    full_shot_spec_ref: VersionRef
    static_keyframe_spec_ref: VersionRef
    motion_delta_spec_ref: VersionRef
    state_snapshot_ref: VersionRef
    approved_state_designation_ref: VersionRef
    active_profile_ref: VersionRef
    reference_asset_refs: tuple[VersionRef, ...] = ()
    compiler_rule_ref: VersionRef
    execution_constraints: tuple[ProviderNeutralExecutionConstraint, ...] = ()

    @field_validator("reference_asset_refs")
    @classmethod
    def normalize_reference_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        values = _unique_refs(values, "reference_asset_refs")
        for ref in values:
            if not ref.logical_id.root.startswith("reference-asset:"):
                raise ValueError("reference_asset_refs must reference canonical ReferenceAsset")
        return values

    @field_validator("execution_constraints")
    @classmethod
    def normalize_constraints(
        cls,
        values: tuple[ProviderNeutralExecutionConstraint, ...],
    ) -> tuple[ProviderNeutralExecutionConstraint, ...]:
        keys = [value.key for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("execution_constraints keys must be unique")
        return tuple(sorted(values, key=lambda value: value.key))

    @model_validator(mode="after")
    def validate_project(self) -> "ShotIRCompileRequest":
        _project_ref(
            self.full_shot_spec_ref,
            project_id=self.project_id,
            prefix="full-shot-spec:",
            label="full_shot_spec_ref",
        )
        _project_ref(
            self.static_keyframe_spec_ref,
            project_id=self.project_id,
            prefix="static-keyframe-spec:",
            label="static_keyframe_spec_ref",
        )
        _project_ref(
            self.motion_delta_spec_ref,
            project_id=self.project_id,
            prefix="motion-delta-spec:",
            label="motion_delta_spec_ref",
        )
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        if self.compiler_rule_ref.logical_id != compiler_rule_logical_id():
            raise ValueError("compiler_rule_ref must bind canonical Production Compiler rule set")
        return self


class ProductionCompileResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact: ProductionCompilerArtifact
    diagnostics: tuple[CompileDiagnostic, ...]
    hashes: CompileHashes



def build_production_compiler_provenance(
    value: CompilerValue,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    source_versions = value.source_bindings()
    rule_version = value.compiler_rule_ref if isinstance(value, ShotIR) else None
    if not source_versions and not source_refs:
        raise ProductionCompilerGateBlocked(
            "compiler rule provenance requires at least one source/evidence reference"
        )
    return Provenance(
        source_versions=source_versions,
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        rule_version=rule_version,
        correlation_id=correlation_id,
    )


class ProductionCompilerRepository:
    """Versioned ShotIR repository plus deterministic compiler service."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)
        self.realization = ShotRealizationRepository(writer)
        self.states = StateSnapshotRepository(writer)
        self.references = ReferenceAssetRepository(writer)

    async def create_rule_set(
        self,
        *,
        rule_set: CompilerRuleSet,
        provenance: Provenance,
        created_at: datetime,
    ) -> ProductionCompilerArtifact:
        if provenance.source_versions:
            raise ProductionCompilerGateBlocked(
                "CompilerRuleSet provenance may cite evidence refs but no upstream semantic source versions"
            )
        current = await self.versions.get_current(rule_set.logical_id)
        if current is None:
            metadata = SemanticRecordMetadata(
                logical_id=rule_set.logical_id,
                version_id=rule_set.version_id,
                provenance=provenance,
                created_at=created_at,
            )
            stored = await self.versions.create_initial(
                metadata=metadata,
                payload=rule_set.model_dump(mode="json"),
                status=LifecycleState.DRAFT,
            )
            artifact = ProductionCompilerArtifact(metadata=stored.metadata, value=rule_set)
        else:
            if current.version_id != rule_set.version_id:
                raise ProductionCompilerIdentityError(
                    "CompilerRuleSet logical identity already has a different current version"
                )
            artifact = await self.get_rule_set(rule_set.ref)
            if artifact is None:
                raise ProductionCompilerIdentityError("CompilerRuleSet current payload is missing")
            if artifact.value != rule_set or artifact.metadata.provenance != provenance:
                raise ProductionCompilerIdentityError(
                    "CompilerRuleSet exact replay conflicts with persisted immutable evidence"
                )
        await self._promote_exact_current(
            artifact.ref,
            status=LifecycleState.LOCKED,
            label="CompilerRuleSet",
        )
        return artifact

    async def revise_rule_set(
        self,
        *,
        rule_set: CompilerRuleSet,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ProductionCompilerArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != rule_set.logical_id:
            raise ProductionCompilerIdentityError("CompilerRuleSet successor must preserve logical identity")
        if provenance.source_versions:
            raise ProductionCompilerGateBlocked(
                "CompilerRuleSet provenance may cite evidence refs but no upstream semantic source versions"
            )
        current = await self.versions.get_current(rule_set.logical_id)
        if current is None:
            raise ProductionCompilerIdentityError("CompilerRuleSet current pointer is missing")
        replay_after_promote = current.version_id == rule_set.version_id
        if replay_after_promote:
            if current.status is not LifecycleState.LOCKED or current.revision != expected_revision + 1:
                raise ProductionCompilerIdentityError(
                    "CompilerRuleSet successor replay revision/state mismatch"
                )
        elif (
            current.version_id != predecessor.version_id
            or current.status is not LifecycleState.LOCKED
            or current.revision != expected_revision
        ):
            raise ProductionCompilerIdentityError(
                "CompilerRuleSet successor requires exact current locked predecessor/revision"
            )
        previous = await self.get_rule_set(predecessor)
        if previous is None:
            raise ProductionCompilerIdentityError("CompilerRuleSet predecessor does not exist")
        previous_payload = previous.value.model_dump(mode="json")
        current_payload = rule_set.model_dump(mode="json")
        previous_payload.pop("version_id", None)
        current_payload.pop("version_id", None)
        if previous_payload == current_payload:
            raise ProductionCompilerIdentityError("CompilerRuleSet successor requires semantic rule change")
        stored = await self.versions.get_version(rule_set.ref)
        if stored is None:
            metadata = SemanticRecordMetadata(
                logical_id=rule_set.logical_id,
                version_id=rule_set.version_id,
                predecessor=predecessor,
                provenance=provenance,
                created_at=created_at,
            )
            stored = await self.versions.create_successor(
                metadata=metadata,
                payload=rule_set.model_dump(mode="json"),
                supersession_reason=provenance.reason,
            )
        artifact = ProductionCompilerArtifact(
            metadata=stored.metadata,
            value=CompilerRuleSet.model_validate(stored.payload),
        )
        if artifact.value != rule_set or artifact.metadata.provenance != provenance:
            raise ProductionCompilerIdentityError(
                "CompilerRuleSet successor replay conflicts with persisted immutable evidence"
            )
        records = await self.invalidations.create_for_change(
            cause="PRODUCTION_COMPILER_RULE_REVISED",
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope="shot_ir_and_compiled_request_descendants",
            repair_or_recompute_requirement=(
                "Recompile ShotIR and downstream provider-specific requests with the current compiler rule set."
            ),
        )
        if not replay_after_promote:
            await self.versions.update_current(
                logical_id=rule_set.logical_id,
                version_id=rule_set.version_id,
                status=LifecycleState.LOCKED,
                expected_revision=expected_revision,
            )
        return artifact, tuple(records)

    async def get_rule_set(self, ref: VersionRef) -> ProductionCompilerArtifact | None:
        if ref.logical_id != compiler_rule_logical_id():
            raise ProductionCompilerIdentityError("expected canonical CompilerRuleSet ref")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        return ProductionCompilerArtifact(
            metadata=stored.metadata,
            value=CompilerRuleSet.model_validate(stored.payload),
        )

    async def compile_initial(
        self,
        *,
        request: ShotIRCompileRequest,
        ir_version: VersionId,
        actor_ref: str,
        reason: str,
        recorded_at: datetime,
        source_refs: tuple[str, ...] = (),
        correlation_id: str | None = None,
    ) -> ProductionCompileResult:
        context = await self._resolve_context(request)
        ir = self._build_ir(request=request, context=context, ir_version=ir_version)
        provenance = build_production_compiler_provenance(
            ir,
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=recorded_at,
            source_refs=source_refs,
            correlation_id=correlation_id,
        )
        artifact = await self._ensure_initial_draft(
            ir=ir,
            provenance=provenance,
            created_at=recorded_at,
        )
        await self._promote_exact_current(
            artifact.ref,
            status=LifecycleState.APPROVED,
            label="ShotIR",
        )
        await self._assert_current_valid(artifact.ref, "ShotIR", _ACCEPTED)
        return ProductionCompileResult(
            artifact=artifact,
            diagnostics=ir.diagnostics,
            hashes=ir.hashes,
        )

    async def recompile_successor(
        self,
        *,
        request: ShotIRCompileRequest,
        ir_version: VersionId,
        predecessor: VersionRef,
        expected_revision: int,
        actor_ref: str,
        reason: str,
        recorded_at: datetime,
        source_refs: tuple[str, ...] = (),
        correlation_id: str | None = None,
    ) -> tuple[ProductionCompileResult, tuple[InvalidationRecord, ...]]:
        context = await self._resolve_context(request)
        ir = self._build_ir(request=request, context=context, ir_version=ir_version)
        if predecessor.logical_id != ir.logical_id:
            raise ProductionCompilerIdentityError("ShotIR successor must preserve logical identity")
        provenance = build_production_compiler_provenance(
            ir,
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=recorded_at,
            source_refs=source_refs,
            correlation_id=correlation_id,
        )
        previous = await self.get_shot_ir(predecessor)
        if previous is None:
            raise ProductionCompilerIdentityError("ShotIR predecessor does not exist")
        previous_payload = previous.value.model_dump(mode="json")
        current_payload = ir.model_dump(mode="json")
        previous_payload.pop("version_id", None)
        current_payload.pop("version_id", None)
        if previous_payload == current_payload:
            raise ProductionCompilerIdentityError("ShotIR successor requires changed source/rule/constraint semantics")
        artifact, records = await self._ensure_successor_draft(
            ir=ir,
            predecessor=predecessor,
            provenance=provenance,
            created_at=recorded_at,
            expected_revision=expected_revision,
        )
        return (
            ProductionCompileResult(
                artifact=artifact,
                diagnostics=ir.diagnostics,
                hashes=ir.hashes,
            ),
            records,
        )

    async def get_shot_ir(self, ref: VersionRef) -> ProductionCompilerArtifact | None:
        if not ref.logical_id.root.startswith("shot-ir:"):
            raise ProductionCompilerIdentityError("expected ShotIR ref")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        return ProductionCompilerArtifact(
            metadata=stored.metadata,
            value=ShotIR.model_validate(stored.payload),
        )

    async def _resolve_context(self, request: ShotIRCompileRequest) -> dict[str, Any]:
        rule = await self._load_rule_current(request.compiler_rule_ref)
        full_artifact = await self.realization.get_full_shot_spec(request.full_shot_spec_ref)
        if full_artifact is None:
            raise ProductionCompilerGateBlocked("FullShotSpec exact version does not exist")
        await self._assert_current_valid(request.full_shot_spec_ref, "FullShotSpec", _ACCEPTED)
        full = full_artifact.value
        assert isinstance(full, FullShotSpec)
        if full.project_id != request.project_id:
            raise ProductionCompilerGateBlocked("FullShotSpec belongs to different project")
        await self.realization.assert_current_eligible_gate(full.eligibility_gate_ref)

        static_artifact = await self.realization.get_static_keyframe_spec(
            request.static_keyframe_spec_ref
        )
        motion_artifact = await self.realization.get_motion_delta_spec(request.motion_delta_spec_ref)
        if static_artifact is None or motion_artifact is None:
            raise ProductionCompilerGateBlocked("StaticKeyframeSpec/MotionDeltaSpec exact version is missing")
        await self._assert_current_valid(request.static_keyframe_spec_ref, "StaticKeyframeSpec", _ACCEPTED)
        await self._assert_current_valid(request.motion_delta_spec_ref, "MotionDeltaSpec", _ACCEPTED)
        static = static_artifact.value
        motion = motion_artifact.value
        assert isinstance(static, StaticKeyframeSpec)
        assert isinstance(motion, MotionDeltaSpec)
        if (
            static.project_id != request.project_id
            or motion.project_id != request.project_id
            or static.shot_ref != full.shot_ref
            or motion.shot_ref != full.shot_ref
            or static.full_shot_spec_ref != full.ref
            or motion.full_shot_spec_ref != full.ref
            or motion.static_keyframe_spec_ref != static.ref
        ):
            raise ProductionCompilerGateBlocked("FullShotSpec/static/motion exact lineage mismatch")
        if motion.duration_seconds != full.duration_seconds:
            raise ProductionCompilerGateBlocked("MotionDeltaSpec duration differs from FullShotSpec")

        if (
            request.state_snapshot_ref != full.state_snapshot_ref
            or request.approved_state_designation_ref != full.approved_state_designation_ref
            or static.state_snapshot_ref != full.state_snapshot_ref
            or static.approved_state_designation_ref != full.approved_state_designation_ref
        ):
            raise ProductionCompilerGateBlocked("compile StateSnapshot/designation pins do not match realization")
        designation = await self.states.assert_propagatable(request.state_snapshot_ref)
        if designation.ref != request.approved_state_designation_ref:
            raise ProductionCompilerGateBlocked("StateSnapshot approved designation is stale/mismatched")

        profile = await self._load_profile_current(request.active_profile_ref, request.project_id)
        if full.active_profile_ref != profile.ref:
            raise ProductionCompilerGateBlocked("FullShotSpec/profile exact lineage mismatch")

        expected_refs = tuple(sorted((item.asset_ref for item in full.reference_evidence), key=_ref_key))
        if request.reference_asset_refs != expected_refs:
            raise ProductionCompilerGateBlocked("compile ReferenceAsset pins must exactly match FullShotSpec evidence")
        static_refs = tuple(sorted(static.reference_asset_refs, key=_ref_key))
        if static_refs != expected_refs:
            raise ProductionCompilerGateBlocked(
                "StaticKeyframeSpec ReferenceAsset pins must exactly match FullShotSpec evidence"
            )
        reference_bindings: list[IRReferenceBinding] = []
        for evidence in full.reference_evidence:
            asset = await self._load_reference_current(evidence)
            reference_bindings.append(
                IRReferenceBinding(
                    role=evidence.role,
                    asset_ref=asset.ref,
                    entity_ref=asset.entity_ref,
                    content_hash=asset.content_hash,
                )
            )

        declared_sources = {
            _ref_key(full.ref),
            _ref_key(static.ref),
            _ref_key(motion.ref),
            _ref_key(full.state_snapshot_ref),
            _ref_key(full.approved_state_designation_ref),
            _ref_key(full.active_profile_ref),
            _ref_key(rule.ref),
            *(_ref_key(item.asset_ref) for item in reference_bindings),
        }
        for constraint in request.execution_constraints:
            if any(_ref_key(ref) not in declared_sources for ref in constraint.source_refs):
                raise ProductionCompilerGateBlocked(
                    "execution constraint source_refs must be pinned compiler inputs"
                )

        return {
            "rule": rule,
            "full": full,
            "static": static,
            "motion": motion,
            "profile": profile,
            "references": tuple(
                sorted(
                    reference_bindings,
                    key=lambda value: (_ref_key(value.asset_ref), value.role),
                )
            ),
        }

    def _build_ir(
        self,
        *,
        request: ShotIRCompileRequest,
        context: dict[str, Any],
        ir_version: VersionId,
    ) -> ShotIR:
        rule: CompilerRuleSet = context["rule"]
        full: FullShotSpec = context["full"]
        static: StaticKeyframeSpec = context["static"]
        motion: MotionDeltaSpec = context["motion"]
        references: tuple[IRReferenceBinding, ...] = context["references"]

        static_state = IRStaticState(
            state_summary=static.state_summary,
            composition=static.composition,
            visible_performance=static.visible_performance,
            environment_state=static.environment_state,
            lighting_state=static.lighting_state,
            visible_subject_refs=static.visible_subject_refs,
        )
        motion_delta = IRMotionDelta(
            duration_seconds=motion.duration_seconds,
            action_delta=motion.action_delta,
            performance_delta=motion.performance_delta,
            blocking_delta=motion.blocking_delta,
            camera_movement_delta=motion.camera_movement_delta,
            continuity_requirements=motion.continuity_requirements,
        )
        qa = self._qa_expectations(full=full, static=static, motion=motion, references=references)
        diagnostics = self._diagnostics(
            full=full,
            static=static,
            motion=motion,
            rule=rule,
            references=references,
        )
        draft = ShotIR.model_construct(
            project_id=request.project_id,
            shot_ir_id=shot_ir_logical_id(request.project_id, full.shot_ref.logical_id),
            version_id=ir_version,
            shot_ref=full.shot_ref,
            full_shot_spec_ref=full.ref,
            eligibility_gate_ref=full.eligibility_gate_ref,
            static_keyframe_spec_ref=static.ref,
            motion_delta_spec_ref=motion.ref,
            state_snapshot_ref=full.state_snapshot_ref,
            approved_state_designation_ref=full.approved_state_designation_ref,
            active_profile_ref=full.active_profile_ref,
            compiler_rule_ref=rule.ref,
            reference_bindings=references,
            semantic_layers=full.layers,
            static_state=static_state,
            motion_delta=motion_delta,
            execution_constraints=request.execution_constraints,
            qa_expectations=qa,
            diagnostics=diagnostics,
            hashes=CompileHashes(
                input_fingerprint="sha256:" + "0" * 64,
                semantic_ir_hash="sha256:" + "0" * 64,
                static_request_hash="sha256:" + "0" * 64,
                motion_request_hash="sha256:" + "0" * 64,
            ),
        )
        return ShotIR.model_validate(
            {
                **draft.model_dump(mode="python"),
                "hashes": draft.compute_hashes().model_dump(mode="python"),
            }
        )

    @staticmethod
    def _qa_expectations(
        *,
        full: FullShotSpec,
        static: StaticKeyframeSpec,
        motion: MotionDeltaSpec,
        references: tuple[IRReferenceBinding, ...],
    ) -> tuple[IRQAExpectation, ...]:
        values = [
            IRQAExpectation(
                code="SHOT_IDENTITY_PRESERVED",
                expectation="Generated artifacts must remain attributable to the exact canonical shot_id.",
                source_refs=(full.shot_ref, full.ref),
            ),
            IRQAExpectation(
                code="APPROVED_STATE_PRESERVED",
                expectation="Observable output must not contradict the exact approved StateSnapshot/designation.",
                source_refs=(full.state_snapshot_ref, full.approved_state_designation_ref),
            ),
            IRQAExpectation(
                code="STATIC_MOTION_BOUNDARY_PRESERVED",
                expectation="Motion may change only declared temporal deltas and must not silently redefine the static start state.",
                source_refs=(static.ref, motion.ref),
            ),
        ]
        if references:
            values.append(
                IRQAExpectation(
                    code="REFERENCE_HASHES_PRESERVED",
                    expectation="Resolved visual references must match the exact ReferenceAsset versions/content hashes bound by ShotIR.",
                    source_refs=tuple(item.asset_ref for item in references),
                )
            )
        return tuple(sorted(values, key=lambda value: value.code))

    @staticmethod
    def _diagnostics(
        *,
        full: FullShotSpec,
        static: StaticKeyframeSpec,
        motion: MotionDeltaSpec,
        rule: CompilerRuleSet,
        references: tuple[IRReferenceBinding, ...],
    ) -> tuple[CompileDiagnostic, ...]:
        values = [
            CompileDiagnostic(
                code="CANONICAL_INPUTS_PINNED",
                severity=CompileDiagnosticSeverity.INFO,
                message="FullShotSpec, static start state, motion delta, state/profile and compiler rule are exact-version pinned.",
                source_refs=(full.ref, static.ref, motion.ref, full.active_profile_ref, rule.ref),
            ),
            CompileDiagnostic(
                code="PROVIDER_NEUTRAL_IR",
                severity=CompileDiagnosticSeverity.INFO,
                message="ShotIR contains canonical execution semantics only; provider capability/routing fields are deferred downstream.",
                source_refs=(full.ref, rule.ref),
            ),
        ]
        if not references:
            values.append(
                CompileDiagnostic(
                    code="NO_REFERENCE_ASSETS_REQUIRED",
                    severity=CompileDiagnosticSeverity.INFO,
                    message="This exact FullShotSpec compiles without selected ReferenceAsset conditioning.",
                    source_refs=(full.ref,),
                )
            )
        return tuple(sorted(values, key=lambda value: (value.severity.value, value.code)))

    async def _load_rule_current(self, ref: VersionRef) -> CompilerRuleSet:
        await self._assert_current_valid(ref, "CompilerRuleSet", {LifecycleState.LOCKED})
        artifact = await self.get_rule_set(ref)
        if artifact is None:
            raise ProductionCompilerGateBlocked("CompilerRuleSet exact version does not exist")
        rule = artifact.value
        assert isinstance(rule, CompilerRuleSet)
        return rule

    async def _load_profile_current(
        self,
        ref: VersionRef,
        project_id: LogicalId,
    ) -> ActiveProductionProfile:
        if ref.logical_id != _active_profile_id(project_id):
            raise ProductionCompilerGateBlocked("ActiveProductionProfile belongs to different project")
        await self._assert_current_valid(ref, "ActiveProductionProfile", {LifecycleState.LOCKED})
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise ProductionCompilerGateBlocked("ActiveProductionProfile exact version does not exist")
        try:
            profile = ActiveProductionProfile.model_validate(stored.payload)
        except Exception as exc:
            raise ProductionCompilerGateBlocked("ActiveProductionProfile payload is invalid") from exc
        if profile.project_id != project_id:
            raise ProductionCompilerGateBlocked("ActiveProductionProfile payload project mismatch")
        return profile

    async def _load_reference_current(
        self,
        evidence: ResolvedReferenceEvidence,
    ) -> ReferenceAsset:
        await self._assert_current_valid(evidence.asset_ref, "ReferenceAsset", _ACCEPTED)
        artifact = await self.references.get_version(evidence.asset_ref)
        if artifact is None:
            raise ProductionCompilerGateBlocked("ReferenceAsset exact version does not exist")
        asset = artifact.value
        if (
            asset.entity_ref != evidence.entity_ref
            or asset.role != evidence.role
            or asset.content_hash != evidence.content_hash
        ):
            raise ProductionCompilerGateBlocked(
                "ReferenceAsset exact content/role/entity does not match FullShotSpec evidence"
            )
        return asset

    async def _assert_current_valid(
        self,
        ref: VersionRef,
        label: str,
        allowed: set[LifecycleState],
    ) -> CurrentVersionPointer:
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise ProductionCompilerGateBlocked(f"{label} exact version does not exist")
        try:
            pointer = await self.versions.get_current(ref.logical_id)
        except CurrentPointerNotFound as exc:
            raise ProductionCompilerGateBlocked(f"{label} current pointer is missing") from exc
        if (
            pointer is None
            or pointer.version_id != ref.version_id
            or pointer.status not in allowed
        ):
            raise ProductionCompilerGateBlocked(f"{label} is not exact current accepted version")
        for record in await self.invalidations.list_unresolved():
            if (
                record.affected_object_id == ref.logical_id
                and record.affected_object_version == ref.version_id
            ):
                raise ProductionCompilerGateBlocked(f"{label} has unresolved durable invalidation")
        return pointer

    async def _ensure_initial_draft(
        self,
        *,
        ir: ShotIR,
        provenance: Provenance,
        created_at: datetime,
    ) -> ProductionCompilerArtifact:
        if provenance.source_versions != ir.source_bindings():
            raise ProductionCompilerGateBlocked("ShotIR provenance must exactly bind declared source versions")
        current = await self.versions.get_current(ir.logical_id)
        if current is None:
            metadata = SemanticRecordMetadata(
                logical_id=ir.logical_id,
                version_id=ir.version_id,
                provenance=provenance,
                created_at=created_at,
            )
            stored = await self.versions.create_initial(
                metadata=metadata,
                payload=ir.model_dump(mode="json"),
                status=LifecycleState.DRAFT,
            )
            artifact = ProductionCompilerArtifact(metadata=stored.metadata, value=ir)
        else:
            if current.version_id != ir.version_id:
                raise ProductionCompilerIdentityError(
                    "ShotIR logical identity already has a different current version"
                )
            stored = await self.versions.get_version(ir.ref)
            if stored is None:
                raise ProductionCompilerIdentityError("ShotIR current payload is missing")
            existing = ProductionCompilerArtifact(
                metadata=stored.metadata,
                value=ShotIR.model_validate(stored.payload),
            )
            if existing.value != ir or existing.metadata.provenance != provenance:
                raise ProductionCompilerIdentityError(
                    "ShotIR exact replay conflicts with persisted immutable compile evidence"
                )
            artifact = existing
        await self._register_dependencies(artifact)
        return artifact

    async def _ensure_successor_draft(
        self,
        *,
        ir: ShotIR,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ProductionCompilerArtifact, tuple[InvalidationRecord, ...]]:
        if provenance.source_versions != ir.source_bindings():
            raise ProductionCompilerGateBlocked("ShotIR provenance must exactly bind declared source versions")
        current = await self.versions.get_current(ir.logical_id)
        if current is None:
            raise ProductionCompilerIdentityError("ShotIR current pointer is missing")
        replay_after_promote = current.version_id == ir.version_id
        if replay_after_promote:
            if current.status not in _ACCEPTED or current.revision != expected_revision + 1:
                raise ProductionCompilerIdentityError("ShotIR successor replay revision/state mismatch")
        elif (
            current.version_id != predecessor.version_id
            or current.status not in _ACCEPTED
            or current.revision != expected_revision
        ):
            raise ProductionCompilerIdentityError(
                "ShotIR successor requires exact current accepted predecessor/revision"
            )
        stored = await self.versions.get_version(ir.ref)
        if stored is None:
            metadata = SemanticRecordMetadata(
                logical_id=ir.logical_id,
                version_id=ir.version_id,
                predecessor=predecessor,
                provenance=provenance,
                created_at=created_at,
            )
            stored = await self.versions.create_successor(
                metadata=metadata,
                payload=ir.model_dump(mode="json"),
                supersession_reason=provenance.reason,
            )
        artifact = ProductionCompilerArtifact(
            metadata=stored.metadata,
            value=ShotIR.model_validate(stored.payload),
        )
        if artifact.value != ir or artifact.metadata.provenance != provenance:
            raise ProductionCompilerIdentityError(
                "ShotIR successor replay conflicts with persisted immutable compile evidence"
            )
        await self._register_dependencies(artifact)
        records = await self.invalidations.create_for_change(
            cause="SHOT_IR_RECOMPILED",
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope="compiled_request_and_generation_descendants",
            repair_or_recompute_requirement=(
                "Re-run provider capability lowering and rebuild dependent compiled requests/jobs from current ShotIR."
            ),
        )
        if not replay_after_promote:
            await self.versions.update_current(
                logical_id=ir.logical_id,
                version_id=ir.version_id,
                status=LifecycleState.APPROVED,
                expected_revision=expected_revision,
            )
        await self._assert_current_valid(artifact.ref, "ShotIR", _ACCEPTED)
        return artifact, tuple(records)

    async def _register_dependencies(self, artifact: ProductionCompilerArtifact) -> None:
        if not isinstance(artifact.value, ShotIR):
            return
        for binding in artifact.value.source_bindings():
            await self.graph.create_edge(
                source=binding.source,
                dependent=artifact.ref,
                edge_type="production_compiler_source",
                dependency_reason=f"production_compiler_source:{binding.role}",
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _promote_exact_current(
        self,
        ref: VersionRef,
        *,
        status: LifecycleState,
        label: str,
    ) -> CurrentVersionPointer:
        pointer = await self.versions.get_current(ref.logical_id)
        if pointer is None or pointer.version_id != ref.version_id:
            raise ProductionCompilerIdentityError(f"{label} current pointer changed during promotion")
        if pointer.status == status:
            return pointer
        if pointer.status is not LifecycleState.DRAFT:
            raise ProductionCompilerIdentityError(
                f"{label} can promote only its exact DRAFT current version"
            )
        return await self.versions.update_current(
            logical_id=ref.logical_id,
            version_id=ref.version_id,
            status=status,
            expected_revision=pointer.revision,
        )
