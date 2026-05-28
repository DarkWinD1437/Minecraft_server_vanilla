from __future__ import annotations

import asyncio
from datetime import datetime

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, Static
from textual.containers import Horizontal, Vertical, Grid
from textual.reactive import reactive

from mc_manager.core.config import docker, app_config
from mc_manager.core.docker_client import ContainerState
from mc_manager.core.events import (
    StatsUpdated, ContainerStateChanged, TunnelLinkUpdated
)
from mc_manager.features.monitoring.meters import SparklineCard


_STATE_ICON = {
    ContainerState.RUNNING: "🟢",
    ContainerState.STOPPED: "🔴",
    ContainerState.PAUSED:  "⏸",
    ContainerState.NOT_CREATED: "⚪",
    ContainerState.UNKNOWN: "⚠️",
}

_STATE_TEXT = {
    ContainerState.RUNNING: "SERVIDOR EN LÍNEA",
    ContainerState.STOPPED: "SERVIDOR DETENIDO",
    ContainerState.PAUSED:  "SERVIDOR EN PAUSA",
    ContainerState.NOT_CREATED: "SIN CONTENEDOR",
    ContainerState.UNKNOWN: "ESTADO DESCONOCIDO",
}


class DashboardPane(Widget):

    DEFAULT_CSS = """
    DashboardPane {
        width: 100%;
        height: 100%;
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
        padding: 1 2;
    }
    .dash-card {
        border: solid $primary-darken-2;
        background: $panel;
        padding: 1;
        height: 100%;
    }
    .dash-card-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #status-card {
        height: 14;
    }
    #actions-card {
        height: 14;
    }
    #monitor-mini-card {
        height: 14;
    }
    #tunnel-card {
        height: 14;
    }
    #world-card {
        column-span: 2;
        height: 7;
    }
    #dash-status-label {
        text-align: center;
        text-style: bold;
        height: 3;
        content-align: center middle;
    }
    #dash-uptime {
        text-align: center;
        color: $text-muted;
    }
    #dash-players {
        text-align: center;
        color: $accent;
        margin-top: 1;
    }
    .dash-btn-row {
        layout: horizontal;
        height: auto;
        margin-top: 1;
        align: center middle;
    }
    .dash-btn-row Button {
        margin: 0 1;
        width: 14;
    }
    #dash-tunnel-url {
        color: $accent;
        text-style: underline;
        margin-top: 1;
    }
    .mini-spark-row {
        layout: horizontal;
        height: 8;
    }
    .world-name-row {
        layout: horizontal;
        height: 2;
        align: left middle;
        margin-bottom: 1;
    }
    .world-name-label {
        width: 18;
        color: $text-muted;
    }
    #dash-world-name {
        color: $accent;
        text-style: bold;
    }
    .dash-world-btn-row {
        layout: horizontal;
        height: 3;
        align: left middle;
    }
    .dash-world-btn-row Button {
        margin-right: 1;
        min-width: 16;
    }
    """

    _current_state: ContainerState = ContainerState.UNKNOWN
    _tunnel_url: str = ""

    def compose(self) -> ComposeResult:
        # Card 1: Server Status
        with Vertical(classes="dash-card", id="status-card"):
            yield Label("🖥  Estado del Servidor", classes="dash-card-title")
            yield Label("⚠️  Verificando...", id="dash-status-label")
            yield Label("Uptime: --:--:--", id="dash-uptime")
            yield Label("Jugadores: --", id="dash-players")

        # Card 2: Quick Actions
        with Vertical(classes="dash-card", id="actions-card"):
            yield Label("⚡  Acciones Rápidas", classes="dash-card-title")
            with Horizontal(classes="dash-btn-row"):
                yield Button("▶ Iniciar", id="dash-btn-start", variant="success")
                yield Button("⏹ Detener", id="dash-btn-stop", variant="error")
            with Horizontal(classes="dash-btn-row"):
                yield Button("🔄 Reiniciar", id="dash-btn-restart", variant="warning")
                yield Button("💻 Consola", id="dash-btn-console", variant="default")
            with Horizontal(classes="dash-btn-row"):
                yield Button("💾 Backup", id="dash-btn-backup", variant="default")

        # Card 3: Mini monitor
        with Vertical(classes="dash-card", id="monitor-mini-card"):
            yield Label("📊  Recursos (últimos 30s)", classes="dash-card-title")
            with Horizontal(classes="mini-spark-row"):
                yield SparklineCard("CPU", unit="%", max_points=30, id="mini-cpu")
                yield SparklineCard("RAM", unit="MB", max_points=30, id="mini-ram")

        # Card 4: Tunnel
        with Vertical(classes="dash-card", id="tunnel-card"):
            yield Label("🌐  Túnel Playit.gg", classes="dash-card-title")
            yield Label("Sin link detectado aún.", id="dash-tunnel-status")
            yield Label("", id="dash-tunnel-url")
            with Horizontal(classes="dash-btn-row"):
                yield Button("🔄 Recargar Link", id="dash-btn-reload-link", variant="default")

        # Card 5: World (spans both columns)
        with Vertical(classes="dash-card", id="world-card"):
            yield Label("🌍  Mundo Activo", classes="dash-card-title")
            with Horizontal(classes="world-name-row"):
                yield Label("Nombre actual:", classes="world-name-label")
                yield Label("—", id="dash-world-name")
            with Horizontal(classes="dash-world-btn-row"):
                yield Button("✏️ Renombrar Mundo", id="dash-btn-rename-world", variant="default")
                yield Button("🌱 Nuevo Mundo", id="dash-btn-new-world", variant="error")

    def on_mount(self) -> None:
        self.run_worker(self._refresh_state(), exclusive=False)
        self.set_interval(30.0, lambda: self.run_worker(self._refresh_state()))
        self.set_interval(1.0, self._tick_uptime)
        self._start_ts: datetime | None = None
        self._load_world_name()

    def _load_world_name(self) -> None:
        try:
            from mc_manager.features.settings.properties_parser import read_properties
            props = read_properties(app_config.server_properties)
            name = props.get("level-name", "world")
            self.query_one("#dash-world-name", Label).update(name)
        except Exception:
            pass

    async def _refresh_state(self) -> None:
        state = await asyncio.to_thread(docker.get_container_state, app_config.minecraft_container)
        self._update_status_display(state)

        if state == ContainerState.RUNNING:
            info, _ = await asyncio.to_thread(docker.get_container_info, app_config.minecraft_container)
            started = info.get("State", {}).get("StartedAt", "")
            if started:
                try:
                    from datetime import timezone
                    dt_str = started[:26].replace("Z", "+00:00")
                    self._start_ts = datetime.fromisoformat(dt_str.replace("+00:00", "")).replace(tzinfo=timezone.utc)
                except Exception:
                    self._start_ts = None

    def _update_status_display(self, state: ContainerState) -> None:
        self._current_state = state
        icon = _STATE_ICON.get(state, "⚠️")
        text = _STATE_TEXT.get(state, "DESCONOCIDO")
        try:
            lbl = self.query_one("#dash-status-label", Label)
            lbl.update(f"{icon}  {text}")
            lbl.remove_class("status-running", "status-stopped", "status-unknown")
            if state == ContainerState.RUNNING:
                lbl.add_class("status-running")
            elif state == ContainerState.STOPPED:
                lbl.add_class("status-stopped")
            else:
                lbl.add_class("status-unknown")
        except Exception:
            pass

        # Enable/disable buttons
        is_running = state == ContainerState.RUNNING
        try:
            self.query_one("#dash-btn-start", Button).disabled = is_running
            self.query_one("#dash-btn-stop", Button).disabled = not is_running
            self.query_one("#dash-btn-restart", Button).disabled = not is_running
        except Exception:
            pass

    def _tick_uptime(self) -> None:
        if self._start_ts is None:
            return
        from datetime import timezone
        from mc_manager.utils.formatting import seconds_to_human
        now = datetime.now(tz=timezone.utc)
        delta = (now - self._start_ts).total_seconds()
        try:
            self.query_one("#dash-uptime", Label).update(f"Uptime: {seconds_to_human(delta)}")
        except Exception:
            pass

    def on_stats_updated(self, message: StatsUpdated) -> None:
        try: self.query_one("#mini-cpu", SparklineCard).push(message.cpu_pct)
        except Exception: pass
        try: self.query_one("#mini-ram", SparklineCard).push(message.ram_used_mb)
        except Exception: pass

    def on_container_state_changed(self, message: ContainerStateChanged) -> None:
        if message.container == app_config.minecraft_container:
            self._update_status_display(message.state)

    def on_tunnel_link_updated(self, message: TunnelLinkUpdated) -> None:
        self._tunnel_url = message.url
        try:
            self.query_one("#dash-tunnel-status", Label).update("Link detectado:")
            self.query_one("#dash-tunnel-url", Label).update(message.url)
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "dash-btn-start":
            event.button.disabled = True
            self.app.notify("Iniciando servidor...", severity="information")
            self.run_worker(self._do_start(), exclusive=True)
        elif bid == "dash-btn-stop":
            event.button.disabled = True
            self.app.notify("Deteniendo servidor...", severity="warning")
            self.run_worker(self._do_stop(), exclusive=True)
        elif bid == "dash-btn-restart":
            self.app.notify("Reiniciando servidor...", severity="warning")
            self.run_worker(self._do_restart(), exclusive=True)
        elif bid == "dash-btn-console":
            # Navigate to console
            try:
                from mc_manager.screens.main_screen import MainScreen
                screen = self.app.query_one(MainScreen)
                screen._switch_to("console")
            except Exception:
                pass
        elif bid == "dash-btn-backup":
            try:
                from mc_manager.screens.main_screen import MainScreen
                screen = self.app.query_one(MainScreen)
                screen._switch_to("backups")
            except Exception:
                pass
        elif bid == "dash-btn-reload-link":
            self.run_worker(self._reload_tunnel_link(), exclusive=False)

        elif bid == "dash-btn-rename-world":
            from mc_manager.screens.world_name_modal import WorldNameModal
            from mc_manager.features.settings.properties_parser import read_properties
            current_name = "world"
            try:
                props = read_properties(app_config.server_properties)
                current_name = props.get("level-name", "world")
            except Exception:
                pass

            def _on_rename(new_name: str | None) -> None:
                if not new_name or new_name == current_name:
                    return
                from mc_manager.screens.confirm_modal import ConfirmModal
                def _on_confirm(confirmed: bool) -> None:
                    if confirmed:
                        self.run_worker(self._do_rename_world(current_name, new_name), exclusive=True)
                self.app.push_screen(
                    ConfirmModal(
                        title="✏️  Renombrar Mundo",
                        body=(
                            f'Renombrar de "{current_name}" a "{new_name}".\n\n'
                            "Se detendrá el servidor, se renombrarán los\n"
                            "directorios del mundo y se actualizará la\n"
                            "configuración. Luego se reiniciará."
                        ),
                        confirm_label="Renombrar",
                        danger=False,
                    ),
                    _on_confirm,
                )
            self.app.push_screen(
                WorldNameModal(current_name=current_name, action_label="Renombrar"),
                _on_rename,
            )

        elif bid == "dash-btn-new-world":
            from mc_manager.screens.world_name_modal import WorldNameModal
            from mc_manager.features.settings.properties_parser import read_properties
            current_name = "world"
            try:
                props = read_properties(app_config.server_properties)
                current_name = props.get("level-name", "world")
            except Exception:
                pass

            def _on_new_name(new_name: str | None) -> None:
                if not new_name:
                    return
                from mc_manager.screens.confirm_modal import ConfirmModal
                def _on_confirm(confirmed: bool) -> None:
                    if confirmed:
                        self.run_worker(self._do_new_world(new_name), exclusive=True)
                self.app.push_screen(
                    ConfirmModal(
                        title="🌱  Generar Nuevo Mundo",
                        body=(
                            f'Se creará el mundo "{new_name}" desde cero.\n\n'
                            "Se eliminan TODOS los mundos existentes (incluidos\n"
                            "los no activos). Se crea backup automático antes.\n\n"
                            "Los inventarios de jugadores también se reiniciarán.\n"
                            "Esta acción NO se puede deshacer (excepto por backup)."
                        ),
                        confirm_label="Crear Nuevo Mundo",
                        danger=True,
                    ),
                    _on_confirm,
                )
            self.app.push_screen(
                WorldNameModal(current_name=current_name, action_label="Crear Nuevo Mundo"),
                _on_new_name,
            )

    async def _do_start(self) -> None:
        out, err = await asyncio.to_thread(docker.start)
        if err and not out:
            self.app.notify(f"Error: {err}", severity="error")
        else:
            self.app.notify("Servidor iniciado", severity="information")
        await self._refresh_state()

    async def _do_stop(self) -> None:
        out, err = await asyncio.to_thread(docker.stop)
        if err and not out:
            self.app.notify(f"Error: {err}", severity="error")
        else:
            self.app.notify("Servidor detenido", severity="warning")
        self._start_ts = None
        await self._refresh_state()

    async def _do_restart(self) -> None:
        out, err = await asyncio.to_thread(docker.restart, app_config.minecraft_container)
        if err and not out:
            self.app.notify(f"Error al reiniciar: {err}", severity="error")
        else:
            self.app.notify("Servidor reiniciado", severity="information")
        await self._refresh_state()

    async def _do_rename_world(self, old_name: str, new_name: str) -> None:
        from mc_manager.features.world_stats.widget import (
            _rename_world_dirs, _update_world_name_in_compose, _update_world_name_in_properties,
        )
        was_running = self._current_state == ContainerState.RUNNING
        if was_running:
            self.app.notify("Deteniendo servidor para renombrar...", severity="warning", timeout=5)
            await asyncio.to_thread(docker.stop, app_config.minecraft_container)

        errors = await asyncio.to_thread(_rename_world_dirs, old_name, new_name)
        for err in errors:
            self.app.notify(err, severity="error")

        await asyncio.to_thread(_update_world_name_in_compose, new_name)
        await asyncio.to_thread(_update_world_name_in_properties, new_name)

        try:
            self.query_one("#dash-world-name", Label).update(new_name)
        except Exception:
            pass

        if was_running:
            self.app.notify("Reiniciando servidor...", severity="information", timeout=5)
            await asyncio.to_thread(docker.start)
            await self._refresh_state()

        self.app.notify(f'Mundo renombrado a "{new_name}".', severity="information", timeout=8)

    async def _do_new_world(self, new_name: str) -> None:
        import shutil
        from mc_manager.features.world_stats.widget import (
            _find_all_world_root_dirs, _update_world_name_in_compose, _update_world_name_in_properties,
        )
        from mc_manager.features.event_log import event_store
        data_dir = app_config.data_dir

        self.app.notify("Creando backup antes de eliminar el mundo...", severity="warning", timeout=8)
        try:
            from mc_manager.features.backups.backup_engine import create_backup
            backup_dir = app_config.compose_dir / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(create_backup, data_dir, backup_dir, "pre-nuevo-mundo", True)
        except Exception as e:
            self.app.notify(f"Backup falló: {e}. Abortando.", severity="error")
            return

        self.app.notify("Deteniendo servidor...", severity="warning", timeout=5)
        await asyncio.to_thread(docker.stop, app_config.minecraft_container)

        all_world_roots = await asyncio.to_thread(_find_all_world_root_dirs, data_dir)
        for world_root in all_world_roots:
            for suffix in ["", "_nether", "_the_end"]:
                d = data_dir / f"{world_root.name}{suffix}"
                if d.exists():
                    try:
                        await asyncio.to_thread(shutil.rmtree, str(d))
                    except Exception as e:
                        self.app.notify(f"Error eliminando {d.name}: {e}", severity="error")

        try:
            await asyncio.to_thread(_update_world_name_in_compose, new_name)
            await asyncio.to_thread(_update_world_name_in_properties, new_name)
        except Exception as e:
            self.app.notify(f"Error actualizando configuración: {e}", severity="warning")

        try:
            self.query_one("#dash-world-name", Label).update(new_name)
        except Exception:
            pass

        self.app.notify(f'Iniciando servidor con mundo "{new_name}"...', severity="information", timeout=8)
        await asyncio.to_thread(docker.start)
        await self._refresh_state()

        event_store.init(app_config.logs_dir / "events.db")
        epoch_id = event_store.create_world_epoch(seed=None, notes=f'Mundo regenerado: "{new_name}"')
        self.app.notify(
            f'Mundo "{new_name}" creado (época #{epoch_id}). Backup guardado.',
            severity="information",
            timeout=10,
        )

    async def _reload_tunnel_link(self) -> None:
        logs, _ = docker.get_logs(app_config.tunnel_container, tail=100)
        import re
        url_match = re.search(r"https://(?:www\.)?playit\.gg\S+", logs, re.IGNORECASE)
        if url_match:
            url = url_match.group(0)
            self._tunnel_url = url
            try:
                self.query_one("#dash-tunnel-status", Label).update("Link detectado:")
                self.query_one("#dash-tunnel-url", Label).update(url)
            except Exception:
                pass
        else:
            self.app.notify("No se encontró link de Playit.gg en los logs", severity="warning")
