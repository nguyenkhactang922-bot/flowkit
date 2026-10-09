"""IMP-042 canonical StateSnapshot, ContinuityLedger and ApprovedEndState.

StateSnapshot owns semantic continuity/world-state facts. ContinuityLedger owns
only continuity evidence/constraints and exact propagation links. Approved end
state is an approval-qualified reference to one immutable StateSnapshot version;
it never duplicates state payload. Legacy media/image chaining stays outside this
canonical authority boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .entity import EntityVersion
from .invalidation import (
    DependencyGraphRepository,
    InvalidationRecord,
    InvalidationRepository,
)
from .persistence import SQLiteWriteOwner
from .primitives import (
    FindingSeverity,
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    VersionId,
    VersionRef,
)
from .versioning import CurrentVersionPointer, VersionRepository


_ACCEPTED = {LifecycleState.APPROVED, LifecycleState.LOCKED}
_PATH_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
_SCOPE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+-]{0,127}$")
_FORBIDDEN_STATE_KEYS = {
    "media_id",
    "image_media_id",
    "video_media_id",
    "image_url",
    "video_url",
    "parent_scene_id",
    "chain_type",
    "prompt",
    "image_prompt",
    "video_prompt",
    "provider",
    "provider_id",
    "request_id",
    "generation_id",
}


class StateContinuityError(ValueError):
    """Base IMP-042 state/continuity contract error."""


class StateIdentityError(StateContinuityError):
    """Raised when snapshot/ledger/designation identity lineage is invalid."""


class StateApprovalBlocked(StateContinuityError):
    """Raised when a candidate snapshot lacks valid exact approval evidence."""


class StatePropagationBlocked(StateContinuityError):
    """Raised when a state cannot be consumed as downstream continuity authority."""


class StateFactNamespace(str, Enum):
    """State Engine-owned observable/semantic continuity fact families."""

    WARDROBE = "wardrobe"
    PROP = "prop"
    PHYSICAL = "physical"
    LOCATION = "location"
    ENVIRONMENT = "environment"
    LIGHTING = "lighting"
    SPATIAL = "spatial"
    ACTION = "action"


class StateDeltaKind(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    CHANGED = "CHANGED"


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _scope_key(value: str) -> str:
    value = _trimmed(value, "scope_key")
    if not _SCOPE_RE.fullmatch(value):
        raise ValueError("scope_key contains unsupported characters")
    return value


def _path(value: str) -> str:
    normalized = _trimmed(value, "state fact key").lower()
    if not _PATH_RE.fullmatch(normalized):
        raise ValueError(
            "state fact key must start with lowercase letter and contain only "
            "lowercase letters, digits, '.', '_' or '-'"
        )
    if normalized in _FORBIDDEN_STATE_KEYS or normalized.rsplit(".", 1)[-1] in _FORBIDDEN_STATE_KEYS:
        raise ValueError(
            "execution/provider/media fields cannot become canonical StateSnapshot facts"
        )
    return normalized


def _reject_execution_payload(value) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            if normalized in _FORBIDDEN_STATE_KEYS:
                raise ValueError(
                    f"execution/provider/media field cannot enter StateSnapshot payload: {normalized}"
                )
            _reject_execution_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_execution_payload(item)


def _canonical_json(value_json: str) -> str:
    raw = _trimmed(value_json, "value_json")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("value_json must contain valid JSON") from exc
    if value is None:
        raise ValueError("canonical state fact value cannot be null")
    _reject_execution_payload(value)
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("state fact value must be canonical JSON data") from exc


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return ref.logical_id.root, ref.version_id.root


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _digest_parts(*parts: str) -> str:
    raw = "\0".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def state_snapshot_logical_id(project_id: LogicalId, scope_key: str) -> LogicalId:
    scope = _scope_key(scope_key)
    digest = _digest_parts(project_id.root, scope)
    return LogicalId(f"state-snapshot:{project_id.root}:{digest}")


def approved_end_state_logical_id(
    project_id: LogicalId,
    state_snapshot_ref: VersionRef,
) -> LogicalId:
    digest = _digest_parts(
        project_id.root,
        state_snapshot_ref.logical_id.root,
        state_snapshot_ref.version_id.root,
    )
    return LogicalId(f"approved-end-state:{project_id.root}:{digest}")


def continuity_ledger_logical_id(project_id: LogicalId, scope_key: str) -> LogicalId:
    scope = _scope_key(scope_key)
    digest = _digest_parts(project_id.root, scope)
    return LogicalId(f"continuity-ledger:{project_id.root}:{digest}")


class StateFact(BaseModel):
    """One canonical State Engine-owned semantic continuity fact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    namespace: StateFactNamespace
    key: str
    value_json: str
    subject_ref: VersionRef | None = None

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        return _path(value)

    @field_validator("value_json")
    @classmethod
    def validate_value(cls, value: str) -> str:
        return _canonical_json(value)

    @model_validator(mode="after")
    def validate_subject(self) -> "StateFact":
        if self.namespace in {
            StateFactNamespace.WARDROBE,
            StateFactNamespace.PHYSICAL,
        } and self.subject_ref is None:
            raise ValueError(f"{self.namespace.value} facts require an exact subject_ref")
        if self.subject_ref is not None and not self.subject_ref.logical_id.root.startswith("entity:"):
            raise ValueError("StateFact subject_ref must bind an exact canonical EntityVersion")
        return self

    @property
    def fact_key(self) -> str:
        subject = self.subject_ref.logical_id.root if self.subject_ref is not None else "world"
        return f"{self.namespace.value}:{subject}:{self.key}"

    @property
    def value_hash(self) -> str:
        return _sha256_text(self.value_json)


