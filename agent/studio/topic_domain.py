"""Provider-neutral Project / Topic / Domain resolution contracts.

Frozen authority implemented here:
- Project domain owns project identity/bootstrap intent.
- Topic Intelligence owns normalized topic labels/ambiguity/constraints only.
- Domain/Niche/Genre Resolution owns topic-derived classification only.
- Topic resolution cannot depend on ProfileResolver/ActiveProductionProfile.
- Hard project constraints outrank soft classification preferences.
- Semantic outputs persist through the generic immutable VersionRepository.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
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
from .versioning import (
    CurrentVersionPointer,
    StoredSemanticVersion,
    VersionRepository,
)


class ResolutionContractError(ValueError):
    """Base error for Project/Topic/Domain resolution contract violations."""


class UnsupportedFactualityClass(ResolutionContractError):
    """Raised when bootstrap factuality policy is unsupported by the resolver."""


class HardConstraintViolation(ResolutionContractError):
    """Raised when classifier output contradicts a locked project constraint."""


class MissingAmbiguityTrace(ResolutionContractError):
    """Raised when ambiguity is detected but not represented explicitly."""


_KEY_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _unique_trimmed(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        item = _trimmed(value, label)
        if item not in result:
            result.append(item)
    return tuple(result)


def _normalize_topic(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("raw_topic must contain non-whitespace text")
    return " ".join(unicodedata.normalize("NFKC", value).split())


def _logical_project_input_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"project-input:{project_id.root}")


def _logical_topic_resolution_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"topic-resolution:{project_id.root}")


def _logical_domain_resolution_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"niche-resolution:{project_id.root}")


def _binding_map(provenance: Provenance) -> dict[str, VersionRef]:
    result: dict[str, VersionRef] = {}
    for binding in provenance.source_versions:
        if binding.role in result:
            raise ValueError(f"duplicate provenance role: {binding.role}")
        result[binding.role] = binding.source
    return result


def _collect_evidence_refs(*groups: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for group in groups:
        for value in group:
            item = _trimmed(value, "source evidence ref")
            if item not in result:
                result.append(item)
    return tuple(result)


class ProjectConstraint(BaseModel):
    """Project-level constraint or preference carried into classification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    value: str
    hard: bool = False
    reason: str | None = None

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        normalized = _trimmed(value, "constraint key").lower()
        if not _KEY_RE.fullmatch(normalized):
            raise ValueError("constraint key must be a canonical lowercase key")
        return normalized

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        return _trimmed(value, "constraint value")

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str | None) -> str | None:
        return None if value is None else _trimmed(value, "constraint reason")


class ProjectBootstrapInput(BaseModel):
    """Canonical bootstrap intent, stripped of FlowKit/provider-specific fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    raw_topic: str
    project_goals: tuple[str, ...] = ()
    language: str
    locale: str | None = None
    target_duration_seconds: int | None = Field(default=None, ge=1)
    platform_hints: tuple[str, ...] = ()
    format_hints: tuple[str, ...] = ()
    audience_hints: tuple[str, ...] = ()
    factuality_mode: str
    constraints: tuple[ProjectConstraint, ...] = ()
    source_evidence_refs: tuple[str, ...]

    @field_validator("raw_topic")
    @classmethod
    def validate_raw_topic(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("raw_topic must contain non-whitespace text")
        return value

    @field_validator("language", "factuality_mode")
    @classmethod
    def validate_required_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("locale")
    @classmethod
    def validate_locale(cls, value: str | None) -> str | None:
        return None if value is None else _trimmed(value, "locale")

    @field_validator(
        "project_goals",
        "platform_hints",
        "format_hints",
        "audience_hints",
        "source_evidence_refs",
    )
    @classmethod
    def validate_string_groups(
        cls,
        values: tuple[str, ...],
        info,
    ) -> tuple[str, ...]:
        return _unique_trimmed(values, info.field_name)

    @model_validator(mode="after")
    def require_source_evidence(self) -> "ProjectBootstrapInput":
        if not self.source_evidence_refs:
            raise ValueError("bootstrap input requires at least one source evidence ref")
        keys = [item.key for item in self.constraints]
        if len(set(keys)) != len(keys):
            raise ValueError("project constraint keys must be unique")
        return self


class WeightedLabel(BaseModel):
    """One weighted classification candidate with inspectable rationale."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str
    weight: float = Field(ge=0.0, le=1.0)
    reason: str
    evidence_refs: tuple[str, ...] = ()

    @field_validator("label", "reason")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _unique_trimmed(values, "evidence ref")


