"""Exact-version DependencyGraph and durable InvalidationRecord repository.

DependencyGraph owns immutable dependency-edge truth. InvalidationRecord only
records the consequences of an accepted source-version change; it never invents
or rewrites graph edges.
"""

from __future__ import annotations

import hashlib
import json
from collections import deque
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable

import aiosqlite
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from .persistence import CASConflict, PersistenceError, SQLiteReadRepository, SQLiteWriteOwner
from .primitives import LogicalId, Provenance, VersionId, VersionRef


class DependencyInvalidationError(PersistenceError):
    """Base error for graph/invalidation persistence."""


class DependencyEdgeConflict(DependencyInvalidationError):
    """Raised when an edge identity collides with different immutable truth."""


class InvalidationNotFound(DependencyInvalidationError):
    """Raised when an invalidation identity does not exist."""


class InvalidationAlreadyResolved(DependencyInvalidationError):
    """Raised when a resolved invalidation is asked to transition again."""


class InvalidationStatus(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    RESOLVED = "RESOLVED"


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _opaque(value: str, label: str) -> str:
    _trimmed(value, label)
    LogicalId(value)
    return value


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class DependencyEdge(BaseModel):
    """Immutable exact-version dependency edge."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    edge_id: str
    source_object_id: LogicalId
    source_version: VersionId
    dependent_object_id: LogicalId
    dependent_version: VersionId
    edge_type: str
    dependency_reason: str
    provenance: Provenance
    created_at: AwareDatetime

    @field_validator("edge_id")
    @classmethod
    def validate_edge_id(cls, value: str) -> str:
        return _opaque(value, "edge_id")

    @field_validator("edge_type", "dependency_reason")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def reject_self_edge(self) -> "DependencyEdge":
        if self.source_ref == self.dependent_ref:
            raise ValueError("dependency edge cannot reference the same exact version")
        return self

    @property
    def source_ref(self) -> VersionRef:
        return VersionRef(
            logical_id=self.source_object_id,
            version_id=self.source_version,
        )

    @property
    def dependent_ref(self) -> VersionRef:
        return VersionRef(
            logical_id=self.dependent_object_id,
            version_id=self.dependent_version,
        )


class DependencyReachability(BaseModel):
    """One deterministic reachable descendant/ancestor path."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    object_id: LogicalId
    version_id: VersionId
    via_edge_id: str
    via_edge_type: str
    dependency_reason: str
    depth: int = Field(ge=1)
    path_edge_ids: tuple[str, ...]

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.object_id, version_id=self.version_id)


class InvalidationRecord(BaseModel):
    """Durable consequence of DependencyGraph/version truth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    invalidation_id: str
    cause: str
    source_object_id: LogicalId
    source_version_old: VersionId
    source_version_new: VersionId
    affected_object_id: LogicalId
    affected_object_version: VersionId
    dependency_edge_id: str
    dependency_edge_type: str
    dependency_reason: str
    scope: str
    status: InvalidationStatus
    revision: int = Field(ge=0)
    created_at: AwareDatetime
    provenance: Provenance
    repair_or_recompute_requirement: str
    resolved_at: AwareDatetime | None = None
    resolution_record_id: str | None = None
    dedupe_key: str

    @field_validator(
        "invalidation_id",
        "dependency_edge_id",
        "dedupe_key",
    )
    @classmethod
    def validate_ids(cls, value: str, info) -> str:
        return _opaque(value, info.field_name)

    @field_validator(
        "cause",
        "dependency_edge_type",
        "dependency_reason",
        "scope",
        "repair_or_recompute_requirement",
    )
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("resolution_record_id")
    @classmethod
    def validate_resolution_id(cls, value: str | None) -> str | None:
        return None if value is None else _opaque(value, "resolution_record_id")

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "InvalidationRecord":
        if self.source_version_old == self.source_version_new:
            raise ValueError("source old/new versions must differ")
        if self.status is InvalidationStatus.UNRESOLVED:
            if self.resolved_at is not None or self.resolution_record_id is not None:
                raise ValueError("unresolved invalidation cannot carry resolution fields")
        else:
            if self.resolved_at is None or self.resolution_record_id is None:
                raise ValueError("resolved invalidation requires resolution evidence")
        return self


class InvalidationTransition(BaseModel):
    """Immutable audit history for invalidation lifecycle mutation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    transition_id: str
    invalidation_id: str
    from_status: InvalidationStatus
    to_status: InvalidationStatus
    from_revision: int = Field(ge=0)
    to_revision: int = Field(ge=1)
    resolution_record_id: str
    provenance: Provenance
    created_at: AwareDatetime


