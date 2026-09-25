"""Canonical SQLite persistence foundation for Studio domains.

This module implements the frozen Master persistence rules for new canonical
Studio state. Legacy FlowKit CRUD remains a compatibility surface; new Studio
canonical mutations must enter through :class:`SQLiteWriteOwner`.

The write owner serializes one bounded command queue onto one SQLite write
connection. Reads use a separate query-only connection. Startup migrations run
before the write owner accepts commands.
"""

from __future__ import annotations

import asyncio
import contextvars
import inspect
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Generic, Iterable, Sequence, TypeVar

import aiosqlite


FOUNDATION_SCHEMA_VERSION = 3
_MIGRATION_TABLE = "studio_schema_migration"
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_in_write_transaction: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "studio_sqlite_write_transaction",
    default=False,
)
_active_writer_paths: set[Path] = set()

T = TypeVar("T")
WriteOperation = Callable[["SQLiteWriteTransaction"], Awaitable[T] | T]


class PersistenceError(RuntimeError):
    """Base error for the canonical persistence foundation."""


class SchemaCompatibilityError(PersistenceError):
    """Raised when the database schema is newer/incompatible with this runtime."""


class WriteQueueFull(PersistenceError):
    """Raised when bounded canonical write admission is exhausted."""


class WriteOwnerNotRunning(PersistenceError):
    """Raised when a write is submitted before start or after close."""


class WriteOwnerAlreadyRunning(PersistenceError):
    """Raised when another canonical writer already owns the same DB path."""


class CASConflict(PersistenceError):
    """Raised when optimistic revision compare-and-swap rejects a stale writer."""


class NetworkInTransactionError(PersistenceError):
    """Raised when a network/provider boundary is entered inside a DB transaction."""


@dataclass(frozen=True)
class Migration:
    """One deterministic, ordered schema migration."""

    version: int
    name: str
    statements: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("migration version must be >= 1")
        if not self.name or self.name != self.name.strip():
            raise ValueError("migration name must be non-empty and trimmed")


