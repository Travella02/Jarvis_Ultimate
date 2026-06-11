"""Lightweight view-model helpers for desktop UI rendering."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ChatLine:
    role: str
    text: str

    def display(self) -> str:
        prefix = "You" if self.role == "user" else "Jarvis"
        return f"{prefix}: {self.text}"


@dataclass(slots=True)
class StatusLine:
    label: str
    value: str

    def display(self) -> str:
        return f"{self.label}: {self.value}"
