"""Canonical StoryCore, Conflict/Stakes, CausalStoryGraph and StoryCore lock.

IMP-023 implements the frozen two-phase StoryCore lifecycle:

StoryCore DRAFT -> Conflict/Stakes -> CausalStoryGraph -> causal validation ->
FROZEN_FOR_STRUCTURE successor of the same StoryCore logical identity.

All records are provider-neutral immutable semantic versions. Exact-version
dependencies are persisted through the shared DependencyGraphRepository and
StoryCore revisions produce durable selective invalidation records.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TypeAlias

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from .character_state import CharacterModelVersion, RelationshipState

from .invalidation import (
    DependencyGraphRepository,
    InvalidationRecord,
    InvalidationRepository,
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
from .versioning import CurrentVersionPointer, VersionRepository


class StoryCoreError(ValueError):
    """Base error for IMP-023 story-core domain boundaries."""


class StoryCoreGateBlocked(StoryCoreError):
    """Raised when exact-version or causal gates block progression."""


class StoryCoreIdentityError(StoryCoreError):
    """Raised when a record crosses canonical identity/authority boundaries."""


class StoryCorePhase(str, Enum):
    DRAFT = "DRAFT"
    FROZEN_FOR_STRUCTURE = "FROZEN_FOR_STRUCTURE"


class StoryGraphNodeKind(str, Enum):
    EVENT = "EVENT"
    DECISION = "DECISION"
    REVELATION = "REVELATION"
    REVERSAL = "REVERSAL"
    SETUP = "SETUP"
    PAYOFF = "PAYOFF"
    STATE_CHANGE = "STATE_CHANGE"


class StoryGraphEdgeKind(str, Enum):
    CAUSES = "CAUSES"
    ENABLES = "ENABLES"
    MOTIVATES = "MOTIVATES"
    REVEALS = "REVEALS"
    PAYS_OFF = "PAYS_OFF"


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _unique_text(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        item = _trimmed(value, label)
        if item not in result:
            result.append(item)
    return tuple(result)


def _unique_refs(values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
    result: list[VersionRef] = []
    seen: set[tuple[str, str]] = set()
    for ref in values:
        key = (ref.logical_id.root, ref.version_id.root)
        if key not in seen:
            seen.add(key)
            result.append(ref)
    return tuple(result)


def story_core_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"story-core:{project_id.root}")


def conflict_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"conflict:{project_id.root}")


def stakes_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"stakes:{project_id.root}")


def story_graph_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"story-graph:{project_id.root}")


def causal_validation_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"story-graph-validation:{project_id.root}")


def _active_profile_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"active-profile:{project_id.root}")


def _require_prefix(ref: VersionRef, prefix: str, label: str) -> None:
    if not ref.logical_id.root.startswith(prefix):
        raise ValueError(f"{label} must reference canonical {prefix.rstrip(':')}")


def _require_project_logical_id(
    ref: VersionRef,
    expected: LogicalId,
    label: str,
) -> None:
    if ref.logical_id != expected:
        raise ValueError(
            f"{label} must reference canonical object for the same project"
        )


def _require_project_research_ref(
    ref: VersionRef,
    project_id: LogicalId,
    label: str,
) -> None:
    root = ref.logical_id.root
    allowed = (
        f"research-brief:{project_id.root}",
        f"evidence-claim:{project_id.root}:",
        f"story-material:{project_id.root}:",
    )
    if root != allowed[0] and not root.startswith(allowed[1:]):
        raise ValueError(
            f"{label} must reference canonical Research/StoryMaterial "
            "for the same project"
        )


class StoryCoreLockManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    draft_ref: VersionRef
    story_graph_ref: VersionRef
    causal_validation_ref: VersionRef
    locked_at: AwareDatetime

    @model_validator(mode="after")
    def validate_refs(self) -> "StoryCoreLockManifest":
        _require_prefix(self.draft_ref, "story-core:", "draft_ref")
        _require_prefix(self.story_graph_ref, "story-graph:", "story_graph_ref")
        _require_prefix(
            self.causal_validation_ref,
            "story-graph-validation:",
            "causal_validation_ref",
        )
        return self


class StoryCoreVersion(BaseModel):
    """One immutable version of the single canonical StoryCore identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    version_id: VersionId
    phase: StoryCorePhase
    active_profile_ref: VersionRef
    idea_ref: VersionRef
    logline_ref: VersionRef
    premise_ref: VersionRef
    angle_ref: VersionRef
    theme_ref: VersionRef
    character_refs: tuple[VersionRef, ...] = ()
    research_refs: tuple[VersionRef, ...] = ()
    core_goal: str
    core_question: str
    core_conflict: str
    core_stakes: str
    factual_constraints: tuple[str, ...] = ()
    canonical_hard_constraints_satisfied: bool = True
    factuality_compatible: bool = True
    lock_manifest: StoryCoreLockManifest | None = None

    @field_validator("character_refs", "research_refs")
    @classmethod
    def normalize_refs(
        cls,
        values: tuple[VersionRef, ...],
    ) -> tuple[VersionRef, ...]:
        return _unique_refs(values)

    @field_validator(
        "core_goal",
        "core_question",
        "core_conflict",
        "core_stakes",
    )
    @classmethod
    def validate_required_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("factual_constraints")
    @classmethod
    def normalize_constraints(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _unique_text(values, "factual_constraints")

    @model_validator(mode="after")
    def validate_authority(self) -> "StoryCoreVersion":
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError(
                "active_profile_ref must bind exact ActiveProductionProfile "
                "for same project"
            )
        _require_project_logical_id(
            self.idea_ref,
            LogicalId(f"story-idea:{self.project_id.root}"),
            "idea_ref",
        )
        _require_project_logical_id(
            self.logline_ref,
            LogicalId(f"story-logline:{self.project_id.root}"),
            "logline_ref",
        )
        _require_project_logical_id(
            self.premise_ref,
            LogicalId(f"story-premise:{self.project_id.root}"),
            "premise_ref",
        )
        _require_project_logical_id(
            self.angle_ref,
            LogicalId(f"story-angle:{self.project_id.root}"),
            "angle_ref",
        )
        _require_project_logical_id(
            self.theme_ref,
            LogicalId(f"story-theme:{self.project_id.root}"),
            "theme_ref",
        )
        for ref in self.character_refs:
            _require_prefix(ref, "character-model:", "character_refs")
        for ref in self.research_refs:
            _require_project_research_ref(ref, self.project_id, "research_refs")
        if self.phase is StoryCorePhase.DRAFT:
            if self.lock_manifest is not None:
                raise ValueError("DRAFT StoryCore cannot carry a lock_manifest")
        else:
            if self.lock_manifest is None:
                raise ValueError(
                    "FROZEN_FOR_STRUCTURE StoryCore requires lock_manifest"
                )
            if self.lock_manifest.draft_ref.logical_id != self.logical_id:
                raise ValueError(
                    "lock manifest draft must reference same StoryCore identity"
                )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return story_core_logical_id(self.project_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="accepted_idea", source=self.idea_ref),
            SourceVersionBinding(role="approved_logline", source=self.logline_ref),
            SourceVersionBinding(role="accepted_premise", source=self.premise_ref),
            SourceVersionBinding(role="accepted_angle", source=self.angle_ref),
            SourceVersionBinding(role="theme_hypothesis", source=self.theme_ref),
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
            SourceVersionBinding(role=f"research_{index:03d}", source=ref)
            for index, ref in enumerate(self.research_refs)
        )
        if self.lock_manifest is not None:
            values.extend(
                (
                    SourceVersionBinding(
                        role="draft_story_core",
                        source=self.lock_manifest.draft_ref,
                    ),
                    SourceVersionBinding(
                        role="causal_validation_evidence",
                        source=self.lock_manifest.causal_validation_ref,
                    ),
                    SourceVersionBinding(
                        role="validated_story_graph",
                        source=self.lock_manifest.story_graph_ref,
                    ),
                )
            )
        return tuple(values)


class ConflictModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    version_id: VersionId
    story_core_draft_ref: VersionRef
    active_profile_ref: VersionRef
    theme_ref: VersionRef
    character_refs: tuple[VersionRef, ...] = ()
    relationship_refs: tuple[VersionRef, ...] = ()
    incompatible_objectives: tuple[str, ...] = Field(min_length=2)
    opposition_forces: tuple[str, ...] = Field(min_length=1)
    leverage_points: tuple[str, ...] = Field(min_length=1)
    escalation_steps: tuple[str, ...] = Field(min_length=1)
    produces_resistance: bool = True
    change_potential: bool = True

    @field_validator(
        "incompatible_objectives",
        "opposition_forces",
        "leverage_points",
        "escalation_steps",
    )
    @classmethod
    def normalize_text(cls, values: tuple[str, ...], info) -> tuple[str, ...]:
        return _unique_text(values, info.field_name)

    @field_validator("character_refs", "relationship_refs")
    @classmethod
    def normalize_refs(
        cls,
        values: tuple[VersionRef, ...],
    ) -> tuple[VersionRef, ...]:
        return _unique_refs(values)

    @model_validator(mode="after")
    def validate_refs(self) -> "ConflictModel":
        _require_project_logical_id(
            self.story_core_draft_ref,
            story_core_logical_id(self.project_id),
            "story_core_draft_ref",
        )
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("conflict profile must bind same project")
        _require_project_logical_id(
            self.theme_ref,
            LogicalId(f"story-theme:{self.project_id.root}"),
            "theme_ref",
        )
        for ref in self.character_refs:
            _require_prefix(ref, "character-model:", "character_refs")
        for ref in self.relationship_refs:
            _require_prefix(ref, "relationship:", "relationship_refs")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return conflict_logical_id(self.project_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(
                role="story_core_draft",
                source=self.story_core_draft_ref,
            ),
            SourceVersionBinding(role="theme_hypothesis", source=self.theme_ref),
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
            SourceVersionBinding(role=f"relationship_{index:03d}", source=ref)
            for index, ref in enumerate(self.relationship_refs)
        )
        return tuple(values)


class StakesModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    version_id: VersionId
    story_core_draft_ref: VersionRef
    conflict_ref: VersionRef
    active_profile_ref: VersionRef
    practical_stakes: tuple[str, ...] = ()
    relational_stakes: tuple[str, ...] = ()
    identity_stakes: tuple[str, ...] = ()
    irreversible_stakes: tuple[str, ...] = ()
    escalation_steps: tuple[str, ...] = Field(min_length=1)
    major_turn_consequences: tuple[str, ...] = Field(min_length=1)
    genre_scale_compatible: bool = True

    @field_validator(
        "practical_stakes",
        "relational_stakes",
        "identity_stakes",
        "irreversible_stakes",
        "escalation_steps",
        "major_turn_consequences",
    )
    @classmethod
    def normalize_text(cls, values: tuple[str, ...], info) -> tuple[str, ...]:
        return _unique_text(values, info.field_name)

    @model_validator(mode="after")
    def validate_refs(self) -> "StakesModel":
        _require_project_logical_id(
            self.story_core_draft_ref,
            story_core_logical_id(self.project_id),
            "story_core_draft_ref",
        )
        _require_project_logical_id(
            self.conflict_ref,
            conflict_logical_id(self.project_id),
            "conflict_ref",
        )
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("stakes profile must bind same project")
        if not (
            self.practical_stakes
            or self.relational_stakes
            or self.identity_stakes
            or self.irreversible_stakes
        ):
            raise ValueError("StakesModel requires at least one concrete stakes track")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return stakes_logical_id(self.project_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return (
            SourceVersionBinding(
                role="story_core_draft",
                source=self.story_core_draft_ref,
            ),
            SourceVersionBinding(role="conflict_model", source=self.conflict_ref),
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
        )


class StoryGraphNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    node_id: str
    kind: StoryGraphNodeKind
    summary: str
    major_change: bool = False
    root_cause: bool = False
    requires_consequence: bool = False
    causal_gap: bool = False

    @field_validator("node_id", "summary")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)


