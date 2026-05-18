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


@dataclass
class PlayerDeathStat:
    player: str
    count: int
    last_death_at: str


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

    _CONN.execute("""
        CREATE TABLE IF NOT EXISTS world_epochs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            seed TEXT,
            notes TEXT
        )
    """)

    _CONN.execute("""
        CREATE TABLE IF NOT EXISTS player_deaths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player TEXT NOT NULL,
            world_epoch_id INTEGER NOT NULL,
            count INTEGER DEFAULT 0,
            last_death_at TEXT,
            UNIQUE(player, world_epoch_id)
        )
    """)

    # Ensure at least one epoch exists (epoch 1 = world from before we started tracking)
    row = _CONN.execute("SELECT COUNT(*) FROM world_epochs").fetchone()
    if row[0] == 0:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _CONN.execute(
            "INSERT INTO world_epochs (started_at, seed, notes) VALUES (?,?,?)",
            (ts, None, "Época inicial")
        )

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


# ── World epochs ──────────────────────────────────────────────────────────────

def create_world_epoch(seed: str | None = None, notes: str | None = None) -> int:
    """Crea una nueva época de mundo y retorna su id."""
    if _CONN is None:
        return 1
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _LOCK:
        cur = _CONN.execute(
            "INSERT INTO world_epochs (started_at, seed, notes) VALUES (?,?,?)",
            (ts, seed, notes)
        )
        _CONN.commit()
        return cur.lastrowid or 1


def get_current_epoch() -> int:
    """Retorna el id de la época más reciente."""
    if _CONN is None:
        return 1
    with _LOCK:
        row = _CONN.execute(
            "SELECT id FROM world_epochs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return row[0] if row else 1


# ── Player deaths ─────────────────────────────────────────────────────────────

def record_death(player: str, epoch_id: int) -> None:
    """Incrementa el contador de muertes del jugador en la época dada."""
    if _CONN is None:
        return
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _LOCK:
        _CONN.execute(
            """
            INSERT INTO player_deaths (player, world_epoch_id, count, last_death_at)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(player, world_epoch_id) DO UPDATE SET
                count = count + 1,
                last_death_at = excluded.last_death_at
            """,
            (player, epoch_id, ts),
        )
        _CONN.commit()


def query_player_deaths(epoch_id: int) -> list[PlayerDeathStat]:
    """Retorna stats de muertes por jugador para la época indicada, ordenado por count desc."""
    if _CONN is None:
        return []
    with _LOCK:
        rows = _CONN.execute(
            """
            SELECT player, count, last_death_at
            FROM player_deaths
            WHERE world_epoch_id = ?
            ORDER BY count DESC
            """,
            (epoch_id,),
        ).fetchall()
    return [PlayerDeathStat(player=r[0], count=r[1], last_death_at=r[2] or "—") for r in rows]


# ── EssentialsX balance (opcional) ───────────────────────────────────────────

def read_essentialsx_balance(uuid: str, data_dir: Path) -> float | None:
    """Lee el saldo de EssentialsX del YAML de userdata si existe."""
    userdata = data_dir / "plugins" / "Essentials" / "userdata" / f"{uuid}.yml"
    if not userdata.exists():
        return None
    try:
        for line in userdata.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("money:"):
                val = stripped.split(":", 1)[1].strip()
                return float(val)
    except Exception:
        pass
    return None
