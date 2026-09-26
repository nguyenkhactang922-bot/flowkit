"""Single canonical Profile Resolver authority.

This module resolves exact Project/Topic/Domain inputs and exact frozen
BrainPack versions into a deterministic effective-policy result plus an
immutable ResolutionTrace. It intentionally does NOT define or persist
ActiveProductionProfile; IMP-013 owns that downstream snapshot.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from .brainpack import (
    BrainPackApplicability,
    BrainPackDefinition,
    BrainPackFamily,
    BrainPackLifecycleState,
    BrainPackRef,
    BrainPackRegistryRepository,
    BrainPackRule,
    BrainPackRuleStrength,
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
from .topic_domain import (
    ClassificationAxis,
    DomainResolutionArtifact,
    ProjectBootstrapArtifact,
    TopicResolutionArtifact,
)
from .versioning import StoredSemanticVersion, VersionRepository


class ProfileResolverError(ValueError):
    """Base error for canonical profile-resolution failures."""


class ProfileResolverInputError(ProfileResolverError):
    """Raised when exact upstream input authority is inconsistent."""


class PackNotReadyError(ProfileResolverError):
    """Raised when a selected/inherited pack is not FROZEN."""


class PackCompositionConflict(ProfileResolverError):
    """Raised when BrainPack inheritance/composition cannot be resolved safely."""


class HardConstraintConflict(ProfileResolverError):
    """Raised for unresolved top-authority hard-hard conflicts."""


class ResolutionConflict(ProfileResolverError):
    """Raised for unresolved equal-precedence conflicting values."""


class OverrideNotAllowed(ProfileResolverError):
    """Raised when a project override targets a non-allowlisted path."""


class LocalIntentNotAllowed(ProfileResolverError):
    """Raised when local downstream intent targets a forbidden path."""


_PATH_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
_FORBIDDEN_VALUE_KEYS = {
    "provider",
    "provider_id",
    "provider_name",
    "model",
    "model_id",
    "model_key",
    "remote_job_id",
    "request_id",
    "flow_project_id",
    "google_project_id",
}


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _policy_path(value: str) -> str:
    normalized = _trimmed(value, "policy path").lower()
    if not _PATH_RE.fullmatch(normalized):
        raise ValueError(
            "policy path must start with a lowercase letter and contain only "
            "lowercase letters, digits, '.', '_', or '-'"
        )
    return normalized


def _validate_policy_value(value: Any, path: str = "value") -> Any:
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} mapping keys must be strings")
            if key.casefold() in _FORBIDDEN_VALUE_KEYS:
                raise ValueError(f"{path} contains provider/runtime field {key!r}")
            _validate_policy_value(nested, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _validate_policy_value(nested, f"{path}[{index}]")
    _canonical_json({"value": value})
    return value


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("profile policy values must be canonical JSON data") from exc


def _sha256_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _version_ref_for_pack(ref: BrainPackRef) -> VersionRef:
    return VersionRef(logical_id=ref.pack_id, version_id=ref.pack_version)


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return (ref.logical_id.root, ref.version_id.root)


def _pack_ref_key(ref: BrainPackRef) -> tuple[str, str]:
    return (ref.pack_id.root, ref.pack_version.root)


class AuthorityTier(str, Enum):
    LOCKED_CANONICAL = "LOCKED_CANONICAL"
    HARD_CONSTRAINT = "HARD_CONSTRAINT"
    PROJECT_OVERRIDE = "PROJECT_OVERRIDE"
    INHERITED_PACK_POLICY = "INHERITED_PACK_POLICY"
    SOFT_PREFERENCE = "SOFT_PREFERENCE"
    LOCAL_INTENT = "LOCAL_INTENT"


_AUTHORITY_RANK = {
    AuthorityTier.LOCKED_CANONICAL: 0,
    AuthorityTier.HARD_CONSTRAINT: 1,
    AuthorityTier.PROJECT_OVERRIDE: 2,
    AuthorityTier.INHERITED_PACK_POLICY: 3,
    AuthorityTier.SOFT_PREFERENCE: 4,
    AuthorityTier.LOCAL_INTENT: 5,
}


class PolicySourceKind(str, Enum):
    LOCKED_FACT = "LOCKED_FACT"
    PROJECT_HARD_CONSTRAINT = "PROJECT_HARD_CONSTRAINT"
    BRAINPACK_HARD_RULE = "BRAINPACK_HARD_RULE"
    PROJECT_OVERRIDE = "PROJECT_OVERRIDE"
    BRAINPACK_POLICY = "BRAINPACK_POLICY"
    PROJECT_SOFT_PREFERENCE = "PROJECT_SOFT_PREFERENCE"
    LOCAL_INTENT = "LOCAL_INTENT"


class ContenderDisposition(str, Enum):
    SELECTED = "SELECTED"
    EQUIVALENT = "EQUIVALENT"
    OVERRIDDEN_BY_HIGHER_AUTHORITY = "OVERRIDDEN_BY_HIGHER_AUTHORITY"


class PolicyAssertion(BaseModel):
    """Exact-source canonical fact/invariant."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    value: Any
    source_ref: VersionRef
    reason: str

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _policy_path(value)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: Any) -> Any:
        return _validate_policy_value(value)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        return _trimmed(value, "policy assertion reason")


