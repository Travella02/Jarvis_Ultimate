"""Basic permission checks for Jarvis 3."""

from __future__ import annotations


class PermissionManager:
    """Small permission manager for early milestones."""

    def __init__(self, defaults: dict[str, str] | None = None) -> None:
        self.defaults = defaults or {}

    def default_for(self, permission: str) -> str:
        return self.defaults.get(permission, "ask")

    def is_allowed_without_confirmation(self, permission: str) -> bool:
        return self.default_for(permission) == "allow"
