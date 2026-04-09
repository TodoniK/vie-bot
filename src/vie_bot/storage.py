import sqlite3
import logging
import os
from pathlib import Path

from vie_bot.config import settings

logger = logging.getLogger(__name__)

DB_PATH = Path(settings.data_dir) / "vie_bot.db"


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
        rows = conn.execute("SELECT id FROM seen_offers").fetchall()
        return {row[0] for row in rows}
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


def import_from_txt(txt_path: str) -> int:
    """Importe les IDs depuis un fichier ids.txt legacy vers SQLite."""
    path = Path(txt_path)
    if not path.exists():
        return 0
    with open(path) as f:
        ids = [int(line.strip()) for line in f if line.strip()]
    if not ids:
        return 0
    mark_as_seen(ids)
    logger.info("Imported %d IDs from %s", len(ids), txt_path)
    return len(ids)
