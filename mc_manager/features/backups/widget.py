from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, Input, DataTable, ProgressBar, Switch, Static
from textual.containers import Horizontal, Vertical

from mc_manager.core.config import app_config
from mc_manager.core.events import BackupCompleted
from mc_manager.features.backups.backup_engine import (
    list_backups, create_backup, restore_backup, delete_backup, BackupInfo
)
from mc_manager.utils.formatting import bytes_to_human


class BackupsPane(Widget):

    DEFAULT_CSS = """
    BackupsPane {
        width: 100%;
        height: 100%;
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
        padding: 1 2;
    }
    .backups-left {
        height: 100%;
    }
    .backups-right {
        height: 100%;
        border: solid $primary-darken-2;
        padding: 1;
    }
    .backups-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    DataTable {
        height: 1fr;
    }
    .backup-btn-row {
        layout: horizontal;
        height: 3;
        margin-top: 1;
        align: left middle;
    }
    .backup-btn-row Button {
        margin-right: 1;
    }
    .backup-opt-row {
        layout: horizontal;
        height: 3;
        align: left middle;
        margin-bottom: 1;
    }
    .backup-opt-row Label {
        width: 18;
        color: $text-muted;
    }
    #backup-progress {
        margin-top: 1;
        height: 2;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._backups: list[BackupInfo] = []
        self._max_backups: int = 0  # 0 = sin límite

    def compose(self) -> ComposeResult:
        with Vertical(classes="backups-left"):
            yield Label("💾  Backups Disponibles", classes="backups-title")
            yield DataTable(id="backups-table")
            with Horizontal(classes="backup-btn-row"):
                yield Button("🔄 Actualizar", id="bk-refresh", variant="primary")
                yield Button("♻ Restaurar", id="bk-restore", variant="warning")
                yield Button("🗑 Eliminar", id="bk-delete", variant="error")

        with Vertical(classes="backups-right"):
            yield Label("➕  Crear Backup", classes="backups-title")

            with Horizontal(classes="backup-opt-row"):
                yield Label("Nombre del backup:")
                yield Input(value="world", id="bk-name", placeholder="mundo")

            with Horizontal(classes="backup-opt-row"):
                yield Label("Comprimir (.tar.gz):")
                yield Switch(value=True, id="bk-compress")

            with Horizontal(classes="backup-opt-row"):
                yield Label("Retención máx. (0=∞):")
                yield Input(value="0", id="bk-retention", placeholder="0")

            with Horizontal(classes="backup-btn-row"):
                yield Button("💾 Crear Backup Ahora", id="bk-create", variant="success")

            yield Static("", id="backup-status")
            yield ProgressBar(total=100, show_eta=False, show_percentage=True, id="backup-progress")

            yield Label("\n📁  Directorio de backups:", classes="backups-title")
            yield Static(str(app_config.backup_dir), id="backup-dir-label")

    def on_mount(self) -> None:
        self._setup_table()
        self.run_worker(self._load_backups(), exclusive=False)

    def _setup_table(self) -> None:
        try:
            tbl = self.query_one("#backups-table", DataTable)
            tbl.add_columns("Nombre", "Tamaño", "Fecha", "Tipo")
        except Exception:
            pass

    async def _load_backups(self) -> None:
        self._backups = list_backups(app_config.backup_dir)
        try:
            tbl = self.query_one("#backups-table", DataTable)
            tbl.clear()
            if not self._backups:
                tbl.add_row("(sin backups)", "—", "—", "—")
            else:
                for bk in self._backups:
                    tbl.add_row(
                        bk.name,
                        bytes_to_human(bk.size_bytes),
                        bk.created_at.strftime("%Y-%m-%d %H:%M"),
                        ".tar.gz" if bk.compressed else ".tar"
                    )
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "bk-refresh":
            await self._load_backups()
        elif bid == "bk-create":
            await self._create_backup()
        elif bid == "bk-restore":
            await self._restore_selected()
        elif bid == "bk-delete":
            await self._delete_selected()

    def _enforce_retention(self) -> None:
        if self._max_backups <= 0:
            return
        backups = list_backups(app_config.backup_dir)
        if len(backups) <= self._max_backups:
            return
        to_delete = backups[self._max_backups:]
        deleted = 0
        for bk in to_delete:
            ok, _ = delete_backup(bk.path)
            if ok:
                deleted += 1
        if deleted:
            self.app.notify(
                f"Retención: {deleted} backup(s) antiguo(s) eliminado(s)",
                severity="information",
            )

    async def _create_backup(self) -> None:
        try:
            btn = self.query_one("#bk-create", Button)
            btn.disabled = True
            btn.label = "Creando..."

            name = self.query_one("#bk-name", Input).value.strip() or "world"
            compress = self.query_one("#bk-compress", Switch).value
            try:
                self._max_backups = int(self.query_one("#bk-retention", Input).value or "0")
            except ValueError:
                self._max_backups = 0

            self.query_one("#backup-status", Static).update("Enviando save-off al servidor...")

            # Try save-off via rcon (non-critical)
            try:
                from mc_manager.features.players.rcon_client import RconClient
                rcon = RconClient("localhost", app_config.rcon_port, app_config.rcon_password)
                rcon.send("save-off")
                rcon.send("save-all")
                rcon.disconnect()
            except Exception:
                pass

            self.query_one("#backup-status", Static).update("Comprimiendo mundo...")
            self.run_worker(self._do_backup(name, compress), exclusive=True)
        except Exception as e:
            self.app.notify(str(e), severity="error")

    async def _do_backup(self, name: str, compress: bool) -> None:
        path, err = create_backup(
            source_dir=app_config.data_dir,
            backup_dir=app_config.backup_dir,
            name=name,
            compress=compress,
        )

        # Re-enable save
        try:
            from mc_manager.features.players.rcon_client import RconClient
            rcon = RconClient("localhost", app_config.rcon_port, app_config.rcon_password)
            rcon.send("save-on")
            rcon.disconnect()
        except Exception:
            pass

        success = not bool(err)
        self.app.post_message(BackupCompleted(path=path, success=success, error=err))

        try:
            btn = self.query_one("#bk-create", Button)
            btn.disabled = False
            btn.label = "💾 Crear Backup Ahora"
            status = self.query_one("#backup-status", Static)
            if success:
                status.update(f"✓ Backup creado: {path.name} ({bytes_to_human(path.stat().st_size)})")
            else:
                status.update(f"✗ Error: {err}")
        except Exception:
            pass

        await self._load_backups()
        self._enforce_retention()

    async def _restore_selected(self) -> None:
        try:
            tbl = self.query_one("#backups-table", DataTable)
            if tbl.cursor_row is None or not self._backups:
                self.app.notify("Selecciona un backup primero", severity="warning")
                return
            idx = tbl.cursor_row
            if idx >= len(self._backups):
                return
            bk = self._backups[idx]
            self.app.notify(f"Restaurando {bk.name}...", severity="warning")
            self.run_worker(self._do_restore(bk.path), exclusive=True)
        except Exception as e:
            self.app.notify(str(e), severity="error")

    async def _do_restore(self, archive: Path) -> None:
        success, err = restore_backup(archive, app_config.data_dir.parent)
        if success:
            self.app.notify("Backup restaurado. Reinicia el servidor.", severity="information")
        else:
            self.app.notify(f"Error restaurando: {err}", severity="error")

    async def _delete_selected(self) -> None:
        try:
            tbl = self.query_one("#backups-table", DataTable)
            if tbl.cursor_row is None or not self._backups:
                self.app.notify("Selecciona un backup primero", severity="warning")
                return
            idx = tbl.cursor_row
            if idx >= len(self._backups):
                return
            bk = self._backups[idx]
            success, err = delete_backup(bk.path)
            if success:
                self.app.notify(f"Eliminado: {bk.name}", severity="warning")
                await self._load_backups()
            else:
                self.app.notify(f"Error: {err}", severity="error")
        except Exception as e:
            self.app.notify(str(e), severity="error")
