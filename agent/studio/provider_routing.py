"""IMP-050 evidence-versioned provider capability registry and deterministic router.

This module implements Frozen Master sections 65-66. Provider capability evidence
is canonical only inside the provider boundary; it cannot rewrite ShotIR or other
upstream semantic truth. Routing is deterministic and side-effect-free: no network
or provider call occurs while profiles/routing evidence are persisted.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .active_profile import (
    ActiveProductionProfile,
    ActiveProductionProfileDependencyBinder,
)
from .invalidation import DependencyGraphRepository, InvalidationRecord, InvalidationRepository
from .observability import EvidenceReference
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
from .production_compiler import ProductionCompilerRepository, ShotIR
from .versioning import VersionRepository


_ACCEPTED = {LifecycleState.APPROVED, LifecycleState.LOCKED}
_TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")
_FACT_KEY_RE = re.compile(r"^[a-z][a-z0-9_.:-]{1,127}$")
_ROUTING_RULE_ID = LogicalId("provider-routing-rule")
_PROFILE_POLICY_PATHS = {
    "allowed_provider_keys": "provider.routing.allowed_provider_keys",
    "allow_degradation_keys": "provider.routing.allow_degradation_keys",
    "allow_degraded_availability": "provider.routing.allow_degraded_availability",
    "max_cost_micros": "provider.routing.max_cost_micros",
    "currency": "provider.routing.currency",
    "require_reconcile": "provider.routing.require_reconcile",
}


def _trimmed(value: str, label: str) -> str:
    value = str(value).strip()
    if not value:
        raise ValueError(f"{label} must be non-empty")
    return value


def _token(value: str, label: str) -> str:
    value = _trimmed(value, label).lower()
    if not _TOKEN_RE.fullmatch(value):
        raise ValueError(f"{label} must be a lowercase provider token")
    return value


def _fact_key(value: str) -> str:
    value = _trimmed(value, "fact key").lower()
    if not _FACT_KEY_RE.fullmatch(value):
        raise ValueError("fact key must be a lowercase dotted/token key")
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonicalize_json_text(value: str, label: str) -> str:
    value = _trimmed(value, label)
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON") from exc
    return _canonical_json(parsed)


def _hash_payload(value: Any) -> str:
    raw = _canonical_json(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return (ref.logical_id.root, ref.version_id.root)


def _active_profile_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"active-profile:{project_id.root}")


def provider_profile_logical_id(
    provider_key: str,
    surface: str,
    region: str,
    model_family: str,
    model_version: str,
) -> LogicalId:
    identity = {
        "provider": _token(provider_key, "provider_key"),
        "surface": _token(surface, "surface"),
        "region": _token(region, "region"),
        "model_family": _token(model_family, "model_family"),
        "model_version": _token(model_version, "model_version"),
    }
    digest = hashlib.sha256(_canonical_json(identity).encode("utf-8")).hexdigest()[:32]
    return LogicalId(f"provider-profile:{digest}")


def provider_routing_rule_logical_id() -> LogicalId:
    return _ROUTING_RULE_ID


def provider_route_decision_logical_id(project_id: LogicalId, shot_ir_id: LogicalId) -> LogicalId:
    digest = hashlib.sha256(shot_ir_id.root.encode("utf-8")).hexdigest()[:32]
    return LogicalId(f"provider-route:{project_id.root}:{digest}")


class ProviderRoutingError(ValueError):
    """Base error for IMP-050 provider capability/routing authority."""


class ProviderRoutingIdentityError(ProviderRoutingError):
    """Raised when immutable profile/decision identity conflicts."""


class ProviderRoutingGateBlocked(ProviderRoutingError):
    """Raised when required exact-current authority is missing/stale."""


class CapabilitySupport(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


class ProviderFactKind(str, Enum):
    CAPABILITY = "CAPABILITY"
    LIMIT = "LIMIT"
    COST = "COST"
    RECOVERY = "RECOVERY"


class ProviderAvailabilityState(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class RequirementOperator(str, Enum):
    SUPPORTED = "SUPPORTED"
    EQUALS = "EQUALS"
    CONTAINS = "CONTAINS"
    AT_LEAST = "AT_LEAST"
    AT_MOST = "AT_MOST"


class RequirementDisposition(str, Enum):
    SATISFIED = "SATISFIED"
    DEGRADED = "DEGRADED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"
    MISMATCH = "MISMATCH"


class RoutingVerdict(str, Enum):
    SELECTED = "SELECTED"
    NO_ELIGIBLE_PROVIDER = "NO_ELIGIBLE_PROVIDER"


class ProviderEvidenceFact(BaseModel):
    """One evidence-backed capability/limit/cost/recovery fact.

    UNKNOWN is first-class. A missing/unknown fact is never upgraded to support by
    provider brand/model assumptions.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: ProviderFactKind
    key: str
    support: CapabilitySupport
    value_json: str | None = None
    evidence: EvidenceReference
    verified_at: datetime
    expires_at: datetime

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        return _fact_key(value)

    @field_validator("value_json")
    @classmethod
    def canonicalize_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _canonicalize_json_text(value, "provider fact value_json")

    @model_validator(mode="after")
    def validate_fact(self) -> "ProviderEvidenceFact":
        if self.verified_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("provider fact timestamps must be timezone-aware")
        if self.expires_at <= self.verified_at:
            raise ValueError("provider fact expires_at must be after verified_at")
        if self.support is not CapabilitySupport.SUPPORTED and self.value_json is not None:
            raise ValueError("UNSUPPORTED/UNKNOWN provider facts cannot carry guessed value_json")
        return self

    @property
    def value(self) -> Any:
        return None if self.value_json is None else json.loads(self.value_json)


class ProviderAvailabilityEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    state: ProviderAvailabilityState
    evidence: EvidenceReference
    verified_at: datetime
    expires_at: datetime
    detail: str | None = None

    @field_validator("detail")
    @classmethod
    def normalize_detail(cls, value: str | None) -> str | None:
        return None if value is None else _trimmed(value, "availability detail")

    @model_validator(mode="after")
    def validate_window(self) -> "ProviderAvailabilityEvidence":
        if self.verified_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("availability timestamps must be timezone-aware")
        if self.expires_at <= self.verified_at:
            raise ValueError("availability expires_at must be after verified_at")
        return self


