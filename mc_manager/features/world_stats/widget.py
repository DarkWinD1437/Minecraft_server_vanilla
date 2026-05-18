from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import struct
import gzip
import urllib.request
from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, DataTable, Static, Input
from textual.containers import Horizontal, Vertical, ScrollableContainer

from mc_manager.core.config import app_config, docker
from mc_manager.utils.formatting import bytes_to_human
from mc_manager.features.event_log import event_store


def _dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except OSError:
                pass
    return total


def _count_region_files(region_dir: Path) -> int:
    if not region_dir.exists():
        return 0
    return sum(1 for f in region_dir.glob("*.mca"))


def _read_seed_from_level_dat(level_dat: Path) -> str:
    """Extract world seed from level.dat (NBT). Minimal implementation."""
    if not level_dat.exists():
        return "—"
    try:
        with gzip.open(str(level_dat), "rb") as f:
            data = f.read(8192)
        seed_marker = b"RandomSeed"
        idx = data.find(seed_marker)
        if idx != -1:
            offset = idx + len(seed_marker)
            if offset + 8 <= len(data):
                seed_val = struct.unpack(">q", data[offset:offset + 8])[0]
                return str(seed_val)
    except Exception:
        pass
    return "—"


def _open_folder(path: Path) -> None:
    import subprocess
    import platform
    if platform.system() == "Windows":
        os.startfile(str(path))
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def _get_installed_chunky_version() -> str | None:
    """Extrae la versión del JAR de Chunky instalado en plugins/."""
    plugins_dir = app_config.data_dir / "plugins"
    if not plugins_dir.exists():
        return None
    pattern = re.compile(r"chunky[^/\\]*?[_-]?(\d+\.\d+[\.\d]*)", re.IGNORECASE)
    for p in plugins_dir.glob("*.jar"):
        m = pattern.search(p.name)
        if m:
            return m.group(1)
    return None