DEFAULT_MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        name="studio_persistence_foundation",
    ),
    Migration(
        version=2,
        name="studio_version_provenance_repository",
        statements=(
            """
            CREATE TABLE studio_semantic_version (
                logical_id TEXT NOT NULL,
                version_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                provenance_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                predecessor_version_id TEXT,
                PRIMARY KEY (logical_id, version_id),
                FOREIGN KEY (logical_id, predecessor_version_id)
                    REFERENCES studio_semantic_version(logical_id, version_id)
            )
            """,
            """
            CREATE TABLE studio_supersession (
                logical_id TEXT NOT NULL,
                predecessor_version_id TEXT NOT NULL,
                successor_version_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                provenance_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (
                    logical_id,
                    predecessor_version_id,
                    successor_version_id
                ),
                FOREIGN KEY (logical_id, predecessor_version_id)
                    REFERENCES studio_semantic_version(logical_id, version_id),
                FOREIGN KEY (logical_id, successor_version_id)
                    REFERENCES studio_semantic_version(logical_id, version_id)
            )
            """,
            """
            CREATE TABLE studio_current_pointer (
                logical_id TEXT PRIMARY KEY,
                version_id TEXT NOT NULL,
                lifecycle_status TEXT NOT NULL CHECK (
                    lifecycle_status IN (
                        'DRAFT',
                        'REVIEW',
                        'APPROVED',
                        'LOCKED',
                        'SUPERSEDED',
                        'INVALIDATED'
                    )
                ),
                revision INTEGER NOT NULL DEFAULT 0 CHECK (revision >= 0),
                updated_at TEXT NOT NULL,
                FOREIGN KEY (logical_id, version_id)
                    REFERENCES studio_semantic_version(logical_id, version_id)
            )
            """,
            """
            CREATE TRIGGER studio_semantic_version_no_update
            BEFORE UPDATE ON studio_semantic_version
            BEGIN
                SELECT RAISE(ABORT, 'studio semantic versions are immutable');
            END
            """,
            """
            CREATE TRIGGER studio_semantic_version_no_delete
            BEFORE DELETE ON studio_semantic_version
            BEGIN
                SELECT RAISE(ABORT, 'studio semantic versions are immutable');
            END
            """,
        ),
    ),
    Migration(
        version=3,
        name="studio_dependency_invalidation",
        statements=(
            """
            CREATE TABLE studio_dependency_edge (
                edge_id TEXT PRIMARY KEY,
                source_object_id TEXT NOT NULL,
                source_version TEXT NOT NULL,
                dependent_object_id TEXT NOT NULL,
                dependent_version TEXT NOT NULL,
                edge_type TEXT NOT NULL,
                dependency_reason TEXT NOT NULL,
                provenance_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE (
                    source_object_id,
                    source_version,
                    dependent_object_id,
                    dependent_version,
                    edge_type
                ),
                FOREIGN KEY (source_object_id, source_version)
                    REFERENCES studio_semantic_version(logical_id, version_id),
                FOREIGN KEY (dependent_object_id, dependent_version)
                    REFERENCES studio_semantic_version(logical_id, version_id)
            )
            """,
            """
            CREATE INDEX studio_dependency_edge_source_idx
            ON studio_dependency_edge(source_object_id, source_version)
            """,
            """
            CREATE INDEX studio_dependency_edge_dependent_idx
            ON studio_dependency_edge(dependent_object_id, dependent_version)
            """,
            """
            CREATE TRIGGER studio_dependency_edge_no_update
            BEFORE UPDATE ON studio_dependency_edge
            BEGIN
                SELECT RAISE(ABORT, 'studio dependency edges are immutable');
            END
            """,
            """
            CREATE TRIGGER studio_dependency_edge_no_delete
            BEFORE DELETE ON studio_dependency_edge
            BEGIN
                SELECT RAISE(ABORT, 'studio dependency edges are immutable');
            END
            """,
            """
            CREATE TABLE studio_invalidation_record (
                invalidation_id TEXT PRIMARY KEY,
                cause TEXT NOT NULL,
                source_object_id TEXT NOT NULL,
                source_version_old TEXT NOT NULL,
                source_version_new TEXT NOT NULL,
                affected_object_id TEXT NOT NULL,
                affected_object_version TEXT NOT NULL,
                dependency_edge_id TEXT NOT NULL,
                dependency_edge_type TEXT NOT NULL,
                dependency_reason TEXT NOT NULL,
                scope TEXT NOT NULL,
                status TEXT NOT NULL CHECK (
                    status IN ('UNRESOLVED', 'RESOLVED')
                ),
                revision INTEGER NOT NULL DEFAULT 0 CHECK (revision >= 0),
                created_at TEXT NOT NULL,
                provenance_json TEXT NOT NULL,
                repair_requirement TEXT NOT NULL,
                resolved_at TEXT,
                resolution_record_id TEXT,
                dedupe_key TEXT NOT NULL UNIQUE,
                FOREIGN KEY (source_object_id, source_version_old)
                    REFERENCES studio_semantic_version(logical_id, version_id),
                FOREIGN KEY (source_object_id, source_version_new)
                    REFERENCES studio_semantic_version(logical_id, version_id),
                FOREIGN KEY (affected_object_id, affected_object_version)
                    REFERENCES studio_semantic_version(logical_id, version_id),
                FOREIGN KEY (dependency_edge_id)
                    REFERENCES studio_dependency_edge(edge_id),
                CHECK (
                    (
                        status='UNRESOLVED'
                        AND resolved_at IS NULL
                        AND resolution_record_id IS NULL
                    )
                    OR
                    (
                        status='RESOLVED'
                        AND resolved_at IS NOT NULL
                        AND resolution_record_id IS NOT NULL
                    )
                )
            )
            """,
            """
            CREATE INDEX studio_invalidation_unresolved_idx
            ON studio_invalidation_record(status, created_at, invalidation_id)
            """,
            """
            CREATE TRIGGER studio_invalidation_immutable_fields
            BEFORE UPDATE ON studio_invalidation_record
            WHEN
                NEW.invalidation_id IS NOT OLD.invalidation_id
                OR NEW.cause IS NOT OLD.cause
                OR NEW.source_object_id IS NOT OLD.source_object_id
                OR NEW.source_version_old IS NOT OLD.source_version_old
                OR NEW.source_version_new IS NOT OLD.source_version_new
                OR NEW.affected_object_id IS NOT OLD.affected_object_id
                OR NEW.affected_object_version IS NOT OLD.affected_object_version
                OR NEW.dependency_edge_id IS NOT OLD.dependency_edge_id
                OR NEW.dependency_edge_type IS NOT OLD.dependency_edge_type
                OR NEW.dependency_reason IS NOT OLD.dependency_reason
                OR NEW.scope IS NOT OLD.scope
                OR NEW.created_at IS NOT OLD.created_at
                OR NEW.provenance_json IS NOT OLD.provenance_json
                OR NEW.repair_requirement IS NOT OLD.repair_requirement
                OR NEW.dedupe_key IS NOT OLD.dedupe_key
            BEGIN
                SELECT RAISE(ABORT, 'invalidation cause/bindings are immutable');
            END
            """,
            """
            CREATE TRIGGER studio_invalidation_status_transition
            BEFORE UPDATE ON studio_invalidation_record
            WHEN (
                NEW.status IS NOT OLD.status
                OR NEW.revision IS NOT OLD.revision
                OR NEW.resolved_at IS NOT OLD.resolved_at
                OR NEW.resolution_record_id IS NOT OLD.resolution_record_id
            )
            AND NOT (
                OLD.status='UNRESOLVED'
                AND NEW.status='RESOLVED'
                AND NEW.revision=OLD.revision+1
                AND NEW.resolved_at IS NOT NULL
                AND NEW.resolution_record_id IS NOT NULL
            )
            BEGIN
                SELECT RAISE(ABORT, 'illegal invalidation status transition');
            END
            """,
            """
            CREATE TRIGGER studio_invalidation_no_delete
            BEFORE DELETE ON studio_invalidation_record
            BEGIN
                SELECT RAISE(ABORT, 'invalidation history is immutable');
            END
            """,
            """
            CREATE TABLE studio_invalidation_transition (
                transition_id TEXT PRIMARY KEY,
                invalidation_id TEXT NOT NULL,
                from_status TEXT NOT NULL,
                to_status TEXT NOT NULL,
                from_revision INTEGER NOT NULL,
                to_revision INTEGER NOT NULL,
                resolution_record_id TEXT NOT NULL,
                provenance_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE (invalidation_id, to_revision),
                FOREIGN KEY (invalidation_id)
                    REFERENCES studio_invalidation_record(invalidation_id)
            )
            """,
            """
            CREATE TRIGGER studio_invalidation_transition_no_update
            BEFORE UPDATE ON studio_invalidation_transition
            BEGIN
                SELECT RAISE(ABORT, 'invalidation transition history is immutable');
            END
            """,
            """
            CREATE TRIGGER studio_invalidation_transition_no_delete
            BEFORE DELETE ON studio_invalidation_transition
            BEGIN
                SELECT RAISE(ABORT, 'invalidation transition history is immutable');
            END
            """,
        ),
    ),
)


