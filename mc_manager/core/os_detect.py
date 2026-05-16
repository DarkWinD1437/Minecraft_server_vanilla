from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OSInfo:
    system: str       # "Windows", "Linux", "Darwin"
    distro: str       # e.g. "Linux Mint", "Ubuntu", "Windows" (empty on Windows)
    distro_id: str    # e.g. "linuxmint", "ubuntu"
    is_wsl: bool
    is_windows: bool
    is_linux: bool

    @property
    def display_name(self) -> str:
        if self.is_windows and not self.is_wsl:
            return "Windows"
        if self.is_wsl:
            return f"WSL ({self.distro or 'Linux'})"
        if self.distro:
            return f"Linux / {self.distro}"
        return self.system


_INSTANCE: OSInfo | None = None


def detect() -> OSInfo:
    global _INSTANCE
    if _INSTANCE is not None:
        return _INSTANCE

    system = platform.system()  # "Windows", "Linux", "Darwin"
    distro = ""
    distro_id = ""
    is_wsl = False
    is_windows = system == "Windows"
    is_linux = system == "Linux"

    if is_linux:
        # Check for WSL via /proc/version
        try:
            proc_version = Path("/proc/version").read_text(encoding="utf-8", errors="ignore")
            if "microsoft" in proc_version.lower():
                is_wsl = True
        except OSError:
            pass

        # Also check env var as secondary signal
        if os.environ.get("WSL_DISTRO_NAME"):
            is_wsl = True

        # Parse /etc/os-release for distro name
        try:
            os_release = Path("/etc/os-release").read_text(encoding="utf-8", errors="ignore")
            for line in os_release.splitlines():
                if line.startswith("NAME="):
                    distro = line.split("=", 1)[1].strip().strip('"')
                elif line.startswith("ID="):
                    distro_id = line.split("=", 1)[1].strip().strip('"')
        except OSError:
            pass

    elif is_windows:
        distro = "Windows"
        distro_id = "windows"

    _INSTANCE = OSInfo(
        system=system,
        distro=distro,
        distro_id=distro_id,
        is_wsl=is_wsl,
        is_windows=is_windows,
        is_linux=is_linux,
    )
    return _INSTANCE


def get() -> OSInfo:
    if _INSTANCE is None:
        return detect()
    return _INSTANCE
