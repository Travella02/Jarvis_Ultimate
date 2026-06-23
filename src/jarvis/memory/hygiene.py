"""Sensitive-data redaction and runtime file hygiene for Jarvis memory.

0.3.6 keeps passwords, account numbers, API keys, and similar values out of
normal chat archives, memory candidates, UI snapshots, and JSONL logs.  This
module is local-only and dependency-free so it can run during installation, in
unit tests, or from a future maintenance command without requiring Jarvis to
restart.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from jarvis.memory.secure_vault import redact_sensitive_payload, redact_sensitive_text, redaction_happened


@dataclass(slots=True)
class RedactionHygieneResult:
    """Summary of a redaction pass over local runtime files."""

    scanned_files: int = 0
    updated_files: int = 0
    redacted_items: int = 0
    errors: list[str] = field(default_factory=list)

    def merge(self, other: "RedactionHygieneResult") -> None:
        self.scanned_files += other.scanned_files
        self.updated_files += other.updated_files
        self.redacted_items += other.redacted_items
        self.errors.extend(other.errors)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_RUNTIME_PATTERNS: tuple[str, ...] = (
    "data/memory/chat_archive/**/*.jsonl",
    "data/memory/*.json",
    "data/conversations/**/*.json",
    "data/conversations/**/*.jsonl",
    "logs/**/*.jsonl",
    "logs/**/*.json",
)


def redact_sensitive_runtime_files(project_root: str | Path = ".", *, patterns: Iterable[str] | None = None) -> RedactionHygieneResult:
    """Redact sensitive values from already-written local runtime files.

    The normal forward path redacts before writing.  This function exists for
    upgrades: if a previous version wrote a fake/test password or real secret
    into chat archives or logs, this can clean the local files in-place.
    """

    root = Path(project_root)
    result = RedactionHygieneResult()
    seen: set[Path] = set()
    for pattern in patterns or DEFAULT_RUNTIME_PATTERNS:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            if path.suffix.lower() == ".jsonl":
                result.merge(_redact_jsonl_file(path))
            elif path.suffix.lower() == ".json":
                result.merge(_redact_json_file(path))
    return result


def _redact_json_file(path: Path) -> RedactionHygieneResult:
    result = RedactionHygieneResult(scanned_files=1)
    try:
        raw = path.read_text(encoding="utf-8")
        if not raw.strip():
            return result
        payload = json.loads(raw)
        redacted = redact_sensitive_payload(payload)
        if redaction_happened(payload, redacted):
            path.write_text(json.dumps(redacted, indent=2, ensure_ascii=False), encoding="utf-8")
            result.updated_files = 1
            result.redacted_items = 1
    except Exception as exc:  # pragma: no cover - defensive migration boundary
        result.errors.append(f"{path}: {exc}")
    return result


def _redact_jsonl_file(path: Path) -> RedactionHygieneResult:
    result = RedactionHygieneResult(scanned_files=1)
    try:
        original_lines = path.read_text(encoding="utf-8").splitlines()
        new_lines: list[str] = []
        changed = False
        redacted_count = 0
        for line in original_lines:
            if not line.strip():
                new_lines.append(line)
                continue
            try:
                payload = json.loads(line)
                redacted = redact_sensitive_payload(payload)
                if redaction_happened(payload, redacted):
                    changed = True
                    redacted_count += 1
                new_lines.append(json.dumps(redacted, ensure_ascii=False, default=str))
            except json.JSONDecodeError:
                redacted_line = redact_sensitive_text(line, max_chars=max(len(line), 120))
                if redacted_line != line:
                    changed = True
                    redacted_count += 1
                new_lines.append(redacted_line)
        if changed:
            path.write_text("\n".join(new_lines) + ("\n" if original_lines else ""), encoding="utf-8")
            result.updated_files = 1
            result.redacted_items = redacted_count
    except Exception as exc:  # pragma: no cover - defensive migration boundary
        result.errors.append(f"{path}: {exc}")
    return result
