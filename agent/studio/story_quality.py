"""Independent story critique, repair, quality gate and script lock for IMP-027.

Authority boundaries:
- critique/root-cause/quality are immutable evidence for exact evaluated versions;
- repair plans describe targeted change scope and preserve obligations but do not
  mutate accepted narrative truth;
- ScriptLockManifest is the explicit lock boundary and never rewrites upstream
  StoryCore or screenplay payloads;
- provider/prompt/runtime state is never canonical authority here.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

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
from .screenplay_realization import FullScreenplay
from .story_core import StoryCorePhase, StoryCoreVersion, story_core_logical_id
from .versioning import CurrentPointerNotFound, CurrentVersionPointer, VersionRepository


class StoryQualityError(ValueError):
    """Base error for IMP-027 critique/repair/quality/lock boundaries."""


class StoryQualityGateBlocked(StoryQualityError):
    """Raised when exact-version or hard-gate preconditions fail closed."""


class StoryQualityIdentityError(StoryQualityError):
    """Raised when identity/provenance crosses canonical ownership."""


class CritiqueKind(str, Enum):
    SUBJECTIVE_DISAGREEMENT = "SUBJECTIVE_DISAGREEMENT"
    FACTUAL_CONTRADICTION = "FACTUAL_CONTRADICTION"
    CAUSALITY_BREAK = "CAUSALITY_BREAK"
    IDENTITY_STATE_CONTRADICTION = "IDENTITY_STATE_CONTRADICTION"
    MISSING_CRITICAL_PAYOFF = "MISSING_CRITICAL_PAYOFF"
    STRUCTURAL_WEAKNESS = "STRUCTURAL_WEAKNESS"
    CHARACTER = "CHARACTER"
    DIALOGUE = "DIALOGUE"
    CONTINUITY = "CONTINUITY"
    RHYTHM = "RHYTHM"


class FindingDisposition(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class ResponsibleLayer(str, Enum):
    RESEARCH = "RESEARCH"
    STORY_CORE = "STORY_CORE"
    STORY_GRAPH = "STORY_GRAPH"
    CHARACTER_MODEL = "CHARACTER_MODEL"
    CHARACTER_STATE = "CHARACTER_STATE"
    STRUCTURE = "STRUCTURE"
    MACRO_STORY_BEAT = "MACRO_STORY_BEAT"
    SEQUENCE = "SEQUENCE"
    SCENE = "SCENE"
    SCENE_DRAMATIC_BEAT = "SCENE_DRAMATIC_BEAT"
    DIALOGUE_INTENT = "DIALOGUE_INTENT"
    SETUP_PAYOFF = "SETUP_PAYOFF"
    SCREENPLAY_SCENE = "SCREENPLAY_SCENE"
    FULL_SCREENPLAY = "FULL_SCREENPLAY"


class RepairMode(str, Enum):
    LINE_EXCHANGE = "LINE_EXCHANGE"
    SCENE_DRAMATIC_BEAT = "SCENE_DRAMATIC_BEAT"
    SCENE = "SCENE"
    SEQUENCE = "SEQUENCE"
    CHARACTER_MODEL = "CHARACTER_MODEL"
    RESEARCH_PACKAGE = "RESEARCH_PACKAGE"
    STRUCTURE = "STRUCTURE"
    PREMISE_ANGLE = "PREMISE_ANGLE"


class QualityHardGate(str, Enum):
    FACTUAL_CONTRADICTION = "FACTUAL_CONTRADICTION"
    CAUSALITY_BREAK = "CAUSALITY_BREAK"
    IDENTITY_STATE_CONTRADICTION = "IDENTITY_STATE_CONTRADICTION"
    MISSING_CRITICAL_PAYOFF = "MISSING_CRITICAL_PAYOFF"


class ScriptApprovalPolicy(str, Enum):
    AUTOMATED_PASS_ALLOWED = "AUTOMATED_PASS_ALLOWED"
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"


_HARD_CRITIQUE_KINDS = {
    CritiqueKind.FACTUAL_CONTRADICTION,
    CritiqueKind.CAUSALITY_BREAK,
    CritiqueKind.IDENTITY_STATE_CONTRADICTION,
    CritiqueKind.MISSING_CRITICAL_PAYOFF,
}


_RESPONSIBLE_LAYER_PREFIXES = {
    ResponsibleLayer.RESEARCH: ("story-material:", "research-story-material:"),
    ResponsibleLayer.STORY_CORE: ("story-core:",),
    ResponsibleLayer.STORY_GRAPH: ("story-graph:",),
    ResponsibleLayer.CHARACTER_MODEL: ("character-model:",),
    ResponsibleLayer.CHARACTER_STATE: ("character-knowledge:", "relationship:"),
    ResponsibleLayer.STRUCTURE: (
        "structure-profile:",
        "duration-budget:",
        "macro-beat-sheet:",
        "scene-budget:",
        "scene-list-manifest:",
        "scene-breakdown-manifest:",
    ),
    ResponsibleLayer.MACRO_STORY_BEAT: ("macro-story-beat:",),
    ResponsibleLayer.SEQUENCE: ("sequence:",),
    ResponsibleLayer.SCENE: ("scene:",),
    ResponsibleLayer.SCENE_DRAMATIC_BEAT: ("scene-dramatic-beat:",),
    ResponsibleLayer.DIALOGUE_INTENT: ("dialogue-intent:",),
    ResponsibleLayer.SETUP_PAYOFF: ("setup-payoff-link:",),
    ResponsibleLayer.SCREENPLAY_SCENE: ("screenplay-scene:",),
    ResponsibleLayer.FULL_SCREENPLAY: ("screenplay:",),
}


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _key(value: str, label: str) -> str:
    value = _trimmed(value, label)
    if ":" in value:
        raise ValueError(f"{label} must not contain ':'")
    return value


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return (ref.logical_id.root, ref.version_id.root)


def _reachability_keys(items) -> set[tuple[str, str]]:
    return {(item.object_id.root, item.version_id.root) for item in items}


def _active_profile_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"active-profile:{project_id.root}")


def _is_project_scoped(
    ref: VersionRef,
    *,
    prefix: str,
    project_id: LogicalId,
) -> bool:
    base = f"{prefix}{project_id.root}"
    root = ref.logical_id.root
    return root == base or root.startswith(base + ":")


def _require_project_scoped(
    ref: VersionRef,
    *,
    prefix: str,
    project_id: LogicalId,
    label: str,
) -> None:
    if not _is_project_scoped(ref, prefix=prefix, project_id=project_id):
        raise ValueError(f"{label} must belong to the same project")


def _require_exact_ref(ref: VersionRef, expected: LogicalId, label: str) -> None:
    if ref.logical_id != expected:
        raise ValueError(f"{label} must reference canonical object for same project")


def critique_finding_logical_id(project_id: LogicalId, finding_key: str) -> LogicalId:
    return LogicalId(f"critique-finding:{project_id.root}:{_key(finding_key, 'finding_key')}")


def root_cause_logical_id(project_id: LogicalId, finding_key: str) -> LogicalId:
    return LogicalId(f"root-cause:{project_id.root}:{_key(finding_key, 'finding_key')}")


def story_repair_plan_logical_id(project_id: LogicalId, repair_key: str) -> LogicalId:
    return LogicalId(f"story-repair-plan:{project_id.root}:{_key(repair_key, 'repair_key')}")


def story_quality_result_logical_id(project_id: LogicalId, quality_key: str) -> LogicalId:
    return LogicalId(f"story-quality:{project_id.root}:{_key(quality_key, 'quality_key')}")


def script_lock_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"script-lock:{project_id.root}")


def locked_refs_digest(refs: tuple[VersionRef, ...]) -> str:
    canonical = "\n".join(
        f"{ref.logical_id.root}@{ref.version_id.root}" for ref in refs
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class CritiqueFinding(BaseModel):
    """Independent evidence-linked critique for exact story/screenplay versions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    finding_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    story_core_ref: VersionRef
    full_screenplay_ref: VersionRef
    location_ref: VersionRef
    evidence_refs: tuple[VersionRef, ...] = Field(min_length=1)
    critic_role: str
    generator_role: str
    kind: CritiqueKind
    severity: FindingSeverity
    disposition: FindingDisposition = FindingDisposition.OPEN
    summary: str
    rationale: str
    resolution_ref: VersionRef | None = None
    dismissal_reason: str | None = None

    @field_validator("finding_key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        return _key(value, "finding_key")

    @field_validator("critic_role", "generator_role", "summary", "rationale")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("dismissal_reason")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        return None if value is None else _trimmed(value, "dismissal_reason")

    @field_validator("evidence_refs")
    @classmethod
    def unique_evidence(
        cls,
        values: tuple[VersionRef, ...],
    ) -> tuple[VersionRef, ...]:
        if len({_ref_key(ref) for ref in values}) != len(values):
            raise ValueError("evidence_refs must be unique")
        return values

    @model_validator(mode="after")
    def validate_finding(self) -> "CritiqueFinding":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.story_core_ref,
            story_core_logical_id(self.project_id),
            "story_core_ref",
        )
        _require_project_scoped(
            self.full_screenplay_ref,
            prefix="screenplay:",
            project_id=self.project_id,
            label="full_screenplay_ref",
        )
        if self.critic_role == self.generator_role:
            raise ValueError("critic_role must be isolated from generator_role")
        if (
            self.kind is CritiqueKind.SUBJECTIVE_DISAGREEMENT
            and self.severity is FindingSeverity.BLOCKER
        ):
            raise ValueError(
                "subjective disagreement cannot automatically be BLOCKER"
            )
        if self.kind in _HARD_CRITIQUE_KINDS and self.severity is not FindingSeverity.BLOCKER:
            raise ValueError("hard-gate critique kinds must be BLOCKER severity")
        if self.disposition is FindingDisposition.OPEN:
            if self.resolution_ref is not None or self.dismissal_reason is not None:
                raise ValueError("OPEN finding cannot carry resolution/dismissal")
        elif self.disposition is FindingDisposition.RESOLVED:
            if self.resolution_ref is None:
                raise ValueError("RESOLVED finding requires resolution_ref")
            _require_project_scoped(
                self.resolution_ref,
                prefix="story-repair-plan:",
                project_id=self.project_id,
                label="resolution_ref",
            )
            if self.dismissal_reason is not None:
                raise ValueError("RESOLVED finding cannot carry dismissal_reason")
        else:
            if self.severity is FindingSeverity.BLOCKER:
                raise ValueError("BLOCKER finding cannot be dismissed")
            if self.dismissal_reason is None:
                raise ValueError("DISMISSED finding requires dismissal_reason")
            if self.resolution_ref is not None:
                raise ValueError("DISMISSED finding cannot carry resolution_ref")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return critique_finding_logical_id(self.project_id, self.finding_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="story_core", source=self.story_core_ref),
            SourceVersionBinding(role="full_screenplay", source=self.full_screenplay_ref),
            SourceVersionBinding(role="visible_location", source=self.location_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"evidence_{index:03d}", source=ref)
            for index, ref in enumerate(self.evidence_refs)
        )
        if self.resolution_ref is not None:
            values.append(SourceVersionBinding(role="resolution", source=self.resolution_ref))
        return tuple(values)


