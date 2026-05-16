from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual.containers import Center, Vertical

from mc_manager.core.config import docker, app_config, os_info
from mc_manager.core.docker_client import ContainerState


class StartupScreen(ModalScreen):
    """Modal shown at startup to display and handle container state."""

    CSS = """
    StartupScreen {
        align: center middle;
    }
    #startup-box {
        width: 58;
        height: auto;
        background: $surface;
        border: double $accent;
        padding: 2 3;
    }
    #startup-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #startup-os {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    #startup-status-label {
        text-align: center;
        text-style: bold;
        height: 3;
        content-align: center middle;
        margin-bottom: 1;
    }
    #startup-description {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }
    .startup-btn-row {
        layout: horizontal;
        height: auto;
        align: center middle;
    }
    .startup-btn-row Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="startup-box"):
            yield Label("⛏  MC SERVER MANAGER", id="startup-title")
            yield Label(f"Sistema: {os_info.display_name}", id="startup-os")
            yield Label("Comprobando servidor...", id="startup-status-label")
            yield Label("", id="startup-description")
            with Center(classes="startup-btn-row"):
                yield Button("Continuar →", id="btn-continue", variant="primary")

    def on_mount(self) -> None:
        self.run_worker(self._check_state(), exclusive=True)

    async def _check_state(self) -> None:
        state = docker.get_container_state(app_config.minecraft_container)
        status_label = self.query_one("#startup-status-label", Label)
        desc_label = self.query_one("#startup-description", Label)
        btn_continue = self.query_one("#btn-continue", Button)

        if state == ContainerState.RUNNING:
            status_label.update("🟢  SERVIDOR EN LÍNEA")
            status_label.add_class("status-running")
            desc_label.update("El servidor Minecraft ya está corriendo.\nPuedes gestionar todo desde el dashboard.")
            btn_continue.label = "Ir al Dashboard →"

        elif state == ContainerState.STOPPED:
            status_label.update("🔴  SERVIDOR DETENIDO")
            status_label.add_class("status-stopped")
            desc_label.update("El contenedor existe pero está parado.\nPuedes iniciarlo desde el Dashboard.")
            btn_continue.label = "Continuar al Manager →"
            # Add a start button dynamically
            btn_row = self.query_one(".startup-btn-row")
            await btn_row.mount(
                Button("▶  Iniciar Servidor", id="btn-start", variant="success"),
                before=btn_continue
            )

        elif state == ContainerState.NOT_CREATED:
            status_label.update("⚪  PRIMERA VEZ / SIN CONTENEDOR")
            status_label.add_class("status-unknown")
            desc_label.update(
                "No se encontró el contenedor de Minecraft.\n"
                "Usa 'Crear y Levantar' para iniciar por primera vez."
            )
            btn_row = self.query_one(".startup-btn-row")
            await btn_row.mount(
                Button("🚀  Crear y Levantar", id="btn-create", variant="warning"),
                before=btn_continue
            )

        else:
            status_label.update("⚠  ESTADO DESCONOCIDO")
            status_label.add_class("status-unknown")
            desc_label.update(
                "No se pudo determinar el estado del servidor.\n"
                "Comprueba que Docker esté corriendo."
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-continue":
            self.dismiss()

        elif event.button.id == "btn-start":
            event.button.disabled = True
            event.button.label = "Iniciando..."
            self.run_worker(self._start_server(), exclusive=True)

        elif event.button.id == "btn-create":
            event.button.disabled = True
            event.button.label = "Creando contenedores..."
            self.run_worker(self._create_server(), exclusive=True)

    async def _start_server(self) -> None:
        out, err = docker.start()
        desc = self.query_one("#startup-description", Label)
        if err and not out:
            desc.update(f"Error al iniciar: {err}")
        else:
            desc.update("Servidor iniciado correctamente.")
            self.query_one("#startup-status-label", Label).update("🟢  SERVIDOR EN LÍNEA")
        btn = self.query_one("#btn-start", Button)
        btn.label = "▶  Iniciado"

    async def _create_server(self) -> None:
        desc = self.query_one("#startup-description", Label)
        desc.update("Descargando imagen y creando contenedores...\n(puede tardar varios minutos la primera vez)")
        out, err = docker.start()
        if err and not out:
            desc.update(f"Error: {err}")
        else:
            desc.update("Contenedores creados y servidor iniciando.")
            self.query_one("#startup-status-label", Label).update("🟢  SERVIDOR EN LÍNEA")
        btn = self.query_one("#btn-create", Button)
        btn.label = "✓  Creado"
