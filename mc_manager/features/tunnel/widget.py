from __future__ import annotations

import re

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, Static
from textual.containers import Horizontal, Vertical

from mc_manager.core.config import docker, app_config
from mc_manager.core.events import TunnelLinkUpdated
from mc_manager.core.docker_client import ContainerState


_PLAYIT_URL = re.compile(r"https://(?:www\.)?playit\.gg\S+", re.IGNORECASE)
_CONNECT_ADDR = re.compile(r"connect_addr:\s*([\d\.]+:\d+)")


class TunnelPane(Widget):

    DEFAULT_CSS = """
    TunnelPane {
        width: 100%;
        height: 100%;
        padding: 1 2;
        layout: vertical;
    }
    .tunnel-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .tunnel-card {
        border: solid $primary-darken-2;
        background: $panel;
        padding: 1;
        margin-bottom: 1;
    }
    .tunnel-status-label {
        text-style: bold;
        height: 2;
        content-align: left middle;
    }
    .tunnel-url-label {
        color: $accent;
        text-style: underline bold;
        margin-top: 1;
    }
    .tunnel-btn-row {
        layout: horizontal;
        height: 3;
        margin-top: 1;
        align: left middle;
    }
    .tunnel-btn-row Button {
        margin-right: 1;
    }
    .tunnel-info {
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._link = ""

    def compose(self) -> ComposeResult:
        yield Label("🌐  Túnel de Red — Playit.gg", classes="tunnel-title")

        with Vertical(classes="tunnel-card"):
            yield Label("Estado del Túnel:", classes="tunnel-title")
            yield Label("Verificando...", id="tunnel-state-label", classes="tunnel-status-label")

            with Horizontal(classes="tunnel-btn-row"):
                yield Button("▶ Iniciar Túnel", id="tun-start", variant="success")
                yield Button("⏹ Detener Túnel", id="tun-stop", variant="error")
                yield Button("🔄 Reiniciar Túnel", id="tun-restart", variant="warning")
                yield Button("🔍 Buscar Link", id="tun-find-link", variant="default")

        with Vertical(classes="tunnel-card"):
            yield Label("🔗  Link de Conexión:", classes="tunnel-title")
            yield Static("Sin link detectado. Inicia el túnel y espera el link.", id="tunnel-link-display")
            with Horizontal(classes="tunnel-btn-row"):
                yield Button("📋 Copiar Link", id="tun-copy", variant="primary")

        with Vertical(classes="tunnel-card"):
            yield Label("ℹ️  Información:", classes="tunnel-title")
            yield Static(
                "Playit.gg es un servicio gratuito de tunel de red para juegos.\n"
                "Permite que otros jugadores se conecten al servidor Minecraft\n"
                "sin necesidad de abrir puertos en el router.\n\n"
                "1. Inicia el tunel con el boton 'Iniciar Tunel'\n"
                "2. La direccion publica aparece en playit.gg > Tunnels\n"
                "   (el agente v0.17 no la imprime en los logs)\n"
                "3. Cuando alguien se conecta, 'Buscar Link' detecta la IP:Puerto\n"
                "4. Compartir esa direccion con tus amigos en Minecraft",
                classes="tunnel-info"
            )

    def on_mount(self) -> None:
        self.run_worker(self._check_state(), exclusive=False)
        self.set_interval(10.0, lambda: self.run_worker(self._check_state()))

    async def _check_state(self) -> None:
        state = docker.get_container_state(app_config.tunnel_container)
        lbl = self.query_one("#tunnel-state-label", Label)
        if state == ContainerState.RUNNING:
            lbl.update("🟢  TÚNEL ACTIVO")
            lbl.add_class("status-running")
        elif state == ContainerState.STOPPED:
            lbl.update("🔴  TÚNEL DETENIDO")
            lbl.add_class("status-stopped")
        elif state == ContainerState.NOT_CREATED:
            lbl.update("⚪  CONTENEDOR NO CREADO")
        else:
            lbl.update("⚠  ESTADO DESCONOCIDO")

    def on_tunnel_link_updated(self, message: TunnelLinkUpdated) -> None:
        self._link = message.url
        try:
            self.query_one("#tunnel-link-display", Static).update(message.url)
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "tun-start":
            self.app.notify("Iniciando túnel Playit.gg...", severity="information")
            self.run_worker(self._do_start(), exclusive=True)
        elif bid == "tun-stop":
            self.app.notify("Deteniendo túnel...", severity="warning")
            self.run_worker(self._do_stop(), exclusive=True)
        elif bid == "tun-restart":
            self.app.notify("Reiniciando túnel...", severity="warning")
            self.run_worker(self._do_restart(), exclusive=True)
        elif bid == "tun-find-link":
            self.run_worker(self._scan_logs_for_link(), exclusive=False)
        elif bid == "tun-copy":
            if self._link:
                self.app.notify(f"Link: {self._link}\n(Cópialo manualmente de arriba)", severity="information")
            else:
                self.app.notify("No hay link disponible", severity="warning")

    async def _do_start(self) -> None:
        out, err = docker.start(service="playit-agent")
        if err and not out:
            self.app.notify(f"Error: {err}", severity="error")
        await self._check_state()

    async def _do_stop(self) -> None:
        out, err = docker.stop(service=app_config.tunnel_container)
        if err and not out:
            self.app.notify(f"Error: {err}", severity="error")
        await self._check_state()

    async def _do_restart(self) -> None:
        docker.restart(app_config.tunnel_container)
        self.app.notify("Túnel reiniciado", severity="information")
        await self._check_state()

    async def _scan_logs_for_link(self) -> None:
        logs, _ = docker.get_logs(app_config.tunnel_container, tail=200)
        match = _PLAYIT_URL.search(logs) or _CONNECT_ADDR.search(logs)
        if match:
            url = match.group(1) if match.lastindex else match.group(0)
            self._link = url
            try:
                self.query_one("#tunnel-link-display", Static).update(url)
            except Exception:
                pass
            self.app.notify("Direccion detectada en logs", severity="information")
        else:
            self.app.notify(
                "No se detecto direccion en logs. Buscala en playit.gg > Tunnels",
                severity="warning"
            )
