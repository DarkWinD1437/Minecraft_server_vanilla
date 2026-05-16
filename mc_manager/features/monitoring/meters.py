from __future__ import annotations

from collections import deque

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Label, Sparkline, ProgressBar
from textual.widget import Widget
from textual.containers import Horizontal, Vertical


class SparklineCard(Widget):
    """A titled sparkline widget with current value display."""

    DEFAULT_CSS = """
    SparklineCard {
        height: 10;
        border: solid $primary-darken-2;
        background: $panel;
        padding: 0 1;
        margin-right: 1;
    }
    SparklineCard .sc-title {
        text-style: bold;
        color: $text-muted;
    }
    SparklineCard .sc-value {
        color: $accent;
        text-style: bold;
    }
    SparklineCard .sc-minmax {
        color: $text-muted;
        text-style: italic;
    }
    SparklineCard Sparkline {
        height: 5;
    }
    """

    current: reactive[float] = reactive(0.0)

    def __init__(
        self,
        title: str,
        unit: str = "%",
        max_points: int = 60,
        color: str = "green",
        extra_css_class: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._unit = unit
        self._max_points = max_points
        self._color = color
        self._data: deque[float] = deque([0.0] * max_points, maxlen=max_points)
        self._extra_css = extra_css_class

    def compose(self) -> ComposeResult:
        yield Label(self._title, classes="sc-title")
        yield Sparkline(list(self._data), id=f"spark-{self.id or 'x'}", classes=f"sc-spark {self._extra_css}")
        yield Label("0.0", classes="sc-value", id=f"val-{self.id or 'x'}")
        yield Label("min: 0  max: 0", classes="sc-minmax", id=f"mm-{self.id or 'x'}")

    def push(self, value: float) -> None:
        self._data.append(value)
        self.current = value
        data_list = list(self._data)

        try:
            self.query_one(Sparkline).data = data_list
        except Exception:
            pass

        try:
            self.query_one(f"#val-{self.id or 'x'}", Label).update(
                f"{value:.1f} {self._unit}"
            )
        except Exception:
            pass

        min_v = min(data_list)
        max_v = max(data_list)
        try:
            self.query_one(f"#mm-{self.id or 'x'}", Label).update(
                f"min: {min_v:.1f}  max: {max_v:.1f}"
            )
        except Exception:
            pass


class MeterBar(Widget):
    """Horizontal progress bar with label and percentage."""

    DEFAULT_CSS = """
    MeterBar {
        height: 2;
        margin-bottom: 1;
    }
    MeterBar .mb-row {
        layout: horizontal;
        height: 1;
        align: left middle;
    }
    MeterBar .mb-label {
        width: 14;
        color: $text-muted;
    }
    MeterBar .mb-bar {
        width: 1fr;
        height: 1;
    }
    MeterBar .mb-value {
        width: 10;
        text-align: right;
        color: $accent;
    }
    """

    def __init__(self, label: str, total: float = 100.0, **kwargs) -> None:
        super().__init__(**kwargs)
        self._label = label
        self._total = total
        self._value = 0.0

    def compose(self) -> ComposeResult:
        with Horizontal(classes="mb-row"):
            yield Label(self._label, classes="mb-label")
            yield ProgressBar(total=self._total, show_eta=False, show_percentage=False, classes="mb-bar", id=f"bar-{self.id or 'mb'}")
            yield Label("0%", classes="mb-value", id=f"barval-{self.id or 'mb'}")

    def set_value(self, value: float, total: float | None = None) -> None:
        if total is not None:
            self._total = total
        self._value = value
        try:
            bar = self.query_one(ProgressBar)
            bar.total = self._total
            bar.progress = value
        except Exception:
            pass
        try:
            pct = (value / self._total * 100) if self._total else 0
            self.query_one(f"#barval-{self.id or 'mb'}", Label).update(f"{pct:.1f}%")
        except Exception:
            pass


class IOCard(Widget):
    """Shows two sparklines for read/write or in/out IO."""

    DEFAULT_CSS = """
    IOCard {
        height: 12;
        border: solid $primary-darken-2;
        background: $panel;
        padding: 0 1;
        margin-right: 1;
    }
    IOCard .io-title {
        text-style: bold;
        color: $text-muted;
    }
    """

    def __init__(self, title: str, label_a: str = "↑ In", label_b: str = "↓ Out", unit: str = "KB/s", **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._label_a = label_a
        self._label_b = label_b
        self._unit = unit

    def compose(self) -> ComposeResult:
        yield Label(self._title, classes="io-title")
        yield SparklineCard(self._label_a, unit=self._unit, max_points=60, id=f"{self.id}-in" if self.id else "io-in")
        yield SparklineCard(self._label_b, unit=self._unit, max_points=60, id=f"{self.id}-out" if self.id else "io-out")

    def push(self, value_a: float, value_b: float) -> None:
        try:
            cards = self.query(SparklineCard)
            cards_list = list(cards)
            if len(cards_list) >= 2:
                cards_list[0].push(value_a)
                cards_list[1].push(value_b)
        except Exception:
            pass
