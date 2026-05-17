from __future__ import annotations

import asyncio
import re

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, Input, RichLog
from textual.containers import Horizontal, Vertical

from mc_manager.core.config import docker, app_config
from mc_manager.core.events import LogLine


_LEVEL_COLORS = {
    "INFO": "white",
    "WARN": "yellow",
    "WARNING": "yellow",
    "ERROR": "red",
    "FATAL": "bold red",
    "DEBUG": "dim",
}


class ConsolePane(Widget):

    DEFAULT_CSS = """
    ConsolePane {
        width: 100%;
        height: 100%;
        layout: vertical;
        padding: 0 1;
    }
    .console-toolbar {
        layout: horizontal;
        height: 3;
        background: $panel-darken-1;
        padding: 0 1;
        align: left middle;
        margin-bottom: 0;
    }
    .console-toolbar Button {
        margin-right: 1;
        height: 3;
    }
    .console-toolbar Label {
        margin-right: 2;
        color: $text-muted;
    }
    #console-log {
        height: 1fr;
        border: solid $primary-darken-3;
        background: $surface-darken-1;
    }
    .console-input-row {
        layout: horizontal;
        height: 3;
        margin-top: 0;
        align: left middle;
    }
    .console-input-row Label {
        width: 4;
        color: $accent;
        text-style: bold;
    }
    .console-input-row Input {
        width: 1fr;
    }
    .console-input-row Button {
        width: 10;
        margin-left: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._auto_scroll = True
        self._filter_text = ""
        self._paused = False

    def compose(self) -> ComposeResult:
        with Horizontal(classes="console-toolbar"):
            yield Label("Consola MC")
            yield Button("Limpiar", id="con-clear", variant="default")
            yield Button("⏸ Pausar", id="con-pause", variant="default")
            yield Button("Auto-scroll: ON", id="con-autoscroll", variant="default")

        yield RichLog(
            id="console-log",
            highlight=True,
            markup=True,
            max_lines=2000,
            wrap=True,
        )

        with Horizontal(classes="console-input-row"):
            yield Label("> ")
            yield Input(placeholder="Escribe un comando (ej: list, say Hola)", id="console-input")
            yield Button("Enviar", id="con-send", variant="primary")

    def on_log_line(self, message: LogLine) -> None:
        if message.source != app_config.minecraft_container:
            return
        if self._paused:
            return
        if self._filter_text and self._filter_text.lower() not in message.text.lower():
            return
        self._write_line(message.text, message.level)

    def _write_line(self, text: str, level: str = "INFO") -> None:
        color = _LEVEL_COLORS.get(level, "white")
        try:
            log = self.query_one("#console-log", RichLog)
            log.write(f"[{color}]{text}[/{color}]")
            if self._auto_scroll:
                log.scroll_end(animate=False)
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "con-clear":
            try:
                self.query_one("#console-log", RichLog).clear()
            except Exception:
                pass
        elif bid == "con-pause":
            self._paused = not self._paused
            event.button.label = "▶ Reanudar" if self._paused else "⏸ Pausar"
        elif bid == "con-autoscroll":
            self._auto_scroll = not self._auto_scroll
            event.button.label = f"Auto-scroll: {'ON' if self._auto_scroll else 'OFF'}"
        elif bid == "con-send":
            await self._send_command()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "console-input":
            await self._send_command()

    async def _send_command(self) -> None:
        try:
            inp = self.query_one("#console-input", Input)
            cmd = inp.value.strip()
            if not cmd:
                return
            inp.value = ""
            self._write_line(f"> {cmd}", "INFO")
            self.run_worker(self._exec(cmd), exclusive=False)
        except Exception:
            pass

    async def _exec(self, command: str) -> None:
        stdout, stderr, rc = await asyncio.to_thread(
            docker.exec_command,
            app_config.minecraft_container,
            f"rcon-cli {command}",
        )
        if stdout:
            self._write_line(stdout, "INFO")
        if stderr and rc != 0:
            self._write_line(f"[Error] {stderr}", "ERROR")
