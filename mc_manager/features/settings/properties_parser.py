from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class PropertyMeta:
    prop_type: Literal["bool", "int", "select", "str"]
    default: str
    description: str
    choices: list[str] = field(default_factory=list)
    range_min: int | None = None
    range_max: int | None = None
    section: str = "Otros"


PROPERTY_METADATA: dict[str, PropertyMeta] = {
    # Mundo
    "level-name":        PropertyMeta("str",    "world",       "Nombre del mundo",                section="Mundo"),
    "level-seed":        PropertyMeta("str",    "",            "Semilla del mundo",               section="Mundo"),
    "level-type":        PropertyMeta("select", "DEFAULT",     "Tipo de mundo",
                                     choices=["DEFAULT", "FLAT", "LARGEB", "AMPLIFIED"], section="Mundo"),
    "gamemode":          PropertyMeta("select", "survival",    "Modo de juego predeterminado",
                                     choices=["survival", "creative", "adventure", "spectator"], section="Gameplay"),
    "difficulty":        PropertyMeta("select", "easy",        "Dificultad",
                                     choices=["peaceful", "easy", "normal", "hard"], section="Gameplay"),
    "max-players":       PropertyMeta("int",    "20",          "Máximo de jugadores", range_min=1, range_max=100, section="Red"),
    "view-distance":     PropertyMeta("int",    "10",          "Distancia de visión (chunks)", range_min=3, range_max=32, section="Rendimiento"),
    "simulation-distance": PropertyMeta("int",  "10",          "Distancia de simulación", range_min=3, range_max=32, section="Rendimiento"),
    "max-tick-time":     PropertyMeta("int",    "60000",       "Tiempo máximo por tick (ms)", range_min=0, range_max=600000, section="Rendimiento"),
    "online-mode":       PropertyMeta("bool",   "true",        "Verificar cuentas premium", section="Seguridad"),
    "white-list":        PropertyMeta("bool",   "false",       "Habilitar whitelist", section="Seguridad"),
    "enable-command-block": PropertyMeta("bool","false",       "Habilitar bloques de comandos", section="Gameplay"),
    "spawn-monsters":    PropertyMeta("bool",   "true",        "Generar monstruos", section="Gameplay"),
    "spawn-animals":     PropertyMeta("bool",   "true",        "Generar animales", section="Gameplay"),
    "spawn-npcs":        PropertyMeta("bool",   "true",        "Generar aldeanos", section="Gameplay"),
    "pvp":               PropertyMeta("bool",   "true",        "Permitir PvP", section="Gameplay"),
    "server-port":       PropertyMeta("int",    "25565",       "Puerto del servidor", range_min=1, range_max=65535, section="Red"),
    "enable-rcon":       PropertyMeta("bool",   "false",       "Habilitar RCON", section="Seguridad"),
    "rcon.port":         PropertyMeta("int",    "25575",       "Puerto RCON", range_min=1, range_max=65535, section="Seguridad"),
    "rcon.password":     PropertyMeta("str",    "",            "Contraseña RCON", section="Seguridad"),
    "motd":              PropertyMeta("str",    "A Minecraft Server", "Mensaje del día (MOTD)", section="Red"),
    "allow-flight":      PropertyMeta("bool",   "false",       "Permitir vuelo", section="Gameplay"),
    "force-gamemode":    PropertyMeta("bool",   "false",       "Forzar gamemode al entrar", section="Gameplay"),
    "player-idle-timeout": PropertyMeta("int",  "0",           "Kick por inactividad (min, 0=deshabilitado)", range_min=0, range_max=1440, section="Red"),
}

_SECTIONS_ORDER = ["Mundo", "Red", "Gameplay", "Rendimiento", "Seguridad", "Otros"]


def read_properties(path: Path) -> dict[str, str]:
    """Read server.properties into a dict, skipping comment lines."""
    if not path.exists():
        return {}
    props: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            props[key.strip()] = value.strip()
    return props


def write_properties(path: Path, props: dict[str, str]) -> None:
    """Write server.properties, preserving original comment header if present."""
    original_header = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                original_header.append(line)
            else:
                break

    lines = original_header if original_header else ["#Minecraft server properties"]
    for key, value in props.items():
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_sections(props: dict[str, str]) -> dict[str, list[tuple[str, str, PropertyMeta | None]]]:
    """Group properties by section. Returns {section: [(key, value, meta), ...]}."""
    sections: dict[str, list] = {s: [] for s in _SECTIONS_ORDER}
    for key, value in props.items():
        meta = PROPERTY_METADATA.get(key)
        section = meta.section if meta else "Otros"
        if section not in sections:
            sections[section] = []
        sections[section].append((key, value, meta))
    return {k: v for k, v in sections.items() if v}
