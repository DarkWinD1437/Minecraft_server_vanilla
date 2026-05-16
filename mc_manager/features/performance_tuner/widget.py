from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, Input, Select, Static
from textual.containers import Horizontal, Vertical

from mc_manager.core.config import app_config


def _to_safe_id(text: str) -> str:
    """Strip accents so the result is valid as a Textual widget ID."""
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


_PRESETS = {
    "Balanceado (5GB)": {
        "MEMORY": "5G",
        "JVM_XX_OPTS": "-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:G1HeapRegionSize=8M"
    },
    "GC Agresivo (5GB)": {
        "MEMORY": "5G",
        "JVM_XX_OPTS": "-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=16M -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40"
    },
    "Mínimo (2GB)": {
        "MEMORY": "2G",
        "JVM_XX_OPTS": "-XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:G1HeapRegionSize=4M"
    },
    "Grande (8GB)": {
        "MEMORY": "8G",
        "JVM_XX_OPTS": "-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:G1HeapRegionSize=16M -XX:G1NewSizePercent=25 -XX:G1MaxNewSizePercent=45"
    },
}


def _read_compose(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _update_env_var(content: str, key: str, value: str) -> str:
    """Replace an env var value in docker-compose.yml content."""
    pattern = re.compile(rf"(\s+{re.escape(key)}:\s*)\S+")
    replacement = rf"\g<1>{value}"
    new_content = pattern.sub(replacement, content)
    if new_content == content:
        # key not found, try quoted form
        pattern2 = re.compile(rf'(\s+{re.escape(key)}:\s*)["\'].*?["\']')
        new_content = pattern2.sub(rf'\g<1>"{value}"', content)
    return new_content


class PerformanceTunerPane(Widget):

    DEFAULT_CSS = """
    PerformanceTunerPane {
        width: 100%;
        height: 100%;
        padding: 1 2;
        layout: vertical;
        overflow-y: auto;
    }
    .perf-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .perf-card {
        border: solid $primary-darken-2;
        background: $panel;
        padding: 1;
        margin-bottom: 1;
    }
    .perf-field-row {
        layout: horizontal;
        height: 3;
        align: left middle;
        margin-bottom: 1;
    }
    .perf-field-row Label {
        width: 22;
        color: $text-muted;
    }
    .perf-field-row Input {
        width: 1fr;
    }
    .perf-btn-row {
        layout: horizontal;
        height: 3;
        margin-top: 1;
        align: left middle;
    }
    .perf-btn-row Button {
        margin-right: 1;
    }
    .perf-preset-row {
        layout: horizontal;
        height: 3;
        margin-bottom: 1;
        align: left middle;
    }
    .perf-preset-row Button {
        margin-right: 1;
    }
    #perf-diff-preview {
        height: 6;
        background: $surface-darken-1;
        border: solid $primary-darken-3;
        padding: 0 1;
        margin-top: 1;
        overflow-y: auto;
    }
    .perf-warn {
        background: $warning-darken-2;
        color: $text;
        padding: 0 1;
        margin-bottom: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._compose_content = ""

    def compose(self) -> ComposeResult:
        yield Label("🚀  Rendimiento JVM — Editor de Flags", classes="perf-title")
        yield Label(
            "⚠ Estos cambios modifican docker-compose.yml. El servidor debe reiniciarse para aplicarlos.",
            classes="perf-warn"
        )

        with Vertical(classes="perf-card"):
            yield Label("Presets de configuración:", classes="perf-title")
            with Horizontal(classes="perf-preset-row"):
                for name in _PRESETS:
                    yield Button(name, id=f"preset-{_to_safe_id(name.split()[0].lower())}", variant="default")

        with Vertical(classes="perf-card"):
            yield Label("Configuración Manual:", classes="perf-title")

            with Horizontal(classes="perf-field-row"):
                yield Label("Memoria Heap (ej: 5G, 512M):")
                yield Input(placeholder="5G", id="perf-memory")

            with Horizontal(classes="perf-field-row"):
                yield Label("Flags GC adicionales:")
                yield Input(placeholder="-XX:+UseG1GC ...", id="perf-jvm-flags")

            with Horizontal(classes="perf-btn-row"):
                yield Button("🔍 Leer docker-compose.yml", id="perf-read", variant="default")
                yield Button("💾 Guardar cambios", id="perf-save", variant="primary")

            yield Label("Vista previa de cambios:", classes="perf-title")
            yield Static("Usa '🔍 Leer' para cargar la configuración actual.", id="perf-diff-preview")

    def on_mount(self) -> None:
        self.run_worker(self._load_compose(), exclusive=False)

    async def _load_compose(self) -> None:
        compose_path = app_config.compose_dir / "docker-compose.yml"
        self._compose_content = _read_compose(compose_path)

        # Extract current values
        mem_match = re.search(r"MEMORY:\s*(\S+)", self._compose_content)
        jvm_match = re.search(r"JVM_XX_OPTS:\s*[\"']?(.+?)[\"']?\s*$", self._compose_content, re.MULTILINE)

        try:
            if mem_match:
                self.query_one("#perf-memory", Input).value = mem_match.group(1)
            if jvm_match:
                self.query_one("#perf-jvm-flags", Input).value = jvm_match.group(1).strip('"').strip("'")
        except Exception:
            pass

        self._update_preview()

    def _update_preview(self) -> None:
        try:
            mem = self.query_one("#perf-memory", Input).value
            flags = self.query_one("#perf-jvm-flags", Input).value
            preview = f"MEMORY: {mem}\nJVM_XX_OPTS: {flags}"
            self.query_one("#perf-diff-preview", Static).update(preview)
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "perf-read":
            await self._load_compose()
        elif bid == "perf-save":
            await self._save_compose()
        elif bid and bid.startswith("preset-"):
            # Find matching preset
            prefix = bid[7:]  # e.g. "balanceado"
            for name, values in _PRESETS.items():
                if _to_safe_id(name.lower()).startswith(prefix):
                    try:
                        self.query_one("#perf-memory", Input).value = values["MEMORY"]
                        self.query_one("#perf-jvm-flags", Input).value = values["JVM_XX_OPTS"]
                    except Exception:
                        pass
                    self._update_preview()
                    self.app.notify(f"Preset '{name}' aplicado (aún no guardado)", severity="information")
                    break

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id in ("perf-memory", "perf-jvm-flags"):
            self._update_preview()

    async def _save_compose(self) -> None:
        try:
            compose_path = app_config.compose_dir / "docker-compose.yml"
            mem = self.query_one("#perf-memory", Input).value.strip()
            flags = self.query_one("#perf-jvm-flags", Input).value.strip()

            content = self._compose_content
            if mem:
                content = _update_env_var(content, "MEMORY", mem)
            if flags:
                content = _update_env_var(content, "JVM_XX_OPTS", flags)

            compose_path.write_text(content, encoding="utf-8")
            self._compose_content = content
            self.app.notify(
                "docker-compose.yml actualizado. Reinicia el servidor para aplicar.",
                severity="warning"
            )
        except Exception as e:
            self.app.notify(f"Error: {e}", severity="error")
