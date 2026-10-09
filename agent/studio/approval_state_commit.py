"""IMP-064 explicit approval -> canonical StateSnapshot commit boundary.

This service does not own StateSnapshot or ApprovedEndState persistence. It
validates exact approval/QA authority and then delegates the commit to the
existing StateSnapshotRepository, which remains the sole canonical state owner.
"""

from __future__ import annotations

from typing import TypeAlias

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from .generation_job import CreativeState, GenerationJobAxis, GenerationJobRepository
from .motion_qa import MotionQAExecutionStatus, MotionQAResult
from .persistence import CASConflict
from .primitives import GateVerdict, LifecycleState, LogicalId, VersionId, VersionRef
from .state_continuity import (
    StateApprovalBlocked,
    StateApprovalResult,
    StateContinuityError,
    StateSnapshotRepository,
)
from .static_qa import StaticQAExecutionStatus, StaticQAResult
from .versioning import VersionRepository


_ACCEPTED = {LifecycleState.APPROVED, LifecycleState.LOCKED}
_QA_PREFIXES = ("qa-result:", "motion-qa-result:")


class ApprovalStateCommitError(RuntimeError):
    """Base IMP-064 approval/state-commit boundary error."""


class ApprovalStateCommitBlocked(ApprovalStateCommitError):
    """Raised when exact approval/state authority is missing, stale, or contradictory."""


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


class ApprovalStateCommitRequest(BaseModel):
    """Exact authority required to promote one candidate StateSnapshot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    generation_job_id: LogicalId
    state_snapshot_ref: VersionRef
    qa_result_ref: VersionRef
    approval_policy_ref: VersionRef
    source_outcome_ref: VersionRef
    designation_version: VersionId
    expected_snapshot_revision: int = Field(ge=0)
    status: LifecycleState = LifecycleState.APPROVED
    actor_ref: str
    reason: str
    recorded_at: AwareDatetime
    correlation_id: str | None = None
    repair_or_recompute_requirement: str = "recompute/revalidate state-dependent descendants"

    @field_validator("actor_ref", "reason", "repair_or_recompute_requirement")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_request(self) -> "ApprovalStateCommitRequest":
        if self.status not in _ACCEPTED:
            raise ValueError("state commit status must be APPROVED or LOCKED")
        if not self.state_snapshot_ref.logical_id.root.startswith("state-snapshot:"):
            raise ValueError("state_snapshot_ref must identify canonical StateSnapshot")
        if not self.qa_result_ref.logical_id.root.startswith(_QA_PREFIXES):
            raise ValueError("qa_result_ref must identify typed Static or Motion QA evidence")
        return self


class ApprovalStateCommitResult(BaseModel):
    """Boundary result; canonical state/designation payload remains owned downstream."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    generation_job_id: LogicalId
    qa_result_ref: VersionRef
    approval_policy_ref: VersionRef
    source_outcome_ref: VersionRef
    state_approval: StateApprovalResult


TypedQAResult: TypeAlias = StaticQAResult | MotionQAResult