class RootCauseLocalization(BaseModel):
    """Diagnostic evidence mapping a visible defect to responsible exact source."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    finding_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    finding_ref: VersionRef
    visible_location_ref: VersionRef
    responsible_artifact_ref: VersionRef
    responsible_layer: ResponsibleLayer
    preserve_refs: tuple[VersionRef, ...] = ()
    invalidation_scope_candidate_refs: tuple[VersionRef, ...] = ()
    diagnosis: str

    @field_validator("finding_key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        return _key(value, "finding_key")

    @field_validator("diagnosis")
    @classmethod
    def validate_diagnosis(cls, value: str) -> str:
        return _trimmed(value, "diagnosis")

    @model_validator(mode="after")
    def validate_localization(self) -> "RootCauseLocalization":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.finding_ref,
            critique_finding_logical_id(self.project_id, self.finding_key),
            "finding_ref",
        )
        allowed_prefixes = _RESPONSIBLE_LAYER_PREFIXES[self.responsible_layer]
        if not any(
            _is_project_scoped(
                self.responsible_artifact_ref,
                prefix=prefix,
                project_id=self.project_id,
            )
            for prefix in allowed_prefixes
        ):
            raise ValueError(
                "responsible_layer must match responsible_artifact_ref authority "
                "for the same project"
            )
        preserve = {_ref_key(ref) for ref in self.preserve_refs}
        invalidation = {
            _ref_key(ref) for ref in self.invalidation_scope_candidate_refs
        }
        if preserve & invalidation:
            raise ValueError(
                "preserve_refs cannot overlap invalidation_scope_candidate_refs"
            )
        if len(preserve) != len(self.preserve_refs):
            raise ValueError("preserve_refs must be unique")
        if len(invalidation) != len(self.invalidation_scope_candidate_refs):
            raise ValueError("invalidation_scope_candidate_refs must be unique")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return root_cause_logical_id(self.project_id, self.finding_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="critique_finding", source=self.finding_ref),
            SourceVersionBinding(role="visible_location", source=self.visible_location_ref),
            SourceVersionBinding(role="responsible_artifact", source=self.responsible_artifact_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"preserve_{index:03d}", source=ref)
            for index, ref in enumerate(self.preserve_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"invalidation_candidate_{index:03d}", source=ref)
            for index, ref in enumerate(self.invalidation_scope_candidate_refs)
        )
        return tuple(values)


class StoryRepairPlan(BaseModel):
    """Targeted repair scope with explicit preserve/regression obligations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    repair_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    root_cause_ref: VersionRef
    mode: RepairMode
    target_refs: tuple[VersionRef, ...] = Field(min_length=1)
    preserve_refs: tuple[VersionRef, ...]
    regression_obligations: tuple[str, ...] = Field(min_length=1)
    expected_resolution: str

    @field_validator("repair_key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        return _key(value, "repair_key")

    @field_validator("expected_resolution")
    @classmethod
    def validate_resolution(cls, value: str) -> str:
        return _trimmed(value, "expected_resolution")

    @field_validator("regression_obligations")
    @classmethod
    def validate_obligations(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        result: list[str] = []
        for value in values:
            item = _trimmed(value, "regression_obligations")
            if item not in result:
                result.append(item)
        if not result:
            raise ValueError("regression_obligations cannot be empty")
        return tuple(result)

    @model_validator(mode="after")
    def validate_plan(self) -> "StoryRepairPlan":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_project_scoped(
            self.root_cause_ref,
            prefix="root-cause:",
            project_id=self.project_id,
            label="root_cause_ref",
        )
        targets = {_ref_key(ref) for ref in self.target_refs}
        preserve = {_ref_key(ref) for ref in self.preserve_refs}
        if len(targets) != len(self.target_refs):
            raise ValueError("target_refs must be unique")
        if len(preserve) != len(self.preserve_refs):
            raise ValueError("preserve_refs must be unique")
        if targets & preserve:
            raise ValueError("repair targets cannot overlap preserve_refs")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return story_repair_plan_logical_id(self.project_id, self.repair_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="root_cause", source=self.root_cause_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"repair_target_{index:03d}", source=ref)
            for index, ref in enumerate(self.target_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"preserve_{index:03d}", source=ref)
            for index, ref in enumerate(self.preserve_refs)
        )
        return tuple(values)


class QualityGateCheck(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    gate: QualityHardGate
    verdict: GateVerdict
    evidence_refs: tuple[VersionRef, ...] = ()

    @model_validator(mode="after")
    def validate_check(self) -> "QualityGateCheck":
        if self.verdict is GateVerdict.OPEN:
            raise ValueError("persisted quality hard-gate check cannot remain OPEN")
        return self


class StoryQualityResult(BaseModel):
    """Explicit story quality verdict; aggregate score never overrides blockers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    quality_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    story_core_ref: VersionRef
    full_screenplay_ref: VersionRef
    finding_refs: tuple[VersionRef, ...] = Field(min_length=1)
    repair_plan_refs: tuple[VersionRef, ...] = ()
    hard_gate_checks: tuple[QualityGateCheck, ...]
    aggregate_score: float | None = Field(default=None, ge=0.0, le=100.0)
    verdict: GateVerdict

    @field_validator("quality_key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        return _key(value, "quality_key")

    @model_validator(mode="after")
    def validate_quality(self) -> "StoryQualityResult":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.story_core_ref,
            story_core_logical_id(self.project_id),
            "story_core_ref",
        )
        _require_project_scoped(
            self.full_screenplay_ref,
            prefix="screenplay:",
            project_id=self.project_id,
            label="full_screenplay_ref",
        )
        for ref in self.finding_refs:
            _require_project_scoped(
                ref,
                prefix="critique-finding:",
                project_id=self.project_id,
                label="finding_refs",
            )
        finding_keys = [_ref_key(ref) for ref in self.finding_refs]
        if len(set(finding_keys)) != len(finding_keys):
            raise ValueError("finding_refs must be unique")
        for ref in self.repair_plan_refs:
            _require_project_scoped(
                ref,
                prefix="story-repair-plan:",
                project_id=self.project_id,
                label="repair_plan_refs",
            )
        repair_keys = [_ref_key(ref) for ref in self.repair_plan_refs]
        if len(set(repair_keys)) != len(repair_keys):
            raise ValueError("repair_plan_refs must be unique")
        checks = {item.gate: item for item in self.hard_gate_checks}
        if set(checks) != set(QualityHardGate):
            raise ValueError("hard_gate_checks must include every required hard gate exactly once")
        if len(checks) != len(self.hard_gate_checks):
            raise ValueError("hard_gate_checks cannot duplicate gates")
        if self.verdict is GateVerdict.OPEN:
            raise ValueError("StoryQualityResult cannot persist OPEN verdict")
        if any(item.verdict is GateVerdict.FAIL for item in self.hard_gate_checks):
            if self.verdict is not GateVerdict.FAIL:
                raise ValueError("hard-gate FAIL forces StoryQualityResult FAIL")
        elif any(
            item.verdict is GateVerdict.NEEDS_HUMAN_REVIEW
            for item in self.hard_gate_checks
        ):
            if self.verdict not in {
                GateVerdict.NEEDS_HUMAN_REVIEW,
                GateVerdict.FAIL,
            }:
                raise ValueError(
                    "hard-gate NEEDS_HUMAN_REVIEW cannot produce PASS/WARN"
                )
        elif self.verdict is GateVerdict.PASS and any(
            item.verdict is not GateVerdict.PASS for item in self.hard_gate_checks
        ):
            raise ValueError("PASS requires all hard-gate checks PASS")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return story_quality_result_logical_id(self.project_id, self.quality_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="story_core", source=self.story_core_ref),
            SourceVersionBinding(role="full_screenplay", source=self.full_screenplay_ref),
        ]
        values.extend(
            SourceVersionBinding(role=f"finding_{index:03d}", source=ref)
            for index, ref in enumerate(self.finding_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"repair_plan_{index:03d}", source=ref)
            for index, ref in enumerate(self.repair_plan_refs)
        )
        for gate in self.hard_gate_checks:
            values.extend(
                SourceVersionBinding(
                    role=f"hard_gate_{gate.gate.value.lower()}_{index:03d}",
                    source=ref,
                )
                for index, ref in enumerate(gate.evidence_refs)
            )
        return tuple(values)


class ScriptLockManifest(BaseModel):
    """Explicit immutable lock over exact story/screenplay versions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    version_id: VersionId
    active_profile_ref: VersionRef
    story_core_ref: VersionRef
    full_screenplay_ref: VersionRef
    quality_result_ref: VersionRef
    approval_policy: ScriptApprovalPolicy
    approval_ref: VersionRef | None = None
    locked_refs: tuple[VersionRef, ...] = Field(min_length=2)
    locked_versions_digest: str

    @field_validator("locked_versions_digest")
    @classmethod
    def validate_digest_text(cls, value: str) -> str:
        value = _trimmed(value, "locked_versions_digest")
        if (
            not value.startswith("sha256:")
            or len(value) != 71
            or any(ch not in "0123456789abcdef" for ch in value[7:])
        ):
            raise ValueError("locked_versions_digest must be sha256:<64 lowercase hex>")
        return value

    @model_validator(mode="after")
    def validate_lock_shape(self) -> "ScriptLockManifest":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.story_core_ref,
            story_core_logical_id(self.project_id),
            "story_core_ref",
        )
        _require_project_scoped(
            self.full_screenplay_ref,
            prefix="screenplay:",
            project_id=self.project_id,
            label="full_screenplay_ref",
        )
        _require_project_scoped(
            self.quality_result_ref,
            prefix="story-quality:",
            project_id=self.project_id,
            label="quality_result_ref",
        )
        if (
            self.approval_policy is ScriptApprovalPolicy.HUMAN_APPROVAL_REQUIRED
            and self.approval_ref is None
        ):
            raise ValueError("HUMAN_APPROVAL_REQUIRED requires approval_ref")
        keys = [_ref_key(ref) for ref in self.locked_refs]
        if len(set(keys)) != len(keys):
            raise ValueError("locked_refs must be unique")
        if _ref_key(self.story_core_ref) not in set(keys):
            raise ValueError("locked_refs must include exact StoryCore")
        if _ref_key(self.full_screenplay_ref) not in set(keys):
            raise ValueError("locked_refs must include exact FullScreenplay")
        expected = locked_refs_digest(self.locked_refs)
        if self.locked_versions_digest != expected:
            raise ValueError("locked_versions_digest does not match locked_refs")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return script_lock_logical_id(self.project_id)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role="active_production_profile", source=self.active_profile_ref),
            SourceVersionBinding(role="story_core", source=self.story_core_ref),
            SourceVersionBinding(role="full_screenplay", source=self.full_screenplay_ref),
            SourceVersionBinding(role="story_quality_result", source=self.quality_result_ref),
        ]
        if self.approval_ref is not None:
            values.append(SourceVersionBinding(role="approval_evidence", source=self.approval_ref))
        values.extend(
            SourceVersionBinding(role=f"locked_ref_{index:03d}", source=ref)
            for index, ref in enumerate(self.locked_refs)
        )
        return tuple(values)


