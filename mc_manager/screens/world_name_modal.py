from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Input
from textual.containers import Center, Vertical


class WorldNameModal(ModalScreen[str | None]):
    """Modal para ingresar o cambiar el nombre del mundo. Retorna el nombre o None al cancelar."""

    CSS = """
    WorldNameModal {
        align: center middle;
    }
    #wname-box {
        width: 64;
        height: auto;
        background: $surface;
        border: double $accent;
        padding: 2 3;
    }
    #wname-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #wname-hint {
        color: $text-muted;
        text-align: center;
        margin-bottom: 1;
    }
    #wname-error {
        color: $error;
        text-align: center;
        height: 1;
        margin-bottom: 1;
    }
    #wname-input {
        margin-bottom: 2;
    }
    .wname-btn-row {
        height: auto;
        align: center middle;
    }
    .wname-btn-row Button {
        margin: 0 1;
    }
    """

    def __init__(self, current_name: str = "world", action_label: str = "Confirmar") -> None:
        super().__init__()
        self._current_name = current_name
        self._action_label = action_label

    def compose(self) -> ComposeResult:
        with Vertical(id="wname-box"):
            yield Label("🌍  Nombre del Mundo", id="wname-title")
            yield Label(
                f'Nombre actual: "{self._current_name}"\n'
                "Los directorios del mundo serán renombrados automáticamente.",
                id="wname-hint",
            )
            yield Label("", id="wname-error")
            yield Input(
                value=self._current_name,
                placeholder="Nombre del mundo",
                id="wname-input",
            )
            with Center(classes="wname-btn-row"):
                yield Button(self._action_label, id="btn-wname-ok", variant="primary")
                yield Button("Cancelar", id="btn-wname-cancel", variant="default")

    def on_mount(self) -> None:
        self.query_one("#wname-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-wname-cancel":
            self.dismiss(None)
        else:
            self._submit()

    def _submit(self) -> None:
        name = self.query_one("#wname-input", Input).value.strip()
        if not name:
            self.query_one("#wname-error", Label).update("El nombre no puede estar vacío.")
            return
        self.dismiss(name)