class ProviderProfile(BaseModel):
    """Immutable evidence-versioned provider capability profile."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_profile_id: LogicalId
    profile_version: VersionId
    provider_key: str
    surface: str
    region: str
    model_family: str
    model_version: str
    verified_at: datetime
    expires_at: datetime
    facts: tuple[ProviderEvidenceFact, ...] = Field(min_length=1)
    availability: ProviderAvailabilityEvidence

    @field_validator("provider_key", "surface", "region", "model_family", "model_version")
    @classmethod
    def normalize_identity_token(cls, value: str, info) -> str:
        return _token(value, info.field_name)

    @field_validator("facts")
    @classmethod
    def normalize_facts(cls, values: tuple[ProviderEvidenceFact, ...]) -> tuple[ProviderEvidenceFact, ...]:
        keys = [value.key for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("ProviderProfile facts must have unique keys")
        return tuple(sorted(values, key=lambda value: value.key))

    @model_validator(mode="after")
    def validate_profile(self) -> "ProviderProfile":
        expected = provider_profile_logical_id(
            self.provider_key,
            self.surface,
            self.region,
            self.model_family,
            self.model_version,
        )
        if self.provider_profile_id != expected:
            raise ValueError(f"provider_profile_id must be {expected.root}")
        if self.verified_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("ProviderProfile timestamps must be timezone-aware")
        if self.expires_at <= self.verified_at:
            raise ValueError("ProviderProfile expires_at must be after verified_at")
        if self.availability.verified_at > self.verified_at:
            raise ValueError("ProviderProfile verified_at must include availability evidence")
        if self.availability.expires_at < self.expires_at:
            raise ValueError("ProviderProfile validity cannot outlive availability evidence")
        for fact in self.facts:
            if fact.verified_at > self.verified_at:
                raise ValueError("ProviderProfile verified_at must include all fact evidence")
            if fact.expires_at < self.expires_at:
                raise ValueError("ProviderProfile validity cannot outlive fact evidence")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.provider_profile_id

    @property
    def version_id(self) -> VersionId:
        return self.profile_version

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.profile_version)

    @property
    def evidence_ids(self) -> tuple[str, ...]:
        ids = [self.availability.evidence.evidence_id]
        ids.extend(fact.evidence.evidence_id for fact in self.facts)
        return tuple(sorted(set(ids)))

    def fact_map(self) -> dict[str, ProviderEvidenceFact]:
        return {fact.key: fact for fact in self.facts}

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return ()


class ProviderRequirement(BaseModel):
    """Provider-neutral requirement derived from exact ShotIR/policy inputs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    operator: RequirementOperator
    expected_value_json: str | None = None
    degradable: bool = False
    source_refs: tuple[VersionRef, ...] = Field(min_length=1)

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        return _fact_key(value)

    @field_validator("expected_value_json")
    @classmethod
    def canonicalize_expected(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _canonicalize_json_text(value, "requirement expected_value_json")

    @field_validator("source_refs")
    @classmethod
    def normalize_sources(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        ordered = sorted(set(_ref_key(value) for value in values))
        return tuple(VersionRef(logical_id=LogicalId(a), version_id=VersionId(b)) for a, b in ordered)

    @model_validator(mode="after")
    def validate_requirement(self) -> "ProviderRequirement":
        if self.operator is RequirementOperator.SUPPORTED:
            if self.expected_value_json is not None:
                raise ValueError("SUPPORTED requirement cannot carry expected_value_json")
        elif self.expected_value_json is None:
            raise ValueError(f"{self.operator.value} requirement requires expected_value_json")
        return self

    @property
    def expected_value(self) -> Any:
        return None if self.expected_value_json is None else json.loads(self.expected_value_json)


class ProviderRoutingRuleSet(BaseModel):
    """Versioned deterministic evaluator semantics; contains no provider preference."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    routing_rule_id: LogicalId
    version_id: VersionId
    algorithm: str = "strict-capability-evidence-v1"
    unknown_is_ineligible: bool = True
    unsupported_is_ineligible: bool = True
    tie_breaker: str = "fewest-degradations-then-profile-identity"

    @field_validator("algorithm", "tie_breaker")
    @classmethod
    def normalize_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_rule(self) -> "ProviderRoutingRuleSet":
        if self.routing_rule_id != provider_routing_rule_logical_id():
            raise ValueError("routing_rule_id must bind canonical Provider Router rule set")
        if not self.unknown_is_ineligible or not self.unsupported_is_ineligible:
            raise ValueError("IMP-050 cannot authorize UNKNOWN/UNSUPPORTED as eligible")
        if self.algorithm != "strict-capability-evidence-v1":
            raise ValueError("unsupported Provider Router algorithm")
        if self.tie_breaker != "fewest-degradations-then-profile-identity":
            raise ValueError("unsupported Provider Router tie_breaker")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.routing_rule_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return ()


class RequirementEvaluation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    operator: RequirementOperator
    disposition: RequirementDisposition
    message: str
    fact_evidence_id: str | None = None

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        return _fact_key(value)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        return _trimmed(value, "requirement evaluation message")


class ProviderCandidateEvaluation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_profile_ref: VersionRef
    eligible: bool
    availability_state: ProviderAvailabilityState
    requirement_evaluations: tuple[RequirementEvaluation, ...] = ()
    degradation_keys: tuple[str, ...] = ()
    rejection_reasons: tuple[str, ...] = ()

    @field_validator("degradation_keys")
    @classmethod
    def normalize_degradations(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(sorted({_fact_key(value) for value in values}))
        return normalized

    @field_validator("rejection_reasons")
    @classmethod
    def normalize_reasons(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(sorted({_trimmed(value, "rejection reason") for value in values}))
        return normalized

    @field_validator("requirement_evaluations")
    @classmethod
    def normalize_evaluations(
        cls, values: tuple[RequirementEvaluation, ...]
    ) -> tuple[RequirementEvaluation, ...]:
        return tuple(sorted(values, key=lambda value: (value.key, value.operator.value)))


class ProviderRouteRequest(BaseModel):
    """Side-effect-free deterministic routing inputs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    shot_ir_ref: VersionRef
    active_profile_ref: VersionRef
    routing_rule_ref: VersionRef
    surface: str
    region: str
    candidate_profile_refs: tuple[VersionRef, ...] = ()
    requirements: tuple[ProviderRequirement, ...] = ()
    evaluated_at: datetime
    run_correlation_id: str

    @field_validator("surface", "region")
    @classmethod
    def normalize_route_token(cls, value: str, info) -> str:
        return _token(value, info.field_name)

    @field_validator("run_correlation_id")
    @classmethod
    def normalize_correlation(cls, value: str) -> str:
        return LogicalId(value).root

    @field_validator("candidate_profile_refs")
    @classmethod
    def normalize_candidates(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        keys = sorted(set(_ref_key(value) for value in values))
        if len(keys) != len(values):
            raise ValueError("candidate_profile_refs must not duplicate exact profiles")
        for logical_id, _ in keys:
            if not logical_id.startswith("provider-profile:"):
                raise ValueError("candidate_profile_refs must reference ProviderProfile")
        return tuple(VersionRef(logical_id=LogicalId(a), version_id=VersionId(b)) for a, b in keys)

    @field_validator("requirements")
    @classmethod
    def normalize_requirements(
        cls, values: tuple[ProviderRequirement, ...]
    ) -> tuple[ProviderRequirement, ...]:
        keys = [(value.key, value.operator.value) for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("requirements must not duplicate key/operator")
        return tuple(sorted(values, key=lambda value: (value.key, value.operator.value)))

    @model_validator(mode="after")
    def validate_request(self) -> "ProviderRouteRequest":
        if self.evaluated_at.tzinfo is None:
            raise ValueError("evaluated_at must be timezone-aware")
        if not self.shot_ir_ref.logical_id.root.startswith("shot-ir:"):
            raise ValueError("shot_ir_ref must reference canonical ShotIR")
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        if self.routing_rule_ref.logical_id != provider_routing_rule_logical_id():
            raise ValueError("routing_rule_ref must bind canonical routing rule set")
        for requirement in self.requirements:
            if self.shot_ir_ref not in requirement.source_refs:
                raise ValueError("each explicit routing requirement must cite exact ShotIR source")
        return self


class ProviderRoutingDecision(BaseModel):
    """Immutable routing evidence. It never changes canonical shot intent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    routing_decision_id: LogicalId
    version_id: VersionId
    shot_ir_ref: VersionRef
    active_profile_ref: VersionRef
    routing_rule_ref: VersionRef
    surface: str
    region: str
    candidate_profile_refs: tuple[VersionRef, ...]
    requirements: tuple[ProviderRequirement, ...]
    evaluated_at: datetime
    run_correlation_id: str
    policy_hash: str
    candidate_evaluations: tuple[ProviderCandidateEvaluation, ...]
    verdict: RoutingVerdict
    selected_profile_ref: VersionRef | None = None
    rationale: str
    decision_hash: str

    @field_validator("surface", "region")
    @classmethod
    def normalize_route_token(cls, value: str, info) -> str:
        return _token(value, info.field_name)

    @field_validator("run_correlation_id")
    @classmethod
    def normalize_correlation(cls, value: str) -> str:
        return LogicalId(value).root

    @field_validator("rationale")
    @classmethod
    def normalize_rationale(cls, value: str) -> str:
        return _trimmed(value, "routing rationale")

    @field_validator("policy_hash", "decision_hash")
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
            raise ValueError("routing hashes must be sha256:<64 lowercase hex>")
        return value

    @field_validator("candidate_profile_refs")
    @classmethod
    def normalize_candidate_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        keys = sorted(set(_ref_key(value) for value in values))
        if len(keys) != len(values):
            raise ValueError("candidate_profile_refs must be unique")
        for logical_id, _ in keys:
            if not logical_id.startswith("provider-profile:"):
                raise ValueError("candidate_profile_refs must reference ProviderProfile")
        return tuple(VersionRef(logical_id=LogicalId(a), version_id=VersionId(b)) for a, b in keys)

    @field_validator("requirements")
    @classmethod
    def normalize_requirements(
        cls, values: tuple[ProviderRequirement, ...]
    ) -> tuple[ProviderRequirement, ...]:
        keys = [(value.key, value.operator.value) for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("requirements must not duplicate key/operator")
        return tuple(sorted(values, key=lambda value: (value.key, value.operator.value)))

    @field_validator("candidate_evaluations")
    @classmethod
    def normalize_candidate_evaluations(
        cls, values: tuple[ProviderCandidateEvaluation, ...]
    ) -> tuple[ProviderCandidateEvaluation, ...]:
        keys = [_ref_key(value.provider_profile_ref) for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("candidate_evaluations must be unique by ProviderProfile")
        return tuple(sorted(values, key=lambda value: _ref_key(value.provider_profile_ref)))

    @model_validator(mode="after")
    def validate_decision(self) -> "ProviderRoutingDecision":
        if self.evaluated_at.tzinfo is None:
            raise ValueError("evaluated_at must be timezone-aware")
        if not self.shot_ir_ref.logical_id.root.startswith("shot-ir:"):
            raise ValueError("shot_ir_ref must reference canonical ShotIR")
        for requirement in self.requirements:
            if self.shot_ir_ref not in requirement.source_refs:
                raise ValueError("each routing requirement must cite exact ShotIR source")
        expected = provider_route_decision_logical_id(self.project_id, self.shot_ir_ref.logical_id)
        if self.routing_decision_id != expected:
            raise ValueError(f"routing_decision_id must be {expected.root}")
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("active_profile_ref must bind this project")
        if self.routing_rule_ref.logical_id != provider_routing_rule_logical_id():
            raise ValueError("routing_rule_ref must bind canonical routing rule set")
        candidate_set = set(self.candidate_profile_refs)
        evaluation_set = {item.provider_profile_ref for item in self.candidate_evaluations}
        if candidate_set != evaluation_set:
            raise ValueError("candidate evaluations must cover every exact candidate profile")
        eligible = {
            item.provider_profile_ref
            for item in self.candidate_evaluations
            if item.eligible
        }
        if self.verdict is RoutingVerdict.SELECTED:
            if self.selected_profile_ref is None or self.selected_profile_ref not in eligible:
                raise ValueError("SELECTED routing verdict requires one eligible selected ProviderProfile")
        elif self.selected_profile_ref is not None or eligible:
            raise ValueError("NO_ELIGIBLE_PROVIDER cannot hide an eligible/selected profile")
        expected_hash = self.compute_decision_hash()
        if self.decision_hash != expected_hash:
            raise ValueError("decision_hash does not match exact routing evidence")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return self.routing_decision_id

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values: list[SourceVersionBinding] = [
            SourceVersionBinding(role="shot_ir", source=self.shot_ir_ref),
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="provider_routing_rule", source=self.routing_rule_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"candidate_profile_{index:03d}", source=ref)
            for index, ref in enumerate(self.candidate_profile_refs)
        )
        seen = {_ref_key(binding.source) for binding in values}
        for requirement in self.requirements:
            for ref in requirement.source_refs:
                if _ref_key(ref) in seen:
                    continue
                seen.add(_ref_key(ref))
                values.append(
                    SourceVersionBinding(role=f"requirement_source_{len(values):03d}", source=ref)
                )
        return tuple(values)

    def compute_decision_hash(self) -> str:
        payload = self.model_dump(mode="json", exclude={"decision_hash"})
        return _hash_payload(payload)


ProviderRoutingValue: TypeAlias = ProviderProfile | ProviderRoutingRuleSet | ProviderRoutingDecision


class ProviderRoutingArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: ProviderRoutingValue

    @model_validator(mode="after")
    def validate_identity(self) -> "ProviderRoutingArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("provider routing metadata logical_id mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("provider routing metadata version mismatch")
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(
            logical_id=self.metadata.logical_id,
            version_id=self.metadata.version_id,
        )


def build_provider_routing_provenance(
    value: ProviderRoutingValue,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    rule_version: VersionRef | None = None,
    correlation_id: str | None = None,
) -> Provenance:
    source_versions = value.source_bindings()
    if isinstance(value, ProviderRoutingDecision):
        rule_version = value.routing_rule_ref
    return Provenance(
        source_versions=source_versions,
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        rule_version=rule_version,
        correlation_id=correlation_id,
    )


class ProviderCapabilityRoutingRepository:
    """ProviderProfile registry plus deterministic provider routing evidence."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)
        self.profile_binder = ActiveProductionProfileDependencyBinder(self.graph)
        self.compiler = ProductionCompilerRepository(writer)

    async def create_profile(
        self,
        *,
        profile: ProviderProfile,
        provenance: Provenance,
        created_at: datetime,
    ) -> ProviderRoutingArtifact:
        self._assert_profile_provenance(profile, provenance)
        artifact = await self._ensure_initial(
            value=profile,
            provenance=provenance,
            created_at=created_at,
            status=LifecycleState.APPROVED,
            label="ProviderProfile",
        )
        return artifact

    async def revise_profile(
        self,
        *,
        profile: ProviderProfile,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ProviderRoutingArtifact, tuple[InvalidationRecord, ...]]:
        self._assert_profile_provenance(profile, provenance)
        return await self._revise_simple(
            value=profile,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            status=LifecycleState.APPROVED,
            label="ProviderProfile",
            cause="PROVIDER_PROFILE_REVISED",
            scope="routing_and_provider_lowering_descendants",
            repair="Re-evaluate routing/admission/lowering with current ProviderProfile evidence.",
        )

    async def create_routing_rule(
        self,
        *,
        rule: ProviderRoutingRuleSet,
        provenance: Provenance,
        created_at: datetime,
    ) -> ProviderRoutingArtifact:
        if provenance.source_versions:
            raise ProviderRoutingGateBlocked(
                "ProviderRoutingRuleSet provenance may cite evidence refs but no semantic source versions"
            )
        return await self._ensure_initial(
            value=rule,
            provenance=provenance,
            created_at=created_at,
            status=LifecycleState.LOCKED,
            label="ProviderRoutingRuleSet",
        )

    async def revise_routing_rule(
        self,
        *,
        rule: ProviderRoutingRuleSet,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ProviderRoutingArtifact, tuple[InvalidationRecord, ...]]:
        if provenance.source_versions:
            raise ProviderRoutingGateBlocked(
                "ProviderRoutingRuleSet provenance may cite evidence refs but no semantic source versions"
            )
        return await self._revise_simple(
            value=rule,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            status=LifecycleState.LOCKED,
            label="ProviderRoutingRuleSet",
            cause="PROVIDER_ROUTING_RULE_REVISED",
            scope="routing_decision_descendants",
            repair="Re-evaluate provider routing with the current routing rule set.",
        )

    async def route_initial(
        self,
        *,
        request: ProviderRouteRequest,
        decision_version: VersionId,
        actor_ref: str,
        reason: str,
        recorded_at: datetime,
        source_refs: tuple[str, ...] = (),
    ) -> ProviderRoutingArtifact:
        context = await self._resolve_route_context(request)
        decision = await self._build_decision(
            request=request,
            context=context,
            decision_version=decision_version,
        )
        provenance = build_provider_routing_provenance(
            decision,
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=recorded_at,
            source_refs=source_refs,
            correlation_id=request.run_correlation_id,
        )
        artifact = await self._ensure_initial(
            value=decision,
            provenance=provenance,
            created_at=recorded_at,
            status=LifecycleState.DRAFT,
            label="ProviderRoutingDecision",
            promote=False,
        )
        await self._register_dependencies(artifact)
        await self._bind_profile_policy(
            profile=context["active_profile"],
            dependent=artifact.ref,
            provenance=provenance,
            created_at=recorded_at,
        )
        await self._promote_exact_current(
            artifact.ref,
            status=LifecycleState.APPROVED,
            label="ProviderRoutingDecision",
        )
        return artifact

    async def reroute_successor(
        self,
        *,
        request: ProviderRouteRequest,
        decision_version: VersionId,
        predecessor: VersionRef,
        expected_revision: int,
        actor_ref: str,
        reason: str,
        recorded_at: datetime,
        source_refs: tuple[str, ...] = (),
    ) -> tuple[ProviderRoutingArtifact, tuple[InvalidationRecord, ...]]:
        context = await self._resolve_route_context(request)
        decision = await self._build_decision(
            request=request,
            context=context,
            decision_version=decision_version,
        )
        if predecessor.logical_id != decision.logical_id:
            raise ProviderRoutingIdentityError("routing successor must preserve logical identity")
        provenance = build_provider_routing_provenance(
            decision,
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=recorded_at,
            source_refs=source_refs,
            correlation_id=request.run_correlation_id,
        )
        previous = await self.get_routing_decision(predecessor)
        if previous is None:
            raise ProviderRoutingIdentityError("routing predecessor does not exist")
        previous_payload = previous.value.model_dump(mode="json")
        current_payload = decision.model_dump(mode="json")
        previous_payload.pop("version_id", None)
        current_payload.pop("version_id", None)
        previous_payload.pop("decision_hash", None)
        current_payload.pop("decision_hash", None)
        if previous_payload == current_payload:
            raise ProviderRoutingIdentityError("routing successor requires changed evaluated inputs/evidence")

        artifact, replay_after_promote = await self._ensure_successor_draft(
            value=decision,
            predecessor=predecessor,
            provenance=provenance,
            created_at=recorded_at,
            expected_revision=expected_revision,
            label="ProviderRoutingDecision",
        )
        await self._register_dependencies(artifact)
        await self._bind_profile_policy(
            profile=context["active_profile"],
            dependent=artifact.ref,
            provenance=provenance,
            created_at=recorded_at,
        )
        records = await self.invalidations.create_for_change(
            cause="PROVIDER_ROUTE_REEVALUATED",
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope="provider_execution_descendants",
            repair_or_recompute_requirement=(
                "Re-lower provider request/admission using the current routing decision."
            ),
        )
        if not replay_after_promote:
            await self.versions.update_current(
                logical_id=decision.logical_id,
                version_id=decision.version_id,
                status=LifecycleState.APPROVED,
                expected_revision=expected_revision,
            )
        return artifact, tuple(records)

    async def get_provider_profile(self, ref: VersionRef) -> ProviderRoutingArtifact | None:
        if not ref.logical_id.root.startswith("provider-profile:"):
            raise ProviderRoutingIdentityError("expected ProviderProfile ref")
        return await self._get_typed(ref, ProviderProfile)

    async def get_routing_rule(self, ref: VersionRef) -> ProviderRoutingArtifact | None:
        if ref.logical_id != provider_routing_rule_logical_id():
            raise ProviderRoutingIdentityError("expected ProviderRoutingRuleSet ref")
        return await self._get_typed(ref, ProviderRoutingRuleSet)

    async def get_routing_decision(self, ref: VersionRef) -> ProviderRoutingArtifact | None:
        if not ref.logical_id.root.startswith("provider-route:"):
            raise ProviderRoutingIdentityError("expected ProviderRoutingDecision ref")
        return await self._get_typed(ref, ProviderRoutingDecision)

    async def assert_selected_route(
        self,
        ref: VersionRef,
        *,
        as_of: datetime,
    ) -> ProviderRoutingDecision:
        await self._assert_current_valid(ref, "ProviderRoutingDecision", {LifecycleState.APPROVED})
        artifact = await self.get_routing_decision(ref)
        if artifact is None:
            raise ProviderRoutingGateBlocked("ProviderRoutingDecision exact version does not exist")
        decision = artifact.value
        assert isinstance(decision, ProviderRoutingDecision)
        if decision.verdict is not RoutingVerdict.SELECTED or decision.selected_profile_ref is None:
            raise ProviderRoutingGateBlocked("routing decision has no eligible selected provider")
        await self._assert_current_valid(decision.shot_ir_ref, "ShotIR", _ACCEPTED)
        await self._assert_current_valid(
            decision.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        await self._assert_current_valid(
            decision.routing_rule_ref,
            "ProviderRoutingRuleSet",
            {LifecycleState.LOCKED},
        )
        profiles: dict[VersionRef, ProviderProfile] = {}
        for candidate_ref in decision.candidate_profile_refs:
            profiles[candidate_ref] = await self._assert_profile_current(candidate_ref)
        selected_profile = profiles[decision.selected_profile_ref]
        check_time = as_of
        if check_time.tzinfo is None:
            raise ProviderRoutingGateBlocked("selected route as_of timestamp must be timezone-aware")
        if check_time < selected_profile.verified_at or check_time >= selected_profile.expires_at:
            raise ProviderRoutingGateBlocked("selected ProviderProfile evidence is stale at execution time")
        if selected_profile.availability.state in {
            ProviderAvailabilityState.UNKNOWN,
            ProviderAvailabilityState.UNAVAILABLE,
        }:
            raise ProviderRoutingGateBlocked("selected ProviderProfile availability is not executable")
        return decision

    async def _resolve_route_context(self, request: ProviderRouteRequest) -> dict[str, Any]:
        rule_artifact = await self.get_routing_rule(request.routing_rule_ref)
        if rule_artifact is None:
            raise ProviderRoutingGateBlocked("ProviderRoutingRuleSet exact version does not exist")
        await self._assert_current_valid(
            request.routing_rule_ref,
            "ProviderRoutingRuleSet",
            {LifecycleState.LOCKED},
        )
        rule = rule_artifact.value
        assert isinstance(rule, ProviderRoutingRuleSet)

        ir_artifact = await self.compiler.get_shot_ir(request.shot_ir_ref)
        if ir_artifact is None:
            raise ProviderRoutingGateBlocked("ShotIR exact version does not exist")
        await self._assert_current_valid(request.shot_ir_ref, "ShotIR", _ACCEPTED)
        shot_ir = ir_artifact.value
        assert isinstance(shot_ir, ShotIR)
        if shot_ir.project_id != request.project_id:
            raise ProviderRoutingGateBlocked("ShotIR belongs to a different project")
        if shot_ir.active_profile_ref != request.active_profile_ref:
            raise ProviderRoutingGateBlocked("ShotIR and route request ActiveProductionProfile mismatch")

        profile_stored = await self.versions.get_version(request.active_profile_ref)
        if profile_stored is None:
            raise ProviderRoutingGateBlocked("ActiveProductionProfile exact version does not exist")
        await self._assert_current_valid(
            request.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        try:
            active_profile = ActiveProductionProfile.model_validate(profile_stored.payload)
        except Exception as exc:
            raise ProviderRoutingGateBlocked("ActiveProductionProfile payload is invalid") from exc
        if active_profile.project_id != request.project_id:
            raise ProviderRoutingGateBlocked("ActiveProductionProfile belongs to a different project")

        constraint_keys = {item.key for item in shot_ir.execution_constraints}
        requirement_keys = {item.key for item in request.requirements}
        missing_constraints = sorted(constraint_keys - requirement_keys)
        if missing_constraints:
            raise ProviderRoutingGateBlocked(
                "routing request omitted ShotIR execution constraints: " + ", ".join(missing_constraints)
            )
        for constraint in shot_ir.execution_constraints:
            matches = [item for item in request.requirements if item.key == constraint.key]
            if not any(
                item.expected_value_json == constraint.value_json
                and item.operator in {RequirementOperator.EQUALS, RequirementOperator.CONTAINS}
                for item in matches
            ):
                raise ProviderRoutingGateBlocked(
                    f"routing requirement weakens or changes ShotIR execution constraint: {constraint.key}"
                )

        candidates: list[ProviderProfile] = []
        for ref in request.candidate_profile_refs:
            artifact = await self.get_provider_profile(ref)
            if artifact is None:
                raise ProviderRoutingGateBlocked(f"candidate ProviderProfile missing: {ref.logical_id.root}")
            value = artifact.value
            assert isinstance(value, ProviderProfile)
            candidates.append(value)

        return {
            "rule": rule,
            "shot_ir": shot_ir,
            "active_profile": active_profile,
            "candidates": tuple(candidates),
        }

    async def _build_decision(
        self,
        *,
        request: ProviderRouteRequest,
        context: dict[str, Any],
        decision_version: VersionId,
    ) -> ProviderRoutingDecision:
        active_profile: ActiveProductionProfile = context["active_profile"]
        policy = self._extract_policy(active_profile)
        evaluations = tuple(
            self._evaluate_candidate(
                profile=profile,
                request=request,
                policy=policy,
            )
            for profile in context["candidates"]
        )
        evaluations = await self._resolve_candidate_statuses(evaluations)
        eligible = [item for item in evaluations if item.eligible]
        selected: VersionRef | None = None
        verdict = RoutingVerdict.NO_ELIGIBLE_PROVIDER
        if eligible:
            eligible.sort(
                key=lambda item: (
                    len(item.degradation_keys),
                    item.provider_profile_ref.logical_id.root,
                    item.provider_profile_ref.version_id.root,
                )
            )
            selected = eligible[0].provider_profile_ref
            verdict = RoutingVerdict.SELECTED
            rationale = (
                "Selected deterministic eligible ProviderProfile after exact capability, freshness, "
                "availability and project-policy evaluation."
            )
        else:
            rationale = (
                "No eligible ProviderProfile satisfies exact capability/freshness/policy inputs; "
                "planning/repair/escalation is required and hidden fallback is forbidden."
            )

        policy_hash = _hash_payload(policy)
        draft = ProviderRoutingDecision.model_construct(
            project_id=request.project_id,
            routing_decision_id=provider_route_decision_logical_id(
                request.project_id,
                request.shot_ir_ref.logical_id,
            ),
            version_id=decision_version,
            shot_ir_ref=request.shot_ir_ref,
            active_profile_ref=request.active_profile_ref,
            routing_rule_ref=request.routing_rule_ref,
            surface=request.surface,
            region=request.region,
            candidate_profile_refs=request.candidate_profile_refs,
            requirements=request.requirements,
            evaluated_at=request.evaluated_at,
            run_correlation_id=request.run_correlation_id,
            policy_hash=policy_hash,
            candidate_evaluations=evaluations,
            verdict=verdict,
            selected_profile_ref=selected,
            rationale=rationale,
            decision_hash="sha256:" + "0" * 64,
        )
        payload = draft.model_dump(mode="python")
        payload["decision_hash"] = draft.compute_decision_hash()
        return ProviderRoutingDecision.model_validate(payload)

    def _evaluate_candidate(
        self,
        *,
        profile: ProviderProfile,
        request: ProviderRouteRequest,
        policy: dict[str, Any],
    ) -> ProviderCandidateEvaluation:
        reasons: list[str] = []
        degradations: list[str] = []
        evaluations: list[RequirementEvaluation] = []

        if profile.surface != request.surface:
            reasons.append(f"surface mismatch: requires {request.surface}, profile is {profile.surface}")
        if profile.region != request.region:
            reasons.append(f"region mismatch: requires {request.region}, profile is {profile.region}")
        allowed = policy["allowed_provider_keys"]
        if allowed and profile.provider_key not in allowed:
            reasons.append("provider key is excluded by ActiveProductionProfile routing policy")
        if request.evaluated_at < profile.verified_at or request.evaluated_at >= profile.expires_at:
            reasons.append("ProviderProfile evidence is stale/not-yet-valid at routing evaluation time")

        availability = profile.availability.state
        if availability in {ProviderAvailabilityState.UNKNOWN, ProviderAvailabilityState.UNAVAILABLE}:
            reasons.append(f"provider availability is {availability.value}")
        elif availability is ProviderAvailabilityState.DEGRADED:
            if policy["allow_degraded_availability"]:
                degradations.append("availability")
            else:
                reasons.append("provider availability is DEGRADED and policy does not allow degradation")

        fact_map = profile.fact_map()
        for requirement in request.requirements:
            result = self._evaluate_requirement(
                requirement=requirement,
                fact=fact_map.get(requirement.key),
                evaluated_at=request.evaluated_at,
            )
            if result.disposition is not RequirementDisposition.SATISFIED:
                if (
                    requirement.degradable
                    and requirement.key in policy["allow_degradation_keys"]
                    and result.disposition
                    in {
                        RequirementDisposition.UNSUPPORTED,
                        RequirementDisposition.UNKNOWN,
                        RequirementDisposition.MISMATCH,
                    }
                ):
                    result = result.model_copy(update={"disposition": RequirementDisposition.DEGRADED})
                    degradations.append(requirement.key)
                else:
                    reasons.append(f"requirement {requirement.key}: {result.message}")
            evaluations.append(result)

        if policy["max_cost_micros"] is not None:
            cost_requirement = ProviderRequirement(
                key="cost.estimated_micros",
                operator=RequirementOperator.AT_MOST,
                expected_value_json=_canonical_json(policy["max_cost_micros"]),
                source_refs=(request.shot_ir_ref,),
            )
            result = self._evaluate_requirement(
                requirement=cost_requirement,
                fact=fact_map.get(cost_requirement.key),
                evaluated_at=request.evaluated_at,
            )
            evaluations.append(result)
            if result.disposition is not RequirementDisposition.SATISFIED:
                reasons.append(f"budget: {result.message}")
            if policy["currency"] is not None:
                currency_requirement = ProviderRequirement(
                    key="cost.currency",
                    operator=RequirementOperator.EQUALS,
                    expected_value_json=_canonical_json(policy["currency"]),
                    source_refs=(request.shot_ir_ref,),
                )
                currency_result = self._evaluate_requirement(
                    requirement=currency_requirement,
                    fact=fact_map.get(currency_requirement.key),
                    evaluated_at=request.evaluated_at,
                )
                evaluations.append(currency_result)
                if currency_result.disposition is not RequirementDisposition.SATISFIED:
                    reasons.append(f"budget currency: {currency_result.message}")

        if policy["require_reconcile"]:
            recovery_requirement = ProviderRequirement(
                key="recovery.reconcile",
                operator=RequirementOperator.SUPPORTED,
                source_refs=(request.shot_ir_ref,),
            )
            result = self._evaluate_requirement(
                requirement=recovery_requirement,
                fact=fact_map.get(recovery_requirement.key),
                evaluated_at=request.evaluated_at,
            )
            evaluations.append(result)
            if result.disposition is not RequirementDisposition.SATISFIED:
                reasons.append(f"recovery: {result.message}")

        # Candidate current-pointer/invalidation checks are represented as a required
        # precondition here and completed asynchronously in _resolve_candidate_statuses.
        return ProviderCandidateEvaluation(
            provider_profile_ref=profile.ref,
            eligible=not reasons,
            availability_state=availability,
            requirement_evaluations=tuple(evaluations),
            degradation_keys=tuple(degradations),
            rejection_reasons=tuple(reasons),
        )

    def _evaluate_requirement(
        self,
        *,
        requirement: ProviderRequirement,
        fact: ProviderEvidenceFact | None,
        evaluated_at: datetime,
    ) -> RequirementEvaluation:
        if fact is None:
            return RequirementEvaluation(
                key=requirement.key,
                operator=requirement.operator,
                disposition=RequirementDisposition.UNKNOWN,
                message="required provider fact is missing/UNKNOWN",
            )
        if evaluated_at < fact.verified_at or evaluated_at >= fact.expires_at:
            return RequirementEvaluation(
                key=requirement.key,
                operator=requirement.operator,
                disposition=RequirementDisposition.UNKNOWN,
                message="required provider fact evidence is stale/not-yet-valid",
                fact_evidence_id=fact.evidence.evidence_id,
            )
        if fact.support is CapabilitySupport.UNKNOWN:
            return RequirementEvaluation(
                key=requirement.key,
                operator=requirement.operator,
                disposition=RequirementDisposition.UNKNOWN,
                message="provider fact is UNKNOWN; guessing is forbidden",
                fact_evidence_id=fact.evidence.evidence_id,
            )
        if fact.support is CapabilitySupport.UNSUPPORTED:
            return RequirementEvaluation(
                key=requirement.key,
                operator=requirement.operator,
                disposition=RequirementDisposition.UNSUPPORTED,
                message="provider evidence explicitly marks requirement unsupported",
                fact_evidence_id=fact.evidence.evidence_id,
            )
        if requirement.operator is RequirementOperator.SUPPORTED:
            return RequirementEvaluation(
                key=requirement.key,
                operator=requirement.operator,
                disposition=RequirementDisposition.SATISFIED,
                message="provider evidence supports required capability",
                fact_evidence_id=fact.evidence.evidence_id,
            )
        if fact.value_json is None:
            return RequirementEvaluation(
                key=requirement.key,
                operator=requirement.operator,
                disposition=RequirementDisposition.UNKNOWN,
                message="supported provider fact lacks a comparable evidence value",
                fact_evidence_id=fact.evidence.evidence_id,
            )
        actual = fact.value
        expected = requirement.expected_value
        matched = self._compare_requirement(
            operator=requirement.operator,
            actual=actual,
            expected=expected,
        )
        return RequirementEvaluation(
            key=requirement.key,
            operator=requirement.operator,
            disposition=(
                RequirementDisposition.SATISFIED
                if matched
                else RequirementDisposition.MISMATCH
            ),
            message=(
                "provider evidence satisfies required value"
                if matched
                else "provider evidence value does not satisfy requirement"
            ),
            fact_evidence_id=fact.evidence.evidence_id,
        )

    @staticmethod
    def _compare_requirement(*, operator: RequirementOperator, actual: Any, expected: Any) -> bool:
        if operator is RequirementOperator.EQUALS:
            return actual == expected
        if operator is RequirementOperator.CONTAINS:
            if isinstance(actual, list):
                return expected in actual
            if isinstance(actual, dict) and isinstance(expected, str):
                return expected in actual
            return False
        if operator in {RequirementOperator.AT_LEAST, RequirementOperator.AT_MOST}:
            if isinstance(actual, bool) or isinstance(expected, bool):
                return False
            if not isinstance(actual, (int, float)) or not isinstance(expected, (int, float)):
                return False
            return actual >= expected if operator is RequirementOperator.AT_LEAST else actual <= expected
        return False

    def _extract_policy(self, profile: ActiveProductionProfile) -> dict[str, Any]:
        policy = profile.effective_policy

        def value(path_key: str, default: Any) -> Any:
            return policy.get(_PROFILE_POLICY_PATHS[path_key], default)

        allowed_raw = value("allowed_provider_keys", [])
        degrade_raw = value("allow_degradation_keys", [])
        if not isinstance(allowed_raw, list) or not all(isinstance(item, str) for item in allowed_raw):
            raise ProviderRoutingGateBlocked("provider.routing.allowed_provider_keys must be a string list")
        if not isinstance(degrade_raw, list) or not all(isinstance(item, str) for item in degrade_raw):
            raise ProviderRoutingGateBlocked("provider.routing.allow_degradation_keys must be a string list")
        allow_degraded = value("allow_degraded_availability", False)
        if not isinstance(allow_degraded, bool):
            raise ProviderRoutingGateBlocked("provider.routing.allow_degraded_availability must be boolean")
        max_cost = value("max_cost_micros", None)
        if max_cost is not None and (isinstance(max_cost, bool) or not isinstance(max_cost, int) or max_cost < 0):
            raise ProviderRoutingGateBlocked("provider.routing.max_cost_micros must be non-negative integer")
        currency = value("currency", None)
        if currency is not None:
            currency = _token(str(currency), "provider.routing.currency")
        require_reconcile = value("require_reconcile", False)
        if not isinstance(require_reconcile, bool):
            raise ProviderRoutingGateBlocked("provider.routing.require_reconcile must be boolean")
        return {
            "allowed_provider_keys": tuple(sorted({_token(item, "allowed provider key") for item in allowed_raw})),
            "allow_degradation_keys": tuple(sorted({_fact_key(item) for item in degrade_raw})),
            "allow_degraded_availability": allow_degraded,
            "max_cost_micros": max_cost,
            "currency": currency,
            "require_reconcile": require_reconcile,
        }

    async def _resolve_candidate_statuses(
        self,
        evaluations: tuple[ProviderCandidateEvaluation, ...],
    ) -> tuple[ProviderCandidateEvaluation, ...]:
        unresolved = {
            (record.affected_object_id.root, record.affected_object_version.root)
            for record in await self.invalidations.list_unresolved()
        }
        updated: list[ProviderCandidateEvaluation] = []
        for evaluation in evaluations:
            ref = evaluation.provider_profile_ref
            pointer = await self.versions.get_current(ref.logical_id)
            reasons = list(evaluation.rejection_reasons)
            if (
                pointer is None
                or pointer.version_id != ref.version_id
                or pointer.status not in _ACCEPTED
            ):
                reasons.append("ProviderProfile is not exact current accepted evidence")
            if _ref_key(ref) in unresolved:
                reasons.append("ProviderProfile has unresolved invalidation")
            updated.append(
                evaluation.model_copy(
                    update={
                        "eligible": not reasons,
                        "rejection_reasons": tuple(reasons),
                    }
                )
            )
        return tuple(updated)

    async def _get_typed(self, ref: VersionRef, model: type[BaseModel]) -> ProviderRoutingArtifact | None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = model.model_validate(stored.payload)
        return ProviderRoutingArtifact(metadata=stored.metadata, value=value)

    async def _ensure_initial(
        self,
        *,
        value: ProviderRoutingValue,
        provenance: Provenance,
        created_at: datetime,
        status: LifecycleState,
        label: str,
        promote: bool = True,
    ) -> ProviderRoutingArtifact:
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
            artifact = ProviderRoutingArtifact(metadata=stored.metadata, value=value)
        else:
            if current.version_id != value.version_id:
                raise ProviderRoutingIdentityError(f"{label} logical identity already has another current version")
            stored = await self.versions.get_version(value.ref)
            if stored is None:
                raise ProviderRoutingIdentityError(f"{label} current payload is missing")
            typed = type(value).model_validate(stored.payload)
            artifact = ProviderRoutingArtifact(metadata=stored.metadata, value=typed)
            if typed != value or stored.metadata.provenance != provenance:
                raise ProviderRoutingIdentityError(f"{label} exact replay conflicts with immutable evidence")
        if promote:
            await self._promote_exact_current(artifact.ref, status=status, label=label)
        return artifact

    async def _ensure_successor_draft(
        self,
        *,
        value: ProviderRoutingValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
        label: str,
    ) -> tuple[ProviderRoutingArtifact, bool]:
        current = await self.versions.get_current(value.logical_id)
        if current is None:
            raise ProviderRoutingIdentityError(f"{label} current pointer is missing")
        replay_after_promote = current.version_id == value.version_id
        if replay_after_promote:
            if current.status not in _ACCEPTED or current.revision != expected_revision + 1:
                raise ProviderRoutingIdentityError(f"{label} successor replay revision/state mismatch")
        elif (
            current.version_id != predecessor.version_id
            or current.status not in _ACCEPTED
            or current.revision != expected_revision
        ):
            raise ProviderRoutingIdentityError(f"{label} successor requires exact current accepted predecessor/revision")
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
        typed = type(value).model_validate(stored.payload)
        artifact = ProviderRoutingArtifact(metadata=stored.metadata, value=typed)
        if typed != value or stored.metadata.provenance != provenance:
            raise ProviderRoutingIdentityError(f"{label} successor replay conflicts with immutable evidence")
        return artifact, replay_after_promote

    async def _revise_simple(
        self,
        *,
        value: ProviderProfile | ProviderRoutingRuleSet,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
        status: LifecycleState,
        label: str,
        cause: str,
        scope: str,
        repair: str,
    ) -> tuple[ProviderRoutingArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise ProviderRoutingIdentityError(f"{label} successor must preserve logical identity")
        previous = (
            await self.get_provider_profile(predecessor)
            if isinstance(value, ProviderProfile)
            else await self.get_routing_rule(predecessor)
        )
        if previous is None:
            raise ProviderRoutingIdentityError(f"{label} predecessor does not exist")
        previous_payload = previous.value.model_dump(mode="json")
        current_payload = value.model_dump(mode="json")
        previous_payload.pop("profile_version" if isinstance(value, ProviderProfile) else "version_id", None)
        current_payload.pop("profile_version" if isinstance(value, ProviderProfile) else "version_id", None)
        if previous_payload == current_payload:
            raise ProviderRoutingIdentityError(f"{label} successor requires semantic/evidence change")
        artifact, replay_after_promote = await self._ensure_successor_draft(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label=label,
        )
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
                status=status,
                expected_revision=expected_revision,
            )
        return artifact, tuple(records)

    async def _register_dependencies(self, artifact: ProviderRoutingArtifact) -> None:
        provenance = artifact.metadata.provenance
        for binding in artifact.value.source_bindings():
            await self.graph.create_edge(
                source=binding.source,
                dependent=artifact.ref,
                edge_type="provider_routing_input",
                dependency_reason=f"provider routing source:{binding.role}",
                provenance=provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _bind_profile_policy(
        self,
        *,
        profile: ActiveProductionProfile,
        dependent: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> None:
        await self.profile_binder.bind(
            profile=profile,
            dependent=dependent,
            path="*",
            reason="Provider routing depends on pinned ActiveProductionProfile policy",
            provenance=provenance,
            created_at=created_at,
        )

    async def _assert_current_valid(
        self,
        ref: VersionRef,
        label: str,
        allowed: set[LifecycleState],
    ) -> None:
        pointer = await self.versions.get_current(ref.logical_id)
        if pointer is None or pointer.version_id != ref.version_id or pointer.status not in allowed:
            raise ProviderRoutingGateBlocked(f"{label} is not exact current accepted authority")
        for record in await self.invalidations.list_unresolved():
            if (
                record.affected_object_id == ref.logical_id
                and record.affected_object_version == ref.version_id
            ):
                raise ProviderRoutingGateBlocked(f"{label} has unresolved invalidation")

    async def _assert_profile_current(self, ref: VersionRef) -> ProviderProfile:
        artifact = await self.get_provider_profile(ref)
        if artifact is None:
            raise ProviderRoutingGateBlocked("ProviderProfile exact version does not exist")
        await self._assert_current_valid(ref, "ProviderProfile", _ACCEPTED)
        value = artifact.value
        assert isinstance(value, ProviderProfile)
        return value

    async def _promote_exact_current(
        self,
        ref: VersionRef,
        *,
        status: LifecycleState,
        label: str,
    ) -> None:
        current = await self.versions.get_current(ref.logical_id)
        if current is None or current.version_id != ref.version_id:
            raise ProviderRoutingIdentityError(f"{label} current pointer does not match exact version")
        if current.status is status:
            return
        if current.status is not LifecycleState.DRAFT:
            raise ProviderRoutingIdentityError(f"{label} cannot promote from {current.status.value}")
        await self.versions.update_current(
            logical_id=ref.logical_id,
            version_id=ref.version_id,
            status=status,
            expected_revision=current.revision,
        )

    def _assert_profile_provenance(self, profile: ProviderProfile, provenance: Provenance) -> None:
        if provenance.source_versions:
            raise ProviderRoutingGateBlocked(
                "ProviderProfile capability evidence must not claim upstream semantic source versions"
            )
        missing = sorted(set(profile.evidence_ids) - set(provenance.source_refs))
        if missing:
            raise ProviderRoutingGateBlocked(
                "ProviderProfile provenance is missing evidence refs: " + ", ".join(missing)
            )