class ApprovalStateCommitService:
    """Validate approval authority, then delegate canonical state commit."""

    def __init__(self, writer) -> None:
        self.jobs = GenerationJobRepository(writer)
        self.versions = VersionRepository(writer)
        self.state = StateSnapshotRepository(writer)

    async def commit(self, request: ApprovalStateCommitRequest) -> ApprovalStateCommitResult:
        job = await self.jobs.get_job(request.generation_job_id)
        if job is None:
            raise ApprovalStateCommitBlocked("GenerationJob does not exist")
        if job.creative_state not in {CreativeState.APPROVED, CreativeState.LOCKED}:
            raise ApprovalStateCommitBlocked(
                "NO QA APPROVAL -> NO STATE COMMIT: GenerationJob creative state is not APPROVED/LOCKED"
            )

        snapshot_artifact = await self.state.get_version(request.state_snapshot_ref)
        if snapshot_artifact is None:
            raise ApprovalStateCommitBlocked("candidate StateSnapshot exact version does not exist")
        snapshot = snapshot_artifact.value
        if snapshot.project_id != job.project_id:
            raise ApprovalStateCommitBlocked("candidate StateSnapshot project does not match GenerationJob")
        pointer = await self.state.get_current_pointer(snapshot.state_snapshot_id)
        if (
            pointer is None
            or pointer.version_id != request.state_snapshot_ref.version_id
            or pointer.revision != request.expected_snapshot_revision
        ):
            raise ApprovalStateCommitBlocked("candidate StateSnapshot is stale or CAS revision changed")

        qa, qa_pointer = await self._load_typed_qa(request.qa_result_ref)
        if qa.project_id != job.project_id or qa.generation_job_id != job.generation_job_id:
            raise ApprovalStateCommitBlocked("typed QA result does not belong to the approved GenerationJob")
        if isinstance(qa, StaticQAResult):
            completed = qa.execution_status is StaticQAExecutionStatus.COMPLETED
        else:
            completed = qa.execution_status is MotionQAExecutionStatus.COMPLETED
        if not completed or qa.verdict is not GateVerdict.PASS:
            raise ApprovalStateCommitBlocked("typed QA result must be COMPLETED with verdict PASS")

        await self._assert_exact_current_accepted(request.approval_policy_ref, "approval policy")
        await self._assert_exact_current_accepted(request.source_outcome_ref, "source outcome")
        if snapshot.source_outcome_ref is not None and snapshot.source_outcome_ref != request.source_outcome_ref:
            raise ApprovalStateCommitBlocked("source outcome contradicts candidate StateSnapshot lineage")

        # A REVIEW QA pointer may be promoted here only when the durable creative
        # approval path was HUMAN_APPROVE. If QA_PASS_AND_AUTO_APPROVE is durable
        # but the QA pointer is still REVIEW, the QA stage was interrupted after its
        # state transition and must be recovered there rather than silently repaired
        # by State Commit.
        if qa_pointer.status is LifecycleState.REVIEW:
            approval_command = await self._latest_creative_approval_command(
                request.generation_job_id
            )
            if approval_command != "HUMAN_APPROVE":
                raise ApprovalStateCommitBlocked(
                    "REVIEW QA requires durable HUMAN_APPROVE evidence before state commit"
                )
            try:
                qa_pointer = await self.versions.update_current(
                    logical_id=request.qa_result_ref.logical_id,
                    version_id=request.qa_result_ref.version_id,
                    status=LifecycleState.APPROVED,
                    expected_revision=qa_pointer.revision,
                )
            except CASConflict as exc:
                raise ApprovalStateCommitBlocked(
                    "QA result current pointer changed during approval"
                ) from exc
        elif qa_pointer.status not in _ACCEPTED:
            raise ApprovalStateCommitBlocked("QA result is not reviewable/accepted current authority")

        try:
            approved = await self.state.approve_end_state(
                snapshot_ref=request.state_snapshot_ref,
                designation_version=request.designation_version,
                qa_result_ref=request.qa_result_ref,
                approval_policy_ref=request.approval_policy_ref,
                source_outcome_ref=request.source_outcome_ref,
                actor_ref=request.actor_ref,
                reason=request.reason,
                recorded_at=request.recorded_at,
                expected_snapshot_revision=request.expected_snapshot_revision,
                status=request.status,
                repair_or_recompute_requirement=request.repair_or_recompute_requirement,
                correlation_id=request.correlation_id,
            )
        except (StateApprovalBlocked, StateContinuityError) as exc:
            raise ApprovalStateCommitBlocked(str(exc)) from exc

        if approved.designation.value.state_snapshot_ref != request.state_snapshot_ref:
            raise ApprovalStateCommitError("ApprovedEndState designation lost exact StateSnapshot identity")
        return ApprovalStateCommitResult(
            generation_job_id=request.generation_job_id,
            qa_result_ref=request.qa_result_ref,
            approval_policy_ref=request.approval_policy_ref,
            source_outcome_ref=request.source_outcome_ref,
            state_approval=approved,
        )

    async def _latest_creative_approval_command(self, job_id: LogicalId) -> str | None:
        history = await self.jobs.list_transitions(job_id)
        for transition in reversed(history):
            if (
                transition.axis is GenerationJobAxis.CREATIVE
                and transition.command in {"HUMAN_APPROVE", "QA_PASS_AND_AUTO_APPROVE"}
            ):
                return transition.command
        return None

    async def _load_typed_qa(self, ref: VersionRef):
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise ApprovalStateCommitBlocked("QA result exact version does not exist")
        pointer = await self.versions.get_current(ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != ref.version_id
            or pointer.status not in {LifecycleState.REVIEW, *_ACCEPTED}
        ):
            raise ApprovalStateCommitBlocked(
                "QA result is not exact current REVIEW/APPROVED/LOCKED authority"
            )
        for record in await self.state.invalidations.list_unresolved():
            if record.affected_object_id == ref.logical_id and record.affected_object_version == ref.version_id:
                raise ApprovalStateCommitBlocked("QA result has unresolved invalidation")
        root = ref.logical_id.root
        try:
            if root.startswith("qa-result:"):
                return StaticQAResult.model_validate(stored.payload), pointer
            if root.startswith("motion-qa-result:"):
                return MotionQAResult.model_validate(stored.payload), pointer
        except Exception as exc:
            raise ApprovalStateCommitBlocked("QA result payload is not valid typed QA evidence") from exc
        raise ApprovalStateCommitBlocked("qa_result_ref is not a supported typed QA identity")

    async def _assert_exact_current_accepted(self, ref: VersionRef, label: str) -> None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise ApprovalStateCommitBlocked(f"{label} exact version does not exist")
        pointer = await self.versions.get_current(ref.logical_id)
        if pointer is None or pointer.version_id != ref.version_id or pointer.status not in _ACCEPTED:
            raise ApprovalStateCommitBlocked(f"{label} is not exact current APPROVED/LOCKED")
        for record in await self.state.invalidations.list_unresolved():
            if record.affected_object_id == ref.logical_id and record.affected_object_version == ref.version_id:
                raise ApprovalStateCommitBlocked(f"{label} has unresolved invalidation")
