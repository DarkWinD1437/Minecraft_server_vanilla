from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Header, Footer, ListView, ListItem, Label, ContentSwitcher, Static
)
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from mc_manager.core.config import os_info, app_config, docker
from mc_manager.core.docker_client import ContainerState
from mc_manager.core.events import (
    StatsUpdated, SystemStatsUpdated, LogLine, ContainerStateChanged,
    PlayitLinkFound, TunnelLinkUpdated, AlertTriggered
)
from mc_manager.screens.help_screen import HelpScreen


# Feature registry: (id, label, emoji)
FEATURES = [
    ("dashboard",         "Dashboard",          "🏠"),
    ("monitoring",        "Monitoreo",           "📊"),
    ("console",           "Consola",             "💻"),
    ("players",           "Jugadores",           "👥"),
    ("backups",           "Backups",             "💾"),
    ("settings",          "Configuración",       "⚙️"),
    ("logs",              "Log Viewer",          "📄"),
    ("tunnel",            "Túnel Playit.gg",     "🌐"),
    # Advanced
    ("scheduler",         "Programador",         "⏰"),
    ("performance_tuner", "Rendimiento JVM",     "🚀"),
    ("event_log",         "Historial Eventos",   "📋"),
    ("compose_editor",    "Editor Compose",      "🐳"),
    ("alerts",            "Alertas",             "🔔"),
    ("world_stats",       "Stats del Mundo",     "🌍"),
    ("plugins",           "Plugins",             "🔌"),
]

ADVANCED_SEPARATOR_IDX = 8  # index where "Avanzado" separator appears


class NavItem(ListItem):
    def __init__(self, feature_id: str, label: str, emoji: str) -> None:
        super().__init__()
        self.feature_id = feature_id
        self._label = label
        self._emoji = emoji

    def compose(self) -> ComposeResult:
        yield Label(f" {self._emoji} {self._label}")


