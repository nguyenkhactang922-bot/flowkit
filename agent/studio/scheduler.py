"""IMP-053 canonical scheduler / queue / DAG / lease / admission boundary.

The scheduler does not own a second job state machine. GenerationJob.scheduler_state
from IMP-052 remains the canonical coordination authority. This module persists only
immutable DAG/scheduling metadata plus durable readiness, admission, lease and fairness
evidence, then drives the closed GenerationJob scheduler transitions.
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .generation_job import (
    ArtifactState,
    CreativeState,
    GenerationJob,
    GenerationJobAxis,
    GenerationJobRepository,
    GuardFact,
    SchedulerState,
    TransitionGuardEvidence,
    TransitionOwner,
)
from .persistence import CASConflict, SQLiteReadRepository, SQLiteWriteOwner
from .primitives import LogicalId


_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
_SHA_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class SchedulerError(RuntimeError):
    """Base IMP-053 scheduler error."""


class SchedulerIdentityError(SchedulerError):
    """Immutable scheduler metadata/identity conflict."""


class SchedulerDependencyError(SchedulerError):
    """Invalid/cyclic/missing scheduler dependency."""


class SchedulerAdmissionBlocked(SchedulerError):
    """Admission was not granted."""


class SchedulerLeaseConflict(SchedulerError):
    """Lease ownership/revision conflict."""


class DependencyRequirement(str, Enum):
    SCHEDULER_TERMINAL = "SCHEDULER_TERMINAL"
    ARTIFACT_READY = "ARTIFACT_READY"
    CREATIVE_ACCEPTED = "CREATIVE_ACCEPTED"


class LeaseState(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class LeaseEvent(str, Enum):
    ACQUIRE = "ACQUIRE"
    RENEW = "RENEW"
    RELEASE = "RELEASE"
    EXPIRE = "EXPIRE"


def _trim_token(value: str, label: str) -> str:
    value = value.strip()
    if not _TOKEN_RE.fullmatch(value):
        raise ValueError(f"{label} must be a stable token")
    return value


def _trim_text(value: str, label: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{label} must be non-empty")
    return value


def _evidence(values: tuple[str, ...]) -> tuple[str, ...]:
    result = tuple(sorted(set(value.strip() for value in values if value.strip())))
    if not result:
        raise ValueError("evidence_refs must contain at least one durable evidence reference")
    return result


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _opaque_id(prefix: str, value: Any) -> str:
    return f"{prefix}:" + hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def scheduler_dependency_edge_id(
    upstream_job_id: LogicalId,
    downstream_job_id: LogicalId,
    requirement: DependencyRequirement,
) -> str:
    return _opaque_id(
        "scheduler-dependency",
        [upstream_job_id.root, downstream_job_id.root, requirement.value],
    )


def scheduler_model_capacity_key(job: GenerationJob) -> str:
    return f"{job.provider_key}/{job.model_family}/{job.model_version}"


class SchedulerNodeRegistration(BaseModel):
    """Immutable scheduling metadata for an existing GenerationJob."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    generation_job_id: LogicalId
    priority_class: int = Field(ge=0, le=1000)
    operation_key: str
    local_resource_key: str
    estimated_cost_microunits: int = Field(ge=0)
    evidence_refs: tuple[str, ...] = Field(min_length=1)

    @field_validator("operation_key", "local_resource_key")
    @classmethod
    def normalize_tokens(cls, value: str, info) -> str:
        return _trim_token(value, info.field_name)

    @field_validator("evidence_refs")
    @classmethod
    def normalize_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _evidence(values)


class SchedulerNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    generation_job_id: LogicalId
    priority_class: int
    operation_key: str
    local_resource_key: str
    estimated_cost_microunits: int
    evidence_refs: tuple[str, ...]
    created_at: datetime


