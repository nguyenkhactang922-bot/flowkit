"""Canonical early-story intake: Idea, Logline, Premise, Angle and Theme.

Legacy FlowKit project.story remains a compatibility field only. Canonical
story-intake truth is represented by immutable, exact-version artifacts stored
through VersionRepository and promoted only after stage-local blocking gates
pass.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    field_validator,
    model_validator,
)

from .primitives import (
    FindingSeverity,
    GateVerdict,
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    VersionId,
    VersionRef,
)
from .versioning import CurrentPointerNotFound, CurrentVersionPointer, VersionRepository


class StoryIntakeError(ValueError):
    """Base error for canonical early-story intake."""


class StoryIntakeGateBlocked(StoryIntakeError):
    """Raised when a stage-local blocking gate rejects promotion."""


class StoryIntakeIdentityError(StoryIntakeError):
    """Raised when identity or source lineage crosses project/stage authority."""


class StoryIntakeStage(str, Enum):
    IDEA = "IDEA"
    LOGLINE = "LOGLINE"
    PREMISE = "PREMISE"
    ANGLE = "ANGLE"
    THEME = "THEME"


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _unique_refs(values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
    result: list[VersionRef] = []
    seen: set[tuple[str, str]] = set()
    for ref in values:
        key = (ref.logical_id.root, ref.version_id.root)
        if key not in seen:
            seen.add(key)
            result.append(ref)
    return tuple(result)


def _stage_logical_id(stage: StoryIntakeStage, project_id: LogicalId) -> LogicalId:
    return LogicalId(f"story-{stage.value.lower()}:{project_id.root}")


def _active_profile_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"active-profile:{project_id.root}")


def _validate_profile_ref(project_id: LogicalId, ref: VersionRef) -> None:
    if ref.logical_id != _active_profile_id(project_id):
        raise ValueError(
            "active_profile_ref must bind the exact ActiveProductionProfile "
            "for the same project"
        )


class StoryFinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    severity: FindingSeverity
    message: str
    blocking: bool = True

    @field_validator("code", "message")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)


class StoryGateResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    stage: StoryIntakeStage
    verdict: GateVerdict
    findings: tuple[StoryFinding, ...] = ()

    @model_validator(mode="after")
    def validate_verdict(self) -> "StoryGateResult":
        has_blocker = any(item.blocking for item in self.findings)
        if has_blocker and self.verdict is not GateVerdict.FAIL:
            raise ValueError("blocking findings require FAIL verdict")
        if not has_blocker and self.verdict is GateVerdict.FAIL:
            raise ValueError("FAIL verdict requires a blocking finding")
        return self

    @property
    def passed(self) -> bool:
        return self.verdict is GateVerdict.PASS


class _StoryArtifactBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    stage: StoryIntakeStage
    project_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    research_refs: tuple[VersionRef, ...] = ()

    @field_validator("research_refs")
    @classmethod
    def normalize_research_refs(
        cls,
        values: tuple[VersionRef, ...],
    ) -> tuple[VersionRef, ...]:
        return _unique_refs(values)

    @model_validator(mode="after")
    def validate_profile(self):
        _validate_profile_ref(self.project_id, self.active_profile_ref)
        return self

    @property
    def logical_id(self) -> LogicalId:
        return _stage_logical_id(self.stage, self.project_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        raise NotImplementedError


class IdeaContract(_StoryArtifactBase):
    stage: Literal[StoryIntakeStage.IDEA] = StoryIntakeStage.IDEA
    project_ref: VersionRef
    topic_ref: VersionRef
    proposition: str
    intent: str
    scope: str
    context: str
    premise_potential: str
    distinctness: str
    policy_compatible: bool = True
    factuality_compatible: bool = True

    @field_validator(
        "proposition",
        "intent",
        "scope",
        "context",
        "premise_potential",
        "distinctness",
    )
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="project_input", source=self.project_ref),
            SourceVersionBinding(role="topic_resolution", source=self.topic_ref),
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
        ]
        values.extend(
            SourceVersionBinding(role=f"research_seed_{index:03d}", source=ref)
            for index, ref in enumerate(self.research_refs)
        )
        return tuple(values)


class LoglineContract(_StoryArtifactBase):
    stage: Literal[StoryIntakeStage.LOGLINE] = StoryIntakeStage.LOGLINE
    idea_ref: VersionRef
    text: str
    protagonist: str
    drive: str
    conflict: str
    stakes: str
    causal_chain_explicit: bool = True
    locked_fact_conflict: bool = False
    unsupported_factual_claim: bool = False

    @field_validator("text", "protagonist", "drive", "conflict", "stakes")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_idea_project(self) -> "LoglineContract":
        if self.idea_ref.logical_id != _stage_logical_id(
            StoryIntakeStage.IDEA,
            self.project_id,
        ):
            raise ValueError("idea_ref must bind canonical Idea for same project")
        return self

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="accepted_idea", source=self.idea_ref),
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
        ]
        values.extend(
            SourceVersionBinding(role=f"research_constraint_{index:03d}", source=ref)
            for index, ref in enumerate(self.research_refs)
        )
        return tuple(values)


class PremiseCandidate(_StoryArtifactBase):
    stage: Literal[StoryIntakeStage.PREMISE] = StoryIntakeStage.PREMISE
    idea_ref: VersionRef
    logline_ref: VersionRef
    statement: str
    causal_engine: str
    conflict_potential: str
    novelty: str
    causal_development_supported: bool = True
    topic_restatement_only: bool = False

    @field_validator("statement", "causal_engine", "conflict_potential", "novelty")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_parent_project(self) -> "PremiseCandidate":
        if self.idea_ref.logical_id != _stage_logical_id(
            StoryIntakeStage.IDEA,
            self.project_id,
        ):
            raise ValueError("idea_ref must bind canonical Idea for same project")
        if self.logline_ref.logical_id != _stage_logical_id(
            StoryIntakeStage.LOGLINE,
            self.project_id,
        ):
            raise ValueError("logline_ref must bind canonical Logline for same project")
        return self

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="accepted_idea", source=self.idea_ref),
            SourceVersionBinding(role="approved_logline", source=self.logline_ref),
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
        ]
        values.extend(
            SourceVersionBinding(role=f"research_dependency_{index:03d}", source=ref)
            for index, ref in enumerate(self.research_refs)
        )
        return tuple(values)


class AngleCandidate(_StoryArtifactBase):
    stage: Literal[StoryIntakeStage.ANGLE] = StoryIntakeStage.ANGLE
    premise_ref: VersionRef
    perspective: str
    differentiation: str
    audience_promise: str
    factuality_compatible: bool = True
    locked_fact_conflict: bool = False

    @field_validator("perspective", "differentiation", "audience_promise")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_parent_project(self) -> "AngleCandidate":
        if self.premise_ref.logical_id != _stage_logical_id(
            StoryIntakeStage.PREMISE,
            self.project_id,
        ):
            raise ValueError("premise_ref must bind canonical Premise for same project")
        return self

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="accepted_premise", source=self.premise_ref),
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
        ]
        values.extend(
            SourceVersionBinding(role=f"research_perspective_{index:03d}", source=ref)
            for index, ref in enumerate(self.research_refs)
        )
        return tuple(values)


class ThemeHypothesis(_StoryArtifactBase):
    stage: Literal[StoryIntakeStage.THEME] = StoryIntakeStage.THEME
    premise_ref: VersionRef
    angle_ref: VersionRef
    character_refs: tuple[VersionRef, ...] = ()
    conflict_refs: tuple[VersionRef, ...] = ()
    thematic_question: str
    hypothesis: str
    integration_principle: str
    causal_truth_compatible: bool = True
    didactic_repetition_risk: bool = False

    @field_validator("character_refs", "conflict_refs")
    @classmethod
    def normalize_refs(
        cls,
        values: tuple[VersionRef, ...],
    ) -> tuple[VersionRef, ...]:
        return _unique_refs(values)

    @field_validator("thematic_question", "hypothesis", "integration_principle")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_parent_project(self) -> "ThemeHypothesis":
        if self.premise_ref.logical_id != _stage_logical_id(
            StoryIntakeStage.PREMISE,
            self.project_id,
        ):
            raise ValueError("premise_ref must bind canonical Premise for same project")
        if self.angle_ref.logical_id != _stage_logical_id(
            StoryIntakeStage.ANGLE,
            self.project_id,
        ):
            raise ValueError("angle_ref must bind canonical Angle for same project")
        return self

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="accepted_premise", source=self.premise_ref),
            SourceVersionBinding(role="accepted_angle", source=self.angle_ref),
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
        ]
        values.extend(
            SourceVersionBinding(role=f"character_{index:03d}", source=ref)
            for index, ref in enumerate(self.character_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"conflict_{index:03d}", source=ref)
            for index, ref in enumerate(self.conflict_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"research_{index:03d}", source=ref)
            for index, ref in enumerate(self.research_refs)
        )
        return tuple(values)


StoryIntakeValue = Annotated[
    Union[
        IdeaContract,
        LoglineContract,
        PremiseCandidate,
        AngleCandidate,
        ThemeHypothesis,
    ],
    Field(discriminator="stage"),
]
_STORY_VALUE_ADAPTER = TypeAdapter(StoryIntakeValue)


class StoryIntakeArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: StoryIntakeValue

    @model_validator(mode="after")
    def validate_identity(self) -> "StoryIntakeArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("story artifact logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("story artifact version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError(
                "story artifact provenance must exactly bind declared canonical inputs"
            )
        if self.metadata.provenance.rule_version != self.value.active_profile_ref:
            raise ValueError(
                "story artifact provenance rule_version must pin ActiveProductionProfile"
            )
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


class StoryIntakeGateEvaluator:
    """Deterministic stage-local blocking checks; no provider authority."""

    def evaluate(self, value: StoryIntakeValue) -> StoryGateResult:
        findings: list[StoryFinding] = []

        def block(code: str, message: str) -> None:
            findings.append(
                StoryFinding(
                    code=code,
                    severity=FindingSeverity.BLOCKER,
                    message=message,
                    blocking=True,
                )
            )

        if isinstance(value, IdeaContract):
            if not value.policy_compatible:
                block("IDEA_POLICY_CONFLICT", "idea conflicts with pinned project policy")
            if not value.factuality_compatible:
                block("IDEA_FACTUALITY_CONFLICT", "idea conflicts with locked factual truth")

        elif isinstance(value, LoglineContract):
            if not value.causal_chain_explicit:
                block(
                    "LOGLINE_CAUSALITY_MISSING",
                    "logline must encode a causal dramatic chain",
                )
            if value.locked_fact_conflict:
                block(
                    "LOGLINE_LOCKED_FACT_CONFLICT",
                    "logline contradicts locked canonical fact",
                )
            if value.unsupported_factual_claim:
                block(
                    "LOGLINE_UNSUPPORTED_FACT",
                    "logline contains unsupported factual claim",
                )

        elif isinstance(value, PremiseCandidate):
            if not value.causal_development_supported:
                block(
                    "PREMISE_CAUSAL_DEVELOPMENT_MISSING",
                    "premise does not support causal development",
                )
            if value.topic_restatement_only:
                block(
                    "PREMISE_TOPIC_RESTATEMENT",
                    "premise only restates the topic",
                )

        elif isinstance(value, AngleCandidate):
            if not value.factuality_compatible:
                block(
                    "ANGLE_FACTUALITY_CONFLICT",
                    "angle is incompatible with canonical evidence/facts",
                )
            if value.locked_fact_conflict:
                block(
                    "ANGLE_LOCKED_FACT_CONFLICT",
                    "angle contradicts locked canonical fact",
                )

        elif isinstance(value, ThemeHypothesis):
            if not value.causal_truth_compatible:
                block(
                    "THEME_CAUSAL_TRUTH_CONFLICT",
                    "theme would force violation of causal truth",
                )
            if value.didactic_repetition_risk:
                block(
                    "THEME_DIDACTIC_REPETITION",
                    "theme repeats as slogan rather than integrated meaning",
                )

        return StoryGateResult(
            stage=value.stage,
            verdict=GateVerdict.FAIL if findings else GateVerdict.PASS,
            findings=tuple(findings),
        )


def build_story_intake_provenance(
    value: StoryIntakeValue,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=value.source_bindings(),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        rule_version=value.active_profile_ref,
        correlation_id=correlation_id,
    )


class StoryIntakeRepository:
    """Immutable repository + approval coordination for early-story artifacts."""

    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)
        self.gates = StoryIntakeGateEvaluator()

    async def create_initial(
        self,
        *,
        value: StoryIntakeValue,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryIntakeArtifact:
        artifact = self._artifact(
            value=value,
            provenance=provenance,
            created_at=created_at,
            predecessor=None,
        )
        stored = await self.versions.create_initial(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        return StoryIntakeArtifact(metadata=stored.metadata, value=value)

    async def create_successor(
        self,
        *,
        value: StoryIntakeValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryIntakeArtifact:
        if predecessor.logical_id != value.logical_id:
            raise StoryIntakeIdentityError(
                "story successor predecessor must share canonical stage identity"
            )
        artifact = self._artifact(
            value=value,
            provenance=provenance,
            created_at=created_at,
            predecessor=predecessor,
        )
        stored = await self.versions.create_successor(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        return StoryIntakeArtifact(metadata=stored.metadata, value=value)

    async def get(self, ref: VersionRef) -> StoryIntakeArtifact | None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = _STORY_VALUE_ADAPTER.validate_python(stored.payload)
        return StoryIntakeArtifact(metadata=stored.metadata, value=value)

    async def promote(
        self,
        *,
        ref: VersionRef,
        expected_revision: int,
    ) -> CurrentVersionPointer:
        artifact = await self.get(ref)
        if artifact is None:
            raise StoryIntakeIdentityError(
                f"story artifact not found: {ref.logical_id.root}/{ref.version_id.root}"
            )
        gate = self.gates.evaluate(artifact.value)
        if not gate.passed:
            codes = ",".join(item.code for item in gate.findings if item.blocking)
            raise StoryIntakeGateBlocked(
                f"{artifact.value.stage.value} gate blocked: {codes}"
            )
        await self._assert_exact_inputs_ready(artifact.value)
        return await self.versions.update_current(
            logical_id=artifact.value.logical_id,
            version_id=artifact.value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )

    async def _assert_exact_inputs_ready(
        self,
        value: StoryIntakeValue,
    ) -> None:
        for binding in value.source_bindings():
            if await self.versions.get_version(binding.source) is None:
                raise StoryIntakeGateBlocked(
                    f"{value.stage.value} gate blocked: missing exact source "
                    f"{binding.role}={binding.source.logical_id.root}/"
                    f"{binding.source.version_id.root}"
                )

        try:
            profile_pointer = await self.versions.get_current(
                value.active_profile_ref.logical_id
            )
        except CurrentPointerNotFound as exc:
            raise StoryIntakeGateBlocked(
                f"{value.stage.value} gate blocked: missing "
                "ActiveProductionProfile current pointer"
            ) from exc
        if (
            profile_pointer.version_id != value.active_profile_ref.version_id
            or profile_pointer.status is not LifecycleState.LOCKED
        ):
            raise StoryIntakeGateBlocked(
                f"{value.stage.value} gate blocked: stale/unlocked "
                "ActiveProductionProfile"
            )

        for parent in self._story_parent_refs(value):
            try:
                pointer = await self.versions.get_current(parent.logical_id)
            except CurrentPointerNotFound as exc:
                raise StoryIntakeGateBlocked(
                    f"{value.stage.value} gate blocked: parent story artifact "
                    f"has no current pointer {parent.logical_id.root}"
                ) from exc
            if (
                pointer.version_id != parent.version_id
                or pointer.status
                not in {LifecycleState.APPROVED, LifecycleState.LOCKED}
            ):
                raise StoryIntakeGateBlocked(
                    f"{value.stage.value} gate blocked: parent story artifact "
                    f"is not exact current accepted version "
                    f"{parent.logical_id.root}/{parent.version_id.root}"
                )

    @staticmethod
    def _story_parent_refs(value: StoryIntakeValue) -> tuple[VersionRef, ...]:
        if isinstance(value, IdeaContract):
            return ()
        if isinstance(value, LoglineContract):
            return (value.idea_ref,)
        if isinstance(value, PremiseCandidate):
            return (value.idea_ref, value.logline_ref)
        if isinstance(value, AngleCandidate):
            return (value.premise_ref,)
        if isinstance(value, ThemeHypothesis):
            return (value.premise_ref, value.angle_ref)
        raise TypeError(f"unsupported story intake value: {type(value)!r}")

    async def get_current(
        self,
        *,
        stage: StoryIntakeStage,
        project_id: LogicalId,
    ) -> StoryIntakeArtifact | None:
        logical_id = _stage_logical_id(stage, project_id)
        try:
            pointer = await self.versions.get_current(logical_id)
        except CurrentPointerNotFound:
            return None
        if pointer is None:
            return None
        return await self.get(
            VersionRef(logical_id=logical_id, version_id=pointer.version_id)
        )

    @staticmethod
    def _artifact(
        *,
        value: StoryIntakeValue,
        provenance: Provenance,
        created_at: datetime,
        predecessor: VersionRef | None,
    ) -> StoryIntakeArtifact:
        metadata = SemanticRecordMetadata(
            logical_id=value.logical_id,
            version_id=value.version_id,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
        )
        return StoryIntakeArtifact(metadata=metadata, value=value)


class StoryIntakeService:
    """Application boundary for candidate creation, revision and acceptance."""

    def __init__(self, repository: StoryIntakeRepository) -> None:
        self.repository = repository
        self.gates = repository.gates

    def evaluate(self, value: StoryIntakeValue) -> StoryGateResult:
        return self.gates.evaluate(value)

    async def create_candidate(
        self,
        *,
        value: StoryIntakeValue,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryIntakeArtifact:
        return await self.repository.create_initial(
            value=value,
            provenance=provenance,
            created_at=created_at,
        )

    async def revise_candidate(
        self,
        *,
        value: StoryIntakeValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryIntakeArtifact:
        return await self.repository.create_successor(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
        )

    async def accept_candidate(
        self,
        *,
        ref: VersionRef,
        expected_revision: int,
    ) -> CurrentVersionPointer:
        return await self.repository.promote(
            ref=ref,
            expected_revision=expected_revision,
        )
