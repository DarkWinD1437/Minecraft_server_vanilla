from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Callable


async def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 30,
) -> tuple[str, str, int]:
    """Run a subprocess asynchronously. Returns (stdout, stderr, returncode)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd) if cwd else None,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return (
            stdout.decode("utf-8", errors="replace").strip(),
            stderr.decode("utf-8", errors="replace").strip(),
            proc.returncode or 0,
        )
    except asyncio.TimeoutError:
        return "", f"Timeout después de {timeout}s", -1
    except FileNotFoundError:
        return "", f"Comando no encontrado: {cmd[0]}", -1
    except Exception as e:
        return "", str(e), -1


async def run_command_stream(
    cmd: list[str],
    line_callback: Callable[[str], None],
    cwd: Path | None = None,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Stream stdout lines from a subprocess, calling line_callback for each."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(cwd) if cwd else None,
        )
        while True:
            if stop_event and stop_event.is_set():
                proc.terminate()
                break
            try:
                line_bytes = await asyncio.wait_for(proc.stdout.readline(), timeout=1.0)
            except asyncio.TimeoutError:
                if proc.returncode is not None:
                    break
                continue
            if not line_bytes:
                break
            line = line_bytes.decode("utf-8", errors="replace").rstrip()
            if line:
                line_callback(line)
    except Exception:
        pass
