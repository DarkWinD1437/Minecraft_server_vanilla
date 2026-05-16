from __future__ import annotations

import tarfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class BackupInfo:
    path: Path
    name: str
    size_bytes: int
    created_at: datetime
    compressed: bool


def list_backups(backup_dir: Path) -> list[BackupInfo]:
    if not backup_dir.exists():
        return []
    backups = []
    for f in backup_dir.iterdir():
        if f.suffix in (".gz", ".tar") or f.name.endswith(".tar.gz"):
            stat = f.stat()
            try:
                ts_str = f.stem.split("_", 1)[1] if "_" in f.stem else ""
                created = datetime.strptime(ts_str[:15], "%Y%m%d_%H%M%S")
            except (ValueError, IndexError):
                created = datetime.fromtimestamp(stat.st_mtime)
            backups.append(BackupInfo(
                path=f,
                name=f.name,
                size_bytes=stat.st_size,
                created_at=created,
                compressed=f.name.endswith(".gz"),
            ))
    return sorted(backups, key=lambda b: b.created_at, reverse=True)


def create_backup(
    source_dir: Path,
    backup_dir: Path,
    name: str | None = None,
    compress: bool = True,
) -> tuple[Path, str]:
    """Create a backup archive. Returns (path, error). error is empty on success."""
    backup_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = (name or "world").replace(" ", "_").replace("/", "_")
    filename = f"{safe_name}_{ts}.tar.gz" if compress else f"{safe_name}_{ts}.tar"
    out_path = backup_dir / filename

    try:
        mode = "w:gz" if compress else "w"
        with tarfile.open(out_path, mode) as tar:
            if source_dir.exists():
                tar.add(str(source_dir), arcname=source_dir.name)
            else:
                return out_path, f"Directorio de datos no encontrado: {source_dir}"
        return out_path, ""
    except Exception as e:
        if out_path.exists():
            out_path.unlink()
        return out_path, str(e)


def restore_backup(archive: Path, target_dir: Path) -> tuple[bool, str]:
    """Extract a backup archive to target_dir. Returns (success, error)."""
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive, "r:*") as tar:
            tar.extractall(str(target_dir))
        return True, ""
    except Exception as e:
        return False, str(e)


def delete_backup(archive: Path) -> tuple[bool, str]:
    try:
        archive.unlink()
        return True, ""
    except Exception as e:
        return False, str(e)