class StoryGraphEdge(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    edge_id: str
    source_node_id: str
    target_node_id: str
    kind: StoryGraphEdgeKind
    rationale: str

    @field_validator("edge_id", "source_node_id", "target_node_id", "rationale")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def reject_self_edge(self) -> "StoryGraphEdge":
        if self.source_node_id == self.target_node_id:
            raise ValueError("StoryGraph edge cannot self-reference")
        return self


class CausalStoryGraph(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    version_id: VersionId
    story_core_draft_ref: VersionRef
    conflict_ref: VersionRef
    stakes_ref: VersionRef
    active_profile_ref: VersionRef
    character_refs: tuple[VersionRef, ...] = ()
    research_refs: tuple[VersionRef, ...] = ()
    nodes: tuple[StoryGraphNode, ...] = Field(min_length=1)
    edges: tuple[StoryGraphEdge, ...] = ()

    @field_validator("character_refs", "research_refs")
    @classmethod
    def normalize_refs(
        cls,
        values: tuple[VersionRef, ...],
    ) -> tuple[VersionRef, ...]:
        return _unique_refs(values)

    @model_validator(mode="after")
    def validate_shape(self) -> "CausalStoryGraph":
        _require_project_logical_id(
            self.story_core_draft_ref,
            story_core_logical_id(self.project_id),
            "story_core_draft_ref",
        )
        _require_project_logical_id(
            self.conflict_ref,
            conflict_logical_id(self.project_id),
            "conflict_ref",
        )
        _require_project_logical_id(
            self.stakes_ref,
            stakes_logical_id(self.project_id),
            "stakes_ref",
        )
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("StoryGraph profile must bind same project")
        for ref in self.character_refs:
            _require_prefix(ref, "character-model:", "character_refs")
        for ref in self.research_refs:
            _require_project_research_ref(ref, self.project_id, "research_refs")

        node_ids = [node.node_id for node in self.nodes]
        if len(set(node_ids)) != len(node_ids):
            raise ValueError("StoryGraph node_id values must be unique")
        edge_ids = [edge.edge_id for edge in self.edges]
        if len(set(edge_ids)) != len(edge_ids):
            raise ValueError("StoryGraph edge_id values must be unique")
        known = set(node_ids)
        for edge in self.edges:
            if edge.source_node_id not in known or edge.target_node_id not in known:
                raise ValueError(
                    "StoryGraph edge endpoints must reference nodes in same graph"
                )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return story_graph_logical_id(self.project_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(
                role="story_core_draft",
                source=self.story_core_draft_ref,
            ),
            SourceVersionBinding(role="conflict_model", source=self.conflict_ref),
            SourceVersionBinding(role="stakes_model", source=self.stakes_ref),
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
            SourceVersionBinding(role=f"research_{index:03d}", source=ref)
            for index, ref in enumerate(self.research_refs)
        )
        return tuple(values)


class CausalFinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    severity: FindingSeverity
    message: str
    node_id: str | None = None
    blocking: bool = True

    @field_validator("code", "message")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("node_id")
    @classmethod
    def validate_node_id(cls, value: str | None) -> str | None:
        return None if value is None else _trimmed(value, "node_id")


class CausalValidationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    version_id: VersionId
    story_core_draft_ref: VersionRef
    story_graph_ref: VersionRef
    active_profile_ref: VersionRef
    verdict: GateVerdict
    findings: tuple[CausalFinding, ...] = ()

    @model_validator(mode="after")
    def validate_result(self) -> "CausalValidationEvidence":
        _require_project_logical_id(
            self.story_core_draft_ref,
            story_core_logical_id(self.project_id),
            "story_core_draft_ref",
        )
        _require_project_logical_id(
            self.story_graph_ref,
            story_graph_logical_id(self.project_id),
            "story_graph_ref",
        )
        if self.active_profile_ref.logical_id != _active_profile_id(self.project_id):
            raise ValueError("validation profile must bind same project")
        blockers = any(item.blocking for item in self.findings)
        if blockers and self.verdict is not GateVerdict.FAIL:
            raise ValueError("blocking causal findings require FAIL verdict")
        if not blockers and self.verdict is GateVerdict.FAIL:
            raise ValueError("FAIL causal verdict requires blocking finding")
        if self.verdict not in {GateVerdict.PASS, GateVerdict.FAIL}:
            raise ValueError("causal validation verdict must be PASS or FAIL")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return causal_validation_logical_id(self.project_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return (
            SourceVersionBinding(
                role="story_core_draft",
                source=self.story_core_draft_ref,
            ),
            SourceVersionBinding(
                role="causal_story_graph",
                source=self.story_graph_ref,
            ),
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
        )

    @property
    def passed(self) -> bool:
        return self.verdict is GateVerdict.PASS


StoryCoreDomainValue: TypeAlias = (
    StoryCoreVersion | ConflictModel | StakesModel | CausalStoryGraph | CausalValidationEvidence
)


class StoryCoreArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: StoryCoreDomainValue

    @model_validator(mode="after")
    def validate_identity(self) -> "StoryCoreArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("story-core artifact logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("story-core artifact version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError(
                "story-core provenance must exactly bind declared canonical inputs"
            )
        if self.metadata.provenance.rule_version != self.value.active_profile_ref:
            raise ValueError(
                "story-core provenance rule_version must pin ActiveProductionProfile"
            )
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


def build_story_core_provenance(
    value: StoryCoreDomainValue,
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


class CausalStoryGraphEvaluator:
    """Deterministic causal gate. Ordering alone never satisfies causality."""

    def evaluate(
        self,
        graph: CausalStoryGraph,
        *,
        version_id: VersionId,
    ) -> CausalValidationEvidence:
        findings: list[CausalFinding] = []
        incoming: dict[str, list[StoryGraphEdge]] = {
            node.node_id: [] for node in graph.nodes
        }
        outgoing: dict[str, list[StoryGraphEdge]] = {
            node.node_id: [] for node in graph.nodes
        }
        for edge in graph.edges:
            incoming[edge.target_node_id].append(edge)
            outgoing[edge.source_node_id].append(edge)

        def block(code: str, message: str, node_id: str | None = None) -> None:
            findings.append(
                CausalFinding(
                    code=code,
                    severity=FindingSeverity.BLOCKER,
                    message=message,
                    node_id=node_id,
                    blocking=True,
                )
            )

        for node in graph.nodes:
            if node.causal_gap:
                block(
                    "STORY_GRAPH_CAUSAL_GAP",
                    "node declares an unresolved causal gap",
                    node.node_id,
                )
            if not node.root_cause and not incoming[node.node_id]:
                block(
                    "STORY_GRAPH_ORPHAN_CAUSE",
                    "non-root story node has no causal predecessor",
                    node.node_id,
                )
            if (
                node.major_change
                and not node.root_cause
                and not incoming[node.node_id]
            ):
                block(
                    "STORY_GRAPH_MAJOR_CHANGE_WITHOUT_CAUSE",
                    "major change must answer because of what prior event/decision",
                    node.node_id,
                )
            if node.requires_consequence and not outgoing[node.node_id]:
                block(
                    "STORY_GRAPH_MISSING_CONSEQUENCE",
                    "node requires a causal consequence but has no outgoing edge",
                    node.node_id,
                )

        if self._has_cycle(graph):
            block(
                "STORY_GRAPH_ILLEGAL_CYCLE",
                "causal graph contains a directed cycle",
            )

        return CausalValidationEvidence(
            project_id=graph.project_id,
            version_id=version_id,
            story_core_draft_ref=graph.story_core_draft_ref,
            story_graph_ref=graph.ref,
            active_profile_ref=graph.active_profile_ref,
            verdict=GateVerdict.FAIL if findings else GateVerdict.PASS,
            findings=tuple(findings),
        )

    @staticmethod
    def _has_cycle(graph: CausalStoryGraph) -> bool:
        adjacency: dict[str, list[str]] = {
            node.node_id: [] for node in graph.nodes
        }
        indegree: dict[str, int] = {node.node_id: 0 for node in graph.nodes}
        for edge in graph.edges:
            adjacency[edge.source_node_id].append(edge.target_node_id)
            indegree[edge.target_node_id] += 1

        queue = [node_id for node_id, degree in indegree.items() if degree == 0]
        visited = 0
        while queue:
            current = queue.pop()
            visited += 1
            for target in adjacency[current]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)
        return visited != len(graph.nodes)


class StoryCoreRepository:
    """IMP-023 immutable repository, dependency graph, gates and lock transition."""

    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, self.graph)
        self.causal_gate = CausalStoryGraphEvaluator()

    async def create_story_core_draft(
        self,
        *,
        value: StoryCoreVersion,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryCoreArtifact:
        if value.phase is not StoryCorePhase.DRAFT:
            raise StoryCoreIdentityError(
                "initial StoryCore version must be DRAFT"
            )
        await self._assert_story_core_draft_inputs(value)
        return await self._create_initial(value, provenance, created_at)

    async def revise_story_core_draft(
        self,
        *,
        value: StoryCoreVersion,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[StoryCoreArtifact, tuple[InvalidationRecord, ...]]:
        if value.phase is not StoryCorePhase.DRAFT:
            raise StoryCoreIdentityError("StoryCore revision must create DRAFT")
        if predecessor.logical_id != value.logical_id:
            raise StoryCoreIdentityError(
                "StoryCore revision must preserve story_core_id"
            )
        previous = await self.get_story_core(predecessor)
        if previous is None:
            raise StoryCoreIdentityError("StoryCore predecessor not found")
        await self._assert_story_core_draft_inputs(value)
        artifact = await self._create_successor(
            value,
            predecessor,
            provenance,
            created_at,
        )
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.DRAFT,
            expected_revision=expected_revision,
        )

        invalidation_source = predecessor
        if (
            previous.value.phase is StoryCorePhase.FROZEN_FOR_STRUCTURE
            and previous.value.lock_manifest is not None
        ):
            invalidation_source = previous.value.lock_manifest.draft_ref

        records = await self.invalidations.create_for_change(
            cause="StoryCore semantic revision",
            source_old=invalidation_source,
            source_new=artifact.ref,
            provenance=provenance,
            scope="story_core_descendants",
            repair_or_recompute_requirement=(
                "Recompute causal StoryGraph/validation and dependency-reachable "
                "structural descendants from the new StoryCore DRAFT."
            ),
        )
        return artifact, tuple(records)

    async def create_conflict(
        self,
        *,
        value: ConflictModel,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryCoreArtifact:
        await self._assert_conflict_inputs(value)
        artifact = await self._create_initial(value, provenance, created_at)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )
        return artifact

    async def revise_conflict(
        self,
        *,
        value: ConflictModel,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[StoryCoreArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise StoryCoreIdentityError("ConflictModel revision must preserve identity")
        await self._assert_conflict_inputs(value)
        artifact = await self._create_successor(
            value,
            predecessor,
            provenance,
            created_at,
        )
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )
        records = await self.invalidations.create_for_change(
            cause="ConflictModel semantic revision",
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope="conflict_descendants",
            repair_or_recompute_requirement=(
                "Recompute dependency-reachable Stakes/StoryGraph/validation outputs."
            ),
        )
        return artifact, tuple(records)

    async def create_stakes(
        self,
        *,
        value: StakesModel,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryCoreArtifact:
        await self._assert_stakes_inputs(value)
        artifact = await self._create_initial(value, provenance, created_at)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )
        return artifact

    async def revise_stakes(
        self,
        *,
        value: StakesModel,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[StoryCoreArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise StoryCoreIdentityError("StakesModel revision must preserve identity")
        await self._assert_stakes_inputs(value)
        artifact = await self._create_successor(
            value,
            predecessor,
            provenance,
            created_at,
        )
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )
        records = await self.invalidations.create_for_change(
            cause="StakesModel semantic revision",
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope="stakes_descendants",
            repair_or_recompute_requirement=(
                "Recompute dependency-reachable StoryGraph/validation outputs."
            ),
        )
        return artifact, tuple(records)

    async def create_story_graph(
        self,
        *,
        value: CausalStoryGraph,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryCoreArtifact:
        await self._assert_graph_inputs(value)
        return await self._create_initial(value, provenance, created_at)

    async def revise_story_graph(
        self,
        *,
        value: CausalStoryGraph,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[StoryCoreArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise StoryCoreIdentityError("StoryGraph revision must preserve identity")
        await self._assert_graph_inputs(value)
        artifact = await self._create_successor(
            value,
            predecessor,
            provenance,
            created_at,
        )
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.DRAFT,
            expected_revision=expected_revision,
        )
        records = await self.invalidations.create_for_change(
            cause="CausalStoryGraph semantic revision",
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope="story_graph_descendants",
            repair_or_recompute_requirement=(
                "Re-run causal validation for the revised exact StoryGraph."
            ),
        )
        return artifact, tuple(records)

    async def validate_story_graph(
        self,
        *,
        graph_ref: VersionRef,
        validation_version_id: VersionId,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryCoreArtifact:
        graph_artifact = await self.get_story_graph(graph_ref)
        if graph_artifact is None:
            raise StoryCoreGateBlocked("StoryGraph exact version not found")
        graph = graph_artifact.value
        await self._assert_current(
            graph.ref,
            "StoryGraph",
            {LifecycleState.DRAFT, LifecycleState.APPROVED},
        )
        await self._assert_graph_inputs(graph)

        evidence = self.causal_gate.evaluate(
            graph,
            version_id=validation_version_id,
        )
        if provenance.source_versions != evidence.source_bindings():
            raise StoryCoreIdentityError(
                "causal-validation provenance does not match evaluated graph"
            )
        validation_pointer = await self.versions.get_current(evidence.logical_id)
        if validation_pointer is None:
            artifact = await self._create_initial(evidence, provenance, created_at)
            validation_expected_revision = 0
        else:
            predecessor = VersionRef(
                logical_id=evidence.logical_id,
                version_id=validation_pointer.version_id,
            )
            artifact = await self._create_successor(
                evidence,
                predecessor,
                provenance,
                created_at,
            )
            validation_expected_revision = validation_pointer.revision
            await self.versions.update_current(
                logical_id=evidence.logical_id,
                version_id=evidence.version_id,
                status=LifecycleState.DRAFT,
                expected_revision=validation_expected_revision,
            )
            validation_pointer = await self.versions.get_current(evidence.logical_id)
            assert validation_pointer is not None
            validation_expected_revision = validation_pointer.revision

        if evidence.passed:
            graph_pointer = await self.versions.get_current(graph.logical_id)
            if graph_pointer is None or graph_pointer.version_id != graph.version_id:
                raise StoryCoreGateBlocked(
                    "StoryGraph is not exact current version during validation"
                )
            await self.versions.update_current(
                logical_id=graph.logical_id,
                version_id=graph.version_id,
                status=LifecycleState.APPROVED,
                expected_revision=graph_pointer.revision,
            )
            await self.versions.update_current(
                logical_id=evidence.logical_id,
                version_id=evidence.version_id,
                status=LifecycleState.APPROVED,
                expected_revision=validation_expected_revision,
            )
        return artifact

    async def lock_story_core(
        self,
        *,
        draft_ref: VersionRef,
        graph_ref: VersionRef,
        validation_ref: VersionRef,
        frozen_version_id: VersionId,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> StoryCoreArtifact:
        draft_artifact = await self.get_story_core(draft_ref)
        graph_artifact = await self.get_story_graph(graph_ref)
        validation_artifact = await self.get_validation(validation_ref)
        if draft_artifact is None:
            raise StoryCoreGateBlocked("StoryCore DRAFT exact version not found")
        if graph_artifact is None:
            raise StoryCoreGateBlocked("StoryGraph exact version not found")
        if validation_artifact is None:
            raise StoryCoreGateBlocked("causal validation exact version not found")

        draft = draft_artifact.value
        graph = graph_artifact.value
        validation = validation_artifact.value
        if draft.phase is not StoryCorePhase.DRAFT:
            raise StoryCoreGateBlocked("lock input must be StoryCore DRAFT")
        await self._assert_current(
            draft.ref,
            "StoryCore DRAFT",
            {LifecycleState.DRAFT},
        )
        if graph.story_core_draft_ref != draft.ref:
            raise StoryCoreGateBlocked(
                "StoryGraph does not reference exact StoryCore DRAFT"
            )
        if validation.story_core_draft_ref != draft.ref:
            raise StoryCoreGateBlocked(
                "causal validation does not match exact StoryCore DRAFT"
            )
        if validation.story_graph_ref != graph.ref:
            raise StoryCoreGateBlocked(
                "causal validation does not match exact StoryGraph"
            )
        if not validation.passed or any(item.blocking for item in validation.findings):
            raise StoryCoreGateBlocked(
                "StoryCore lock blocked by unresolved causal defect"
            )
        if not draft.canonical_hard_constraints_satisfied:
            raise StoryCoreGateBlocked(
                "StoryCore lock blocked by canonical hard constraint"
            )
        if not draft.factuality_compatible:
            raise StoryCoreGateBlocked(
                "StoryCore lock blocked by factuality constraint"
            )
        await self._assert_current(
            graph.ref,
            "StoryGraph",
            {LifecycleState.APPROVED},
        )
        await self._assert_current(
            validation.ref,
            "causal validation",
            {LifecycleState.APPROVED},
        )

        frozen = draft.model_copy(
            update={
                "version_id": frozen_version_id,
                "phase": StoryCorePhase.FROZEN_FOR_STRUCTURE,
                "lock_manifest": StoryCoreLockManifest(
                    draft_ref=draft.ref,
                    story_graph_ref=graph.ref,
                    causal_validation_ref=validation.ref,
                    locked_at=created_at,
                ),
            }
        )
        if provenance.source_versions != frozen.source_bindings():
            raise StoryCoreIdentityError(
                "lock provenance must bind exact draft/graph/validation and "
                "carried StoryCore sources"
            )
        artifact = await self._create_successor(
            frozen,
            draft.ref,
            provenance,
            created_at,
        )
        await self.versions.update_current(
            logical_id=frozen.logical_id,
            version_id=frozen.version_id,
            status=LifecycleState.LOCKED,
            expected_revision=expected_revision,
        )
        return artifact

    async def get_story_core(
        self,
        ref: VersionRef,
    ) -> StoryCoreArtifact | None:
        return await self._get_typed(ref, StoryCoreVersion, "story-core:")

    async def get_conflict(
        self,
        ref: VersionRef,
    ) -> StoryCoreArtifact | None:
        return await self._get_typed(ref, ConflictModel, "conflict:")

    async def get_stakes(
        self,
        ref: VersionRef,
    ) -> StoryCoreArtifact | None:
        return await self._get_typed(ref, StakesModel, "stakes:")

    async def get_story_graph(
        self,
        ref: VersionRef,
    ) -> StoryCoreArtifact | None:
        return await self._get_typed(ref, CausalStoryGraph, "story-graph:")

    async def get_validation(
        self,
        ref: VersionRef,
    ) -> StoryCoreArtifact | None:
        return await self._get_typed(
            ref,
            CausalValidationEvidence,
            "story-graph-validation:",
        )

    async def get_current_story_core(
        self,
        project_id: LogicalId,
    ) -> StoryCoreArtifact | None:
        logical_id = story_core_logical_id(project_id)
        pointer = await self.versions.get_current(logical_id)
        if pointer is None:
            return None
        return await self.get_story_core(
            VersionRef(logical_id=logical_id, version_id=pointer.version_id)
        )

    async def _create_initial(
        self,
        value: StoryCoreDomainValue,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryCoreArtifact:
        self._assert_provenance(value, provenance)
        artifact = self._artifact(value, provenance, created_at, None)
        stored = await self.versions.create_initial(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        materialized = StoryCoreArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(materialized)
        return materialized

    async def _create_successor(
        self,
        value: StoryCoreDomainValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryCoreArtifact:
        if predecessor.logical_id != value.logical_id:
            raise StoryCoreIdentityError(
                "successor must preserve canonical logical identity"
            )
        self._assert_provenance(value, provenance)
        artifact = self._artifact(value, provenance, created_at, predecessor)
        stored = await self.versions.create_successor(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        materialized = StoryCoreArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(materialized)
        return materialized

    async def _get_typed(self, ref, model, prefix) -> StoryCoreArtifact | None:
        if not ref.logical_id.root.startswith(prefix):
            raise StoryCoreIdentityError(
                f"expected {prefix.rstrip(':')} artifact, got {ref.logical_id.root}"
            )
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = model.model_validate(stored.payload)
        return StoryCoreArtifact(metadata=stored.metadata, value=value)

    async def _register_dependencies(self, artifact: StoryCoreArtifact) -> None:
        grouped: dict[tuple[str, str], list[str]] = {}
        refs: dict[tuple[str, str], VersionRef] = {}
        for binding in artifact.value.source_bindings():
            if binding.source == artifact.ref:
                continue
            key = (
                binding.source.logical_id.root,
                binding.source.version_id.root,
            )
            refs[key] = binding.source
            grouped.setdefault(key, []).append(binding.role)

        for key in sorted(grouped):
            await self.graph.create_edge(
                source=refs[key],
                dependent=artifact.ref,
                edge_type="story_core_input",
                dependency_reason=" + ".join(sorted(set(grouped[key]))),
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _assert_story_core_draft_inputs(
        self,
        value: StoryCoreVersion,
    ) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        for ref, label in (
            (value.idea_ref, "Idea"),
            (value.logline_ref, "Logline"),
            (value.premise_ref, "Premise"),
            (value.angle_ref, "Angle"),
            (value.theme_ref, "Theme"),
        ):
            await self._assert_current(
                ref,
                label,
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
        for ref in value.research_refs:
            await self._assert_current(
                ref,
                "Research/StoryMaterial",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
        # IMP-022 permits a pre-StoryCore CharacterModelVersion to remain DRAFT.
        # Conflict/StoryGraph later require accepted successors bound to this draft.
        for ref in value.character_refs:
            await self._assert_current(
                ref,
                "pre-core CharacterModelVersion",
                {
                    LifecycleState.DRAFT,
                    LifecycleState.REVIEW,
                    LifecycleState.APPROVED,
                    LifecycleState.LOCKED,
                },
            )

    async def _assert_conflict_inputs(self, value: ConflictModel) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.story_core_draft_ref,
            "StoryCore DRAFT",
            {LifecycleState.DRAFT},
        )
        core = await self.get_story_core(value.story_core_draft_ref)
        if core is None or core.value.phase is not StoryCorePhase.DRAFT:
            raise StoryCoreGateBlocked("ConflictModel requires StoryCore DRAFT")
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.theme_ref,
            "Theme",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        for ref in value.character_refs:
            await self._assert_character_model_for_core(
                ref,
                project_id=value.project_id,
                story_core_ref=value.story_core_draft_ref,
                label="ConflictModel CharacterModelVersion",
            )
        for ref in value.relationship_refs:
            await self._assert_relationship_for_project(
                ref,
                project_id=value.project_id,
                label="ConflictModel RelationshipState",
            )
        if not value.produces_resistance:
            raise StoryCoreGateBlocked("ConflictModel must produce resistance")
        if not value.change_potential:
            raise StoryCoreGateBlocked(
                "ConflictModel must produce change potential"
            )

    async def _assert_stakes_inputs(self, value: StakesModel) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.story_core_draft_ref,
            "StoryCore DRAFT",
            {LifecycleState.DRAFT},
        )
        await self._assert_current(
            value.conflict_ref,
            "ConflictModel",
            {LifecycleState.APPROVED},
        )
        conflict = await self.get_conflict(value.conflict_ref)
        if (
            conflict is None
            or conflict.value.story_core_draft_ref != value.story_core_draft_ref
        ):
            raise StoryCoreGateBlocked(
                "StakesModel ConflictModel must bind the same exact StoryCore DRAFT"
            )
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        if not value.genre_scale_compatible:
            raise StoryCoreGateBlocked(
                "StakesModel escalation is incompatible with genre/scale"
            )

    async def _assert_graph_inputs(self, value: CausalStoryGraph) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.story_core_draft_ref,
            "StoryCore DRAFT",
            {LifecycleState.DRAFT},
        )
        core = await self.get_story_core(value.story_core_draft_ref)
        if core is None or core.value.phase is not StoryCorePhase.DRAFT:
            raise StoryCoreGateBlocked(
                "StoryGraph MUST consume StoryCore DRAFT, never locked StoryCore"
            )
        await self._assert_current(
            value.conflict_ref,
            "ConflictModel",
            {LifecycleState.APPROVED},
        )
        await self._assert_current(
            value.stakes_ref,
            "StakesModel",
            {LifecycleState.APPROVED},
        )
        conflict = await self.get_conflict(value.conflict_ref)
        stakes = await self.get_stakes(value.stakes_ref)
        if (
            conflict is None
            or conflict.value.story_core_draft_ref != value.story_core_draft_ref
        ):
            raise StoryCoreGateBlocked(
                "StoryGraph ConflictModel must bind the same exact StoryCore DRAFT"
            )
        if (
            stakes is None
            or stakes.value.story_core_draft_ref != value.story_core_draft_ref
            or stakes.value.conflict_ref != value.conflict_ref
        ):
            raise StoryCoreGateBlocked(
                "StoryGraph StakesModel must bind the same exact StoryCore DRAFT "
                "and ConflictModel"
            )
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        for ref in value.character_refs:
            await self._assert_character_model_for_core(
                ref,
                project_id=value.project_id,
                story_core_ref=value.story_core_draft_ref,
                label="StoryGraph CharacterModelVersion",
            )
        for ref in value.research_refs:
            await self._assert_current(
                ref,
                "StoryGraph Research/StoryMaterial",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )

    async def _assert_character_model_for_core(
        self,
        ref: VersionRef,
        *,
        project_id: LogicalId,
        story_core_ref: VersionRef,
        label: str,
    ) -> None:
        await self._assert_current(
            ref,
            label,
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise StoryCoreGateBlocked(f"{label} exact version not found")
        try:
            character = CharacterModelVersion.model_validate(stored.payload)
        except ValidationError as exc:
            raise StoryCoreGateBlocked(
                f"{label} payload is not canonical CharacterModelVersion"
            ) from exc
        if character.project_id != project_id:
            raise StoryCoreGateBlocked(f"{label} belongs to a different project")
        if character.story_core_ref != story_core_ref:
            raise StoryCoreGateBlocked(
                f"{label} must bind the same exact StoryCore DRAFT"
            )

    async def _assert_relationship_for_project(
        self,
        ref: VersionRef,
        *,
        project_id: LogicalId,
        label: str,
    ) -> None:
        await self._assert_current(
            ref,
            label,
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise StoryCoreGateBlocked(f"{label} exact version not found")
        try:
            relationship = RelationshipState.model_validate(stored.payload)
        except ValidationError as exc:
            raise StoryCoreGateBlocked(
                f"{label} payload is not canonical RelationshipState"
            ) from exc
        if relationship.project_id != project_id:
            raise StoryCoreGateBlocked(f"{label} belongs to a different project")

    async def _assert_all_sources_exist(self, value: StoryCoreDomainValue) -> None:
        for binding in value.source_bindings():
            if await self.versions.get_version(binding.source) is None:
                raise StoryCoreGateBlocked(
                    f"missing exact source {binding.role}="
                    f"{binding.source.logical_id.root}/"
                    f"{binding.source.version_id.root}"
                )

    async def _assert_current(
        self,
        ref: VersionRef,
        label: str,
        allowed: set[LifecycleState],
    ) -> CurrentVersionPointer:
        pointer = await self.versions.get_current(ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != ref.version_id
            or pointer.status not in allowed
        ):
            raise StoryCoreGateBlocked(
                f"{label} is not exact current accepted version"
            )
        return pointer

    @staticmethod
    def _assert_provenance(
        value: StoryCoreDomainValue,
        provenance: Provenance,
    ) -> None:
        if provenance.source_versions != value.source_bindings():
            raise StoryCoreIdentityError(
                "provenance must exactly match declared source bindings"
            )
        if provenance.rule_version != value.active_profile_ref:
            raise StoryCoreIdentityError(
                "provenance rule_version must pin ActiveProductionProfile"
            )

    @staticmethod
    def _artifact(
        value: StoryCoreDomainValue,
        provenance: Provenance,
        created_at: datetime,
        predecessor: VersionRef | None,
    ) -> StoryCoreArtifact:
        return StoryCoreArtifact(
            metadata=SemanticRecordMetadata(
                logical_id=value.logical_id,
                version_id=value.version_id,
                predecessor=predecessor,
                provenance=provenance,
                created_at=created_at,
            ),
            value=value,
        )
