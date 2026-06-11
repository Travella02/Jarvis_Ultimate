"""Simple wake-word detection foundation for Jarvis.

0.1.1 intentionally starts with dependency-free phrase detection over STT text.
This gives Jarvis a testable wake-word path before adding a continuous always-on
wake engine such as Porcupine, openWakeWord, or another provider later.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from jarvis.core.events import EventBus


_WORD_BOUNDARY_RE = re.compile(r"[^a-z0-9]+")


@dataclass(slots=True)
class WakeWordMatch:
    """Result of checking a transcript for a wake phrase."""

    detected: bool
    transcript: str
    wake_word: str = ""
    command: str = ""
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def has_command(self) -> bool:
        return bool(self.command.strip())


class WakeWordManager:
    """Configurable phrase wake-word manager.

    This manager does not keep the microphone open. It detects wake phrases from
    text that was already captured by STT. Continuous listening will build on the
    same interface in a later patch.
    """

    def __init__(self, config: Any, *, events: EventBus | None = None) -> None:
        self.config = config
        self.events = events or EventBus()
        self.enabled = bool(getattr(config, "wake_word_enabled", True))
        self.provider_name = _normalize_provider(getattr(config, "wake_word_provider", "phrase"))
        self.wake_words = _parse_wake_words(getattr(config, "wake_words", "hey jarvis,jarvis"))
        self.require_wake_word = bool(getattr(config, "wake_require_wake_word", True))
        self.strip_wake_word = bool(getattr(config, "wake_strip_wake_word", True))
        self.empty_response = str(getattr(config, "wake_empty_response", "Yes, sir?") or "Yes, sir?").strip()
        self.last_match: WakeWordMatch | None = None

    def status(self) -> str:
        """Return user-facing wake-word status."""
        lines = [
            "Wake-word status:",
            f"- enabled: {self.enabled}",
            f"- provider: {self.provider_name}",
            f"- wake words: {', '.join(self.wake_words) if self.wake_words else 'none'}",
            f"- require wake word: {self.require_wake_word}",
            f"- strip wake word before routing: {self.strip_wake_word}",
            f"- empty wake response: {self.empty_response}",
            "- mode: phrase detection over STT transcript",
            "- continuous wake listening: not implemented yet; use 'wake listen once' or 'wake voice once' for now",
        ]
        if self.last_match is not None:
            lines.extend(
                [
                    "Last wake check:",
                    f"- detected: {self.last_match.detected}",
                    f"- wake word: {self.last_match.wake_word or 'none'}",
                    f"- command: {self.last_match.command or 'none'}",
                    f"- transcript: {self.last_match.transcript or 'none'}",
                ]
            )
        return "\n".join(lines)

    def detect(self, transcript: str) -> WakeWordMatch:
        """Detect a configured wake phrase in a transcript."""
        text = str(transcript or "").strip()
        normalized = _normalize_text(text)
        if not self.enabled:
            match = WakeWordMatch(False, text, message="Wake-word detection is disabled.", data={"reason": "disabled"})
            self.last_match = match
            return match
        if not normalized:
            match = WakeWordMatch(False, text, message="No transcript text to check.", data={"reason": "empty"})
            self.last_match = match
            return match

        for wake_word in self.wake_words:
            wake_norm = _normalize_text(wake_word)
            if not wake_norm:
                continue
            command = _command_after_wake(normalized, wake_norm)
            if command is not None:
                routed_command = command if self.strip_wake_word else normalized
                message = "Wake word detected."
                if not routed_command:
                    message = "Wake word detected with no command."
                match = WakeWordMatch(
                    True,
                    text,
                    wake_word=wake_word,
                    command=routed_command.strip(),
                    message=message,
                    data={"normalized_transcript": normalized, "normalized_wake_word": wake_norm},
                )
                self.last_match = match
                self.events.emit(
                    "wake_word.detected",
                    source="wake_word_manager",
                    message=message,
                    data={"wake_word": wake_word, "command": routed_command.strip(), "transcript": text},
                )
                return match

        match = WakeWordMatch(False, text, message="Wake word not detected.", data={"normalized_transcript": normalized})
        self.last_match = match
        self.events.emit("wake_word.not_detected", source="wake_word_manager", message="Wake word not detected.", data={"transcript": text})
        return match

    def format_match(self, match: WakeWordMatch | None = None) -> str:
        """Format a wake detection result for CLI output."""
        item = match or self.last_match
        if item is None:
            return "No wake-word check has run yet."
        lines = [item.message or ("Wake word detected." if item.detected else "Wake word not detected.")]
        lines.append(f"Detected: {item.detected}")
        lines.append(f"Wake word: {item.wake_word or 'none'}")
        lines.append(f"Transcript: {item.transcript or 'none'}")
        lines.append(f"Command after wake word: {item.command or 'none'}")
        if item.detected and not item.command:
            lines.append(f"Empty wake response: {self.empty_response}")
        return "\n".join(lines)


def _normalize_provider(value: Any) -> str:
    text = str(value or "phrase").strip().lower().replace("-", "_")
    if text in {"simple", "text", "stt_phrase"}:
        return "phrase"
    return text or "phrase"


def _parse_wake_words(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        items = [str(item).strip() for item in value]
    else:
        items = [part.strip() for part in str(value or "").replace("|", ",").split(",")]
    result: list[str] = []
    for item in items:
        normalized = " ".join(item.lower().split())
        if normalized and normalized not in result:
            result.append(normalized)
    return result or ["hey jarvis", "jarvis"]


def _normalize_text(value: str) -> str:
    text = value.strip().lower()
    text = _WORD_BOUNDARY_RE.sub(" ", text)
    return " ".join(text.split())


def _command_after_wake(normalized_transcript: str, normalized_wake_word: str) -> str | None:
    """Return command after the wake phrase, or None if not detected.

    The first foundation intentionally favors wake words at the start of a
    transcript. It also accepts a short polite lead-in such as "okay hey jarvis".
    This avoids accidentally triggering on random mentions in the middle of a
    longer sentence.
    """
    if not normalized_transcript or not normalized_wake_word:
        return None

    if normalized_transcript == normalized_wake_word:
        return ""
    prefix = normalized_wake_word + " "
    if normalized_transcript.startswith(prefix):
        return normalized_transcript[len(prefix):].strip()

    lead_ins = ("okay ", "ok ", "hey ", "yo ")
    for lead in lead_ins:
        lead_phrase = lead + normalized_wake_word
        if normalized_transcript == lead_phrase:
            return ""
        lead_prefix = lead_phrase + " "
        if normalized_transcript.startswith(lead_prefix):
            return normalized_transcript[len(lead_prefix):].strip()

    return None