class RequestedProjectOverride(BaseModel):
    """Project-requested override; source authority is the exact project input."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    value: Any
    reason: str

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _policy_path(value)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: Any) -> Any:
        return _validate_policy_value(value)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        return _trimmed(value, "override reason")


class LocalPolicyIntent(BaseModel):
    """Low-authority local intent allowed only on resolver allowlisted paths."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    value: Any
    source_ref: VersionRef
    reason: str

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _policy_path(value)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: Any) -> Any:
        return _validate_policy_value(value)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        return _trimmed(value, "local intent reason")


class ProfileResolverRequest(BaseModel):
    """Exact versioned inputs to the single Profile Resolver."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project: ProjectBootstrapArtifact
    topic: TopicResolutionArtifact
    domain: DomainResolutionArtifact
    candidate_pack_refs: tuple[BrainPackRef, ...] = ()
    locked_values: tuple[PolicyAssertion, ...] = ()
    requested_overrides: tuple[RequestedProjectOverride, ...] = ()
    local_intent: tuple[LocalPolicyIntent, ...] = ()

    @model_validator(mode="after")
    def validate_lineage(self) -> "ProfileResolverRequest":
        project_id = self.project.value.project_id
        if self.topic.value.project_id != project_id:
            raise ValueError("topic belongs to a different project")
        if self.domain.value.project_id != project_id:
            raise ValueError("domain belongs to a different project")
        if self.domain.value.topic_resolution_ref != self.topic.ref:
            raise ValueError("domain is not bound to the supplied exact topic version")
        if self.domain.value.project_constraints != self.topic.value.constraints:
            raise ValueError("domain constraints do not match supplied topic version")

        pack_keys = [_pack_ref_key(ref) for ref in self.candidate_pack_refs]
        if len(set(pack_keys)) != len(pack_keys):
            raise ValueError("candidate BrainPack refs must be unique")

        override_paths = [item.path for item in self.requested_overrides]
        if len(set(override_paths)) != len(override_paths):
            raise ValueError("requested override paths must be unique")

        local_paths = [item.path for item in self.local_intent]
        if len(set(local_paths)) != len(local_paths):
            raise ValueError("local intent paths must be unique")
        return self


class PackSelectionDecision(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    pack_ref: BrainPackRef
    selected: bool
    reason: str


class ResolutionContender(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    value: Any
    tier: AuthorityTier
    precedence_rank: int = Field(ge=0, le=5)
    source_kind: PolicySourceKind
    source_ref: VersionRef
    source_pack_ref: BrainPackRef | None = None
    inherited_via: BrainPackRef | None = None
    reason: str
    disposition: ContenderDisposition


class FieldResolutionTrace(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    value: Any
    winning_tier: AuthorityTier
    precedence_rank: int = Field(ge=0, le=5)
    winning_source_kind: PolicySourceKind
    winning_source_ref: VersionRef
    winning_pack_ref: BrainPackRef | None = None
    resolution_reason: str
    contenders: tuple[ResolutionContender, ...]


class ResolutionTrace(BaseModel):
    """Immutable explainability record for one exact deterministic resolution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    resolution_id: LogicalId
    resolver_version: VersionRef
    project_id: LogicalId
    project_ref: VersionRef
    topic_ref: VersionRef
    domain_ref: VersionRef
    pack_selection: tuple[PackSelectionDecision, ...]
    direct_selected_pack_refs: tuple[BrainPackRef, ...]
    effective_pack_refs: tuple[BrainPackRef, ...]
    fields: tuple[FieldResolutionTrace, ...]
    input_fingerprint: str
    effective_policy_hash: str


