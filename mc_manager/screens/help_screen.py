from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Markdown, Label
from textual.containers import Vertical, Center

from mc_manager.__about__ import __brand__, __copyright__


_FEATURE_TITLES = {
    "dashboard": "Dashboard",
    "monitoring": "Monitoreo en Tiempo Real",
    "console": "Consola del Servidor",
    "players": "Gestión de Jugadores",
    "backups": "Backups",
    "settings": "Configuración del Servidor",
    "logs": "Log Viewer",
    "tunnel": "Túnel Playit.gg",
    "scheduler": "Programador de Tareas",
    "performance_tuner": "Rendimiento JVM",
    "event_log": "Historial de Eventos",
    "compose_editor": "Editor Compose",
    "alerts": "Alertas",
    "world_stats": "Stats del Mundo",
    "plugins": "Gestor de Plugins",
}


class HelpScreen(ModalScreen):
    """Modal that displays the help.md file for a specific feature."""

    BINDINGS = [("escape", "dismiss", "Cerrar")]

    CSS = """
    HelpScreen {
        align: center middle;
    }
    #help-box {
        width: 80%;
        height: 85%;
        background: $surface;
        border: double $accent;
        padding: 1 2;
    }
    #help-header {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #help-markdown {
        height: 1fr;
        overflow-y: auto;
    }
    #help-close-row {
        height: 3;
        align: center middle;
        margin-top: 1;
    }
    #help-brand {
        text-align: center;
        color: $text-muted;
        text-style: italic;
        height: 1;
    }
    """

    def __init__(self, feature_id: str = "dashboard") -> None:
        super().__init__()
        self.feature_id = feature_id

    def compose(self) -> ComposeResult:
        title = _FEATURE_TITLES.get(self.feature_id, self.feature_id.replace("_", " ").title())
        content = self._load_help_content()
        with Vertical(id="help-box"):
            yield Label(f"❓  Ayuda: {title}", id="help-header")
            yield Markdown(content, id="help-markdown")
            with Center(id="help-close-row"):
                yield Button("Cerrar  [ESC]", id="btn-close", variant="default")
            yield Label(f"{__brand__}  —  {__copyright__}", id="help-brand")

    def _load_help_content(self) -> str:
        features_dir = Path(__file__).parent.parent / "features"
        help_file = features_dir / self.feature_id / "help.md"
        if help_file.exists():
            return help_file.read_text(encoding="utf-8")
        return f"# {self.feature_id.replace('_', ' ').title()}\n\nNo hay documentación disponible para esta sección."

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close":
            self.dismiss()

    def action_dismiss(self) -> None:
        self.dismiss()
