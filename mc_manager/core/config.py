from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mc_manager.core.os_detect import OSInfo, detect as detect_os
from mc_manager.core.docker_client import DockerClient


@dataclass
class AppConfig:
    compose_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    minecraft_container: str = "mc_servidor"
    tunnel_container: str = "mc_tunel_red"
    rcon_port: int = 25575
    rcon_password: str = "mcpassword"
    stats_interval: float = 2.0
    log_buffer_size: int = 5000
    backup_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "backups")
    logs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")

    @property
    def data_dir(self) -> Path:
        return self.compose_dir / "datos_mc"

    @property
    def server_properties(self) -> Path:
        return self.data_dir / "server.properties"

    @property
    def whitelist_json(self) -> Path:
        return self.data_dir / "whitelist.json"

    @property
    def banned_players_json(self) -> Path:
        return self.data_dir / "banned-players.json"

    @property
    def banned_ips_json(self) -> Path:
        return self.data_dir / "banned-ips.json"

    @property
    def ops_json(self) -> Path:
        return self.data_dir / "ops.json"


# Module-level singletons — import from here everywhere
os_info: OSInfo = detect_os()
app_config: AppConfig = AppConfig()
docker: DockerClient = DockerClient(compose_dir=app_config.compose_dir)
