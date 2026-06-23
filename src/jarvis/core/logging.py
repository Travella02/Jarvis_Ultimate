"""Jarvis logging helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jarvis.core.result import utc_now_iso
from jarvis.memory.secure_vault import redact_sensitive_payload


def append_jsonl(path: str | Path, payload: dict[str, Any]) -> None:
    """Append a JSON line to a log file, creating folders if needed."""
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": utc_now_iso(), **redact_sensitive_payload(payload)}
    with log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")


class JarvisLogger:
    """Very small JSONL logger for early Jarvis 3 milestones."""

    def __init__(self, logs_dir: str | Path = "logs") -> None:
        self.logs_dir = Path(logs_dir)

    def log_event(self, event_type: str, *, source: str = "system", message: str = "", data: dict[str, Any] | None = None) -> None:
        append_jsonl(
            self.logs_dir / "brain" / "events.jsonl",
            {
                "event_type": event_type,
                "source": source,
                "message": message,
                "data": data or {},
            },
        )

    def log_result(self, result: Any) -> None:
        payload = result.to_dict() if hasattr(result, "to_dict") else {"result": str(result)}
        append_jsonl(self.logs_dir / "brain" / "results.jsonl", redact_sensitive_payload(payload))
