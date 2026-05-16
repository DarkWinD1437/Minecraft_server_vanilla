from __future__ import annotations

from collections import deque
from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, Input, Select, RichLog
from textual.containers import Horizontal, Vertical

from mc_manager.core.config import app_config
from mc_manager.core.events import LogLine


_LEVEL_COLORS = {
    "INFO": "white",
    "WARN": "yellow",
    "WARNING": "yellow",
    "ERROR": "red",
    "FATAL": "bold red",
    "DEBUG": "dim",
}

_LEVEL_OPTIONS = [
    ("Todos los niveles", "ALL"),
    ("INFO", "INFO"),
    ("WARN", "WARN"),
    ("ERROR", "ERROR"),
]


class LogViewerPane(Widget):

    DEFAULT_CSS = """
    LogViewerPane {
        width: 100%;
        height: 100%;
        layout: vertical;
        padding: 0 1;
    }
    .log-toolbar {
        layout: horizontal;
        height: 3;
        background: $panel-darken-1;
        padding: 0 1;
        align: left middle;
        margin-bottom: 0;
    }
    .log-toolbar Input {
        width: 20;
        margin-right: 1;
    }
    .log-toolbar Select {
        width: 18;
        margin-right: 1;
    }
    .log-toolbar Button {
        margin-right: 1;
        height: 3;
    }
    #log-richlog {
        height: 1fr;
        border: solid $primary-darken-3;
        background: $surface-darken-1;
    }
    .log-status-bar {
        height: 1;
        background: $panel-darken-1;
        padding: 0 1;
        layout: horizontal;
        align: left middle;
    }
    .log-status-bar Label {
        margin-right: 3;
        color: $text-muted;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._buffer: deque[tuple[str, str, str]] = deque(maxlen=app_config.log_buffer_size)
        self._filter_text = ""
        self._filter_level = "ALL"
        self._live = True
        self._line_count = 0
        self._match_count = 0

    def compose(self) -> ComposeResult:
        with Horizontal(classes="log-toolbar"):
            yield Input(placeholder="🔍 Buscar...", id="log-search")
            yield Select(
                options=_LEVEL_OPTIONS,
                value="ALL",
                id="log-level-filter",
                allow_blank=False,
            )
            yield Button("⏸ Pausar", id="log-pause", variant="default")
            yield Button("Limpiar", id="log-clear", variant="default")
            yield Button("📤 Exportar", id="log-export", variant="default")

        yield RichLog(
            id="log-richlog",
            highlight=True,
            markup=True,
            max_lines=5000,
            wrap=True,
        )

        with Horizontal(classes="log-status-bar"):
            yield Label("Líneas: 0", id="log-stat-lines")
            yield Label("Coincidencias: 0", id="log-stat-matches")
            yield Label("● LIVE", id="log-stat-live")

    def on_log_line(self, message: LogLine) -> None:
        self._buffer.append((message.source, message.text, message.level))
        self._line_count += 1

        if not self._live:
            return

        if self._matches_filter(message.text, message.level):
            self._match_count += 1
            self._append_to_view(message.source, message.text, message.level)
            self._update_status()

    def _matches_filter(self, text: str, level: str) -> bool:
        if self._filter_level != "ALL" and level not in (self._filter_level, "WARN" if self._filter_level == "WARNING" else self._filter_level):
            return False
        if self._filter_text and self._filter_text.lower() not in text.lower():
            return False
        return True

    def _append_to_view(self, source: str, text: str, level: str) -> None:
        color = _LEVEL_COLORS.get(level, "white")
        prefix = f"[dim]{source}[/dim] " if source != app_config.minecraft_container else ""
        try:
            log = self.query_one("#log-richlog", RichLog)
            log.write(f"{prefix}[{color}]{text}[/{color}]")
        except Exception:
            pass

    def _rerender_buffer(self) -> None:
        try:
            log = self.query_one("#log-richlog", RichLog)
            log.clear()
        except Exception:
            return
        self._match_count = 0
        for source, text, level in self._buffer:
            if self._matches_filter(text, level):
                self._match_count += 1
                self._append_to_view(source, text, level)
        self._update_status()

    def _update_status(self) -> None:
        try:
            self.query_one("#log-stat-lines", Label).update(f"Líneas: {self._line_count}")
            self.query_one("#log-stat-matches", Label).update(f"Coincidencias: {self._match_count}")
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "log-pause":
            self._live = not self._live
            event.button.label = "▶ Reanudar" if not self._live else "⏸ Pausar"
            try:
                self.query_one("#log-stat-live", Label).update(
                    "● LIVE" if self._live else "⏸ PAUSADO"
                )
            except Exception:
                pass
        elif bid == "log-clear":
            try:
                self.query_one("#log-richlog", RichLog).clear()
            except Exception:
                pass
            self._buffer.clear()
            self._line_count = 0
            self._match_count = 0
            self._update_status()
        elif bid == "log-export":
            self._export_logs()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "log-search":
            self._filter_text = event.value
            self._rerender_buffer()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "log-level-filter":
            self._filter_level = str(event.value)
            self._rerender_buffer()

    def _export_logs(self) -> None:
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = app_config.logs_dir / f"export_{ts}.txt"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                f"[{src}] [{lvl}] {txt}"
                for src, txt, lvl in self._buffer
                if self._matches_filter(txt, lvl)
            ]
            out_path.write_text("\n".join(lines), encoding="utf-8")
            self.app.notify(f"Exportado: {out_path.name}", severity="information")
        except Exception as e:
            self.app.notify(f"Error al exportar: {e}", severity="error")
