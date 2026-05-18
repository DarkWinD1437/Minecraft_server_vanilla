from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual.containers import Center, Vertical, Horizontal


class ConfirmModal(ModalScreen[bool]):
    """Modal de confirmación genérico. Llama dismiss(True/False)."""

    CSS = """
    ConfirmModal {
        align: center middle;
    }
    #confirm-box {
        width: 62;
        height: auto;
        background: $surface;
        border: double $warning;
        padding: 2 3;
    }
    #confirm-box.danger {
        border: double $error;
    }
    #confirm-title {
        text-align: center;
        text-style: bold;
        color: $warning;
        margin-bottom: 1;
    }
    #confirm-title.danger {
        color: $error;
    }
    #confirm-body {
        text-align: center;
        color: $text;
        margin-bottom: 2;
    }
    .confirm-btn-row {
        layout: horizontal;
        height: auto;
        align: center middle;
    }
    .confirm-btn-row Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        title: str,
        body: str,
        confirm_label: str = "Confirmar",
        danger: bool = False,
    ) -> None:
        super().__init__()
        self._title = title
        self._body = body
        self._confirm_label = confirm_label
        self._danger = danger

    def compose(self) -> ComposeResult:
        box_classes = "danger" if self._danger else ""
        with Vertical(id="confirm-box", classes=box_classes):
            yield Label(self._title, id="confirm-title", classes=box_classes)
            yield Label(self._body, id="confirm-body")
            with Center(classes="confirm-btn-row"):
                yield Button(
                    self._confirm_label,
                    id="btn-confirm",
                    variant="error" if self._danger else "warning",
                )
                yield Button("Cancelar", id="btn-cancel", variant="default")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-confirm")