class SchedulerDependencyEdge(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dependency_edge_id: str
    upstream_job_id: LogicalId
    downstream_job_id: LogicalId
    requirement: DependencyRequirement
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    created_at: datetime

    @field_validator("evidence_refs")
    @classmethod
    def normalize_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _evidence(values)

    @model_validator(mode="after")
    def validate_identity(self) -> "SchedulerDependencyEdge":
        if self.upstream_job_id == self.downstream_job_id:
            raise ValueError("scheduler dependency cannot self-reference")
        expected = scheduler_dependency_edge_id(
            self.upstream_job_id,
            self.downstream_job_id,
            self.requirement,
        )
        if self.dependency_edge_id != expected:
            raise ValueError("dependency_edge_id does not match exact immutable edge")
        return self


class SchedulerCheckpoint(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    generation_job_id: LogicalId
    dependency_ready: bool
    blocked_dependency_ids: tuple[str, ...]
    dependency_digest: str
    ready_since: datetime | None = None
    last_evaluated_at: datetime
    last_admission_decision_id: str | None = None
    revision: int = Field(ge=0)

    @field_validator("blocked_dependency_ids")
    @classmethod
    def normalize_blocked(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(sorted(set(value.strip() for value in values if value.strip())))
        return cleaned

    @field_validator("dependency_digest")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        if not _SHA_RE.fullmatch(value):
            raise ValueError("dependency_digest must be sha256:<64 lowercase hex>")
        return value

    @model_validator(mode="after")
    def validate_ready(self) -> "SchedulerCheckpoint":
        if self.dependency_ready and self.blocked_dependency_ids:
            raise ValueError("ready checkpoint cannot retain blocked dependencies")
        if self.dependency_ready and self.ready_since is None:
            raise ValueError("ready checkpoint requires ready_since")
        if not self.dependency_ready and self.ready_since is not None:
            raise ValueError("blocked checkpoint cannot retain ready_since")
        return self


class SchedulerLease(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    generation_job_id: LogicalId
    lease_token: str
    worker_id: str
    state: LeaseState
    acquired_at: datetime
    expires_at: datetime
    updated_at: datetime
    revision: int = Field(ge=0)

    @field_validator("lease_token", "worker_id")
    @classmethod
    def normalize_token(cls, value: str, info) -> str:
        return _trim_token(value, info.field_name)

    @model_validator(mode="after")
    def validate_times(self) -> "SchedulerLease":
        if self.expires_at <= self.acquired_at:
            raise ValueError("lease expiry must be after acquisition")
        return self


class SchedulerAdmissionPolicy(BaseModel):
    """Evidence snapshot of dynamic admission limits; no provider caps are hard-coded."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_id: str
    global_limit: int = Field(gt=0)
    provider_limits: dict[str, int]
    model_limits: dict[str, int]
    operation_limits: dict[str, int]
    local_resource_limits: dict[str, int]
    budget_limit_microunits: int = Field(ge=0)
    budget_spent_microunits: int = Field(ge=0)
    evidence_refs: tuple[str, ...] = Field(min_length=1)

    @field_validator("policy_id")
    @classmethod
    def normalize_policy_id(cls, value: str) -> str:
        return _trim_token(value, "policy_id")

    @field_validator(
        "provider_limits",
        "model_limits",
        "operation_limits",
        "local_resource_limits",
    )
    @classmethod
    def validate_limits(cls, values: dict[str, int], info) -> dict[str, int]:
        result: dict[str, int] = {}
        for key, value in values.items():
            key = _trim_token(str(key), f"{info.field_name} key")
            if int(value) < 1:
                raise ValueError(f"{info.field_name} limits must be >= 1")
            result[key] = int(value)
        return dict(sorted(result.items()))

    @field_validator("evidence_refs")
    @classmethod
    def normalize_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _evidence(values)


class AdmissionUsage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    global_active: int = Field(ge=0)
    provider_active: int = Field(ge=0)
    model_active: int = Field(ge=0)
    operation_active: int = Field(ge=0)
    local_resource_active: int = Field(ge=0)


class SchedulerAdmissionDecision(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    decision_id: str
    generation_job_id: LogicalId
    admitted: bool
    reasons: tuple[str, ...]
    usage: AdmissionUsage
    policy: SchedulerAdmissionPolicy
    job_revision: int = Field(ge=0)
    checkpoint_revision: int = Field(ge=0)
    actor_ref: str
    reason: str
    correlation_id: str
    evidence_refs: tuple[str, ...]
    created_at: datetime

    @field_validator("actor_ref", "reason", "correlation_id")
    @classmethod
    def normalize_text(cls, value: str, info) -> str:
        return _trim_text(value, info.field_name)

    @field_validator("reasons")
    @classmethod
    def normalize_reasons(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value.strip() for value in values if value.strip())))

    @field_validator("evidence_refs")
    @classmethod
    def normalize_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _evidence(values)

    @model_validator(mode="after")
    def validate_decision(self) -> "SchedulerAdmissionDecision":
        if self.admitted and self.reasons:
            raise ValueError("admitted decision cannot contain blocking reasons")
        if not self.admitted and not self.reasons:
            raise ValueError("blocked decision requires at least one reason")
        return self


class SchedulerClaim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    job: GenerationJob
    lease: SchedulerLease
    admission: SchedulerAdmissionDecision


class SchedulerStartupReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    expired_idle_leases: tuple[LogicalId, ...]
    recovery_required_jobs: tuple[LogicalId, ...]
    reevaluated_jobs: tuple[LogicalId, ...]


class SchedulerRepository:
    """Durable provider-neutral IMP-053 scheduler coordination repository."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.reader = SQLiteReadRepository(writer.db_path)
        self.jobs = GenerationJobRepository(writer)

    async def register_node(
        self,
        registration: SchedulerNodeRegistration,
        *,
        created_at: datetime,
    ) -> SchedulerNode:
        self._aware(created_at, "created_at")
        job = await self.jobs.get_job(registration.generation_job_id)
        if job is None:
            raise SchedulerIdentityError("GenerationJob must exist before scheduler registration")
        node = SchedulerNode(
            generation_job_id=registration.generation_job_id,
            priority_class=registration.priority_class,
            operation_key=registration.operation_key,
            local_resource_key=registration.local_resource_key,
            estimated_cost_microunits=registration.estimated_cost_microunits,
            evidence_refs=registration.evidence_refs,
            created_at=created_at,
        )
        evidence_json = _json({"evidence_refs": list(node.evidence_refs)})

        async def command(tx):
            existing = await tx.fetchone(
                "SELECT * FROM studio_scheduler_node WHERE generation_job_id=?",
                (node.generation_job_id.root,),
            )
            if existing is not None:
                stored = self._node_from_row(existing)
                if stored != node:
                    raise SchedulerIdentityError("scheduler node exact replay conflicts with immutable metadata")
                return stored
            await tx.execute(
                """
                INSERT INTO studio_scheduler_node(
                    generation_job_id,priority_class,operation_key,local_resource_key,
                    estimated_cost_microunits,registration_evidence_json,created_at
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    node.generation_job_id.root,
                    node.priority_class,
                    node.operation_key,
                    node.local_resource_key,
                    node.estimated_cost_microunits,
                    evidence_json,
                    node.created_at.isoformat(),
                ),
            )
            return node

        return await self.writer.execute(command)

    async def get_node(self, job_id: LogicalId) -> SchedulerNode | None:
        row = await self.reader.fetchone(
            "SELECT * FROM studio_scheduler_node WHERE generation_job_id=?",
            (job_id.root,),
        )
        return None if row is None else self._node_from_row(row)

    async def add_dependency(
        self,
        *,
        upstream_job_id: LogicalId,
        downstream_job_id: LogicalId,
        requirement: DependencyRequirement,
        evidence_refs: tuple[str, ...],
        created_at: datetime,
    ) -> SchedulerDependencyEdge:
        self._aware(created_at, "created_at")
        evidence_refs = _evidence(evidence_refs)
        upstream = await self.jobs.get_job(upstream_job_id)
        downstream = await self.jobs.get_job(downstream_job_id)
        if upstream is None or downstream is None:
            raise SchedulerDependencyError("both dependency GenerationJobs must exist")
        if await self.get_node(upstream_job_id) is None or await self.get_node(downstream_job_id) is None:
            raise SchedulerDependencyError("both dependency jobs must be registered scheduler nodes")
        if upstream_job_id == downstream_job_id:
            raise SchedulerDependencyError("scheduler dependency cannot self-reference")
        if await self._reachable(downstream_job_id, upstream_job_id):
            raise SchedulerDependencyError("scheduler dependency would create a DAG cycle")
        edge = SchedulerDependencyEdge(
            dependency_edge_id=scheduler_dependency_edge_id(
                upstream_job_id, downstream_job_id, requirement
            ),
            upstream_job_id=upstream_job_id,
            downstream_job_id=downstream_job_id,
            requirement=requirement,
            evidence_refs=evidence_refs,
            created_at=created_at,
        )
        evidence_json = _json({"evidence_refs": list(edge.evidence_refs)})

        async def command(tx):
            existing = await tx.fetchone(
                "SELECT * FROM studio_scheduler_dependency WHERE dependency_edge_id=?",
                (edge.dependency_edge_id,),
            )
            if existing is not None:
                stored = self._dependency_from_row(existing)
                if stored != edge:
                    raise SchedulerIdentityError("scheduler dependency exact replay conflicts with immutable evidence")
                return stored
            if await self._reachable_tx(tx, downstream_job_id, upstream_job_id):
                raise SchedulerDependencyError("scheduler dependency would create a DAG cycle")
            await tx.execute(
                """
                INSERT INTO studio_scheduler_dependency(
                    dependency_edge_id,upstream_job_id,downstream_job_id,requirement,evidence_json,created_at
                ) VALUES (?,?,?,?,?,?)
                """,
                (
                    edge.dependency_edge_id,
                    edge.upstream_job_id.root,
                    edge.downstream_job_id.root,
                    edge.requirement.value,
                    evidence_json,
                    edge.created_at.isoformat(),
                ),
            )
            return edge

        return await self.writer.execute(command)

    async def list_dependencies(self, downstream_job_id: LogicalId) -> list[SchedulerDependencyEdge]:
        rows = await self.reader.fetchall(
            "SELECT * FROM studio_scheduler_dependency WHERE downstream_job_id=? ORDER BY dependency_edge_id",
            (downstream_job_id.root,),
        )
        return [self._dependency_from_row(row) for row in rows]

    async def get_checkpoint(self, job_id: LogicalId) -> SchedulerCheckpoint | None:
        row = await self.reader.fetchone(
            "SELECT * FROM studio_scheduler_checkpoint WHERE generation_job_id=?",
            (job_id.root,),
        )
        return None if row is None else self._checkpoint_from_row(row)

    async def evaluate_readiness(
        self,
        *,
        job_id: LogicalId,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> SchedulerCheckpoint:
        self._event_inputs(actor_ref, reason, correlation_id, recorded_at, evidence_refs)
        job = await self.jobs.get_job(job_id)
        if job is None:
            raise SchedulerIdentityError("GenerationJob does not exist")
        if await self.get_node(job_id) is None:
            raise SchedulerIdentityError("GenerationJob is not registered with scheduler")
        dependencies = await self.list_dependencies(job_id)
        states: list[dict[str, str]] = []
        blocked: list[str] = []
        for edge in dependencies:
            upstream = await self.jobs.get_job(edge.upstream_job_id)
            if upstream is None:
                blocked.append(edge.dependency_edge_id)
                states.append({"edge": edge.dependency_edge_id, "state": "MISSING"})
                continue
            satisfied = self._requirement_satisfied(edge.requirement, upstream)
            states.append(
                {
                    "edge": edge.dependency_edge_id,
                    "scheduler": upstream.scheduler_state.value,
                    "artifact": upstream.artifact_state.value,
                    "creative": upstream.creative_state.value,
                    "satisfied": str(satisfied).lower(),
                }
            )
            if not satisfied:
                blocked.append(edge.dependency_edge_id)
        digest = _hash(states)
        checkpoint = await self._persist_checkpoint(
            job_id=job_id,
            dependency_ready=not blocked,
            blocked_dependency_ids=tuple(blocked),
            dependency_digest=digest,
            recorded_at=recorded_at,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            evidence_refs=evidence_refs,
        )
        latest = await self.jobs.get_job(job_id)
        assert latest is not None
        guard = TransitionGuardEvidence(
            summary="scheduler dependency readiness evaluation",
            evidence_refs=evidence_refs,
            facts=(
                GuardFact(key="dependency_ready", value=checkpoint.dependency_ready),
                GuardFact(key="checkpoint_revision", value=checkpoint.revision),
            ),
        )
        if not checkpoint.dependency_ready and latest.scheduler_state is SchedulerState.QUEUED:
            result = await self.jobs.transition(
                job_id=job_id,
                axis=GenerationJobAxis.SCHEDULER,
                command="EVALUATE_DEPENDENCIES",
                owner=TransitionOwner.SCHEDULER,
                guard_evidence=guard,
                expected_revision=latest.revision,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                recorded_at=recorded_at,
            )
            latest = result.job
        elif checkpoint.dependency_ready and latest.scheduler_state is SchedulerState.WAITING_DEPENDENCY:
            await self.jobs.transition(
                job_id=job_id,
                axis=GenerationJobAxis.SCHEDULER,
                command="DEPENDENCIES_READY",
                owner=TransitionOwner.SCHEDULER,
                guard_evidence=guard,
                expected_revision=latest.revision,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                recorded_at=recorded_at,
            )
        return checkpoint

    async def evaluate_admission(
        self,
        *,
        job_id: LogicalId,
        policy: SchedulerAdmissionPolicy,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> SchedulerAdmissionDecision:
        self._event_inputs(actor_ref, reason, correlation_id, recorded_at, evidence_refs)
        job = await self.jobs.get_job(job_id)
        node = await self.get_node(job_id)
        checkpoint = await self.get_checkpoint(job_id)
        if job is None or node is None or checkpoint is None:
            raise SchedulerAdmissionBlocked("scheduler node/readiness checkpoint is missing")
        if not checkpoint.dependency_ready:
            raise SchedulerAdmissionBlocked("dependencies are not ready")
        usage = await self._active_usage(job, node, recorded_at)
        decision = self._build_admission_decision(
            job=job,
            node=node,
            checkpoint=checkpoint,
            policy=policy,
            usage=usage,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            evidence_refs=evidence_refs,
            recorded_at=recorded_at,
        )
        await self._persist_admission(decision)
        checkpoint = await self._set_last_admission(
            checkpoint,
            decision.decision_id,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            evidence_refs=evidence_refs,
            recorded_at=recorded_at,
        )
        latest = await self.jobs.get_job(job_id)
        assert latest is not None
        guard = TransitionGuardEvidence(
            summary="scheduler hierarchical admission decision",
            evidence_refs=evidence_refs,
            facts=(
                GuardFact(key="admitted", value=decision.admitted),
                GuardFact(key="checkpoint_revision", value=checkpoint.revision),
            ),
        )
        if not decision.admitted and latest.scheduler_state is SchedulerState.QUEUED:
            await self.jobs.transition(
                job_id=job_id,
                axis=GenerationJobAxis.SCHEDULER,
                command="EVALUATE_ADMISSION",
                owner=TransitionOwner.SCHEDULER,
                guard_evidence=guard,
                expected_revision=latest.revision,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                recorded_at=recorded_at,
            )
        elif decision.admitted and latest.scheduler_state is SchedulerState.WAITING_CAPACITY:
            await self.jobs.transition(
                job_id=job_id,
                axis=GenerationJobAxis.SCHEDULER,
                command="CAPACITY_AVAILABLE",
                owner=TransitionOwner.SCHEDULER,
                guard_evidence=guard,
                expected_revision=latest.revision,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                recorded_at=recorded_at,
            )
        return decision

    async def claim_next(
        self,
        *,
        policy: SchedulerAdmissionPolicy,
        worker_id: str,
        lease_ttl_seconds: int,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> SchedulerClaim | None:
        worker_id = _trim_token(worker_id, "worker_id")
        if lease_ttl_seconds < 1:
            raise SchedulerLeaseConflict("lease_ttl_seconds must be >= 1")
        self._event_inputs(actor_ref, reason, correlation_id, recorded_at, evidence_refs)
        candidates = await self._ordered_ready_candidates(recorded_at)
        for job_id in candidates:
            reserved = await self._reserve_if_admitted(
                job_id=job_id,
                policy=policy,
                worker_id=worker_id,
                lease_ttl_seconds=lease_ttl_seconds,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                recorded_at=recorded_at,
                evidence_refs=evidence_refs,
            )
            if reserved is None:
                continue
            lease, decision, expected_job_revision = reserved
            guard = TransitionGuardEvidence(
                summary="scheduler lease/admission claim",
                evidence_refs=evidence_refs,
                facts=(
                    GuardFact(key="admitted", value=True),
                    GuardFact(key="active_lease", value=True),
                    GuardFact(key="lease_revision", value=lease.revision),
                ),
            )
            try:
                transitioned = await self.jobs.transition(
                    job_id=job_id,
                    axis=GenerationJobAxis.SCHEDULER,
                    command="CLAIM",
                    owner=TransitionOwner.SCHEDULER,
                    guard_evidence=guard,
                    expected_revision=expected_job_revision,
                    actor_ref=actor_ref,
                    reason=reason,
                    correlation_id=correlation_id,
                    recorded_at=recorded_at,
                )
            except Exception:
                await self.release_lease(
                    job_id=job_id,
                    lease_token=lease.lease_token,
                    worker_id=worker_id,
                    actor_ref=actor_ref,
                    reason="claim transition failed; release reserved lease",
                    correlation_id=correlation_id,
                    recorded_at=recorded_at,
                    evidence_refs=evidence_refs,
                )
                raise
            return SchedulerClaim(job=transitioned.job, lease=lease, admission=decision)
        return None

    async def start_work(
        self,
        *,
        job_id: LogicalId,
        lease_token: str,
        worker_id: str,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> GenerationJob:
        self._event_inputs(actor_ref, reason, correlation_id, recorded_at, evidence_refs)
        lease = await self.get_lease(job_id)
        if lease is None or lease.state is not LeaseState.ACTIVE:
            raise SchedulerLeaseConflict("START_WORK requires active lease")
        if lease.lease_token != lease_token or lease.worker_id != worker_id:
            raise SchedulerLeaseConflict("START_WORK lease token/worker mismatch")
        if lease.expires_at <= recorded_at:
            raise SchedulerLeaseConflict("START_WORK lease has expired")
        job = await self.jobs.get_job(job_id)
        if job is None or job.scheduler_state is not SchedulerState.CLAIMED:
            raise SchedulerLeaseConflict("START_WORK requires GenerationJob CLAIMED")
        result = await self.jobs.transition(
            job_id=job_id,
            axis=GenerationJobAxis.SCHEDULER,
            command="START_WORK",
            owner=TransitionOwner.WORKER_COORDINATOR,
            guard_evidence=TransitionGuardEvidence(
                summary="worker starts work under active scheduler lease",
                evidence_refs=evidence_refs,
                facts=(
                    GuardFact(key="active_lease", value=True),
                    GuardFact(key="lease_revision", value=lease.revision),
                ),
            ),
            expected_revision=job.revision,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            recorded_at=recorded_at,
        )
        return result.job

    async def get_lease(self, job_id: LogicalId) -> SchedulerLease | None:
        row = await self.reader.fetchone(
            "SELECT * FROM studio_scheduler_lease WHERE generation_job_id=?",
            (job_id.root,),
        )
        return None if row is None else self._lease_from_row(row)

    async def renew_lease(
        self,
        *,
        job_id: LogicalId,
        lease_token: str,
        worker_id: str,
        lease_ttl_seconds: int,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> SchedulerLease:
        if lease_ttl_seconds < 1:
            raise SchedulerLeaseConflict("lease_ttl_seconds must be >= 1")
        self._event_inputs(actor_ref, reason, correlation_id, recorded_at, evidence_refs)
        return await self._mutate_lease(
            job_id=job_id,
            lease_token=lease_token,
            worker_id=worker_id,
            event=LeaseEvent.RENEW,
            new_expires_at=recorded_at + timedelta(seconds=lease_ttl_seconds),
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            recorded_at=recorded_at,
            evidence_refs=evidence_refs,
        )

    async def release_lease(
        self,
        *,
        job_id: LogicalId,
        lease_token: str,
        worker_id: str,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> SchedulerLease:
        self._event_inputs(actor_ref, reason, correlation_id, recorded_at, evidence_refs)
        return await self._mutate_lease(
            job_id=job_id,
            lease_token=lease_token,
            worker_id=worker_id,
            event=LeaseEvent.RELEASE,
            new_expires_at=None,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            recorded_at=recorded_at,
            evidence_refs=evidence_refs,
        )

    async def expire_stale_leases(
        self,
        *,
        recorded_at: datetime,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        evidence_refs: tuple[str, ...],
    ) -> tuple[tuple[LogicalId, ...], tuple[LogicalId, ...]]:
        self._event_inputs(actor_ref, reason, correlation_id, recorded_at, evidence_refs)
        rows = await self.reader.fetchall(
            "SELECT * FROM studio_scheduler_lease WHERE state='ACTIVE' AND expires_at<=? ORDER BY generation_job_id",
            (recorded_at.isoformat(),),
        )
        idle: list[LogicalId] = []
        recovery: list[LogicalId] = []
        for row in rows:
            lease = self._lease_from_row(row)
            await self._mutate_lease(
                job_id=lease.generation_job_id,
                lease_token=lease.lease_token,
                worker_id=lease.worker_id,
                event=LeaseEvent.EXPIRE,
                new_expires_at=None,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                recorded_at=recorded_at,
                evidence_refs=evidence_refs,
            )
            job = await self.jobs.get_job(lease.generation_job_id)
            if job is not None and job.scheduler_state in {SchedulerState.CLAIMED, SchedulerState.RUNNING}:
                recovery.append(lease.generation_job_id)
            else:
                idle.append(lease.generation_job_id)
        return tuple(idle), tuple(recovery)

    async def recover_startup(
        self,
        *,
        recorded_at: datetime,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        evidence_refs: tuple[str, ...],
    ) -> SchedulerStartupReport:
        idle, recovery = await self.expire_stale_leases(
            recorded_at=recorded_at,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            evidence_refs=evidence_refs,
        )
        rows = await self.reader.fetchall(
            """
            SELECT n.generation_job_id
            FROM studio_scheduler_node n
            JOIN studio_generation_job j ON j.generation_job_id=n.generation_job_id
            WHERE j.scheduler_state != 'TERMINAL'
            ORDER BY n.generation_job_id
            """
        )
        reevaluated: list[LogicalId] = []
        for row in rows:
            job_id = LogicalId(str(row["generation_job_id"]))
            job = await self.jobs.get_job(job_id)
            if job is None or job.scheduler_state in {SchedulerState.CLAIMED, SchedulerState.RUNNING, SchedulerState.WAITING_RECOVERY}:
                continue
            await self.evaluate_readiness(
                job_id=job_id,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                recorded_at=recorded_at,
                evidence_refs=evidence_refs,
            )
            reevaluated.append(job_id)
        return SchedulerStartupReport(
            expired_idle_leases=idle,
            recovery_required_jobs=recovery,
            reevaluated_jobs=tuple(reevaluated),
        )

    async def _reserve_if_admitted(
        self,
        *,
        job_id: LogicalId,
        policy: SchedulerAdmissionPolicy,
        worker_id: str,
        lease_ttl_seconds: int,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> tuple[SchedulerLease, SchedulerAdmissionDecision, int] | None:
        evidence_refs = _evidence(evidence_refs)
        lease_token = _trim_token("lease-" + secrets.token_hex(16), "lease_token")

        async def command(tx):
            job_row = await tx.fetchone(
                "SELECT * FROM studio_generation_job WHERE generation_job_id=?",
                (job_id.root,),
            )
            node_row = await tx.fetchone(
                "SELECT * FROM studio_scheduler_node WHERE generation_job_id=?",
                (job_id.root,),
            )
            checkpoint_row = await tx.fetchone(
                "SELECT * FROM studio_scheduler_checkpoint WHERE generation_job_id=?",
                (job_id.root,),
            )
            if job_row is None or node_row is None or checkpoint_row is None:
                return None
            job = self.jobs._job_from_row(job_row)
            node = self._node_from_row(node_row)
            checkpoint = self._checkpoint_from_row(checkpoint_row)
            if job.scheduler_state is not SchedulerState.QUEUED or not checkpoint.dependency_ready:
                return None
            if not await self._dependencies_ready_tx(tx, job_id):
                return None
            usage = await self._active_usage_tx(tx, job, node, recorded_at)
            decision = self._build_admission_decision(
                job=job,
                node=node,
                checkpoint=checkpoint,
                policy=policy,
                usage=usage,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                evidence_refs=evidence_refs,
                recorded_at=recorded_at,
            )
            await self._insert_admission_tx(tx, decision)
            if not decision.admitted:
                return None
            current_lease = await tx.fetchone(
                "SELECT * FROM studio_scheduler_lease WHERE generation_job_id=?",
                (job_id.root,),
            )
            if current_lease is not None:
                existing = self._lease_from_row(current_lease)
                if existing.state is LeaseState.ACTIVE and existing.expires_at > recorded_at:
                    return None
                if existing.state is LeaseState.ACTIVE:
                    await self._lease_update_tx(
                        tx,
                        existing,
                        event=LeaseEvent.EXPIRE,
                        lease_token=existing.lease_token,
                        worker_id=existing.worker_id,
                        new_expires_at=None,
                        actor_ref=actor_ref,
                        reason="expire stale lease before safe reacquire",
                        correlation_id=correlation_id,
                        recorded_at=recorded_at,
                        evidence_refs=evidence_refs,
                    )
                    current_lease = await tx.fetchone(
                        "SELECT * FROM studio_scheduler_lease WHERE generation_job_id=?",
                        (job_id.root,),
                    )
                    assert current_lease is not None
                    existing = self._lease_from_row(current_lease)
                lease = await self._lease_update_tx(
                    tx,
                    existing,
                    event=LeaseEvent.ACQUIRE,
                    lease_token=lease_token,
                    worker_id=worker_id,
                    new_expires_at=recorded_at + timedelta(seconds=lease_ttl_seconds),
                    actor_ref=actor_ref,
                    reason=reason,
                    correlation_id=correlation_id,
                    recorded_at=recorded_at,
                    evidence_refs=evidence_refs,
                )
            else:
                lease = SchedulerLease(
                    generation_job_id=job_id,
                    lease_token=lease_token,
                    worker_id=worker_id,
                    state=LeaseState.ACTIVE,
                    acquired_at=recorded_at,
                    expires_at=recorded_at + timedelta(seconds=lease_ttl_seconds),
                    updated_at=recorded_at,
                    revision=0,
                )
                await tx.execute(
                    """
                    INSERT INTO studio_scheduler_lease(
                        generation_job_id,lease_token,worker_id,state,acquired_at,expires_at,updated_at,revision
                    ) VALUES (?,?,?,?,?,?,?,0)
                    """,
                    (
                        job_id.root, lease.lease_token, lease.worker_id, lease.state.value,
                        lease.acquired_at.isoformat(), lease.expires_at.isoformat(), lease.updated_at.isoformat(),
                    ),
                )
                await self._insert_lease_history_tx(
                    tx,
                    lease=lease,
                    event=LeaseEvent.ACQUIRE,
                    previous_expires_at=None,
                    from_revision=-1,
                    actor_ref=actor_ref,
                    reason=reason,
                    correlation_id=correlation_id,
                    evidence_refs=evidence_refs,
                    recorded_at=recorded_at,
                )
            await self._update_fairness_tx(
                tx,
                priority_class=node.priority_class,
                project_id=job.project_id,
                recorded_at=recorded_at,
            )
            await self._set_last_admission_tx(
                tx,
                checkpoint,
                decision.decision_id,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                evidence_refs=evidence_refs,
                recorded_at=recorded_at,
            )
            return lease, decision, job.revision

        return await self.writer.execute(command)

    @staticmethod
    def _fair_order_rows(
        rows: list[Any],
        last_project_by_priority: dict[int, str | None],
    ) -> list[LogicalId]:
        """Priority -> durable project round-robin -> oldest-ready ordering."""
        by_priority: dict[int, list[Any]] = defaultdict(list)
        for row in rows:
            by_priority[int(row["priority_class"])].append(row)
        ordered: list[LogicalId] = []
        for priority in sorted(by_priority):
            project_rows: dict[str, list[Any]] = defaultdict(list)
            for row in by_priority[priority]:
                project_rows[str(row["project_id"])].append(row)
            projects = sorted(
                project_rows,
                key=lambda pid: min(str(r["ready_since"]) for r in project_rows[pid]),
            )
            last_project = last_project_by_priority.get(priority)
            if last_project in projects:
                index = projects.index(last_project) + 1
                projects = projects[index:] + projects[:index]
            max_depth = max((len(project_rows[p]) for p in projects), default=0)
            for offset in range(max_depth):
                for project_id in projects:
                    items = sorted(
                        project_rows[project_id],
                        key=lambda r: (str(r["ready_since"]), str(r["generation_job_id"])),
                    )
                    if offset < len(items):
                        ordered.append(LogicalId(str(items[offset]["generation_job_id"])))
        return ordered

    async def _ordered_ready_candidates(self, recorded_at: datetime) -> list[LogicalId]:
        rows = await self.reader.fetchall(
            """
            SELECT n.generation_job_id,n.priority_class,c.ready_since,j.project_id
            FROM studio_scheduler_node n
            JOIN studio_scheduler_checkpoint c ON c.generation_job_id=n.generation_job_id
            JOIN studio_generation_job j ON j.generation_job_id=n.generation_job_id
            LEFT JOIN studio_scheduler_lease l ON l.generation_job_id=n.generation_job_id
            WHERE c.dependency_ready=1
              AND j.scheduler_state='QUEUED'
              AND (l.generation_job_id IS NULL OR l.state!='ACTIVE' OR l.expires_at<=?)
            ORDER BY n.priority_class,c.ready_since,n.generation_job_id
            """,
            (recorded_at.isoformat(),),
        )
        cursor_rows = await self.reader.fetchall(
            "SELECT priority_class,last_project_id FROM studio_scheduler_fairness_cursor"
        )
        cursors = {
            int(row["priority_class"]): (
                None if row["last_project_id"] is None else str(row["last_project_id"])
            )
            for row in cursor_rows
        }
        return self._fair_order_rows(rows, cursors)

    async def _active_usage(
        self, job: GenerationJob, node: SchedulerNode, recorded_at: datetime
    ) -> AdmissionUsage:
        rows = await self.reader.fetchall(
            """
            SELECT j.provider_key,j.model_family,j.model_version,n.operation_key,n.local_resource_key
            FROM studio_scheduler_lease l
            JOIN studio_scheduler_node n ON n.generation_job_id=l.generation_job_id
            JOIN studio_generation_job j ON j.generation_job_id=l.generation_job_id
            WHERE l.state='ACTIVE' AND l.expires_at>?
            """,
            (recorded_at.isoformat(),),
        )
        return self._usage_from_rows(rows, job, node)

    async def _active_usage_tx(self, tx, job, node, recorded_at) -> AdmissionUsage:
        rows = await tx.fetchall(
            """
            SELECT j.provider_key,j.model_family,j.model_version,n.operation_key,n.local_resource_key
            FROM studio_scheduler_lease l
            JOIN studio_scheduler_node n ON n.generation_job_id=l.generation_job_id
            JOIN studio_generation_job j ON j.generation_job_id=l.generation_job_id
            WHERE l.state='ACTIVE' AND l.expires_at>?
            """,
            (recorded_at.isoformat(),),
        )
        return self._usage_from_rows(rows, job, node)

    @staticmethod
    def _usage_from_rows(rows, job: GenerationJob, node: SchedulerNode) -> AdmissionUsage:
        model_key = scheduler_model_capacity_key(job)
        provider = model = operation = resource = 0
        for row in rows:
            if str(row["provider_key"]) == job.provider_key:
                provider += 1
            row_model = f"{row['provider_key']}/{row['model_family']}/{row['model_version']}"
            if row_model == model_key:
                model += 1
            if str(row["operation_key"]) == node.operation_key:
                operation += 1
            if str(row["local_resource_key"]) == node.local_resource_key:
                resource += 1
        return AdmissionUsage(
            global_active=len(rows),
            provider_active=provider,
            model_active=model,
            operation_active=operation,
            local_resource_active=resource,
        )

    def _build_admission_decision(
        self,
        *,
        job: GenerationJob,
        node: SchedulerNode,
        checkpoint: SchedulerCheckpoint,
        policy: SchedulerAdmissionPolicy,
        usage: AdmissionUsage,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        evidence_refs: tuple[str, ...],
        recorded_at: datetime,
    ) -> SchedulerAdmissionDecision:
        reasons: list[str] = []
        model_key = scheduler_model_capacity_key(job)
        checks = (
            ("GLOBAL_CAPACITY", usage.global_active, policy.global_limit),
            ("PROVIDER_CAPACITY", usage.provider_active, policy.provider_limits.get(job.provider_key)),
            ("MODEL_CAPACITY", usage.model_active, policy.model_limits.get(model_key)),
            ("OPERATION_CAPACITY", usage.operation_active, policy.operation_limits.get(node.operation_key)),
            (
                "LOCAL_RESOURCE_CAPACITY",
                usage.local_resource_active,
                policy.local_resource_limits.get(node.local_resource_key),
            ),
        )
        for label, active, limit in checks:
            if limit is None:
                reasons.append(f"MISSING_{label}")
            elif active >= limit:
                reasons.append(label)
        if policy.budget_spent_microunits + node.estimated_cost_microunits > policy.budget_limit_microunits:
            reasons.append("BUDGET_CAPACITY")
        payload = {
            "job_id": job.generation_job_id.root,
            "job_revision": job.revision,
            "checkpoint_revision": checkpoint.revision,
            "policy": policy.model_dump(mode="json"),
            "usage": usage.model_dump(mode="json"),
            "estimate": node.estimated_cost_microunits,
            "created_at": recorded_at.isoformat(),
            "correlation_id": correlation_id,
        }
        return SchedulerAdmissionDecision(
            decision_id=_opaque_id("scheduler-admission", payload),
            generation_job_id=job.generation_job_id,
            admitted=not reasons,
            reasons=tuple(reasons),
            usage=usage,
            policy=policy,
            job_revision=job.revision,
            checkpoint_revision=checkpoint.revision,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            evidence_refs=_evidence(tuple(policy.evidence_refs) + tuple(evidence_refs)),
            created_at=recorded_at,
        )

    async def _persist_admission(self, decision: SchedulerAdmissionDecision) -> None:
        async def command(tx):
            await self._insert_admission_tx(tx, decision)
        await self.writer.execute(command)

    async def _insert_admission_tx(self, tx, decision: SchedulerAdmissionDecision) -> None:
        existing = await tx.fetchone(
            "SELECT * FROM studio_scheduler_admission WHERE decision_id=?",
            (decision.decision_id,),
        )
        if existing is not None:
            stored = self._admission_from_row(existing)
            if stored != decision:
                raise SchedulerIdentityError("admission decision id conflicts with persisted evidence")
            return
        await tx.execute(
            """
            INSERT INTO studio_scheduler_admission(
                decision_id,generation_job_id,admitted,reasons_json,snapshot_json,
                job_revision,checkpoint_revision,actor_ref,reason,correlation_id,evidence_json,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                decision.decision_id,
                decision.generation_job_id.root,
                int(decision.admitted),
                _json(list(decision.reasons)),
                _json(
                    {
                        "usage": decision.usage.model_dump(mode="json"),
                        "policy": decision.policy.model_dump(mode="json"),
                    }
                ),
                decision.job_revision,
                decision.checkpoint_revision,
                decision.actor_ref,
                decision.reason,
                decision.correlation_id,
                _json({"evidence_refs": list(decision.evidence_refs)}),
                decision.created_at.isoformat(),
            ),
        )

    async def _persist_checkpoint(
        self,
        *,
        job_id: LogicalId,
        dependency_ready: bool,
        blocked_dependency_ids: tuple[str, ...],
        dependency_digest: str,
        recorded_at: datetime,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        evidence_refs: tuple[str, ...],
    ) -> SchedulerCheckpoint:
        evidence_refs = _evidence(evidence_refs)

        async def command(tx):
            row = await tx.fetchone(
                "SELECT * FROM studio_scheduler_checkpoint WHERE generation_job_id=?",
                (job_id.root,),
            )
            if row is None:
                checkpoint = SchedulerCheckpoint(
                    generation_job_id=job_id,
                    dependency_ready=dependency_ready,
                    blocked_dependency_ids=blocked_dependency_ids,
                    dependency_digest=dependency_digest,
                    ready_since=recorded_at if dependency_ready else None,
                    last_evaluated_at=recorded_at,
                    last_admission_decision_id=None,
                    revision=0,
                )
                await tx.execute(
                    """
                    INSERT INTO studio_scheduler_checkpoint(
                        generation_job_id,dependency_ready,blocked_dependencies_json,dependency_digest,
                        ready_since,last_evaluated_at,last_admission_decision_id,revision
                    ) VALUES (?,?,?,?,?,?,NULL,0)
                    """,
                    (
                        job_id.root,
                        int(checkpoint.dependency_ready),
                        _json(list(checkpoint.blocked_dependency_ids)),
                        checkpoint.dependency_digest,
                        None if checkpoint.ready_since is None else checkpoint.ready_since.isoformat(),
                        checkpoint.last_evaluated_at.isoformat(),
                    ),
                )
                await self._insert_checkpoint_history_tx(
                    tx,
                    checkpoint=checkpoint,
                    from_revision=-1,
                    actor_ref=actor_ref,
                    reason=reason,
                    correlation_id=correlation_id,
                    evidence_refs=evidence_refs,
                    recorded_at=recorded_at,
                )
                return checkpoint
            old = self._checkpoint_from_row(row)
            ready_since = old.ready_since if old.dependency_ready and dependency_ready else (
                recorded_at if dependency_ready else None
            )
            new_revision = await tx.cas_update(
                table="studio_scheduler_checkpoint",
                pk_column="generation_job_id",
                pk_value=job_id.root,
                expected_revision=old.revision,
                changes={
                    "dependency_ready": int(dependency_ready),
                    "blocked_dependencies_json": _json(list(blocked_dependency_ids)),
                    "dependency_digest": dependency_digest,
                    "ready_since": None if ready_since is None else ready_since.isoformat(),
                    "last_evaluated_at": recorded_at.isoformat(),
                    "last_admission_decision_id": old.last_admission_decision_id,
                },
            )
            checkpoint = SchedulerCheckpoint(
                generation_job_id=job_id,
                dependency_ready=dependency_ready,
                blocked_dependency_ids=blocked_dependency_ids,
                dependency_digest=dependency_digest,
                ready_since=ready_since,
                last_evaluated_at=recorded_at,
                last_admission_decision_id=old.last_admission_decision_id,
                revision=new_revision,
            )
            await self._insert_checkpoint_history_tx(
                tx,
                checkpoint=checkpoint,
                from_revision=old.revision,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                evidence_refs=evidence_refs,
                recorded_at=recorded_at,
            )
            return checkpoint

        return await self.writer.execute(command)

    async def _set_last_admission(
        self,
        checkpoint: SchedulerCheckpoint,
        decision_id: str,
        **event,
    ) -> SchedulerCheckpoint:
        async def command(tx):
            return await self._set_last_admission_tx(tx, checkpoint, decision_id, **event)
        return await self.writer.execute(command)

    async def _set_last_admission_tx(
        self,
        tx,
        checkpoint: SchedulerCheckpoint,
        decision_id: str,
        *,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        evidence_refs: tuple[str, ...],
        recorded_at: datetime,
    ) -> SchedulerCheckpoint:
        row = await tx.fetchone(
            "SELECT * FROM studio_scheduler_checkpoint WHERE generation_job_id=?",
            (checkpoint.generation_job_id.root,),
        )
        if row is None:
            raise SchedulerIdentityError("scheduler checkpoint disappeared")
        current = self._checkpoint_from_row(row)
        if current.revision != checkpoint.revision:
            raise CASConflict("stale scheduler checkpoint while attaching admission evidence")
        new_revision = await tx.cas_update(
            table="studio_scheduler_checkpoint",
            pk_column="generation_job_id",
            pk_value=checkpoint.generation_job_id.root,
            expected_revision=current.revision,
            changes={
                "dependency_ready": int(current.dependency_ready),
                "blocked_dependencies_json": _json(list(current.blocked_dependency_ids)),
                "dependency_digest": current.dependency_digest,
                "ready_since": None if current.ready_since is None else current.ready_since.isoformat(),
                "last_evaluated_at": current.last_evaluated_at.isoformat(),
                "last_admission_decision_id": decision_id,
            },
        )
        updated = current.model_copy(
            update={"last_admission_decision_id": decision_id, "revision": new_revision}
        )
        await self._insert_checkpoint_history_tx(
            tx,
            checkpoint=updated,
            from_revision=current.revision,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            evidence_refs=evidence_refs,
            recorded_at=recorded_at,
        )
        return updated

    async def _insert_checkpoint_history_tx(
        self,
        tx,
        *,
        checkpoint: SchedulerCheckpoint,
        from_revision: int,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        evidence_refs: tuple[str, ...],
        recorded_at: datetime,
    ) -> None:
        event_id = _opaque_id(
            "scheduler-checkpoint-event",
            [checkpoint.generation_job_id.root, checkpoint.revision, checkpoint.dependency_digest, checkpoint.last_admission_decision_id],
        )
        await tx.execute(
            """
            INSERT INTO studio_scheduler_checkpoint_history(
                checkpoint_event_id,generation_job_id,dependency_ready,blocked_dependencies_json,
                dependency_digest,ready_since,last_admission_decision_id,from_revision,to_revision,
                actor_ref,reason,correlation_id,evidence_json,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                event_id,
                checkpoint.generation_job_id.root,
                int(checkpoint.dependency_ready),
                _json(list(checkpoint.blocked_dependency_ids)),
                checkpoint.dependency_digest,
                None if checkpoint.ready_since is None else checkpoint.ready_since.isoformat(),
                checkpoint.last_admission_decision_id,
                from_revision,
                checkpoint.revision,
                actor_ref,
                reason,
                correlation_id,
                _json({"evidence_refs": list(_evidence(evidence_refs))}),
                recorded_at.isoformat(),
            ),
        )

    async def _mutate_lease(
        self,
        *,
        job_id: LogicalId,
        lease_token: str,
        worker_id: str,
        event: LeaseEvent,
        new_expires_at: datetime | None,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> SchedulerLease:
        lease_token = _trim_token(lease_token, "lease_token")
        worker_id = _trim_token(worker_id, "worker_id")
        evidence_refs = _evidence(evidence_refs)

        async def command(tx):
            row = await tx.fetchone(
                "SELECT * FROM studio_scheduler_lease WHERE generation_job_id=?",
                (job_id.root,),
            )
            if row is None:
                raise SchedulerLeaseConflict("scheduler lease does not exist")
            current = self._lease_from_row(row)
            if current.lease_token != lease_token or current.worker_id != worker_id:
                raise SchedulerLeaseConflict("lease token/worker mismatch")
            return await self._lease_update_tx(
                tx,
                current,
                event=event,
                lease_token=lease_token,
                worker_id=worker_id,
                new_expires_at=new_expires_at,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                recorded_at=recorded_at,
                evidence_refs=evidence_refs,
            )

        return await self.writer.execute(command)

    async def _lease_update_tx(
        self,
        tx,
        current: SchedulerLease,
        *,
        event: LeaseEvent,
        lease_token: str,
        worker_id: str,
        new_expires_at: datetime | None,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> SchedulerLease:
        if event is LeaseEvent.RENEW:
            if current.state is not LeaseState.ACTIVE or current.expires_at <= recorded_at:
                raise SchedulerLeaseConflict("cannot renew inactive/expired lease")
            assert new_expires_at is not None and new_expires_at > recorded_at
            state = LeaseState.ACTIVE
            acquired_at = current.acquired_at
            expires_at = new_expires_at
        elif event is LeaseEvent.RELEASE:
            if current.state is LeaseState.RELEASED:
                return current
            if current.state is not LeaseState.ACTIVE:
                raise SchedulerLeaseConflict("only active lease can be released")
            state = LeaseState.RELEASED
            acquired_at = current.acquired_at
            expires_at = current.expires_at
        elif event is LeaseEvent.EXPIRE:
            if current.state is LeaseState.EXPIRED:
                return current
            if current.state is not LeaseState.ACTIVE or current.expires_at > recorded_at:
                raise SchedulerLeaseConflict("only elapsed active lease can expire")
            state = LeaseState.EXPIRED
            acquired_at = current.acquired_at
            expires_at = current.expires_at
        elif event is LeaseEvent.ACQUIRE:
            if current.state is LeaseState.ACTIVE:
                raise SchedulerLeaseConflict("active lease cannot be acquired twice")
            assert new_expires_at is not None and new_expires_at > recorded_at
            state = LeaseState.ACTIVE
            acquired_at = recorded_at
            expires_at = new_expires_at
        else:  # pragma: no cover
            raise SchedulerLeaseConflict("unsupported lease event")
        new_revision = await tx.cas_update(
            table="studio_scheduler_lease",
            pk_column="generation_job_id",
            pk_value=current.generation_job_id.root,
            expected_revision=current.revision,
            changes={
                "lease_token": lease_token,
                "worker_id": worker_id,
                "state": state.value,
                "acquired_at": acquired_at.isoformat(),
                "expires_at": expires_at.isoformat(),
                "updated_at": recorded_at.isoformat(),
            },
        )
        updated = SchedulerLease(
            generation_job_id=current.generation_job_id,
            lease_token=lease_token,
            worker_id=worker_id,
            state=state,
            acquired_at=acquired_at,
            expires_at=expires_at,
            updated_at=recorded_at,
            revision=new_revision,
        )
        await self._insert_lease_history_tx(
            tx,
            lease=updated,
            event=event,
            previous_expires_at=current.expires_at,
            from_revision=current.revision,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            evidence_refs=evidence_refs,
            recorded_at=recorded_at,
        )
        return updated

    async def _insert_lease_history_tx(
        self,
        tx,
        *,
        lease: SchedulerLease,
        event: LeaseEvent,
        previous_expires_at: datetime | None,
        from_revision: int,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        evidence_refs: tuple[str, ...],
        recorded_at: datetime,
    ) -> None:
        event_id = _opaque_id(
            "scheduler-lease-event",
            [lease.generation_job_id.root, lease.revision, event.value, lease.lease_token],
        )
        await tx.execute(
            """
            INSERT INTO studio_scheduler_lease_history(
                lease_event_id,generation_job_id,lease_token,worker_id,event,
                previous_expires_at,new_expires_at,from_revision,to_revision,
                actor_ref,reason,correlation_id,evidence_json,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                event_id,
                lease.generation_job_id.root,
                lease.lease_token,
                lease.worker_id,
                event.value,
                None if previous_expires_at is None else previous_expires_at.isoformat(),
                lease.expires_at.isoformat(),
                from_revision,
                lease.revision,
                actor_ref,
                reason,
                correlation_id,
                _json({"evidence_refs": list(_evidence(evidence_refs))}),
                recorded_at.isoformat(),
            ),
        )

    async def _update_fairness_tx(
        self, tx, *, priority_class: int, project_id: LogicalId, recorded_at: datetime
    ) -> None:
        row = await tx.fetchone(
            "SELECT * FROM studio_scheduler_fairness_cursor WHERE priority_class=?",
            (priority_class,),
        )
        if row is None:
            await tx.execute(
                "INSERT INTO studio_scheduler_fairness_cursor(priority_class,last_project_id,revision,updated_at) VALUES (?,?,0,?)",
                (priority_class, project_id.root, recorded_at.isoformat()),
            )
            return
        await tx.cas_update(
            table="studio_scheduler_fairness_cursor",
            pk_column="priority_class",
            pk_value=priority_class,
            expected_revision=int(row["revision"]),
            changes={"last_project_id": project_id.root, "updated_at": recorded_at.isoformat()},
        )

    async def _dependencies_ready_tx(self, tx, job_id: LogicalId) -> bool:
        edges = await tx.fetchall(
            "SELECT * FROM studio_scheduler_dependency WHERE downstream_job_id=? ORDER BY dependency_edge_id",
            (job_id.root,),
        )
        for edge in edges:
            row = await tx.fetchone(
                "SELECT * FROM studio_generation_job WHERE generation_job_id=?",
                (str(edge["upstream_job_id"]),),
            )
            if row is None:
                return False
            job = self.jobs._job_from_row(row)
            if not self._requirement_satisfied(
                DependencyRequirement(str(edge["requirement"])), job
            ):
                return False
        return True

    async def _reachable_tx(self, tx, start: LogicalId, target: LogicalId) -> bool:
        queue: deque[LogicalId] = deque([start])
        seen: set[str] = set()
        while queue:
            current = queue.popleft()
            if current == target:
                return True
            if current.root in seen:
                continue
            seen.add(current.root)
            rows = await tx.fetchall(
                "SELECT downstream_job_id FROM studio_scheduler_dependency WHERE upstream_job_id=?",
                (current.root,),
            )
            queue.extend(LogicalId(str(row["downstream_job_id"])) for row in rows)
        return False

    async def _reachable(self, start: LogicalId, target: LogicalId) -> bool:
        queue: deque[LogicalId] = deque([start])
        seen: set[str] = set()
        while queue:
            current = queue.popleft()
            if current == target:
                return True
            if current.root in seen:
                continue
            seen.add(current.root)
            rows = await self.reader.fetchall(
                "SELECT downstream_job_id FROM studio_scheduler_dependency WHERE upstream_job_id=?",
                (current.root,),
            )
            queue.extend(LogicalId(str(row["downstream_job_id"])) for row in rows)
        return False

    @staticmethod
    def _requirement_satisfied(requirement: DependencyRequirement, job: GenerationJob) -> bool:
        if requirement is DependencyRequirement.SCHEDULER_TERMINAL:
            return job.scheduler_state is SchedulerState.TERMINAL
        if requirement is DependencyRequirement.ARTIFACT_READY:
            return job.artifact_state is ArtifactState.READY
        if requirement is DependencyRequirement.CREATIVE_ACCEPTED:
            return job.creative_state in {CreativeState.APPROVED, CreativeState.LOCKED}
        return False

    @staticmethod
    def _event_inputs(
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> None:
        _trim_text(actor_ref, "actor_ref")
        _trim_text(reason, "reason")
        _trim_text(correlation_id, "correlation_id")
        SchedulerRepository._aware(recorded_at, "recorded_at")
        _evidence(evidence_refs)

    @staticmethod
    def _aware(value: datetime, label: str) -> None:
        if value.tzinfo is None:
            raise SchedulerError(f"{label} must be timezone-aware")

    @staticmethod
    def _node_from_row(row) -> SchedulerNode:
        evidence = json.loads(str(row["registration_evidence_json"]))
        return SchedulerNode(
            generation_job_id=LogicalId(str(row["generation_job_id"])),
            priority_class=int(row["priority_class"]),
            operation_key=str(row["operation_key"]),
            local_resource_key=str(row["local_resource_key"]),
            estimated_cost_microunits=int(row["estimated_cost_microunits"]),
            evidence_refs=tuple(evidence.get("evidence_refs", ())),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )

    @staticmethod
    def _dependency_from_row(row) -> SchedulerDependencyEdge:
        evidence = json.loads(str(row["evidence_json"]))
        return SchedulerDependencyEdge(
            dependency_edge_id=str(row["dependency_edge_id"]),
            upstream_job_id=LogicalId(str(row["upstream_job_id"])),
            downstream_job_id=LogicalId(str(row["downstream_job_id"])),
            requirement=DependencyRequirement(str(row["requirement"])),
            evidence_refs=tuple(evidence.get("evidence_refs", ())),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )

    @staticmethod
    def _checkpoint_from_row(row) -> SchedulerCheckpoint:
        return SchedulerCheckpoint(
            generation_job_id=LogicalId(str(row["generation_job_id"])),
            dependency_ready=bool(int(row["dependency_ready"])),
            blocked_dependency_ids=tuple(json.loads(str(row["blocked_dependencies_json"]))),
            dependency_digest=str(row["dependency_digest"]),
            ready_since=None if row["ready_since"] is None else datetime.fromisoformat(str(row["ready_since"])),
            last_evaluated_at=datetime.fromisoformat(str(row["last_evaluated_at"])),
            last_admission_decision_id=None if row["last_admission_decision_id"] is None else str(row["last_admission_decision_id"]),
            revision=int(row["revision"]),
        )

    @staticmethod
    def _lease_from_row(row) -> SchedulerLease:
        return SchedulerLease(
            generation_job_id=LogicalId(str(row["generation_job_id"])),
            lease_token=str(row["lease_token"]),
            worker_id=str(row["worker_id"]),
            state=LeaseState(str(row["state"])),
            acquired_at=datetime.fromisoformat(str(row["acquired_at"])),
            expires_at=datetime.fromisoformat(str(row["expires_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
            revision=int(row["revision"]),
        )

    @staticmethod
    def _admission_from_row(row) -> SchedulerAdmissionDecision:
        snapshot = json.loads(str(row["snapshot_json"]))
        evidence = json.loads(str(row["evidence_json"]))
        return SchedulerAdmissionDecision(
            decision_id=str(row["decision_id"]),
            generation_job_id=LogicalId(str(row["generation_job_id"])),
            admitted=bool(int(row["admitted"])),
            reasons=tuple(json.loads(str(row["reasons_json"]))),
            usage=AdmissionUsage.model_validate(snapshot["usage"]),
            policy=SchedulerAdmissionPolicy.model_validate(snapshot["policy"]),
            job_revision=int(row["job_revision"]),
            checkpoint_revision=int(row["checkpoint_revision"]),
            actor_ref=str(row["actor_ref"]),
            reason=str(row["reason"]),
            correlation_id=str(row["correlation_id"]),
            evidence_refs=tuple(evidence.get("evidence_refs", ())),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )


__all__ = [
    "AdmissionUsage",
    "DependencyRequirement",
    "LeaseEvent",
    "LeaseState",
    "SchedulerAdmissionBlocked",
    "SchedulerAdmissionDecision",
    "SchedulerAdmissionPolicy",
    "SchedulerCheckpoint",
    "SchedulerClaim",
    "SchedulerDependencyEdge",
    "SchedulerDependencyError",
    "SchedulerError",
    "SchedulerIdentityError",
    "SchedulerLease",
    "SchedulerLeaseConflict",
    "SchedulerNode",
    "SchedulerNodeRegistration",
    "SchedulerRepository",
    "SchedulerStartupReport",
    "scheduler_dependency_edge_id",
    "scheduler_model_capacity_key",
]
