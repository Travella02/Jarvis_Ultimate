"""Jarvis ability framework.

Abilities are the small, callable capabilities that live inside broader agents.
Agents remain the owning specialist modules, while this package gives Jarvis a
single registry for discovering, describing, routing, and displaying those
capabilities safely.
"""

from jarvis.abilities.registry import AbilityRecord, AbilityRegistry, AbilitySelection
from jarvis.abilities.permissions import AbilityPermissionDecision, AbilityPermissionPolicy

__all__ = [
    "AbilityRecord",
    "AbilityRegistry",
    "AbilitySelection",
    "AbilityPermissionDecision",
    "AbilityPermissionPolicy",
]