class StateSnapshot(BaseModel):
    """Immutable semantic continuity/world-state snapshot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    state_snapshot_id: LogicalId
    version_id: VersionId
    scope_key: str
    story_time: str
    facts: tuple[StateFact, ...] = Field(min_length=1)
    previous_snapshot_ref: VersionRef | None = None
    source_outcome_ref: VersionRef | None = None
    change_refs: tuple[VersionRef, ...] = Field(min_length=1)
    context_state_refs: tuple[VersionRef, ...] = ()

    @field_validator("scope_key")
    @classmethod
    def validate_scope_key(cls, value: str) -> str:
        return _scope_key(value)

    @field_validator("story_time")
    @classmethod
    def validate_story_time(cls, value: str) -> str:
        return _trimmed(value, "story_time")

    @field_validator("change_refs", "context_state_refs")
    @classmethod
    def normalize_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        unique = {_ref_key(ref): ref for ref in values}
        return tuple(unique[key] for key in sorted(unique))

    @field_validator("facts")
    @classmethod
    def normalize_facts(cls, values: tuple[StateFact, ...]) -> tuple[StateFact, ...]:
        by_key: dict[str, StateFact] = {}
        for fact in values:
            if fact.fact_key in by_key:
                raise ValueError(f"duplicate StateFact identity: {fact.fact_key}")
            by_key[fact.fact_key] = fact
        return tuple(by_key[key] for key in sorted(by_key))

    @model_validator(mode="after")
    def validate_identity(self) -> "StateSnapshot":
        expected = state_snapshot_logical_id(self.project_id, self.scope_key)
        if self.state_snapshot_id != expected:
            raise ValueError(f"state_snapshot_id must be {expected.root}")
        if self.previous_snapshot_ref is not None:
            if self.previous_snapshot_ref.logical_id != self.state_snapshot_id:
                raise ValueError("previous_snapshot_ref must preserve StateSnapshot logical identity")
            if self.previous_snapshot_ref.version_id == self.version_id:
                raise ValueError("previous_snapshot_ref must reference an older version")
        for ref in self.context_state_refs:
            root = ref.logical_id.root
            if not (
                root.startswith("character-model:")
                or root.startswith("relationship:")
                or root.startswith("character-knowledge:")
            ):
                raise ValueError(
                    "context_state_refs may reference Story-owned psychology/relationship/knowledge state only"
                )
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.state_snapshot_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values: list[SourceVersionBinding] = []
        if self.previous_snapshot_ref is not None:
            values.append(
                SourceVersionBinding(role="previous_state_snapshot", source=self.previous_snapshot_ref)
            )
        if self.source_outcome_ref is not None:
            values.append(SourceVersionBinding(role="source_outcome", source=self.source_outcome_ref))

        subject_refs = {
            _ref_key(fact.subject_ref): fact.subject_ref
            for fact in self.facts
            if fact.subject_ref is not None
        }
        values.extend(
            SourceVersionBinding(role=f"subject_entity_{index:03d}", source=subject_refs[key])
            for index, key in enumerate(sorted(subject_refs))
        )
        values.extend(
            SourceVersionBinding(role=f"accepted_change_{index:03d}", source=ref)
            for index, ref in enumerate(self.change_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"story_owned_state_{index:03d}", source=ref)
            for index, ref in enumerate(self.context_state_refs)
        )
        return tuple(values)


class StateSnapshotArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: StateSnapshot

    @model_validator(mode="after")
    def validate_artifact(self) -> "StateSnapshotArtifact":
        if self.metadata.logical_id != self.value.state_snapshot_id:
            raise ValueError("StateSnapshot metadata logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("StateSnapshot metadata version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError("StateSnapshot provenance must exactly bind snapshot sources")
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


class StateDeltaEntry(BaseModel):
    """Payload-free state diff entry; values remain authoritative in snapshots."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fact_key: str
    kind: StateDeltaKind
    before_value_hash: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    after_value_hash: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hashes(self) -> "StateDeltaEntry":
        if self.kind is StateDeltaKind.ADDED:
            if self.before_value_hash is not None or self.after_value_hash is None:
                raise ValueError("ADDED state delta requires only after_value_hash")
        elif self.kind is StateDeltaKind.REMOVED:
            if self.before_value_hash is None or self.after_value_hash is not None:
                raise ValueError("REMOVED state delta requires only before_value_hash")
        else:
            if self.before_value_hash is None or self.after_value_hash is None:
                raise ValueError("CHANGED state delta requires before/after hashes")
            if self.before_value_hash == self.after_value_hash:
                raise ValueError("CHANGED state delta hashes must differ")
        return self


