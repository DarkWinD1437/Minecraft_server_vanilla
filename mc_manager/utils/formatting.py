from __future__ import annotations

import re


def bytes_to_human(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


_UNIT_MULTIPLIERS = {
    "b": 1,
    "kb": 1024,
    "mb": 1024**2,
    "gb": 1024**3,
    "tb": 1024**4,
    "kib": 1024,
    "mib": 1024**2,
    "gib": 1024**3,
    "tib": 1024**4,
}


def parse_size_to_bytes(size_str: str) -> float:
    """Parse Docker human-readable size like '4.52GiB', '512MiB', '1.2GB' to bytes."""
    size_str = size_str.strip()
    match = re.match(r"^([\d.]+)\s*([a-zA-Z]+)?$", size_str)
    if not match:
        return 0.0
    value = float(match.group(1))
    unit = (match.group(2) or "b").lower()
    return value * _UNIT_MULTIPLIERS.get(unit, 1)


def parse_size_to_mb(size_str: str) -> float:
    return parse_size_to_bytes(size_str) / (1024**2)


def parse_size_to_gb(size_str: str) -> float:
    return parse_size_to_bytes(size_str) / (1024**3)


def parse_docker_mem_usage(mem_str: str) -> tuple[float, float]:
    """Parse '4.52GiB / 10GiB' → (used_mb, limit_mb)."""
    parts = mem_str.split("/")
    if len(parts) != 2:
        return 0.0, 0.0
    return parse_size_to_mb(parts[0].strip()), parse_size_to_mb(parts[1].strip())


def parse_docker_io(io_str: str) -> tuple[float, float]:
    """Parse '1.2MB / 500kB' → (read_mb, write_mb) or (in_kb, out_kb)."""
    parts = io_str.split("/")
    if len(parts) != 2:
        return 0.0, 0.0
    left = parse_size_to_mb(parts[0].strip())
    right = parse_size_to_mb(parts[1].strip())
    return left, right


def parse_docker_net_kb(io_str: str) -> tuple[float, float]:
    """Parse '1.2MB / 500kB' → (in_kb, out_kb)."""
    parts = io_str.split("/")
    if len(parts) != 2:
        return 0.0, 0.0
    in_bytes = parse_size_to_bytes(parts[0].strip())
    out_bytes = parse_size_to_bytes(parts[1].strip())
    return in_bytes / 1024, out_bytes / 1024


def parse_cpu_pct(cpu_str: str) -> float:
    """Parse '12.34%' → 12.34."""
    return float(cpu_str.strip().rstrip("%") or 0)


def seconds_to_human(seconds: float) -> str:
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days:
        return f"{days}d {hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def truncate(text: str, max_len: int = 40) -> str:
    return text if len(text) <= max_len else text[: max_len - 3] + "..."