class ProfileResolutionResult(BaseModel):
    """IMP-012 output consumed by IMP-013; not an ActiveProductionProfile."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    effective_policy: dict[str, Any]
    trace: ResolutionTrace

    @model_validator(mode="after")
    def validate_result(self) -> "ProfileResolutionResult":
        if self.trace.project_id != self.project_id:
            raise ValueError("resolution trace project mismatch")
        if _sha256_json(self.effective_policy) != self.trace.effective_policy_hash:
            raise ValueError("effective policy hash mismatch")
        return self


class ProfileResolutionArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    result: ProfileResolutionResult

    @model_validator(mode="after")
    def validate_identity(self) -> "ProfileResolutionArtifact":
        expected = _profile_resolution_logical_id(self.result.project_id)
        if self.metadata.logical_id != expected:
            raise ValueError(
                f"profile resolution logical_id must be {expected.root}"
            )
        _validate_resolution_provenance(self.result, self.metadata.provenance)
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(
            logical_id=self.metadata.logical_id,
            version_id=self.metadata.version_id,
        )


@dataclass(frozen=True)
class _Candidate:
    path: str
    value: Any
    tier: AuthorityTier
    source_kind: PolicySourceKind
    source_ref: VersionRef
    reason: str
    source_pack_ref: BrainPackRef | None = None
    inherited_via: BrainPackRef | None = None

    @property
    def rank(self) -> int:
        return _AUTHORITY_RANK[self.tier]

    @property
    def canonical_value(self) -> str:
        return _canonical_json(self.value)


@dataclass(frozen=True)
class _PackRuleAtDistance:
    definition: BrainPackDefinition
    rule: BrainPackRule
    distance: int


def _profile_resolution_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"profile-resolution:{project_id.root}")


def _brainpack_binding_refs(
    refs: Iterable[BrainPackRef],
) -> tuple[VersionRef, ...]:
    return tuple(
        _version_ref_for_pack(ref)
        for ref in sorted(refs, key=_pack_ref_key)
    )


def _expected_resolution_source_bindings(
    result: ProfileResolutionResult,
) -> tuple[SourceVersionBinding, ...]:
    """Bind every exact source version consumed by the resolution decision."""

    trace = result.trace
    bindings: list[SourceVersionBinding] = [
        SourceVersionBinding(role="project_input", source=trace.project_ref),
        SourceVersionBinding(role="topic_resolution", source=trace.topic_ref),
        SourceVersionBinding(role="domain_resolution", source=trace.domain_ref),
    ]
    already = {
        _ref_key(trace.project_ref),
        _ref_key(trace.topic_ref),
        _ref_key(trace.domain_ref),
    }

    # Candidate packs that were evaluated and rejected still affected the
    # selection decision, so they are provenance inputs just like selected and
    # inherited packs.
    consumed_pack_refs: dict[tuple[str, str], BrainPackRef] = {
        _pack_ref_key(item.pack_ref): item.pack_ref
        for item in trace.pack_selection
    }
    for ref in trace.effective_pack_refs:
        consumed_pack_refs[_pack_ref_key(ref)] = ref

    for index, ref in enumerate(
        _brainpack_binding_refs(consumed_pack_refs.values())
    ):
        bindings.append(
            SourceVersionBinding(role=f"brainpack_{index:03d}", source=ref)
        )
        already.add(_ref_key(ref))

    # Losing contenders are also consumed exact inputs: they are evidence for
    # why the winning value won and must remain replayable/auditable.
    contender_refs: dict[tuple[str, str], VersionRef] = {}
    for field in trace.fields:
        for contender in field.contenders:
            key = _ref_key(contender.source_ref)
            if key not in already:
                contender_refs[key] = contender.source_ref

    for index, ref in enumerate(
        sorted(contender_refs.values(), key=_ref_key)
    ):
        bindings.append(
            SourceVersionBinding(role=f"consumed_source_{index:03d}", source=ref)
        )
    return tuple(bindings)


def build_resolution_provenance(
    result: ProfileResolutionResult,
    *,
    actor_ref: str,
    reason: str,
    recorded_at,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=_expected_resolution_source_bindings(result),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        rule_version=result.trace.resolver_version,
        correlation_id=correlation_id,
    )


def _validate_resolution_provenance(
    result: ProfileResolutionResult,
    provenance: Provenance,
) -> None:
    if provenance.rule_version != result.trace.resolver_version:
        raise ValueError("profile resolution provenance resolver version mismatch")
    expected = _expected_resolution_source_bindings(result)
    if provenance.source_versions != expected:
        raise ValueError(
            "profile resolution provenance does not match exact effective sources"
        )


class ProfileResolver:
    """Single authority for pack selection/composition/precedence/overrides."""

    def __init__(
        self,
        *,
        registry: BrainPackRegistryRepository,
        resolver_version: VersionRef,
        override_allowlist: frozenset[str] = frozenset(),
        local_intent_allowlist: frozenset[str] = frozenset(),
    ) -> None:
        self.registry = registry
        self.resolver_version = resolver_version
        self.override_allowlist = frozenset(
            _policy_path(path) for path in override_allowlist
        )
        self.local_intent_allowlist = frozenset(
            _policy_path(path) for path in local_intent_allowlist
        )

    async def resolve(
        self,
        request: ProfileResolverRequest,
    ) -> ProfileResolutionResult:
        self._validate_requested_paths(request)

        fingerprint_payload = self._fingerprint_payload(request)
        input_fingerprint = _sha256_json(fingerprint_payload)
        resolution_id = LogicalId(
            "resolution:" + input_fingerprint.split(":", 1)[1]
        )

        pack_selection: list[PackSelectionDecision] = []
        direct_selected: list[BrainPackRef] = []
        effective_pack_refs: dict[tuple[str, str], BrainPackRef] = {}
        candidates: list[_Candidate] = []

        applicability_context = self._applicability_context(request)
        for ref in sorted(request.candidate_pack_refs, key=_pack_ref_key):
            definition = await self.registry.require(ref)
            lifecycle = await self.registry.get_lifecycle(ref)
            if lifecycle.state is not BrainPackLifecycleState.FROZEN:
                raise PackNotReadyError(
                    f"candidate BrainPack must be FROZEN: "
                    f"{ref.pack_id.root}/{ref.pack_version.root} "
                    f"is {lifecycle.state.value}"
                )

            applicable, reason = self._is_applicable(
                definition.applicability,
                applicability_context,
            )
            pack_selection.append(
                PackSelectionDecision(
                    pack_ref=ref,
                    selected=applicable,
                    reason=reason,
                )
            )
            if not applicable:
                continue

            direct_selected.append(ref)
            pack_candidates, lineage_refs = await self._pack_candidates_for_root(ref)
            candidates.extend(pack_candidates)
            for lineage_ref in lineage_refs:
                effective_pack_refs[_pack_ref_key(lineage_ref)] = lineage_ref

        candidates.extend(self._locked_candidates(request))
        candidates.extend(self._constraint_candidates(request))
        candidates.extend(self._override_candidates(request))
        candidates.extend(self._local_intent_candidates(request))

        effective_policy, field_traces = self._resolve_fields(candidates)
        effective_policy_hash = _sha256_json(effective_policy)

        trace = ResolutionTrace(
            resolution_id=resolution_id,
            resolver_version=self.resolver_version,
            project_id=request.project.value.project_id,
            project_ref=request.project.ref,
            topic_ref=request.topic.ref,
            domain_ref=request.domain.ref,
            pack_selection=tuple(pack_selection),
            direct_selected_pack_refs=tuple(
                sorted(direct_selected, key=_pack_ref_key)
            ),
            effective_pack_refs=tuple(
                effective_pack_refs[key] for key in sorted(effective_pack_refs)
            ),
            fields=field_traces,
            input_fingerprint=input_fingerprint,
            effective_policy_hash=effective_policy_hash,
        )
        return ProfileResolutionResult(
            project_id=request.project.value.project_id,
            effective_policy=effective_policy,
            trace=trace,
        )

    def _validate_requested_paths(self, request: ProfileResolverRequest) -> None:
        for override in request.requested_overrides:
            if override.path not in self.override_allowlist:
                raise OverrideNotAllowed(
                    f"project override path is not allowlisted: {override.path}"
                )
        for intent in request.local_intent:
            if intent.path not in self.local_intent_allowlist:
                raise LocalIntentNotAllowed(
                    f"local intent path is not allowlisted: {intent.path}"
                )

    def _fingerprint_payload(self, request: ProfileResolverRequest) -> dict[str, Any]:
        def ref_json(ref: VersionRef) -> dict[str, str]:
            return {
                "logical_id": ref.logical_id.root,
                "version_id": ref.version_id.root,
            }

        def pack_json(ref: BrainPackRef) -> dict[str, str]:
            return {
                "pack_id": ref.pack_id.root,
                "pack_version": ref.pack_version.root,
            }

        return {
            "resolver_version": ref_json(self.resolver_version),
            "override_allowlist": sorted(self.override_allowlist),
            "local_intent_allowlist": sorted(self.local_intent_allowlist),
            "project": ref_json(request.project.ref),
            "topic": ref_json(request.topic.ref),
            "domain": ref_json(request.domain.ref),
            "candidate_pack_refs": [
                pack_json(ref)
                for ref in sorted(request.candidate_pack_refs, key=_pack_ref_key)
            ],
            "locked_values": [
                {
                    "path": item.path,
                    "value": item.value,
                    "source_ref": ref_json(item.source_ref),
                    "reason": item.reason,
                }
                for item in sorted(
                    request.locked_values,
                    key=lambda item: (
                        item.path,
                        item.source_ref.logical_id.root,
                        item.source_ref.version_id.root,
                    ),
                )
            ],
            "requested_overrides": [
                item.model_dump(mode="json")
                for item in sorted(
                    request.requested_overrides,
                    key=lambda item: item.path,
                )
            ],
            "local_intent": [
                {
                    **item.model_dump(mode="json"),
                    "source_ref": ref_json(item.source_ref),
                }
                for item in sorted(
                    request.local_intent,
                    key=lambda item: item.path,
                )
            ],
        }

    @staticmethod
    def _applicability_context(
        request: ProfileResolverRequest,
    ) -> dict[str, set[str]]:
        result: dict[str, set[str]] = {
            "topic_labels": {
                request.topic.value.normalized_topic.casefold(),
                *(
                    label.label.casefold()
                    for label in request.topic.value.weighted_topic_labels
                ),
            },
            "domains": set(),
            "niches": set(),
            "genres": set(),
            "audiences": set(),
            "formats": set(),
            "platforms": set(),
            "factuality_modes": {
                request.topic.value.factuality_mode.casefold(),
            },
        }
        mapping = {
            ClassificationAxis.DOMAIN: "domains",
            ClassificationAxis.NICHE: "niches",
            ClassificationAxis.GENRE: "genres",
            ClassificationAxis.AUDIENCE: "audiences",
            ClassificationAxis.FORMAT: "formats",
            ClassificationAxis.PLATFORM: "platforms",
            ClassificationAxis.FACTUALITY: "factuality_modes",
        }
        for classification in request.domain.value.classifications:
            target = result[mapping[classification.axis]]
            target.update(label.label.casefold() for label in classification.labels)
        return result

    @staticmethod
    def _is_applicable(
        applicability: BrainPackApplicability,
        context: dict[str, set[str]],
    ) -> tuple[bool, str]:
        dimensions = (
            "topic_labels",
            "domains",
            "niches",
            "genres",
            "audiences",
            "formats",
            "platforms",
            "factuality_modes",
        )
        mismatches: list[str] = []
        for dimension in dimensions:
            required = {
                value.casefold() for value in getattr(applicability, dimension)
            }
            if required and required.isdisjoint(context[dimension]):
                mismatches.append(dimension)
        if mismatches:
            return False, "not applicable: " + ", ".join(sorted(mismatches))
        return True, "applicability matched exact topic/domain classification"

    async def _pack_candidates_for_root(
        self,
        root_ref: BrainPackRef,
    ) -> tuple[list[_Candidate], tuple[BrainPackRef, ...]]:
        lineage = await self._load_lineage(root_ref)
        by_path: dict[str, list[_PackRuleAtDistance]] = defaultdict(list)
        for definition, distance in lineage:
            for rule in definition.rules:
                path = _policy_path(rule.key)
                by_path[path].append(
                    _PackRuleAtDistance(
                        definition=definition,
                        rule=rule,
                        distance=distance,
                    )
                )

        result: list[_Candidate] = []
        for path in sorted(by_path):
            entries = by_path[path]
            min_distance = min(item.distance for item in entries)
            top = [item for item in entries if item.distance == min_distance]
            top_values = {self._rule_value(item.rule) for item in top}
            if len(top_values) != 1:
                raise PackCompositionConflict(
                    f"unresolved same-specificity inherited pack conflict at {path}"
                )
            chosen = sorted(
                top,
                key=lambda item: _pack_ref_key(item.definition.ref),
            )[0]
            chosen_value = self._rule_value(chosen.rule)

            for ancestor in entries:
                if ancestor.distance <= min_distance:
                    continue
                if self._rule_value(ancestor.rule) == chosen_value:
                    continue
                if not ancestor.rule.override_allowed:
                    raise PackCompositionConflict(
                        f"pack {chosen.definition.pack_id.root}/"
                        f"{chosen.definition.pack_version.root} cannot override "
                        f"non-overrideable inherited rule {path} from "
                        f"{ancestor.definition.pack_id.root}/"
                        f"{ancestor.definition.pack_version.root}"
                    )

            tier = (
                AuthorityTier.HARD_CONSTRAINT
                if chosen.rule.strength is BrainPackRuleStrength.HARD
                else AuthorityTier.INHERITED_PACK_POLICY
            )
            kind = (
                PolicySourceKind.BRAINPACK_HARD_RULE
                if chosen.rule.strength is BrainPackRuleStrength.HARD
                else PolicySourceKind.BRAINPACK_POLICY
            )
            result.append(
                _Candidate(
                    path=path,
                    value=chosen.rule.value,
                    tier=tier,
                    source_kind=kind,
                    source_ref=_version_ref_for_pack(chosen.definition.ref),
                    source_pack_ref=chosen.definition.ref,
                    inherited_via=root_ref,
                    reason=chosen.rule.reason,
                )
            )

        lineage_refs = tuple(
            sorted(
                (definition.ref for definition, _ in lineage),
                key=_pack_ref_key,
            )
        )
        return result, lineage_refs

    async def _load_lineage(
        self,
        root_ref: BrainPackRef,
    ) -> list[tuple[BrainPackDefinition, int]]:
        queue: deque[tuple[BrainPackRef, int]] = deque([(root_ref, 0)])
        best: dict[tuple[str, str], tuple[BrainPackDefinition, int]] = {}

        while queue:
            ref, distance = queue.popleft()
            key = _pack_ref_key(ref)
            existing = best.get(key)
            if existing is not None and existing[1] <= distance:
                continue

            definition = await self.registry.require(ref)
            lifecycle = await self.registry.get_lifecycle(ref)
            if lifecycle.state is not BrainPackLifecycleState.FROZEN:
                raise PackNotReadyError(
                    f"inherited BrainPack must be FROZEN: "
                    f"{ref.pack_id.root}/{ref.pack_version.root} "
                    f"is {lifecycle.state.value}"
                )
            best[key] = (definition, distance)
            for parent in definition.parents:
                queue.append((parent, distance + 1))

        return [
            best[key]
            for key in sorted(
                best,
                key=lambda item: (best[item][1], item[0], item[1]),
            )
        ]

    @staticmethod
    def _rule_value(rule: BrainPackRule) -> str:
        return _canonical_json(rule.value)

    @staticmethod
    def _locked_candidates(
        request: ProfileResolverRequest,
    ) -> list[_Candidate]:
        return [
            _Candidate(
                path=item.path,
                value=item.value,
                tier=AuthorityTier.LOCKED_CANONICAL,
                source_kind=PolicySourceKind.LOCKED_FACT,
                source_ref=item.source_ref,
                reason=item.reason,
            )
            for item in request.locked_values
        ]

    @staticmethod
    def _constraint_candidates(
        request: ProfileResolverRequest,
    ) -> list[_Candidate]:
        result: list[_Candidate] = []
        for constraint in request.topic.value.constraints:
            result.append(
                _Candidate(
                    path=_policy_path(constraint.key),
                    value=constraint.value,
                    tier=(
                        AuthorityTier.HARD_CONSTRAINT
                        if constraint.hard
                        else AuthorityTier.SOFT_PREFERENCE
                    ),
                    source_kind=(
                        PolicySourceKind.PROJECT_HARD_CONSTRAINT
                        if constraint.hard
                        else PolicySourceKind.PROJECT_SOFT_PREFERENCE
                    ),
                    source_ref=request.topic.ref,
                    reason=constraint.reason
                    or "project/topic constraint carried into profile resolution",
                )
            )
        return result

    @staticmethod
    def _override_candidates(
        request: ProfileResolverRequest,
    ) -> list[_Candidate]:
        return [
            _Candidate(
                path=item.path,
                value=item.value,
                tier=AuthorityTier.PROJECT_OVERRIDE,
                source_kind=PolicySourceKind.PROJECT_OVERRIDE,
                source_ref=request.project.ref,
                reason=item.reason,
            )
            for item in request.requested_overrides
        ]

    @staticmethod
    def _local_intent_candidates(
        request: ProfileResolverRequest,
    ) -> list[_Candidate]:
        return [
            _Candidate(
                path=item.path,
                value=item.value,
                tier=AuthorityTier.LOCAL_INTENT,
                source_kind=PolicySourceKind.LOCAL_INTENT,
                source_ref=item.source_ref,
                reason=item.reason,
            )
            for item in request.local_intent
        ]

    @staticmethod
    def _resolve_fields(
        candidates: list[_Candidate],
    ) -> tuple[dict[str, Any], tuple[FieldResolutionTrace, ...]]:
        by_path: dict[str, list[_Candidate]] = defaultdict(list)
        for candidate in candidates:
            by_path[candidate.path].append(candidate)

        effective: dict[str, Any] = {}
        traces: list[FieldResolutionTrace] = []
        for path in sorted(by_path):
            contenders = by_path[path]
            best_rank = min(item.rank for item in contenders)
            top = [item for item in contenders if item.rank == best_rank]
            top_values = {item.canonical_value for item in top}
            if len(top_values) != 1:
                if best_rank == _AUTHORITY_RANK[AuthorityTier.HARD_CONSTRAINT]:
                    raise HardConstraintConflict(
                        f"unresolved hard-hard conflict at {path}"
                    )
                raise ResolutionConflict(
                    f"unresolved equal-precedence conflict at {path}: "
                    f"{top[0].tier.value}"
                )

            chosen = sorted(
                top,
                key=lambda item: (
                    item.source_ref.logical_id.root,
                    item.source_ref.version_id.root,
                    item.source_kind.value,
                ),
            )[0]
            effective[path] = chosen.value

            trace_contenders: list[ResolutionContender] = []
            for contender in sorted(
                contenders,
                key=lambda item: (
                    item.rank,
                    item.source_ref.logical_id.root,
                    item.source_ref.version_id.root,
                    item.source_kind.value,
                ),
            ):
                if contender is chosen:
                    disposition = ContenderDisposition.SELECTED
                elif (
                    contender.rank == chosen.rank
                    and contender.canonical_value == chosen.canonical_value
                ):
                    disposition = ContenderDisposition.EQUIVALENT
                else:
                    disposition = ContenderDisposition.OVERRIDDEN_BY_HIGHER_AUTHORITY
                trace_contenders.append(
                    ResolutionContender(
                        path=path,
                        value=contender.value,
                        tier=contender.tier,
                        precedence_rank=contender.rank,
                        source_kind=contender.source_kind,
                        source_ref=contender.source_ref,
                        source_pack_ref=contender.source_pack_ref,
                        inherited_via=contender.inherited_via,
                        reason=contender.reason,
                        disposition=disposition,
                    )
                )

            traces.append(
                FieldResolutionTrace(
                    path=path,
                    value=chosen.value,
                    winning_tier=chosen.tier,
                    precedence_rank=chosen.rank,
                    winning_source_kind=chosen.source_kind,
                    winning_source_ref=chosen.source_ref,
                    winning_pack_ref=chosen.source_pack_ref,
                    resolution_reason=(
                        f"{chosen.tier.value} outranks lower-authority contenders; "
                        f"{chosen.reason}"
                    ),
                    contenders=tuple(trace_contenders),
                )
            )
        return effective, tuple(traces)


class ProfileResolutionRepository:
    """Immutable persistence adapter for resolver result + ResolutionTrace."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.versions = VersionRepository(writer)

    async def create_initial(
        self,
        *,
        result: ProfileResolutionResult,
        version_id: VersionId,
        provenance: Provenance,
        created_at,
    ) -> ProfileResolutionArtifact:
        artifact = self._artifact(
            result=result,
            version_id=version_id,
            provenance=provenance,
            created_at=created_at,
            predecessor=None,
        )
        stored = await self.versions.create_initial(
            metadata=artifact.metadata,
            payload=artifact.result.model_dump(mode="json"),
            status=LifecycleState.APPROVED,
        )
        return ProfileResolutionArtifact(
            metadata=stored.metadata,
            result=result,
        )

    async def create_successor(
        self,
        *,
        result: ProfileResolutionResult,
        version_id: VersionId,
        provenance: Provenance,
        created_at,
        predecessor: VersionRef,
    ) -> ProfileResolutionArtifact:
        artifact = self._artifact(
            result=result,
            version_id=version_id,
            provenance=provenance,
            created_at=created_at,
            predecessor=predecessor,
        )
        stored = await self.versions.create_successor(
            metadata=artifact.metadata,
            payload=artifact.result.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        return ProfileResolutionArtifact(
            metadata=stored.metadata,
            result=result,
        )

    async def get(
        self,
        ref: VersionRef,
    ) -> ProfileResolutionArtifact | None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        return ProfileResolutionArtifact(
            metadata=stored.metadata,
            result=ProfileResolutionResult.model_validate(stored.payload),
        )

    @staticmethod
    def _artifact(
        *,
        result: ProfileResolutionResult,
        version_id: VersionId,
        provenance: Provenance,
        created_at,
        predecessor: VersionRef | None,
    ) -> ProfileResolutionArtifact:
        metadata = SemanticRecordMetadata(
            logical_id=_profile_resolution_logical_id(result.project_id),
            version_id=version_id,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
        )
        return ProfileResolutionArtifact(
            metadata=metadata,
            result=result,
        )
