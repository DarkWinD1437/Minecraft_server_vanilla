from __future__ import annotations

import asyncio
import json
import urllib.request
from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, DataTable, Input
from textual.containers import Horizontal, Vertical, ScrollableContainer

from mc_manager.core.config import app_config, docker


_RECOMMENDED = [
    {
        "name": "EssentialsX",
        "desc": "Comandos /ping, /home, /tpa, /spawn, /back",
        "url_info": "essentialsx.net",
        "source": "github",
        "repo": "EssentialsX/Essentials",
        "pattern": "EssentialsX-",
    },
    {
        "name": "LuckPerms",
        "desc": "Permisos por grupos — controla quien usa cada comando",
        "url_info": "luckperms.net",
        "source": "github",
        "repo": "LuckPerms/LuckPerms",
        "pattern": "LuckPerms-Bukkit-",
    },
    {
        "name": "spark",
        "desc": "Profiler de rendimiento recomendado por Paper",
        "url_info": "spark.lucko.me",
        "source": "github",
        "repo": "lucko/spark",
        "pattern": "spark-",
    },
    {
        "name": "Dynmap",
        "desc": "Mapa web interactivo del mundo en tiempo real",
        "url_info": "dynmap.us",
        "source": "github",
        "repo": "webbukkit/dynmap",
        "pattern": "Dynmap-",
    },
    {
        "name": "Coordinates HUD",
        "desc": "Coordenadas visibles en pantalla para todos por igual",
        "url_info": "hangar.papermc.io",
        "source": "modrinth",
        "project_id": "coordinateshud",
        "pattern": ".jar",
    },
    {
        "name": "Chunky",
        "desc": "Pre-genera chunks del mundo — instala antes del primer arranque",
        "url_info": "github.com/pop4959/Chunky",
        "source": "github",
        "repo": "pop4959/Chunky",
        "pattern": "Chunky",
    },
    {
        "name": "CoreProtect",
        "desc": "Registro de bloques: quién rompió/colocó qué y cuándo",
        "url_info": "coreprotect.net",
        "source": "github",
        "repo": "PlayPro/CoreProtect",
        "pattern": "CoreProtect-",
    },
    {
        "name": "Vault",
        "desc": "Puente de economía y permisos — requerido por muchos plugins",
        "url_info": "github.com/MilkBowl/Vault",
        "source": "github",
        "repo": "MilkBowl/Vault",
        "pattern": "Vault",
    },
    {
        "name": "ViaVersion",
        "desc": "Permite conectar con versiones de cliente más nuevas que el servidor",
        "url_info": "viaversion.com",
        "source": "github",
        "repo": "ViaVersion/ViaVersion",
        "pattern": "ViaVersion-",
    },
]