def derive_dependency_edge_id(
    source: VersionRef,
    dependent: VersionRef,
    edge_type: str,
) -> str:
    edge_type = _trimmed(edge_type, "edge_type")
    raw = json.dumps(
        {
            "source_object_id": source.logical_id.root,
            "source_version": source.version_id.root,
            "dependent_object_id": dependent.logical_id.root,
            "dependent_version": dependent.version_id.root,
            "edge_type": edge_type,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "dep:" + hashlib.sha256(raw).hexdigest()


def derive_invalidation_dedupe_key(
    *,
    cause: str,
    source_old: VersionRef,
    source_new: VersionRef,
    affected: VersionRef,
    dependency_edge_id: str,
) -> str:
    cause = _trimmed(cause, "cause")
    dependency_edge_id = _opaque(dependency_edge_id, "dependency_edge_id")
    raw = json.dumps(
        {
            "cause": cause,
            "source_object_id": source_old.logical_id.root,
            "source_version_old": source_old.version_id.root,
            "source_version_new": source_new.version_id.root,
            "affected_object_id": affected.logical_id.root,
            "affected_object_version": affected.version_id.root,
            "dependency_edge_id": dependency_edge_id,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "dedupe:" + hashlib.sha256(raw).hexdigest()


class DependencyGraphRepository:
    """Immutable exact-version DependencyGraph repository."""

    def __init__(self, writer: SQLiteWriteOwner) -> None:
        self.writer = writer
        self.reader = SQLiteReadRepository(writer.db_path)

    async def create_edge(
        self,
        *,
        source: VersionRef,
        dependent: VersionRef,
        edge_type: str,
        dependency_reason: str,
        provenance: Provenance,
        created_at: datetime | None = None,
    ) -> DependencyEdge:
        edge = DependencyEdge(
            edge_id=derive_dependency_edge_id(source, dependent, edge_type),
            source_object_id=source.logical_id,
            source_version=source.version_id,
            dependent_object_id=dependent.logical_id,
            dependent_version=dependent.version_id,
            edge_type=edge_type,
            dependency_reason=dependency_reason,
            provenance=provenance,
            created_at=created_at or _utc_now(),
        )
        return await self.add_edge(edge)

    async def add_edge(self, edge: DependencyEdge) -> DependencyEdge:
        async def command(tx):
            existing = await tx.fetchone(
                "SELECT * FROM studio_dependency_edge WHERE edge_id=?",
                (edge.edge_id,),
            )
            if existing is not None:
                stored = self._edge_from_row(existing)
                if stored != edge:
                    raise DependencyEdgeConflict(
                        f"edge identity already exists with different truth: {edge.edge_id}"
                    )
                return stored

            duplicate = await tx.fetchone(
                """
                SELECT *
                FROM studio_dependency_edge
                WHERE source_object_id=?
                  AND source_version=?
                  AND dependent_object_id=?
                  AND dependent_version=?
                  AND edge_type=?
                """,
                (
                    edge.source_object_id.root,
                    edge.source_version.root,
                    edge.dependent_object_id.root,
                    edge.dependent_version.root,
                    edge.edge_type,
                ),
            )
            if duplicate is not None:
                stored = self._edge_from_row(duplicate)
                if stored != edge:
                    raise DependencyEdgeConflict(
                        "same dependency binding/type exists with different immutable evidence"
                    )
                return stored

            await tx.execute(
                """
                INSERT INTO studio_dependency_edge (
                    edge_id,
                    source_object_id,
                    source_version,
                    dependent_object_id,
                    dependent_version,
                    edge_type,
                    dependency_reason,
                    provenance_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    edge.edge_id,
                    edge.source_object_id.root,
                    edge.source_version.root,
                    edge.dependent_object_id.root,
                    edge.dependent_version.root,
                    edge.edge_type,
                    edge.dependency_reason,
                    edge.provenance.model_dump_json(),
                    edge.created_at.isoformat(),
                ),
            )
            return edge

        try:
            return await self.writer.execute(command)
        except aiosqlite.IntegrityError as exc:
            raise DependencyInvalidationError(
                f"dependency edge references missing exact semantic version: {edge.edge_id}"
            ) from exc

    async def get_edge(self, edge_id: str) -> DependencyEdge | None:
        row = await self.reader.fetchone(
            "SELECT * FROM studio_dependency_edge WHERE edge_id=?",
            (_opaque(edge_id, "edge_id"),),
        )
        return None if row is None else self._edge_from_row(row)

    async def list_outgoing(self, source: VersionRef) -> list[DependencyEdge]:
        rows = await self.reader.fetchall(
            """
            SELECT *
            FROM studio_dependency_edge
            WHERE source_object_id=? AND source_version=?
            ORDER BY edge_id
            """,
            (source.logical_id.root, source.version_id.root),
        )
        return [self._edge_from_row(row) for row in rows]

    async def list_incoming(self, dependent: VersionRef) -> list[DependencyEdge]:
        rows = await self.reader.fetchall(
            """
            SELECT *
            FROM studio_dependency_edge
            WHERE dependent_object_id=? AND dependent_version=?
            ORDER BY edge_id
            """,
            (dependent.logical_id.root, dependent.version_id.root),
        )
        return [self._edge_from_row(row) for row in rows]

    async def descendants(self, source: VersionRef) -> list[DependencyReachability]:
        return await self._reach(source, forward=True)

    async def ancestors(self, dependent: VersionRef) -> list[DependencyReachability]:
        return await self._reach(dependent, forward=False)

    async def _reach(
        self,
        origin: VersionRef,
        *,
        forward: bool,
    ) -> list[DependencyReachability]:
        queue: deque[tuple[VersionRef, int, tuple[str, ...]]] = deque(
            [(origin, 0, ())]
        )
        visited = {(origin.logical_id.root, origin.version_id.root)}
        result: list[DependencyReachability] = []

        while queue:
            current, depth, path = queue.popleft()
            edges = (
                await self.list_outgoing(current)
                if forward
                else await self.list_incoming(current)
            )
            for edge in edges:
                next_ref = edge.dependent_ref if forward else edge.source_ref
                key = (next_ref.logical_id.root, next_ref.version_id.root)
                if key in visited:
                    continue
                visited.add(key)
                next_path = path + (edge.edge_id,)
                result.append(
                    DependencyReachability(
                        object_id=next_ref.logical_id,
                        version_id=next_ref.version_id,
                        via_edge_id=edge.edge_id,
                        via_edge_type=edge.edge_type,
                        dependency_reason=edge.dependency_reason,
                        depth=depth + 1,
                        path_edge_ids=next_path,
                    )
                )
                queue.append((next_ref, depth + 1, next_path))

        return result

    @staticmethod
    def _edge_from_row(row) -> DependencyEdge:
        return DependencyEdge(
            edge_id=row["edge_id"],
            source_object_id=LogicalId(row["source_object_id"]),
            source_version=VersionId(row["source_version"]),
            dependent_object_id=LogicalId(row["dependent_object_id"]),
            dependent_version=VersionId(row["dependent_version"]),
            edge_type=row["edge_type"],
            dependency_reason=row["dependency_reason"],
            provenance=Provenance.model_validate_json(row["provenance_json"]),
            created_at=row["created_at"],
        )


class InvalidationRepository:
    """Durable InvalidationRecord lifecycle over immutable DependencyGraph truth."""

    def __init__(
        self,
        writer: SQLiteWriteOwner,
        graph: DependencyGraphRepository | None = None,
    ) -> None:
        self.writer = writer
        self.reader = SQLiteReadRepository(writer.db_path)
        self.graph = graph or DependencyGraphRepository(writer)

    async def create_for_change(
        self,
        *,
        cause: str,
        source_old: VersionRef,
        source_new: VersionRef,
        provenance: Provenance,
        scope: str,
        repair_or_recompute_requirement: str,
        reachable: Iterable[DependencyReachability] | None = None,
    ) -> list[InvalidationRecord]:
        cause = _trimmed(cause, "cause")
        scope = _trimmed(scope, "scope")
        repair_or_recompute_requirement = _trimmed(
            repair_or_recompute_requirement,
            "repair_or_recompute_requirement",
        )
        if source_old.logical_id != source_new.logical_id:
            raise ValueError("source old/new versions must share logical identity")
        if source_old.version_id == source_new.version_id:
            raise ValueError("source old/new versions must differ")

        # Frozen authority: graph lookup is outside the DB write transaction.
        # A caller may supply a graph-derived selective reachability plan (for
        # example, ActiveProductionProfile changed-path invalidation). The DB
        # write still validates every referenced edge against durable graph truth.
        if reachable is None:
            reachable_items = await self.graph.descendants(source_old)
        else:
            reachable_items = list(reachable)
            await self._validate_reachability_plan(
                source=source_old,
                reachable_items=reachable_items,
            )
        if not reachable_items:
            return []

        created_at = _utc_now()
        planned: list[InvalidationRecord] = []
        for item in reachable_items:
            affected = item.ref
            dedupe_key = derive_invalidation_dedupe_key(
                cause=cause,
                source_old=source_old,
                source_new=source_new,
                affected=affected,
                dependency_edge_id=item.via_edge_id,
            )
            digest = dedupe_key.split(":", 1)[1]
            planned.append(
                InvalidationRecord(
                    invalidation_id="inv:" + digest,
                    cause=cause,
                    source_object_id=source_old.logical_id,
                    source_version_old=source_old.version_id,
                    source_version_new=source_new.version_id,
                    affected_object_id=affected.logical_id,
                    affected_object_version=affected.version_id,
                    dependency_edge_id=item.via_edge_id,
                    dependency_edge_type=item.via_edge_type,
                    dependency_reason=item.dependency_reason,
                    scope=scope,
                    status=InvalidationStatus.UNRESOLVED,
                    revision=0,
                    created_at=created_at,
                    provenance=provenance,
                    repair_or_recompute_requirement=repair_or_recompute_requirement,
                    dedupe_key=dedupe_key,
                )
            )

        async def command(tx):
            materialized: list[InvalidationRecord] = []
            for record in planned:
                edge = await tx.fetchone(
                    """
                    SELECT edge_type, dependency_reason, dependent_object_id, dependent_version
                    FROM studio_dependency_edge
                    WHERE edge_id=?
                    """,
                    (record.dependency_edge_id,),
                )
                if edge is None:
                    raise DependencyInvalidationError(
                        f"dependency edge disappeared before invalidation commit: "
                        f"{record.dependency_edge_id}"
                    )
                if (
                    edge["edge_type"] != record.dependency_edge_type
                    or edge["dependency_reason"] != record.dependency_reason
                    or edge["dependent_object_id"] != record.affected_object_id.root
                    or edge["dependent_version"] != record.affected_object_version.root
                ):
                    raise DependencyInvalidationError(
                        "dependency edge truth does not match planned invalidation"
                    )

                await tx.execute(
                    """
                    INSERT OR IGNORE INTO studio_invalidation_record (
                        invalidation_id,
                        cause,
                        source_object_id,
                        source_version_old,
                        source_version_new,
                        affected_object_id,
                        affected_object_version,
                        dependency_edge_id,
                        dependency_edge_type,
                        dependency_reason,
                        scope,
                        status,
                        revision,
                        created_at,
                        provenance_json,
                        repair_requirement,
                        resolved_at,
                        resolution_record_id,
                        dedupe_key
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
                    """,
                    (
                        record.invalidation_id,
                        record.cause,
                        record.source_object_id.root,
                        record.source_version_old.root,
                        record.source_version_new.root,
                        record.affected_object_id.root,
                        record.affected_object_version.root,
                        record.dependency_edge_id,
                        record.dependency_edge_type,
                        record.dependency_reason,
                        record.scope,
                        record.status.value,
                        record.revision,
                        record.created_at.isoformat(),
                        record.provenance.model_dump_json(),
                        record.repair_or_recompute_requirement,
                        record.dedupe_key,
                    ),
                )
                row = await tx.fetchone(
                    """
                    SELECT *
                    FROM studio_invalidation_record
                    WHERE dedupe_key=?
                    """,
                    (record.dedupe_key,),
                )
                if row is None:
                    raise DependencyInvalidationError(
                        "invalidation insert/dedupe did not materialize a record"
                    )
                materialized.append(self._record_from_row(row))
            return materialized

        try:
            return await self.writer.execute(command)
        except aiosqlite.IntegrityError as exc:
            raise DependencyInvalidationError(
                "invalidation references missing version/edge truth"
            ) from exc

    async def _validate_reachability_plan(
        self,
        *,
        source: VersionRef,
        reachable_items: Iterable[DependencyReachability],
    ) -> None:
        """Fail closed unless a supplied plan is a real durable graph path."""

        for item in reachable_items:
            if item.depth < 1 or item.depth != len(item.path_edge_ids):
                raise DependencyInvalidationError(
                    "selective reachability depth/path evidence is inconsistent"
                )
            current = source
            last_edge = None
            for edge_id in item.path_edge_ids:
                edge = await self.graph.get_edge(edge_id)
                if edge is None:
                    raise DependencyInvalidationError(
                        f"selective reachability references missing edge: {edge_id}"
                    )
                if edge.source_ref != current:
                    raise DependencyInvalidationError(
                        "selective reachability path does not start from/continue "
                        "through the declared source version"
                    )
                current = edge.dependent_ref
                last_edge = edge

            if current != item.ref or last_edge is None:
                raise DependencyInvalidationError(
                    "selective reachability path does not end at affected version"
                )
            if (
                last_edge.edge_id != item.via_edge_id
                or last_edge.edge_type != item.via_edge_type
                or last_edge.dependency_reason != item.dependency_reason
            ):
                raise DependencyInvalidationError(
                    "selective reachability terminal edge evidence does not match"
                )

    async def get(self, invalidation_id: str) -> InvalidationRecord | None:
        row = await self.reader.fetchone(
            "SELECT * FROM studio_invalidation_record WHERE invalidation_id=?",
            (_opaque(invalidation_id, "invalidation_id"),),
        )
        return None if row is None else self._record_from_row(row)

    async def list_unresolved(self) -> list[InvalidationRecord]:
        rows = await self.reader.fetchall(
            """
            SELECT *
            FROM studio_invalidation_record
            WHERE status='UNRESOLVED'
            ORDER BY created_at, invalidation_id
            """
        )
        return [self._record_from_row(row) for row in rows]

    async def resolve(
        self,
        *,
        invalidation_id: str,
        expected_revision: int,
        resolution_record_id: str,
        provenance: Provenance,
    ) -> InvalidationRecord:
        invalidation_id = _opaque(invalidation_id, "invalidation_id")
        resolution_record_id = _opaque(
            resolution_record_id,
            "resolution_record_id",
        )
        resolved_at = _utc_now()

        async def command(tx):
            row = await tx.fetchone(
                "SELECT * FROM studio_invalidation_record WHERE invalidation_id=?",
                (invalidation_id,),
            )
            if row is None:
                raise InvalidationNotFound(invalidation_id)
            current = self._record_from_row(row)
            if current.status is InvalidationStatus.RESOLVED:
                raise InvalidationAlreadyResolved(invalidation_id)

            new_revision = await tx.cas_update(
                table="studio_invalidation_record",
                pk_column="invalidation_id",
                pk_value=invalidation_id,
                expected_revision=expected_revision,
                changes={
                    "status": InvalidationStatus.RESOLVED.value,
                    "resolved_at": _utc_text(resolved_at),
                    "resolution_record_id": resolution_record_id,
                },
            )
            transition_id = f"inv-transition:{invalidation_id}:{new_revision}"
            await tx.execute(
                """
                INSERT INTO studio_invalidation_transition (
                    transition_id,
                    invalidation_id,
                    from_status,
                    to_status,
                    from_revision,
                    to_revision,
                    resolution_record_id,
                    provenance_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transition_id,
                    invalidation_id,
                    current.status.value,
                    InvalidationStatus.RESOLVED.value,
                    current.revision,
                    new_revision,
                    resolution_record_id,
                    provenance.model_dump_json(),
                    _utc_text(resolved_at),
                ),
            )
            updated = await tx.fetchone(
                "SELECT * FROM studio_invalidation_record WHERE invalidation_id=?",
                (invalidation_id,),
            )
            assert updated is not None
            return self._record_from_row(updated)

        return await self.writer.execute(command)

    async def list_resolution_history(
        self,
        invalidation_id: str,
    ) -> list[InvalidationTransition]:
        rows = await self.reader.fetchall(
            """
            SELECT *
            FROM studio_invalidation_transition
            WHERE invalidation_id=?
            ORDER BY to_revision
            """,
            (_opaque(invalidation_id, "invalidation_id"),),
        )
        return [self._transition_from_row(row) for row in rows]

    @staticmethod
    def _record_from_row(row) -> InvalidationRecord:
        return InvalidationRecord(
            invalidation_id=row["invalidation_id"],
            cause=row["cause"],
            source_object_id=LogicalId(row["source_object_id"]),
            source_version_old=VersionId(row["source_version_old"]),
            source_version_new=VersionId(row["source_version_new"]),
            affected_object_id=LogicalId(row["affected_object_id"]),
            affected_object_version=VersionId(row["affected_object_version"]),
            dependency_edge_id=row["dependency_edge_id"],
            dependency_edge_type=row["dependency_edge_type"],
            dependency_reason=row["dependency_reason"],
            scope=row["scope"],
            status=InvalidationStatus(row["status"]),
            revision=int(row["revision"]),
            created_at=row["created_at"],
            provenance=Provenance.model_validate_json(row["provenance_json"]),
            repair_or_recompute_requirement=row["repair_requirement"],
            resolved_at=row["resolved_at"],
            resolution_record_id=row["resolution_record_id"],
            dedupe_key=row["dedupe_key"],
        )

    @staticmethod
    def _transition_from_row(row) -> InvalidationTransition:
        return InvalidationTransition(
            transition_id=row["transition_id"],
            invalidation_id=row["invalidation_id"],
            from_status=InvalidationStatus(row["from_status"]),
            to_status=InvalidationStatus(row["to_status"]),
            from_revision=int(row["from_revision"]),
            to_revision=int(row["to_revision"]),
            resolution_record_id=row["resolution_record_id"],
            provenance=Provenance.model_validate_json(row["provenance_json"]),
            created_at=row["created_at"],
        )
