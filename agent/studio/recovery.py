"""IMP-054 retry/resume and remote-ambiguity recovery.

GenerationJob remains the sole mutable job-state authority.  This module owns
provider-neutral recovery policy plus immutable RecoveryEvent proof/history.
It never treats timeout/transport failure as permission to resubmit paid work.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .generation_job import (
    GenerationJob,
    GenerationJobAxis,
    GenerationJobIdentityError,
    GenerationJobRepository,
    GuardFact,
    ProviderRemoteLineage,
    ProviderState,
    SchedulerState,
    TransitionGuardEvidence,
    TransitionOwner,
)
from .observability import ErrorClass, RetryDisposition, redact_text
from .persistence import SQLiteReadRepository, SQLiteWriteOwner
from .primitives import LogicalId, VersionRef
from .provider_adapter import (
    ProviderAdapterPort,
    ProviderHandleKind,
    ProviderObservationState,
    ProviderTransportHandle,
    ProviderTransportObservation,
)


def _trimmed(value: str, label: str) -> str:
    value = str(value).strip()
    if not value:
        raise ValueError(f"{label} must be non-empty")
    return value


def _event_id(job_id: LogicalId, attempt_id: str) -> str:
    digest = hashlib.sha256(f"{job_id.root}|{attempt_id}".encode("utf-8")).hexdigest()
    return f"recovery-event:{digest}"


class RecoveryError(RuntimeError):
    """Base IMP-054 recovery error."""


class RecoveryGateBlocked(RecoveryError):
    """Recovery/retry was requested without the proof required by authority."""


class RecoveryEvidenceConflict(RecoveryError):
    """A recovery attempt identity was replayed with different immutable truth."""


class RecoveryTrigger(str, Enum):
    PRE_DISPATCH_FAILURE = "PRE_DISPATCH_FAILURE"
    SUBMIT_RESPONSE_LOST = "SUBMIT_RESPONSE_LOST"
    PROCESS_CRASH = "PROCESS_CRASH"
    POLL_TIMEOUT = "POLL_TIMEOUT"
    RESTART = "RESTART"
    CANCELLATION_RACE = "CANCELLATION_RACE"
    MANUAL_RECONCILE = "MANUAL_RECONCILE"


class RecoveryProbeOutcome(str, Enum):
    PROVEN_NOT_SUBMITTED = "PROVEN_NOT_SUBMITTED"
    PROVEN_ABSENT = "PROVEN_ABSENT"
    VERIFIED_SAME_JOB_IDEMPOTENCY = "VERIFIED_SAME_JOB_IDEMPOTENCY"
    RECOVERED_HANDLE = "RECOVERED_HANDLE"
    RECOVERED_ACTIVE_POLL = "RECOVERED_ACTIVE_POLL"
    REMOTE_SUCCEEDED = "REMOTE_SUCCEEDED"
    REMOTE_FAILED = "REMOTE_FAILED"
    REMOTE_CANCELED = "REMOTE_CANCELED"
    STILL_AMBIGUOUS = "STILL_AMBIGUOUS"


class RecoveryProofKind(str, Enum):
    NONE = "NONE"
    TRANSPORT_NOT_DISPATCHED = "TRANSPORT_NOT_DISPATCHED"
    PROVEN_ABSENT = "PROVEN_ABSENT"
    VERIFIED_SAME_JOB_IDEMPOTENCY = "VERIFIED_SAME_JOB_IDEMPOTENCY"
    RECOVERED_HANDLE = "RECOVERED_HANDLE"
    RECOVERED_ACTIVE_POLL = "RECOVERED_ACTIVE_POLL"
    REMOTE_SUCCEEDED = "REMOTE_SUCCEEDED"
    REMOTE_FAILED = "REMOTE_FAILED"
    REMOTE_CANCELED = "REMOTE_CANCELED"
    STILL_AMBIGUOUS = "STILL_AMBIGUOUS"


class RecoveryDecision(str, Enum):
    SAFE_TO_REQUEUE = "SAFE_TO_REQUEUE"
    RESUME_EXISTING = "RESUME_EXISTING"
    HOLD_AMBIGUOUS = "HOLD_AMBIGUOUS"
    TERMINAL_OBSERVED = "TERMINAL_OBSERVED"
    NO_ACTION = "NO_ACTION"


class RecoveryFailureClassification(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    error_code: str
    error_class: ErrorClass
    retry_disposition: RetryDisposition

    @field_validator("error_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        value = _trimmed(value, "error_code").upper()
        if value == "FAILED":
            raise ValueError('generic error code "FAILED" is forbidden')
        return value

    @model_validator(mode="after")
    def ambiguity_requires_reconciliation(self) -> "RecoveryFailureClassification":
        if (
            self.error_class is ErrorClass.PROVIDER_AMBIGUITY
            and self.retry_disposition is not RetryDisposition.RECONCILIATION_REQUIRED
        ):
            raise ValueError("provider ambiguity must require reconciliation")
        return self


class RecoveryProbeResult(BaseModel):
    """Provider-neutral reconciliation result backed by explicit evidence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    outcome: RecoveryProbeOutcome
    strategy: str
    observed_at: datetime
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    handle: ProviderTransportHandle | None = None
    observation: ProviderTransportObservation | None = None
    message: str | None = None

    @field_validator("strategy")
    @classmethod
    def normalize_strategy(cls, value: str) -> str:
        return _trimmed(value, "strategy")

    @field_validator("evidence_refs")
    @classmethod
    def normalize_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(sorted(set(_trimmed(value, "evidence_ref") for value in values)))
        if not cleaned:
            raise ValueError("recovery result requires evidence")
        return cleaned

    @field_validator("message", mode="before")
    @classmethod
    def redact_message(cls, value):
        if value is None:
            return None
        return redact_text(_trimmed(str(value), "message"))

    @model_validator(mode="after")
    def validate_outcome(self) -> "RecoveryProbeResult":
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        requires_handle = {
            RecoveryProbeOutcome.RECOVERED_HANDLE,
            RecoveryProbeOutcome.RECOVERED_ACTIVE_POLL,
            RecoveryProbeOutcome.REMOTE_SUCCEEDED,
            RecoveryProbeOutcome.REMOTE_FAILED,
            RecoveryProbeOutcome.REMOTE_CANCELED,
        }
        if self.outcome in requires_handle and self.handle is None:
            raise ValueError(f"{self.outcome.value} requires recovered remote handle")
        if self.outcome in {
            RecoveryProbeOutcome.PROVEN_NOT_SUBMITTED,
            RecoveryProbeOutcome.PROVEN_ABSENT,
            RecoveryProbeOutcome.VERIFIED_SAME_JOB_IDEMPOTENCY,
        } and self.handle is not None:
            raise ValueError("absence/idempotency proof cannot bind a new remote handle")
        return self


