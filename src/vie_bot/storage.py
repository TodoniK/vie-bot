import logging
import os
import sqlite3
import time
from pathlib import Path

from vie_bot.config import settings

logger = logging.getLogger(__name__)

DB_PATH = Path(settings.data_dir) / "vie_bot.db"
HEARTBEAT_PATH = Path(settings.data_dir) / "heartbeat"


def _get_connection() -> sqlite3.Connection:
    os.makedirs(settings.data_dir, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_offers (
            id INTEGER PRIMARY KEY,
            seen_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    return conn


def get_seen_ids() -> set[int]:
    """Retourne l'ensemble des IDs déjà vus."""
    conn = _get_connection()
    try:
        return {row[0] for row in conn.execute("SELECT id FROM seen_offers")}
    finally:
        conn.close()


def count_seen() -> int:
    conn = _get_connection()
    try:
        return conn.execute("SELECT count(*) FROM seen_offers").fetchone()[0]
    finally:
        conn.close()


def mark_as_seen(offer_ids: list[int]) -> None:
    """Marque des IDs comme vus (insert or ignore)."""
    if not offer_ids:
        return
    conn = _get_connection()
    try:
        conn.executemany(
            "INSERT OR IGNORE INTO seen_offers (id) VALUES (?)",
            [(oid,) for oid in offer_ids],
        )
        conn.commit()
        logger.info("Saved %d offer ID(s)", len(offer_ids))
    finally:
        conn.close()


def touch_heartbeat() -> None:
    """Horodate le dernier cycle réussi (lu par le HEALTHCHECK Docker)."""
    HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    HEARTBEAT_PATH.write_text(str(int(time.time())))


def heartbeat_age() -> float | None:
    try:
        return time.time() - int(HEARTBEAT_PATH.read_text())
    except (FileNotFoundError, ValueError):
        return None
