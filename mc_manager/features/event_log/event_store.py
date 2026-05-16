from __future__ import annotations

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass


@dataclass
class EventRecord:
    id: int
    timestamp: str
    category: str
    severity: str
    message: str


_LOCK = threading.Lock()
_DB_PATH: Path | None = None
_CONN: sqlite3.Connection | None = None


def init(db_path: Path) -> None:
    global _DB_PATH, _CONN
    _DB_PATH = db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _CONN = sqlite3.connect(str(db_path), check_same_thread=False)
    _CONN.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    _CONN.execute("CREATE INDEX IF NOT EXISTS idx_category ON events(category)")
    _CONN.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)")
    _CONN.commit()


def insert(category: str, severity: str, message: str) -> None:
    if _CONN is None:
        return
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _LOCK:
        _CONN.execute(
            "INSERT INTO events (timestamp, category, severity, message) VALUES (?,?,?,?)",
            (ts, category, severity, message)
        )
        _CONN.commit()


def query_recent(limit: int = 200, category: str | None = None) -> list[EventRecord]:
    if _CONN is None:
        return []
    with _LOCK:
        if category and category != "Todos":
            rows = _CONN.execute(
                "SELECT id,timestamp,category,severity,message FROM events WHERE category=? ORDER BY id DESC LIMIT ?",
                (category, limit)
            ).fetchall()
        else:
            rows = _CONN.execute(
                "SELECT id,timestamp,category,severity,message FROM events ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
    return [EventRecord(*row) for row in rows]


def export_csv(out_path: Path, category: str | None = None) -> None:
    records = query_recent(limit=10000, category=category)
    lines = ["id,timestamp,category,severity,message"]
    for r in records:
        msg = r.message.replace('"', '""')
        lines.append(f'{r.id},"{r.timestamp}","{r.category}","{r.severity}","{msg}"')
    out_path.write_text("\n".join(lines), encoding="utf-8")
