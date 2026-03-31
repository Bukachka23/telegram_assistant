import logging
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from bot.shared.constants import SCHEMA

logger = logging.getLogger(__name__)


class MemoryStore:
    """SQLite-backed long-term memory with full-text search."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def init(self) -> None:
        """Open database and create schema."""
        db_path = Path(self._db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._db = await aiosqlite.connect(db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA)
        await self._db.commit()
        count = await self._count()
        logger.info("Memory store ready: %d memories in %s", count, self._db_path)

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()

    async def save(self, fact: str, *, category: str = "") -> int:
        """Save a fact. Returns the row id."""
        now = datetime.now(UTC).isoformat()
        async with self._db.execute(
            "INSERT INTO memories (fact, category, created_at) VALUES (?, ?, ?)",
            (fact, category, now),
        ) as cursor:
            row_id = cursor.lastrowid
        await self._db.commit()
        logger.info("Memory saved [%d]: %s", row_id, fact[:80])
        return row_id

    async def recall(self, query: str, *, limit: int = 5) -> list[dict]:
        """Full-text search for memories matching query. Newest first."""
        async with self._db.execute(
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
        async with self._db.execute(
            "SELECT id, fact, category, created_at FROM memories ORDER BY id DESC LIMIT ?",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def _count(self) -> int:
        async with self._db.execute("SELECT COUNT(*) FROM memories") as cursor:
            row = await cursor.fetchone()
        return row[0] if row else 0
