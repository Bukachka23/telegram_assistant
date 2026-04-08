import logging
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from bot.infrastructure.storage.schemas import MEMORY_SCHEMA

logger = logging.getLogger(__name__)


class MemoryStore:
    """SQLite-backed long-term memory with full-text search."""

    def __init__(self, db_path: str, *, db: aiosqlite.Connection | None = None) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = db
        self._owns_connection: bool = db is None

    def _get_db(self) -> aiosqlite.Connection:
        """Return the active connection. Raises if init() was not called."""
        if self._db is None:
            msg = "MemoryStore not initialized — call init() first"
            raise RuntimeError(msg)
        return self._db

    async def init(self) -> None:
        """Open (or reuse) a database connection and ensure the schema exists."""
        if self._owns_connection:
            db_path = Path(self._db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._db = await aiosqlite.connect(db_path)
            self._db.row_factory = aiosqlite.Row
        db = self._get_db()
        await db.executescript(MEMORY_SCHEMA)
        await db.commit()
        count = await self.count()
        logger.info("Memory store ready: %d memories in %s", count, self._db_path)

    async def close(self) -> None:
        """Close the connection only when this store owns it."""
        if self._owns_connection and self._db:
            await self._db.close()

    async def save(self, fact: str, *, category: str = "") -> int:
        """Save a fact. Returns the row id."""
        now = datetime.now(UTC).isoformat()
        db = self._get_db()
        async with db.execute(
            "INSERT INTO memories (fact, category, created_at) VALUES (?, ?, ?)",
            (fact, category, now),
        ) as cursor:
            row_id = cursor.lastrowid
        await db.commit()
        if row_id is None:
            msg = "INSERT did not return a row id"
            raise RuntimeError(msg)
        logger.info("Memory saved [%d]: %s", row_id, fact[:80])
        return row_id

    async def recall(self, query: str, *, limit: int = 5) -> list[dict]:
        """Full-text search for memories matching query. Newest first."""
        async with self._get_db().execute(
            """
            SELECT m.id, m.fact, m.category, m.created_at
            FROM memories_fts fts
            JOIN memories m ON m.id = fts.rowid
            WHERE memories_fts MATCH ?
            ORDER BY m.id DESC
            LIMIT ?
            """,
            (query, limit),
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def list_recent(self, *, limit: int = 10) -> list[dict]:
        """Return the most recent memories."""
        async with self._get_db().execute(
            "SELECT id, fact, category, created_at FROM memories ORDER BY id DESC LIMIT ?",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def count(self) -> int:
        """Return total number of stored memories."""
        async with self._get_db().execute("SELECT COUNT(*) FROM memories") as cursor:
            row = await cursor.fetchone()
        return row[0] if row else 0
