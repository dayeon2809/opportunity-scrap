import json
import sqlite3
from datetime import datetime, timezone

from core.config import SQLITE_PATH


def connection():
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                title TEXT NOT NULL,
                organization TEXT NOT NULL,
                source_url TEXT NOT NULL,
                normalized_json TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                validation_errors TEXT NOT NULL DEFAULT '[]',
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                PRIMARY KEY (source, external_id)
            )
        """)


def save_rows(rows: list[dict], raw_by_key: dict[tuple[str, str], dict], errors_by_key: dict[tuple[str, str], list[str]]) -> int:
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with connection() as conn:
        for row in rows:
            key = (row["source"], row["external_id"])
            conn.execute("""
                INSERT INTO opportunities (source, external_id, title, organization, source_url, normalized_json, raw_json, validation_errors, first_seen_at, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, external_id) DO UPDATE SET
                    title=excluded.title, organization=excluded.organization, source_url=excluded.source_url,
                    normalized_json=excluded.normalized_json, raw_json=excluded.raw_json,
                    validation_errors=excluded.validation_errors, last_seen_at=excluded.last_seen_at
            """, (*key, row["title"], row["organization"], row["source_url"], json.dumps(row, ensure_ascii=False), json.dumps(raw_by_key.get(key, row), ensure_ascii=False), json.dumps(errors_by_key.get(key, []), ensure_ascii=False), now, now))
    return len(rows)

