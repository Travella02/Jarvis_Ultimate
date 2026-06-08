"""Prompts for the Conversation Agent."""

from __future__ import annotations

from typing import Literal


SYSTEM_PROMPT = """You are Jarvis, Tanner's local-first AI assistant.

Speak naturally and clearly. You are part of a modular assistant system with
a central brain, specialized agents, tools, providers, memory, events, and a
future visual avatar UI. For now, you can chat normally through the local LLM
provider, but many specialized tools are still being built.

Be honest about your current capabilities. Do not claim you opened apps,
read the screen, checked files, used email, or changed settings unless a
tool/agent result actually proves it happened. Keep answers helpful and not
too long unless Tanner asks for detail.
"""

MINIMAL_SYSTEM_PROMPT = """You are Jarvis, Tanner's local AI assistant. Reply naturally, concisely, and honestly."""

PromptMode = Literal["normal", "minimal", "off"]


def normalize_prompt_mode(mode: str | None) -> PromptMode:
    """Return a safe prompt mode for Jarvis conversation turns."""
    normalized = (mode or "normal").strip().lower().replace("-", "_")
    if normalized in {"minimal", "small", "short", "fast"}:
        return "minimal"
    if normalized in {"off", "none", "no_system", "disabled", "false", "0"}:
        return "off"
    return "normal"


def get_system_prompt(mode: str | None = "normal") -> str | None:
    """Return the configured system prompt, or None when disabled."""
    prompt_mode = normalize_prompt_mode(mode)
    if prompt_mode == "minimal":
        return MINIMAL_SYSTEM_PROMPT
    if prompt_mode == "off":
        return None
    return SYSTEM_PROMPT


def get_prompt_stats(mode: str | None = "normal") -> dict[str, int | str | bool]:
    """Return small prompt diagnostics for speed comparisons."""
    prompt_mode = normalize_prompt_mode(mode)
    prompt = get_system_prompt(prompt_mode) or ""
    return {
        "mode": prompt_mode,
        "enabled": bool(prompt),
        "chars": len(prompt),
        "words": len(prompt.split()),
        "lines": len(prompt.splitlines()) if prompt else 0,
    }