@dataclass
class _QueuedWrite(Generic[T]):
    operation: WriteOperation[T]
    future: asyncio.Future[T]


async def configure_sqlite_connection(
    db: aiosqlite.Connection,
    *,
    query_only: bool = False,
) -> None:
    """Apply the frozen V1 SQLite connection contract."""

    await db.execute("PRAGMA foreign_keys=ON")
    await db.execute("PRAGMA synchronous=FULL")
    if query_only:
        await db.execute("PRAGMA query_only=ON")
    else:
        row = await (await db.execute("PRAGMA journal_mode=WAL")).fetchone()
        if row is None or str(row[0]).lower() != "wal":
            raise PersistenceError("SQLite journal_mode must be WAL")


async def read_sqlite_pragmas(db: aiosqlite.Connection) -> dict[str, Any]:
    """Return the persistence pragmas used as verification evidence."""

    journal = await (await db.execute("PRAGMA journal_mode")).fetchone()
    synchronous = await (await db.execute("PRAGMA synchronous")).fetchone()
    foreign_keys = await (await db.execute("PRAGMA foreign_keys")).fetchone()
    query_only = await (await db.execute("PRAGMA query_only")).fetchone()
    return {
        "journal_mode": str(journal[0]).lower() if journal else None,
        "synchronous": int(synchronous[0]) if synchronous else None,
        "foreign_keys": int(foreign_keys[0]) if foreign_keys else None,
        "query_only": int(query_only[0]) if query_only else None,
    }


def assert_network_allowed() -> None:
    """Fail closed if provider/network work is attempted in a write transaction.

    Network/provider adapters should call this at their entry boundary. The
    context variable propagates through awaited coroutines, so nested provider
    work inside a canonical write command is rejected deterministically.
    """

    if _in_write_transaction.get():
        raise NetworkInTransactionError(
            "provider/network calls are forbidden inside SQLite write transactions"
        )


def _validate_identifier(value: str, label: str) -> str:
    if not _IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"invalid SQL {label}: {value!r}")
    return value


