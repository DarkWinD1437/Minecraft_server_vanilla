from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING

from mc_manager.core.events import LogLine, PlayitLinkFound, TunnelLinkUpdated

if TYPE_CHECKING:
    from textual.app import App


_LEVEL_PATTERN = re.compile(r"\[([\d:]+)\s+(INFO|WARN|WARNING|ERROR|FATAL|DEBUG)\]", re.IGNORECASE)
_PLAYIT_URL = re.compile(r"https://(?:www\.)?playit\.gg\S+", re.IGNORECASE)
_PLAYIT_CONNECT_ADDR = re.compile(r"connect_addr:\s*([\d\.]+:\d+)")
_PLAYER_JOIN = re.compile(r"(\w+) joined the game")
_PLAYER_LEAVE = re.compile(r"(\w+) left the game")


def _extract_level(line: str) -> str:
    m = _LEVEL_PATTERN.search(line)
    if m:
        lvl = m.group(2).upper()
        return "WARNING" if lvl == "WARNING" else lvl
    if "ERROR" in line.upper():
        return "ERROR"
    if "WARN" in line.upper():
        return "WARN"
    return "INFO"


async def run_log_worker(app: "App", container: str) -> None:
    """Stream docker logs -f for a container, posting LogLine messages to app."""
    is_tunnel = "tunel" in container or "tunnel" in container or "playit" in container
    _found_links: set[str] = set()

    while True:
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "logs", "-f", "--tail", "50", container,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            while True:
                try:
                    line_bytes = await asyncio.wait_for(proc.stdout.readline(), timeout=2.0)
                except asyncio.TimeoutError:
                    if proc.returncode is not None:
                        break
                    continue

                if not line_bytes:
                    break

                line = line_bytes.decode("utf-8", errors="replace").rstrip()
                if not line:
                    continue

                level = _extract_level(line)
                app.screen.post_message(LogLine(source=container, text=line, level=level))

                # Extract Playit.gg links from tunnel container
                if is_tunnel:
                    url_match = _PLAYIT_URL.search(line)
                    if url_match:
                        url = url_match.group(0)
                        if url not in _found_links:
                            _found_links.add(url)
                            app.screen.post_message(PlayitLinkFound(url=url))
                            app.screen.post_message(TunnelLinkUpdated(url=url, container_running=True))
                    else:
                        # playit-agent v0.17 logs connect_addr: IP:PORT when a client connects
                        addr_match = _PLAYIT_CONNECT_ADDR.search(line)
                        if addr_match:
                            addr = addr_match.group(1)
                            if addr not in _found_links:
                                _found_links.add(addr)
                                app.screen.post_message(TunnelLinkUpdated(url=addr, container_running=True))

        except FileNotFoundError:
            app.screen.post_message(LogLine(
                source="manager",
                text=f"[Log] Docker no encontrado en PATH. ¿Está instalado y corriendo?",
                level="ERROR",
            ))
            await asyncio.sleep(10)
            continue
        except PermissionError:
            app.screen.post_message(LogLine(
                source="manager",
                text=f"[Log] Sin permiso para ejecutar Docker. En Linux: sudo usermod -aG docker $USER",
                level="ERROR",
            ))
            await asyncio.sleep(10)
            continue
        except Exception as e:
            app.screen.post_message(LogLine(
                source="manager",
                text=f"[Log] Error al leer logs de '{container}': {e}",
                level="ERROR",
            ))

        # Container stopped or error — wait before retrying
        await asyncio.sleep(3)
