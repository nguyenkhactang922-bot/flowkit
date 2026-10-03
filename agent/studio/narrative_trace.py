"""IMP-028 exact-version NarrativeTrace lineage/provenance service.

NarrativeTrace owns trace evidence only. Canonical StoryCore/MacroStoryBeat/Sequence/
Scene/SceneDramaticBeat/Shot truth remains owned by its domain repository, while the
shared DependencyGraph remains the only dependency truth.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .invalidation import (
    DependencyGraphRepository,
    DependencyReachability,
    InvalidationRepository,
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
from .versioning import VersionRepository


class NarrativeTraceError(ValueError):
    """Base error for NarrativeTrace operations."""


class NarrativeTraceIdentityError(NarrativeTraceError):
    """Raised when trace identity/provenance crosses canonical authority."""


class NarrativeTraceFindingCode(str, Enum):
    TRACE_ORPHAN_ARTIFACT = "TRACE_ORPHAN_ARTIFACT"
    TRACE_MISSING_PARENT = "TRACE_MISSING_PARENT"
    TRACE_CYCLE = "TRACE_CYCLE"
    TRACE_STALE_SOURCE = "TRACE_STALE_SOURCE"
    TRACE_CONTRADICTORY_PARENT = "TRACE_CONTRADICTORY_PARENT"


class NarrativeTraceGateBlocked(NarrativeTraceError):
    """Fail-closed trace validation with a stable finding code."""

    def __init__(self, code: NarrativeTraceFindingCode, message: str) -> None:
        super().__init__(f"{code.value}: {message}")
        self.code = code


class NarrativeArtifactType(str, Enum):
    STORY_CORE = "STORY_CORE"
    MACRO_STORY_BEAT = "MACRO_STORY_BEAT"
    SEQUENCE = "SEQUENCE"
    SCENE = "SCENE"
    SCENE_DRAMATIC_BEAT = "SCENE_DRAMATIC_BEAT"
    SHOT_LIST_ITEM = "SHOT_LIST_ITEM"


class NarrativeTraceState(str, Enum):
    CURRENT = "CURRENT"
    SUPERSEDED = "SUPERSEDED"
    INVALIDATED = "INVALIDATED"


_ARTIFACT_PREFIX: dict[NarrativeArtifactType, str] = {
    NarrativeArtifactType.STORY_CORE: "story-core:",
    NarrativeArtifactType.MACRO_STORY_BEAT: "macro-story-beat:",
    NarrativeArtifactType.SEQUENCE: "sequence:",
    NarrativeArtifactType.SCENE: "scene:",
    NarrativeArtifactType.SCENE_DRAMATIC_BEAT: "scene-dramatic-beat:",
    NarrativeArtifactType.SHOT_LIST_ITEM: "shot-list-item:",
}

_REQUIRED_PARENT: dict[NarrativeArtifactType, NarrativeArtifactType | None] = {
    NarrativeArtifactType.STORY_CORE: None,
    NarrativeArtifactType.MACRO_STORY_BEAT: NarrativeArtifactType.STORY_CORE,
    NarrativeArtifactType.SEQUENCE: NarrativeArtifactType.MACRO_STORY_BEAT,
    NarrativeArtifactType.SCENE: NarrativeArtifactType.SEQUENCE,
    NarrativeArtifactType.SCENE_DRAMATIC_BEAT: NarrativeArtifactType.SCENE,
    NarrativeArtifactType.SHOT_LIST_ITEM: NarrativeArtifactType.SCENE_DRAMATIC_BEAT,
}

_ACCEPTED_SOURCE_STATES = {LifecycleState.APPROVED, LifecycleState.LOCKED}


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return ref.logical_id.root, ref.version_id.root


def _is_project_scoped(
    ref: VersionRef,
    *,
    prefix: str,
    project_id: LogicalId,
) -> bool:
    base = f"{prefix}{project_id.root}"
    root = ref.logical_id.root
    return root == base or root.startswith(base + ":")


def _type_for_ref(
    ref: VersionRef,
    *,
    project_id: LogicalId | None = None,
) -> NarrativeArtifactType | None:
    root = ref.logical_id.root
    for artifact_type, prefix in _ARTIFACT_PREFIX.items():
        if project_id is None:
            if root.startswith(prefix):
                return artifact_type
        elif _is_project_scoped(ref, prefix=prefix, project_id=project_id):
            return artifact_type
    return None


def narrative_trace_logical_id(
    artifact_type: NarrativeArtifactType,
    traced_ref: VersionRef,
) -> LogicalId:
    """Stable trace identity without becoming a second narrative object identity."""

    raw = f"{artifact_type.value}\0{traced_ref.logical_id.root}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:32]
    return LogicalId(f"narrative-trace:{artifact_type.value.lower()}:{digest}")


class NarrativeTraceRecord(BaseModel):
    """Immutable exact-version trace evidence for one canonical narrative artifact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    artifact_type: NarrativeArtifactType
    trace_version: VersionId
    traced_ref: VersionRef
    root_story_core_ref: VersionRef
    parent_refs: tuple[VersionRef, ...] = ()
    source_version_refs: tuple[VersionRef, ...] = ()

    @model_validator(mode="after")
    def validate_authority(self) -> "NarrativeTraceRecord":
        actual_type = _type_for_ref(self.traced_ref, project_id=self.project_id)
        if actual_type is not self.artifact_type:
            raise ValueError(
                "traced_ref must be canonical artifact of artifact_type in same project"
            )

        expected_root = f"story-core:{self.project_id.root}"
        if self.root_story_core_ref.logical_id.root != expected_root:
            raise ValueError("root_story_core_ref must be canonical StoryCore for same project")

        required_parent_type = _REQUIRED_PARENT[self.artifact_type]
        if required_parent_type is None:
            if self.traced_ref != self.root_story_core_ref:
                raise ValueError("StoryCore trace must trace the declared root StoryCore")
            if self.parent_refs:
                raise ValueError("StoryCore trace must not declare canonical parents")
        else:
            if not self.parent_refs:
                raise ValueError("derived narrative trace requires canonical parent_refs")
            for parent_ref in self.parent_refs:
                if (
                    _type_for_ref(parent_ref, project_id=self.project_id)
                    is not required_parent_type
                ):
                    raise ValueError(
                        "parent_refs must use the required canonical parent type in same project"
                    )
            if self.artifact_type is not NarrativeArtifactType.SEQUENCE and len(self.parent_refs) != 1:
                raise ValueError("this narrative artifact requires exactly one canonical parent")

        parent_keys = [_ref_key(ref) for ref in self.parent_refs]
        if len(parent_keys) != len(set(parent_keys)):
            raise ValueError("parent_refs must not contain duplicates")

        source_keys = [_ref_key(ref) for ref in self.source_version_refs]
        if len(source_keys) != len(set(source_keys)):
            raise ValueError("source_version_refs must not contain duplicates")
        if _ref_key(self.traced_ref) in set(source_keys):
            raise ValueError("source_version_refs must not duplicate traced_ref")
        return self

    @property
    def logical_id(self) -> LogicalId:
        return narrative_trace_logical_id(self.artifact_type, self.traced_ref)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.trace_version)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        bindings: list[SourceVersionBinding] = [
            SourceVersionBinding(role="traced_artifact", source=self.traced_ref),
            SourceVersionBinding(role="root_story_core", source=self.root_story_core_ref),
        ]
        bindings.extend(
            SourceVersionBinding(role=f"parent_{index:03d}", source=ref)
            for index, ref in enumerate(self.parent_refs)
        )
        bindings.extend(
            SourceVersionBinding(role=f"source_{index:03d}", source=ref)
            for index, ref in enumerate(self.source_version_refs)
        )
        return tuple(bindings)


