"""Permission policy for Jarvis abilities."""

from __future__ import annotations

from dataclasses import dataclass


SAFE_RISK_LEVELS = {"safe", "read_only"}
CONFIRM_RISK_LEVELS = {"confirm", "write", "external"}
BLOCKED_RISK_LEVELS = {"blocked", "dangerous"}


@dataclass(slots=True)
class AbilityPermissionDecision:
    """The safety decision for one ability/action request."""

    allowed: bool
    needs_confirmation: bool
    reason: str
    risk_level: str = "safe"

    @property
    def blocked(self) -> bool:
        return not self.allowed and not self.needs_confirmation


class AbilityPermissionPolicy:
    """Small permission guardrail used before tools become more powerful."""

    def evaluate(self, *, ability_name: str, risk_level: str = "safe", permissions: list[str] | tuple[str, ...] = ()) -> AbilityPermissionDecision:
        risk = str(risk_level or "safe").strip().lower()
        permission_set = {str(permission).strip().lower() for permission in permissions}

        if risk in BLOCKED_RISK_LEVELS or any(permission in {"dangerous", "system_destructive"} for permission in permission_set):
            return AbilityPermissionDecision(
                allowed=False,
                needs_confirmation=False,
                risk_level=risk,
                reason=f"{ability_name} is blocked because it is marked as a dangerous action.",
            )

        if risk in CONFIRM_RISK_LEVELS or permission_set.intersection({"file_write", "app_close", "process_kill", "network"}):
            return AbilityPermissionDecision(
                allowed=False,
                needs_confirmation=True,
                risk_level=risk,
                reason=f"{ability_name} needs confirmation before it can run.",
            )

        return AbilityPermissionDecision(
            allowed=True,
            needs_confirmation=False,
            risk_level=risk if risk in SAFE_RISK_LEVELS else "safe",
            reason=f"{ability_name} is allowed as a safe/read-only ability.",
        )
