from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, Input, Select, Switch, TextArea, Static
from textual.containers import Horizontal, Vertical, ScrollableContainer

from mc_manager.core.config import app_config


_SERVER_TYPES = [
    ("PAPER", "PAPER"),
    ("VANILLA", "VANILLA"),
    ("SPIGOT", "SPIGOT"),
    ("FABRIC", "FABRIC"),
    ("FORGE", "FORGE"),
    ("PURPUR", "PURPUR"),
]

_VERSIONS = [
    ("1.21.4", "1.21.4"),
    ("1.21.1", "1.21.1"),
    ("1.20.6", "1.20.6"),
    ("1.20.4", "1.20.4"),
    ("1.20.1", "1.20.1"),
    ("1.19.4", "1.19.4"),
    ("LATEST", "LATEST"),
]

_RESTART_POLICIES = [
    ("Siempre (always)", "always"),
    ("A menos que parado (unless-stopped)", "unless-stopped"),
    ("En caso de fallo (on-failure)", "on-failure"),
    ("Nunca (no)", "no"),
]


class ComposeEditorPane(Widget):

    DEFAULT_CSS = """
    ComposeEditorPane {
        width: 100%;
        height: 100%;
        layout: vertical;
        padding: 0 1;
    }
    .compose-toolbar {
        layout: horizontal;
        height: 3;
        background: $panel-darken-1;
        padding: 0 1;
        align: left middle;
        margin-bottom: 1;
    }
    .compose-toolbar Button {
        margin-right: 1;
    }
    #compose-scroll {
        height: 1fr;
    }
    .compose-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .compose-card {
        border: solid $primary-darken-2;
        background: $panel;
        padding: 1;
        margin-bottom: 1;
    }
    .compose-field-row {
        layout: horizontal;
        height: 3;
        align: left middle;
        margin-bottom: 1;
    }
    .compose-field-row Label {
        width: 22;
        color: $text-muted;
    }
    .compose-field-row Input, .compose-field-row Select {
        width: 1fr;
    }
    .compose-warn {
        background: $warning-darken-2;
        color: $text;
        padding: 0 1;
        margin-bottom: 1;
    }
    #compose-raw-area {
        height: 20;
        margin-top: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._raw_content = ""
        self._show_raw = False

    def compose(self) -> ComposeResult:
        with Horizontal(classes="compose-toolbar"):
            yield Label("🐳  Editor docker-compose.yml", classes="compose-title")
            yield Button("🔍 Leer archivo", id="cmp-read", variant="default")
            yield Button("💾 Guardar", id="cmp-save", variant="primary")
            yield Button("👁 Ver YAML", id="cmp-toggle-raw", variant="default")

        yield Static(
            "⚠ Los cambios requieren reiniciar los contenedores para aplicarse.",
            classes="compose-warn"
        )

        yield ScrollableContainer(
            # Minecraft server section
            self._build_mc_section(),
            id="compose-scroll"
        )

        yield TextArea("", id="compose-raw-area", language="yaml", show_line_numbers=True)

    def _build_mc_section(self) -> Vertical:
        return Vertical(
            Label("Servidor Minecraft (mc_servidor)", classes="compose-title"),

            Horizontal(
                Label("Versión de Minecraft:"),
                Select(options=_VERSIONS, value="1.20.4", id="cmp-version", allow_blank=False),
                classes="compose-field-row"
            ),
            Horizontal(
                Label("Tipo de servidor:"),
                Select(options=_SERVER_TYPES, value="PAPER", id="cmp-type", allow_blank=False),
                classes="compose-field-row"
            ),
            Horizontal(
                Label("Memoria RAM (ej: 5G):"),
                Input(value="5G", placeholder="5G", id="cmp-memory"),
                classes="compose-field-row"
            ),
            Horizontal(
                Label("Puerto (host:25565):"),
                Input(value="25565", placeholder="25565", id="cmp-port"),
                classes="compose-field-row"
            ),
            Horizontal(
                Label("Política de reinicio:"),
                Select(options=_RESTART_POLICIES, value="always", id="cmp-restart", allow_blank=False),
                classes="compose-field-row"
            ),
            Horizontal(
                Label("RCON habilitado:"),
                Switch(value=True, id="cmp-rcon-enabled"),
                classes="compose-field-row"
            ),
            Horizontal(
                Label("Contraseña RCON:"),
                Input(value="mcpassword", placeholder="contraseña", id="cmp-rcon-pass", password=True),
                classes="compose-field-row"
            ),
            classes="compose-card"
        )

    def on_mount(self) -> None:
        self.run_worker(self._load_compose(), exclusive=False)
        # Hide raw area initially
        try:
            self.query_one("#compose-raw-area", TextArea).display = False
        except Exception:
            pass

    async def _load_compose(self) -> None:
        compose_path = app_config.compose_dir / "docker-compose.yml"
        if not compose_path.exists():
            return

        self._raw_content = compose_path.read_text(encoding="utf-8")

        # Parse key values using regex (avoids pyyaml dependency for simple cases)
        import re

        def _get(key: str, default: str = "") -> str:
            m = re.search(rf"{re.escape(key)}:\s*[\"']?([^\n\"']+)[\"']?", self._raw_content)
            return m.group(1).strip() if m else default

        try:
            version = _get("VERSION", "1.20.4")
            srv_type = _get("TYPE", "PAPER")
            memory = _get("MEMORY", "5G")
            rcon_pass = _get("rcon.password", "mcpassword")

            # Find the matching option or use first available
            self.query_one("#cmp-version", Select).value = version if any(v[1] == version for v in _VERSIONS) else "1.20.4"
            self.query_one("#cmp-type", Select).value = srv_type if any(v[1] == srv_type for v in _SERVER_TYPES) else "PAPER"
            self.query_one("#cmp-memory", Input).value = memory
            self.query_one("#cmp-rcon-pass", Input).value = rcon_pass
        except Exception:
            pass

        try:
            self.query_one("#compose-raw-area", TextArea).text = self._raw_content
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "cmp-read":
            await self._load_compose()
        elif bid == "cmp-save":
            await self._save_compose()
        elif bid == "cmp-toggle-raw":
            self._show_raw = not self._show_raw
            try:
                raw = self.query_one("#compose-raw-area", TextArea)
                raw.display = self._show_raw
                raw.text = self._raw_content
            except Exception:
                pass
            event.button.label = "🙈 Ocultar YAML" if self._show_raw else "👁 Ver YAML"

    async def _save_compose(self) -> None:
        import re
        try:
            content = self._raw_content
            version = str(self.query_one("#cmp-version", Select).value)
            srv_type = str(self.query_one("#cmp-type", Select).value)
            memory = self.query_one("#cmp-memory", Input).value.strip()
            rcon_pass = self.query_one("#cmp-rcon-pass", Input).value.strip()
            rcon_enabled = self.query_one("#cmp-rcon-enabled", Switch).value

            def _replace(key: str, value: str) -> str:
                return re.sub(
                    rf"(\s+{re.escape(key)}:\s*)\S+",
                    rf"\g<1>{value}",
                    content
                )

            content = _replace("VERSION", version)
            content = _replace("TYPE", srv_type)
            content = _replace("MEMORY", memory)

            compose_path = app_config.compose_dir / "docker-compose.yml"
            compose_path.write_text(content, encoding="utf-8")
            self._raw_content = content

            try:
                self.query_one("#compose-raw-area", TextArea).text = content
            except Exception:
                pass

            self.app.notify(
                "docker-compose.yml guardado. Ejecuta 'docker compose up -d' para aplicar.",
                severity="warning"
            )
        except Exception as e:
            self.app.notify(f"Error: {e}", severity="error")
