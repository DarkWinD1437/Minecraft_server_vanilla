from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Callable


@dataclass
class ScheduledTask:
    name: str
    task_type: str           # "restart", "backup", "command", "announce"
    schedule: str            # "daily@04:00", "interval@6h", "interval@30m"
    enabled: bool = True
    last_run: datetime | None = None
    next_run: datetime | None = None
    extra: dict = field(default_factory=dict)


class TaskEngine:
    def __init__(self) -> None:
        self._tasks: list[ScheduledTask] = []
        self._timers: dict[str, threading.Timer] = {}
        self._running = False
        self._callbacks: dict[str, Callable] = {}

    def register_callback(self, task_type: str, fn: Callable) -> None:
        self._callbacks[task_type] = fn

    def add_task(self, task: ScheduledTask) -> None:
        self._tasks.append(task)
        if self._running and task.enabled:
            self._schedule_task(task)

    def remove_task(self, name: str) -> None:
        self._tasks = [t for t in self._tasks if t.name != name]
        if name in self._timers:
            self._timers[name].cancel()
            del self._timers[name]

    def start(self) -> None:
        self._running = True
        for task in self._tasks:
            if task.enabled:
                self._schedule_task(task)

    def stop(self) -> None:
        self._running = False
        for timer in self._timers.values():
            timer.cancel()
        self._timers.clear()

    def _schedule_task(self, task: ScheduledTask) -> None:
        delay = self._seconds_until_next(task)
        task.next_run = datetime.now()

        def _fire():
            if not self._running or not task.enabled:
                return
            task.last_run = datetime.now()
            fn = self._callbacks.get(task.task_type)
            if fn:
                try:
                    fn(task)
                except Exception:
                    pass
            # Re-schedule
            self._schedule_task(task)

        if task.name in self._timers:
            self._timers[task.name].cancel()
        t = threading.Timer(delay, _fire)
        t.daemon = True
        t.start()
        self._timers[task.name] = t

    def _seconds_until_next(self, task: ScheduledTask) -> float:
        schedule = task.schedule
        if schedule.startswith("interval@"):
            val = schedule[9:]
            if val.endswith("h"):
                return float(val[:-1]) * 3600
            if val.endswith("m"):
                return float(val[:-1]) * 60
            return float(val)
        if schedule.startswith("daily@"):
            target_str = schedule[6:]
            try:
                h, m = map(int, target_str.split(":"))
                now = datetime.now()
                target = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if target <= now:
                    target = target.replace(day=target.day + 1)
                return (target - now).total_seconds()
            except Exception:
                return 3600
        return 3600

    @property
    def tasks(self) -> list[ScheduledTask]:
        return list(self._tasks)


# Module-level singleton
engine = TaskEngine()