class RecoveryEvent(BaseModel):
    """Append-only proof/decision history; never a second GenerationJob state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    recovery_event_id: str
    recovery_attempt_id: str
    generation_job_id: LogicalId
    job_revision_observed: int = Field(ge=0)
    trigger: RecoveryTrigger
    strategy: str
    failure: RecoveryFailureClassification
    proof_kind: RecoveryProofKind
    decision: RecoveryDecision
    provider_profile_ref: VersionRef
    rule_version: str
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    observation: ProviderTransportObservation | None = None
    recovered_provider_request_id: str | None = None
    recovered_provider_operation_id: str | None = None
    actor_ref: str
    reason: str
    correlation_id: str
    created_at: datetime

    @field_validator(
        "recovery_event_id",
        "recovery_attempt_id",
        "strategy",
        "rule_version",
        "actor_ref",
        "reason",
        "correlation_id",
    )
    @classmethod
    def normalize_required(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("evidence_refs")
    @classmethod
    def normalize_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(sorted(set(_trimmed(value, "evidence_ref") for value in values)))
        if not cleaned:
            raise ValueError("RecoveryEvent requires evidence")
        return cleaned

    @field_validator("recovered_provider_request_id", "recovered_provider_operation_id")
    @classmethod
    def normalize_optional(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_event(self) -> "RecoveryEvent":
        if self.created_at.tzinfo is None:
            raise ValueError("RecoveryEvent created_at must be timezone-aware")
        if self.recovery_event_id != _event_id(self.generation_job_id, self.recovery_attempt_id):
            raise ValueError("recovery_event_id does not match job/attempt identity")
        if self.decision is RecoveryDecision.SAFE_TO_REQUEUE and self.proof_kind not in {
            RecoveryProofKind.TRANSPORT_NOT_DISPATCHED,
            RecoveryProofKind.PROVEN_ABSENT,
            RecoveryProofKind.VERIFIED_SAME_JOB_IDEMPOTENCY,
        }:
            raise ValueError("SAFE_TO_REQUEUE requires explicit absence/idempotency proof")
        if self.decision is RecoveryDecision.HOLD_AMBIGUOUS and self.proof_kind is not RecoveryProofKind.STILL_AMBIGUOUS:
            raise ValueError("HOLD_AMBIGUOUS requires STILL_AMBIGUOUS proof")
        return self


class RecoveryResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    job: GenerationJob
    event: RecoveryEvent


@runtime_checkable
class RecoveryProbePort(Protocol):
    async def reconcile(
        self,
        job: GenerationJob,
        *,
        observed_at: datetime,
    ) -> RecoveryProbeResult:
        ...


class ProviderAdapterRecoveryProbe:
    """Adapter wrapper for HANDLE_ONLY provider reconciliation.

    It never invents PROVEN_ABSENT.  Without a durable handle, existing Flow/Omni
    adapters return AMBIGUOUS and this wrapper maps that to STILL_AMBIGUOUS.
    """

    def __init__(
        self,
        adapter: ProviderAdapterPort,
        *,
        handle_kind: ProviderHandleKind = ProviderHandleKind.OPERATION,
        project_handle: str | None = None,
    ) -> None:
        self.adapter = adapter
        self.handle_kind = handle_kind
        self.project_handle = project_handle

    async def reconcile(self, job: GenerationJob, *, observed_at: datetime) -> RecoveryProbeResult:
        handle_id = job.provider_operation_id or job.provider_request_id
        handle = None
        if handle_id is not None:
            handle = ProviderTransportHandle(
                provider_key=job.provider_key,
                kind=self.handle_kind,
                handle_id=handle_id,
                project_handle=self.project_handle,
            )
        observation = await self.adapter.reconcile(handle, observed_at=observed_at)
        if observation.provider_key != job.provider_key:
            raise RecoveryGateBlocked("provider reconciliation returned different provider identity")
        mapping = {
            ProviderObservationState.ACCEPTED: RecoveryProbeOutcome.RECOVERED_HANDLE,
            ProviderObservationState.PENDING: RecoveryProbeOutcome.RECOVERED_ACTIVE_POLL,
            ProviderObservationState.SUCCEEDED: RecoveryProbeOutcome.REMOTE_SUCCEEDED,
            ProviderObservationState.FAILED: RecoveryProbeOutcome.REMOTE_FAILED,
            ProviderObservationState.CANCELLED: RecoveryProbeOutcome.REMOTE_CANCELED,
            ProviderObservationState.AMBIGUOUS: RecoveryProbeOutcome.STILL_AMBIGUOUS,
            ProviderObservationState.UNSUPPORTED: RecoveryProbeOutcome.STILL_AMBIGUOUS,
        }
        outcome = mapping[observation.state]
        safe = _safe_observation_dict(observation)
        digest_payload = dict(safe)
        if observation.output_url is not None:
            digest_payload["output_url_sha256"] = hashlib.sha256(
                observation.output_url.encode("utf-8")
            ).hexdigest()
        digest = hashlib.sha256(
            json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        persisted_observation = None
        if not (
            observation.state is ProviderObservationState.SUCCEEDED
            and observation.output_media_id is None
            and observation.output_url is not None
        ):
            persisted_observation = ProviderTransportObservation.model_validate(safe)
        return RecoveryProbeResult(
            outcome=outcome,
            strategy="provider_handle_reconcile",
            observed_at=observed_at,
            evidence_refs=(f"provider-reconcile:{digest}",),
            handle=observation.handle,
            observation=persisted_observation,
            message=observation.message,
        )


class RecoveryEventRepository:
    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.reader = SQLiteReadRepository(writer.db_path)

    async def get_attempt(self, job_id: LogicalId, attempt_id: str) -> RecoveryEvent | None:
        row = await self.reader.fetchone(
            """
            SELECT * FROM studio_generation_recovery_event
            WHERE generation_job_id=? AND recovery_attempt_id=?
            """,
            (job_id.root, _trimmed(attempt_id, "recovery_attempt_id")),
        )
        return None if row is None else self._from_row(row)

    async def list_for_job(self, job_id: LogicalId) -> list[RecoveryEvent]:
        rows = await self.reader.fetchall(
            """
            SELECT * FROM studio_generation_recovery_event
            WHERE generation_job_id=? ORDER BY created_at,recovery_event_id
            """,
            (job_id.root,),
        )
        return [self._from_row(row) for row in rows]

    async def append(self, event: RecoveryEvent) -> RecoveryEvent:
        async def command(tx):
            existing = await tx.fetchone(
                "SELECT * FROM studio_generation_recovery_event WHERE recovery_event_id=?",
                (event.recovery_event_id,),
            )
            if existing is not None:
                stored = self._from_row(existing)
                if stored != event:
                    raise RecoveryEvidenceConflict(
                        "recovery attempt identity already exists with different immutable evidence"
                    )
                return stored
            await tx.execute(
                """
                INSERT INTO studio_generation_recovery_event (
                    recovery_event_id,recovery_attempt_id,generation_job_id,job_revision_observed,
                    trigger,strategy,failure_code,failure_class,retry_disposition,
                    proof_kind,decision,provider_profile_object_id,provider_profile_version,
                    rule_version,evidence_json,observation_json,
                    recovered_provider_request_id,recovered_provider_operation_id,
                    actor_ref,reason,correlation_id,created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    event.recovery_event_id,
                    event.recovery_attempt_id,
                    event.generation_job_id.root,
                    event.job_revision_observed,
                    event.trigger.value,
                    event.strategy,
                    event.failure.error_code,
                    event.failure.error_class.value,
                    event.failure.retry_disposition.value,
                    event.proof_kind.value,
                    event.decision.value,
                    event.provider_profile_ref.logical_id.root,
                    event.provider_profile_ref.version_id.root,
                    event.rule_version,
                    json.dumps({"evidence_refs": list(event.evidence_refs)}, sort_keys=True, separators=(",", ":")),
                    None if event.observation is None else json.dumps(_safe_observation_dict(event.observation), sort_keys=True, separators=(",", ":")),
                    event.recovered_provider_request_id,
                    event.recovered_provider_operation_id,
                    event.actor_ref,
                    event.reason,
                    event.correlation_id,
                    event.created_at.isoformat(),
                ),
            )
            return event

        return await self.writer.execute(command)

    @staticmethod
    def _from_row(row) -> RecoveryEvent:
        evidence = json.loads(str(row["evidence_json"]))
        observation_raw = row["observation_json"]
        observation = None
        if observation_raw is not None:
            observation = ProviderTransportObservation.model_validate(json.loads(str(observation_raw)))
        return RecoveryEvent(
            recovery_event_id=str(row["recovery_event_id"]),
            recovery_attempt_id=str(row["recovery_attempt_id"]),
            generation_job_id=LogicalId(str(row["generation_job_id"])),
            job_revision_observed=int(row["job_revision_observed"]),
            trigger=RecoveryTrigger(str(row["trigger"])),
            strategy=str(row["strategy"]),
            failure=RecoveryFailureClassification(
                error_code=str(row["failure_code"]),
                error_class=ErrorClass(str(row["failure_class"])),
                retry_disposition=RetryDisposition(str(row["retry_disposition"])),
            ),
            proof_kind=RecoveryProofKind(str(row["proof_kind"])),
            decision=RecoveryDecision(str(row["decision"])),
            provider_profile_ref=VersionRef(
                logical_id=LogicalId(str(row["provider_profile_object_id"])),
                version_id=str(row["provider_profile_version"]),
            ),
            rule_version=str(row["rule_version"]),
            evidence_refs=tuple(str(value) for value in evidence["evidence_refs"]),
            observation=observation,
            recovered_provider_request_id=row["recovered_provider_request_id"],
            recovered_provider_operation_id=row["recovered_provider_operation_id"],
            actor_ref=str(row["actor_ref"]),
            reason=str(row["reason"]),
            correlation_id=str(row["correlation_id"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )


class RecoveryCoordinator:
    RULE_VERSION = "imp054-recovery-v1"

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.jobs = GenerationJobRepository(writer)
        self.events = RecoveryEventRepository(writer)
        self.reader = SQLiteReadRepository(writer.db_path)

    async def list_startup_candidates(self) -> list[GenerationJob]:
        rows = await self.reader.fetchall(
            """
            SELECT generation_job_id FROM studio_generation_job
            WHERE scheduler_state='WAITING_RECOVERY'
               OR provider_state IN (
                   'SUBMITTING','SUBMITTED','POLLING','UNKNOWN_REMOTE_STATE',
                   'RECONCILING','AMBIGUOUS_HOLD','CANCEL_REQUESTED'
               )
            ORDER BY created_at,generation_job_id
            """
        )
        jobs: list[GenerationJob] = []
        for row in rows:
            job = await self.jobs.get_job(LogicalId(str(row["generation_job_id"])))
            if job is not None:
                jobs.append(job)
        return jobs

    async def recover_pre_dispatch(
        self,
        *,
        job_id: LogicalId,
        recovery_attempt_id: str,
        expected_revision: int,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> RecoveryResult:
        existing = await self.events.get_attempt(job_id, recovery_attempt_id)
        if existing is not None:
            return await self._finalize_event(existing)
        job = await self._require_job(job_id, expected_revision)
        if job.provider_state is not ProviderState.NOT_SUBMITTED:
            raise RecoveryGateBlocked("pre-dispatch proof requires provider NOT_SUBMITTED")
        history = await self.jobs.list_transitions(job_id)
        if any(
            item.axis is GenerationJobAxis.PROVIDER and item.command == "SUBMIT"
            for item in history
        ):
            raise RecoveryGateBlocked(
                "cannot claim transport-not-dispatched after durable SUBMIT transition"
            )
        job = await self._hold_scheduler_if_needed(
            job,
            evidence_refs=evidence_refs,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            recorded_at=recorded_at,
        )
        event = RecoveryEvent(
            recovery_event_id=_event_id(job_id, recovery_attempt_id),
            recovery_attempt_id=recovery_attempt_id,
            generation_job_id=job_id,
            job_revision_observed=job.revision,
            trigger=RecoveryTrigger.PRE_DISPATCH_FAILURE,
            strategy="durable_transition_history",
            failure=RecoveryFailureClassification(
                error_code="TRANSPORT_NOT_DISPATCHED",
                error_class=ErrorClass.PROVIDER_TRANSPORT,
                retry_disposition=RetryDisposition.RETRYABLE,
            ),
            proof_kind=RecoveryProofKind.TRANSPORT_NOT_DISPATCHED,
            decision=RecoveryDecision.SAFE_TO_REQUEUE,
            provider_profile_ref=job.provider_profile_ref,
            rule_version=self.RULE_VERSION,
            evidence_refs=evidence_refs,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            created_at=recorded_at,
        )
        event = await self.events.append(event)
        return await self._finalize_event(event)

    async def recover(
        self,
        *,
        job_id: LogicalId,
        recovery_attempt_id: str,
        trigger: RecoveryTrigger,
        probe: RecoveryProbePort,
        expected_revision: int,
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
        evidence_refs: tuple[str, ...],
    ) -> RecoveryResult:
        existing = await self.events.get_attempt(job_id, recovery_attempt_id)
        if existing is not None:
            return await self._finalize_event(existing)
        job = await self._require_job(job_id, expected_revision)
        if job.provider_state is ProviderState.NOT_SUBMITTED:
            raise RecoveryGateBlocked(
                "NOT_SUBMITTED recovery requires explicit pre-dispatch/absence proof path"
            )
        cancellation_path = job.provider_state is ProviderState.CANCEL_REQUESTED
        if not cancellation_path:
            job = await self._hold_scheduler_if_needed(
                job,
                evidence_refs=evidence_refs,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                recorded_at=recorded_at,
            )
            job = await self._enter_reconciling(
                job,
                trigger=trigger,
                evidence_refs=evidence_refs,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                recorded_at=recorded_at,
            )
        result = await probe.reconcile(job, observed_at=recorded_at)
        self._validate_probe_result(job, result)
        failure = _classify_failure(trigger, result)
        proof_kind, decision = _proof_and_decision(result.outcome)
        merged_evidence = tuple(sorted(set(evidence_refs + result.evidence_refs)))
        handle = result.handle
        event = RecoveryEvent(
            recovery_event_id=_event_id(job_id, recovery_attempt_id),
            recovery_attempt_id=recovery_attempt_id,
            generation_job_id=job_id,
            job_revision_observed=job.revision,
            trigger=trigger,
            strategy=result.strategy,
            failure=failure,
            proof_kind=proof_kind,
            decision=decision,
            provider_profile_ref=job.provider_profile_ref,
            rule_version=self.RULE_VERSION,
            evidence_refs=merged_evidence,
            observation=result.observation,
            recovered_provider_request_id=(
                handle.handle_id if handle is not None and handle.kind is ProviderHandleKind.WORKFLOW else None
            ),
            recovered_provider_operation_id=(
                handle.handle_id if handle is not None and handle.kind is ProviderHandleKind.OPERATION else None
            ),
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            created_at=recorded_at,
        )
        event = await self.events.append(event)
        return await self._finalize_event(event)

    async def _require_job(self, job_id: LogicalId, expected_revision: int) -> GenerationJob:
        job = await self.jobs.get_job(job_id)
        if job is None:
            raise GenerationJobIdentityError("GenerationJob does not exist")
        if job.revision != expected_revision:
            raise RecoveryGateBlocked(
                f"stale recovery revision; expected {expected_revision}, actual {job.revision}"
            )
        return job

    async def _hold_scheduler_if_needed(
        self,
        job: GenerationJob,
        *,
        evidence_refs: tuple[str, ...],
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
    ) -> GenerationJob:
        command = None
        if job.scheduler_state is SchedulerState.CLAIMED:
            command = "LEASE_OR_RESTART_RECOVERY"
        elif job.scheduler_state is SchedulerState.RUNNING:
            command = "REMOTE_OR_LEASE_RECOVERY_REQUIRED"
        elif job.scheduler_state is SchedulerState.WAITING_RECOVERY:
            return job
        elif job.provider_state not in {ProviderState.NOT_SUBMITTED}:
            raise RecoveryGateBlocked(
                "remote recovery requires scheduler CLAIMED/RUNNING/WAITING_RECOVERY"
            )
        if command is None:
            return job
        result = await self.jobs.transition(
            job_id=job.generation_job_id,
            axis=GenerationJobAxis.SCHEDULER,
            command=command,
            owner=TransitionOwner.RECOVERY_COORDINATOR,
            guard_evidence=_guard(
                evidence_refs,
                recovery_required=True,
                provider_state=job.provider_state.value,
            ),
            expected_revision=job.revision,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            recorded_at=recorded_at,
        )
        return result.job

    async def _enter_reconciling(
        self,
        job: GenerationJob,
        *,
        trigger: RecoveryTrigger,
        evidence_refs: tuple[str, ...],
        actor_ref: str,
        reason: str,
        correlation_id: str,
        recorded_at: datetime,
    ) -> GenerationJob:
        command = {
            ProviderState.SUBMITTING: "ACCEPTANCE_AMBIGUOUS",
            ProviderState.UNKNOWN_REMOTE_STATE: "BEGIN_RECONCILE",
            ProviderState.SUBMITTED: "RECOVERY_SCAN",
            ProviderState.POLLING: "RECOVERY_SCAN",
            ProviderState.AMBIGUOUS_HOLD: "RECONCILE_AGAIN",
            ProviderState.RECONCILING: None,
        }.get(job.provider_state)
        if job.provider_state is ProviderState.SUBMITTING:
            result = await self.jobs.transition(
                job_id=job.generation_job_id,
                axis=GenerationJobAxis.PROVIDER,
                command="ACCEPTANCE_AMBIGUOUS",
                owner=TransitionOwner.RECOVERY_COORDINATOR,
                guard_evidence=_guard(
                    evidence_refs,
                    side_effect_may_have_occurred=True,
                    trigger=trigger.value,
                ),
                expected_revision=job.revision,
                actor_ref=actor_ref,
                reason=reason,
                correlation_id=correlation_id,
                recorded_at=recorded_at,
            )
            job = result.job
            command = "BEGIN_RECONCILE"
        if command is None:
            if job.provider_state is not ProviderState.RECONCILING:
                raise RecoveryGateBlocked(
                    f"provider state {job.provider_state.value} is not recoverable by ambiguity coordinator"
                )
            return job
        result = await self.jobs.transition(
            job_id=job.generation_job_id,
            axis=GenerationJobAxis.PROVIDER,
            command=command,
            owner=TransitionOwner.RECOVERY_COORDINATOR,
            guard_evidence=_guard(evidence_refs, recovery_scan=True, trigger=trigger.value),
            expected_revision=job.revision,
            actor_ref=actor_ref,
            reason=reason,
            correlation_id=correlation_id,
            recorded_at=recorded_at,
        )
        return result.job

    def _validate_probe_result(self, job: GenerationJob, result: RecoveryProbeResult) -> None:
        if result.handle is not None and result.handle.provider_key != job.provider_key:
            raise RecoveryGateBlocked("recovered handle belongs to different provider")
        if (
            result.outcome is RecoveryProbeOutcome.VERIFIED_SAME_JOB_IDEMPOTENCY
            and job.idempotency_key is None
        ):
            raise RecoveryGateBlocked("same-job idempotency proof requires durable job idempotency_key")
        if (
            result.outcome is RecoveryProbeOutcome.REMOTE_CANCELED
            and job.provider_state is not ProviderState.CANCEL_REQUESTED
        ):
            raise RecoveryGateBlocked(
                "REMOTE_CANCELED proof requires prior local CANCEL_REQUESTED state"
            )


    async def _finalize_event(self, event: RecoveryEvent) -> RecoveryResult:
        job = await self.jobs.get_job(event.generation_job_id)
        if job is None:
            raise GenerationJobIdentityError("GenerationJob does not exist")
        evidence = event.evidence_refs

        if job.provider_state is ProviderState.CANCEL_REQUESTED:
            cancel_command = {
                RecoveryProofKind.REMOTE_CANCELED: "CANCEL_CONFIRMED",
                RecoveryProofKind.REMOTE_SUCCEEDED: "REMOTE_SUCCESS_WON_RACE",
                RecoveryProofKind.REMOTE_FAILED: "REMOTE_FAILURE_WON_RACE",
            }.get(event.proof_kind)
            if cancel_command is not None:
                result = await self.jobs.transition(
                    job_id=job.generation_job_id,
                    axis=GenerationJobAxis.PROVIDER,
                    command=cancel_command,
                    owner=TransitionOwner.PROVIDER_ADAPTER,
                    guard_evidence=_guard(evidence, recovery_event_id=event.recovery_event_id),
                    expected_revision=job.revision,
                    actor_ref=event.actor_ref,
                    reason=event.reason,
                    correlation_id=event.correlation_id,
                    recorded_at=event.created_at,
                )
                job = result.job
            return RecoveryResult(job=job, event=event)

        if event.decision is RecoveryDecision.SAFE_TO_REQUEUE:
            if job.provider_state is ProviderState.RECONCILING:
                facts = _proof_facts(event.proof_kind)
                result = await self.jobs.transition(
                    job_id=job.generation_job_id,
                    axis=GenerationJobAxis.PROVIDER,
                    command="PROVEN_ABSENT",
                    owner=TransitionOwner.RECOVERY_COORDINATOR,
                    guard_evidence=_guard(evidence, **facts),
                    expected_revision=job.revision,
                    actor_ref=event.actor_ref,
                    reason=event.reason,
                    correlation_id=event.correlation_id,
                    recorded_at=event.created_at,
                )
                job = result.job
            if job.provider_state is not ProviderState.NOT_SUBMITTED:
                raise RecoveryGateBlocked("safe requeue proof did not resolve provider to NOT_SUBMITTED")
            if job.scheduler_state is SchedulerState.WAITING_RECOVERY:
                facts = _proof_facts(event.proof_kind)
                result = await self.jobs.transition(
                    job_id=job.generation_job_id,
                    axis=GenerationJobAxis.SCHEDULER,
                    command="RECOVERY_PROVEN_SAFE_TO_REQUEUE",
                    owner=TransitionOwner.RECOVERY_COORDINATOR,
                    guard_evidence=_guard(evidence, **facts),
                    expected_revision=job.revision,
                    actor_ref=event.actor_ref,
                    reason=event.reason,
                    correlation_id=event.correlation_id,
                    recorded_at=event.created_at,
                )
                job = result.job
            return RecoveryResult(job=job, event=event)

        if event.decision is RecoveryDecision.HOLD_AMBIGUOUS:
            if job.provider_state is ProviderState.RECONCILING:
                result = await self.jobs.transition(
                    job_id=job.generation_job_id,
                    axis=GenerationJobAxis.PROVIDER,
                    command="STILL_AMBIGUOUS",
                    owner=TransitionOwner.RECOVERY_COORDINATOR,
                    guard_evidence=_guard(evidence, ambiguity_unresolved=True),
                    expected_revision=job.revision,
                    actor_ref=event.actor_ref,
                    reason=event.reason,
                    correlation_id=event.correlation_id,
                    recorded_at=event.created_at,
                )
                job = result.job
            if job.provider_state is not ProviderState.AMBIGUOUS_HOLD:
                raise RecoveryGateBlocked("ambiguous recovery must remain held")
            return RecoveryResult(job=job, event=event)

        if event.decision in {RecoveryDecision.RESUME_EXISTING, RecoveryDecision.TERMINAL_OBSERVED}:
            if job.provider_state is ProviderState.RECONCILING:
                remote = ProviderRemoteLineage(
                    provider_request_id=event.recovered_provider_request_id,
                    provider_operation_id=event.recovered_provider_operation_id,
                )
                command = (
                    "RECOVERED_HANDLE"
                    if event.proof_kind is RecoveryProofKind.RECOVERED_HANDLE
                    else "RECOVERED_ACTIVE_POLL"
                )
                result = await self.jobs.transition(
                    job_id=job.generation_job_id,
                    axis=GenerationJobAxis.PROVIDER,
                    command=command,
                    owner=TransitionOwner.RECOVERY_COORDINATOR,
                    guard_evidence=_guard(evidence, recovered_existing_remote=True),
                    expected_revision=job.revision,
                    actor_ref=event.actor_ref,
                    reason=event.reason,
                    correlation_id=event.correlation_id,
                    recorded_at=event.created_at,
                    remote_lineage=remote,
                )
                job = result.job
            if job.scheduler_state is SchedulerState.WAITING_RECOVERY and job.provider_state in {
                ProviderState.SUBMITTED,
                ProviderState.POLLING,
            }:
                result = await self.jobs.transition(
                    job_id=job.generation_job_id,
                    axis=GenerationJobAxis.SCHEDULER,
                    command="RECOVERY_RESUMES_ACTIVE_WORK",
                    owner=TransitionOwner.RECOVERY_COORDINATOR,
                    guard_evidence=_guard(evidence, recovered_existing_remote=True),
                    expected_revision=job.revision,
                    actor_ref=event.actor_ref,
                    reason=event.reason,
                    correlation_id=event.correlation_id,
                    recorded_at=event.created_at,
                )
                job = result.job
            terminal_command = {
                RecoveryProofKind.REMOTE_SUCCEEDED: "REMOTE_SUCCESS",
                RecoveryProofKind.REMOTE_FAILED: "REMOTE_FAILURE",
            }.get(event.proof_kind)
            if terminal_command is not None and job.provider_state is ProviderState.POLLING:
                result = await self.jobs.transition(
                    job_id=job.generation_job_id,
                    axis=GenerationJobAxis.PROVIDER,
                    command=terminal_command,
                    owner=TransitionOwner.PROVIDER_ADAPTER,
                    guard_evidence=_guard(evidence, recovered_terminal_observation=True),
                    expected_revision=job.revision,
                    actor_ref=event.actor_ref,
                    reason=event.reason,
                    correlation_id=event.correlation_id,
                    recorded_at=event.created_at,
                )
                job = result.job
            return RecoveryResult(job=job, event=event)

        return RecoveryResult(job=job, event=event)


def _guard(evidence_refs: tuple[str, ...], **facts) -> TransitionGuardEvidence:
    refs = tuple(sorted(set(_trimmed(value, "evidence_ref") for value in evidence_refs)))
    return TransitionGuardEvidence(
        summary="IMP-054 durable recovery proof",
        evidence_refs=refs,
        facts=tuple(GuardFact(key=key, value=value) for key, value in sorted(facts.items())),
    )


def _proof_facts(kind: RecoveryProofKind) -> dict[str, bool]:
    if kind is RecoveryProofKind.VERIFIED_SAME_JOB_IDEMPOTENCY:
        return {"verified_same_job_idempotency": True}
    if kind is RecoveryProofKind.TRANSPORT_NOT_DISPATCHED:
        return {"transport_not_dispatched": True}
    return {"proven_absent": True}


def _proof_and_decision(outcome: RecoveryProbeOutcome) -> tuple[RecoveryProofKind, RecoveryDecision]:
    mapping = {
        RecoveryProbeOutcome.PROVEN_NOT_SUBMITTED: (
            RecoveryProofKind.TRANSPORT_NOT_DISPATCHED,
            RecoveryDecision.SAFE_TO_REQUEUE,
        ),
        RecoveryProbeOutcome.PROVEN_ABSENT: (
            RecoveryProofKind.PROVEN_ABSENT,
            RecoveryDecision.SAFE_TO_REQUEUE,
        ),
        RecoveryProbeOutcome.VERIFIED_SAME_JOB_IDEMPOTENCY: (
            RecoveryProofKind.VERIFIED_SAME_JOB_IDEMPOTENCY,
            RecoveryDecision.SAFE_TO_REQUEUE,
        ),
        RecoveryProbeOutcome.RECOVERED_HANDLE: (
            RecoveryProofKind.RECOVERED_HANDLE,
            RecoveryDecision.RESUME_EXISTING,
        ),
        RecoveryProbeOutcome.RECOVERED_ACTIVE_POLL: (
            RecoveryProofKind.RECOVERED_ACTIVE_POLL,
            RecoveryDecision.RESUME_EXISTING,
        ),
        RecoveryProbeOutcome.REMOTE_SUCCEEDED: (
            RecoveryProofKind.REMOTE_SUCCEEDED,
            RecoveryDecision.TERMINAL_OBSERVED,
        ),
        RecoveryProbeOutcome.REMOTE_FAILED: (
            RecoveryProofKind.REMOTE_FAILED,
            RecoveryDecision.TERMINAL_OBSERVED,
        ),
        RecoveryProbeOutcome.REMOTE_CANCELED: (
            RecoveryProofKind.REMOTE_CANCELED,
            RecoveryDecision.TERMINAL_OBSERVED,
        ),
        RecoveryProbeOutcome.STILL_AMBIGUOUS: (
            RecoveryProofKind.STILL_AMBIGUOUS,
            RecoveryDecision.HOLD_AMBIGUOUS,
        ),
    }
    return mapping[outcome]


def _classify_failure(
    trigger: RecoveryTrigger,
    result: RecoveryProbeResult,
) -> RecoveryFailureClassification:
    if trigger is RecoveryTrigger.CANCELLATION_RACE:
        return RecoveryFailureClassification(
            error_code="CANCELLATION_RACE",
            error_class=ErrorClass.CANCELLATION,
            retry_disposition=RetryDisposition.RECONCILIATION_REQUIRED,
        )
    if result.outcome in {
        RecoveryProbeOutcome.STILL_AMBIGUOUS,
        RecoveryProbeOutcome.RECOVERED_HANDLE,
        RecoveryProbeOutcome.RECOVERED_ACTIVE_POLL,
        RecoveryProbeOutcome.REMOTE_SUCCEEDED,
        RecoveryProbeOutcome.REMOTE_FAILED,
        RecoveryProbeOutcome.REMOTE_CANCELED,
    }:
        return RecoveryFailureClassification(
            error_code=f"PROVIDER_{trigger.value}",
            error_class=ErrorClass.PROVIDER_AMBIGUITY,
            retry_disposition=RetryDisposition.RECONCILIATION_REQUIRED,
        )
    return RecoveryFailureClassification(
        error_code=f"RECOVERY_PROOF_{result.outcome.value}",
        error_class=ErrorClass.PROVIDER_TRANSPORT,
        retry_disposition=RetryDisposition.RETRYABLE,
    )


def _safe_observation_dict(observation: ProviderTransportObservation) -> dict:
    """Persist only recovery-relevant normalized provider evidence, never output URLs."""
    data = observation.model_dump(mode="json", exclude={"output_url"})
    if data.get("message") is not None:
        data["message"] = redact_text(str(data["message"]))
    return data


__all__ = [
    "ProviderAdapterRecoveryProbe",
    "RecoveryCoordinator",
    "RecoveryDecision",
    "RecoveryError",
    "RecoveryEvent",
    "RecoveryEventRepository",
    "RecoveryEvidenceConflict",
    "RecoveryFailureClassification",
    "RecoveryGateBlocked",
    "RecoveryProbeOutcome",
    "RecoveryProbePort",
    "RecoveryProbeResult",
    "RecoveryProofKind",
    "RecoveryResult",
    "RecoveryTrigger",
]
