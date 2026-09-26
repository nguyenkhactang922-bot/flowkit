"""Immutable ActiveProductionProfile snapshots and selective profile invalidation.

IMP-013 materializes the exact output of the canonical Profile Resolver into a
pinned, immutable effective-policy snapshot. Downstream consumers bind an exact
profile version; they never receive BrainPack definitions or resolver authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from .brainpack import BrainPackRef
from .invalidation import (
    DependencyGraphRepository,
    DependencyReachability,
    InvalidationRecord,
    InvalidationRepository,
)
from .primitives import (
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    VersionId,
    VersionRef,
)
from .profile_resolver import (
    AuthorityTier,
    FieldResolutionTrace,
    PolicySourceKind,
    ProfileResolutionArtifact,
)
from .versioning import CurrentVersionPointer, VersionRepository


_PATH_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
_PROFILE_PATH_EDGE_PREFIX = "PROFILE_PATH:"


class ActiveProductionProfileError(ValueError):
    """Base error for canonical ActiveProductionProfile operations."""


class ActiveProductionProfileMismatch(ActiveProductionProfileError):
    """Raised when profile identity/source lineage is inconsistent."""


class ProfilePathBindingError(ActiveProductionProfileError):
    """Raised when a downstream path dependency is invalid."""


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _policy_path(value: str, *, allow_wildcard: bool = False) -> str:
    normalized = _trimmed(value, "policy path").lower()
    if allow_wildcard and normalized == "*":
        return normalized
    if not _PATH_RE.fullmatch(normalized):
        raise ValueError(
            "policy path must start with a lowercase letter and contain only "
            "lowercase letters, digits, '.', '_', or '-'"
        )
    return normalized


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
        raise ValueError("profile snapshot value must be canonical JSON data") from exc


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_text(_canonical_json(value))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _active_profile_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"active-profile:{project_id.root}")


def _profile_resolution_logical_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"profile-resolution:{project_id.root}")


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return (ref.logical_id.root, ref.version_id.root)


def _pack_ref_key(ref: BrainPackRef) -> tuple[str, str]:
    return (ref.pack_id.root, ref.pack_version.root)


class EffectivePolicyPathProvenance(BaseModel):
    """Winning authority provenance pinned for one effective policy path."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    winning_tier: AuthorityTier
    precedence_rank: int = Field(ge=0, le=5)
    winning_source_kind: PolicySourceKind
    winning_source_ref: VersionRef
    winning_pack_ref: BrainPackRef | None = None
    resolution_reason: str

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _policy_path(value)

    @field_validator("resolution_reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        return _trimmed(value, "resolution_reason")


class EffectivePolicyEntry(BaseModel):
    """Deeply immutable policy entry: JSON bytes, hash and path provenance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    value_json: str
    value_hash: str
    provenance: EffectivePolicyPathProvenance

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _policy_path(value)

    @model_validator(mode="after")
    def validate_entry(self) -> "EffectivePolicyEntry":
        if self.provenance.path != self.path:
            raise ValueError("policy entry/provenance path mismatch")
        try:
            decoded = json.loads(self.value_json)
        except json.JSONDecodeError as exc:
            raise ValueError("value_json must contain valid JSON") from exc
        canonical = _canonical_json(decoded)
        if canonical != self.value_json:
            raise ValueError("value_json must be canonical JSON")
        if _sha256_text(self.value_json) != self.value_hash:
            raise ValueError("policy entry value_hash mismatch")
        return self

    @property
    def value(self) -> Any:
        """Return a fresh decoded value so callers cannot mutate the snapshot."""

        return json.loads(self.value_json)


class ActiveProductionProfile(BaseModel):
    """Immutable pinned effective-policy snapshot consumed by downstream stages."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_id: LogicalId
    profile_version: VersionId
    project_id: LogicalId
    resolver_version: VersionRef
    profile_resolution_ref: VersionRef
    resolution_id: LogicalId
    project_ref: VersionRef
    topic_ref: VersionRef
    domain_ref: VersionRef
    effective_pack_refs: tuple[BrainPackRef, ...]
    policy_entries: tuple[EffectivePolicyEntry, ...]
    input_fingerprint: str
    effective_policy_hash: str
    resolution_trace_hash: str

    @model_validator(mode="after")
    def validate_profile(self) -> "ActiveProductionProfile":
        expected_id = _active_profile_logical_id(self.project_id)
        if self.profile_id != expected_id:
            raise ValueError(f"profile_id must be {expected_id.root}")
        expected_resolution_id = _profile_resolution_logical_id(self.project_id)
        if self.profile_resolution_ref.logical_id != expected_resolution_id:
            raise ValueError("profile_resolution_ref belongs to a different project")

        paths = [entry.path for entry in self.policy_entries]
        if paths != sorted(paths):
            raise ValueError("policy_entries must be sorted by path")
        if len(paths) != len(set(paths)):
            raise ValueError("policy_entries paths must be unique")

        pack_keys = [_pack_ref_key(ref) for ref in self.effective_pack_refs]
        if pack_keys != sorted(pack_keys):
            raise ValueError("effective_pack_refs must be sorted")
        if len(pack_keys) != len(set(pack_keys)):
            raise ValueError("effective_pack_refs must be unique")

        if _sha256_json(self.effective_policy) != self.effective_policy_hash:
            raise ValueError("effective_policy_hash mismatch")
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(
            logical_id=self.profile_id,
            version_id=self.profile_version,
        )

    @property
    def effective_policy(self) -> dict[str, Any]:
        return {entry.path: entry.value for entry in self.policy_entries}

    @property
    def path_provenance(self) -> dict[str, EffectivePolicyPathProvenance]:
        return {entry.path: entry.provenance for entry in self.policy_entries}


class ActiveProductionProfileArtifact(BaseModel):
    """Persisted profile snapshot with canonical semantic metadata."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    profile: ActiveProductionProfile

    @model_validator(mode="after")
    def validate_artifact(self) -> "ActiveProductionProfileArtifact":
        if self.metadata.logical_id != self.profile.profile_id:
            raise ValueError("profile metadata logical_id mismatch")
        if self.metadata.version_id != self.profile.profile_version:
            raise ValueError("profile metadata version_id mismatch")
        _validate_profile_provenance(self.profile, self.metadata.provenance)
        return self

    @property
    def ref(self) -> VersionRef:
        return self.profile.ref


class ActiveProductionProfileBinding(BaseModel):
    """Downstream contract: bind one exact profile version, never re-resolve packs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_ref: VersionRef
    required_paths: tuple[str, ...] = ()

    @field_validator("required_paths")
    @classmethod
    def validate_required_paths(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(sorted({_policy_path(value) for value in values}))
        return normalized


class ProfileChangeSet(BaseModel):
    """Deterministic semantic/path delta between two profile versions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_id: LogicalId
    old_profile_ref: VersionRef
    new_profile_ref: VersionRef
    added_paths: tuple[str, ...]
    removed_paths: tuple[str, ...]
    value_changed_paths: tuple[str, ...]
    provenance_changed_paths: tuple[str, ...]
    changed_paths: tuple[str, ...]

    @model_validator(mode="after")
    def validate_change_set(self) -> "ProfileChangeSet":
        all_groups = (
            self.added_paths,
            self.removed_paths,
            self.value_changed_paths,
            self.provenance_changed_paths,
            self.changed_paths,
        )
        for values in all_groups:
            if tuple(sorted(set(values))) != values:
                raise ValueError("profile change paths must be sorted and unique")
        expected = tuple(
            sorted(
                set(self.added_paths)
                | set(self.removed_paths)
                | set(self.value_changed_paths)
                | set(self.provenance_changed_paths)
            )
        )
        if self.changed_paths != expected:
            raise ValueError("changed_paths must equal the union of path deltas")
        return self


class ProfileInvalidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    change_set: ProfileChangeSet
    invalidations: tuple[InvalidationRecord, ...]


def _entry_from_trace(field: FieldResolutionTrace) -> EffectivePolicyEntry:
    value_json = _canonical_json(field.value)
    return EffectivePolicyEntry(
        path=field.path,
        value_json=value_json,
        value_hash=_sha256_text(value_json),
        provenance=EffectivePolicyPathProvenance(
            path=field.path,
            winning_tier=field.winning_tier,
            precedence_rank=field.precedence_rank,
            winning_source_kind=field.winning_source_kind,
            winning_source_ref=field.winning_source_ref,
            winning_pack_ref=field.winning_pack_ref,
            resolution_reason=field.resolution_reason,
        ),
    )


def materialize_active_profile(
    resolution: ProfileResolutionArtifact,
    *,
    profile_version: VersionId,
) -> ActiveProductionProfile:
    """Materialize an immutable snapshot from one exact resolver artifact."""

    result = resolution.result
    trace = result.trace
    entries = tuple(
        _entry_from_trace(field)
        for field in sorted(trace.fields, key=lambda item: item.path)
    )
    entry_paths = {entry.path for entry in entries}
    if entry_paths != set(result.effective_policy):
        raise ActiveProductionProfileMismatch(
            "resolution trace fields do not exactly cover effective policy paths"
        )
    for entry in entries:
        if entry.value != result.effective_policy[entry.path]:
            raise ActiveProductionProfileMismatch(
                f"resolution trace value mismatch at {entry.path}"
            )

    return ActiveProductionProfile(
        profile_id=_active_profile_logical_id(result.project_id),
        profile_version=profile_version,
        project_id=result.project_id,
        resolver_version=trace.resolver_version,
        profile_resolution_ref=resolution.ref,
        resolution_id=trace.resolution_id,
        project_ref=trace.project_ref,
        topic_ref=trace.topic_ref,
        domain_ref=trace.domain_ref,
        effective_pack_refs=tuple(
            sorted(trace.effective_pack_refs, key=_pack_ref_key)
        ),
        policy_entries=entries,
        input_fingerprint=trace.input_fingerprint,
        effective_policy_hash=trace.effective_policy_hash,
        resolution_trace_hash=_sha256_json(trace.model_dump(mode="json")),
    )


def _expected_profile_source_bindings(
    profile: ActiveProductionProfile,
) -> tuple[SourceVersionBinding, ...]:
    bindings: list[SourceVersionBinding] = [
        SourceVersionBinding(
            role="profile_resolution",
            source=profile.profile_resolution_ref,
        ),
        SourceVersionBinding(role="project_input", source=profile.project_ref),
        SourceVersionBinding(role="topic_resolution", source=profile.topic_ref),
        SourceVersionBinding(role="domain_resolution", source=profile.domain_ref),
    ]
    for index, ref in enumerate(profile.effective_pack_refs):
        bindings.append(
            SourceVersionBinding(
                role=f"effective_brainpack_{index:03d}",
                source=VersionRef(
                    logical_id=ref.pack_id,
                    version_id=ref.pack_version,
                ),
            )
        )
    return tuple(bindings)


def build_active_profile_provenance(
    profile: ActiveProductionProfile,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=_expected_profile_source_bindings(profile),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        rule_version=profile.resolver_version,
        correlation_id=correlation_id,
    )


def _validate_profile_provenance(
    profile: ActiveProductionProfile,
    provenance: Provenance,
) -> None:
    if provenance.rule_version != profile.resolver_version:
        raise ValueError("ActiveProductionProfile resolver version mismatch")
    if provenance.source_versions != _expected_profile_source_bindings(profile):
        raise ValueError(
            "ActiveProductionProfile provenance does not match exact pinned sources"
        )


def diff_active_profiles(
    old: ActiveProductionProfile,
    new: ActiveProductionProfile,
) -> ProfileChangeSet:
    if old.profile_id != new.profile_id or old.project_id != new.project_id:
        raise ActiveProductionProfileMismatch(
            "profile versions must share profile_id and project_id"
        )
    if old.profile_version == new.profile_version:
        raise ActiveProductionProfileMismatch(
            "profile versions must have different version IDs"
        )

    old_entries = {entry.path: entry for entry in old.policy_entries}
    new_entries = {entry.path: entry for entry in new.policy_entries}
    old_paths = set(old_entries)
    new_paths = set(new_entries)

    added = tuple(sorted(new_paths - old_paths))
    removed = tuple(sorted(old_paths - new_paths))

    value_changed: list[str] = []
    provenance_changed: list[str] = []
    for path in sorted(old_paths & new_paths):
        old_entry = old_entries[path]
        new_entry = new_entries[path]
        if old_entry.value_json != new_entry.value_json:
            value_changed.append(path)
        if (
            old_entry.provenance.model_dump(mode="json")
            != new_entry.provenance.model_dump(mode="json")
        ):
            provenance_changed.append(path)

    changed = tuple(
        sorted(set(added) | set(removed) | set(value_changed) | set(provenance_changed))
    )
    return ProfileChangeSet(
        profile_id=old.profile_id,
        old_profile_ref=old.ref,
        new_profile_ref=new.ref,
        added_paths=added,
        removed_paths=removed,
        value_changed_paths=tuple(value_changed),
        provenance_changed_paths=tuple(provenance_changed),
        changed_paths=changed,
    )


class ActiveProductionProfileRepository:
    """Immutable profile persistence over the canonical VersionRepository."""

    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)

    async def create_initial(
        self,
        *,
        profile: ActiveProductionProfile,
        provenance: Provenance,
        created_at: datetime,
    ) -> ActiveProductionProfileArtifact:
        artifact = self._artifact(
            profile=profile,
            provenance=provenance,
            created_at=created_at,
            predecessor=None,
        )
        stored = await self.versions.create_initial(
            metadata=artifact.metadata,
            payload=profile.model_dump(mode="json"),
            status=LifecycleState.LOCKED,
        )
        return ActiveProductionProfileArtifact(
            metadata=stored.metadata,
            profile=profile,
        )

    async def create_successor(
        self,
        *,
        profile: ActiveProductionProfile,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
    ) -> ActiveProductionProfileArtifact:
        if predecessor.logical_id != profile.profile_id:
            raise ActiveProductionProfileMismatch(
                "profile predecessor must share profile_id"
            )
        artifact = self._artifact(
            profile=profile,
            provenance=provenance,
            created_at=created_at,
            predecessor=predecessor,
        )
        stored = await self.versions.create_successor(
            metadata=artifact.metadata,
            payload=profile.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        return ActiveProductionProfileArtifact(
            metadata=stored.metadata,
            profile=profile,
        )

    async def pin_current(
        self,
        *,
        profile_ref: VersionRef,
        expected_revision: int,
    ) -> CurrentVersionPointer:
        return await self.versions.update_current(
            logical_id=profile_ref.logical_id,
            version_id=profile_ref.version_id,
            status=LifecycleState.LOCKED,
            expected_revision=expected_revision,
        )

    async def get(
        self,
        ref: VersionRef,
    ) -> ActiveProductionProfileArtifact | None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        profile = ActiveProductionProfile.model_validate(stored.payload)
        return ActiveProductionProfileArtifact(
            metadata=stored.metadata,
            profile=profile,
        )

    async def get_current(
        self,
        project_id: LogicalId,
    ) -> ActiveProductionProfileArtifact | None:
        logical_id = _active_profile_logical_id(project_id)
        try:
            pointer = await self.versions.get_current(logical_id)
        except Exception as exc:
            # VersionRepository uses a typed not-found error, but this domain
            # presents absence as None like other Studio read adapters.
            from .versioning import CurrentPointerNotFound

            if isinstance(exc, CurrentPointerNotFound):
                return None
            raise
        return await self.get(
            VersionRef(logical_id=logical_id, version_id=pointer.version_id)
        )

    @staticmethod
    def _artifact(
        *,
        profile: ActiveProductionProfile,
        provenance: Provenance,
        created_at: datetime,
        predecessor: VersionRef | None,
    ) -> ActiveProductionProfileArtifact:
        metadata = SemanticRecordMetadata(
            logical_id=profile.profile_id,
            version_id=profile.profile_version,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
        )
        return ActiveProductionProfileArtifact(
            metadata=metadata,
            profile=profile,
        )


def profile_path_edge_type(path: str) -> str:
    normalized = _policy_path(path, allow_wildcard=True)
    return _PROFILE_PATH_EDGE_PREFIX + normalized


class ActiveProductionProfileDependencyBinder:
    """Create exact downstream dependency edges against one pinned profile."""

    def __init__(self, graph: DependencyGraphRepository) -> None:
        self.graph = graph

    async def bind(
        self,
        *,
        profile: ActiveProductionProfile,
        dependent: VersionRef,
        path: str,
        reason: str,
        provenance: Provenance,
        created_at: datetime | None = None,
    ):
        normalized = _policy_path(path, allow_wildcard=True)
        if normalized != "*" and normalized not in profile.effective_policy:
            raise ProfilePathBindingError(
                f"profile path does not exist in pinned snapshot: {normalized}"
            )
        return await self.graph.create_edge(
            source=profile.ref,
            dependent=dependent,
            edge_type=profile_path_edge_type(normalized),
            dependency_reason=_trimmed(reason, "dependency reason"),
            provenance=provenance,
            created_at=created_at or _utc_now(),
        )


class ActiveProductionProfileInvalidationService:
    """Selective dependency invalidation for changed profile paths."""

    def __init__(
        self,
        graph: DependencyGraphRepository,
        invalidations: InvalidationRepository,
    ) -> None:
        self.graph = graph
        self.invalidations = invalidations

    async def invalidate_change(
        self,
        *,
        old: ActiveProductionProfile,
        new: ActiveProductionProfile,
        provenance: Provenance,
        repair_or_recompute_requirement: str,
    ) -> ProfileInvalidationResult:
        change_set = diff_active_profiles(old, new)
        if not change_set.changed_paths:
            return ProfileInvalidationResult(
                change_set=change_set,
                invalidations=(),
            )

        reachable = await self._select_reachability(
            source=old.ref,
            changed_paths=change_set.changed_paths,
        )
        records = await self.invalidations.create_for_change(
            cause="ACTIVE_PRODUCTION_PROFILE_CHANGED",
            source_old=old.ref,
            source_new=new.ref,
            provenance=provenance,
            scope="ACTIVE_PROFILE_PATHS:" + ",".join(change_set.changed_paths),
            repair_or_recompute_requirement=_trimmed(
                repair_or_recompute_requirement,
                "repair_or_recompute_requirement",
            ),
            reachable=reachable,
        )
        return ProfileInvalidationResult(
            change_set=change_set,
            invalidations=tuple(records),
        )

    async def _select_reachability(
        self,
        *,
        source: VersionRef,
        changed_paths: tuple[str, ...],
    ) -> list[DependencyReachability]:
        allowed_edge_types = {
            profile_path_edge_type(path) for path in changed_paths
        }
        allowed_edge_types.add(profile_path_edge_type("*"))

        selected: dict[tuple[str, str], DependencyReachability] = {}

        def consider(item: DependencyReachability) -> None:
            if item.ref == source:
                return
            key = _ref_key(item.ref)
            existing = selected.get(key)
            item_rank = (item.depth, item.path_edge_ids, item.via_edge_id)
            if existing is None:
                selected[key] = item
                return
            existing_rank = (
                existing.depth,
                existing.path_edge_ids,
                existing.via_edge_id,
            )
            if item_rank < existing_rank:
                selected[key] = item

        for edge in await self.graph.list_outgoing(source):
            if edge.edge_type not in allowed_edge_types:
                continue
            direct = DependencyReachability(
                object_id=edge.dependent_object_id,
                version_id=edge.dependent_version,
                via_edge_id=edge.edge_id,
                via_edge_type=edge.edge_type,
                dependency_reason=edge.dependency_reason,
                depth=1,
                path_edge_ids=(edge.edge_id,),
            )
            consider(direct)
            for descendant in await self.graph.descendants(edge.dependent_ref):
                consider(
                    DependencyReachability(
                        object_id=descendant.object_id,
                        version_id=descendant.version_id,
                        via_edge_id=descendant.via_edge_id,
                        via_edge_type=descendant.via_edge_type,
                        dependency_reason=descendant.dependency_reason,
                        depth=descendant.depth + 1,
                        path_edge_ids=(edge.edge_id,) + descendant.path_edge_ids,
                    )
                )

        return [
            selected[key]
            for key in sorted(selected)
        ]
