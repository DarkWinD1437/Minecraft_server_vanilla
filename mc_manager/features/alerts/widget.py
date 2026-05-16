from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, Input, Select, Switch, DataTable
from textual.containers import Horizontal, Vertical

from mc_manager.core.events import StatsUpdated, SystemStatsUpdated, AlertTriggered


_METRICS = [
    ("CPU Servidor (%)", "mc_cpu"),
    ("RAM Servidor (%)", "mc_ram"),
    ("CPU Sistema (%)", "sys_cpu"),
    ("RAM Sistema (%)", "sys_ram"),
]

_CONDITIONS = [
    ("Mayor que (>)", "gt"),
    ("Menor que (<)", "lt"),
]

_SEVERITIES = [
    ("Información", "info"),
    ("Advertencia", "warning"),
    ("Crítico", "error"),
]


@dataclass
class AlertRule:
    name: str
    metric: str
    condition: str  # "gt" or "lt"
    threshold: float
    severity: str
    enabled: bool = True
    triggered_count: int = 0
    last_triggered: datetime | None = None
    _consecutive: int = field(default=0, repr=False)


class AlertsPane(Widget):

    DEFAULT_CSS = """
    AlertsPane {
        width: 100%;
        height: 100%;
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
        padding: 1 2;
    }
    .alerts-left {
        height: 100%;
    }
    .alerts-right {
        height: 100%;
        border: solid $primary-darken-2;
        padding: 1;
    }
    .alerts-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    DataTable {
        height: 1fr;
    }
    .alert-btn-row {
        layout: horizontal;
        height: 3;
        margin-top: 1;
        align: left middle;
    }
    .alert-btn-row Button {
        margin-right: 1;
    }
    .alert-field-row {
        layout: horizontal;
        height: 3;
        align: left middle;
        margin-bottom: 1;
    }
    .alert-field-row Label {
        width: 18;
        color: $text-muted;
    }
    .alert-field-row Input, .alert-field-row Select {
        width: 1fr;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._rules: list[AlertRule] = []
        self._history: list[tuple[str, str, str]] = []  # (time, rule, value)
        self._last_stats: dict[str, float] = {}

        # Default rules
        self._rules = [
            AlertRule("CPU alta MC", "mc_cpu", "gt", 90.0, "warning"),
            AlertRule("RAM crítica MC", "mc_ram", "gt", 95.0, "error"),
            AlertRule("CPU alta sistema", "sys_cpu", "gt", 90.0, "warning"),
        ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="alerts-left"):
            yield Label("🔔  Reglas de Alerta Activas", classes="alerts-title")
            yield DataTable(id="alerts-rules-table")
            with Horizontal(classes="alert-btn-row"):
                yield Button("🔄 Actualizar", id="alr-refresh", variant="primary")
                yield Button("🗑 Eliminar", id="alr-delete", variant="error")

            yield Label("\n📜  Historial de Alertas:", classes="alerts-title")
            yield DataTable(id="alerts-history-table")

        with Vertical(classes="alerts-right"):
            yield Label("➕  Nueva Regla de Alerta", classes="alerts-title")

            with Horizontal(classes="alert-field-row"):
                yield Label("Nombre:")
                yield Input(placeholder="Mi alerta", id="alr-name")

            with Horizontal(classes="alert-field-row"):
                yield Label("Métrica:")
                yield Select(options=_METRICS, value="mc_cpu", id="alr-metric", allow_blank=False)

            with Horizontal(classes="alert-field-row"):
                yield Label("Condición:")
                yield Select(options=_CONDITIONS, value="gt", id="alr-condition", allow_blank=False)

            with Horizontal(classes="alert-field-row"):
                yield Label("Umbral (valor):")
                yield Input(value="90", placeholder="90", id="alr-threshold")

            with Horizontal(classes="alert-field-row"):
                yield Label("Severidad:")
                yield Select(options=_SEVERITIES, value="warning", id="alr-severity", allow_blank=False)

            with Horizontal(classes="alert-field-row"):
                yield Label("Habilitada:")
                yield Switch(value=True, id="alr-enabled")

            with Horizontal(classes="alert-btn-row"):
                yield Button("➕ Agregar Regla", id="alr-add", variant="success")

    def on_mount(self) -> None:
        self._setup_tables()
        self._reload_rules()

    def _setup_tables(self) -> None:
        try:
            tbl = self.query_one("#alerts-rules-table", DataTable)
            tbl.add_columns("Nombre", "Métrica", "Condición", "Umbral", "Severidad", "Disparos")
        except Exception:
            pass
        try:
            tbl = self.query_one("#alerts-history-table", DataTable)
            tbl.add_columns("Hora", "Regla", "Valor")
        except Exception:
            pass

    def _reload_rules(self) -> None:
        try:
            tbl = self.query_one("#alerts-rules-table", DataTable)
            tbl.clear()
            cond_labels = {"gt": ">", "lt": "<"}
            for rule in self._rules:
                tbl.add_row(
                    rule.name, rule.metric,
                    cond_labels.get(rule.condition, rule.condition),
                    str(rule.threshold), rule.severity,
                    str(rule.triggered_count)
                )
        except Exception:
            pass

    def _check_rules(self, metric: str, value: float) -> None:
        for rule in self._rules:
            if not rule.enabled or rule.metric != metric:
                continue
            triggered = (rule.condition == "gt" and value > rule.threshold) or \
                        (rule.condition == "lt" and value < rule.threshold)
            if triggered:
                rule._consecutive += 1
                if rule._consecutive >= 3:  # 3 consecutive readings (avoid flapping)
                    rule._consecutive = 0
                    rule.triggered_count += 1
                    rule.last_triggered = datetime.now()
                    ts = datetime.now().strftime("%H:%M:%S")
                    self._history.insert(0, (ts, rule.name, f"{value:.1f}"))
                    self._update_history_table()
                    self.app.post_message(AlertTriggered(
                        rule_name=rule.name, metric=metric,
                        value=value, threshold=rule.threshold, severity=rule.severity
                    ))
            else:
                rule._consecutive = 0

    def _update_history_table(self) -> None:
        try:
            tbl = self.query_one("#alerts-history-table", DataTable)
            tbl.clear()
            for ts, rule, val in self._history[:20]:
                tbl.add_row(ts, rule, val)
        except Exception:
            pass

    def on_stats_updated(self, message: StatsUpdated) -> None:
        ram_pct = (message.ram_used_mb / message.ram_limit_mb * 100) if message.ram_limit_mb > 0 else 0
        self._check_rules("mc_cpu", message.cpu_pct)
        self._check_rules("mc_ram", ram_pct)

    def on_system_stats_updated(self, message: SystemStatsUpdated) -> None:
        self._check_rules("sys_cpu", message.cpu_pct)
        self._check_rules("sys_ram", message.ram_pct)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "alr-add":
            await self._add_rule()
        elif bid == "alr-refresh":
            self._reload_rules()
        elif bid == "alr-delete":
            await self._delete_selected()

    async def _add_rule(self) -> None:
        try:
            name = self.query_one("#alr-name", Input).value.strip()
            if not name:
                self.app.notify("Ingresa un nombre para la regla", severity="warning")
                return
            metric = str(self.query_one("#alr-metric", Select).value)
            condition = str(self.query_one("#alr-condition", Select).value)
            threshold = float(self.query_one("#alr-threshold", Input).value or "90")
            severity = str(self.query_one("#alr-severity", Select).value)
            enabled = self.query_one("#alr-enabled", Switch).value

            rule = AlertRule(
                name=name, metric=metric, condition=condition,
                threshold=threshold, severity=severity, enabled=enabled
            )
            self._rules.append(rule)
            self._reload_rules()
            self.app.notify(f"Regla '{name}' agregada", severity="information")
        except ValueError:
            self.app.notify("El umbral debe ser un número", severity="error")
        except Exception as e:
            self.app.notify(str(e), severity="error")

    async def _delete_selected(self) -> None:
        try:
            tbl = self.query_one("#alerts-rules-table", DataTable)
            if tbl.cursor_row is None:
                return
            idx = tbl.cursor_row
            if idx < len(self._rules):
                name = self._rules[idx].name
                self._rules.pop(idx)
                self._reload_rules()
                self.app.notify(f"Regla '{name}' eliminada", severity="warning")
        except Exception:
            pass
