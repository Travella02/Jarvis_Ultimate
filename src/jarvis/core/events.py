"""Jarvis event bus.

The event bus keeps the brain, agents, tools, logs, and future UI/avatar layer
loosely connected.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable

from jarvis.core.result import JarvisEvent

EventHandler = Callable[[JarvisEvent], None]


class EventBus:
    """Small synchronous event bus with history."""

    def __init__(self, *, history_limit: int = 500) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._wildcard_handlers: list[EventHandler] = []
        self._history: list[JarvisEvent] = []
        self._history_limit = history_limit

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to an event type. Use '*' for every event."""
        if event_type == "*":
            self._wildcard_handlers.append(handler)
            return
        self._handlers[event_type].append(handler)

    def emit(self, event_type: str, *, source: str = "system", message: str = "", data: dict | None = None) -> JarvisEvent:
        event = JarvisEvent(event_type=event_type, source=source, message=message, data=data or {})
        self._history.append(event)
        if len(self._history) > self._history_limit:
            self._history = self._history[-self._history_limit :]

        for handler in list(self._handlers.get(event_type, [])):
            handler(event)
        for handler in list(self._wildcard_handlers):
            handler(event)
        return event

    def history(self, *, limit: int | None = None) -> list[JarvisEvent]:
        if limit is None:
            return list(self._history)
        return list(self._history[-limit:])

    def clear(self) -> None:
        self._history.clear()
