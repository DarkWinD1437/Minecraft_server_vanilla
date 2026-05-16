from __future__ import annotations

import re


def is_valid_player_name(name: str) -> bool:
    return bool(re.match(r"^[A-Za-z0-9_]{1,16}$", name))


def is_valid_port(value: str) -> bool:
    try:
        port = int(value)
        return 1 <= port <= 65535
    except ValueError:
        return False


def is_valid_positive_int(value: str) -> bool:
    try:
        return int(value) > 0
    except ValueError:
        return False


def is_valid_memory(value: str) -> bool:
    """Validate memory strings like '5G', '512M', '2048M'."""
    return bool(re.match(r"^\d+[MmGg]$", value.strip()))