StoryQualityValue: TypeAlias = (
    CritiqueFinding
    | RootCauseLocalization
    | StoryRepairPlan
    | StoryQualityResult
    | ScriptLockManifest
)


class StoryQualityArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: StoryQualityValue

    @model_validator(mode="after")
    def validate_artifact(self) -> "StoryQualityArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("story-quality artifact logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("story-quality artifact version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError("story-quality provenance must exactly bind declared sources")
        if self.metadata.provenance.rule_version != self.value.active_profile_ref:
            raise ValueError(
                "story-quality provenance rule_version must pin ActiveProductionProfile"
            )
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


def build_story_quality_provenance(
    value: StoryQualityValue,
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


class StoryQualityRepository:
    """Shared immutable repository/gates for IMP-027 story quality and lock."""

    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, self.graph)

    async def create_critique_finding(
        self,
        *,
        value: CritiqueFinding,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryQualityArtifact:
        await self._assert_critique_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_critique_finding(
        self,
        *,
        value: CritiqueFinding,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[StoryQualityArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_critique_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            cause="CritiqueFinding evidence/disposition revision",
            scope="critique_dependents",
        )

    async def create_root_cause(
        self,
        *,
        value: RootCauseLocalization,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryQualityArtifact:
        await self._assert_root_cause_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_root_cause(
        self,
        *,
        value: RootCauseLocalization,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[StoryQualityArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_root_cause_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            cause="RootCauseLocalization revision",
            scope="root_cause_dependents",
        )

    async def create_repair_plan(
        self,
        *,
        value: StoryRepairPlan,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryQualityArtifact:
        await self._assert_repair_plan_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_repair_plan(
        self,
        *,
        value: StoryRepairPlan,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[StoryQualityArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_repair_plan_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            cause="StoryRepairPlan scope revision",
            scope="repair_plan_dependents",
        )

    async def create_quality_result(
        self,
        *,
        value: StoryQualityResult,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryQualityArtifact:
        await self._assert_quality_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_quality_result(
        self,
        *,
        value: StoryQualityResult,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[StoryQualityArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_quality_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            cause="StoryQualityResult revision",
            scope="story_quality_dependents",
        )

    async def create_script_lock(
        self,
        *,
        value: ScriptLockManifest,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryQualityArtifact:
        await self._assert_script_lock_inputs(value)
        return await self._create_locked(value, provenance, created_at)

    async def revise_script_lock(
        self,
        *,
        value: ScriptLockManifest,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[StoryQualityArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_script_lock_inputs(value)
        await self._assert_current(
            predecessor,
            "ScriptLockManifest revision predecessor",
            {LifecycleState.LOCKED},
        )
        if predecessor.logical_id != value.logical_id:
            raise StoryQualityIdentityError(
                "ScriptLockManifest revision must preserve logical identity"
            )
        artifact = await self._create_successor(value, predecessor, provenance, created_at)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.LOCKED,
            expected_revision=expected_revision,
        )
        records = await self.invalidations.create_for_change(
            cause="ScriptLockManifest successor",
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope="script_lock_descendants",
            repair_or_recompute_requirement=(
                "Rebind downstream directing/cinematography to the new exact script lock."
            ),
        )
        return artifact, tuple(records)

    async def get_critique_finding(self, ref: VersionRef) -> StoryQualityArtifact | None:
        return await self._get_typed(ref, CritiqueFinding, "critique-finding:")

    async def get_root_cause(self, ref: VersionRef) -> StoryQualityArtifact | None:
        return await self._get_typed(ref, RootCauseLocalization, "root-cause:")

    async def get_repair_plan(self, ref: VersionRef) -> StoryQualityArtifact | None:
        return await self._get_typed(ref, StoryRepairPlan, "story-repair-plan:")

    async def get_quality_result(self, ref: VersionRef) -> StoryQualityArtifact | None:
        return await self._get_typed(ref, StoryQualityResult, "story-quality:")

    async def get_script_lock(self, ref: VersionRef) -> StoryQualityArtifact | None:
        return await self._get_typed(ref, ScriptLockManifest, "script-lock:")

    async def trace_ancestors(self, ref: VersionRef):
        return tuple(await self.graph.ancestors(ref))

    async def trace_descendants(self, ref: VersionRef):
        return tuple(await self.graph.descendants(ref))

    async def _create_approved(
        self,
        value: StoryQualityValue,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryQualityArtifact:
        artifact = await self._create_initial(value, provenance, created_at)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )
        return artifact

    async def _create_locked(
        self,
        value: ScriptLockManifest,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryQualityArtifact:
        artifact = await self._create_initial(value, provenance, created_at)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.LOCKED,
            expected_revision=0,
        )
        return artifact

    async def _revise_approved(
        self,
        *,
        value: StoryQualityValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
        cause: str,
        scope: str,
    ) -> tuple[StoryQualityArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise StoryQualityIdentityError(
                "story-quality revision must preserve logical identity"
            )
        await self._assert_current(
            predecessor,
            f"{type(value).__name__} revision predecessor",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        artifact = await self._create_successor(value, predecessor, provenance, created_at)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )
        records = await self.invalidations.create_for_change(
            cause=cause,
            source_old=predecessor,
            source_new=artifact.ref,
            provenance=provenance,
            scope=scope,
            repair_or_recompute_requirement=(
                "Recompute only dependency-reachable story quality/lock descendants."
            ),
        )
        return artifact, tuple(records)

    async def _create_initial(
        self,
        value: StoryQualityValue,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryQualityArtifact:
        self._assert_provenance(value, provenance)
        artifact = self._artifact(value, provenance, created_at, None)
        stored = await self.versions.create_initial(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        materialized = StoryQualityArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(materialized)
        return materialized

    async def _create_successor(
        self,
        value: StoryQualityValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> StoryQualityArtifact:
        self._assert_provenance(value, provenance)
        artifact = self._artifact(value, provenance, created_at, predecessor)
        stored = await self.versions.create_successor(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        materialized = StoryQualityArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(materialized)
        return materialized

    async def _get_typed(self, ref, model, prefix) -> StoryQualityArtifact | None:
        if not ref.logical_id.root.startswith(prefix):
            raise StoryQualityIdentityError(f"expected {prefix.rstrip(':')} artifact")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = model.model_validate(stored.payload)
        return StoryQualityArtifact(metadata=stored.metadata, value=value)

    async def _register_dependencies(self, artifact: StoryQualityArtifact) -> None:
        grouped: dict[tuple[str, str], list[str]] = {}
        refs: dict[tuple[str, str], VersionRef] = {}
        for binding in artifact.value.source_bindings():
            if binding.source == artifact.ref:
                continue
            key = _ref_key(binding.source)
            refs[key] = binding.source
            grouped.setdefault(key, []).append(binding.role)
        for key in sorted(grouped):
            await self.graph.create_edge(
                source=refs[key],
                dependent=artifact.ref,
                edge_type="story_quality_input",
                dependency_reason=" + ".join(sorted(set(grouped[key]))),
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _assert_critique_inputs(self, value: CritiqueFinding) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.story_core_ref,
            "StoryCore",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.full_screenplay_ref,
            "FullScreenplay",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.location_ref,
            "critique location",
            {
                LifecycleState.DRAFT,
                LifecycleState.REVIEW,
                LifecycleState.APPROVED,
                LifecycleState.LOCKED,
            },
        )
        for ref in value.evidence_refs:
            await self._assert_current(
                ref,
                "critique evidence",
                {
                    LifecycleState.DRAFT,
                    LifecycleState.REVIEW,
                    LifecycleState.APPROVED,
                    LifecycleState.LOCKED,
                },
            )
        if value.resolution_ref is not None:
            await self._assert_current(
                value.resolution_ref,
                "finding resolution",
                {LifecycleState.APPROVED},
            )
        story = await self._load(value.story_core_ref, StoryCoreVersion, "StoryCore")
        screenplay = await self._load(
            value.full_screenplay_ref,
            FullScreenplay,
            "FullScreenplay",
        )
        if story.phase is not StoryCorePhase.FROZEN_FOR_STRUCTURE:
            raise StoryQualityGateBlocked(
                "Story Critique requires FROZEN_FOR_STRUCTURE StoryCore"
            )
        if (
            story.active_profile_ref != value.active_profile_ref
            or screenplay.active_profile_ref != value.active_profile_ref
        ):
            raise StoryQualityGateBlocked(
                "Critique inputs must share exact ActiveProductionProfile"
            )
        if value.location_ref != value.full_screenplay_ref:
            ancestors = _reachability_keys(
                await self.graph.ancestors(value.full_screenplay_ref)
            )
            if _ref_key(value.location_ref) not in ancestors:
                raise StoryQualityGateBlocked(
                    "Critique location must be FullScreenplay or exact upstream ancestor"
                )

    async def _assert_root_cause_inputs(self, value: RootCauseLocalization) -> None:
        await self._assert_all_sources_exist(value)
        for ref, label, allowed in (
            (value.active_profile_ref, "ActiveProductionProfile", {LifecycleState.LOCKED}),
            (value.finding_ref, "CritiqueFinding", {LifecycleState.APPROVED}),
            (
                value.visible_location_ref,
                "visible defect location",
                {
                    LifecycleState.DRAFT,
                    LifecycleState.REVIEW,
                    LifecycleState.APPROVED,
                    LifecycleState.LOCKED,
                },
            ),
            (
                value.responsible_artifact_ref,
                "responsible artifact",
                {
                    LifecycleState.DRAFT,
                    LifecycleState.REVIEW,
                    LifecycleState.APPROVED,
                    LifecycleState.LOCKED,
                },
            ),
        ):
            await self._assert_current(ref, label, allowed)
        finding_artifact = await self.get_critique_finding(value.finding_ref)
        if finding_artifact is None:
            raise StoryQualityGateBlocked("CritiqueFinding exact version not found")
        finding = finding_artifact.value
        assert isinstance(finding, CritiqueFinding)
        if finding.location_ref != value.visible_location_ref:
            raise StoryQualityGateBlocked(
                "RootCause visible_location_ref must equal CritiqueFinding location"
            )
        if finding.active_profile_ref != value.active_profile_ref:
            raise StoryQualityGateBlocked("RootCause profile lineage mismatch")
        if value.responsible_artifact_ref != value.visible_location_ref:
            ancestors = _reachability_keys(
                await self.graph.ancestors(value.visible_location_ref)
            )
            if _ref_key(value.responsible_artifact_ref) not in ancestors:
                raise StoryQualityGateBlocked(
                    "responsible artifact must be visible defect source or exact ancestor"
                )
        visible_ancestors = _reachability_keys(
            await self.graph.ancestors(value.visible_location_ref)
        )
        visible_scope = {
            _ref_key(value.visible_location_ref),
            *visible_ancestors,
        }
        for ref in value.preserve_refs:
            if _ref_key(ref) not in visible_scope:
                raise StoryQualityGateBlocked(
                    "preserve ref must belong to visible defect exact ancestry"
                )

        descendants = _reachability_keys(
            await self.graph.descendants(value.responsible_artifact_ref)
        )
        for ref in value.invalidation_scope_candidate_refs:
            if (
                ref != value.responsible_artifact_ref
                and _ref_key(ref) not in descendants
            ):
                raise StoryQualityGateBlocked(
                    "invalidation candidate must be responsible artifact or descendant"
                )
        for ref in (*value.preserve_refs, *value.invalidation_scope_candidate_refs):
            await self._assert_current(
                ref,
                "root-cause preserve/invalidation ref",
                {
                    LifecycleState.DRAFT,
                    LifecycleState.REVIEW,
                    LifecycleState.APPROVED,
                    LifecycleState.LOCKED,
                },
            )

    async def _assert_repair_plan_inputs(self, value: StoryRepairPlan) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.root_cause_ref,
            "RootCauseLocalization",
            {LifecycleState.APPROVED},
        )
        root_artifact = await self.get_root_cause(value.root_cause_ref)
        if root_artifact is None:
            raise StoryQualityGateBlocked("RootCauseLocalization exact version not found")
        root = root_artifact.value
        assert isinstance(root, RootCauseLocalization)
        if root.active_profile_ref != value.active_profile_ref:
            raise StoryQualityGateBlocked("StoryRepairPlan profile lineage mismatch")
        if {_ref_key(ref) for ref in value.preserve_refs} != {
            _ref_key(ref) for ref in root.preserve_refs
        }:
            raise StoryQualityGateBlocked(
                "StoryRepairPlan must preserve the exact diagnosed preserve set"
            )
        descendants = _reachability_keys(
            await self.graph.descendants(root.responsible_artifact_ref)
        )
        for ref in value.target_refs:
            await self._assert_current(
                ref,
                "repair target",
                {
                    LifecycleState.DRAFT,
                    LifecycleState.REVIEW,
                    LifecycleState.APPROVED,
                    LifecycleState.LOCKED,
                },
            )
            if (
                ref != root.responsible_artifact_ref
                and _ref_key(ref) not in descendants
            ):
                raise StoryQualityGateBlocked(
                    "repair target must be responsible artifact or dependency descendant"
                )
        for ref in value.preserve_refs:
            await self._assert_current(
                ref,
                "preserve obligation",
                {
                    LifecycleState.DRAFT,
                    LifecycleState.REVIEW,
                    LifecycleState.APPROVED,
                    LifecycleState.LOCKED,
                },
            )

    async def _assert_quality_inputs(self, value: StoryQualityResult) -> None:
        await self._assert_all_sources_exist(value)
        for ref, label, allowed in (
            (value.active_profile_ref, "ActiveProductionProfile", {LifecycleState.LOCKED}),
            (value.story_core_ref, "StoryCore", {LifecycleState.LOCKED}),
            (
                value.full_screenplay_ref,
                "FullScreenplay",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            ),
        ):
            await self._assert_current(ref, label, allowed)
        story = await self._load(value.story_core_ref, StoryCoreVersion, "StoryCore")
        screenplay = await self._load(
            value.full_screenplay_ref,
            FullScreenplay,
            "FullScreenplay",
        )
        if story.phase is not StoryCorePhase.FROZEN_FOR_STRUCTURE:
            raise StoryQualityGateBlocked(
                "StoryQualityResult requires FROZEN_FOR_STRUCTURE StoryCore"
            )
        if (
            story.active_profile_ref != value.active_profile_ref
            or screenplay.active_profile_ref != value.active_profile_ref
        ):
            raise StoryQualityGateBlocked("StoryQualityResult profile lineage mismatch")

        repairs = {_ref_key(ref) for ref in value.repair_plan_refs}
        for ref in value.repair_plan_refs:
            await self._assert_current(ref, "StoryRepairPlan", {LifecycleState.APPROVED})
            repair_artifact = await self.get_repair_plan(ref)
            if repair_artifact is None:
                raise StoryQualityGateBlocked("StoryRepairPlan exact version not found")
            repair = repair_artifact.value
            assert isinstance(repair, StoryRepairPlan)
            if (
                repair.project_id != value.project_id
                or repair.active_profile_ref != value.active_profile_ref
            ):
                raise StoryQualityGateBlocked(
                    "StoryQualityResult repair-plan lineage mismatch"
                )

        unresolved_blocker = False
        unresolved_major = False
        for ref in value.finding_refs:
            await self._assert_current(ref, "CritiqueFinding", {LifecycleState.APPROVED})
            artifact = await self.get_critique_finding(ref)
            if artifact is None:
                raise StoryQualityGateBlocked("CritiqueFinding exact version not found")
            finding = artifact.value
            assert isinstance(finding, CritiqueFinding)
            if (
                finding.story_core_ref != value.story_core_ref
                or finding.full_screenplay_ref != value.full_screenplay_ref
                or finding.active_profile_ref != value.active_profile_ref
            ):
                raise StoryQualityGateBlocked(
                    "StoryQualityResult finding lineage mismatch"
                )
            if finding.disposition is FindingDisposition.OPEN:
                if finding.severity is FindingSeverity.BLOCKER:
                    unresolved_blocker = True
                elif finding.severity is FindingSeverity.MAJOR:
                    unresolved_major = True
            elif finding.disposition is FindingDisposition.RESOLVED:
                assert finding.resolution_ref is not None
                if _ref_key(finding.resolution_ref) not in repairs:
                    raise StoryQualityGateBlocked(
                        "resolved finding repair plan must be included in StoryQualityResult"
                    )

        if unresolved_blocker and value.verdict is not GateVerdict.FAIL:
            raise StoryQualityGateBlocked(
                "unresolved BLOCKER finding forces StoryQualityResult FAIL"
            )
        if unresolved_major and value.verdict is GateVerdict.PASS:
            raise StoryQualityGateBlocked(
                "open MAJOR finding prevents StoryQualityResult PASS"
            )

    async def _assert_script_lock_inputs(self, value: ScriptLockManifest) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.story_core_ref,
            "StoryCore",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.full_screenplay_ref,
            "FullScreenplay",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.quality_result_ref,
            "StoryQualityResult",
            {LifecycleState.APPROVED},
        )
        if value.approval_ref is not None:
            await self._assert_current(
                value.approval_ref,
                "script lock approval evidence",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
        for ref in value.locked_refs:
            await self._assert_current(
                ref,
                "locked exact version",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )

        screenplay_ancestors = _reachability_keys(
            await self.graph.ancestors(value.full_screenplay_ref)
        )
        allowed_locked = {
            _ref_key(value.story_core_ref),
            _ref_key(value.full_screenplay_ref),
            *screenplay_ancestors,
        }
        for ref in value.locked_refs:
            if _ref_key(ref) not in allowed_locked:
                raise StoryQualityGateBlocked(
                    "locked_refs must belong to exact screenplay/story ancestry"
                )

        story = await self._load(value.story_core_ref, StoryCoreVersion, "StoryCore")
        screenplay = await self._load(
            value.full_screenplay_ref,
            FullScreenplay,
            "FullScreenplay",
        )
        quality_artifact = await self.get_quality_result(value.quality_result_ref)
        if quality_artifact is None:
            raise StoryQualityGateBlocked("StoryQualityResult exact version not found")
        quality = quality_artifact.value
        assert isinstance(quality, StoryQualityResult)
        if story.phase is not StoryCorePhase.FROZEN_FOR_STRUCTURE:
            raise StoryQualityGateBlocked(
                "ScriptLock requires FROZEN_FOR_STRUCTURE StoryCore"
            )
        if quality.verdict is not GateVerdict.PASS:
            raise StoryQualityGateBlocked("ScriptLock requires StoryQualityResult PASS")
        if (
            quality.story_core_ref != value.story_core_ref
            or quality.full_screenplay_ref != value.full_screenplay_ref
            or quality.active_profile_ref != value.active_profile_ref
            or screenplay.active_profile_ref != value.active_profile_ref
            or story.active_profile_ref != value.active_profile_ref
        ):
            raise StoryQualityGateBlocked("ScriptLock exact-version lineage mismatch")

        for finding_ref in quality.finding_refs:
            artifact = await self.get_critique_finding(finding_ref)
            if artifact is None:
                raise StoryQualityGateBlocked("ScriptLock critique evidence not found")
            finding = artifact.value
            assert isinstance(finding, CritiqueFinding)
            if (
                finding.severity is FindingSeverity.BLOCKER
                and finding.disposition is not FindingDisposition.RESOLVED
            ):
                raise StoryQualityGateBlocked(
                    "ScriptLock blocked by unresolved BLOCKER finding"
                )

    async def _assert_all_sources_exist(self, value: StoryQualityValue) -> None:
        for binding in value.source_bindings():
            if await self.versions.get_version(binding.source) is None:
                raise StoryQualityGateBlocked(
                    f"missing exact source {binding.role}="
                    f"{binding.source.logical_id.root}/{binding.source.version_id.root}"
                )

    async def _assert_current(
        self,
        ref: VersionRef,
        label: str,
        allowed: set[LifecycleState],
    ) -> CurrentVersionPointer:
        try:
            pointer = await self.versions.get_current(ref.logical_id)
        except CurrentPointerNotFound as exc:
            raise StoryQualityGateBlocked(f"{label} has no current version") from exc
        if pointer.version_id != ref.version_id or pointer.status not in allowed:
            raise StoryQualityGateBlocked(
                f"{label} is not exact current accepted version"
            )
        return pointer

    async def _load(self, ref: VersionRef, model, label: str):
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise StoryQualityGateBlocked(f"{label} exact version not found")
        try:
            return model.model_validate(stored.payload)
        except ValidationError as exc:
            raise StoryQualityGateBlocked(
                f"{label} payload is not canonical {model.__name__}"
            ) from exc

    @staticmethod
    def _assert_provenance(value: StoryQualityValue, provenance: Provenance) -> None:
        if provenance.source_versions != value.source_bindings():
            raise StoryQualityIdentityError(
                "story-quality provenance must exactly match declared source bindings"
            )
        if provenance.rule_version != value.active_profile_ref:
            raise StoryQualityIdentityError(
                "story-quality provenance rule_version must pin ActiveProductionProfile"
            )

    @staticmethod
    def _artifact(
        value: StoryQualityValue,
        provenance: Provenance,
        created_at: datetime,
        predecessor: VersionRef | None,
    ) -> StoryQualityArtifact:
        return StoryQualityArtifact(
            metadata=SemanticRecordMetadata(
                logical_id=value.logical_id,
                version_id=value.version_id,
                predecessor=predecessor,
                provenance=provenance,
                created_at=created_at,
            ),
            value=value,
        )