async def ensure_schema_compatibility(
    db_path: str | Path,
    *,
    supported_version: int = FOUNDATION_SCHEMA_VERSION,
    migrations: Sequence[Migration] = DEFAULT_MIGRATIONS,
) -> int:
    """Apply known startup migrations and reject unknown future schemas."""

    path = Path(db_path)
    ordered = tuple(sorted(migrations, key=lambda item: item.version))
    versions = [item.version for item in ordered]
    if len(set(versions)) != len(versions):
        raise ValueError("migration versions must be unique")
    if versions and versions != list(range(1, max(versions) + 1)):
        raise ValueError("migration versions must be contiguous from 1")
    if ordered and ordered[-1].version < supported_version:
        raise ValueError("known migrations do not reach supported schema version")

    async with aiosqlite.connect(str(path)) as db:
        await configure_sqlite_connection(db)
        await db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {_MIGRATION_TABLE} (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL DEFAULT (
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                )
            )
            """
        )
        await db.commit()

        rows = await (
            await db.execute(
                f"SELECT version, name FROM {_MIGRATION_TABLE} ORDER BY version"
            )
        ).fetchall()
        applied = {int(row[0]): str(row[1]) for row in rows}
        latest = max(applied, default=0)
        if latest > supported_version:
            raise SchemaCompatibilityError(
                f"database schema version {latest} is newer than supported "
                f"version {supported_version}"
            )

        known = {item.version: item for item in ordered}
        for version, name in applied.items():
            migration = known.get(version)
            if migration is None or migration.name != name:
                raise SchemaCompatibilityError(
                    f"migration identity mismatch at version {version}: {name!r}"
                )

        for migration in ordered:
            if migration.version > supported_version:
                break
            if migration.version in applied:
                continue
            await db.execute("BEGIN IMMEDIATE")
            try:
                for statement in migration.statements:
                    await db.execute(statement)
                await db.execute(
                    f"INSERT INTO {_MIGRATION_TABLE} (version, name) VALUES (?, ?)",
                    (migration.version, migration.name),
                )
                await db.commit()
            except BaseException:
                await db.rollback()
                raise

        row = await (
            await db.execute(f"SELECT MAX(version) FROM {_MIGRATION_TABLE}")
        ).fetchone()
        final_version = int(row[0] or 0)
        if final_version != supported_version:
            raise SchemaCompatibilityError(
                f"schema version {final_version} does not match required "
                f"version {supported_version}"
            )
        return final_version


class SQLiteWriteTransaction:
    """Restricted DB transaction surface handed to canonical write commands."""

    __slots__ = ("_db",)

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    async def execute(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> aiosqlite.Cursor:
        return await self._db.execute(sql, tuple(parameters))

    async def executemany(
        self,
        sql: str,
        parameters: Iterable[Iterable[Any]],
    ) -> aiosqlite.Cursor:
        return await self._db.executemany(
            sql,
            [tuple(item) for item in parameters],
        )

    async def fetchone(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> aiosqlite.Row | None:
        cursor = await self.execute(sql, parameters)
        return await cursor.fetchone()

    async def fetchall(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> list[aiosqlite.Row]:
        cursor = await self.execute(sql, parameters)
        return list(await cursor.fetchall())

    async def cas_update(
        self,
        *,
        table: str,
        pk_column: str,
        pk_value: Any,
        expected_revision: int,
        changes: dict[str, Any],
        revision_column: str = "revision",
    ) -> int:
        """Update one row only when its mutable revision equals expectation."""

        if expected_revision < 0:
            raise ValueError("expected_revision must be >= 0")
        if not changes:
            raise ValueError("CAS update requires at least one changed field")

        table = _validate_identifier(table, "table")
        pk_column = _validate_identifier(pk_column, "primary-key column")
        revision_column = _validate_identifier(revision_column, "revision column")
        columns = [_validate_identifier(name, "column") for name in changes]
        if revision_column in columns:
            raise ValueError("revision column is owned by CAS and cannot be supplied")

        set_clause = ", ".join(f"{column}=?" for column in columns)
        sql = (
            f"UPDATE {table} SET {set_clause}, "
            f"{revision_column}={revision_column}+1 "
            f"WHERE {pk_column}=? AND {revision_column}=?"
        )
        values = [changes[column] for column in columns]
        values.extend([pk_value, expected_revision])
        cursor = await self._db.execute(sql, values)
        if cursor.rowcount != 1:
            raise CASConflict(
                f"stale revision for {table}.{pk_column}={pk_value!r}; "
                f"expected {expected_revision}"
            )
        return expected_revision + 1


class SQLiteReadRepository:
    """Separate query-only read path for canonical Studio persistence."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    async def fetchone(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> aiosqlite.Row | None:
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            await configure_sqlite_connection(db, query_only=True)
            cursor = await db.execute(sql, tuple(parameters))
            return await cursor.fetchone()

    async def fetchall(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> list[aiosqlite.Row]:
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            await configure_sqlite_connection(db, query_only=True)
            cursor = await db.execute(sql, tuple(parameters))
            return list(await cursor.fetchall())


class SQLiteWriteOwner:
    """One bounded logical writer for canonical Studio SQLite mutation."""

    def __init__(
        self,
        db_path: str | Path,
        *,
        max_queue_size: int = 128,
        supported_schema_version: int = FOUNDATION_SCHEMA_VERSION,
        migrations: Sequence[Migration] = DEFAULT_MIGRATIONS,
    ) -> None:
        if max_queue_size < 1:
            raise ValueError("max_queue_size must be >= 1")
        self.db_path = Path(db_path)
        self.max_queue_size = max_queue_size
        self.supported_schema_version = supported_schema_version
        self.migrations = tuple(migrations)
        self._queue: asyncio.Queue[_QueuedWrite[Any] | None] = asyncio.Queue(
            maxsize=max_queue_size
        )
        self._db: aiosqlite.Connection | None = None
        self._worker_task: asyncio.Task[None] | None = None
        self._closing = False
        self._owns_path = False

    @property
    def running(self) -> bool:
        return self._worker_task is not None and not self._worker_task.done()

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    async def start(self) -> None:
        if self.running:
            return
        if self._closing:
            raise WriteOwnerNotRunning("write owner is closing")

        resolved_path = self.db_path.resolve()
        if resolved_path in _active_writer_paths:
            raise WriteOwnerAlreadyRunning(
                f"canonical SQLite writer already owns {resolved_path}"
            )
        _active_writer_paths.add(resolved_path)
        self._owns_path = True

        try:
            await ensure_schema_compatibility(
                self.db_path,
                supported_version=self.supported_schema_version,
                migrations=self.migrations,
            )
            db = await aiosqlite.connect(str(self.db_path))
            db.row_factory = aiosqlite.Row
            await configure_sqlite_connection(db)
            self._db = db
            self._worker_task = asyncio.create_task(
                self._run(),
                name="studio-sqlite-write-owner",
            )
        except BaseException:
            if self._owns_path:
                _active_writer_paths.discard(resolved_path)
                self._owns_path = False
            raise

    def submit(self, operation: WriteOperation[T]) -> asyncio.Future[T]:
        """Admit one write command without waiting for queue capacity."""

        if not self.running or self._closing:
            raise WriteOwnerNotRunning("write owner is not running")
        loop = asyncio.get_running_loop()
        future: asyncio.Future[T] = loop.create_future()
        command = _QueuedWrite(operation=operation, future=future)
        try:
            self._queue.put_nowait(command)
        except asyncio.QueueFull as exc:
            future.cancel()
            raise WriteQueueFull(
                f"canonical write queue is full (capacity={self.max_queue_size})"
            ) from exc
        return future

    async def execute(self, operation: WriteOperation[T]) -> T:
        return await self.submit(operation)

    async def close(self) -> None:
        if self._worker_task is None:
            return
        self._closing = True
        await self._queue.join()
        await self._queue.put(None)
        await self._worker_task
        self._worker_task = None
        if self._db is not None:
            await self._db.close()
            self._db = None
        if self._owns_path:
            _active_writer_paths.discard(self.db_path.resolve())
            self._owns_path = False
        self._closing = False

    async def _run(self) -> None:
        if self._db is None:
            raise WriteOwnerNotRunning("write connection was not initialized")

        while True:
            command = await self._queue.get()
            try:
                if command is None:
                    return
                await self._db.execute("BEGIN IMMEDIATE")
                token = _in_write_transaction.set(True)
                try:
                    result = command.operation(SQLiteWriteTransaction(self._db))
                    if inspect.isawaitable(result):
                        result = await result
                    await self._db.commit()
                except BaseException as exc:
                    await self._db.rollback()
                    if not command.future.done():
                        command.future.set_exception(exc)
                else:
                    if not command.future.done():
                        command.future.set_result(result)
                finally:
                    _in_write_transaction.reset(token)
            finally:
                self._queue.task_done()
