from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, Input, Select, Switch, DataTable, Static
from textual.containers import Horizontal, Vertical

from mc_manager.core.config import docker, app_config
from mc_manager.features.scheduler.task_engine import engine, ScheduledTask


_TASK_TYPES = [
    ("Reiniciar servidor", "restart"),
    ("Crear backup", "backup"),
    ("Ejecutar comando RCON", "command"),
    ("Anunciar en chat", "announce"),
]

_SCHEDULE_TYPES = [
    ("Cada hora", "interval@1h"),
    ("Cada 6 horas", "interval@6h"),
    ("Cada 12 horas", "interval@12h"),
    ("Cada 24 horas", "interval@24h"),
    ("Cada 30 minutos", "interval@30m"),
    ("Diario a las 4:00am", "daily@04:00"),
    ("Diario a las 6:00am", "daily@06:00"),
    ("Diario a las 3:00am", "daily@03:00"),
]


class SchedulerPane(Widget):

    DEFAULT_CSS = """
    SchedulerPane {
        width: 100%;
        height: 100%;
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
        padding: 1 2;
    }
    .sched-left {
        height: 100%;
    }
    .sched-right {
        height: 100%;
        border: solid $primary-darken-2;
        padding: 1;
    }
    .sched-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    DataTable {
        height: 1fr;
    }
    .sched-btn-row {
        layout: horizontal;
        height: 3;
        margin-top: 1;
        align: left middle;
    }
    .sched-btn-row Button {
        margin-right: 1;
    }
    .sched-field-row {
        layout: horizontal;
        height: 3;
        align: left middle;
        margin-bottom: 1;
    }
    .sched-field-row Label {
        width: 18;
        color: $text-muted;
    }
    .sched-field-row Input, .sched-field-row Select {
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(classes="sched-left"):
            yield Label("⏰  Tareas Programadas", classes="sched-title")
            yield DataTable(id="sched-table")
            with Horizontal(classes="sched-btn-row"):
                yield Button("🔄 Actualizar", id="sched-refresh", variant="primary")
                yield Button("▶ Activar", id="sched-enable", variant="success")
                yield Button("⏸ Desactivar", id="sched-disable", variant="warning")
                yield Button("🗑 Eliminar", id="sched-delete", variant="error")

            yield Label("\n📋  Plantillas rápidas:", classes="sched-title")
            with Horizontal(classes="sched-btn-row"):
                yield Button("+ Restart diario", id="tmpl-restart", variant="default")
                yield Button("+ Backup cada 6h", id="tmpl-backup", variant="default")
            with Horizontal(classes="sched-btn-row"):
                yield Button("+ Aviso cada 24h", id="tmpl-announce", variant="default")

        with Vertical(classes="sched-right"):
            yield Label("➕  Nueva Tarea", classes="sched-title")

            with Horizontal(classes="sched-field-row"):
                yield Label("Nombre:")
                yield Input(placeholder="Mi tarea", id="sched-name")

            with Horizontal(classes="sched-field-row"):
                yield Label("Tipo:")
                yield Select(options=_TASK_TYPES, value="restart", id="sched-type", allow_blank=False)

            with Horizontal(classes="sched-field-row"):
                yield Label("Horario:")
                yield Select(options=_SCHEDULE_TYPES, value="daily@04:00", id="sched-schedule", allow_blank=False)

            with Horizontal(classes="sched-field-row"):
                yield Label("Parámetro extra:")
                yield Input(placeholder="ej: 'say Server restart in 5min!'", id="sched-extra")

            with Horizontal(classes="sched-field-row"):
                yield Label("Habilitado:")
                yield Switch(value=True, id="sched-enabled")

            with Horizontal(classes="sched-btn-row"):
                yield Button("➕ Agregar Tarea", id="sched-add", variant="success")

            yield Static("", id="sched-status")

    def on_mount(self) -> None:
        self._setup_table()
        self._setup_callbacks()
        engine.start()
        self._reload_table()
        self.set_interval(30.0, self._reload_table)

    def _setup_table(self) -> None:
        try:
            tbl = self.query_one("#sched-table", DataTable)
            tbl.add_columns("Nombre", "Tipo", "Horario", "Última ejecución", "Activa")
        except Exception:
            pass

    def _setup_callbacks(self) -> None:
        engine.register_callback("restart", self._cb_restart)
        engine.register_callback("backup", self._cb_backup)
        engine.register_callback("announce", self._cb_announce)
        engine.register_callback("command", self._cb_command)

    def _cb_restart(self, task: ScheduledTask) -> None:
        self.app.notify(f"Tarea: reiniciando servidor ({task.name})", severity="warning")
        docker.restart(app_config.minecraft_container)

    def _cb_backup(self, task: ScheduledTask) -> None:
        from mc_manager.features.backups.backup_engine import create_backup
        self.app.notify(f"Tarea: creando backup automático ({task.name})", severity="information")
        create_backup(app_config.data_dir, app_config.backup_dir, name="auto")

    def _cb_announce(self, task: ScheduledTask) -> None:
        msg = task.extra.get("message", "Mensaje automático")
        try:
            from mc_manager.features.players.rcon_client import RconClient
            rcon = RconClient("localhost", app_config.rcon_port, app_config.rcon_password)
            rcon.send(f"say {msg}")
            rcon.disconnect()
        except Exception:
            pass

    def _cb_command(self, task: ScheduledTask) -> None:
        cmd = task.extra.get("command", "")
        if cmd:
            try:
                from mc_manager.features.players.rcon_client import RconClient
                rcon = RconClient("localhost", app_config.rcon_port, app_config.rcon_password)
                rcon.send(cmd)
                rcon.disconnect()
            except Exception:
                pass

    def _reload_table(self) -> None:
        try:
            tbl = self.query_one("#sched-table", DataTable)
            tbl.clear()
            for task in engine.tasks:
                last = task.last_run.strftime("%H:%M:%S") if task.last_run else "—"
                tbl.add_row(
                    task.name, task.task_type, task.schedule,
                    last, "✓" if task.enabled else "✗"
                )
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "sched-add":
            await self._add_task()
        elif bid == "sched-refresh":
            self._reload_table()
        elif bid == "sched-delete":
            await self._delete_selected()
        elif bid == "sched-enable":
            await self._toggle_selected(True)
        elif bid == "sched-disable":
            await self._toggle_selected(False)
        elif bid == "tmpl-restart":
            engine.add_task(ScheduledTask("Restart diario", "restart", "daily@04:00"))
            self._reload_table()
        elif bid == "tmpl-backup":
            engine.add_task(ScheduledTask("Backup 6h", "backup", "interval@6h"))
            self._reload_table()
        elif bid == "tmpl-announce":
            engine.add_task(ScheduledTask("Aviso diario", "announce", "daily@12:00",
                                         extra={"message": "El servidor lleva corriendo 24h!"}))
            self._reload_table()

    async def _add_task(self) -> None:
        try:
            name = self.query_one("#sched-name", Input).value.strip()
            if not name:
                self.app.notify("Escribe un nombre para la tarea", severity="warning")
                return
            task_type = str(self.query_one("#sched-type", Select).value)
            schedule = str(self.query_one("#sched-schedule", Select).value)
            extra_val = self.query_one("#sched-extra", Input).value.strip()
            enabled = self.query_one("#sched-enabled", Switch).value

            extra = {}
            if task_type == "announce":
                extra["message"] = extra_val or "Mensaje automático"
            elif task_type == "command":
                extra["command"] = extra_val

            task = ScheduledTask(name=name, task_type=task_type, schedule=schedule, enabled=enabled, extra=extra)
            engine.add_task(task)
            self._reload_table()
            self.query_one("#sched-status", Static).update(f"✓ Tarea '{name}' agregada")
        except Exception as e:
            self.app.notify(str(e), severity="error")

    async def _delete_selected(self) -> None:
        try:
            tbl = self.query_one("#sched-table", DataTable)
            if tbl.cursor_row is None:
                return
            row = tbl.get_row_at(tbl.cursor_row)
            name = str(row[0])
            engine.remove_task(name)
            self._reload_table()
        except Exception:
            pass

    async def _toggle_selected(self, enabled: bool) -> None:
        try:
            tbl = self.query_one("#sched-table", DataTable)
            if tbl.cursor_row is None:
                return
            row = tbl.get_row_at(tbl.cursor_row)
            name = str(row[0])
            for task in engine.tasks:
                if task.name == name:
                    task.enabled = enabled
                    break
            self._reload_table()
        except Exception:
            pass
