from __future__ import annotations

import json
from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, Input, DataTable, TabbedContent, TabPane
from textual.containers import Horizontal, Vertical

from mc_manager.core.config import docker, app_config
from mc_manager.features.players.rcon_client import RconClient


def _read_json_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


class PlayersPane(Widget):

    DEFAULT_CSS = """
    PlayersPane {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    .players-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .players-btn-row {
        layout: horizontal;
        height: 3;
        margin: 1 0;
        align: left middle;
    }
    .players-btn-row Button {
        margin-right: 1;
    }
    .players-add-row {
        layout: horizontal;
        height: 3;
        margin-top: 1;
        align: left middle;
    }
    .players-add-row Input {
        width: 24;
        margin-right: 1;
    }
    DataTable {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("👥  Gestión de Jugadores", classes="players-title")
        with TabbedContent():
            with TabPane("🟢 Online", id="tab-online"):
                yield DataTable(id="online-table")
                with Horizontal(classes="players-btn-row"):
                    yield Button("🔄 Actualizar", id="online-refresh", variant="primary")
                    yield Button("👢 Kick", id="online-kick", variant="warning")
                    yield Button("⛔ Banear", id="online-ban", variant="error")

            with TabPane("📋 Whitelist", id="tab-whitelist"):
                yield DataTable(id="wl-table")
                with Horizontal(classes="players-btn-row"):
                    yield Button("🔄 Actualizar", id="wl-refresh", variant="primary")
                    yield Button("➕ Agregar", id="wl-add", variant="success")
                    yield Button("➖ Quitar", id="wl-remove", variant="error")
                with Horizontal(classes="players-add-row"):
                    yield Input(placeholder="Nombre del jugador", id="wl-input")
                    yield Button("OK", id="wl-add-confirm", variant="success")

            with TabPane("⛔ Baneos", id="tab-bans"):
                yield DataTable(id="ban-table")
                with Horizontal(classes="players-btn-row"):
                    yield Button("🔄 Actualizar", id="ban-refresh", variant="primary")
                    yield Button("⛔ Banear", id="ban-add", variant="error")
                    yield Button("✅ Desbanear", id="ban-remove", variant="success")
                with Horizontal(classes="players-add-row"):
                    yield Input(placeholder="Nombre o IP del jugador", id="ban-input")
                    yield Button("OK", id="ban-add-confirm", variant="error")

            with TabPane("⭐ Operators", id="tab-ops"):
                yield DataTable(id="ops-table")
                with Horizontal(classes="players-btn-row"):
                    yield Button("🔄 Actualizar", id="ops-refresh", variant="primary")
                    yield Button("⭐ Dar OP", id="ops-add", variant="success")
                    yield Button("✖ Quitar OP", id="ops-remove", variant="error")
                with Horizontal(classes="players-add-row"):
                    yield Input(placeholder="Nombre del jugador", id="ops-input")
                    yield Button("OK", id="ops-add-confirm", variant="success")

    def on_mount(self) -> None:
        self._setup_tables()
        self.run_worker(self._load_all(), exclusive=False)

    def _setup_tables(self) -> None:
        try:
            self.query_one("#online-table", DataTable).add_columns("Jugador", "Info")
            self.query_one("#wl-table", DataTable).add_columns("Nombre", "UUID")
            self.query_one("#ban-table", DataTable).add_columns("Nombre/IP", "Razón", "Expira")
            self.query_one("#ops-table", DataTable).add_columns("Nombre", "Nivel", "UUID")
        except Exception:
            pass

    async def _load_all(self) -> None:
        await self._load_online()
        await self._load_whitelist()
        await self._load_bans()
        await self._load_ops()

    async def _load_online(self) -> None:
        try:
            tbl = self.query_one("#online-table", DataTable)
            tbl.clear()
            rcon = RconClient("localhost", app_config.rcon_port, app_config.rcon_password)
            response, err = rcon.send("list")
            rcon.disconnect()
            if response:
                players_part = response.split(":")[-1].strip() if ":" in response else ""
                names = [n.strip() for n in players_part.split(",") if n.strip()]
                if names:
                    for name in names:
                        tbl.add_row(name, "En línea")
                else:
                    tbl.add_row("(sin jugadores)", "—")
            else:
                tbl.add_row("RCON no disponible", err or "—")
        except Exception as e:
            try:
                self.query_one("#online-table", DataTable).add_row("Error", str(e)[:40])
            except Exception:
                pass

    async def _load_whitelist(self) -> None:
        try:
            tbl = self.query_one("#wl-table", DataTable)
            tbl.clear()
            data = _read_json_list(app_config.whitelist_json)
            for entry in data:
                tbl.add_row(entry.get("name", "?"), entry.get("uuid", "?"))
            if not data:
                tbl.add_row("(whitelist vacía)", "—")
        except Exception:
            pass

    async def _load_bans(self) -> None:
        try:
            tbl = self.query_one("#ban-table", DataTable)
            tbl.clear()
            data = _read_json_list(app_config.banned_players_json)
            for entry in data:
                tbl.add_row(
                    entry.get("name", "?"),
                    entry.get("reason", "Sin razón"),
                    entry.get("expires", "Permanente"),
                )
            if not data:
                tbl.add_row("(sin baneos)", "—", "—")
        except Exception:
            pass

    async def _load_ops(self) -> None:
        try:
            tbl = self.query_one("#ops-table", DataTable)
            tbl.clear()
            data = _read_json_list(app_config.ops_json)
            for entry in data:
                tbl.add_row(
                    entry.get("name", "?"),
                    str(entry.get("level", 4)),
                    entry.get("uuid", "?"),
                )
            if not data:
                tbl.add_row("(sin operators)", "—", "—")
        except Exception:
            pass

    async def _rcon(self, cmd: str) -> str:
        rcon = RconClient("localhost", app_config.rcon_port, app_config.rcon_password)
        resp, err = rcon.send(cmd)
        rcon.disconnect()
        return resp or err

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "online-refresh":
            await self._load_online()
        elif bid == "online-kick":
            await self._kick_selected()
        elif bid == "online-ban":
            await self._ban_online_selected()
        elif bid in ("wl-refresh", "wl-add"):
            await self._load_whitelist()
        elif bid == "wl-add-confirm":
            await self._wl_add()
        elif bid == "wl-remove":
            await self._wl_remove()
        elif bid in ("ban-refresh",):
            await self._load_bans()
        elif bid == "ban-add-confirm":
            await self._ban_add()
        elif bid == "ban-remove":
            await self._ban_remove()
        elif bid in ("ops-refresh",):
            await self._load_ops()
        elif bid == "ops-add-confirm":
            await self._op_add()
        elif bid == "ops-remove":
            await self._op_remove()

    async def _kick_selected(self) -> None:
        try:
            tbl = self.query_one("#online-table", DataTable)
            if tbl.cursor_row is None:
                return
            name = str(tbl.get_row_at(tbl.cursor_row)[0])
            result = await self._rcon(f"kick {name}")
            self.app.notify(result or f"Kickeado: {name}", severity="warning")
            await self._load_online()
        except Exception as e:
            self.app.notify(str(e), severity="error")

    async def _ban_online_selected(self) -> None:
        try:
            tbl = self.query_one("#online-table", DataTable)
            if tbl.cursor_row is None:
                return
            name = str(tbl.get_row_at(tbl.cursor_row)[0])
            result = await self._rcon(f"ban {name}")
            self.app.notify(result or f"Baneado: {name}", severity="warning")
            await self._load_online()
        except Exception as e:
            self.app.notify(str(e), severity="error")

    async def _wl_add(self) -> None:
        try:
            name = self.query_one("#wl-input", Input).value.strip()
            if not name:
                return
            result = await self._rcon(f"whitelist add {name}")
            self.app.notify(result or f"Agregado: {name}", severity="information")
            await self._load_whitelist()
        except Exception as e:
            self.app.notify(str(e), severity="error")

    async def _wl_remove(self) -> None:
        try:
            tbl = self.query_one("#wl-table", DataTable)
            if tbl.cursor_row is None:
                return
            name = str(tbl.get_row_at(tbl.cursor_row)[0])
            result = await self._rcon(f"whitelist remove {name}")
            self.app.notify(result or f"Quitado: {name}", severity="warning")
            await self._load_whitelist()
        except Exception as e:
            self.app.notify(str(e), severity="error")

    async def _ban_add(self) -> None:
        try:
            name = self.query_one("#ban-input", Input).value.strip()
            if not name:
                return
            result = await self._rcon(f"ban {name}")
            self.app.notify(result or f"Baneado: {name}", severity="warning")
            await self._load_bans()
        except Exception as e:
            self.app.notify(str(e), severity="error")

    async def _ban_remove(self) -> None:
        try:
            tbl = self.query_one("#ban-table", DataTable)
            if tbl.cursor_row is None:
                return
            name = str(tbl.get_row_at(tbl.cursor_row)[0])
            result = await self._rcon(f"pardon {name}")
            self.app.notify(result or f"Desbaneado: {name}", severity="information")
            await self._load_bans()
        except Exception as e:
            self.app.notify(str(e), severity="error")

    async def _op_add(self) -> None:
        try:
            name = self.query_one("#ops-input", Input).value.strip()
            if not name:
                return
            result = await self._rcon(f"op {name}")
            self.app.notify(result or f"OP dado: {name}", severity="information")
            await self._load_ops()
        except Exception as e:
            self.app.notify(str(e), severity="error")

    async def _op_remove(self) -> None:
        try:
            tbl = self.query_one("#ops-table", DataTable)
            if tbl.cursor_row is None:
                return
            name = str(tbl.get_row_at(tbl.cursor_row)[0])
            result = await self._rcon(f"deop {name}")
            self.app.notify(result or f"OP quitado: {name}", severity="warning")
            await self._load_ops()
        except Exception as e:
            self.app.notify(str(e), severity="error")
