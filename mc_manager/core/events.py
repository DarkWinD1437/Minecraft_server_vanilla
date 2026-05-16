from __future__ import annotations

from pathlib import Path
from textual.message import Message
from mc_manager.core.docker_client import ContainerState


class ContainerStateChanged(Message):
    def __init__(self, state: ContainerState, container: str) -> None:
        super().__init__()
        self.state = state
        self.container = container


class StatsUpdated(Message):
    def __init__(
        self,
        cpu_pct: float,
        ram_used_mb: float,
        ram_limit_mb: float,
        net_in_kb: float,
        net_out_kb: float,
        block_read_mb: float,
        block_write_mb: float,
        pids: int,
    ) -> None:
        super().__init__()
        self.cpu_pct = cpu_pct
        self.ram_used_mb = ram_used_mb
        self.ram_limit_mb = ram_limit_mb
        self.net_in_kb = net_in_kb
        self.net_out_kb = net_out_kb
        self.block_read_mb = block_read_mb
        self.block_write_mb = block_write_mb
        self.pids = pids


class SystemStatsUpdated(Message):
    def __init__(
        self,
        cpu_pct: float,
        ram_pct: float,
        ram_used_gb: float,
        ram_total_gb: float,
    ) -> None:
        super().__init__()
        self.cpu_pct = cpu_pct
        self.ram_pct = ram_pct
        self.ram_used_gb = ram_used_gb
        self.ram_total_gb = ram_total_gb


class LogLine(Message):
    def __init__(self, source: str, text: str, level: str = "INFO") -> None:
        super().__init__()
        self.source = source
        self.text = text
        self.level = level


class PlayitLinkFound(Message):
    def __init__(self, url: str) -> None:
        super().__init__()
        self.url = url


class BackupCompleted(Message):
    def __init__(self, path: Path, success: bool, error: str = "") -> None:
        super().__init__()
        self.path = path
        self.success = success
        self.error = error


class CommandExecuted(Message):
    def __init__(self, command: str, output: str, success: bool) -> None:
        super().__init__()
        self.command = command
        self.output = output
        self.success = success


class PlayerCountUpdated(Message):
    def __init__(self, count: int, max_count: int) -> None:
        super().__init__()
        self.count = count
        self.max_count = max_count


class AlertTriggered(Message):
    def __init__(self, rule_name: str, metric: str, value: float, threshold: float, severity: str) -> None:
        super().__init__()
        self.rule_name = rule_name
        self.metric = metric
        self.value = value
        self.threshold = threshold
        self.severity = severity


class TunnelLinkUpdated(Message):
    def __init__(self, url: str, container_running: bool) -> None:
        super().__init__()
        self.url = url
        self.container_running = container_running
