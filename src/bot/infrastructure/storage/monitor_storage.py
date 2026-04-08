import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from bot.domain.models import PersistedMonitor
from bot.infrastructure.storage.schemas import MONITOR_SCHEMA

logger = logging.getLogger(__name__)


class MonitorStore:
    """SQLite-backed storage for persisted Telegram channel monitors."""

    def __init__(self, db_path: str, *, db: aiosqlite.Connection | None = None) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = db
        self._owns_connection: bool = db is None

    def _get_db(self) -> aiosqlite.Connection:
        """Return the active connection. Raises if init() was not called."""
        if self._db is None:
            msg = "MonitorStore not initialized — call init() first"
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
        await db.executescript(MONITOR_SCHEMA)
        await db.commit()
        logger.info("Monitor store ready: %s", self._db_path)

    async def close(self) -> None:
        """Close the connection only when this store owns it."""
        if self._owns_connection and self._db:
            await self._db.close()

    async def upsert_monitor(
        self,
        *,
        owner_user_id: int,
        chat_id: int,
        username: str,
        title: str,
        keywords: list[str],
        source_type: str,
    ) -> PersistedMonitor:
        """Create or update a persisted channel monitor."""
        created_at = datetime.now(UTC).isoformat()
        db = self._get_db()
        async with db.execute(
            """
            INSERT INTO channel_monitors (
                owner_user_id,
                chat_id,
                username,
                title,
                keywords_json,
                source_type,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                owner_user_id = excluded.owner_user_id,
                username = excluded.username,
                title = excluded.title,
                keywords_json = excluded.keywords_json,
                source_type = excluded.source_type
            """,
            (
                owner_user_id,
                chat_id,
                username,
                title,
                json.dumps(keywords),
                source_type,
                created_at,
            ),
        ):
            pass
        await db.commit()
        monitor = await self.get_monitor_by_chat_id(chat_id)
        if monitor is None:
            msg = f"monitor for chat_id={chat_id} was not persisted"
            raise RuntimeError(msg)
        return monitor

    async def list_monitors(self, owner_user_id: int) -> list[PersistedMonitor]:
        """Return all persisted monitors for one owner."""
        async with self._get_db().execute(
            """
            SELECT owner_user_id, chat_id, username, title, keywords_json,
                   source_type, created_at
            FROM channel_monitors
            WHERE owner_user_id = ?
            ORDER BY title, chat_id
            """,
            (owner_user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [self._row_to_monitor(row) for row in rows]

    async def get_monitor_by_chat_id(self, chat_id: int) -> PersistedMonitor | None:
        """Return a persisted monitor by chat ID."""
        async with self._get_db().execute(
            """
            SELECT owner_user_id, chat_id, username, title, keywords_json,
                   source_type, created_at
            FROM channel_monitors
            WHERE chat_id = ?
            """,
            (chat_id,),
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_monitor(row)

    async def remove_monitor(self, owner_user_id: int, identifier: str) -> bool:
        """Remove a monitor by username or chat ID string for one owner."""
        normalized_identifier = identifier.strip()
        numeric_identifier = self._parse_chat_id(normalized_identifier)

        db = self._get_db()
        if numeric_identifier is not None:
            async with db.execute(
                "DELETE FROM channel_monitors WHERE owner_user_id = ? AND chat_id = ?",
                (owner_user_id, numeric_identifier),
            ) as cursor:
                await db.commit()
                return cursor.rowcount > 0

        normalized_username = normalized_identifier.lstrip("@").lower()
        async with db.execute(
            """
            DELETE FROM channel_monitors
            WHERE owner_user_id = ?
              AND LOWER(LTRIM(username, '@')) = ?
            """,
            (owner_user_id, normalized_username),
        ) as cursor:
            await db.commit()
            return cursor.rowcount > 0

    @staticmethod
    def _parse_chat_id(identifier: str) -> int | None:
        try:
            return int(identifier)
        except ValueError:
            return None

    @staticmethod
    def _row_to_monitor(row: aiosqlite.Row) -> PersistedMonitor:
        return PersistedMonitor(
            owner_user_id=row["owner_user_id"],
            chat_id=row["chat_id"],
            username=row["username"],
            title=row["title"],
            keywords=json.loads(row["keywords_json"]),
            source_type=row["source_type"],
            created_at=row["created_at"],
        )
