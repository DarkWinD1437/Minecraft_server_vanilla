from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import psutil

from mc_manager.core.config import docker, app_config
from mc_manager.core.events import StatsUpdated, SystemStatsUpdated
from mc_manager.core.docker_client import ContainerState
from mc_manager.utils.formatting import (
    parse_docker_mem_usage, parse_docker_io,
    parse_docker_net_kb, parse_cpu_pct
)

if TYPE_CHECKING:
    from textual.app import App


async def run_stats_worker(app: "App") -> None:
    """Background worker: posts StatsUpdated and SystemStatsUpdated to app every interval."""
    interval = app_config.stats_interval
    container = app_config.minecraft_container

    while True:
        # Docker container stats — fallo aquí no debe afectar las stats del sistema
        try:
            stats_dict, err = await asyncio.to_thread(docker.get_stats, container)
            if stats_dict:
                cpu_pct = parse_cpu_pct(stats_dict.get("CPUPerc", "0%"))
                ram_used_mb, ram_limit_mb = parse_docker_mem_usage(
                    stats_dict.get("MemUsage", "0B / 0B")
                )
                net_in_kb, net_out_kb = parse_docker_net_kb(
                    stats_dict.get("NetIO", "0B / 0B")
                )
                block_read_mb, block_write_mb = parse_docker_io(
                    stats_dict.get("BlockIO", "0B / 0B")
                )
                pids = int(stats_dict.get("PIDs", 0) or 0)

                app.screen.post_message(StatsUpdated(
                    cpu_pct=cpu_pct,
                    ram_used_mb=ram_used_mb,
                    ram_limit_mb=ram_limit_mb,
                    net_in_kb=net_in_kb,
                    net_out_kb=net_out_kb,
                    block_read_mb=block_read_mb,
                    block_write_mb=block_write_mb,
                    pids=pids,
                ))
            else:
                app.screen.post_message(StatsUpdated(0, 0, 0, 0, 0, 0, 0, 0))
        except Exception as exc:
            logging.warning("stats_worker docker error: %s", exc)
            app.screen.post_message(StatsUpdated(0, 0, 0, 0, 0, 0, 0, 0))

        # Stats del sistema host — independiente de Docker, siempre se publica
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            app.screen.post_message(SystemStatsUpdated(
                cpu_pct=cpu,
                ram_pct=mem.percent,
                ram_used_gb=mem.used / (1024**3),
                ram_total_gb=mem.total / (1024**3),
            ))
        except Exception as exc:
            logging.warning("stats_worker psutil error: %s", exc)

        await asyncio.sleep(interval)
