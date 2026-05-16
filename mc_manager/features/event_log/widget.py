from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, Select, DataTable
from textual.containers import Horizontal, Vertical

from mc_manager.core.config import app_config
from mc_manager.core.events import LogLine
from mc_manager.features.event_log import event_store


_JOIN_RE = re.compile(r"(\w+) joined the game")
_LEAVE_RE = re.compile(r"(\w+) left the game")
_DEATH_RE = re.compile(r"(\w+) (was|fell|drowned|burned|suffocated|starved)", re.IGNORECASE)
_CRASH_RE = re.compile(r"(exception|crash|fatal error|stopping server)", re.IGNORECASE)


_CATEGORIES = [
    ("Todos", "Todos"),
    ("Servidor", "Servidor"),
    ("Jugadores", "Jugadores"),
    ("Backups", "Backups"),
    ("Comandos", "Comandos"),
    ("Sistema", "Sistema"),
    ("Errores", "Errores"),
]

_SEV_COLORS = {
    "info": "white",
    "warning": "yellow",
    "error": "red",
    "critical": "bold red",
}


class EventLogPane(Widget):

    DEFAULT_CSS = """
    EventLogPane {
        width: 100%;
        height: 100%;
        layout: vertical;
        padding: 0 1;
    }
    .evlog-toolbar {
        layout: horizontal;
        height: 3;
        background: $panel-darken-1;
        padding: 0 1;
        align: left middle;
        margin-bottom: 1;
    }
    .evlog-toolbar Select {
        width: 14;
        margin-right: 1;
    }
    .evlog-toolbar Button {
        margin-right: 1;
    }
    DataTable {
        height: 1fr;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_category = "Todos"

    def compose(self) -> ComposeResult:
        with Horizontal(classes="evlog-toolbar"):
            yield Label("📋  Historial de Eventos")
            yield Select(options=_CATEGORIES, value="Todos", id="evlog-cat-filter", allow_blank=False)
            yield Button("🔄 Actualizar", id="evlog-refresh", variant="primary")
            yield Button("📤 Exportar CSV", id="evlog-export", variant="default")
            yield Button("🗑 Limpiar vista", id="evlog-clear-view", variant="default")

        yield DataTable(id="evlog-table")

    def on_mount(self) -> None:
        event_store.init(app_config.logs_dir / "events.db")
        event_store.insert("Sistema", "info", "MC Manager iniciado")
        self._setup_table()
        self.run_worker(self._load_events(), exclusive=False)
        self.set_interval(10.0, lambda: self.run_worker(self._load_events()))

    def _setup_table(self) -> None:
        try:
            tbl = self.query_one("#evlog-table", DataTable)
            tbl.add_columns("Fecha/Hora", "Categoría", "Severidad", "Mensaje")
        except Exception:
            pass

    async def _load_events(self) -> None:
        records = event_store.query_recent(
            limit=200,
            category=self._current_category if self._current_category != "Todos" else None
        )
        try:
            tbl = self.query_one("#evlog-table", DataTable)
            tbl.clear()
            if not records:
                tbl.add_row("—", "—", "—", "Sin eventos registrados")
            for rec in records:
                color = _SEV_COLORS.get(rec.severity.lower(), "white")
                tbl.add_row(
                    rec.timestamp,
                    rec.category,
                    rec.severity.upper(),
                    rec.message,
                )
        except Exception:
            pass

    def on_log_line(self, message: LogLine) -> None:
        # Parse log lines for interesting events
        text = message.text
        if _JOIN_RE.search(text):
            m = _JOIN_RE.search(text)
            event_store.insert("Jugadores", "info", f"{m.group(1)} se conectó")
        elif _LEAVE_RE.search(text):
            m = _LEAVE_RE.search(text)
            event_store.insert("Jugadores", "info", f"{m.group(1)} se desconectó")
        elif _DEATH_RE.search(text) and message.level != "DEBUG":
            event_store.insert("Jugadores", "info", text[:120])
        elif _CRASH_RE.search(text) and message.level in ("ERROR", "FATAL"):
            event_store.insert("Errores", "critical", text[:120])
        elif message.level in ("ERROR", "FATAL"):
            event_store.insert("Errores", "error", text[:120])

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "evlog-refresh":
            await self._load_events()
        elif bid == "evlog-export":
            self._export()
        elif bid == "evlog-clear-view":
            try:
                self.query_one("#evlog-table", DataTable).clear()
            except Exception:
                pass

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "evlog-cat-filter":
            self._current_category = str(event.value)
            self.run_worker(self._load_events(), exclusive=False)

    def _export(self) -> None:
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = app_config.logs_dir / f"events_{ts}.csv"
            out.parent.mkdir(parents=True, exist_ok=True)
            event_store.export_csv(out, self._current_category if self._current_category != "Todos" else None)
            self.app.notify(f"Exportado: {out.name}", severity="information")
        except Exception as e:
            self.app.notify(str(e), severity="error")