class StateDelta(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    previous_snapshot_ref: VersionRef
    current_snapshot_ref: VersionRef
    changes: tuple[StateDeltaEntry, ...]


def derive_state_delta(previous: StateSnapshot, current: StateSnapshot) -> StateDelta:
    if previous.state_snapshot_id != current.state_snapshot_id:
        raise StateIdentityError("state delta requires the same logical StateSnapshot identity")
    if current.previous_snapshot_ref != previous.ref:
        raise StateIdentityError("state delta current snapshot must name previous exact version")

    before = {fact.fact_key: fact for fact in previous.facts}
    after = {fact.fact_key: fact for fact in current.facts}
    changes: list[StateDeltaEntry] = []
    for key in sorted(set(before) | set(after)):
        old = before.get(key)
        new = after.get(key)
        if old is None and new is not None:
            changes.append(
                StateDeltaEntry(
                    fact_key=key,
                    kind=StateDeltaKind.ADDED,
                    after_value_hash=new.value_hash,
                )
            )
        elif old is not None and new is None:
            changes.append(
                StateDeltaEntry(
                    fact_key=key,
                    kind=StateDeltaKind.REMOVED,
                    before_value_hash=old.value_hash,
                )
            )
        elif old is not None and new is not None and old.value_hash != new.value_hash:
            changes.append(
                StateDeltaEntry(
                    fact_key=key,
                    kind=StateDeltaKind.CHANGED,
                    before_value_hash=old.value_hash,
                    after_value_hash=new.value_hash,
                )
            )
    return StateDelta(
        previous_snapshot_ref=previous.ref,
        current_snapshot_ref=current.ref,
        changes=tuple(changes),
    )


def build_state_snapshot_provenance(
    snapshot: StateSnapshot,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=snapshot.source_bindings(),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        correlation_id=correlation_id,
    )


class ApprovedEndStateDesignation(BaseModel):
    """Approval lineage/reference only; contains no canonical state payload."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    approval_record_id: LogicalId
    version_id: VersionId
    state_snapshot_ref: VersionRef
    qa_result_ref: VersionRef
    approval_policy_ref: VersionRef
    source_outcome_ref: VersionRef

    @model_validator(mode="after")
    def validate_identity(self) -> "ApprovedEndStateDesignation":
        if not self.state_snapshot_ref.logical_id.root.startswith(
            f"state-snapshot:{self.project_id.root}:"
        ):
            raise ValueError("state_snapshot_ref belongs to a different project")
        expected = approved_end_state_logical_id(self.project_id, self.state_snapshot_ref)
        if self.approval_record_id != expected:
            raise ValueError(f"approval_record_id must be {expected.root}")
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.approval_record_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return (
            SourceVersionBinding(role="approved_state_snapshot", source=self.state_snapshot_ref),
            SourceVersionBinding(role="qa_result", source=self.qa_result_ref),
            SourceVersionBinding(role="approval_policy", source=self.approval_policy_ref),
            SourceVersionBinding(role="source_outcome", source=self.source_outcome_ref),
        )


class ApprovedEndStateArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: ApprovedEndStateDesignation

    @model_validator(mode="after")
    def validate_artifact(self) -> "ApprovedEndStateArtifact":
        if self.metadata.logical_id != self.value.approval_record_id:
            raise ValueError("ApprovedEndState metadata logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("ApprovedEndState metadata version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError("ApprovedEndState provenance must exactly bind approval sources")
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


def build_approved_end_state_provenance(
    designation: ApprovedEndStateDesignation,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=designation.source_bindings(),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        correlation_id=correlation_id,
    )


class StateApprovalResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    snapshot_pointer: CurrentVersionPointer
    designation: ApprovedEndStateArtifact
    invalidations: tuple[InvalidationRecord, ...] = ()


class StateRevocationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    revoked_designation: ApprovedEndStateArtifact
    invalidations: tuple[InvalidationRecord, ...] = ()


class StateSnapshotRepository:
    """StateSnapshot versions plus fail-closed approval/designation coordination."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)

    async def create_initial(
        self,
        *,
        snapshot: StateSnapshot,
        provenance: Provenance,
        created_at: datetime,
    ) -> StateSnapshotArtifact:
        if snapshot.previous_snapshot_ref is not None:
            raise StateIdentityError("initial StateSnapshot cannot declare previous_snapshot_ref")
        self._assert_provenance(snapshot, provenance)
        await self._assert_snapshot_sources_current(snapshot, include_previous=False)
        metadata = SemanticRecordMetadata(
            logical_id=snapshot.state_snapshot_id,
            version_id=snapshot.version_id,
            provenance=provenance,
            created_at=created_at,
        )
        stored = await self.versions.create_initial(
            metadata=metadata,
            payload=snapshot.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        artifact = StateSnapshotArtifact(metadata=stored.metadata, value=snapshot)
        await self._register_snapshot_dependencies(artifact)
        return artifact

    async def create_successor(
        self,
        *,
        snapshot: StateSnapshot,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> StateSnapshotArtifact:
        if predecessor.logical_id != snapshot.state_snapshot_id:
            raise StateIdentityError("StateSnapshot successor must preserve logical identity")
        if snapshot.previous_snapshot_ref != predecessor:
            raise StateIdentityError("successor previous_snapshot_ref must equal predecessor")
        pointer = await self.versions.get_current(snapshot.state_snapshot_id)
        if (
            pointer is None
            or pointer.version_id != predecessor.version_id
            or pointer.status not in _ACCEPTED
        ):
            raise StateIdentityError(
                "StateSnapshot successor predecessor must be exact current APPROVED/LOCKED"
            )
        previous = await self.get_version(predecessor)
        if previous is None:
            raise StateIdentityError("StateSnapshot predecessor does not exist")
        self._assert_semantic_change(previous.value, snapshot)
        self._assert_provenance(snapshot, provenance)
        await self._assert_snapshot_sources_current(snapshot, include_previous=True)
        metadata = SemanticRecordMetadata(
            logical_id=snapshot.state_snapshot_id,
            version_id=snapshot.version_id,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
        )
        stored = await self.versions.create_successor(
            metadata=metadata,
            payload=snapshot.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        artifact = StateSnapshotArtifact(metadata=stored.metadata, value=snapshot)
        await self._register_snapshot_dependencies(artifact)
        return artifact

    async def get_version(self, ref: VersionRef) -> StateSnapshotArtifact | None:
        if not ref.logical_id.root.startswith("state-snapshot:"):
            raise StateIdentityError("expected StateSnapshot ref")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        return StateSnapshotArtifact(
            metadata=stored.metadata,
            value=StateSnapshot.model_validate(stored.payload),
        )

    async def get_current_pointer(
        self,
        state_snapshot_id: LogicalId,
    ) -> CurrentVersionPointer | None:
        return await self.versions.get_current(state_snapshot_id)

    async def approve_end_state(
        self,
        *,
        snapshot_ref: VersionRef,
        designation_version: VersionId,
        qa_result_ref: VersionRef,
        approval_policy_ref: VersionRef,
        source_outcome_ref: VersionRef,
        actor_ref: str,
        reason: str,
        recorded_at: datetime,
        expected_snapshot_revision: int,
        status: LifecycleState = LifecycleState.APPROVED,
        repair_or_recompute_requirement: str = "recompute/revalidate state-dependent descendants",
        correlation_id: str | None = None,
    ) -> StateApprovalResult:
        if status not in _ACCEPTED:
            raise StateApprovalBlocked("approved end state status must be APPROVED or LOCKED")
        snapshot_artifact = await self.get_version(snapshot_ref)
        if snapshot_artifact is None:
            raise StateApprovalBlocked("candidate StateSnapshot exact version does not exist")
        snapshot = snapshot_artifact.value
        await self._assert_not_invalidated(snapshot_ref)
        if not qa_result_ref.logical_id.root.startswith(("qa-result:", "motion-qa-result:")):
            raise StateApprovalBlocked(
                "qa_result_ref must identify canonical Static or Motion QA evidence"
            )
        await self._assert_exact_current_accepted(qa_result_ref, "QA result")
        await self._assert_exact_current_accepted(approval_policy_ref, "approval policy")
        await self._assert_exact_current_accepted(source_outcome_ref, "source outcome")
        if snapshot.source_outcome_ref is not None and snapshot.source_outcome_ref != source_outcome_ref:
            raise StateApprovalBlocked("approval source outcome contradicts StateSnapshot lineage")

        designation = ApprovedEndStateDesignation(
            project_id=snapshot.project_id,
            approval_record_id=approved_end_state_logical_id(snapshot.project_id, snapshot_ref),
            version_id=designation_version,
            state_snapshot_ref=snapshot_ref,
            qa_result_ref=qa_result_ref,
            approval_policy_ref=approval_policy_ref,
            source_outcome_ref=source_outcome_ref,
        )
        designation_provenance = build_approved_end_state_provenance(
            designation,
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=recorded_at,
            correlation_id=correlation_id,
        )
        designation_artifact = await self._ensure_designation_draft(
            designation=designation,
            provenance=designation_provenance,
            created_at=recorded_at,
        )

        pointer = await self.versions.get_current(snapshot.state_snapshot_id)
        if pointer is None or pointer.revision != expected_snapshot_revision:
            raise StateApprovalBlocked("StateSnapshot current pointer revision changed")

        # Revalidate exact inputs immediately before invalidation/pointer side effects.
        await self._assert_snapshot_sources_current(
            snapshot,
            include_previous=snapshot.previous_snapshot_ref is not None,
        )
        await self._assert_exact_current_accepted(qa_result_ref, "QA result")
        await self._assert_exact_current_accepted(approval_policy_ref, "approval policy")
        await self._assert_exact_current_accepted(source_outcome_ref, "source outcome")

        invalidations: tuple[InvalidationRecord, ...] = ()
        if snapshot.previous_snapshot_ref is None:
            if pointer.version_id != snapshot.version_id:
                raise StateApprovalBlocked("initial candidate StateSnapshot is no longer current")
        else:
            predecessor = snapshot.previous_snapshot_ref
            if pointer.version_id == predecessor.version_id and pointer.status in _ACCEPTED:
                reachable = [
                    item
                    for item in await self.graph.descendants(predecessor)
                    if item.ref != snapshot.ref
                ]
                records = await self.invalidations.create_for_change(
                    cause="APPROVED_STATE_SNAPSHOT_CHANGED",
                    source_old=predecessor,
                    source_new=snapshot.ref,
                    provenance=designation_provenance,
                    scope="CANONICAL_STATE_CONTINUITY",
                    repair_or_recompute_requirement=_trimmed(
                        repair_or_recompute_requirement,
                        "repair_or_recompute_requirement",
                    ),
                    reachable=reachable,
                )
                invalidations = tuple(records)
            elif pointer.version_id != snapshot.version_id:
                raise StateApprovalBlocked(
                    "successor StateSnapshot predecessor is no longer current accepted"
                )

        if pointer.version_id != snapshot.version_id or pointer.status != status:
            pointer = await self.versions.update_current(
                logical_id=snapshot.state_snapshot_id,
                version_id=snapshot.version_id,
                status=status,
                expected_revision=pointer.revision,
            )

        designation_pointer = await self.versions.get_current(designation.approval_record_id)
        if designation_pointer is None:
            raise StateApprovalBlocked("approval designation current pointer is missing")
        if designation_pointer.version_id != designation.version_id:
            raise StateApprovalBlocked("approval designation version conflict")
        if designation_pointer.status not in _ACCEPTED:
            await self.versions.update_current(
                logical_id=designation.approval_record_id,
                version_id=designation.version_id,
                status=LifecycleState.APPROVED,
                expected_revision=designation_pointer.revision,
            )

        await self._register_designation_dependencies(designation_artifact)
        return StateApprovalResult(
            snapshot_pointer=pointer,
            designation=designation_artifact,
            invalidations=invalidations,
        )

    async def revoke_end_state(
        self,
        *,
        state_snapshot_ref: VersionRef,
        revocation_version: VersionId,
        expected_designation_revision: int,
        actor_ref: str,
        reason: str,
        recorded_at: datetime,
        repair_or_recompute_requirement: str = "recompute/revalidate descendants after end-state approval revocation",
        correlation_id: str | None = None,
    ) -> StateRevocationResult:
        current = await self.get_approved_designation(state_snapshot_ref)
        if current is None:
            raise StateApprovalBlocked("no current approved end-state designation to revoke")
        pointer = await self.versions.get_current(current.value.approval_record_id)
        if (
            pointer is None
            or pointer.version_id != current.value.version_id
            or pointer.status not in _ACCEPTED
            or pointer.revision != expected_designation_revision
        ):
            raise StateApprovalBlocked(
                "approved end-state designation changed before revocation"
            )

        revoked = current.value.model_copy(update={"version_id": revocation_version})
        artifact_provenance = build_approved_end_state_provenance(
            revoked,
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=recorded_at,
            correlation_id=correlation_id,
        )
        metadata = SemanticRecordMetadata(
            logical_id=revoked.approval_record_id,
            version_id=revoked.version_id,
            predecessor=current.ref,
            provenance=artifact_provenance,
            created_at=recorded_at,
        )
        stored = await self.versions.create_successor(
            metadata=metadata,
            payload=revoked.model_dump(mode="json"),
            supersession_reason=reason,
        )
        revoked_artifact = ApprovedEndStateArtifact(
            metadata=stored.metadata,
            value=revoked,
        )
        invalidation_provenance = Provenance(
            source_versions=(
                SourceVersionBinding(role="previous_approval_designation", source=current.ref),
                SourceVersionBinding(role="revoked_approval_designation", source=revoked.ref),
            ),
            actor_ref=actor_ref,
            reason=reason,
            recorded_at=recorded_at,
            correlation_id=correlation_id,
        )
        records = await self.invalidations.create_for_change(
            cause="APPROVED_END_STATE_REVOKED",
            source_old=current.ref,
            source_new=revoked.ref,
            provenance=invalidation_provenance,
            scope="APPROVED_END_STATE",
            repair_or_recompute_requirement=_trimmed(
                repair_or_recompute_requirement,
                "repair_or_recompute_requirement",
            ),
        )
        await self.versions.update_current(
            logical_id=revoked.approval_record_id,
            version_id=revoked.version_id,
            status=LifecycleState.INVALIDATED,
            expected_revision=expected_designation_revision,
        )
        return StateRevocationResult(
            revoked_designation=revoked_artifact,
            invalidations=tuple(records),
        )

    async def get_approved_designation(
        self,
        state_snapshot_ref: VersionRef,
    ) -> ApprovedEndStateArtifact | None:
        snapshot = await self.get_version(state_snapshot_ref)
        if snapshot is None:
            return None
        logical_id = approved_end_state_logical_id(
            snapshot.value.project_id,
            state_snapshot_ref,
        )
        pointer = await self.versions.get_current(logical_id)
        if pointer is None or pointer.status not in _ACCEPTED:
            return None
        ref = VersionRef(logical_id=logical_id, version_id=pointer.version_id)
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        artifact = ApprovedEndStateArtifact(
            metadata=stored.metadata,
            value=ApprovedEndStateDesignation.model_validate(stored.payload),
        )
        if artifact.value.state_snapshot_ref != state_snapshot_ref:
            raise StateIdentityError("approval designation points to wrong StateSnapshot")
        await self._assert_not_invalidated(artifact.ref)
        return artifact

    async def assert_propagatable(self, state_snapshot_ref: VersionRef) -> ApprovedEndStateArtifact:
        snapshot = await self.get_version(state_snapshot_ref)
        if snapshot is None:
            raise StatePropagationBlocked("StateSnapshot exact version does not exist")
        pointer = await self.versions.get_current(state_snapshot_ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != state_snapshot_ref.version_id
            or pointer.status not in _ACCEPTED
        ):
            raise StatePropagationBlocked(
                "only exact current APPROVED/LOCKED StateSnapshot may propagate"
            )
        await self._assert_not_invalidated(state_snapshot_ref)
        await self._assert_snapshot_sources_current(
            snapshot.value,
            include_previous=False,
        )
        designation = await self.get_approved_designation(state_snapshot_ref)
        if designation is None:
            raise StatePropagationBlocked(
                "StateSnapshot lacks current approved end-state designation"
            )
        for binding in designation.value.source_bindings()[1:]:
            await self._assert_exact_current_accepted(binding.source, binding.role)
        return designation

    async def _ensure_designation_draft(
        self,
        *,
        designation: ApprovedEndStateDesignation,
        provenance: Provenance,
        created_at: datetime,
    ) -> ApprovedEndStateArtifact:
        ref = designation.ref
        existing = await self.versions.get_version(ref)
        if existing is not None:
            artifact = ApprovedEndStateArtifact(
                metadata=existing.metadata,
                value=ApprovedEndStateDesignation.model_validate(existing.payload),
            )
            if artifact.value != designation or artifact.metadata.provenance != provenance:
                raise StateApprovalBlocked(
                    "approval designation retry conflicts with persisted immutable evidence"
                )
            return artifact
        metadata = SemanticRecordMetadata(
            logical_id=designation.approval_record_id,
            version_id=designation.version_id,
            provenance=provenance,
            created_at=created_at,
        )
        stored = await self.versions.create_initial(
            metadata=metadata,
            payload=designation.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        return ApprovedEndStateArtifact(metadata=stored.metadata, value=designation)

    async def _assert_snapshot_sources_current(
        self,
        snapshot: StateSnapshot,
        *,
        include_previous: bool,
    ) -> None:
        for binding in snapshot.source_bindings():
            if binding.role == "previous_state_snapshot" and not include_previous:
                continue
            await self._assert_exact_current_accepted(binding.source, binding.role)
            if binding.role.startswith("subject_entity_"):
                stored = await self.versions.get_version(binding.source)
                assert stored is not None
                entity = EntityVersion.model_validate(stored.payload)
                if snapshot.project_id not in entity.project_ids:
                    raise StateContinuityError(
                        "StateSnapshot subject EntityVersion does not belong to project"
                    )

    async def _assert_exact_current_accepted(self, ref: VersionRef, label: str) -> None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise StateContinuityError(f"{label} exact source version does not exist")
        pointer = await self.versions.get_current(ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != ref.version_id
            or pointer.status not in _ACCEPTED
        ):
            raise StateContinuityError(f"{label} is not exact current APPROVED/LOCKED")
        await self._assert_not_invalidated(ref)

    async def _assert_not_invalidated(self, ref: VersionRef) -> None:
        for record in await self.invalidations.list_unresolved():
            if (
                record.affected_object_id == ref.logical_id
                and record.affected_object_version == ref.version_id
            ):
                raise StateContinuityError(
                    f"exact version has unresolved invalidation: {ref.logical_id.root}/{ref.version_id.root}"
                )

    def _assert_provenance(self, snapshot: StateSnapshot, provenance: Provenance) -> None:
        if provenance.source_versions != snapshot.source_bindings():
            raise StateContinuityError(
                "StateSnapshot provenance must exactly bind snapshot source versions"
            )

    @staticmethod
    def _assert_semantic_change(previous: StateSnapshot, successor: StateSnapshot) -> None:
        old = previous.model_dump(mode="json", exclude={"version_id", "previous_snapshot_ref"})
        new = successor.model_dump(mode="json", exclude={"version_id", "previous_snapshot_ref"})
        if old == new:
            raise StateContinuityError("StateSnapshot successor requires semantic change")

    async def _register_snapshot_dependencies(self, artifact: StateSnapshotArtifact) -> None:
        for binding in artifact.value.source_bindings():
            await self.graph.create_edge(
                source=binding.source,
                dependent=artifact.ref,
                edge_type="state_snapshot_source",
                dependency_reason=f"state_source:{binding.role}",
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _register_designation_dependencies(
        self,
        artifact: ApprovedEndStateArtifact,
    ) -> None:
        for binding in artifact.value.source_bindings():
            await self.graph.create_edge(
                source=binding.source,
                dependent=artifact.ref,
                edge_type="approved_end_state_source",
                dependency_reason=f"approval_source:{binding.role}",
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )


class ContinuityConstraint(BaseModel):
    """Constraint references StateFact identities without copying state values."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    constraint_key: str
    fact_keys: tuple[str, ...] = Field(min_length=1)
    required: bool = True

    @field_validator("constraint_key")
    @classmethod
    def validate_constraint_key(cls, value: str) -> str:
        return _path(value)

    @field_validator("fact_keys")
    @classmethod
    def normalize_fact_keys(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(sorted({_trimmed(value, "fact_key") for value in values}))
        return normalized


class ContinuityFinding(BaseModel):
    """Continuity evidence; message is diagnostic, never canonical state truth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    severity: FindingSeverity
    fact_keys: tuple[str, ...] = ()
    message: str
    responsible_ref: VersionRef | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        return _trimmed(value, "code")

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        return _trimmed(value, "message")

    @field_validator("fact_keys")
    @classmethod
    def normalize_fact_keys(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted({_trimmed(value, "fact_key") for value in values}))


class ContinuityLedger(BaseModel):
    """Versioned continuity evidence/constraints over exact approved sources."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    continuity_ledger_id: LogicalId
    version_id: VersionId
    scope_key: str
    state_snapshot_refs: tuple[VersionRef, ...] = Field(min_length=1)
    approval_designation_refs: tuple[VersionRef, ...] = Field(min_length=1)
    reference_asset_refs: tuple[VersionRef, ...] = ()
    approved_artifact_refs: tuple[VersionRef, ...] = ()
    constraints: tuple[ContinuityConstraint, ...] = ()
    findings: tuple[ContinuityFinding, ...] = ()

    @field_validator("scope_key")
    @classmethod
    def validate_scope(cls, value: str) -> str:
        return _scope_key(value)

    @field_validator(
        "state_snapshot_refs",
        "approval_designation_refs",
        "reference_asset_refs",
        "approved_artifact_refs",
    )
    @classmethod
    def normalize_refs(cls, values: tuple[VersionRef, ...]) -> tuple[VersionRef, ...]:
        unique = {_ref_key(ref): ref for ref in values}
        return tuple(unique[key] for key in sorted(unique))

    @model_validator(mode="after")
    def validate_identity(self) -> "ContinuityLedger":
        expected = continuity_ledger_logical_id(self.project_id, self.scope_key)
        if self.continuity_ledger_id != expected:
            raise ValueError(f"continuity_ledger_id must be {expected.root}")
        if len(self.state_snapshot_refs) != len(self.approval_designation_refs):
            raise ValueError(
                "each StateSnapshot continuity source requires one approval designation ref"
            )
        constraint_keys = [item.constraint_key for item in self.constraints]
        if len(constraint_keys) != len(set(constraint_keys)):
            raise ValueError("ContinuityConstraint keys must be unique")
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.continuity_ledger_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(role=f"state_snapshot_{index:03d}", source=ref)
            for index, ref in enumerate(self.state_snapshot_refs)
        ]
        values.extend(
            SourceVersionBinding(role=f"state_approval_{index:03d}", source=ref)
            for index, ref in enumerate(self.approval_designation_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"reference_asset_{index:03d}", source=ref)
            for index, ref in enumerate(self.reference_asset_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"approved_artifact_{index:03d}", source=ref)
            for index, ref in enumerate(self.approved_artifact_refs)
        )
        responsible_refs = {
            _ref_key(item.responsible_ref): item.responsible_ref
            for item in self.findings
            if item.responsible_ref is not None
        }
        values.extend(
            SourceVersionBinding(role=f"finding_responsible_{index:03d}", source=responsible_refs[key])
            for index, key in enumerate(sorted(responsible_refs))
        )
        return tuple(values)


class ContinuityLedgerArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: ContinuityLedger

    @model_validator(mode="after")
    def validate_artifact(self) -> "ContinuityLedgerArtifact":
        if self.metadata.logical_id != self.value.continuity_ledger_id:
            raise ValueError("ContinuityLedger metadata logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("ContinuityLedger metadata version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError("ContinuityLedger provenance must exactly bind ledger sources")
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


def build_continuity_ledger_provenance(
    ledger: ContinuityLedger,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=ledger.source_bindings(),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        correlation_id=correlation_id,
    )


def build_continuity_binding_provenance(
    *,
    ledger_ref: VersionRef,
    state_snapshot_refs: tuple[VersionRef, ...],
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    bindings = [SourceVersionBinding(role="continuity_ledger", source=ledger_ref)]
    bindings.extend(
        SourceVersionBinding(role=f"state_snapshot_{index:03d}", source=ref)
        for index, ref in enumerate(state_snapshot_refs)
    )
    return Provenance(
        source_versions=tuple(bindings),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        correlation_id=correlation_id,
    )


def build_continuity_change_provenance(
    *,
    previous_ref: VersionRef,
    successor_ref: VersionRef,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    if previous_ref.logical_id != successor_ref.logical_id:
        raise StateIdentityError("ContinuityLedger change refs must share logical identity")
    return Provenance(
        source_versions=(
            SourceVersionBinding(role="previous_continuity_ledger", source=previous_ref),
            SourceVersionBinding(role="successor_continuity_ledger", source=successor_ref),
        ),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        correlation_id=correlation_id,
    )


class ContinuityLedgerRepository:
    """Continuity evidence repository; StateSnapshot remains semantic authority."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.state = StateSnapshotRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)

    async def create_initial(
        self,
        *,
        ledger: ContinuityLedger,
        provenance: Provenance,
        created_at: datetime,
    ) -> ContinuityLedgerArtifact:
        if provenance.source_versions != ledger.source_bindings():
            raise StateContinuityError(
                "ContinuityLedger provenance must exactly bind ledger source versions"
            )
        await self._assert_sources_propagatable(ledger)
        metadata = SemanticRecordMetadata(
            logical_id=ledger.continuity_ledger_id,
            version_id=ledger.version_id,
            provenance=provenance,
            created_at=created_at,
        )
        stored = await self.versions.create_initial(
            metadata=metadata,
            payload=ledger.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        artifact = ContinuityLedgerArtifact(metadata=stored.metadata, value=ledger)
        await self._register_dependencies(artifact)
        return artifact

    async def create_successor(
        self,
        *,
        ledger: ContinuityLedger,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> ContinuityLedgerArtifact:
        if predecessor.logical_id != ledger.continuity_ledger_id:
            raise StateIdentityError("ContinuityLedger successor must preserve logical identity")
        pointer = await self.versions.get_current(ledger.continuity_ledger_id)
        if (
            pointer is None
            or pointer.version_id != predecessor.version_id
            or pointer.status not in _ACCEPTED
        ):
            raise StateIdentityError(
                "ContinuityLedger successor predecessor must be exact current accepted"
            )
        previous = await self.get_version(predecessor)
        if previous is None:
            raise StateIdentityError("ContinuityLedger predecessor does not exist")
        if provenance.source_versions != ledger.source_bindings():
            raise StateContinuityError(
                "ContinuityLedger provenance must exactly bind ledger source versions"
            )
        old_payload = previous.value.model_dump(mode="json", exclude={"version_id"})
        new_payload = ledger.model_dump(mode="json", exclude={"version_id"})
        if old_payload == new_payload:
            raise StateContinuityError("ContinuityLedger successor requires semantic change")
        await self._assert_sources_propagatable(ledger)
        metadata = SemanticRecordMetadata(
            logical_id=ledger.continuity_ledger_id,
            version_id=ledger.version_id,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
        )
        stored = await self.versions.create_successor(
            metadata=metadata,
            payload=ledger.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        artifact = ContinuityLedgerArtifact(metadata=stored.metadata, value=ledger)
        await self._register_dependencies(artifact)
        return artifact

    async def get_version(self, ref: VersionRef) -> ContinuityLedgerArtifact | None:
        if not ref.logical_id.root.startswith("continuity-ledger:"):
            raise StateIdentityError("expected ContinuityLedger ref")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        return ContinuityLedgerArtifact(
            metadata=stored.metadata,
            value=ContinuityLedger.model_validate(stored.payload),
        )

    async def promote_current(
        self,
        *,
        ref: VersionRef,
        expected_revision: int,
        status: LifecycleState = LifecycleState.APPROVED,
    ) -> CurrentVersionPointer:
        if status not in _ACCEPTED:
            raise StateContinuityError("ContinuityLedger status must be APPROVED or LOCKED")
        artifact = await self.get_version(ref)
        if artifact is None:
            raise StateContinuityError("ContinuityLedger exact version does not exist")
        if artifact.metadata.predecessor is not None:
            raise StateContinuityError(
                "ContinuityLedger successor must use promote_successor_current"
            )
        await self._assert_sources_propagatable(artifact.value)
        return await self.versions.update_current(
            logical_id=ref.logical_id,
            version_id=ref.version_id,
            status=status,
            expected_revision=expected_revision,
        )

    async def promote_successor_current(
        self,
        *,
        ref: VersionRef,
        expected_revision: int,
        invalidation_provenance: Provenance,
        repair_or_recompute_requirement: str,
        status: LifecycleState = LifecycleState.APPROVED,
    ) -> tuple[CurrentVersionPointer, tuple[InvalidationRecord, ...]]:
        if status not in _ACCEPTED:
            raise StateContinuityError("ContinuityLedger status must be APPROVED or LOCKED")
        artifact = await self.get_version(ref)
        if artifact is None:
            raise StateContinuityError("ContinuityLedger exact version does not exist")
        predecessor = artifact.metadata.predecessor
        if predecessor is None:
            raise StateContinuityError("initial ContinuityLedger must use promote_current")
        expected_change_bindings = (
            SourceVersionBinding(role="previous_continuity_ledger", source=predecessor),
            SourceVersionBinding(role="successor_continuity_ledger", source=ref),
        )
        if invalidation_provenance.source_versions != expected_change_bindings:
            raise StateContinuityError(
                "ContinuityLedger change provenance must exactly bind old/new versions"
            )
        pointer = await self.versions.get_current(ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != predecessor.version_id
            or pointer.status not in _ACCEPTED
            or pointer.revision != expected_revision
        ):
            raise StateIdentityError(
                "ContinuityLedger successor activation requires exact current predecessor/revision"
            )
        await self._assert_sources_propagatable(artifact.value)
        invalidations = await self.invalidations.create_for_change(
            cause="CONTINUITY_LEDGER_CHANGED",
            source_old=predecessor,
            source_new=ref,
            provenance=invalidation_provenance,
            scope="CONTINUITY_LEDGER",
            repair_or_recompute_requirement=_trimmed(
                repair_or_recompute_requirement,
                "repair_or_recompute_requirement",
            ),
        )
        updated = await self.versions.update_current(
            logical_id=ref.logical_id,
            version_id=ref.version_id,
            status=status,
            expected_revision=expected_revision,
        )
        return updated, tuple(invalidations)

    async def bind_consumer(
        self,
        *,
        ledger_ref: VersionRef,
        consumer_ref: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> None:
        ledger = await self.get_version(ledger_ref)
        if ledger is None:
            raise StatePropagationBlocked("ContinuityLedger exact version does not exist")
        expected_bindings = build_continuity_binding_provenance(
            ledger_ref=ledger_ref,
            state_snapshot_refs=ledger.value.state_snapshot_refs,
            actor_ref=provenance.actor_ref,
            reason=provenance.reason,
            recorded_at=provenance.recorded_at,
            source_refs=provenance.source_refs,
            correlation_id=provenance.correlation_id,
        ).source_versions
        if provenance.source_versions != expected_bindings:
            raise StatePropagationBlocked(
                "continuity consumer provenance must exactly bind ledger + StateSnapshot versions"
            )
        pointer = await self.versions.get_current(ledger_ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != ledger_ref.version_id
            or pointer.status not in _ACCEPTED
        ):
            raise StatePropagationBlocked("ContinuityLedger is not current accepted")
        await self._assert_sources_propagatable(ledger.value)
        consumer = await self.versions.get_version(consumer_ref)
        if consumer is None:
            raise StatePropagationBlocked("continuity consumer exact version does not exist")
        await self.graph.create_edge(
            source=ledger_ref,
            dependent=consumer_ref,
            edge_type="continuity_propagation",
            dependency_reason="consumer binds exact accepted continuity ledger",
            provenance=provenance,
            created_at=created_at,
        )
        for state_ref in ledger.value.state_snapshot_refs:
            await self.graph.create_edge(
                source=state_ref,
                dependent=consumer_ref,
                edge_type="state_continuity_binding",
                dependency_reason="consumer binds exact approved StateSnapshot",
                provenance=provenance,
                created_at=created_at,
            )

    async def _assert_sources_propagatable(self, ledger: ContinuityLedger) -> None:
        state_designations: dict[tuple[str, str], VersionRef] = {}
        for designation_ref in ledger.approval_designation_refs:
            stored = await self.versions.get_version(designation_ref)
            if stored is None:
                raise StatePropagationBlocked("approval designation exact version does not exist")
            designation = ApprovedEndStateDesignation.model_validate(stored.payload)
            pointer = await self.versions.get_current(designation_ref.logical_id)
            if (
                pointer is None
                or pointer.version_id != designation_ref.version_id
                or pointer.status not in _ACCEPTED
            ):
                raise StatePropagationBlocked("approval designation is not current accepted")
            state_designations[_ref_key(designation.state_snapshot_ref)] = designation_ref

        available_fact_keys: set[str] = set()
        for state_ref in ledger.state_snapshot_refs:
            actual = await self.state.assert_propagatable(state_ref)
            mapped = state_designations.get(_ref_key(state_ref))
            if mapped is None or mapped != actual.ref:
                raise StatePropagationBlocked(
                    "ContinuityLedger state/designation exact-version mapping mismatch"
                )
            state_artifact = await self.state.get_version(state_ref)
            assert state_artifact is not None
            available_fact_keys.update(fact.fact_key for fact in state_artifact.value.facts)

        referenced_fact_keys = {
            key
            for item in (*ledger.constraints, *ledger.findings)
            for key in item.fact_keys
        }
        missing_fact_keys = sorted(referenced_fact_keys - available_fact_keys)
        if missing_fact_keys:
            raise StatePropagationBlocked(
                "ContinuityLedger references unknown StateFact keys: "
                + ",".join(missing_fact_keys)
            )

        for ref in (*ledger.reference_asset_refs, *ledger.approved_artifact_refs):
            stored = await self.versions.get_version(ref)
            if stored is None:
                raise StatePropagationBlocked("continuity source exact version does not exist")
            pointer = await self.versions.get_current(ref.logical_id)
            if (
                pointer is None
                or pointer.version_id != ref.version_id
                or pointer.status not in _ACCEPTED
            ):
                raise StatePropagationBlocked("continuity source is not exact current accepted")
            for record in await self.invalidations.list_unresolved():
                if (
                    record.affected_object_id == ref.logical_id
                    and record.affected_object_version == ref.version_id
                ):
                    raise StatePropagationBlocked("continuity source has unresolved invalidation")

    async def _register_dependencies(self, artifact: ContinuityLedgerArtifact) -> None:
        for binding in artifact.value.source_bindings():
            await self.graph.create_edge(
                source=binding.source,
                dependent=artifact.ref,
                edge_type="continuity_ledger_source",
                dependency_reason=f"continuity_source:{binding.role}",
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )


class LegacyMediaChainConditioning(BaseModel):
    """Compatibility-only execution input; never canonical StateSnapshot authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    parent_scene_id: str | None = None
    source_image_media_id: str | None = None
    end_scene_media_id: str | None = None

    @field_validator("parent_scene_id")
    @classmethod
    def validate_parent_scene_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _trimmed(value, "parent_scene_id")

    @field_validator("source_image_media_id", "end_scene_media_id")
    @classmethod
    def validate_media_id(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        text = _trimmed(value, info.field_name)
        try:
            parsed = UUID(text)
        except ValueError as exc:
            raise ValueError(f"{info.field_name} must be a UUID media ID") from exc
        if str(parsed) != text.lower():
            raise ValueError(f"{info.field_name} must use canonical UUID form")
        return text.lower()
