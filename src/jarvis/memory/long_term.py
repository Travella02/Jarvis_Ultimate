"""Persistent long-term memory store for Jarvis.

Long-term memory is intentionally explicit and local-first in this milestone.
Jarvis only saves durable facts/preferences when the user asks it to remember
something.  The store is a small JSON document so it is easy to inspect,
backup, delete, or migrate before we add embeddings/vector search later.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()




def _token_variants(tokens: Iterable[str]) -> set[str]:
    expanded: set[str] = set()
    for token in tokens:
        token = str(token).strip()
        if not token:
            continue
        expanded.add(token)
        if len(token) > 4 and token.endswith("es"):
            expanded.add(token[:-2])
        if len(token) > 3 and token.endswith("s"):
            expanded.add(token[:-1])
    return expanded

def normalize_memory_text(value: str) -> str:
    """Normalize memory text for duplicate detection and simple matching."""

    cleaned = re.sub(r"[^a-z0-9\s]", " ", str(value or "").lower())
    return " ".join(cleaned.split())


@dataclass(slots=True)
class LongTermMemoryRecord:
    """One durable memory item saved by the user or a trusted Jarvis action."""

    text: str
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    source: str = "user"
    importance: int = 3
    id: str = field(default_factory=lambda: f"mem_{uuid4().hex[:12]}")
    created_at: str = field(default_factory=_utc_now_iso)
    updated_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_text(self) -> str:
        return normalize_memory_text(self.text)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "LongTermMemoryRecord | None":
        text = str(item.get("text") or "").strip()
        if not text:
            return None
        tags_raw = item.get("tags")
        tags = [str(tag).strip().lower() for tag in tags_raw if str(tag).strip()] if isinstance(tags_raw, list) else []
        try:
            importance = int(item.get("importance", 3))
        except (TypeError, ValueError):
            importance = 3
        return cls(
            id=str(item.get("id") or f"mem_{uuid4().hex[:12]}"),
            text=text,
            category=str(item.get("category") or "general").strip().lower() or "general",
            tags=tags,
            source=str(item.get("source") or "user"),
            importance=max(1, min(5, importance)),
            created_at=str(item.get("created_at") or _utc_now_iso()),
            updated_at=str(item.get("updated_at") or item.get("created_at") or _utc_now_iso()),
            metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
        )


@dataclass(slots=True)
class MemorySearchResult:
    """Scored search match for a long-term memory record."""

    record: LongTermMemoryRecord
    score: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        data = self.record.to_dict()
        data["score"] = self.score
        data["reason"] = self.reason
        return data


class LongTermMemoryStore:
    """Small local JSON-backed long-term memory store."""

    schema_version = 1

    def __init__(
        self,
        *,
        enabled: bool = True,
        path: str | Path | None = None,
        max_records: int = 500,
        inject_limit: int = 5,
    ) -> None:
        self.enabled = bool(enabled)
        self.path = Path(path) if path else Path("data/memory/long_term_memory.json")
        self.max_records = max(10, int(max_records))
        self.inject_limit = max(0, int(inject_limit))
        self._records: list[LongTermMemoryRecord] = []
        self.load()

    @property
    def records(self) -> tuple[LongTermMemoryRecord, ...]:
        return tuple(self._records)

    def add(
        self,
        text: str,
        *,
        category: str = "general",
        tags: Iterable[str] | None = None,
        source: str = "user",
        importance: int = 3,
        metadata: dict[str, Any] | None = None,
    ) -> LongTermMemoryRecord | None:
        """Add or update one durable memory record."""

        if not self.enabled:
            return None
        cleaned_text = " ".join(str(text or "").strip().split())
        if not cleaned_text:
            return None

        normalized = normalize_memory_text(cleaned_text)
        now = _utc_now_iso()
        tag_list = self._normalize_tags(tags or [])
        category_text = str(category or "general").strip().lower() or "general"

        existing = self._find_duplicate(normalized)
        if existing is not None:
            existing.text = cleaned_text
            existing.category = category_text
            existing.tags = sorted(set([*existing.tags, *tag_list]))
            existing.source = source
            existing.importance = max(existing.importance, max(1, min(5, int(importance))))
            existing.updated_at = now
            existing.metadata.update(metadata or {})
            self.save()
            return existing

        record = LongTermMemoryRecord(
            text=cleaned_text,
            category=category_text,
            tags=tag_list,
            source=source,
            importance=max(1, min(5, int(importance))),
            metadata=dict(metadata or {}),
        )
        self._records.append(record)
        self._trim()
        self.save()
        return record

    def search(self, query: str, *, limit: int = 5) -> list[MemorySearchResult]:
        """Search memories using deterministic token/substring scoring."""

        if not self.enabled:
            return []
        normalized_query = normalize_memory_text(query)
        if not normalized_query:
            return []
        base_query_tokens = set(normalized_query.split())
        query_tokens = _token_variants(base_query_tokens)
        results: list[MemorySearchResult] = []
        for record in self._records:
            normalized_record = record.normalized_text
            base_record_tokens = set(normalized_record.split())
            record_tokens = _token_variants(base_record_tokens)
            tag_tokens = set(token for tag in record.tags for token in normalize_memory_text(tag).split())
            category_tokens = set(normalize_memory_text(record.category).split())
            combined_tokens = record_tokens | tag_tokens | category_tokens
            score = 0.0
            reasons: list[str] = []
            if normalized_query in normalized_record:
                score += 2.0
                reasons.append("text contains query")
            if normalized_record and normalized_record in normalized_query:
                score += 1.25
                reasons.append("query contains saved memory")
            overlap = query_tokens & combined_tokens
            if overlap:
                score += len(overlap) / max(len(query_tokens), 1)
                reasons.append("token overlap: " + ", ".join(sorted(overlap)))
            if query_tokens & tag_tokens:
                score += 0.6
                reasons.append("tag match")
            if query_tokens & category_tokens:
                score += 0.4
                reasons.append("category match")
            if score > 0:
                # Importance is a tiny tie-breaker, not a replacement for relevance.
                score += record.importance * 0.03
                results.append(MemorySearchResult(record=record, score=round(score, 3), reason="; ".join(reasons)))
        results.sort(key=lambda item: (item.score, item.record.updated_at), reverse=True)
        return results[: max(1, int(limit))]

    def relevant_context(self, query: str, *, limit: int | None = None) -> str:
        """Return a compact LLM-ready block of relevant saved memories."""

        selected_limit = self.inject_limit if limit is None else int(limit)
        if selected_limit <= 0:
            return ""
        results = self.search(query, limit=selected_limit)
        if not results:
            return ""
        lines = ["Relevant saved memories:"]
        for result in results:
            lines.append(f"- {result.record.text}")
        return "\n".join(lines)

    def forget(self, query: str, *, limit: int | None = None) -> list[LongTermMemoryRecord]:
        """Remove memories matching a query and return removed records."""

        if not self.enabled:
            return []
        text = str(query or "").strip()
        if not text:
            return []
        normalized_query = normalize_memory_text(text)
        base_query_tokens = set(normalized_query.split())
        query_tokens = _token_variants(base_query_tokens)
        removed: list[LongTermMemoryRecord] = []
        kept: list[LongTermMemoryRecord] = []
        max_remove = len(self._records) if limit is None else max(1, int(limit))
        for record in self._records:
            should_remove = False
            if text == record.id:
                should_remove = True
            elif normalized_query and normalized_query in record.normalized_text:
                should_remove = True
            elif query_tokens and query_tokens <= (set(record.normalized_text.split()) | set(record.tags) | {record.category}):
                should_remove = True
            if should_remove and len(removed) < max_remove:
                removed.append(record)
            else:
                kept.append(record)
        if removed:
            self._records = kept
            self.save()
        return removed

    def clear(self) -> int:
        """Clear all long-term memory records."""

        count = len(self._records)
        self._records.clear()
        self.save()
        return count

    def status(self) -> dict[str, Any]:
        categories: dict[str, int] = {}
        for record in self._records:
            categories[record.category] = categories.get(record.category, 0) + 1
        return {
            "enabled": self.enabled,
            "records": len(self._records),
            "max_records": self.max_records,
            "inject_limit": self.inject_limit,
            "path": str(self.path),
            "categories": dict(sorted(categories.items())),
        }

    def format_status(self) -> str:
        info = self.status()
        state = "enabled" if info["enabled"] else "disabled"
        lines = [
            "Long-term memory status:",
            f"Memory is {state}, sir. I currently have {info['records']} of {info['max_records']} possible long-term memories saved.",
            f"I can inject up to {info['inject_limit']} relevant memories into a conversation when they match what we are talking about.",
            f"Memory file: {info['path']}",
        ]
        if info["categories"]:
            categories = ", ".join(f"{name}: {count}" for name, count in info["categories"].items())
            lines.append(f"Categories: {categories}.")
        return "\n".join(lines)

    def format_records(self, *, limit: int = 10, query: str = "") -> str:
        if query:
            results = self.search(query, limit=limit)
            if not results:
                return f"I do not have anything saved about {self._friendly_query(query)} yet, sir."
            return self._format_human_records([item.record for item in results], query=query)

        records = list(self._records[-max(1, int(limit)) :])
        if not records:
            return "I do not have any long-term memories saved yet, sir."
        return self._format_human_records(records)

    def _format_human_records(self, records: list[LongTermMemoryRecord], *, query: str = "") -> str:
        cleaned_records = [self._human_memory_text(record.text) for record in records if str(record.text or "").strip()]
        if not cleaned_records:
            if query:
                return f"I do not have anything saved about {self._friendly_query(query)} yet, sir."
            return "I do not have any long-term memories saved yet, sir."
        if len(cleaned_records) == 1:
            return f"I remember that {cleaned_records[0]}, sir."

        intro = "I remember a few things, sir:"
        lines = [intro]
        for item in cleaned_records:
            lines.append(f"- {item}")
        return "\n".join(lines)

    def _friendly_query(self, query: str) -> str:
        cleaned = " ".join(str(query or "").strip().strip(" .?!").split())
        return cleaned or "that"

    def _human_memory_text(self, text: str) -> str:
        cleaned = " ".join(str(text or "").strip().strip(" .?!").split())
        if not cleaned:
            return "that"

        # Memories are often saved from the user's first-person wording
        # ("my favorite color is blue"). When Jarvis repeats them back,
        # convert the most common first-person phrases so the response feels
        # like a real assistant rather than a database dump.
        replacements = [
            (r"\bmy\b", "your"),
            (r"\bmine\b", "yours"),
            (r"\bi am\b", "you are"),
            (r"\bi'm\b", "you're"),
            (r"\bi like\b", "you like"),
            (r"\bi prefer\b", "you prefer"),
            (r"\bi want\b", "you want"),
            (r"\bi need\b", "you need"),
            (r"\bi have\b", "you have"),
        ]
        friendly = cleaned
        for pattern, replacement in replacements:
            friendly = re.sub(pattern, replacement, friendly, flags=re.IGNORECASE)
        friendly = friendly[:1].lower() + friendly[1:] if friendly else friendly
        return friendly

    def save(self) -> None:
        if not self.enabled:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.schema_version,
            "saved_at": _utc_now_iso(),
            "records": [record.to_dict() for record in self._records],
        }
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(self.path)

    def load(self) -> None:
        if not self.enabled or not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._records = []
            return
        records: list[LongTermMemoryRecord] = []
        for item in payload.get("records", []):
            if not isinstance(item, dict):
                continue
            record = LongTermMemoryRecord.from_dict(item)
            if record is not None:
                records.append(record)
        self._records = records
        self._trim()

    def _find_duplicate(self, normalized_text: str) -> LongTermMemoryRecord | None:
        for record in self._records:
            if record.normalized_text == normalized_text:
                return record
        return None

    def _trim(self) -> None:
        while len(self._records) > self.max_records:
            self._records.pop(0)

    def _normalize_tags(self, tags: Iterable[str]) -> list[str]:
        normalized: list[str] = []
        for tag in tags:
            tag_text = normalize_memory_text(str(tag)).replace(" ", "_")
            if tag_text and tag_text not in normalized:
                normalized.append(tag_text)
        return normalized
