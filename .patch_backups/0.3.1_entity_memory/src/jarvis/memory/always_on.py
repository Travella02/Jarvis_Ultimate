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
    source: str = "chat_archive"

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




@dataclass(slots=True)
class MemoryCandidateRecord:
    """A possible memory Jarvis noticed but has not permanently saved yet."""

    text: str
    suggested_tier: str = "review"
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    importance: int = 2
    confidence: float = 0.5
    reason: str = "needs review"
    status: str = "pending"
    source: str = "auto_capture"
    source_user: str = ""
    source_assistant: str = ""
    id: str = field(default_factory=lambda: f"cand_{uuid4().hex[:12]}")
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_text(self) -> str:
        return normalize_text(self.text)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "MemoryCandidateRecord | None":
        text = str(item.get("text") or "").strip()
        if not text:
            return None
        try:
            importance = int(item.get("importance", 2))
        except (TypeError, ValueError):
            importance = 2
        try:
            confidence = float(item.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5
        tags_raw = item.get("tags")
        return cls(
            id=str(item.get("id") or f"cand_{uuid4().hex[:12]}"),
            text=" ".join(text.split()),
            suggested_tier=str(item.get("suggested_tier") or "review").strip().lower() or "review",
            category=str(item.get("category") or "general").strip().lower() or "general",
            tags=_normalize_tags(tags_raw if isinstance(tags_raw, list) else []),
            importance=max(1, min(5, importance)),
            confidence=max(0.0, min(1.0, confidence)),
            reason=str(item.get("reason") or "needs review"),
            status=str(item.get("status") or "pending").strip().lower() or "pending",
            source=str(item.get("source") or "auto_capture"),
            source_user=str(item.get("source_user") or ""),
            source_assistant=str(item.get("source_assistant") or ""),
            created_at=str(item.get("created_at") or utc_now_iso()),
            updated_at=str(item.get("updated_at") or item.get("created_at") or utc_now_iso()),
            metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
        )


class MemoryCandidateStore:
    """Crash-safe queue for memories Jarvis may want to save permanently later."""

    schema_version = 1

    def __init__(
        self,
        *,
        enabled: bool = True,
        path: str | Path | None = None,
        max_records: int = 1000,
        review_limit: int = 8,
    ) -> None:
        self.enabled = bool(enabled)
        self.path = Path(path) if path else Path("data/memory/memory_candidates.json")
        self.max_records = max(50, int(max_records))
        self.review_limit = max(1, int(review_limit))
        self._records: list[MemoryCandidateRecord] = []
        self.load()

    @property
    def records(self) -> tuple[MemoryCandidateRecord, ...]:
        return tuple(self._records)

    def add(
        self,
        text: str,
        *,
        suggested_tier: str = "review",
        category: str = "general",
        tags: Iterable[str] | None = None,
        importance: int = 2,
        confidence: float = 0.5,
        reason: str = "needs review",
        source: str = "auto_capture",
        source_user: str = "",
        source_assistant: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> MemoryCandidateRecord | None:
        if not self.enabled:
            return None
        cleaned = " ".join(str(text or "").strip().split())
        if not cleaned:
            return None
        normalized = normalize_text(cleaned)
        existing = self._find_duplicate(normalized, friendly_key=self._friendly_key(cleaned))
        now = utc_now_iso()
        if existing is not None:
            existing.text = cleaned
            existing.suggested_tier = suggested_tier
            existing.category = category
            existing.tags = sorted(set([*existing.tags, *_normalize_tags(tags or [])]))
            existing.importance = max(existing.importance, max(1, min(5, int(importance))))
            existing.confidence = max(existing.confidence, max(0.0, min(1.0, float(confidence))))
            existing.reason = reason or existing.reason
            existing.status = "pending"
            existing.updated_at = now
            existing.metadata.update(metadata or {})
            self.save()
            return existing
        record = MemoryCandidateRecord(
            text=cleaned,
            suggested_tier=str(suggested_tier or "review").strip().lower() or "review",
            category=str(category or "general").strip().lower() or "general",
            tags=_normalize_tags(tags or []),
            importance=max(1, min(5, int(importance))),
            confidence=max(0.0, min(1.0, float(confidence))),
            reason=reason or "needs review",
            source=source,
            source_user=str(source_user or ""),
            source_assistant=str(source_assistant or ""),
            metadata=dict(metadata or {}),
        )
        self._records.append(record)
        self._trim()
        self.save()
        return record

    def pending(self, *, limit: int | None = None) -> list[MemoryCandidateRecord]:
        selected = [record for record in self._records if record.status == "pending"]
        return selected[-(limit or self.review_limit):]

    def latest_pending(self) -> MemoryCandidateRecord | None:
        pending = self.pending(limit=1)
        return pending[-1] if pending else None

    def approve(self, query: str = "", *, all_matches: bool = False) -> list[MemoryCandidateRecord]:
        matches = self._expand_duplicate_matches(self._select(query, all_matches=all_matches))
        for record in matches:
            record.status = "approved"
            record.updated_at = utc_now_iso()
        if matches:
            self.save()
        return matches

    def reject(self, query: str = "", *, all_matches: bool = False) -> list[MemoryCandidateRecord]:
        matches = self._expand_duplicate_matches(self._select(query, all_matches=all_matches))
        for record in matches:
            record.status = "rejected"
            record.updated_at = utc_now_iso()
        if matches:
            self.save()
        return matches

    def search(self, query: str, *, limit: int = 8) -> list[MemoryMatch]:
        normalized_query = normalize_text(query)
        if not normalized_query:
            return []
        tokens = token_variants(normalized_query.split())
        results: list[MemoryMatch] = []
        for record in self._records:
            score, reason = self._score(record, normalized_query, tokens)
            if score > 0:
                results.append(MemoryMatch(record=record, score=round(score, 3), reason=reason, tier="candidate"))
        results.sort(key=lambda item: (item.score, getattr(item.record, "updated_at", "")), reverse=True)
        return results[:max(1, int(limit))]

    def status(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for record in self._records:
            counts[record.status] = counts.get(record.status, 0) + 1
        return {
            "enabled": self.enabled,
            "records": len(self._records),
            "pending": counts.get("pending", 0),
            "approved": counts.get("approved", 0),
            "rejected": counts.get("rejected", 0),
            "max_records": self.max_records,
            "review_limit": self.review_limit,
            "path": str(self.path),
        }

    def format_pending(self, *, limit: int | None = None) -> str:
        pending = self._dedupe_display_records(self.pending(limit=limit))
        if not pending:
            return "I do not have any memory candidates waiting for review right now, sir."

        if len(pending) == 1:
            record = pending[0]
            tier = self._friendly_tier(record.suggested_tier)
            text = self._friendly_candidate(record)
            return f"I found one possible memory waiting for review, sir: {text}. I would treat that as {tier}."

        lines = [f"I found {len(pending)} possible memories waiting for review, sir:"]
        for record in pending:
            lines.append(f"- {self._friendly_candidate(record)} — {self._friendly_tier(record.suggested_tier)}")
        return "\n".join(lines)

    def format_status(self) -> str:
        info = self.status()
        state = "online" if info["enabled"] else "disabled"
        return (
            f"Memory candidate review is {state}, sir. I have {info['pending']} candidate"
            f"{'s' if info['pending'] != 1 else ''} waiting for review."
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
        if not self.enabled or not self.path.exists():
            self._records = []
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._records = []
            return
        records: list[MemoryCandidateRecord] = []
        for item in payload.get("records", []):
            if isinstance(item, dict):
                record = MemoryCandidateRecord.from_dict(item)
                if record is not None:
                    records.append(record)
        self._records = self._dedupe_loaded_records(records)
        self._trim()

    def _select(self, query: str = "", *, all_matches: bool = False) -> list[MemoryCandidateRecord]:
        cleaned = " ".join(str(query or "").strip().split())
        if all_matches:
            return self.pending(limit=len(self._records))
        if not cleaned or normalize_text(cleaned) in {"that", "it", "latest", "last"}:
            latest = self.latest_pending()
            return [latest] if latest is not None else []
        if cleaned.startswith("cand_"):
            return [record for record in self._records if record.id == cleaned and record.status == "pending"]
        return [match.record for match in self.search(cleaned, limit=1) if match.record.status == "pending"]

    def _find_duplicate(self, normalized: str, *, friendly_key: str = "") -> MemoryCandidateRecord | None:
        for record in self._records:
            if record.status != "pending":
                continue
            if record.normalized_text == normalized:
                return record
            if friendly_key and self._friendly_key(record.text) == friendly_key:
                return record
        return None

    def _friendly_key(self, text: str) -> str:
        return normalize_text(ShortTermFactStore._for_user(text))

    def _dedupe_display_records(self, records: list[MemoryCandidateRecord]) -> list[MemoryCandidateRecord]:
        selected: dict[str, MemoryCandidateRecord] = {}
        order: list[str] = []
        for record in records:
            key = self._friendly_key(record.text) or record.normalized_text
            if not key:
                continue
            existing = selected.get(key)
            if existing is None:
                selected[key] = record
                order.append(key)
                continue
            if record.confidence > existing.confidence or len(record.text) > len(existing.text):
                selected[key] = record
        return [selected[key] for key in order if key in selected]

    def _expand_duplicate_matches(self, matches: list[MemoryCandidateRecord]) -> list[MemoryCandidateRecord]:
        if not matches:
            return []
        keys = {self._friendly_key(record.text) or record.normalized_text for record in matches}
        expanded: list[MemoryCandidateRecord] = []
        seen_ids: set[str] = set()
        for record in self._records:
            if record.status != "pending":
                continue
            key = self._friendly_key(record.text) or record.normalized_text
            if key in keys and record.id not in seen_ids:
                expanded.append(record)
                seen_ids.add(record.id)
        return expanded

    def _dedupe_loaded_records(self, records: list[MemoryCandidateRecord]) -> list[MemoryCandidateRecord]:
        deduped: dict[tuple[str, str], MemoryCandidateRecord] = {}
        order: list[tuple[str, str]] = []
        for record in records:
            key = (record.status, self._friendly_key(record.text) or record.normalized_text)
            if not key[1]:
                continue
            existing = deduped.get(key)
            if existing is None:
                deduped[key] = record
                order.append(key)
                continue
            existing.tags = sorted(set([*existing.tags, *record.tags]))
            existing.importance = max(existing.importance, record.importance)
            existing.confidence = max(existing.confidence, record.confidence)
            existing.metadata.update(record.metadata)
            existing.updated_at = max(existing.updated_at, record.updated_at)
            if len(record.text) > len(existing.text):
                existing.text = record.text
        return [deduped[key] for key in order if key in deduped]

    def _trim(self) -> None:
        while len(self._records) > self.max_records:
            # Prefer trimming old rejected/approved records before pending ones.
            index = next((idx for idx, record in enumerate(self._records) if record.status != "pending"), 0)
            self._records.pop(index)

    def _score(self, record: MemoryCandidateRecord, normalized_query: str, query_tokens: set[str]) -> tuple[float, str]:
        normalized_record = record.normalized_text
        combined = token_variants(normalized_record.split()) | set(record.tags) | {normalize_text(record.category), normalize_text(record.suggested_tier)}
        score = 0.0
        reasons: list[str] = []
        if normalized_query in normalized_record:
            score += 2.0
            reasons.append("text contains query")
        overlap = query_tokens & combined
        if overlap:
            score += len(overlap) / max(len(query_tokens), 1)
            reasons.append("token overlap")
        if score > 0:
            score += record.importance * 0.02
        return score, "; ".join(reasons)

    @staticmethod
    def _friendly_candidate(record: MemoryCandidateRecord) -> str:
        return ShortTermFactStore._for_user(record.text).strip(" .?!")

    @staticmethod
    def _friendly_tier(tier: str) -> str:
        normalized = str(tier or "review").strip().lower().replace("-", "_")
        if normalized in {"long_term", "permanent"}:
            return "a permanent memory"
        if normalized in {"short_term", "temporary"}:
            return "a temporary memory"
        if normalized == "chat_archive_only":
            return "chat history only"
        return "something to review first"


class MemoryAutoCaptureEngine:
    """Decides whether a completed turn might contain useful memory."""

    def __init__(self, *, min_importance: int = 2, llm_review_enabled: bool = False) -> None:
        self.min_importance = max(1, min(5, int(min_importance)))
        self.llm_review_enabled = bool(llm_review_enabled)

    def classify_turn(self, user: str, assistant: str = "", *, llm_provider: Any | None = None) -> dict[str, Any]:
        user_text = " ".join(str(user or "").strip().split())
        if not user_text or self._is_low_value(user_text):
            return {"decision": "ignore", "text": "", "importance": 1, "confidence": 0.0, "reason": "low-value or empty turn", "category": "general", "tags": []}

        llm_decision = self._classify_with_llm(user_text, assistant, llm_provider=llm_provider)
        if llm_decision:
            return llm_decision

        return self._classify_with_rules(user_text, assistant)

    def _classify_with_rules(self, user_text: str, assistant: str = "") -> dict[str, Any]:
        lowered = user_text.lower()
        cleaned = self._clean_candidate_text(user_text)
        category = self._infer_category(cleaned)
        tags = self._infer_tags(cleaned, category=category)

        if any(phrase in lowered for phrase in ["from now on", "going forward", "always ", "never ", "remember to", "i prefer", "i like", "my favorite", "i want jarvis", "for future"]):
            return {
                "decision": "long_term",
                "text": cleaned,
                "importance": 4 if "jarvis" not in lowered else 5,
                "confidence": 0.82,
                "reason": "stable preference, instruction, or Jarvis project rule",
                "category": category,
                "tags": tags,
            }

        if any(phrase in lowered for phrase in ["my fiance", "my fiancée", "my wife", "my brother", "my dog", "my pet", "my cat", "my car", "my name is"]):
            return {
                "decision": "long_term",
                "text": cleaned,
                "importance": 4,
                "confidence": 0.78,
                "reason": "relationship, pet, identity, or durable personal detail",
                "category": category,
                "tags": tags,
            }

        if any(phrase in lowered for phrase in ["i ate", "i had for", "today i", "right now", "i'm testing", "i am testing", "we are testing", "i made the commit", "we left off", "next step"]):
            return {
                "decision": "short_term",
                "text": cleaned,
                "importance": 2,
                "confidence": 0.68,
                "reason": "recent context useful for follow-up but not necessarily permanent",
                "category": category,
                "tags": tags,
            }

        return {"decision": "ignore", "text": "", "importance": 1, "confidence": 0.25, "reason": "not important enough to capture automatically", "category": category, "tags": tags}

    def _classify_with_llm(self, user_text: str, assistant: str, *, llm_provider: Any | None = None) -> dict[str, Any] | None:
        if not self.llm_review_enabled or llm_provider is None or not hasattr(llm_provider, "chat"):
            return None
        system_prompt = (
            "You classify possible memories for a local assistant. Return compact JSON only with keys: "
            "decision, text, category, tags, importance, confidence, reason. decision must be one of "
            "long_term, short_term, review, chat_archive_only, ignore. Prefer review over long_term when unsure. "
            "Do not save sensitive details permanently unless the user explicitly frames them as useful to remember."
        )
        prompt = f"User said: {user_text}\nAssistant replied: {assistant[:300]}\nClassify whether this contains useful memory."
        try:
            response = llm_provider.chat([{"role": "user", "content": prompt}], system_prompt=system_prompt)
        except Exception:
            return None
        if not getattr(response, "success", False):
            return None
        try:
            raw = json.loads(str(getattr(response, "content", "")).strip())
        except json.JSONDecodeError:
            return None
        if not isinstance(raw, dict):
            return None
        decision = str(raw.get("decision") or "review").strip().lower()
        if decision not in {"long_term", "short_term", "review", "chat_archive_only", "ignore"}:
            decision = "review"
        text = " ".join(str(raw.get("text") or user_text).split())
        try:
            importance = int(raw.get("importance", 2))
        except (TypeError, ValueError):
            importance = 2
        try:
            confidence = float(raw.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5
        tags_raw = raw.get("tags")
        tags = _normalize_tags(tags_raw if isinstance(tags_raw, list) else [])
        return {
            "decision": decision,
            "text": text,
            "importance": max(1, min(5, importance)),
            "confidence": max(0.0, min(1.0, confidence)),
            "reason": str(raw.get("reason") or "LLM memory classifier"),
            "category": str(raw.get("category") or self._infer_category(text)).strip().lower() or "general",
            "tags": tags or self._infer_tags(text, category=str(raw.get("category") or "general")),
        }

    def _is_low_value(self, text: str) -> bool:
        lowered = normalize_text(text)
        low_value = {"thanks jarvis", "thank you jarvis", "okay", "ok", "yes", "no", "bye", "goodbye", "list agents", "memory status", "status"}
        if lowered in low_value:
            return True
        return lowered.startswith("what do you remember") or lowered.startswith("what did we talk about")

    def _clean_candidate_text(self, text: str) -> str:
        cleaned = " ".join(str(text or "").strip().split())
        cleaned = re.sub(r"^(?:jarvis,?\s*)", "", cleaned, flags=re.IGNORECASE).strip()
        # Keep the durable fact, not the command phrasing.  For example,
        # "From now on, I prefer short instructions" should later read back as
        # "you prefer short instructions," not as a command transcript.
        cleaned = re.sub(r"^(?:from now on|going forward|for future updates?|for the future),?\s+", "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned.strip(" .?!")

    def _infer_category(self, text: str) -> str:
        lowered = text.lower()
        if any(word in lowered for word in ["prefer", "favorite", "like", "want"]):
            return "preference"
        if any(word in lowered for word in ["jarvis", "project", "patch", "update", "version", "commit", "memory pipeline"]):
            return "project"
        if any(word in lowered for word in ["fiance", "fiancée", "wife", "brother", "pet", "dog", "cat", "car", "name"]):
            return "personal"
        if any(word in lowered for word in ["ate", "dinner", "lunch", "breakfast", "food"]):
            return "daily_life"
        return "general"

    def _infer_tags(self, text: str, *, category: str) -> list[str]:
        tags = [category]
        lowered = text.lower()
        if "jarvis" in lowered:
            tags.append("jarvis")
        if "app" in lowered or "spotify" in lowered or "chrome" in lowered:
            tags.append("apps")
        if "memory" in lowered:
            tags.append("memory")
        if "food" in lowered or "ate" in lowered:
            tags.append("food")
        return _normalize_tags(tags)

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
        if existing is None:
            friendly_normalized = normalize_text(self._for_user(cleaned_text))
            existing = self._find_duplicate(friendly_normalized, friendly=True)
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
            phrases = self._dedupe_user_phrases([self._for_user(item.record.text) for item in results])
            if len(phrases) == 1:
                return f"I temporarily remember that {phrases[0]}, sir."
            lines = [f"I found {len(phrases)} temporary memories about {query}, sir:"]
            lines.extend(f"- {phrase}" for phrase in phrases)
            return "\n".join(lines)
        records = list(self.records)[-limit:]
        if not records:
            return "I do not have any temporary memories saved right now, sir."
        phrases = self._dedupe_user_phrases([self._for_user(record.text) for record in records])
        lines = [f"I have {len(phrases)} recent temporary memory item(s), sir:"]
        lines.extend(f"- {phrase}" for phrase in phrases)
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
        state = "online" if info["enabled"] else "disabled"
        record_word = "temporary memory" if info["records"] == 1 else "temporary memories"
        return "\n".join(
            [
                "Short-term fact memory status:",
                f"Short-term memory is {state}, sir. I currently have {info['records']} active {record_word}.",
                f"New short-term facts stay active for about {info['default_days']} day(s) unless they expire or get promoted later.",
                f"I can bring up to {info['inject_limit']} relevant short-term memories into the active conversation."
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
        self._records = self._dedupe_loaded_records(loaded)
        self._trim()

    def _find_duplicate(self, normalized: str, *, friendly: bool = False) -> ShortTermFactRecord | None:
        for record in self._records:
            record_key = normalize_text(self._for_user(record.text)) if friendly else record.normalized_text
            if record_key == normalized:
                return record
        return None

    def _dedupe_loaded_records(self, records: list[ShortTermFactRecord]) -> list[ShortTermFactRecord]:
        deduped: dict[str, ShortTermFactRecord] = {}
        order: list[str] = []
        for record in records:
            key = normalize_text(self._for_user(record.text)) or record.normalized_text
            if not key:
                continue
            existing = deduped.get(key)
            if existing is None:
                deduped[key] = record
                order.append(key)
                continue
            existing.tags = sorted(set([*existing.tags, *record.tags]))
            existing.importance = max(existing.importance, record.importance)
            existing.expires_at = max(existing.expires_at, record.expires_at)
            existing.metadata.update(record.metadata)
            existing.updated_at = max(existing.updated_at, record.updated_at)
            if len(record.text) > len(existing.text):
                existing.text = record.text
        return [deduped[key] for key in order if key in deduped]

    def _dedupe_user_phrases(self, phrases: list[str]) -> list[str]:
        selected: dict[str, tuple[int, str]] = {}
        order = 0
        for phrase in phrases:
            cleaned = " ".join(str(phrase or "").strip(" .?!").split())
            key = normalize_text(cleaned)
            if not key:
                continue
            existing = selected.get(key)
            if existing is None or len(cleaned) > len(existing[1]):
                selected[key] = (existing[0] if existing else order, cleaned)
            order += 1
        return [phrase for _, phrase in sorted(selected.values(), key=lambda item: item[0])]

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
        cleaned = " ".join(str(text or "").strip().strip(" .?!").split())
        cleaned = re.sub(r"^(?:from now on|going forward|for future updates?|for the future),?\s+", "", cleaned, flags=re.IGNORECASE).strip()
        replacements = [
            (r"\bmy\b", "your"),
            (r"\bmine\b", "yours"),
            (r"\bi am\b", "you are"),
            (r"\bi'm\b", "you are"),
            (r"\bi like\b", "you like"),
            (r"\bi prefer\b", "you prefer"),
            (r"\bi want\b", "you want"),
            (r"\bi need\b", "you need"),
            (r"\bi have\b", "you have"),
            (r"\bi use\b", "you use"),
            (r"\bme\b", "you"),
            (r"\bi\b", "you"),
        ]
        for pattern, replacement in replacements:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\byou are prefer\b", "you prefer", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .?!")
        return cleaned[:1].lower() + cleaned[1:] if cleaned else cleaned


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
    source: str = "chat_archive"

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
            source=str(item.get("source") or "chat_archive"),
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

    def format_search(self, query: str, *, limit: int = 5, llm_provider: Any | None = None, timing: Any | None = None) -> str:
        results = self.search(query, limit=limit)
        topic = self._friendly_topic(query)
        if not results:
            return f"I do not remember a recent conversation about {topic}, sir."

        llm_summary = self._summarize_with_llm(topic, query, results[:5], llm_provider=llm_provider, timing=timing)
        if llm_summary:
            return llm_summary

        summary = self._summarize_recent_results(topic, results[:3])
        if summary:
            return summary
        return f"I remember we talked about {topic} recently, sir."

    def _summarize_with_llm(
        self,
        topic: str,
        query: str,
        results: list[MemoryMatch],
        *,
        llm_provider: Any | None = None,
        timing: Any | None = None,
    ) -> str:
        """Ask the attached local LLM to turn archive hits into a human answer.

        The chat archive is evidence, not a final response.  This keeps Jarvis
        from reading raw log fragments aloud while still falling back to a small
        deterministic summary in tests or when the LLM is unavailable.
        """

        if llm_provider is None or not hasattr(llm_provider, "chat"):
            return ""
        evidence = self._archive_evidence_for_llm(results[:5])
        if not evidence:
            return ""
        system_prompt = (
            "You are Jarvis, a concise local assistant. Summarize the provided chat archive evidence "
            "for the user. Answer naturally in first person. Do not quote raw log labels like User: or "
            "Jarvis:. Do not mention archive files, search results, matches, or databases. Keep it under "
            "45 words. End naturally with 'sir.' if appropriate."
        )
        user_prompt = (
            f"The user asked: {query}\n"
            f"Topic: {topic}\n\n"
            "Relevant recent chat evidence:\n"
            f"{evidence}\n\n"
            "Give the spoken answer only."
        )
        try:
            response = llm_provider.chat([{"role": "user", "content": user_prompt}], system_prompt=system_prompt, timing=timing)
        except Exception:
            return ""
        if not getattr(response, "success", False):
            return ""
        return self._clean_llm_archive_summary(getattr(response, "content", ""))

    def _archive_evidence_for_llm(self, results: list[MemoryMatch]) -> str:
        lines: list[str] = []
        for index, item in enumerate(results, start=1):
            record = item.record
            user = self._clean_evidence_text(getattr(record, "user", ""))
            assistant = self._clean_evidence_text(getattr(record, "assistant", ""))
            if not user and not assistant:
                continue
            lines.append(f"Turn {index}: user asked {user!r}; Jarvis answered {assistant!r}.")
        return "\n".join(lines[:5])

    def _clean_llm_archive_summary(self, text: str) -> str:
        cleaned = " ".join(str(text or "").split()).strip().strip('"')
        if not cleaned:
            return ""
        cleaned = re.sub(r"\b(?:User|Assistant|Jarvis)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace("chat archive", "our conversation")
        cleaned = self._preview(cleaned, limit=280)
        if "sir" not in cleaned.lower():
            cleaned = cleaned.rstrip(" .?!") + ", sir."
        elif cleaned[-1] not in ".?!":
            cleaned += "."
        return cleaned

    def _clean_evidence_text(self, text: str) -> str:
        cleaned = " ".join(str(text or "").split()).strip()
        cleaned = re.sub(r"^(?:jarvis,?\s*)", "", cleaned, flags=re.IGNORECASE).strip()
        return self._preview(cleaned, limit=180)

    def _summarize_recent_results(self, topic: str, results: list[MemoryMatch]) -> str:
        """Create a concise spoken chat-memory answer without dumping transcripts."""
        snippets: list[str] = []
        for item in results:
            record = item.record
            user = self._clean_chat_snippet(record.user)
            assistant = self._clean_chat_snippet(record.assistant)
            if user and not self._is_meta_memory_question(user):
                snippets.append(user)
            if assistant and not self._is_raw_memory_status(assistant) and len(snippets) < 3:
                snippets.append(assistant)

        snippets = self._dedupe_snippets(snippets)
        if not snippets:
            return f"I remember we recently talked about {topic}, sir."

        if self._topic_is_memory(topic):
            detail = self._memory_topic_summary(results)
            if detail:
                return detail

        shown = snippets[:1]
        return f"I remember we recently talked about {topic}, sir. {shown[0]}"

    def _topic_is_memory(self, topic: str) -> bool:
        normalized = normalize_text(topic)
        return any(token in normalized.split() for token in {"memory", "memories", "remember", "remembering"})

    def _memory_topic_summary(self, results: list[MemoryMatch]) -> str:
        combined = normalize_text(" ".join(f"{item.record.user} {item.record.assistant}" for item in results))
        points: list[str] = []
        if "favorite test color" in combined:
            points.append("saving and recalling your favorite test color")
        if "temporary memory" in combined or "short term" in combined or "short term" in combined:
            points.append("testing temporary memory")
        if "memory status" in combined:
            points.append("checking memory status")
        if "chat archive" in combined or "what did we talk" in combined:
            points.append("searching our chat history")
        points = self._dedupe_plain(points)
        if not points:
            return ""
        if len(points) == 1:
            return f"I remember we recently talked about memory, sir. We were {points[0]}."
        if len(points) == 2:
            joined = f"{points[0]} and {points[1]}"
        else:
            joined = ", ".join(points[:-1]) + f", and {points[-1]}"
        return f"I remember we recently talked about memory, sir. We were {joined}."

    def _is_meta_memory_question(self, text: str) -> bool:
        normalized = normalize_text(text)
        return normalized.startswith("what did we talk about") or normalized.startswith("what do you remember")

    def _is_raw_memory_status(self, text: str) -> bool:
        normalized = normalize_text(text)
        return "memory status" in normalized and ("enabled" in normalized or "records" in normalized or "archive" in normalized)

    def _dedupe_plain(self, phrases: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for phrase in phrases:
            normalized = normalize_text(phrase)
            if normalized and normalized not in seen:
                seen.add(normalized)
                deduped.append(phrase)
        return deduped

    def _clean_chat_snippet(self, text: str) -> str:
        cleaned = " ".join(str(text or "").split()).strip(" .?!")
        if not cleaned:
            return ""
        cleaned = re.sub(r"^(?:jarvis,?\s*)", "", cleaned, flags=re.IGNORECASE).strip(" .?!")
        cleaned = re.sub(r"^what do you remember about\s+", "you asked what I remembered about ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^what did we talk about\s+", "you asked what we talked about regarding ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^remember that\s+", "you asked me to remember that ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^remember\s+", "you asked me to remember ", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace("Temporary memories:", "For now, I remember")
        cleaned = cleaned.replace("Permanent memories:", "I remember")
        cleaned = self._preview(cleaned, limit=120)
        if cleaned and cleaned[-1] not in ".?!":
            cleaned += "."
        return cleaned

    def _dedupe_snippets(self, snippets: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for snippet in snippets:
            normalized = re.sub(r"[^a-z0-9\s]", " ", snippet.lower())
            normalized = " ".join(normalized.split())
            if not normalized or normalized in seen:
                continue
            if any(normalized in old or old in normalized for old in seen):
                continue
            seen.add(normalized)
            deduped.append(snippet)
        return deduped

    def _friendly_topic(self, query: str) -> str:
        cleaned = " ".join(str(query or "").strip().strip(" .?!").split())
        cleaned = re.sub(r"^(?:what\s+)?(?:did\s+we\s+)?(?:talk\s+about\s+)?", "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned or "that"

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
        state = "online" if info["enabled"] else "disabled"
        turn_word = "turn" if info["recent_turns_indexed"] == 1 else "turns"
        return "\n".join(
            [
                "Chat archive memory status:",
                f"Chat archive memory is {state}, sir. I have {info['daily_files']} daily archive file(s) available.",
                f"Right now I can search {info['recent_turns_indexed']} recent conversation {turn_word} across the last {info['max_search_days']} day(s).",
                "This is the foundation for asking me what we talked about earlier without needing a restart."
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


# Backward-compatible name used by earlier tests/docs.
ChatArchiveMemory = ChatArchiveStore


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
