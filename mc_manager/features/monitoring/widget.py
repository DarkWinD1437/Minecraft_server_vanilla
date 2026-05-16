from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Static
from textual.containers import Horizontal, Vertical, ScrollableContainer

from mc_manager.core.events import StatsUpdated, SystemStatsUpdated
from mc_manager.features.monitoring.meters import SparklineCard, MeterBar, IOCard


class MonitoringPane(Widget):

    DEFAULT_CSS = """
    MonitoringPane {
        width: 100%;
        height: 100%;
        overflow-y: auto;
        padding: 1 2;
    }
    .mon-section-title {
        text-style: bold;
        color: $accent;
        background: $panel-darken-1;
        padding: 0 1;
        margin: 1 0;
    }
    .sparkline-row {
        layout: horizontal;
        height: 11;
        margin-bottom: 1;
    }
    .meter-section {
        margin-bottom: 1;
        border: solid $primary-darken-3;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("📊  SERVIDOR MINECRAFT", classes="mon-section-title")

        with Horizontal(classes="sparkline-row"):
            yield SparklineCard("CPU del Servidor", unit="%", extra_css_class="sparkline-cpu", id="mc-cpu")
            yield SparklineCard("RAM del Servidor", unit="MB", extra_css_class="sparkline-ram", id="mc-ram")

        with Horizontal(classes="sparkline-row"):
            yield SparklineCard("Red Entrada", unit="KB/s", extra_css_class="sparkline-net", id="mc-net-in")
            yield SparklineCard("Red Salida", unit="KB/s", extra_css_class="sparkline-net", id="mc-net-out")

        with Horizontal(classes="sparkline-row"):
            yield SparklineCard("Disco Lectura", unit="MB/s", extra_css_class="sparkline-disk", id="mc-disk-r")
            yield SparklineCard("Disco Escritura", unit="MB/s", extra_css_class="sparkline-disk", id="mc-disk-w")

        with Vertical(classes="meter-section"):
            yield Label("Uso Instantáneo:", classes="mon-section-title")
            yield MeterBar("CPU MC:", total=100.0, id="bar-mc-cpu")
            yield MeterBar("RAM MC:", total=100.0, id="bar-mc-ram")

        yield Label("💻  SISTEMA HOST", classes="mon-section-title")

        with Horizontal(classes="sparkline-row"):
            yield SparklineCard("CPU Sistema", unit="%", extra_css_class="sparkline-cpu", id="sys-cpu")
            yield SparklineCard("RAM Sistema", unit="GB", extra_css_class="sparkline-ram", id="sys-ram")

        with Vertical(classes="meter-section"):
            yield Label("Uso Instantáneo:", classes="mon-section-title")
            yield MeterBar("CPU Sistema:", total=100.0, id="bar-sys-cpu")
            yield MeterBar("RAM Sistema:", total=100.0, id="bar-sys-ram")

    def on_stats_updated(self, message: StatsUpdated) -> None:
        try: self.query_one("#mc-cpu", SparklineCard).push(message.cpu_pct)
        except Exception: pass
        try: self.query_one("#mc-ram", SparklineCard).push(message.ram_used_mb)
        except Exception: pass
        try: self.query_one("#mc-net-in", SparklineCard).push(message.net_in_kb)
        except Exception: pass
        try: self.query_one("#mc-net-out", SparklineCard).push(message.net_out_kb)
        except Exception: pass
        try: self.query_one("#mc-disk-r", SparklineCard).push(message.block_read_mb)
        except Exception: pass
        try: self.query_one("#mc-disk-w", SparklineCard).push(message.block_write_mb)
        except Exception: pass
        try: self.query_one("#bar-mc-cpu", MeterBar).set_value(message.cpu_pct, 100.0)
        except Exception: pass
        if message.ram_limit_mb > 0:
            try: self.query_one("#bar-mc-ram", MeterBar).set_value(message.ram_used_mb, message.ram_limit_mb)
            except Exception: pass

    def on_system_stats_updated(self, message: SystemStatsUpdated) -> None:
        try: self.query_one("#sys-cpu", SparklineCard).push(message.cpu_pct)
        except Exception: pass
        try: self.query_one("#sys-ram", SparklineCard).push(message.ram_used_gb)
        except Exception: pass
        try: self.query_one("#bar-sys-cpu", MeterBar).set_value(message.cpu_pct, 100.0)
        except Exception: pass
        try: self.query_one("#bar-sys-ram", MeterBar).set_value(message.ram_pct, 100.0)
        except Exception: pass
