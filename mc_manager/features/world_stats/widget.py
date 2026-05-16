from __future__ import annotations

import os
import struct
import gzip
from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, DataTable, Static
from textual.containers import Horizontal, Vertical

from mc_manager.core.config import app_config
from mc_manager.utils.formatting import bytes_to_human


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
        # level.dat is gzipped NBT
        with gzip.open(str(level_dat), "rb") as f:
            data = f.read(8192)  # Read enough to find the seed

        # Search for "RandomSeed" or "WorldGenSettings" seed pattern
        # In NBT, seeds are 64-bit long. We do a pattern search.
        seed_marker = b"RandomSeed"
        idx = data.find(seed_marker)
        if idx != -1:
            # After the string length (2 bytes) + string + TAG_Long type
            # The seed value is a big-endian 8-byte int right after
            offset = idx + len(seed_marker)
            if offset + 8 <= len(data):
                seed_val = struct.unpack(">q", data[offset:offset + 8])[0]
                return str(seed_val)
    except Exception:
        pass
    return "—"


def _open_folder(path: Path) -> None:
    import subprocess
    import sys
    import platform
    if platform.system() == "Windows":
        os.startfile(str(path))
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


class WorldStatsPane(Widget):

    DEFAULT_CSS = """
    WorldStatsPane {
        width: 100%;
        height: 100%;
        padding: 1 2;
        layout: vertical;
    }
    .world-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .world-card {
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
    }
    DataTable {
        height: 12;
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
    """

    def compose(self) -> ComposeResult:
        yield Label("🌍  Estadísticas del Mundo Minecraft", classes="world-title")

        with Vertical(classes="world-card"):
            yield Label("📊  Dimensiones:", classes="world-title")
            yield DataTable(id="world-dim-table")

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
            yield Button("🔄 Actualizar stats", id="world-refresh", variant="primary")
            yield Button("📂 Abrir carpeta", id="world-open-folder", variant="default")

    def on_mount(self) -> None:
        self._setup_table()
        self.run_worker(self._load_stats(), exclusive=False)

    def _setup_table(self) -> None:
        try:
            tbl = self.query_one("#world-dim-table", DataTable)
            tbl.add_columns("Dimensión", "Tamaño en disco", "Archivos .mca", "Chunks aprox.")
        except Exception:
            pass

    async def _load_stats(self) -> None:
        data_dir = app_config.data_dir
        if not data_dir.exists():
            self.app.notify("El directorio datos_mc/ no existe aún (inicia el servidor primero)", severity="warning")
            return

        # Find world name from server.properties or use "world"
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
                region_dir = dim_path / "region"
                mca_count = _count_region_files(region_dir)
                chunks = mca_count * 1024  # each .mca has up to 1024 chunks
                tbl.add_row(
                    dim_name,
                    bytes_to_human(size) if size > 0 else "—",
                    str(mca_count) if mca_count > 0 else "—",
                    f"~{chunks:,}" if chunks > 0 else "—"
                )
        except Exception:
            pass

        # Seed
        seed = _read_seed_from_level_dat(world_dir / "level.dat")

        try:
            self.query_one("#world-name-val", Label).update(world_name)
            self.query_one("#world-seed-val", Label).update(seed)
            self.query_one("#world-total-val", Label).update(bytes_to_human(total_bytes))
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "world-refresh":
            self.run_worker(self._load_stats(), exclusive=False)
        elif event.button.id == "world-open-folder":
            try:
                _open_folder(app_config.data_dir)
            except Exception as e:
                self.app.notify(str(e), severity="error")