class AmbiguityItem(BaseModel):
    """Explicit unresolved classification ambiguity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    axis: str
    candidates: tuple[WeightedLabel, ...]
    reason: str

    @field_validator("axis", "reason")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_candidates(self) -> "AmbiguityItem":
        if len(self.candidates) < 2:
            raise ValueError("ambiguity requires at least two candidates")
        return self


class TopicClassifierOutput(BaseModel):
    """Provider-neutral classifier result consumed by TopicResolutionService."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    weighted_labels: tuple[WeightedLabel, ...]
    ambiguity_detected: bool = False
    ambiguity_set: tuple[AmbiguityItem, ...] = ()
    derived_constraints: tuple[ProjectConstraint, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _unique_trimmed(values, "classifier evidence ref")

    @model_validator(mode="after")
    def validate_output(self) -> "TopicClassifierOutput":
        if not self.weighted_labels:
            raise ValueError("topic classifier must emit at least one weighted label")
        labels = [item.label.casefold() for item in self.weighted_labels]
        if len(set(labels)) != len(labels):
            raise ValueError("topic weighted labels must be unique")
        if self.ambiguity_detected and not self.ambiguity_set:
            raise ValueError("detected topic ambiguity must be explicit")
        if not self.ambiguity_detected and self.ambiguity_set:
            raise ValueError("ambiguity_set requires ambiguity_detected=true")
        return self


class TopicResolution(BaseModel):
    """Canonical Topic Intelligence output; topic is intentionally not niche."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    normalized_topic: str
    weighted_topic_labels: tuple[WeightedLabel, ...]
    ambiguity_set: tuple[AmbiguityItem, ...] = ()
    constraints: tuple[ProjectConstraint, ...] = ()
    factuality_mode: str
    normalizer_rule_version: VersionRef
    classifier_rule_version: VersionRef

    @field_validator("normalized_topic", "factuality_mode")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_labels(self) -> "TopicResolution":
        if not self.weighted_topic_labels:
            raise ValueError("topic resolution requires weighted labels")
        return self


class ClassificationAxis(str, Enum):
    DOMAIN = "domain"
    NICHE = "niche"
    GENRE = "genre"
    AUDIENCE = "audience"
    FORMAT = "format"
    PLATFORM = "platform"
    FACTUALITY = "factuality"


class AxisClassification(BaseModel):
    """Weighted classification for one canonical Domain/Niche/Genre axis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    axis: ClassificationAxis
    labels: tuple[WeightedLabel, ...] = ()
    unknown: bool = False

    @model_validator(mode="after")
    def validate_axis(self) -> "AxisClassification":
        if self.axis is ClassificationAxis.NICHE:
            if not self.labels and not self.unknown:
                raise ValueError("empty niche classification must be explicitly unknown")
        elif not self.labels:
            raise ValueError(f"{self.axis.value} classification requires at least one label")

        labels = [item.label.casefold() for item in self.labels]
        if len(set(labels)) != len(labels):
            raise ValueError(f"{self.axis.value} labels must be unique")
        return self


class ClassificationTraceItem(BaseModel):
    """Inspectible rationale without becoming final policy/pack authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    axis: ClassificationAxis
    decision: str
    reason: str
    evidence_refs: tuple[str, ...] = ()

    @field_validator("decision", "reason")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("evidence_refs")
    @classmethod
    def validate_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _unique_trimmed(values, "classification evidence ref")


class DomainClassifierOutput(BaseModel):
    """Provider-neutral Domain/Niche/Genre classifier result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    classifications: tuple[AxisClassification, ...]
    ambiguity_detected: bool = False
    ambiguity_trace: tuple[AmbiguityItem, ...] = ()
    classification_trace: tuple[ClassificationTraceItem, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _unique_trimmed(values, "classifier evidence ref")

    @model_validator(mode="after")
    def validate_complete_axes(self) -> "DomainClassifierOutput":
        seen = [item.axis for item in self.classifications]
        required = set(ClassificationAxis)
        if set(seen) != required or len(seen) != len(required):
            raise ValueError(
                "domain classifier must emit each canonical classification axis exactly once"
            )
        if self.ambiguity_detected and not self.ambiguity_trace:
            raise ValueError("detected domain ambiguity must be explicit")
        if not self.ambiguity_detected and self.ambiguity_trace:
            raise ValueError("ambiguity_trace requires ambiguity_detected=true")
        return self


class DomainResolution(BaseModel):
    """Canonical topic-derived classification; never the effective pack stack."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    topic_resolution_ref: VersionRef
    registry_metadata_ref: VersionRef
    classifier_rule_version: VersionRef
    classifications: tuple[AxisClassification, ...]
    ambiguity_trace: tuple[AmbiguityItem, ...] = ()
    classification_trace: tuple[ClassificationTraceItem, ...] = ()
    project_constraints: tuple[ProjectConstraint, ...] = ()

    @model_validator(mode="after")
    def validate_axes(self) -> "DomainResolution":
        output = DomainClassifierOutput(
            classifications=self.classifications,
            ambiguity_detected=bool(self.ambiguity_trace),
            ambiguity_trace=self.ambiguity_trace,
            classification_trace=self.classification_trace,
        )
        if len(output.classifications) != len(ClassificationAxis):
            raise ValueError("incomplete classification output")
        return self

    def axis(self, axis: ClassificationAxis) -> AxisClassification:
        for item in self.classifications:
            if item.axis is axis:
                return item
        raise KeyError(axis)


class ProjectBootstrapArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: ProjectBootstrapInput

    @model_validator(mode="after")
    def validate_identity(self) -> "ProjectBootstrapArtifact":
        expected = _logical_project_input_id(self.value.project_id)
        if self.metadata.logical_id != expected:
            raise ValueError(
                f"project bootstrap logical_id must be {expected.root}"
            )
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(
            logical_id=self.metadata.logical_id,
            version_id=self.metadata.version_id,
        )


class TopicResolutionArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: TopicResolution

    @model_validator(mode="after")
    def validate_authority(self) -> "TopicResolutionArtifact":
        expected = _logical_topic_resolution_id(self.value.project_id)
        if self.metadata.logical_id != expected:
            raise ValueError(f"topic logical_id must be {expected.root}")

        bindings = _binding_map(self.metadata.provenance)
        required = {
            "project_input",
            "topic_normalizer_rule",
            "topic_classifier_rule",
        }
        if set(bindings) != required:
            raise ValueError(
                "topic provenance must bind project_input, topic_normalizer_rule, "
                "and topic_classifier_rule exactly"
            )
        if (
            bindings["project_input"].logical_id
            != _logical_project_input_id(self.value.project_id)
        ):
            raise ValueError("topic project_input provenance belongs to another project")
        if bindings["topic_normalizer_rule"] != self.value.normalizer_rule_version:
            raise ValueError("topic normalizer rule provenance mismatch")
        if bindings["topic_classifier_rule"] != self.value.classifier_rule_version:
            raise ValueError("topic classifier rule provenance mismatch")
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(
            logical_id=self.metadata.logical_id,
            version_id=self.metadata.version_id,
        )


class DomainResolutionArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: DomainResolution

    @model_validator(mode="after")
    def validate_authority(self) -> "DomainResolutionArtifact":
        expected = _logical_domain_resolution_id(self.value.project_id)
        if self.metadata.logical_id != expected:
            raise ValueError(f"domain logical_id must be {expected.root}")

        bindings = _binding_map(self.metadata.provenance)
        required = {
            "topic_resolution",
            "registry_metadata",
            "domain_classifier_rule",
        }
        if set(bindings) != required:
            raise ValueError(
                "domain provenance must bind topic_resolution, registry_metadata, "
                "and domain_classifier_rule exactly"
            )
        if bindings["topic_resolution"] != self.value.topic_resolution_ref:
            raise ValueError("domain topic provenance mismatch")
        if bindings["registry_metadata"] != self.value.registry_metadata_ref:
            raise ValueError("domain registry provenance mismatch")
        if bindings["domain_classifier_rule"] != self.value.classifier_rule_version:
            raise ValueError("domain classifier rule provenance mismatch")
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(
            logical_id=self.metadata.logical_id,
            version_id=self.metadata.version_id,
        )


class TopicResolutionService:
    """Validates/resolves Topic Intelligence without any profile dependency."""

    def __init__(
        self,
        *,
        normalizer_rule_version: VersionRef,
        classifier_rule_version: VersionRef,
        supported_factuality_modes: frozenset[str],
    ) -> None:
        if not supported_factuality_modes:
            raise ValueError("supported_factuality_modes must not be empty")
        self.normalizer_rule_version = normalizer_rule_version
        self.classifier_rule_version = classifier_rule_version
        self.supported_factuality_modes = frozenset(
            _trimmed(item, "supported factuality mode")
            for item in supported_factuality_modes
        )

    def build_bootstrap_artifact(
        self,
        *,
        value: ProjectBootstrapInput,
        version_id: VersionId,
        actor_ref: str,
        reason: str,
        created_at: datetime,
        predecessor: VersionRef | None = None,
        correlation_id: str | None = None,
    ) -> ProjectBootstrapArtifact:
        provenance = Provenance(
            source_refs=value.source_evidence_refs,
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=created_at,
            correlation_id=correlation_id,
        )
        metadata = SemanticRecordMetadata(
            logical_id=_logical_project_input_id(value.project_id),
            version_id=version_id,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
        )
        return ProjectBootstrapArtifact(metadata=metadata, value=value)

    def resolve(
        self,
        *,
        project_input: ProjectBootstrapArtifact,
        version_id: VersionId,
        classification: TopicClassifierOutput,
        actor_ref: str,
        reason: str,
        created_at: datetime,
        predecessor: VersionRef | None = None,
        correlation_id: str | None = None,
    ) -> TopicResolutionArtifact:
        factuality = project_input.value.factuality_mode
        if factuality not in self.supported_factuality_modes:
            raise UnsupportedFactualityClass(
                f"unsupported factuality mode: {factuality}"
            )

        merged_constraints = self._merge_constraints(
            project_input.value.constraints,
            classification.derived_constraints,
        )
        value = TopicResolution(
            project_id=project_input.value.project_id,
            normalized_topic=_normalize_topic(project_input.value.raw_topic),
            weighted_topic_labels=classification.weighted_labels,
            ambiguity_set=classification.ambiguity_set,
            constraints=merged_constraints,
            factuality_mode=factuality,
            normalizer_rule_version=self.normalizer_rule_version,
            classifier_rule_version=self.classifier_rule_version,
        )
        source_refs = _collect_evidence_refs(
            project_input.value.source_evidence_refs,
            classification.evidence_refs,
            *tuple(
                label.evidence_refs for label in classification.weighted_labels
            ),
        )
        provenance = Provenance(
            source_versions=(
                SourceVersionBinding(
                    role="project_input",
                    source=project_input.ref,
                ),
                SourceVersionBinding(
                    role="topic_normalizer_rule",
                    source=self.normalizer_rule_version,
                ),
                SourceVersionBinding(
                    role="topic_classifier_rule",
                    source=self.classifier_rule_version,
                ),
            ),
            source_refs=source_refs,
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=created_at,
            rule_version=self.classifier_rule_version,
            correlation_id=correlation_id,
        )
        metadata = SemanticRecordMetadata(
            logical_id=_logical_topic_resolution_id(value.project_id),
            version_id=version_id,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
        )
        return TopicResolutionArtifact(metadata=metadata, value=value)

    @staticmethod
    def _merge_constraints(
        base: tuple[ProjectConstraint, ...],
        derived: tuple[ProjectConstraint, ...],
    ) -> tuple[ProjectConstraint, ...]:
        result = list(base)
        by_key = {item.key: item for item in base}
        for item in derived:
            existing = by_key.get(item.key)
            if existing is not None and existing.hard:
                if existing.value.casefold() != item.value.casefold():
                    raise HardConstraintViolation(
                        f"classifier constraint {item.key}={item.value!r} "
                        f"conflicts with locked project value {existing.value!r}"
                    )
                continue
            if existing is None:
                result.append(item)
                by_key[item.key] = item
            else:
                index = result.index(existing)
                result[index] = item
                by_key[item.key] = item
        return tuple(result)


class DomainResolutionService:
    """Validates topic-derived classification without owning effective policy."""

    def __init__(
        self,
        *,
        classifier_rule_version: VersionRef,
        supported_factuality_modes: frozenset[str],
    ) -> None:
        if not supported_factuality_modes:
            raise ValueError("supported_factuality_modes must not be empty")
        self.classifier_rule_version = classifier_rule_version
        self.supported_factuality_modes = frozenset(
            _trimmed(item, "supported factuality mode")
            for item in supported_factuality_modes
        )

    def resolve(
        self,
        *,
        topic: TopicResolutionArtifact,
        registry_metadata_ref: VersionRef,
        version_id: VersionId,
        classification: DomainClassifierOutput,
        actor_ref: str,
        reason: str,
        created_at: datetime,
        predecessor: VersionRef | None = None,
        correlation_id: str | None = None,
    ) -> DomainResolutionArtifact:
        factuality_axis = next(
            item
            for item in classification.classifications
            if item.axis is ClassificationAxis.FACTUALITY
        )
        for label in factuality_axis.labels:
            if label.label not in self.supported_factuality_modes:
                raise UnsupportedFactualityClass(
                    f"unsupported factuality classification: {label.label}"
                )

        self._enforce_hard_constraints(
            topic.value.constraints,
            classification.classifications,
        )
        value = DomainResolution(
            project_id=topic.value.project_id,
            topic_resolution_ref=topic.ref,
            registry_metadata_ref=registry_metadata_ref,
            classifier_rule_version=self.classifier_rule_version,
            classifications=classification.classifications,
            ambiguity_trace=classification.ambiguity_trace,
            classification_trace=classification.classification_trace,
            project_constraints=topic.value.constraints,
        )
        trace_refs = tuple(
            ref
            for item in classification.classification_trace
            for ref in item.evidence_refs
        )
        axis_refs = tuple(
            ref
            for axis in classification.classifications
            for label in axis.labels
            for ref in label.evidence_refs
        )
        provenance = Provenance(
            source_versions=(
                SourceVersionBinding(
                    role="topic_resolution",
                    source=topic.ref,
                ),
                SourceVersionBinding(
                    role="registry_metadata",
                    source=registry_metadata_ref,
                ),
                SourceVersionBinding(
                    role="domain_classifier_rule",
                    source=self.classifier_rule_version,
                ),
            ),
            source_refs=_collect_evidence_refs(
                classification.evidence_refs,
                trace_refs,
                axis_refs,
            ),
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=created_at,
            rule_version=self.classifier_rule_version,
            correlation_id=correlation_id,
        )
        metadata = SemanticRecordMetadata(
            logical_id=_logical_domain_resolution_id(value.project_id),
            version_id=version_id,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
        )
        return DomainResolutionArtifact(metadata=metadata, value=value)

    @staticmethod
    def _enforce_hard_constraints(
        constraints: tuple[ProjectConstraint, ...],
        classifications: tuple[AxisClassification, ...],
    ) -> None:
        by_axis = {item.axis.value: item for item in classifications}
        for constraint in constraints:
            if not constraint.hard or constraint.key not in by_axis:
                continue
            axis = by_axis[constraint.key]
            labels = {item.label.casefold() for item in axis.labels}
            if constraint.value.casefold() not in labels:
                raise HardConstraintViolation(
                    f"{constraint.key} classification violates locked value "
                    f"{constraint.value!r}"
                )


class ProjectTopicDomainRepository:
    """Typed adapter over the generic immutable VersionRepository."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.versions = VersionRepository(writer)

    async def save_project_input(
        self,
        artifact: ProjectBootstrapArtifact,
        *,
        status: LifecycleState = LifecycleState.DRAFT,
    ) -> StoredSemanticVersion:
        return await self._save(
            artifact.metadata,
            artifact.value.model_dump(mode="json"),
            status=status,
        )

    async def save_topic(
        self,
        artifact: TopicResolutionArtifact,
        *,
        status: LifecycleState = LifecycleState.REVIEW,
    ) -> StoredSemanticVersion:
        return await self._save(
            artifact.metadata,
            artifact.value.model_dump(mode="json"),
            status=status,
        )

    async def save_domain(
        self,
        artifact: DomainResolutionArtifact,
        *,
        status: LifecycleState = LifecycleState.REVIEW,
    ) -> StoredSemanticVersion:
        return await self._save(
            artifact.metadata,
            artifact.value.model_dump(mode="json"),
            status=status,
        )

    async def get_project_input(
        self,
        ref: VersionRef,
    ) -> ProjectBootstrapArtifact | None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        return ProjectBootstrapArtifact(
            metadata=stored.metadata,
            value=ProjectBootstrapInput.model_validate(stored.payload),
        )

    async def get_topic(
        self,
        ref: VersionRef,
    ) -> TopicResolutionArtifact | None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        return TopicResolutionArtifact(
            metadata=stored.metadata,
            value=TopicResolution.model_validate(stored.payload),
        )

    async def get_domain(
        self,
        ref: VersionRef,
    ) -> DomainResolutionArtifact | None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        return DomainResolutionArtifact(
            metadata=stored.metadata,
            value=DomainResolution.model_validate(stored.payload),
        )

    async def update_current(
        self,
        *,
        logical_id: LogicalId,
        version_id: VersionId,
        status: LifecycleState,
        expected_revision: int,
    ) -> CurrentVersionPointer:
        return await self.versions.update_current(
            logical_id=logical_id,
            version_id=version_id,
            status=status,
            expected_revision=expected_revision,
        )

    async def _save(
        self,
        metadata: SemanticRecordMetadata,
        payload: dict[str, Any],
        *,
        status: LifecycleState,
    ) -> StoredSemanticVersion:
        if metadata.predecessor is None:
            return await self.versions.create_initial(
                metadata=metadata,
                payload=payload,
                status=status,
            )
        return await self.versions.create_successor(
            metadata=metadata,
            payload=payload,
        )