class PluginsPane(Widget):

    DEFAULT_CSS = """
    PluginsPane {
        width: 100%;
        height: 100%;
        padding: 0;
        layout: vertical;
    }
    #plug-scroll {
        width: 100%;
        height: 1fr;
        padding: 1 2;
    }
    .plug-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .plug-card {
        height: auto;
        border: solid $primary-darken-2;
        background: $panel;
        padding: 1;
        margin-bottom: 1;
    }
    .plug-table-wrap {
        height: 12;
    }
    .plug-btn-row {
        layout: horizontal;
        height: 3;
        margin-top: 1;
        align: left middle;
    }
    .plug-btn-row Button {
        margin-right: 1;
        min-width: 16;
    }
    .plug-warn {
        color: $warning;
        margin-top: 1;
    }
    .plug-hint {
        color: $text-muted;
        margin-bottom: 1;
    }
    .rec-row {
        layout: horizontal;
        height: 5;
        align: left middle;
        margin-bottom: 1;
        border-bottom: dashed $primary-darken-3;
    }
    .rec-info {
        width: 1fr;
    }
    .rec-name {
        text-style: bold;
    }
    .rec-desc {
        color: $text-muted;
    }
    .rec-url {
        color: $accent;
        text-style: italic;
    }
    .rec-install-btn {
        width: 14;
    }
    .url-install-row {
        layout: horizontal;
        height: 3;
        margin-top: 1;
        align: left middle;
    }
    .url-install-row Input {
        width: 1fr;
        margin-right: 1;
    }
    .url-install-row Button {
        width: 18;
    }
    .url-hint {
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._plugins: list[Path] = []

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="plug-scroll"):
            yield Label("🔌  Gestor de Plugins", classes="plug-title")

            with Vertical(classes="plug-card"):
                yield Label("Plugins instalados:", classes="plug-title")
                yield Label(
                    "Seleccionar fila y usar Activar / Desactivar. "
                    "Los JAR van en datos_mc/plugins/",
                    classes="plug-hint",
                )
                with Vertical(classes="plug-table-wrap"):
                    yield DataTable(id="plug-table", cursor_type="row")
                with Horizontal(classes="plug-btn-row"):
                    yield Button("✅ Activar", id="plug-enable", variant="success")
                    yield Button("❌ Desactivar", id="plug-disable", variant="error")
                    yield Button("🔄 Refrescar", id="plug-refresh", variant="default")
                    yield Button("↺ Reiniciar servidor", id="plug-restart", variant="warning")
                yield Label(
                    "⚠  El servidor debe reiniciarse para que los cambios surtan efecto.",
                    classes="plug-warn",
                )

            with Vertical(classes="plug-card"):
                yield Label("Plugins recomendados — ⬇ para instalar:", classes="plug-title")
                for i, plugin in enumerate(_RECOMMENDED):
                    with Horizontal(classes="rec-row"):
                        with Vertical(classes="rec-info"):
                            yield Label(plugin["name"], classes="rec-name")
                            yield Label(plugin["desc"], classes="rec-desc")
                            yield Label(plugin["url_info"], classes="rec-url")
                        yield Button(
                            "⬇ Instalar",
                            id=f"rec-install-{i}",
                            variant="primary",
                            classes="rec-install-btn",
                        )

            with Vertical(classes="plug-card"):
                yield Label("Instalar desde URL directa:", classes="plug-title")
                yield Label(
                    "Pega la URL de descarga directa de cualquier .jar (Hangar, SpigotMC, GitHub, etc.)",
                    classes="url-hint",
                )
                with Horizontal(classes="url-install-row"):
                    yield Input(
                        placeholder="https://ejemplo.com/plugin.jar",
                        id="url-install-input",
                    )
                    yield Button("⬇ Instalar JAR", id="url-install-btn", variant="primary")

    def on_mount(self) -> None:
        table = self.query_one("#plug-table", DataTable)
        table.add_columns("Plugin", "Estado")
        self._refresh()

    def _plugins_dir(self) -> Path:
        return app_config.data_dir / "plugins"

    def _refresh(self) -> None:
        table = self.query_one("#plug-table", DataTable)
        table.clear()
        self._plugins.clear()

        plugins_dir = self._plugins_dir()
        if not plugins_dir.exists():
            return

        active = sorted(plugins_dir.glob("*.jar"), key=lambda p: p.stem.lower())
        inactive = sorted(plugins_dir.glob("*.jar.disabled"), key=lambda p: p.name.lower())

        for jar in active:
            self._plugins.append(jar)
            table.add_row(jar.stem, "[green]● Activo[/]")

        for jar in inactive:
            self._plugins.append(jar)
            stem = jar.name[: -len(".disabled")]
            stem = stem[: -len(".jar")]
            table.add_row(stem, "[red]○ Inactivo[/]")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "plug-refresh":
            self._refresh()
        elif bid == "plug-enable":
            self._toggle(enable=True)
        elif bid == "plug-disable":
            self._toggle(enable=False)
        elif bid == "plug-restart":
            self.app.notify("Reiniciando servidor...", severity="warning")
            self.run_worker(self._do_restart(), exclusive=True)
        elif bid and bid.startswith("rec-install-"):
            idx = int(bid.split("-")[-1])
            event.button.disabled = True
            self.run_worker(self._install_plugin(idx, event.button), exclusive=False)
        elif bid == "url-install-btn":
            self.run_worker(self._install_from_url(event.button), exclusive=False)

    def _toggle(self, enable: bool) -> None:
        table = self.query_one("#plug-table", DataTable)
        row = table.cursor_row
        if row < 0 or row >= len(self._plugins):
            self.app.notify("Selecciona un plugin primero.", severity="warning")
            return

        jar = self._plugins[row]
        is_active = jar.suffix == ".jar"

        if enable and is_active:
            self.app.notify(f"{jar.stem} ya está activo.", severity="warning")
            return
        if not enable and not is_active:
            self.app.notify("El plugin ya está inactivo.", severity="warning")
            return

        try:
            if enable:
                new_path = jar.parent / jar.name[: -len(".disabled")]
                jar.rename(new_path)
                self.app.notify(f"Activado: {new_path.stem}", severity="information")
            else:
                new_path = jar.with_name(jar.name + ".disabled")
                jar.rename(new_path)
                self.app.notify(f"Desactivado: {jar.stem}", severity="warning")
        except Exception as e:
            self.app.notify(f"Error: {e}", severity="error")

        self._refresh()

    async def _do_restart(self) -> None:
        out, err = await asyncio.to_thread(docker.restart, app_config.minecraft_container)
        if err and not out:
            self.app.notify(f"Error al reiniciar: {err}", severity="error")
        else:
            self.app.notify("Servidor reiniciado.", severity="information")
        self._refresh()

    # ── Descarga de plugins recomendados ─────────────────────────────────────

    def _fetch_github_jar(self, repo: str, pattern: str) -> tuple[str, str]:
        """(bloqueante) Retorna (download_url, filename) del último release de GitHub."""
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "MC-Manager/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        for asset in data.get("assets", []):
            name: str = asset["name"]
            if pattern.lower() in name.lower() and name.endswith(".jar"):
                return asset["browser_download_url"], name
        raise ValueError(f"No se encontro JAR con patron '{pattern}' en {repo}")

    def _fetch_modrinth_jar(self, project_id: str) -> tuple[str, str]:
        """(bloqueante) Retorna (download_url, filename) de Modrinth."""
        url = f"https://api.modrinth.com/v2/project/{project_id}/version"
        req = urllib.request.Request(url, headers={"User-Agent": "MC-Manager/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            versions = json.loads(resp.read())
        if versions:
            files = versions[0].get("files", [])
            if files:
                primary = next((f for f in files if f.get("primary")), files[0])
                return primary["url"], primary["filename"]
        raise ValueError(f"No se encontro JAR para '{project_id}' en Modrinth")

    def _download_jar(self, dl_url: str, dest: Path) -> None:
        """(bloqueante) Descarga el JAR a dest."""
        urllib.request.urlretrieve(dl_url, dest)

    async def _install_plugin(self, idx: int, btn: Button) -> None:
        plugin = _RECOMMENDED[idx]
        name = plugin["name"]
        self.app.notify(f"Descargando {name}...", severity="information")

        plugins_dir = self._plugins_dir()
        plugins_dir.mkdir(parents=True, exist_ok=True)

        try:
            if plugin["source"] == "github":
                dl_url, filename = await asyncio.to_thread(
                    self._fetch_github_jar, plugin["repo"], plugin["pattern"]
                )
            else:
                dl_url, filename = await asyncio.to_thread(
                    self._fetch_modrinth_jar, plugin["project_id"]
                )

            dest = plugins_dir / filename
            await asyncio.to_thread(self._download_jar, dl_url, dest)

            self.app.notify(
                f"✅ {name} instalado. Reinicia el servidor para activarlo.",
                severity="information",
                timeout=8,
            )
            self._refresh()
        except Exception as exc:
            self.app.notify(f"❌ Error instalando {name}: {exc}", severity="error")
        finally:
            btn.disabled = False

    async def _install_from_url(self, btn: Button) -> None:
        """Descarga un .jar desde una URL directa pegada por el usuario."""
        try:
            url_input = self.query_one("#url-install-input", Input)
            url = url_input.value.strip()
        except Exception:
            return

        if not url:
            self.app.notify("Pega una URL antes de instalar.", severity="warning")
            return
        if not url.lower().endswith(".jar"):
            self.app.notify("La URL debe terminar en .jar", severity="warning")
            return

        btn.disabled = True
        filename = url.split("/")[-1].split("?")[0] or "plugin.jar"
        self.app.notify(f"Descargando {filename}...", severity="information")

        plugins_dir = self._plugins_dir()
        plugins_dir.mkdir(parents=True, exist_ok=True)
        dest = plugins_dir / filename

        try:
            await asyncio.to_thread(self._download_jar, url, dest)
            self.app.notify(
                f"✅ {filename} instalado. Reinicia el servidor para activarlo.",
                severity="information",
                timeout=8,
            )
            url_input.value = ""
            self._refresh()
        except Exception as exc:
            self.app.notify(f"❌ Error descargando plugin: {exc}", severity="error")
        finally:
            btn.disabled = False
