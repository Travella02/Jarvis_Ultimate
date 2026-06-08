"""Short-term conversation memory for Jarvis.

This module stores a bounded rolling window of recent user/assistant turns.
It is intentionally separate from long-term memory: short-term memory helps
Jarvis answer follow-up questions inside the current session without saving
personal facts forever.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class ConversationTurn:
    """One completed user/assistant exchange in short-term memory."""

    user: str
    assistant: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent_name: str = "conversation_agent"
    action: str = "llm_chat"
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        return len(self.user) + len(self.assistant)


class ShortTermMemory:
    """Bounded session memory for recent Jarvis conversation turns.

    The class is designed for an eventually always-running Jarvis process:
    memory never grows without bounds, and older turns are trimmed by both turn
    count and approximate character budget. Optional session persistence can be
    enabled later without changing the conversation-agent interface.
    """

    def __init__(
        self,
        *,
        enabled: bool = True,
        max_turns: int = 20,
        max_chars: int = 12_000,
        inject_last_turns: int = 8,
        persist_path: str | Path | None = None,
        autosave: bool = False,
        session_id: str | None = None,
    ) -> None:
        self.enabled = bool(enabled)
        self.max_turns = max(1, int(max_turns))
        self.max_chars = max(250, int(max_chars))
        self.inject_last_turns = max(0, int(inject_last_turns))
        self.persist_path = Path(persist_path) if persist_path else None
        self.autosave = bool(autosave and self.persist_path)
        self.session_id = session_id or f"session-{uuid4().hex[:12]}"
        self.started_at = datetime.now(timezone.utc).isoformat()
        self._turns: list[ConversationTurn] = []

        if self.autosave:
            self.load()

    @property
    def turns(self) -> tuple[ConversationTurn, ...]:
        """Return an immutable snapshot of stored turns."""
        return tuple(self._turns)

    def add_turn(
        self,
        *,
        user: str,
        assistant: str,
        agent_name: str = "conversation_agent",
        action: str = "llm_chat",
        success: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationTurn | None:
        """Store one completed exchange and trim the rolling memory window."""
        if not self.enabled:
            return None

        user_text = (user or "").strip()
        assistant_text = (assistant or "").strip()
        if not user_text or not assistant_text:
            return None

        turn = ConversationTurn(
            user=user_text,
            assistant=assistant_text,
            agent_name=agent_name,
            action=action,
            success=bool(success),
            metadata=dict(metadata or {}),
        )
        self._turns.append(turn)
        self._trim()
        self.save()
        return turn

    def recent_turns(self, limit: int | None = None) -> list[ConversationTurn]:
        """Return the most recent turns, oldest-to-newest."""
        if not self.enabled:
            return []
        if limit is None or limit <= 0:
            return list(self._turns)
        return list(self._turns[-int(limit) :])

    def to_llm_messages(self, *, limit: int | None = None) -> list[dict[str, str]]:
        """Convert recent turns to OpenAI-compatible chat messages."""
        if not self.enabled:
            return []
        selected_limit = self.inject_last_turns if limit is None else int(limit)
        if selected_limit <= 0:
            return []

        messages: list[dict[str, str]] = []
        for turn in self.recent_turns(selected_limit):
            messages.append({"role": "user", "content": turn.user})
            messages.append({"role": "assistant", "content": turn.assistant})
        return messages

    def clear(self) -> int:
        """Clear all stored short-term turns and return the number removed."""
        count = len(self._turns)
        self._turns.clear()
        if self.persist_path and self.persist_path.exists():
            self.persist_path.unlink()
        return count

    def status(self) -> dict[str, Any]:
        """Return summary information for diagnostics and UI panels."""
        total_chars = sum(turn.char_count for turn in self._turns)
        return {
            "enabled": self.enabled,
            "session_id": self.session_id,
            "started_at": self.started_at,
            "turns": len(self._turns),
            "max_turns": self.max_turns,
            "total_chars": total_chars,
            "max_chars": self.max_chars,
            "inject_last_turns": self.inject_last_turns,
            "autosave": self.autosave,
            "persist_path": str(self.persist_path) if self.persist_path else None,
        }

    def format_status(self) -> str:
        """Return a user-facing memory status block."""
        info = self.status()
        lines = [
            "Short-term memory status:",
            f"- enabled: {info['enabled']}",
            f"- session id: {info['session_id']}",
            f"- stored turns: {info['turns']} / {info['max_turns']}",
            f"- stored chars: {info['total_chars']} / {info['max_chars']}",
            f"- injected turns per LLM chat: {info['inject_last_turns']}",
            f"- autosave: {info['autosave']}",
        ]
        if info["persist_path"]:
            lines.append(f"- persist path: {info['persist_path']}")
        return "\n".join(lines)

    def format_last(self, limit: int = 5) -> str:
        """Return a readable view of recent memory turns."""
        turns = self.recent_turns(limit)
        if not turns:
            return "Short-term memory is empty."

        lines = [f"Last {len(turns)} short-term memory turn(s):"]
        start_index = len(self._turns) - len(turns) + 1
        for offset, turn in enumerate(turns):
            number = start_index + offset
            user_preview = self._preview(turn.user)
            assistant_preview = self._preview(turn.assistant)
            lines.append(f"{number}. You: {user_preview}")
            lines.append(f"   Jarvis: {assistant_preview}")
        return "\n".join(lines)

    def save(self) -> None:
        """Persist memory when autosave is enabled."""
        if not self.autosave or self.persist_path is None:
            return
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "turns": [asdict(turn) for turn in self._turns],
        }
        tmp_path = self.persist_path.with_suffix(self.persist_path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(self.persist_path)

    def load(self) -> None:
        """Load autosaved short-term memory if available."""
        if self.persist_path is None or not self.persist_path.exists():
            return
        try:
            payload = json.loads(self.persist_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        self.session_id = str(payload.get("session_id") or self.session_id)
        self.started_at = str(payload.get("started_at") or self.started_at)
        turns: list[ConversationTurn] = []
        for item in payload.get("turns", []):
            if not isinstance(item, dict):
                continue
            user = str(item.get("user") or "").strip()
            assistant = str(item.get("assistant") or "").strip()
            if not user or not assistant:
                continue
            metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            turns.append(
                ConversationTurn(
                    user=user,
                    assistant=assistant,
                    timestamp=str(item.get("timestamp") or datetime.now(timezone.utc).isoformat()),
                    agent_name=str(item.get("agent_name") or "conversation_agent"),
                    action=str(item.get("action") or "llm_chat"),
                    success=bool(item.get("success", True)),
                    metadata=metadata,
                )
            )
        self._turns = turns
        self._trim()

    def _trim(self) -> None:
        """Trim by max turns and approximate character budget."""
        while len(self._turns) > self.max_turns:
            self._turns.pop(0)
        while len(self._turns) > 1 and sum(turn.char_count for turn in self._turns) > self.max_chars:
            self._turns.pop(0)

    def _preview(self, text: str, *, limit: int = 120) -> str:
        compact = " ".join(text.split())
        if len(compact) <= limit:
            return compact
        return compact[: limit - 3] + "..."
