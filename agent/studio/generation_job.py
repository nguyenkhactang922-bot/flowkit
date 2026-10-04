"""IMP-052 canonical GenerationJob four-axis coordination state machine.

GenerationJob is mutable coordination state, not semantic narrative truth.  The
closed transition relation in Frozen Master section 68/FM2-002 is encoded here
as data so every unspecified transition fails closed.  Provider/network calls
never happen in this repository; adapters supply durable observations/evidence
to application services which then request legal state transitions.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .invalidation import InvalidationRepository
from .persistence import CASConflict, SQLiteReadRepository, SQLiteWriteOwner
from .primitives import LifecycleState, LogicalId, VersionRef
from .production_compiler import ProductionCompilerRepository, ShotIR
from .provider_adapter import ProviderExecutionPlan
from .provider_routing import (
    ProviderProfile,
    ProviderRoutingDecision,
    ProviderCapabilityRoutingRepository,
    RoutingVerdict,
)
from .versioning import VersionRepository


_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
_ACCEPTED = {LifecycleState.APPROVED, LifecycleState.LOCKED}


class GenerationJobError(RuntimeError):
    """Base IMP-052 error."""


class GenerationJobIdentityError(GenerationJobError):
    """Raised when immutable job identity/input pins disagree."""


class GenerationJobTransitionError(GenerationJobError):
    """Raised when a requested state transition is outside the closed contract."""


class GenerationJobTupleError(GenerationJobTransitionError):
    """Raised when a four-axis tuple violates cross-axis invariants."""


class GenerationJobAxis(str, Enum):
    SCHEDULER = "SCHEDULER"
    PROVIDER = "PROVIDER"
    ARTIFACT = "ARTIFACT"
    CREATIVE = "CREATIVE"


class SchedulerState(str, Enum):
    QUEUED = "QUEUED"
    WAITING_DEPENDENCY = "WAITING_DEPENDENCY"
    WAITING_CAPACITY = "WAITING_CAPACITY"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    WAITING_RECOVERY = "WAITING_RECOVERY"
    TERMINAL = "TERMINAL"


class ProviderState(str, Enum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    SUBMITTING = "SUBMITTING"
    SUBMITTED = "SUBMITTED"
    POLLING = "POLLING"
    UNKNOWN_REMOTE_STATE = "UNKNOWN_REMOTE_STATE"
    RECONCILING = "RECONCILING"
    AMBIGUOUS_HOLD = "AMBIGUOUS_HOLD"
    REMOTE_SUCCEEDED = "REMOTE_SUCCEEDED"
    REMOTE_FAILED = "REMOTE_FAILED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    REMOTE_CANCELED = "REMOTE_CANCELED"


class ArtifactState(str, Enum):
    NONE = "NONE"
    STAGING = "STAGING"
    READY = "READY"
    STALE_RESULT = "STALE_RESULT"
    QUARANTINED = "QUARANTINED"
    MISSING = "MISSING"
    CORRUPT = "CORRUPT"
    ARCHIVED = "ARCHIVED"


class CreativeState(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING_QA = "PENDING_QA"
    QA_RUNNING = "QA_RUNNING"
    QA_ERROR = "QA_ERROR"
    QA_FAILED = "QA_FAILED"
    REPAIR_PENDING = "REPAIR_PENDING"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    APPROVED = "APPROVED"
    LOCKED = "LOCKED"
    REJECTED = "REJECTED"


class TransitionOwner(str, Enum):
    SCHEDULER = "SCHEDULER"
    WORKER_COORDINATOR = "WORKER_COORDINATOR"
    RECOVERY_COORDINATOR = "RECOVERY_COORDINATOR"
    PROVIDER_ADAPTER = "PROVIDER_ADAPTER"
    ORCHESTRATOR = "ORCHESTRATOR"
    ARTIFACT_STORE = "ARTIFACT_STORE"
    ARTIFACT_RECONCILER = "ARTIFACT_RECONCILER"
    INVALIDATION_SERVICE = "INVALIDATION_SERVICE"
    QA_ORCHESTRATOR = "QA_ORCHESTRATOR"
    QA_SUBSYSTEM = "QA_SUBSYSTEM"
    APPROVAL_POLICY = "APPROVAL_POLICY"
    REPAIR_SUBSYSTEM = "REPAIR_SUBSYSTEM"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class DerivedJobStatus(str, Enum):
    WAITING = "WAITING"
    GENERATING = "GENERATING"
    RECOVERING = "RECOVERING"
    AMBIGUOUS = "AMBIGUOUS"
    DOWNLOADING = "DOWNLOADING"
    REVIEWING = "REVIEWING"
    REPAIRING = "REPAIRING"
    APPROVED = "APPROVED"
    FAILED = "FAILED"
    MISSING_ARTIFACT = "MISSING_ARTIFACT"


class GenerationJobStateTuple(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    scheduler: SchedulerState
    provider: ProviderState
    artifact: ArtifactState
    creative: CreativeState

    @model_validator(mode="after")
    def validate_cross_axis(self) -> "GenerationJobStateTuple":
        # Explicit source-backed invalid tuple in Frozen Master §68.
        if self.scheduler is SchedulerState.TERMINAL and self.provider is ProviderState.POLLING:
            raise ValueError("TERMINAL scheduler cannot coexist with provider POLLING")
        # QA may only be queued/running while an eligible current artifact is READY.
        if self.creative in {CreativeState.PENDING_QA, CreativeState.QA_RUNNING} and self.artifact is not ArtifactState.READY:
            raise ValueError("PENDING_QA/QA_RUNNING requires artifact READY")
        # Explicit V0.13 invalid fixture retained verbatim.
        if (
            self.provider is ProviderState.NOT_SUBMITTED
            and self.artifact is ArtifactState.READY
            and self.creative is CreativeState.PENDING_QA
        ):
            raise ValueError("NOT_SUBMITTED + READY + PENDING_QA is invalid")
        if self.artifact is ArtifactState.NONE and self.creative is CreativeState.QA_RUNNING:
            raise ValueError("artifact NONE cannot coexist with QA_RUNNING")
        return self


INITIAL_STATE = GenerationJobStateTuple(
    scheduler=SchedulerState.QUEUED,
    provider=ProviderState.NOT_SUBMITTED,
    artifact=ArtifactState.NONE,
    creative=CreativeState.NOT_APPLICABLE,
)


@dataclass(frozen=True)
class TransitionRule:
    axis: GenerationJobAxis
    from_state: str
    command: str
    to_state: str
    owners: tuple[TransitionOwner, ...]

    @property
    def key(self) -> tuple[GenerationJobAxis, str, str]:
        return (self.axis, self.from_state, self.command)


def _r(
    axis: GenerationJobAxis,
    from_state: Enum,
    command: str,
    to_state: Enum,
    *owners: TransitionOwner,
) -> TransitionRule:
    return TransitionRule(axis, str(from_state.value), command, str(to_state.value), tuple(owners))


# Frozen Master §68/FM2-002 exact closed relation: 15 + 19 + 14 + 14 = 62.
TRANSITION_RULES: tuple[TransitionRule, ...] = (
    # Scheduler (15)
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.QUEUED, "EVALUATE_DEPENDENCIES", SchedulerState.WAITING_DEPENDENCY, TransitionOwner.SCHEDULER),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.QUEUED, "EVALUATE_ADMISSION", SchedulerState.WAITING_CAPACITY, TransitionOwner.SCHEDULER),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.QUEUED, "CLAIM", SchedulerState.CLAIMED, TransitionOwner.SCHEDULER),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.WAITING_DEPENDENCY, "DEPENDENCIES_READY", SchedulerState.QUEUED, TransitionOwner.SCHEDULER),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.WAITING_CAPACITY, "CAPACITY_AVAILABLE", SchedulerState.QUEUED, TransitionOwner.SCHEDULER),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.CLAIMED, "START_WORK", SchedulerState.RUNNING, TransitionOwner.SCHEDULER, TransitionOwner.WORKER_COORDINATOR),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.CLAIMED, "LEASE_OR_RESTART_RECOVERY", SchedulerState.WAITING_RECOVERY, TransitionOwner.RECOVERY_COORDINATOR),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.RUNNING, "REMOTE_OR_LEASE_RECOVERY_REQUIRED", SchedulerState.WAITING_RECOVERY, TransitionOwner.RECOVERY_COORDINATOR),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.WAITING_RECOVERY, "RECOVERY_PROVEN_SAFE_TO_REQUEUE", SchedulerState.QUEUED, TransitionOwner.RECOVERY_COORDINATOR),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.WAITING_RECOVERY, "RECOVERY_RESUMES_ACTIVE_WORK", SchedulerState.RUNNING, TransitionOwner.RECOVERY_COORDINATOR),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.RUNNING, "SCHEDULER_WORK_COMPLETE", SchedulerState.TERMINAL, TransitionOwner.SCHEDULER),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.WAITING_RECOVERY, "RECOVERY_RESOLVED_TERMINAL", SchedulerState.TERMINAL, TransitionOwner.RECOVERY_COORDINATOR, TransitionOwner.SCHEDULER),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.QUEUED, "CANCEL_BEFORE_SIDE_EFFECT", SchedulerState.TERMINAL, TransitionOwner.SCHEDULER),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.WAITING_DEPENDENCY, "CANCEL_BEFORE_SIDE_EFFECT", SchedulerState.TERMINAL, TransitionOwner.SCHEDULER),
    _r(GenerationJobAxis.SCHEDULER, SchedulerState.WAITING_CAPACITY, "CANCEL_BEFORE_SIDE_EFFECT", SchedulerState.TERMINAL, TransitionOwner.SCHEDULER),
    # Provider (19)
    _r(GenerationJobAxis.PROVIDER, ProviderState.NOT_SUBMITTED, "SUBMIT", ProviderState.SUBMITTING, TransitionOwner.PROVIDER_ADAPTER, TransitionOwner.ORCHESTRATOR),
    _r(GenerationJobAxis.PROVIDER, ProviderState.SUBMITTING, "ACCEPTED_HANDLE", ProviderState.SUBMITTED, TransitionOwner.PROVIDER_ADAPTER, TransitionOwner.ORCHESTRATOR),
    _r(GenerationJobAxis.PROVIDER, ProviderState.SUBMITTING, "ACCEPTANCE_AMBIGUOUS", ProviderState.UNKNOWN_REMOTE_STATE, TransitionOwner.PROVIDER_ADAPTER, TransitionOwner.RECOVERY_COORDINATOR),
    _r(GenerationJobAxis.PROVIDER, ProviderState.SUBMITTED, "START_POLL", ProviderState.POLLING, TransitionOwner.PROVIDER_ADAPTER, TransitionOwner.ORCHESTRATOR),
    _r(GenerationJobAxis.PROVIDER, ProviderState.SUBMITTED, "RECOVERY_SCAN", ProviderState.RECONCILING, TransitionOwner.RECOVERY_COORDINATOR, TransitionOwner.PROVIDER_ADAPTER),
    _r(GenerationJobAxis.PROVIDER, ProviderState.POLLING, "REMOTE_SUCCESS", ProviderState.REMOTE_SUCCEEDED, TransitionOwner.PROVIDER_ADAPTER),
    _r(GenerationJobAxis.PROVIDER, ProviderState.POLLING, "REMOTE_FAILURE", ProviderState.REMOTE_FAILED, TransitionOwner.PROVIDER_ADAPTER),
    _r(GenerationJobAxis.PROVIDER, ProviderState.POLLING, "RECOVERY_SCAN", ProviderState.RECONCILING, TransitionOwner.RECOVERY_COORDINATOR, TransitionOwner.PROVIDER_ADAPTER),
    _r(GenerationJobAxis.PROVIDER, ProviderState.UNKNOWN_REMOTE_STATE, "BEGIN_RECONCILE", ProviderState.RECONCILING, TransitionOwner.RECOVERY_COORDINATOR, TransitionOwner.PROVIDER_ADAPTER),
    _r(GenerationJobAxis.PROVIDER, ProviderState.RECONCILING, "RECOVERED_HANDLE", ProviderState.SUBMITTED, TransitionOwner.RECOVERY_COORDINATOR, TransitionOwner.PROVIDER_ADAPTER),
    _r(GenerationJobAxis.PROVIDER, ProviderState.RECONCILING, "RECOVERED_ACTIVE_POLL", ProviderState.POLLING, TransitionOwner.RECOVERY_COORDINATOR, TransitionOwner.PROVIDER_ADAPTER),
    _r(GenerationJobAxis.PROVIDER, ProviderState.RECONCILING, "PROVEN_ABSENT", ProviderState.NOT_SUBMITTED, TransitionOwner.RECOVERY_COORDINATOR),
    _r(GenerationJobAxis.PROVIDER, ProviderState.RECONCILING, "STILL_AMBIGUOUS", ProviderState.AMBIGUOUS_HOLD, TransitionOwner.RECOVERY_COORDINATOR),
    _r(GenerationJobAxis.PROVIDER, ProviderState.AMBIGUOUS_HOLD, "RECONCILE_AGAIN", ProviderState.RECONCILING, TransitionOwner.RECOVERY_COORDINATOR),
    _r(GenerationJobAxis.PROVIDER, ProviderState.SUBMITTED, "REQUEST_CANCEL", ProviderState.CANCEL_REQUESTED, TransitionOwner.PROVIDER_ADAPTER, TransitionOwner.ORCHESTRATOR),
    _r(GenerationJobAxis.PROVIDER, ProviderState.POLLING, "REQUEST_CANCEL", ProviderState.CANCEL_REQUESTED, TransitionOwner.PROVIDER_ADAPTER, TransitionOwner.ORCHESTRATOR),
    _r(GenerationJobAxis.PROVIDER, ProviderState.CANCEL_REQUESTED, "CANCEL_CONFIRMED", ProviderState.REMOTE_CANCELED, TransitionOwner.PROVIDER_ADAPTER),
    _r(GenerationJobAxis.PROVIDER, ProviderState.CANCEL_REQUESTED, "REMOTE_SUCCESS_WON_RACE", ProviderState.REMOTE_SUCCEEDED, TransitionOwner.PROVIDER_ADAPTER),
    _r(GenerationJobAxis.PROVIDER, ProviderState.CANCEL_REQUESTED, "REMOTE_FAILURE_WON_RACE", ProviderState.REMOTE_FAILED, TransitionOwner.PROVIDER_ADAPTER),
    # Artifact (14)
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.NONE, "BEGIN_MATERIALIZE", ArtifactState.STAGING, TransitionOwner.ARTIFACT_STORE),
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.NONE, "DISCOVER_ORPHAN", ArtifactState.QUARANTINED, TransitionOwner.ARTIFACT_RECONCILER),
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.STAGING, "MATERIALIZE_VALID", ArtifactState.READY, TransitionOwner.ARTIFACT_STORE, TransitionOwner.ARTIFACT_RECONCILER),
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.STAGING, "INPUT_BECAME_STALE", ArtifactState.STALE_RESULT, TransitionOwner.ARTIFACT_STORE, TransitionOwner.ARTIFACT_RECONCILER),
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.STAGING, "INTEGRITY_FAILED", ArtifactState.CORRUPT, TransitionOwner.ARTIFACT_RECONCILER),
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.STAGING, "LINEAGE_UNTRUSTED", ArtifactState.QUARANTINED, TransitionOwner.ARTIFACT_RECONCILER),
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.READY, "DEPENDENCY_OR_INPUT_INVALIDATED", ArtifactState.STALE_RESULT, TransitionOwner.ARTIFACT_RECONCILER, TransitionOwner.INVALIDATION_SERVICE),
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.READY, "FILE_MISSING", ArtifactState.MISSING, TransitionOwner.ARTIFACT_RECONCILER),
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.READY, "INTEGRITY_FAILED", ArtifactState.CORRUPT, TransitionOwner.ARTIFACT_RECONCILER),
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.READY, "ARCHIVE", ArtifactState.ARCHIVED, TransitionOwner.ARTIFACT_STORE),
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.STALE_RESULT, "ARCHIVE", ArtifactState.ARCHIVED, TransitionOwner.ARTIFACT_STORE),
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.QUARANTINED, "ARCHIVE", ArtifactState.ARCHIVED, TransitionOwner.ARTIFACT_STORE, TransitionOwner.ARTIFACT_RECONCILER),
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.MISSING, "RECOVER_BYTES", ArtifactState.STAGING, TransitionOwner.ARTIFACT_RECONCILER),
    _r(GenerationJobAxis.ARTIFACT, ArtifactState.CORRUPT, "RECOVER_BYTES", ArtifactState.STAGING, TransitionOwner.ARTIFACT_RECONCILER),
    # Creative (14)
    _r(GenerationJobAxis.CREATIVE, CreativeState.NOT_APPLICABLE, "QUEUE_QA", CreativeState.PENDING_QA, TransitionOwner.QA_ORCHESTRATOR),
    _r(GenerationJobAxis.CREATIVE, CreativeState.PENDING_QA, "START_QA", CreativeState.QA_RUNNING, TransitionOwner.QA_ORCHESTRATOR),
    _r(GenerationJobAxis.CREATIVE, CreativeState.QA_RUNNING, "EVALUATOR_ERROR", CreativeState.QA_ERROR, TransitionOwner.QA_SUBSYSTEM),
    _r(GenerationJobAxis.CREATIVE, CreativeState.QA_RUNNING, "ARTIFACT_QA_FAILED", CreativeState.QA_FAILED, TransitionOwner.QA_SUBSYSTEM),
    _r(GenerationJobAxis.CREATIVE, CreativeState.QA_RUNNING, "REVIEW_REQUIRED", CreativeState.NEEDS_HUMAN_REVIEW, TransitionOwner.QA_SUBSYSTEM),
    _r(GenerationJobAxis.CREATIVE, CreativeState.QA_RUNNING, "QA_PASS_AND_AUTO_APPROVE", CreativeState.APPROVED, TransitionOwner.QA_SUBSYSTEM, TransitionOwner.APPROVAL_POLICY),
    _r(GenerationJobAxis.CREATIVE, CreativeState.QA_RUNNING, "EXPLICIT_REJECT", CreativeState.REJECTED, TransitionOwner.QA_SUBSYSTEM, TransitionOwner.APPROVAL_POLICY),
    _r(GenerationJobAxis.CREATIVE, CreativeState.QA_ERROR, "RETRY_EVALUATOR", CreativeState.PENDING_QA, TransitionOwner.QA_ORCHESTRATOR),
    _r(GenerationJobAxis.CREATIVE, CreativeState.QA_FAILED, "PLAN_REPAIR", CreativeState.REPAIR_PENDING, TransitionOwner.REPAIR_SUBSYSTEM),
    _r(GenerationJobAxis.CREATIVE, CreativeState.REPAIR_PENDING, "REPAIRED_CANDIDATE_READY", CreativeState.PENDING_QA, TransitionOwner.REPAIR_SUBSYSTEM, TransitionOwner.QA_ORCHESTRATOR),
    _r(GenerationJobAxis.CREATIVE, CreativeState.NEEDS_HUMAN_REVIEW, "HUMAN_APPROVE", CreativeState.APPROVED, TransitionOwner.HUMAN_REVIEW),
    _r(GenerationJobAxis.CREATIVE, CreativeState.NEEDS_HUMAN_REVIEW, "HUMAN_REJECT", CreativeState.REJECTED, TransitionOwner.HUMAN_REVIEW),
    _r(GenerationJobAxis.CREATIVE, CreativeState.NEEDS_HUMAN_REVIEW, "HUMAN_REQUEST_REPAIR", CreativeState.REPAIR_PENDING, TransitionOwner.HUMAN_REVIEW, TransitionOwner.REPAIR_SUBSYSTEM),
    _r(GenerationJobAxis.CREATIVE, CreativeState.APPROVED, "LOCK", CreativeState.LOCKED, TransitionOwner.APPROVAL_POLICY, TransitionOwner.HUMAN_REVIEW),
)

_RULES = {rule.key: rule for rule in TRANSITION_RULES}
if len(TRANSITION_RULES) != 62 or len(_RULES) != 62:  # import-time fail closed
    raise RuntimeError("GenerationJob closed transition table must contain exactly 62 unique rows")


def resolve_transition_rule(axis: GenerationJobAxis, from_state: str, command: str) -> TransitionRule:
    """Resolve one exact closed-row key; unspecified transitions are unsupported."""
    key = (axis, from_state.strip().upper(), command.strip().upper())
    rule = _RULES.get(key)
    if rule is None:
        raise GenerationJobTransitionError(
            f"unsupported transition: {axis.value} {key[1]} + {key[2]}"
        )
    return rule


class GuardFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    value: str | bool | int | float

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        value = value.strip()
        if not _TOKEN_RE.fullmatch(value):
            raise ValueError("guard fact key must be a stable token")
        return value


class TransitionGuardEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: str
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    facts: tuple[GuardFact, ...] = ()

    @field_validator("summary")
    @classmethod
    def normalize_summary(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("guard summary must be non-empty")
        return value

    @field_validator("evidence_refs")
    @classmethod
    def normalize_evidence_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(sorted(set(value.strip() for value in values if value.strip())))
        if not cleaned:
            raise ValueError("guard evidence requires at least one evidence ref")
        return cleaned

    @field_validator("facts")
    @classmethod
    def normalize_facts(cls, values: tuple[GuardFact, ...]) -> tuple[GuardFact, ...]:
        keys = [value.key for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("guard fact keys must be unique")
        return tuple(sorted(values, key=lambda value: value.key))

    def fact_map(self) -> dict[str, str | bool | int | float]:
        return {item.key: item.value for item in self.facts}


class ProviderRemoteLineage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_request_id: str | None = None
    provider_operation_id: str | None = None

    @field_validator("provider_request_id", "provider_operation_id")
    @classmethod
    def normalize_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("remote lineage identifier cannot be blank")
        return value

    @model_validator(mode="after")
    def at_least_one(self) -> "ProviderRemoteLineage":
        if self.provider_request_id is None and self.provider_operation_id is None:
            raise ValueError("remote lineage requires request or operation id")
        return self


class GenerationJobCreateRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    shot_ir_ref: VersionRef
    routing_decision_ref: VersionRef
    provider_profile_ref: VersionRef
    expected_input_fingerprint: str
    execution_plan: ProviderExecutionPlan
    attempt: int = Field(ge=1)
    submission_attempt_id: str
    local_submission_key: str
    idempotency_key: str | None = None
    created_at: datetime
    actor_ref: str
    reason: str
    correlation_id: str
    evidence_refs: tuple[str, ...] = Field(min_length=1)

    @field_validator("expected_input_fingerprint")
    @classmethod
    def validate_input_hash(cls, value: str) -> str:
        value = value.strip().lower()
        if not _HASH_RE.fullmatch(value):
            raise ValueError("job input fingerprint must be sha256:<64 lowercase hex>")
        return value

    @field_validator("submission_attempt_id", "local_submission_key", "actor_ref", "reason", "correlation_id")
    @classmethod
    def normalize_required(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{info.field_name} must be non-empty")
        return value

    @field_validator("idempotency_key")
    @classmethod
    def normalize_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("idempotency_key cannot be blank")
        return value

    @field_validator("evidence_refs")
    @classmethod
    def normalize_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        values = tuple(sorted(set(value.strip() for value in values if value.strip())))
        if not values:
            raise ValueError("creation requires evidence refs")
        return values

    @model_validator(mode="after")
    def validate_request(self) -> "GenerationJobCreateRequest":
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if not self.shot_ir_ref.logical_id.root.startswith("shot-ir:"):
            raise ValueError("shot_ir_ref must reference ShotIR")
        if not self.routing_decision_ref.logical_id.root.startswith("provider-route:"):
            raise ValueError("routing_decision_ref must reference ProviderRoutingDecision")
        if not self.provider_profile_ref.logical_id.root.startswith("provider-profile:"):
            raise ValueError("provider_profile_ref must reference ProviderProfile")
        if self.execution_plan.project_id != self.project_id:
            raise ValueError("execution plan belongs to a different project")
        if self.execution_plan.shot_ir_ref != self.shot_ir_ref:
            raise ValueError("execution plan must bind exact ShotIR")
        if self.execution_plan.routing_decision_ref != self.routing_decision_ref:
            raise ValueError("execution plan must bind exact ProviderRoutingDecision")
        if self.execution_plan.provider_profile_ref != self.provider_profile_ref:
            raise ValueError("execution plan must bind exact ProviderProfile")
        return self


class GenerationJob(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    generation_job_id: LogicalId
    project_id: LogicalId
    shot_id: LogicalId
    shot_ir_ref: VersionRef
    routing_decision_ref: VersionRef
    provider_profile_ref: VersionRef
    expected_input_fingerprint: str
    execution_plan_hash: str
    attempt: int = Field(ge=1)
    submission_attempt_id: str
    local_submission_key: str
    idempotency_key: str | None = None
    provider_key: str
    provider_surface: str
    region: str
    model_family: str
    model_version: str
    provider_request_id: str | None = None
    provider_operation_id: str | None = None
    scheduler_state: SchedulerState
    provider_state: ProviderState
    artifact_state: ArtifactState
    creative_state: CreativeState
    revision: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None
    created_by: str
    creation_reason: str
    creation_correlation_id: str
    creation_evidence_refs: tuple[str, ...]

    @field_validator("expected_input_fingerprint", "execution_plan_hash")
    @classmethod
    def validate_hashes(cls, value: str) -> str:
        if not _HASH_RE.fullmatch(value):
            raise ValueError("GenerationJob hash format is invalid")
        return value

    @model_validator(mode="after")
    def validate_job(self) -> "GenerationJob":
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("GenerationJob timestamps must be timezone-aware")
        if self.submitted_at is not None and self.submitted_at.tzinfo is None:
            raise ValueError("submitted_at must be timezone-aware")
        GenerationJobStateTuple(
            scheduler=self.scheduler_state,
            provider=self.provider_state,
            artifact=self.artifact_state,
            creative=self.creative_state,
        )
        expected = generation_job_logical_id(
            self.project_id,
            self.shot_ir_ref,
            self.submission_attempt_id,
        )
        if self.generation_job_id != expected:
            raise ValueError(f"generation_job_id must be {expected.root}")
        return self

    @property
    def state_tuple(self) -> GenerationJobStateTuple:
        return GenerationJobStateTuple(
            scheduler=self.scheduler_state,
            provider=self.provider_state,
            artifact=self.artifact_state,
            creative=self.creative_state,
        )

    @property
    def derived_status(self) -> DerivedJobStatus:
        return derive_job_status(self.state_tuple)


class GenerationJobTransition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    transition_id: str
    generation_job_id: LogicalId
    axis: GenerationJobAxis
    command: str
    from_state: str
    to_state: str
    owner: TransitionOwner
    guard_evidence: TransitionGuardEvidence
    actor_ref: str
    reason: str
    correlation_id: str
    from_revision: int = Field(ge=0)
    to_revision: int = Field(ge=1)
    created_at: datetime

    @model_validator(mode="after")
    def validate_transition(self) -> "GenerationJobTransition":
        if self.to_revision != self.from_revision + 1:
            raise ValueError("transition revision must increment exactly once")
        if self.created_at.tzinfo is None:
            raise ValueError("transition created_at must be timezone-aware")
        return self


class GenerationJobTransitionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    job: GenerationJob
    transition: GenerationJobTransition


def generation_job_logical_id(
    project_id: LogicalId,
    shot_ir_ref: VersionRef,
    submission_attempt_id: str,
) -> LogicalId:
    raw = "|".join(
        (
            project_id.root,
            shot_ir_ref.logical_id.root,
            shot_ir_ref.version_id.root,
            submission_attempt_id.strip(),
        )
    ).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:32]
    return LogicalId(f"generation-job:{project_id.root}:{digest}")


def derive_transition_id(job_id: LogicalId, to_revision: int) -> str:
    raw = f"{job_id.root}|{to_revision}".encode("utf-8")
    return "job-transition:" + hashlib.sha256(raw).hexdigest()


def derive_job_status(state: GenerationJobStateTuple) -> DerivedJobStatus:
    """Non-authoritative UI summary projection from the four durable axes."""
    if state.artifact is ArtifactState.MISSING:
        return DerivedJobStatus.MISSING_ARTIFACT
    if state.provider is ProviderState.AMBIGUOUS_HOLD:
        return DerivedJobStatus.AMBIGUOUS
    if state.scheduler is SchedulerState.WAITING_RECOVERY or state.provider in {
        ProviderState.UNKNOWN_REMOTE_STATE,
        ProviderState.RECONCILING,
    }:
        return DerivedJobStatus.RECOVERING
    if state.artifact is ArtifactState.STAGING:
        return DerivedJobStatus.DOWNLOADING
    if state.creative in {CreativeState.APPROVED, CreativeState.LOCKED}:
        return DerivedJobStatus.APPROVED
    if state.creative is CreativeState.REPAIR_PENDING:
        return DerivedJobStatus.REPAIRING
    if state.creative in {
        CreativeState.PENDING_QA,
        CreativeState.QA_RUNNING,
        CreativeState.QA_ERROR,
        CreativeState.NEEDS_HUMAN_REVIEW,
    }:
        return DerivedJobStatus.REVIEWING
    if (
        state.provider in {ProviderState.REMOTE_FAILED, ProviderState.REMOTE_CANCELED}
        or state.artifact in {ArtifactState.CORRUPT, ArtifactState.STALE_RESULT}
        or state.creative in {CreativeState.QA_FAILED, CreativeState.REJECTED}
    ):
        return DerivedJobStatus.FAILED
    if state.scheduler is SchedulerState.RUNNING or state.provider in {
        ProviderState.SUBMITTING,
        ProviderState.SUBMITTED,
        ProviderState.POLLING,
        ProviderState.CANCEL_REQUESTED,
    }:
        return DerivedJobStatus.GENERATING
    return DerivedJobStatus.WAITING


class GenerationJobRepository:
    """Durable four-axis job repository using the shared SQLite write owner."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.reader = SQLiteReadRepository(writer.db_path)
        self.versions = VersionRepository(writer)
        self.invalidations = InvalidationRepository(writer)
        self.compiler = ProductionCompilerRepository(writer)
        self.routing = ProviderCapabilityRoutingRepository(writer)

    async def create_job(self, request: GenerationJobCreateRequest) -> GenerationJob:
        ir_artifact = await self.compiler.get_shot_ir(request.shot_ir_ref)
        if ir_artifact is None or not isinstance(ir_artifact.value, ShotIR):
            raise GenerationJobIdentityError("ShotIR exact version does not exist")
        shot_ir = ir_artifact.value
        await self._assert_current_valid(request.shot_ir_ref, "ShotIR", _ACCEPTED)
        if shot_ir.project_id != request.project_id:
            raise GenerationJobIdentityError("ShotIR belongs to a different project")
        if shot_ir.hashes.input_fingerprint != request.expected_input_fingerprint:
            raise GenerationJobIdentityError("expected input fingerprint does not equal exact ShotIR fingerprint")

        route_artifact = await self.routing.get_routing_decision(request.routing_decision_ref)
        if route_artifact is None or not isinstance(route_artifact.value, ProviderRoutingDecision):
            raise GenerationJobIdentityError("ProviderRoutingDecision exact version does not exist")
        route = route_artifact.value
        await self._assert_current_valid(request.routing_decision_ref, "ProviderRoutingDecision", {LifecycleState.APPROVED})
        if route.project_id != request.project_id or route.shot_ir_ref != request.shot_ir_ref:
            raise GenerationJobIdentityError("routing decision does not bind exact job ShotIR/project")
        if route.verdict is not RoutingVerdict.SELECTED or route.selected_profile_ref != request.provider_profile_ref:
            raise GenerationJobIdentityError("job requires exact SELECTED ProviderProfile from routing decision")

        profile_artifact = await self.routing.get_provider_profile(request.provider_profile_ref)
        if profile_artifact is None or not isinstance(profile_artifact.value, ProviderProfile):
            raise GenerationJobIdentityError("ProviderProfile exact version does not exist")
        profile = profile_artifact.value
        await self._assert_current_valid(request.provider_profile_ref, "ProviderProfile", _ACCEPTED)
        if not (profile.verified_at <= request.created_at <= profile.expires_at):
            raise GenerationJobIdentityError("ProviderProfile is not valid at GenerationJob creation time")
        if route.evaluated_at > request.created_at:
            raise GenerationJobIdentityError("routing decision cannot be newer than GenerationJob creation time")
        plan = request.execution_plan
        if (
            plan.provider_key != profile.provider_key
            or plan.surface != profile.surface
            or plan.model_family != profile.model_family
            or plan.model_version != profile.model_version
        ):
            raise GenerationJobIdentityError(
                "ProviderExecutionPlan provider/model identity does not match exact ProviderProfile"
            )

        job_id = generation_job_logical_id(
            request.project_id,
            request.shot_ir_ref,
            request.submission_attempt_id,
        )
        creation_evidence_json = json.dumps(
            {"evidence_refs": list(request.evidence_refs)},
            sort_keys=True,
            separators=(",", ":"),
        )
        job = GenerationJob(
            generation_job_id=job_id,
            project_id=request.project_id,
            shot_id=shot_ir.shot_ref.logical_id,
            shot_ir_ref=request.shot_ir_ref,
            routing_decision_ref=request.routing_decision_ref,
            provider_profile_ref=request.provider_profile_ref,
            expected_input_fingerprint=request.expected_input_fingerprint,
            execution_plan_hash=request.execution_plan.plan_hash,
            attempt=request.attempt,
            submission_attempt_id=request.submission_attempt_id,
            local_submission_key=request.local_submission_key,
            idempotency_key=request.idempotency_key,
            provider_key=profile.provider_key,
            provider_surface=profile.surface,
            region=profile.region,
            model_family=profile.model_family,
            model_version=profile.model_version,
            scheduler_state=INITIAL_STATE.scheduler,
            provider_state=INITIAL_STATE.provider,
            artifact_state=INITIAL_STATE.artifact,
            creative_state=INITIAL_STATE.creative,
            revision=0,
            created_at=request.created_at,
            updated_at=request.created_at,
            created_by=request.actor_ref,
            creation_reason=request.reason,
            creation_correlation_id=request.correlation_id,
            creation_evidence_refs=request.evidence_refs,
        )

        async def command(tx):
            existing = await tx.fetchone(
                "SELECT * FROM studio_generation_job WHERE generation_job_id=?",
                (job_id.root,),
            )
            if existing is not None:
                stored = self._job_from_row(existing)
                if not self._same_creation_identity(stored, job):
                    raise GenerationJobIdentityError(
                        "generation_job_id exact replay conflicts with persisted immutable identity"
                    )
                return stored
            await tx.execute(
                """
                INSERT INTO studio_generation_job (
                    generation_job_id, project_id, shot_id,
                    shot_ir_object_id, shot_ir_version,
                    routing_decision_object_id, routing_decision_version,
                    provider_profile_object_id, provider_profile_version,
                    expected_input_fingerprint, execution_plan_hash,
                    attempt, submission_attempt_id, local_submission_key, idempotency_key,
                    provider_key, provider_surface, region, model_family, model_version,
                    created_by, creation_reason, creation_correlation_id, creation_evidence_json,
                    provider_request_id, provider_operation_id,
                    scheduler_state, provider_state, artifact_state, creative_state,
                    revision, created_at, updated_at, submitted_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    job.generation_job_id.root,
                    job.project_id.root,
                    job.shot_id.root,
                    job.shot_ir_ref.logical_id.root,
                    job.shot_ir_ref.version_id.root,
                    job.routing_decision_ref.logical_id.root,
                    job.routing_decision_ref.version_id.root,
                    job.provider_profile_ref.logical_id.root,
                    job.provider_profile_ref.version_id.root,
                    job.expected_input_fingerprint,
                    job.execution_plan_hash,
                    job.attempt,
                    job.submission_attempt_id,
                    job.local_submission_key,
                    job.idempotency_key,
                    job.provider_key,
                    job.provider_surface,
                    job.region,
                    job.model_family,
                    job.model_version,
                    job.created_by,
                    job.creation_reason,
                    job.creation_correlation_id,
                    creation_evidence_json,
                    None,
                    None,
                    job.scheduler_state.value,
                    job.provider_state.value,
                    job.artifact_state.value,
                    job.creative_state.value,
                    0,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                    None,
                ),
            )
            return job

        return await self.writer.execute(command)

    async def get_job(self, job_id: LogicalId) -> GenerationJob | None:
        row = await self.reader.fetchone(
            "SELECT * FROM studio_generation_job WHERE generation_job_id=?",
            (job_id.root,),
        )
        return None if row is None else self._job_from_row(row)

    async def list_transitions(self, job_id: LogicalId) -> list[GenerationJobTransition]:
        rows = await self.reader.fetchall(
            """
            SELECT * FROM studio_generation_job_transition
            WHERE generation_job_id=? ORDER BY to_revision
            """,
            (job_id.root,),
        )
        return [self._transition_from_row(row) for row in rows]

    async def transition(
        self,
        *,
        job_id: LogicalId,
        axis: GenerationJobAxis,
        command: str,
        owner: TransitionOwner,
        guard_evidence: TransitionGuardEvidence,
        expected_revision: int,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        remote_lineage: ProviderRemoteLineage | None = None,
    ) -> GenerationJobTransitionResult:
        command = command.strip().upper()
        actor_ref = actor_ref.strip()
        reason = reason.strip()
        correlation_id = correlation_id.strip()
        if not actor_ref or not reason or not correlation_id:
            raise GenerationJobTransitionError("actor/reason/correlation_id must be non-empty")
        if recorded_at.tzinfo is None:
            raise GenerationJobTransitionError("transition timestamp must be timezone-aware")

        async def mutate(tx):
            row = await tx.fetchone(
                "SELECT * FROM studio_generation_job WHERE generation_job_id=?",
                (job_id.root,),
            )
            if row is None:
                raise GenerationJobIdentityError("GenerationJob does not exist")
            job = self._job_from_row(row)
            if job.revision != expected_revision:
                raise CASConflict(
                    f"stale GenerationJob revision; expected {expected_revision}, actual {job.revision}"
                )
            from_state = self._axis_state(job, axis)
            rule = _RULES.get((axis, from_state, command))
            if rule is None:
                raise GenerationJobTransitionError(
                    f"unsupported transition: {axis.value} {from_state} + {command}"
                )
            if owner not in rule.owners:
                raise GenerationJobTransitionError(
                    f"transition owner {owner.value} is not authorized for {axis.value}/{command}"
                )
            if remote_lineage is not None and (
                axis is not GenerationJobAxis.PROVIDER
                or command not in {"ACCEPTED_HANDLE", "RECOVERED_HANDLE", "RECOVERED_ACTIVE_POLL"}
            ):
                raise GenerationJobTransitionError(
                    "remote provider lineage may only be bound by accepted/recovered provider-handle transitions"
                )
            self._validate_rule_guard(job, rule, guard_evidence, remote_lineage)
            target = self._target_tuple(job, axis, rule.to_state)
            try:
                GenerationJobStateTuple.model_validate(target)
            except Exception as exc:
                raise GenerationJobTupleError("transition would create invalid four-axis tuple") from exc

            changes: dict[str, Any] = {
                self._axis_column(axis): rule.to_state,
                "updated_at": recorded_at.isoformat(),
            }
            if axis is GenerationJobAxis.PROVIDER and command == "SUBMIT" and job.submitted_at is None:
                changes["submitted_at"] = recorded_at.isoformat()
            if remote_lineage is not None:
                self._validate_remote_lineage(job, remote_lineage)
                if remote_lineage.provider_request_id is not None:
                    changes["provider_request_id"] = remote_lineage.provider_request_id
                if remote_lineage.provider_operation_id is not None:
                    changes["provider_operation_id"] = remote_lineage.provider_operation_id

            new_revision = await tx.cas_update(
                table="studio_generation_job",
                pk_column="generation_job_id",
                pk_value=job_id.root,
                expected_revision=expected_revision,
                changes=changes,
            )
            transition = GenerationJobTransition(
                transition_id=derive_transition_id(job_id, new_revision),
                generation_job_id=job_id,
                axis=axis,
                command=command,
                from_state=from_state,
                to_state=rule.to_state,
                owner=owner,
                guard_evidence=guard_evidence,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                from_revision=expected_revision,
                to_revision=new_revision,
                created_at=recorded_at,
            )
            await tx.execute(
                """
                INSERT INTO studio_generation_job_transition (
                    transition_id, generation_job_id, axis, command,
                    from_state, to_state, owner, guard_evidence_json,
                    actor_ref, reason, correlation_id,
                    from_revision, to_revision, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    transition.transition_id,
                    job_id.root,
                    transition.axis.value,
                    transition.command,
                    transition.from_state,
                    transition.to_state,
                    transition.owner.value,
                    transition.guard_evidence.model_dump_json(),
                    transition.actor_ref,
                    transition.reason,
                    transition.correlation_id,
                    transition.from_revision,
                    transition.to_revision,
                    transition.created_at.isoformat(),
                ),
            )
            updated = await tx.fetchone(
                "SELECT * FROM studio_generation_job WHERE generation_job_id=?",
                (job_id.root,),
            )
            assert updated is not None
            return GenerationJobTransitionResult(
                job=self._job_from_row(updated),
                transition=transition,
            )

        return await self.writer.execute(mutate)

    async def _assert_current_valid(
        self,
        ref: VersionRef,
        label: str,
        allowed: set[LifecycleState],
    ) -> None:
        pointer = await self.versions.get_current(ref.logical_id)
        if pointer is None or pointer.version_id != ref.version_id or pointer.status not in allowed:
            raise GenerationJobIdentityError(f"{label} is not exact current accepted authority")
        for record in await self.invalidations.list_unresolved():
            if record.affected_object_id == ref.logical_id and record.affected_object_version == ref.version_id:
                raise GenerationJobIdentityError(f"{label} has unresolved durable invalidation")

    @staticmethod
    def _same_creation_identity(left: GenerationJob, right: GenerationJob) -> bool:
        fields = (
            "generation_job_id", "project_id", "shot_id", "shot_ir_ref",
            "routing_decision_ref", "provider_profile_ref", "expected_input_fingerprint",
            "execution_plan_hash", "attempt", "submission_attempt_id",
            "local_submission_key", "idempotency_key", "provider_key",
            "provider_surface", "region", "model_family", "model_version",
            "created_at", "created_by", "creation_reason",
            "creation_correlation_id", "creation_evidence_refs",
        )
        return all(getattr(left, name) == getattr(right, name) for name in fields)

    @staticmethod
    def _axis_state(job: GenerationJob, axis: GenerationJobAxis) -> str:
        return {
            GenerationJobAxis.SCHEDULER: job.scheduler_state.value,
            GenerationJobAxis.PROVIDER: job.provider_state.value,
            GenerationJobAxis.ARTIFACT: job.artifact_state.value,
            GenerationJobAxis.CREATIVE: job.creative_state.value,
        }[axis]

    @staticmethod
    def _axis_column(axis: GenerationJobAxis) -> str:
        return {
            GenerationJobAxis.SCHEDULER: "scheduler_state",
            GenerationJobAxis.PROVIDER: "provider_state",
            GenerationJobAxis.ARTIFACT: "artifact_state",
            GenerationJobAxis.CREATIVE: "creative_state",
        }[axis]

    @staticmethod
    def _target_tuple(job: GenerationJob, axis: GenerationJobAxis, to_state: str) -> dict[str, str]:
        values = {
            "scheduler": job.scheduler_state.value,
            "provider": job.provider_state.value,
            "artifact": job.artifact_state.value,
            "creative": job.creative_state.value,
        }
        values[axis.value.lower()] = to_state
        return values

    @staticmethod
    def _validate_remote_lineage(job: GenerationJob, value: ProviderRemoteLineage) -> None:
        if (
            job.provider_request_id is not None
            and value.provider_request_id is not None
            and value.provider_request_id != job.provider_request_id
        ):
            raise GenerationJobTransitionError("provider_request_id cannot be rebound")
        if (
            job.provider_operation_id is not None
            and value.provider_operation_id is not None
            and value.provider_operation_id != job.provider_operation_id
        ):
            raise GenerationJobTransitionError("provider_operation_id cannot be rebound")

    @staticmethod
    def _validate_rule_guard(
        job: GenerationJob,
        rule: TransitionRule,
        guard: TransitionGuardEvidence,
        remote: ProviderRemoteLineage | None,
    ) -> None:
        facts = guard.fact_map()
        command = rule.command
        if command == "SUBMIT":
            if job.scheduler_state is not SchedulerState.RUNNING:
                raise GenerationJobTransitionError("SUBMIT requires scheduler RUNNING")
            if facts.get("side_effect_boundary_ready") is not True:
                raise GenerationJobTransitionError("SUBMIT requires durable side-effect-boundary proof")
        if command in {"ACCEPTED_HANDLE", "RECOVERED_HANDLE", "RECOVERED_ACTIVE_POLL"}:
            has_existing = bool(job.provider_request_id or job.provider_operation_id)
            if remote is None and not has_existing:
                raise GenerationJobTransitionError(f"{command} requires durable recovered/accepted remote handle")
        if command in {"START_POLL", "REQUEST_CANCEL"}:
            if not (job.provider_request_id or job.provider_operation_id):
                raise GenerationJobTransitionError(f"{command} requires durable remote handle")
        if command == "REQUEST_CANCEL" and facts.get("cancel_supported") is not True:
            raise GenerationJobTransitionError("REQUEST_CANCEL requires proven provider cancel capability")
        if command == "PROVEN_ABSENT" and not (
            facts.get("proven_absent") is True or facts.get("verified_same_job_idempotency") is True
        ):
            raise GenerationJobTransitionError("PROVEN_ABSENT requires absence/idempotency proof")
        if command == "RECOVERY_PROVEN_SAFE_TO_REQUEUE":
            if job.provider_state is not ProviderState.NOT_SUBMITTED:
                raise GenerationJobTransitionError("safe requeue requires provider NOT_SUBMITTED after reconciliation")
            if not (
                facts.get("proven_absent") is True or facts.get("verified_same_job_idempotency") is True
            ):
                raise GenerationJobTransitionError("safe requeue requires absence/idempotency proof")
        if command == "RECOVERY_RESUMES_ACTIVE_WORK" and job.provider_state not in {
            ProviderState.SUBMITTED,
            ProviderState.POLLING,
        }:
            raise GenerationJobTransitionError("active recovery resume requires recovered submitted/polling operation")
        if command == "SCHEDULER_WORK_COMPLETE" and job.provider_state in {
            ProviderState.SUBMITTING,
            ProviderState.SUBMITTED,
            ProviderState.POLLING,
            ProviderState.UNKNOWN_REMOTE_STATE,
            ProviderState.RECONCILING,
            ProviderState.AMBIGUOUS_HOLD,
            ProviderState.CANCEL_REQUESTED,
        }:
            raise GenerationJobTransitionError("scheduler cannot terminate while provider work/ambiguity is active")
        if command == "CANCEL_BEFORE_SIDE_EFFECT" and job.provider_state is not ProviderState.NOT_SUBMITTED:
            raise GenerationJobTransitionError("pre-side-effect cancel requires provider NOT_SUBMITTED")
        if command == "BEGIN_MATERIALIZE" and not (
            job.provider_state is ProviderState.REMOTE_SUCCEEDED
            or facts.get("local_result_eligible") is True
        ):
            raise GenerationJobTransitionError("materialization requires remote success or proven local result eligibility")
        if command in {"QUEUE_QA", "START_QA", "REPAIRED_CANDIDATE_READY", "HUMAN_APPROVE", "HUMAN_REJECT", "HUMAN_REQUEST_REPAIR", "QA_PASS_AND_AUTO_APPROVE", "EXPLICIT_REJECT"}:
            if job.artifact_state is not ArtifactState.READY:
                raise GenerationJobTransitionError(f"{command} requires artifact READY")

    @staticmethod
    def _job_from_row(row) -> GenerationJob:
        evidence = json.loads(str(row["creation_evidence_json"]))
        return GenerationJob(
            generation_job_id=LogicalId(str(row["generation_job_id"])),
            project_id=LogicalId(str(row["project_id"])),
            shot_id=LogicalId(str(row["shot_id"])),
            shot_ir_ref=VersionRef(
                logical_id=LogicalId(str(row["shot_ir_object_id"])),
                version_id=str(row["shot_ir_version"]),
            ),
            routing_decision_ref=VersionRef(
                logical_id=LogicalId(str(row["routing_decision_object_id"])),
                version_id=str(row["routing_decision_version"]),
            ),
            provider_profile_ref=VersionRef(
                logical_id=LogicalId(str(row["provider_profile_object_id"])),
                version_id=str(row["provider_profile_version"]),
            ),
            expected_input_fingerprint=str(row["expected_input_fingerprint"]),
            execution_plan_hash=str(row["execution_plan_hash"]),
            attempt=int(row["attempt"]),
            submission_attempt_id=str(row["submission_attempt_id"]),
            local_submission_key=str(row["local_submission_key"]),
            idempotency_key=None if row["idempotency_key"] is None else str(row["idempotency_key"]),
            provider_key=str(row["provider_key"]),
            provider_surface=str(row["provider_surface"]),
            region=str(row["region"]),
            model_family=str(row["model_family"]),
            model_version=str(row["model_version"]),
            provider_request_id=None if row["provider_request_id"] is None else str(row["provider_request_id"]),
            provider_operation_id=None if row["provider_operation_id"] is None else str(row["provider_operation_id"]),
            scheduler_state=SchedulerState(str(row["scheduler_state"])),
            provider_state=ProviderState(str(row["provider_state"])),
            artifact_state=ArtifactState(str(row["artifact_state"])),
            creative_state=CreativeState(str(row["creative_state"])),
            revision=int(row["revision"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
            submitted_at=None if row["submitted_at"] is None else datetime.fromisoformat(str(row["submitted_at"])),
            created_by=str(row["created_by"]),
            creation_reason=str(row["creation_reason"]),
            creation_correlation_id=str(row["creation_correlation_id"]),
            creation_evidence_refs=tuple(evidence.get("evidence_refs", ())),
        )

    @staticmethod
    def _transition_from_row(row) -> GenerationJobTransition:
        return GenerationJobTransition(
            transition_id=str(row["transition_id"]),
            generation_job_id=LogicalId(str(row["generation_job_id"])),
            axis=GenerationJobAxis(str(row["axis"])),
            command=str(row["command"]),
            from_state=str(row["from_state"]),
            to_state=str(row["to_state"]),
            owner=TransitionOwner(str(row["owner"])),
            guard_evidence=TransitionGuardEvidence.model_validate_json(str(row["guard_evidence_json"])),
            actor_ref=str(row["actor_ref"]),
            reason=str(row["reason"]),
            correlation_id=str(row["correlation_id"]),
            from_revision=int(row["from_revision"]),
            to_revision=int(row["to_revision"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )


__all__ = [
    "ArtifactState",
    "CreativeState",
    "DerivedJobStatus",
    "GenerationJob",
    "GenerationJobAxis",
    "GenerationJobCreateRequest",
    "GenerationJobError",
    "GenerationJobIdentityError",
    "GenerationJobRepository",
    "GenerationJobStateTuple",
    "GenerationJobTransition",
    "GenerationJobTransitionError",
    "GenerationJobTransitionResult",
    "GenerationJobTupleError",
    "GuardFact",
    "INITIAL_STATE",
    "ProviderRemoteLineage",
    "ProviderState",
    "SchedulerState",
    "TRANSITION_RULES",
    "TransitionGuardEvidence",
    "TransitionOwner",
    "TransitionRule",
    "derive_job_status",
    "derive_transition_id",
    "generation_job_logical_id",
    "resolve_transition_rule",
]