def _fetch_latest_chunky_version() -> str:
    """(bloqueante) Consulta Modrinth API para la versión más reciente de Chunky (Paper)."""
    import urllib.parse
    loaders = urllib.parse.quote('["paper","bukkit","spigot"]')
    url = f"https://api.modrinth.com/v2/project/fALzjamp/version?loaders={loaders}"
    req = urllib.request.Request(url, headers={"User-Agent": "MC-Manager/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        versions = json.loads(resp.read())
    if versions:
        return versions[0].get("version_number", "")
    return ""


def _fetch_chunky_download_url() -> tuple[str, str]:
    """(bloqueante) Retorna (download_url, filename) del JAR de Chunky desde Modrinth."""
    import urllib.parse
    loaders = urllib.parse.quote('["paper","bukkit","spigot"]')
    url = f"https://api.modrinth.com/v2/project/fALzjamp/version?loaders={loaders}"
    req = urllib.request.Request(url, headers={"User-Agent": "MC-Manager/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        versions = json.loads(resp.read())
    if versions:
        for f in versions[0].get("files", []):
            if f["filename"].endswith(".jar"):
                return f["url"], f["filename"]
    raise ValueError("No se encontró JAR de Chunky en Modrinth")


class WorldStatsPane(Widget):

    DEFAULT_CSS = """
    WorldStatsPane {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    #world-scroll {
        width: 100%;
        height: 1fr;
        padding: 1 2;
    }
    .world-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .world-card {
        height: auto;
        border: solid $primary-darken-2;
        background: $panel;
        padding: 1;
        margin-bottom: 1;
    }
    .world-btn-row {
        layout: horizontal;
        height: 3;
        margin-top: 1;
        align: left middle;
    }
    .world-btn-row Button {
        margin-right: 1;
        min-width: 18;
    }
    DataTable {
        height: 8;
    }
    .world-info-row {
        layout: horizontal;
        height: 2;
        align: left middle;
        margin-bottom: 0;
    }
    .world-info-label {
        width: 20;
        color: $text-muted;
    }
    .world-info-value {
        color: $accent;
    }
    .world-warn {
        color: $warning;
        margin-top: 1;
    }
    .world-hint {
        color: $text-muted;
        margin-bottom: 1;
    }
    .chunky-radius-row {
        layout: horizontal;
        height: 3;
        align: left middle;
        margin-bottom: 1;
    }
    .chunky-radius-row Button {
        margin-right: 1;
        min-width: 8;
    }
    .chunky-radius-row Input {
        width: 18;
        margin-right: 1;
    }
    .chunky-action-row {
        layout: horizontal;
        height: 3;
        align: left middle;
        margin-top: 1;
    }
    .chunky-action-row Button {
        margin-right: 1;
        min-width: 18;
    }
    #chunky-version-label {
        color: $text-muted;
        margin-top: 1;
    }
    .deaths-epoch-row {
        layout: horizontal;
        height: 2;
        align: left middle;
        margin-bottom: 1;
    }
    .deaths-epoch-row Label {
        color: $text-muted;
        margin-right: 1;
    }
    .deaths-epoch-row Static {
        color: $accent;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._chunky_radius: int = 5000

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="world-scroll"):
            yield Label("🌍  Estadísticas del Mundo Minecraft", classes="world-title")

            # ── Dimensiones ─────────────────────────────────────────────────
            with Vertical(classes="world-card"):
                yield Label("📊  Dimensiones:", classes="world-title")
                yield DataTable(id="world-dim-table")

            # ── Información general ──────────────────────────────────────────
            with Vertical(classes="world-card"):
                yield Label("ℹ️  Información General:", classes="world-title")
                with Horizontal(classes="world-info-row"):
                    yield Label("Nombre del mundo:", classes="world-info-label")
                    yield Label("—", id="world-name-val", classes="world-info-value")
                with Horizontal(classes="world-info-row"):
                    yield Label("Semilla:", classes="world-info-label")
                    yield Label("—", id="world-seed-val", classes="world-info-value")
                with Horizontal(classes="world-info-row"):
                    yield Label("Tamaño total:", classes="world-info-label")
                    yield Label("—", id="world-total-val", classes="world-info-value")
                with Horizontal(classes="world-info-row"):
                    yield Label("Ruta de datos:", classes="world-info-label")
                    yield Static(str(app_config.data_dir), id="world-path-val")
                with Horizontal(classes="world-btn-row"):
                    yield Button("🔄 Actualizar", id="world-refresh", variant="primary")
                    yield Button("📂 Abrir carpeta", id="world-open-folder", variant="default")

            # ── Acciones del mundo ───────────────────────────────────────────
            with Vertical(classes="world-card"):
                yield Label("⚙️  Acciones del Mundo:", classes="world-title")
                yield Label(
                    "Reiniciar el servidor recarga el mundo sin perder ningún dato.",
                    classes="world-hint",
                )
                with Horizontal(classes="world-btn-row"):
                    yield Button("↺ Reiniciar servidor", id="world-restart-srv", variant="warning")
                    yield Button("🌱 Nuevo Mundo", id="world-new-world", variant="error")
                yield Label(
                    "⚠  'Nuevo Mundo' crea un backup automático, luego elimina el mundo actual.",
                    classes="world-warn",
                )

            # ── Pre-generación con Chunky ────────────────────────────────────
            with Vertical(classes="world-card"):
                yield Label("⛏  Pre-generación con Chunky:", classes="world-title")
                yield Label(
                    "Selecciona el radio (en bloques) desde el spawn para pre-generar:",
                    classes="world-hint",
                )
                with Horizontal(classes="chunky-radius-row"):
                    yield Button("2,500", id="chunky-r-2500", variant="default")
                    yield Button("5,000", id="chunky-r-5000", variant="default")
                    yield Button("7,500", id="chunky-r-7500", variant="default")
                    yield Button("10,000", id="chunky-r-10000", variant="default")
                    yield Input(placeholder="Radio manual (ej: 3000)", id="chunky-custom-input")
                with Horizontal(classes="chunky-action-row"):
                    yield Button("▶ Iniciar pre-gen", id="chunky-start", variant="success")
                    yield Button("⏹ Cancelar", id="chunky-cancel", variant="default")
                    yield Button("⬇ Actualizar Chunky", id="chunky-update", variant="primary")
                yield Label("Chunky: comprobando...", id="chunky-version-label")

            # ── Muertes por jugador (época actual) ──────────────────────────
            with Vertical(classes="world-card"):
                yield Label("💀  Muertes este mundo (por jugador):", classes="world-title")
                with Horizontal(classes="deaths-epoch-row"):
                    yield Label("Época actual:")
                    yield Static("—", id="deaths-epoch-val")
                yield DataTable(id="deaths-table")
                with Horizontal(classes="world-btn-row"):
                    yield Button("🔄 Actualizar muertes", id="deaths-refresh", variant="primary")
                yield Label(
                    "Nota: El dinero (EssentialsX) y los ítems (CoreProtect) se rastrean desde sus respectivos plugins.",
                    classes="world-hint",
                )

    def on_mount(self) -> None:
        # Ensure event_store DB is ready, independientemente de si EventLogPane fue visitado
        event_store.init(app_config.logs_dir / "events.db")
        self._setup_tables()
        self.run_worker(self._load_stats(), exclusive=False)
        self.run_worker(self._check_chunky_version(), exclusive=False)
        self._load_deaths()
        self.set_interval(30.0, self._load_deaths)

    def _setup_tables(self) -> None:
        try:
            tbl = self.query_one("#world-dim-table", DataTable)
            tbl.add_columns("Dimensión", "Tamaño en disco", "Archivos .mca", "Chunks aprox.")
        except Exception:
            pass
        try:
            dtbl = self.query_one("#deaths-table", DataTable)
            dtbl.add_columns("Jugador", "Muertes", "Última muerte")
        except Exception:
            pass

    # ── Stats del mundo ──────────────────────────────────────────────────────

    async def _load_stats(self) -> None:
        data_dir = app_config.data_dir
        if not data_dir.exists():
            self.app.notify(
                "El directorio datos_mc/ no existe aún (inicia el servidor primero)",
                severity="warning",
            )
            return

        world_name = "world"
        try:
            from mc_manager.features.settings.properties_parser import read_properties
            props = read_properties(app_config.server_properties)
            world_name = props.get("level-name", "world")
        except Exception:
            pass

        world_dir = data_dir / world_name
        dimensions = [
            (world_name, world_dir),
            (f"{world_name}_nether", data_dir / f"{world_name}_nether"),
            (f"{world_name}_the_end", data_dir / f"{world_name}_the_end"),
        ]

        try:
            tbl = self.query_one("#world-dim-table", DataTable)
            tbl.clear()
            total_bytes = 0
            for dim_name, dim_path in dimensions:
                size = _dir_size(dim_path)
                total_bytes += size
                mca_count = _count_region_files(dim_path / "region")
                chunks = mca_count * 1024
                tbl.add_row(
                    dim_name,
                    bytes_to_human(size) if size > 0 else "—",
                    str(mca_count) if mca_count > 0 else "—",
                    f"~{chunks:,}" if chunks > 0 else "—",
                )
        except Exception:
            pass

        seed = _read_seed_from_level_dat(world_dir / "level.dat")
        try:
            self.query_one("#world-name-val", Label).update(world_name)
            self.query_one("#world-seed-val", Label).update(seed)
            self.query_one("#world-total-val", Label).update(bytes_to_human(total_bytes))
        except Exception:
            pass

    # ── Chunky version ───────────────────────────────────────────────────────

    async def _check_chunky_version(self) -> None:
        installed = _get_installed_chunky_version()
        try:
            latest = await asyncio.to_thread(_fetch_latest_chunky_version)
        except Exception:
            latest = None

        try:
            lbl = self.query_one("#chunky-version-label", Label)
            if not installed:
                lbl.update("Chunky: no instalado")
            elif latest and latest != installed:
                lbl.update(
                    f"Chunky: v{installed} — [yellow]actualización disponible: v{latest}[/]"
                )
            else:
                lbl.update(f"Chunky: v{installed} — [green]actualizado[/]")

            # Ocultar botón de actualización si no hay versión nueva
            try:
                btn = self.query_one("#chunky-update", Button)
                if not latest or latest == installed:
                    btn.display = False
            except Exception:
                pass
        except Exception:
            pass

    # ── Estadísticas de muertes ──────────────────────────────────────────────

    def _load_deaths(self) -> None:
        try:
            epoch = event_store.get_current_epoch()
            self.query_one("#deaths-epoch-val", Static).update(f"#{epoch}")
            stats = event_store.query_player_deaths(epoch)
            dtbl = self.query_one("#deaths-table", DataTable)
            dtbl.clear()
            if not stats:
                dtbl.add_row("(sin muertes registradas aún)", "—", "—")
            else:
                for s in stats:
                    dtbl.add_row(s.player, str(s.count), s.last_death_at)
        except Exception:
            pass

    # ── Acciones del mundo ───────────────────────────────────────────────────

    async def _do_server_restart(self) -> None:
        self.app.notify("Reiniciando servidor...", severity="warning", timeout=5)
        out, err = await asyncio.to_thread(docker.restart, app_config.minecraft_container)
        if err and not out:
            self.app.notify(f"Error al reiniciar: {err}", severity="error")
        else:
            self.app.notify("Servidor reiniciado correctamente.", severity="information")

    async def _do_new_world(self) -> None:
        data_dir = app_config.data_dir
        world_name = "world"
        try:
            from mc_manager.features.settings.properties_parser import read_properties
            props = read_properties(app_config.server_properties)
            world_name = props.get("level-name", "world")
        except Exception:
            pass

        world_dirs = [
            data_dir / world_name,
            data_dir / f"{world_name}_nether",
            data_dir / f"{world_name}_the_end",
        ]

        self.app.notify("Creando backup antes de eliminar el mundo...", severity="warning", timeout=8)

        # 1. Backup
        try:
            from mc_manager.features.backups.backup_engine import create_backup
            backup_dir = app_config.compose_dir / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(
                create_backup, data_dir, backup_dir, "pre-nuevo-mundo", True
            )
        except Exception as e:
            self.app.notify(f"Backup falló: {e}. Abortando nuevo mundo.", severity="error")
            return

        # 2. Stop server
        self.app.notify("Deteniendo servidor...", severity="warning", timeout=5)
        await asyncio.to_thread(docker.stop, app_config.minecraft_container)

        # 3. Delete world directories
        for d in world_dirs:
            if d.exists():
                try:
                    await asyncio.to_thread(shutil.rmtree, str(d))
                except Exception as e:
                    self.app.notify(f"Error eliminando {d.name}: {e}", severity="error")

        # 4. Start server (Paper regenera el mundo automáticamente)
        self.app.notify("Iniciando servidor con mundo nuevo...", severity="information", timeout=8)
        await asyncio.to_thread(docker.start)

        # 5. Registrar nueva época
        epoch_id = event_store.create_world_epoch(seed=None, notes="Mundo regenerado manualmente")
        self.app.notify(
            f"Nuevo mundo creado (época #{epoch_id}). Backup guardado.",
            severity="information",
            timeout=10,
        )

        # Recargar stats
        self.run_worker(self._load_stats(), exclusive=False)
        self._load_deaths()

    # ── Chunky acciones ──────────────────────────────────────────────────────

    async def _do_chunky_start(self) -> None:
        radius = self._chunky_radius
        from mc_manager.features.players.rcon_client import RconClient
        try:
            rcon = RconClient("localhost", app_config.rcon_port, app_config.rcon_password)
            rcon.send(f"chunky world world")
            rcon.send(f"chunky radius {radius}")
            rcon.send("chunky start")
            rcon.disconnect()
            self.app.notify(
                f"Pre-generación iniciada: radio {radius:,} bloques. Revisa la Consola para el progreso.",
                severity="information",
                timeout=10,
            )
        except Exception as e:
            self.app.notify(f"Error RCON: {e}", severity="error")

    async def _do_chunky_cancel(self) -> None:
        from mc_manager.features.players.rcon_client import RconClient
        try:
            rcon = RconClient("localhost", app_config.rcon_port, app_config.rcon_password)
            rcon.send("chunky cancel")
            rcon.disconnect()
            self.app.notify("Pre-generación cancelada.", severity="warning")
        except Exception as e:
            self.app.notify(f"Error RCON: {e}", severity="error")

    async def _do_chunky_update(self) -> None:
        self.app.notify("Descargando última versión de Chunky...", severity="information")
        try:
            # Remove old Chunky jars
            plugins_dir = app_config.data_dir / "plugins"
            for p in plugins_dir.glob("*.jar"):
                if "chunky" in p.name.lower():
                    p.unlink(missing_ok=True)

            latest_ver = await asyncio.to_thread(_fetch_latest_chunky_version)
            dl_url, filename = await asyncio.to_thread(_fetch_chunky_download_url)
            dest = plugins_dir / filename
            await asyncio.to_thread(urllib.request.urlretrieve, dl_url, dest)
            self.app.notify(
                f"Chunky v{latest_ver} instalado. Reinicia el servidor para activarlo.",
                severity="information",
                timeout=8,
            )
            self.run_worker(self._check_chunky_version(), exclusive=False)
        except Exception as e:
            self.app.notify(f"Error actualizando Chunky: {e}", severity="error")

    # ── Event handlers ───────────────────────────────────────────────────────

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id

        if bid == "world-refresh":
            self.run_worker(self._load_stats(), exclusive=False)

        elif bid == "world-open-folder":
            try:
                _open_folder(app_config.data_dir)
            except Exception as e:
                self.app.notify(str(e), severity="error")

        elif bid == "world-restart-srv":
            from mc_manager.screens.confirm_modal import ConfirmModal
            def _on_confirm(confirmed: bool) -> None:
                if confirmed:
                    self.run_worker(self._do_server_restart(), exclusive=True)
            self.app.push_screen(
                ConfirmModal(
                    title="↺  Reiniciar Servidor",
                    body=(
                        "El servidor se reiniciará y los jugadores serán\n"
                        "desconectados momentáneamente.\n\n"
                        "El mundo, inventarios y todos los datos de jugadores\n"
                        "se conservarán completamente. No perderás nada."
                    ),
                    confirm_label="Reiniciar",
                    danger=False,
                ),
                _on_confirm,
            )

        elif bid == "world-new-world":
            from mc_manager.screens.confirm_modal import ConfirmModal
            def _on_new_world(confirmed: bool) -> None:
                if confirmed:
                    self.run_worker(self._do_new_world(), exclusive=True)
            self.app.push_screen(
                ConfirmModal(
                    title="🌱  Generar Nuevo Mundo",
                    body=(
                        "Se creará un backup automático del mundo actual.\n"
                        "Luego se eliminarán los directorios del mundo\n"
                        "(overworld, nether, end) y los inventarios de jugadores.\n\n"
                        "Todos comenzarán desde cero con el nuevo mapa.\n"
                        "Esta acción NO se puede deshacer (excepto por el backup)."
                    ),
                    confirm_label="Crear Nuevo Mundo",
                    danger=True,
                ),
                _on_new_world,
            )

        # Chunky radius presets
        elif bid == "chunky-r-2500":
            self._chunky_radius = 2500
            self.app.notify("Radio seleccionado: 2,500 bloques", severity="information", timeout=3)
        elif bid == "chunky-r-5000":
            self._chunky_radius = 5000
            self.app.notify("Radio seleccionado: 5,000 bloques", severity="information", timeout=3)
        elif bid == "chunky-r-7500":
            self._chunky_radius = 7500
            self.app.notify("Radio seleccionado: 7,500 bloques", severity="information", timeout=3)
        elif bid == "chunky-r-10000":
            self._chunky_radius = 10000
            self.app.notify("Radio seleccionado: 10,000 bloques", severity="information", timeout=3)

        elif bid == "chunky-start":
            # Si hay valor manual en el input, usarlo
            try:
                val = self.query_one("#chunky-custom-input", Input).value.strip()
                if val.isdigit():
                    self._chunky_radius = int(val)
            except Exception:
                pass
            self.run_worker(self._do_chunky_start(), exclusive=False)

        elif bid == "chunky-cancel":
            self.run_worker(self._do_chunky_cancel(), exclusive=False)

        elif bid == "chunky-update":
            self.run_worker(self._do_chunky_update(), exclusive=False)

        elif bid == "deaths-refresh":
            self._load_deaths()
