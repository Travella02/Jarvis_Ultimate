"""Feature flags for Jarvis 3."""

from __future__ import annotations


class FeatureFlags:
    def __init__(self, flags: dict[str, bool] | None = None) -> None:
        self.flags = flags or {}

    def enabled(self, name: str) -> bool:
        return bool(self.flags.get(name, False))