class MainScreen(Screen):
    CSS_PATH = [
        "../styles/main.tcss",
        "../styles/common.tcss",
        "../styles/monitoring.tcss",
    ]

    BINDINGS = [
        Binding("1", "goto_feature_0", "Dashboard", show=False),
        Binding("2", "goto_feature_1", "Monitoreo", show=False),
        Binding("3", "goto_feature_2", "Consola", show=False),
        Binding("4", "goto_feature_3", "Jugadores", show=False),
        Binding("5", "goto_feature_4", "Backups", show=False),
        Binding("6", "goto_feature_5", "Configuración", show=False),
        Binding("7", "goto_feature_6", "Logs", show=False),
        Binding("8", "goto_feature_7", "Túnel", show=False),
        Binding("9", "goto_feature_8", "Programador", show=False),
        Binding("question_mark", "show_help", "Ayuda", show=True),
        Binding("s", "toggle_server", "Start/Stop", show=True),
        Binding("r", "refresh_pane", "Refresh", show=True),
        Binding("q", "request_quit", "Salir", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._current_feature = "dashboard"
        self._server_state = ContainerState.UNKNOWN

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            with Vertical(id="sidebar"):
                yield Label("⛏  MC MANAGER", id="sidebar-title")
                yield self._build_nav()
            with Vertical(id="content-area"):
                yield self._build_content_switcher()
        yield Footer()

    def _build_nav(self) -> ListView:
        items: list[ListItem] = []
        for i, (fid, label, emoji) in enumerate(FEATURES):
            if i == ADVANCED_SEPARATOR_IDX:
                items.append(ListItem(Static("─── Avanzado ───", classes="nav-separator")))
            items.append(NavItem(fid, label, emoji))
        lv = ListView(*items, id="nav-list")
        return lv

    def _build_content_switcher(self) -> ContentSwitcher:
        from mc_manager.features.dashboard.widget import DashboardPane
        from mc_manager.features.monitoring.widget import MonitoringPane
        from mc_manager.features.console.widget import ConsolePane
        from mc_manager.features.players.widget import PlayersPane
        from mc_manager.features.backups.widget import BackupsPane
        from mc_manager.features.settings.widget import SettingsPane
        from mc_manager.features.logs.widget import LogViewerPane
        from mc_manager.features.tunnel.widget import TunnelPane
        from mc_manager.features.scheduler.widget import SchedulerPane
        from mc_manager.features.performance_tuner.widget import PerformanceTunerPane
        from mc_manager.features.event_log.widget import EventLogPane
        from mc_manager.features.compose_editor.widget import ComposeEditorPane
        from mc_manager.features.alerts.widget import AlertsPane
        from mc_manager.features.world_stats.widget import WorldStatsPane
        from mc_manager.features.plugins.widget import PluginsPane

        return ContentSwitcher(
            DashboardPane(id="dashboard"),
            MonitoringPane(id="monitoring"),
            ConsolePane(id="console"),
            PlayersPane(id="players"),
            BackupsPane(id="backups"),
            SettingsPane(id="settings"),
            LogViewerPane(id="logs"),
            TunnelPane(id="tunnel"),
            SchedulerPane(id="scheduler"),
            PerformanceTunerPane(id="performance_tuner"),
            EventLogPane(id="event_log"),
            ComposeEditorPane(id="compose_editor"),
            AlertsPane(id="alerts"),
            WorldStatsPane(id="world_stats"),
            PluginsPane(id="plugins"),
            initial="dashboard",
        )

    def on_mount(self) -> None:
        from mc_manager.workers.stats_worker import run_stats_worker
        from mc_manager.workers.log_stream_worker import run_log_worker
        self.run_worker(run_stats_worker(self.app), exclusive=False, name="stats")
        self.run_worker(
            run_log_worker(self.app, app_config.minecraft_container),
            exclusive=False, name="mc-logs"
        )
        self.run_worker(
            run_log_worker(self.app, app_config.tunnel_container),
            exclusive=False, name="tunnel-logs"
        )
        self._check_server_state()

    def _check_server_state(self) -> None:
        self.run_worker(self._async_check_state(), exclusive=False)

    async def _async_check_state(self) -> None:
        state = await asyncio.to_thread(docker.get_container_state, app_config.minecraft_container)
        self._server_state = state
        self.post_message(ContainerStateChanged(state, app_config.minecraft_container))

    # ── Navigation ──────────────────────────────────────────────────────────

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, NavItem):
            self._switch_to(event.item.feature_id)

    def _switch_to(self, feature_id: str) -> None:
        self._current_feature = feature_id
        switcher = self.query_one(ContentSwitcher)
        switcher.current = feature_id

    def action_goto_feature_0(self) -> None: self._switch_to("dashboard")
    def action_goto_feature_1(self) -> None: self._switch_to("monitoring")
    def action_goto_feature_2(self) -> None: self._switch_to("console")
    def action_goto_feature_3(self) -> None: self._switch_to("players")
    def action_goto_feature_4(self) -> None: self._switch_to("backups")
    def action_goto_feature_5(self) -> None: self._switch_to("settings")
    def action_goto_feature_6(self) -> None: self._switch_to("logs")
    def action_goto_feature_7(self) -> None: self._switch_to("tunnel")
    def action_goto_feature_8(self) -> None: self._switch_to("scheduler")

    def action_show_help(self) -> None:
        self.app.push_screen(HelpScreen(self._current_feature))

    def action_refresh_pane(self) -> None:
        self._check_server_state()

    def action_toggle_server(self) -> None:
        self.run_worker(self._toggle_server(), exclusive=True, name="server-toggle")

    async def _toggle_server(self) -> None:
        state = await asyncio.to_thread(docker.get_container_state, app_config.minecraft_container)
        if state == ContainerState.RUNNING:
            self.app.notify("Deteniendo servidor...", severity="warning")
            await asyncio.to_thread(docker.stop)
        else:
            self.app.notify("Iniciando servidor...", severity="information")
            await asyncio.to_thread(docker.start)
        await self._async_check_state()

    def action_request_quit(self) -> None:
        self.app.exit()

    # ── Message handlers (broadcast to features that care) ──────────────────

    def on_stats_updated(self, message: StatsUpdated) -> None:
        # Monitoring pane subscribes directly; pass through
        try:
            mon = self.query_one("#monitoring")
            mon.post_message(message)
        except Exception:
            pass
        try:
            dash = self.query_one("#dashboard")
            dash.post_message(message)
        except Exception:
            pass

    def on_system_stats_updated(self, message: SystemStatsUpdated) -> None:
        try:
            mon = self.query_one("#monitoring")
            mon.post_message(message)
        except Exception:
            pass

    def on_log_line(self, message: LogLine) -> None:
        try:
            console = self.query_one("#console")
            console.post_message(message)
        except Exception:
            pass
        try:
            logs = self.query_one("#logs")
            logs.post_message(message)
        except Exception:
            pass
        try:
            event_log = self.query_one("#event_log")
            event_log.post_message(message)
        except Exception:
            pass

    def on_tunnel_link_updated(self, message: TunnelLinkUpdated) -> None:
        try:
            dash = self.query_one("#dashboard")
            dash.post_message(message)
        except Exception:
            pass
        try:
            tunnel = self.query_one("#tunnel")
            tunnel.post_message(message)
        except Exception:
            pass

    def on_alert_triggered(self, message: AlertTriggered) -> None:
        self.app.notify(
            f"[{message.severity.upper()}] {message.rule_name}: {message.metric} = {message.value:.1f}",
            severity="warning" if message.severity == "warning" else "error",
            timeout=8,
        )
