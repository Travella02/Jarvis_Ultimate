"""Always-on memory tier helpers for Jarvis.

This module is intentionally local-first and dependency-free.  It gives Jarvis
memory structures that are safe for long-running sessions: records are written
incrementally, JSON documents are saved with atomic replacement, chat archives
are split by day, and lightweight maintenance can expire temporary records
without relying on a restart.
"""

from __future__ import annotations

import json
import re
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_text(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", str(value or "").lower())
    return " ".join(cleaned.split())


def token_variants(tokens: Iterable[str]) -> set[str]:
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


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a JSON document with temp-file replacement.

    This protects memory files from partial writes if Jarvis crashes or the
    machine loses power in the middle of a save.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def _normalize_tags(tags: Iterable[str]) -> list[str]:
    return sorted({normalize_text(tag) for tag in tags if normalize_text(tag)})


@dataclass(slots=True)
class ShortTermFactRecord:
    """One temporary memory that can expire after a few days."""

    text: str
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    source: str = "user"
    importance: int = 2
    expires_at: str = field(default_factory=lambda: (utc_now() + timedelta(days=3)).isoformat())
    id: str = field(default_factory=lambda: f"stm_{uuid4().hex[:12]}")
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_text(self) -> str:
        return normalize_text(self.text)

    def is_expired(self, now: datetime | None = None) -> bool:
        expires = parse_iso_datetime(self.expires_at)
        if expires is None:
            return False
        return expires <= (now or utc_now())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "ShortTermFactRecord | None":
        text = str(item.get("text") or "").strip()
        if not text:
            return None
        try:
            importance = int(item.get("importance", 2))
        except (TypeError, ValueError):
            importance = 2
        tags_raw = item.get("tags")
        tags = _normalize_tags(tags_raw if isinstance(tags_raw, list) else [])
        return cls(
            id=str(item.get("id") or f"stm_{uuid4().hex[:12]}"),
            text=text,
            category=str(item.get("category") or "general").strip().lower() or "general",
            tags=tags,
            source=str(item.get("source") or "user"),
            importance=max(1, min(5, importance)),
            expires_at=str(item.get("expires_at") or (utc_now() + timedelta(days=3)).isoformat()),
            created_at=str(item.get("created_at") or utc_now_iso()),
            updated_at=str(item.get("updated_at") or item.get("created_at") or utc_now_iso()),
            metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
        )


@dataclass(slots=True)
class MemoryMatch:
    record: Any
    score: float
    reason: str
    tier: str

    def to_dict(self) -> dict[str, Any]:
        if hasattr(self.record, "to_dict"):
            data = self.record.to_dict()
        else:
            data = dict(self.record)
        data["score"] = self.score
        data["reason"] = self.reason
        data["tier"] = self.tier
        return data


class ShortTermFactStore:
    """A few-days memory tier for useful but not permanent facts."""

    schema_version = 1

    def __init__(
        self,
        *,
        enabled: bool = True,
        path: str | Path | None = None,
        max_records: int = 300,
        default_days: int = 3,
        inject_limit: int = 3,
    ) -> None:
        self.enabled = bool(enabled)
        self.path = Path(path) if path else Path("data/memory/short_term_memory.json")
        self.max_records = max(10, int(max_records))
        self.default_days = max(1, int(default_days))
        self.inject_limit = max(0, int(inject_limit))
        self._records: list[ShortTermFactRecord] = []
        self.last_expired_count = 0
        self.load()

    @property
    def records(self) -> tuple[ShortTermFactRecord, ...]:
        self.expire_old(save=False)
        return tuple(self._records)

    def add(
        self,
        text: str,
        *,
        category: str = "general",
        tags: Iterable[str] | None = None,
        source: str = "user",
        importance: int = 2,
        days: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ShortTermFactRecord | None:
        if not self.enabled:
            return None
        cleaned_text = " ".join(str(text or "").strip().split())
        if not cleaned_text:
            return None
        self.expire_old(save=False)
        normalized = normalize_text(cleaned_text)
        tag_list = _normalize_tags(tags or [])
        now = utc_now_iso()
        expires_at = (utc_now() + timedelta(days=max(1, int(days or self.default_days)))).isoformat()
        existing = self._find_duplicate(normalized)
        if existing is not None:
            existing.text = cleaned_text
            existing.category = str(category or "general").strip().lower() or "general"
            existing.tags = sorted(set([*existing.tags, *tag_list]))
            existing.source = source
            existing.importance = max(existing.importance, max(1, min(5, int(importance))))
            existing.expires_at = expires_at
            existing.updated_at = now
            existing.metadata.update(metadata or {})
            self.save()
            return existing
        record = ShortTermFactRecord(
            text=cleaned_text,
            category=str(category or "general").strip().lower() or "general",
            tags=tag_list,
            source=source,
            importance=max(1, min(5, int(importance))),
            expires_at=expires_at,
            metadata=dict(metadata or {}),
        )
        self._records.append(record)
        self._trim()
        self.save()
        return record

    def search(self, query: str, *, limit: int = 5) -> list[MemoryMatch]:
        if not self.enabled:
            return []
        self.expire_old(save=True)
        normalized_query = normalize_text(query)
        if not normalized_query:
            return []
        query_tokens = token_variants(normalized_query.split())
        results: list[MemoryMatch] = []
        for record in self._records:
            score, reason = self._score(record, normalized_query, query_tokens)
            if score > 0:
                results.append(MemoryMatch(record=record, score=round(score, 3), reason=reason, tier="short_term"))
        results.sort(key=lambda item: (item.score, getattr(item.record, "updated_at", "")), reverse=True)
        return results[: max(1, int(limit))]

    def relevant_context(self, query: str, *, limit: int | None = None) -> str:
        selected_limit = self.inject_limit if limit is None else int(limit)
        if selected_limit <= 0:
            return ""
        results = self.search(query, limit=selected_limit)
        if not results:
            return ""
        lines = ["Relevant temporary memories:"]
        for result in results:
            lines.append(f"- {result.record.text}")
        return "\n".join(lines)

    def format_records(self, *, query: str = "", limit: int = 10) -> str:
        if query:
            results = self.search(query, limit=limit)
            if not results:
                return f"I do not have any temporary memories about {query}, sir."
            if len(results) == 1:
                return f"I temporarily remember that {self._for_user(results[0].record.text)}, sir."
            lines = [f"I found {len(results)} temporary memories about {query}, sir:"]
            lines.extend(f"- {self._for_user(item.record.text)}" for item in results)
            return "\n".join(lines)
        records = list(self.records)[-limit:]
        if not records:
            return "I do not have any temporary memories saved right now, sir."
        lines = [f"I have {len(records)} recent temporary memory item(s), sir:"]
        lines.extend(f"- {self._for_user(record.text)}" for record in records)
        return "\n".join(lines)

    def forget(self, query: str, *, limit: int | None = None) -> list[ShortTermFactRecord]:
        if not self.enabled:
            return []
        normalized_query = normalize_text(query)
        if not normalized_query:
            return []
        query_tokens = token_variants(normalized_query.split())
        removed: list[ShortTermFactRecord] = []
        kept: list[ShortTermFactRecord] = []
        max_remove = len(self._records) if limit is None else max(1, int(limit))
        for record in self._records:
            score, _ = self._score(record, normalized_query, query_tokens)
            if (record.id == query or score >= 0.9) and len(removed) < max_remove:
                removed.append(record)
            else:
                kept.append(record)
        if removed:
            self._records = kept
            self.save()
        return removed

    def expire_old(self, *, save: bool = True) -> int:
        now = utc_now()
        before = len(self._records)
        self._records = [record for record in self._records if not record.is_expired(now)]
        removed = before - len(self._records)
        self.last_expired_count = removed
        if removed and save:
            self.save()
        return removed

    def clear(self) -> int:
        count = len(self._records)
        self._records.clear()
        self.save()
        return count

    def status(self) -> dict[str, Any]:
        self.expire_old(save=True)
        return {
            "enabled": self.enabled,
            "records": len(self._records),
            "max_records": self.max_records,
            "default_days": self.default_days,
            "inject_limit": self.inject_limit,
            "path": str(self.path),
            "last_expired_count": self.last_expired_count,
        }

    def format_status(self) -> str:
        info = self.status()
        return "\n".join(
            [
                "Short-term fact memory status:",
                f"- enabled: {info['enabled']}",
                f"- saved temporary memories: {info['records']} / {info['max_records']}",
                f"- default lifetime: {info['default_days']} day(s)",
                f"- injected temporary memories: {info['inject_limit']}",
                f"- path: {info['path']}",
            ]
        )

    def save(self) -> None:
        if not self.enabled:
            return
        payload = {
            "schema_version": self.schema_version,
            "updated_at": utc_now_iso(),
            "records": [record.to_dict() for record in self._records],
        }
        atomic_write_json(self.path, payload)

    def load(self) -> None:
        if not self.path.exists():
            self._records = []
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._records = []
            return
        loaded: list[ShortTermFactRecord] = []
        for item in payload.get("records", []):
            if not isinstance(item, dict):
                continue
            record = ShortTermFactRecord.from_dict(item)
            if record is not None and not record.is_expired():
                loaded.append(record)
        self._records = loaded
        self._trim()

    def _find_duplicate(self, normalized: str) -> ShortTermFactRecord | None:
        for record in self._records:
            if record.normalized_text == normalized:
                return record
        return None

    def _trim(self) -> None:
        while len(self._records) > self.max_records:
            self._records.pop(0)

    def _score(self, record: ShortTermFactRecord, normalized_query: str, query_tokens: set[str]) -> tuple[float, str]:
        normalized_record = record.normalized_text
        record_tokens = token_variants(normalized_record.split())
        tag_tokens = set(token for tag in record.tags for token in normalize_text(tag).split())
        category_tokens = set(normalize_text(record.category).split())
        combined_tokens = record_tokens | tag_tokens | category_tokens
        score = 0.0
        reasons: list[str] = []
        if normalized_query in normalized_record:
            score += 2.0
            reasons.append("text contains query")
        if normalized_record and normalized_record in normalized_query:
            score += 1.25
            reasons.append("query contains memory")
        overlap = query_tokens & combined_tokens
        if overlap:
            score += len(overlap) / max(len(query_tokens), 1)
            reasons.append("token overlap")
        if query_tokens & tag_tokens:
            score += 0.6
            reasons.append("tag match")
        if query_tokens & category_tokens:
            score += 0.4
            reasons.append("category match")
        if score > 0:
            score += record.importance * 0.02
        return score, "; ".join(reasons)

    @staticmethod
    def _for_user(text: str) -> str:
        cleaned = str(text or "").strip()
        replacements = [
            (r"\bmy\b", "your"),
            (r"\bi am\b", "you are"),
            (r"\bi'm\b", "you are"),
            (r"\bme\b", "you"),
        ]
        for pattern, replacement in replacements:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        return cleaned


@dataclass(slots=True)
class ChatArchiveRecord:
    """One archived user/Jarvis turn."""

    user: str
    assistant: str
    session_id: str = "unknown"
    agent_name: str = "conversation_agent"
    action: str = "llm_chat"
    success: bool = True
    id: str = field(default_factory=lambda: f"chat_{uuid4().hex[:12]}")
    timestamp: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_text(self) -> str:
        return normalize_text(f"{self.user} {self.assistant}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "ChatArchiveRecord | None":
        user = str(item.get("user") or "").strip()
        assistant = str(item.get("assistant") or "").strip()
        if not user and not assistant:
            return None
        return cls(
            id=str(item.get("id") or f"chat_{uuid4().hex[:12]}"),
            user=user,
            assistant=assistant,
            session_id=str(item.get("session_id") or "unknown"),
            agent_name=str(item.get("agent_name") or "conversation_agent"),
            action=str(item.get("action") or "llm_chat"),
            success=bool(item.get("success", True)),
            timestamp=str(item.get("timestamp") or utc_now_iso()),
            metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
        )


class ChatArchiveStore:
    """Daily JSONL chat archive for searchable conversation history."""

    schema_version = 1

    def __init__(
        self,
        *,
        enabled: bool = True,
        root_dir: str | Path | None = None,
        max_search_days: int = 30,
        max_results: int = 10,
    ) -> None:
        self.enabled = bool(enabled)
        self.root_dir = Path(root_dir) if root_dir else Path("data/memory/chat_archive")
        self.max_search_days = max(1, int(max_search_days))
        self.max_results = max(1, int(max_results))
        self.last_write_at = ""
        self.last_maintenance_at = ""
        if self.enabled:
            self.root_dir.mkdir(parents=True, exist_ok=True)

    def append_turn(
        self,
        *,
        user: str,
        assistant: str,
        session_id: str = "unknown",
        agent_name: str = "conversation_agent",
        action: str = "llm_chat",
        success: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> ChatArchiveRecord | None:
        if not self.enabled:
            return None
        user_text = " ".join(str(user or "").strip().split())
        assistant_text = " ".join(str(assistant or "").strip().split())
        if not user_text and not assistant_text:
            return None
        record = ChatArchiveRecord(
            user=user_text,
            assistant=assistant_text,
            session_id=session_id,
            agent_name=agent_name,
            action=action,
            success=bool(success),
            metadata=dict(metadata or {}),
        )
        path = self._path_for_timestamp(record.timestamp)
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record.to_dict(), ensure_ascii=False)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        self.last_write_at = record.timestamp
        return record

    def search(self, query: str, *, limit: int | None = None, max_days: int | None = None) -> list[MemoryMatch]:
        if not self.enabled:
            return []
        normalized_query = normalize_text(query)
        if not normalized_query:
            return []
        selected_limit = self.max_results if limit is None else max(1, int(limit))
        selected_days = self.max_search_days if max_days is None else max(1, int(max_days))
        query_tokens = token_variants(normalized_query.split())
        results: list[MemoryMatch] = []
        for record in self._iter_recent_records(selected_days):
            normalized_record = record.normalized_text
            record_tokens = token_variants(normalized_record.split())
            score = 0.0
            reasons: list[str] = []
            if normalized_query in normalized_record:
                score += 2.0
                reasons.append("turn contains query")
            overlap = query_tokens & record_tokens
            if overlap:
                score += len(overlap) / max(len(query_tokens), 1)
                reasons.append("token overlap")
            if score > 0:
                results.append(MemoryMatch(record=record, score=round(score, 3), reason="; ".join(reasons), tier="chat_archive"))
        results.sort(key=lambda item: (item.score, item.record.timestamp), reverse=True)
        return results[:selected_limit]

    def format_search(self, query: str, *, limit: int = 5) -> str:
        results = self.search(query, limit=limit)
        if not results:
            return f"I do not see anything in the recent chat archive about {query}, sir."
        if len(results) == 1:
            record = results[0].record
            return f"I found this from our chat archive, sir: you said, ‘{record.user}’ and I replied, ‘{record.assistant}’."
        lines = [f"I found {len(results)} related chat archive turn(s), sir:"]
        for item in results:
            record = item.record
            lines.append(f"- You: {self._preview(record.user)}")
            if record.assistant:
                lines.append(f"  Jarvis: {self._preview(record.assistant)}")
        return "\n".join(lines)

    def rotate(self, *, keep_days: int = 90) -> int:
        """Remove very old daily chat files and return removed file count."""
        if not self.enabled:
            return 0
        cutoff = utc_now().date() - timedelta(days=max(1, int(keep_days)))
        removed = 0
        for path in self.root_dir.glob("*.jsonl"):
            try:
                file_date = datetime.strptime(path.stem, "%Y-%m-%d").date()
            except ValueError:
                continue
            if file_date < cutoff:
                try:
                    path.unlink()
                    removed += 1
                except OSError:
                    continue
        self.last_maintenance_at = utc_now_iso()
        return removed

    def status(self) -> dict[str, Any]:
        files = sorted(self.root_dir.glob("*.jsonl")) if self.root_dir.exists() else []
        line_count = 0
        for path in files[-min(len(files), self.max_search_days) :]:
            try:
                line_count += sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
            except OSError:
                continue
        return {
            "enabled": self.enabled,
            "root_dir": str(self.root_dir),
            "daily_files": len(files),
            "recent_turns_indexed": line_count,
            "max_search_days": self.max_search_days,
            "max_results": self.max_results,
            "last_write_at": self.last_write_at,
            "last_maintenance_at": self.last_maintenance_at,
        }

    def format_status(self) -> str:
        info = self.status()
        return "\n".join(
            [
                "Chat archive memory status:",
                f"- enabled: {info['enabled']}",
                f"- daily archive files: {info['daily_files']}",
                f"- recent archived turns indexed: {info['recent_turns_indexed']}",
                f"- search window: {info['max_search_days']} day(s)",
                f"- path: {info['root_dir']}",
            ]
        )

    def _path_for_timestamp(self, timestamp: str) -> Path:
        parsed = parse_iso_datetime(timestamp) or utc_now()
        return self.root_dir / f"{parsed.date().isoformat()}.jsonl"

    def _iter_recent_records(self, max_days: int) -> list[ChatArchiveRecord]:
        if not self.root_dir.exists():
            return []
        cutoff = utc_now().date() - timedelta(days=max(0, max_days - 1))
        records: list[ChatArchiveRecord] = []
        for path in sorted(self.root_dir.glob("*.jsonl"), reverse=True):
            try:
                file_date = datetime.strptime(path.stem, "%Y-%m-%d").date()
            except ValueError:
                continue
            if file_date < cutoff:
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                except json.JSONDecodeError:
                    continue
                record = ChatArchiveRecord.from_dict(raw) if isinstance(raw, dict) else None
                if record is not None:
                    records.append(record)
        return records

    @staticmethod
    def _preview(text: str, *, limit: int = 140) -> str:
        compact = " ".join(str(text or "").split())
        if len(compact) <= limit:
            return compact
        return compact[: limit - 3] + "..."


class MemoryMaintenance:
    """Lightweight maintenance coordinator for always-on Jarvis memory."""

    def __init__(
        self,
        *,
        short_term_facts: ShortTermFactStore | None = None,
        chat_archive: ChatArchiveStore | None = None,
        status_path: str | Path | None = None,
        interval_seconds: int = 300,
        chat_keep_days: int = 90,
    ) -> None:
        self.short_term_facts = short_term_facts
        self.chat_archive = chat_archive
        self.status_path = Path(status_path) if status_path else Path("data/memory/maintenance_status.json")
        self.interval_seconds = max(30, int(interval_seconds))
        self.chat_keep_days = max(1, int(chat_keep_days))
        self.last_run_at = ""
        self.last_expired_short_term = 0
        self.last_rotated_chat_files = 0

    def should_run(self) -> bool:
        if not self.last_run_at:
            return True
        last = parse_iso_datetime(self.last_run_at)
        if last is None:
            return True
        return (utc_now() - last).total_seconds() >= self.interval_seconds

    def run_if_due(self) -> dict[str, Any]:
        if not self.should_run():
            return self.status()
        return self.run()

    def run(self) -> dict[str, Any]:
        expired = 0
        rotated = 0
        if self.short_term_facts is not None:
            expired = self.short_term_facts.expire_old(save=True)
        if self.chat_archive is not None:
            rotated = self.chat_archive.rotate(keep_days=self.chat_keep_days)
        self.last_run_at = utc_now_iso()
        self.last_expired_short_term = expired
        self.last_rotated_chat_files = rotated
        status = self.status()
        atomic_write_json(self.status_path, status)
        return status

    def status(self) -> dict[str, Any]:
        return {
            "last_run_at": self.last_run_at,
            "interval_seconds": self.interval_seconds,
            "chat_keep_days": self.chat_keep_days,
            "last_expired_short_term": self.last_expired_short_term,
            "last_rotated_chat_files": self.last_rotated_chat_files,
            "status_path": str(self.status_path),
        }

    def format_status(self) -> str:
        info = self.status()
        return "\n".join(
            [
                "Memory maintenance status:",
                f"- last run: {info['last_run_at'] or 'not run yet'}",
                f"- interval: {info['interval_seconds']} second(s)",
                f"- chat archive retention: {info['chat_keep_days']} day(s)",
                f"- expired temporary memories last run: {info['last_expired_short_term']}",
                f"- rotated chat files last run: {info['last_rotated_chat_files']}",
            ]
        )
