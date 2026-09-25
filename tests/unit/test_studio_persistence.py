"""IMP-003 tests for the canonical SQLite persistence foundation."""

from __future__ import annotations

import asyncio

import aiosqlite
import pytest

from agent.studio.persistence import (
    CASConflict,
    DEFAULT_MIGRATIONS,
    FOUNDATION_SCHEMA_VERSION,
    Migration,
    NetworkInTransactionError,
    SchemaCompatibilityError,
    SQLiteReadRepository,
    SQLiteWriteOwner,
    WriteOwnerAlreadyRunning,
    WriteQueueFull,
    assert_network_allowed,
    configure_sqlite_connection,
    ensure_schema_compatibility,
    read_sqlite_pragmas,
)


async def _create_probe_schema(owner: SQLiteWriteOwner) -> None:
    async def create(tx):
        await tx.execute(
            """
            CREATE TABLE probe (
                id TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                revision INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        await tx.execute(
            """
            CREATE TABLE parent (
                id TEXT PRIMARY KEY
            )
            """
        )
        await tx.execute(
            """
            CREATE TABLE child (
                id TEXT PRIMARY KEY,
                parent_id TEXT NOT NULL REFERENCES parent(id)
            )
            """
        )

    await owner.execute(create)


@pytest.mark.asyncio
async def test_pragmas_are_wal_full_and_foreign_keys_on(tmp_path):
    db_path = tmp_path / "studio.db"
    owner = SQLiteWriteOwner(db_path)
    await owner.start()
    try:
        async with aiosqlite.connect(str(db_path)) as db:
            await configure_sqlite_connection(db)
            pragmas = await read_sqlite_pragmas(db)

        assert pragmas["journal_mode"] == "wal"
        assert pragmas["synchronous"] == 2
        assert pragmas["foreign_keys"] == 1
    finally:
        await owner.close()


@pytest.mark.asyncio
async def test_second_writer_for_same_database_is_rejected(tmp_path):
    db_path = tmp_path / "studio.db"
    first = SQLiteWriteOwner(db_path)
    second = SQLiteWriteOwner(db_path)
    await first.start()

    try:
        with pytest.raises(WriteOwnerAlreadyRunning):
            await second.start()
    finally:
        await first.close()

    await second.start()
    await second.close()


@pytest.mark.asyncio
async def test_legacy_shared_connection_uses_frozen_pragmas(tmp_path, monkeypatch):
    from agent.db import schema as legacy_schema

    await legacy_schema.close_db()
    monkeypatch.setattr(legacy_schema, "DB_PATH", tmp_path / "legacy.db")
    db = await legacy_schema.get_db()
    try:
        pragmas = await read_sqlite_pragmas(db)
        assert pragmas["journal_mode"] == "wal"
        assert pragmas["synchronous"] == 2
        assert pragmas["foreign_keys"] == 1
    finally:
        await legacy_schema.close_db()


@pytest.mark.asyncio
async def test_canonical_writes_are_serialized(tmp_path):
    db_path = tmp_path / "studio.db"
    owner = SQLiteWriteOwner(db_path)
    await owner.start()
    active = 0
    max_active = 0
    order: list[str] = []

    try:
        await _create_probe_schema(owner)

        async def write(label: str):
            async def operation(tx):
                nonlocal active, max_active
                active += 1
                max_active = max(max_active, active)
                order.append(f"start:{label}")
                await asyncio.sleep(0.01)
                await tx.execute(
                    "INSERT INTO probe (id, value) VALUES (?, ?)",
                    (label, label),
                )
                order.append(f"end:{label}")
                active -= 1
                return label

            return await owner.execute(operation)

        assert await asyncio.gather(write("a"), write("b"), write("c")) == [
            "a",
            "b",
            "c",
        ]
        assert max_active == 1
        assert order == [
            "start:a",
            "end:a",
            "start:b",
            "end:b",
            "start:c",
            "end:c",
        ]
    finally:
        await owner.close()


@pytest.mark.asyncio
async def test_bounded_queue_rejects_pressure_without_restarting_owner(tmp_path):
    db_path = tmp_path / "studio.db"
    owner = SQLiteWriteOwner(db_path, max_queue_size=1)
    await owner.start()
    started = asyncio.Event()
    release = asyncio.Event()

    try:
        async def blocking(_tx):
            started.set()
            await release.wait()
            return "first"

        async def second(_tx):
            return "second"

        first_future = owner.submit(blocking)
        await started.wait()
        second_future = owner.submit(second)

        with pytest.raises(WriteQueueFull):
            owner.submit(second)

        release.set()
        assert await first_future == "first"
        assert await second_future == "second"
    finally:
        release.set()
        await owner.close()


@pytest.mark.asyncio
async def test_cas_update_rejects_stale_revision(tmp_path):
    db_path = tmp_path / "studio.db"
    owner = SQLiteWriteOwner(db_path)
    await owner.start()

    try:
        await _create_probe_schema(owner)

        async def insert(tx):
            await tx.execute(
                "INSERT INTO probe (id, value, revision) VALUES ('item', 'v0', 0)"
            )

        await owner.execute(insert)

        async def update(tx):
            return await tx.cas_update(
                table="probe",
                pk_column="id",
                pk_value="item",
                expected_revision=0,
                changes={"value": "v1"},
            )

        assert await owner.execute(update) == 1

        async def stale(tx):
            return await tx.cas_update(
                table="probe",
                pk_column="id",
                pk_value="item",
                expected_revision=0,
                changes={"value": "stale"},
            )

        with pytest.raises(CASConflict):
            await owner.execute(stale)

        reader = SQLiteReadRepository(db_path)
        row = await reader.fetchone(
            "SELECT value, revision FROM probe WHERE id='item'"
        )
        assert row is not None
        assert dict(row) == {"value": "v1", "revision": 1}
    finally:
        await owner.close()


@pytest.mark.asyncio
async def test_foreign_keys_fail_closed_inside_write_owner(tmp_path):
    db_path = tmp_path / "studio.db"
    owner = SQLiteWriteOwner(db_path)
    await owner.start()

    try:
        await _create_probe_schema(owner)

        async def invalid_child(tx):
            await tx.execute(
                "INSERT INTO child (id, parent_id) VALUES ('c1', 'missing')"
            )

        with pytest.raises(aiosqlite.IntegrityError):
            await owner.execute(invalid_child)

        reader = SQLiteReadRepository(db_path)
        rows = await reader.fetchall("SELECT * FROM child")
        assert rows == []
    finally:
        await owner.close()


@pytest.mark.asyncio
async def test_network_guard_rejects_inside_transaction_and_rolls_back(tmp_path):
    db_path = tmp_path / "studio.db"
    owner = SQLiteWriteOwner(db_path)
    await owner.start()

    try:
        await _create_probe_schema(owner)
        assert_network_allowed()

        async def illegal(tx):
            await tx.execute(
                "INSERT INTO probe (id, value) VALUES ('network', 'before')"
            )
            assert_network_allowed()

        with pytest.raises(NetworkInTransactionError):
            await owner.execute(illegal)

        reader = SQLiteReadRepository(db_path)
        assert await reader.fetchone(
            "SELECT * FROM probe WHERE id='network'"
        ) is None
    finally:
        await owner.close()


@pytest.mark.asyncio
async def test_separate_read_path_is_query_only(tmp_path):
    db_path = tmp_path / "studio.db"
    owner = SQLiteWriteOwner(db_path)
    await owner.start()

    try:
        await _create_probe_schema(owner)

        async def insert(tx):
            await tx.execute(
                "INSERT INTO probe (id, value) VALUES ('readable', 'yes')"
            )

        await owner.execute(insert)
        reader = SQLiteReadRepository(db_path)
        row = await reader.fetchone(
            "SELECT value FROM probe WHERE id='readable'"
        )
        assert row is not None
        assert row["value"] == "yes"

        async with aiosqlite.connect(str(db_path)) as db:
            await configure_sqlite_connection(db, query_only=True)
            pragmas = await read_sqlite_pragmas(db)
            assert pragmas["query_only"] == 1
            with pytest.raises(aiosqlite.OperationalError):
                await db.execute(
                    "INSERT INTO probe (id, value) VALUES ('illegal', 'write')"
                )
    finally:
        await owner.close()


@pytest.mark.asyncio
async def test_migration_table_is_idempotent_and_versioned(tmp_path):
    db_path = tmp_path / "studio.db"

    assert await ensure_schema_compatibility(db_path) == FOUNDATION_SCHEMA_VERSION
    assert await ensure_schema_compatibility(db_path) == FOUNDATION_SCHEMA_VERSION

    async with aiosqlite.connect(str(db_path)) as db:
        rows = await (
            await db.execute(
                "SELECT version, name FROM studio_schema_migration ORDER BY version"
            )
        ).fetchall()

    assert rows == [
        (migration.version, migration.name)
        for migration in DEFAULT_MIGRATIONS
    ]


@pytest.mark.asyncio
async def test_newer_database_schema_is_rejected(tmp_path):
    db_path = tmp_path / "studio.db"
    await ensure_schema_compatibility(db_path)

    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute(
            "INSERT INTO studio_schema_migration (version, name) VALUES (?, 'future')",
            (FOUNDATION_SCHEMA_VERSION + 1,),
        )
        await db.commit()

    with pytest.raises(SchemaCompatibilityError, match="newer than supported"):
        await ensure_schema_compatibility(db_path)


def test_migration_sequence_must_be_contiguous(tmp_path):
    migrations = (
        Migration(1, "one"),
        Migration(3, "three"),
    )

    async def run():
        await ensure_schema_compatibility(
            tmp_path / "bad.db",
            supported_version=3,
            migrations=migrations,
        )

    with pytest.raises(ValueError, match="contiguous"):
        asyncio.run(run())