class NarrativeTraceArtifact(BaseModel):
    """Persisted trace semantic version plus typed trace value."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: NarrativeTraceRecord

    @property
    def ref(self) -> VersionRef:
        return VersionRef(
            logical_id=self.metadata.logical_id,
            version_id=self.metadata.version_id,
        )


class NarrativeWhyExists(BaseModel):
    """Bottom-up exact-version explanation for why an artifact exists."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    trace_ref: VersionRef
    traced_ref: VersionRef
    root_story_core_ref: VersionRef
    parent_refs: tuple[VersionRef, ...]
    state: NarrativeTraceState
    ancestors: tuple[DependencyReachability, ...] = Field(default=())


def build_narrative_trace_provenance(
    value: NarrativeTraceRecord,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    rule_version: VersionRef | None = None,
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=value.source_bindings(),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        rule_version=rule_version,
        correlation_id=correlation_id,
    )


class NarrativeTraceRepository:
    """Versioned trace evidence over the shared exact-version dependency graph."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)

    async def create_trace(
        self,
        *,
        value: NarrativeTraceRecord,
        provenance: Provenance,
        created_at: datetime,
    ) -> NarrativeTraceArtifact:
        self._assert_provenance(value, provenance)
        await self._assert_trace_inputs(value)
        metadata = SemanticRecordMetadata(
            logical_id=value.logical_id,
            version_id=value.trace_version,
            provenance=provenance,
            created_at=created_at,
        )
        stored = await self.versions.create_initial(
            metadata=metadata,
            payload=value.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        materialized = NarrativeTraceArtifact(metadata=stored.metadata, value=value)
        await self._register_trace_dependencies(materialized)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.trace_version,
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )
        return materialized

    async def revise_trace(
        self,
        *,
        value: NarrativeTraceRecord,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> NarrativeTraceArtifact:
        if predecessor.logical_id != value.logical_id:
            raise NarrativeTraceIdentityError(
                "NarrativeTrace revision must preserve trace logical identity"
            )
        pointer = await self.versions.get_current(value.logical_id)
        if (
            pointer is None
            or pointer.version_id != predecessor.version_id
            or pointer.status not in _ACCEPTED_SOURCE_STATES
        ):
            raise NarrativeTraceGateBlocked(
                NarrativeTraceFindingCode.TRACE_STALE_SOURCE,
                "trace revision predecessor must be exact current accepted trace",
            )
        self._assert_provenance(value, provenance)
        await self._assert_trace_inputs(value)
        metadata = SemanticRecordMetadata(
            logical_id=value.logical_id,
            version_id=value.trace_version,
            provenance=provenance,
            created_at=created_at,
            predecessor=predecessor,
        )
        stored = await self.versions.create_successor(
            metadata=metadata,
            payload=value.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        materialized = NarrativeTraceArtifact(metadata=stored.metadata, value=value)
        await self._register_trace_dependencies(materialized)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.trace_version,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )
        return materialized

    async def get_trace(self, ref: VersionRef) -> NarrativeTraceArtifact | None:
        if not ref.logical_id.root.startswith("narrative-trace:"):
            raise NarrativeTraceIdentityError("expected narrative-trace reference")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = NarrativeTraceRecord.model_validate(stored.payload)
        if value.logical_id != ref.logical_id:
            raise NarrativeTraceIdentityError(
                "stored NarrativeTrace payload does not match trace logical identity"
            )
        return NarrativeTraceArtifact(metadata=stored.metadata, value=value)

    async def get_current_trace(
        self,
        *,
        artifact_type: NarrativeArtifactType,
        traced_ref: VersionRef,
    ) -> NarrativeTraceArtifact | None:
        logical_id = narrative_trace_logical_id(artifact_type, traced_ref)
        pointer = await self.versions.get_current(logical_id)
        if pointer is None:
            return None
        return await self.get_trace(
            VersionRef(logical_id=logical_id, version_id=pointer.version_id)
        )

    async def trace_state(self, trace_ref: VersionRef) -> NarrativeTraceState:
        trace = await self.get_trace(trace_ref)
        if trace is None:
            raise NarrativeTraceIdentityError("NarrativeTrace version does not exist")
        pointer = await self.versions.get_current(trace.value.logical_id)
        if pointer is None or pointer.version_id != trace_ref.version_id:
            return NarrativeTraceState.SUPERSEDED
        if pointer.status not in _ACCEPTED_SOURCE_STATES:
            return NarrativeTraceState.INVALIDATED
        unresolved = await self.invalidations.list_unresolved()
        if any(
            record.affected_object_id == trace_ref.logical_id
            and record.affected_object_version == trace_ref.version_id
            for record in unresolved
        ):
            return NarrativeTraceState.INVALIDATED
        for binding in trace.value.source_bindings():
            source_pointer = await self.versions.get_current(binding.source.logical_id)
            if (
                source_pointer is None
                or source_pointer.version_id != binding.source.version_id
                or source_pointer.status not in _ACCEPTED_SOURCE_STATES
            ):
                return NarrativeTraceState.INVALIDATED
        return NarrativeTraceState.CURRENT

    async def trace_ancestors(
        self,
        ref: VersionRef,
        *,
        project_id: LogicalId | None = None,
    ) -> tuple[DependencyReachability, ...]:
        values = await self.graph.ancestors(ref)
        return tuple(
            item
            for item in values
            if _type_for_ref(item.ref, project_id=project_id) is not None
        )

    async def trace_descendants(
        self,
        ref: VersionRef,
        *,
        project_id: LogicalId | None = None,
    ) -> tuple[DependencyReachability, ...]:
        values = await self.graph.descendants(ref)
        return tuple(
            item
            for item in values
            if _type_for_ref(item.ref, project_id=project_id) is not None
        )

    async def why_exists(self, trace_ref: VersionRef) -> NarrativeWhyExists:
        trace = await self.get_trace(trace_ref)
        if trace is None:
            raise NarrativeTraceIdentityError("NarrativeTrace version does not exist")
        ancestors = await self.trace_ancestors(
            trace.value.traced_ref,
            project_id=trace.value.project_id,
        )
        return NarrativeWhyExists(
            trace_ref=trace.ref,
            traced_ref=trace.value.traced_ref,
            root_story_core_ref=trace.value.root_story_core_ref,
            parent_refs=trace.value.parent_refs,
            state=await self.trace_state(trace.ref),
            ancestors=ancestors,
        )

    async def validate_trace(self, value: NarrativeTraceRecord) -> None:
        await self._assert_trace_inputs(value)

    async def _register_trace_dependencies(
        self,
        artifact: NarrativeTraceArtifact,
    ) -> None:
        grouped: dict[tuple[str, str], list[str]] = {}
        refs: dict[tuple[str, str], VersionRef] = {}
        for binding in artifact.value.source_bindings():
            key = _ref_key(binding.source)
            refs[key] = binding.source
            grouped.setdefault(key, []).append(binding.role)
        for key in sorted(grouped):
            await self.graph.create_edge(
                source=refs[key],
                dependent=artifact.ref,
                edge_type="narrative_trace_source",
                dependency_reason=" + ".join(sorted(set(grouped[key]))),
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _assert_trace_inputs(self, value: NarrativeTraceRecord) -> None:
        await self._assert_ref_exists_and_current(
            value.traced_ref,
            missing_code=NarrativeTraceFindingCode.TRACE_STALE_SOURCE,
            label="traced artifact",
        )
        await self._assert_ref_exists_and_current(
            value.root_story_core_ref,
            missing_code=NarrativeTraceFindingCode.TRACE_MISSING_PARENT,
            label="root StoryCore",
        )
        for ref in value.parent_refs:
            await self._assert_ref_exists_and_current(
                ref,
                missing_code=NarrativeTraceFindingCode.TRACE_MISSING_PARENT,
                label="canonical parent",
            )
        for ref in value.source_version_refs:
            await self._assert_ref_exists_and_current(
                ref,
                missing_code=NarrativeTraceFindingCode.TRACE_STALE_SOURCE,
                label="trace source",
            )

        await self._assert_no_cycle(value.traced_ref, value.project_id)

        required_parent_type = _REQUIRED_PARENT[value.artifact_type]
        incoming = await self.graph.list_incoming(value.traced_ref)
        canonical_incoming = [
            edge
            for edge in incoming
            if _type_for_ref(edge.source_ref, project_id=value.project_id) is not None
        ]

        if required_parent_type is None:
            if canonical_incoming:
                raise NarrativeTraceGateBlocked(
                    NarrativeTraceFindingCode.TRACE_CONTRADICTORY_PARENT,
                    "root StoryCore must not have canonical narrative parent edges",
                )
            return

        required_graph_parents = {
            _ref_key(edge.source_ref): edge.source_ref
            for edge in canonical_incoming
            if _type_for_ref(edge.source_ref, project_id=value.project_id)
            is required_parent_type
        }
        declared = {_ref_key(ref): ref for ref in value.parent_refs}

        if not required_graph_parents:
            raise NarrativeTraceGateBlocked(
                NarrativeTraceFindingCode.TRACE_ORPHAN_ARTIFACT,
                "derived canonical artifact has no required parent edge",
            )
        if set(declared) != set(required_graph_parents):
            raise NarrativeTraceGateBlocked(
                NarrativeTraceFindingCode.TRACE_CONTRADICTORY_PARENT,
                "declared canonical parents do not exactly match dependency graph truth",
            )

        ancestors = await self.graph.ancestors(value.traced_ref)
        ancestor_keys = {
            _ref_key(item.ref)
            for item in ancestors
            if _type_for_ref(item.ref, project_id=value.project_id) is not None
        }
        if _ref_key(value.root_story_core_ref) not in ancestor_keys:
            raise NarrativeTraceGateBlocked(
                NarrativeTraceFindingCode.TRACE_ORPHAN_ARTIFACT,
                "derived canonical artifact has no exact path to root StoryCore",
            )

    async def _assert_ref_exists_and_current(
        self,
        ref: VersionRef,
        *,
        missing_code: NarrativeTraceFindingCode,
        label: str,
    ) -> None:
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise NarrativeTraceGateBlocked(
                missing_code,
                f"{label} exact version is absent: {ref.logical_id.root}/{ref.version_id.root}",
            )
        pointer = await self.versions.get_current(ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != ref.version_id
            or pointer.status not in _ACCEPTED_SOURCE_STATES
        ):
            raise NarrativeTraceGateBlocked(
                NarrativeTraceFindingCode.TRACE_STALE_SOURCE,
                f"{label} is not exact current accepted version: "
                f"{ref.logical_id.root}/{ref.version_id.root}",
            )

    async def _assert_no_cycle(
        self,
        origin: VersionRef,
        project_id: LogicalId,
    ) -> None:
        visited: set[tuple[str, str]] = set()
        stack: set[tuple[str, str]] = set()

        async def visit(ref: VersionRef) -> None:
            key = _ref_key(ref)
            if key in stack:
                raise NarrativeTraceGateBlocked(
                    NarrativeTraceFindingCode.TRACE_CYCLE,
                    "canonical narrative ancestry contains a cycle",
                )
            if key in visited:
                return
            stack.add(key)
            for edge in await self.graph.list_incoming(ref):
                if _type_for_ref(edge.source_ref, project_id=project_id) is not None:
                    await visit(edge.source_ref)
            stack.remove(key)
            visited.add(key)

        await visit(origin)

    def _assert_provenance(
        self,
        value: NarrativeTraceRecord,
        provenance: Provenance,
    ) -> None:
        if provenance.source_versions != value.source_bindings():
            raise NarrativeTraceIdentityError(
                "NarrativeTrace provenance must exactly bind declared source versions"
            )
