"""Memory review panel helpers for Jarvis.

The normal Memory Agent should not read a long memory dump out loud unless the
user asks for that. This module builds a ranked, redacted, panel-ready memory
review so the UI can show detailed bullets while Jarvis only speaks a short
confirmation.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from jarvis.memory.entities import normalize_text
from jarvis.memory.secure_vault import redact_sensitive_text


def _clean_display(value: str) -> str:
    text = " ".join(str(value or "").strip().strip(" .?!,;:\"'").split())
    return text or "that"


def _display_subject(value: str) -> str:
    cleaned = _clean_display(value)
    if cleaned and cleaned == cleaned.lower() and len(cleaned.split()) <= 3:
        return " ".join(part[:1].upper() + part[1:] for part in cleaned.split())
    return cleaned


def _second_person(text: str) -> str:
    value = " ".join(str(text or "").split())
    replacements = [
        ("the user's", "your"),
        ("The user's", "Your"),
        ("user's", "your"),
        ("User's", "Your"),
        ("the user", "you"),
        ("The user", "You"),
    ]
    for old, new in replacements:
        value = value.replace(old, new)
    return value


def _relationship_label(value: Any) -> str:
    aliases = {
        "fianc": "fiancée",
        "fiance": "fiancée",
        "fiancee": "fiancée",
        "fiancees": "fiancée",
        "fiancée": "fiancée",
        "fiancé": "fiancée",
        "dogs": "dog",
        "pets": "pet",
        "cats": "cat",
    }

    def one(raw: Any) -> str:
        cleaned = normalize_text(str(raw or ""))
        if not cleaned:
            return ""
        direct = aliases.get(cleaned)
        if direct:
            return direct
        labels = [aliases.get(token, token) for token in cleaned.split() if token]
        unique = sorted({label for label in labels if label})
        if not unique:
            return ""
        if "fiancée" in unique:
            return "fiancée"
        if len(unique) == 1:
            return unique[0]
        return cleaned

    if isinstance(value, (list, tuple, set)):
        unique = sorted({one(item) for item in value if one(item)})
        if "fiancée" in unique:
            return "fiancée"
        return unique[0] if unique else ""
    return one(value)


def _sentence(text: str) -> str:
    value = redact_sensitive_text(_second_person(" ".join(str(text or "").split())), max_chars=max(len(str(text or "")), 120))
    value = value.strip(" -")
    if not value:
        return ""
    if value[-1] not in ".!?":
        value += "."
    return value


def _entity_name(record: Any) -> str:
    name = _clean_display(getattr(record, "name", ""))
    entity_type = normalize_text(str(getattr(record, "entity_type", "") or ""))
    if entity_type in {"person", "pet"} and name == name.lower():
        return " ".join(part[:1].upper() + part[1:] for part in name.split())
    return name


def _edge_sentence(edge: dict[str, Any], *, default_source: str = "") -> str:
    source = _clean_display(str(edge.get("source") or default_source or ""))
    target = _clean_display(str(edge.get("target") or edge.get("to") or ""))
    relation = _relationship_label(edge.get("type") or edge.get("relation") or edge.get("relationship") or "")
    summary = _sentence(str(edge.get("summary") or ""))
    if summary:
        return summary
    if target.lower() in {"user", "me", "you", "your", "tanner", "owner"} and relation:
        return _sentence(f"{source} is your {relation}")
    if relation.startswith(("works", "developer", "lead developer")):
        return _sentence(f"{source} {relation} {target}")
    if source and target and relation:
        return _sentence(f"{source} is connected to {target} as {relation}")
    return ""


@dataclass(slots=True)
class MemoryReviewItem:
    text: str
    source: str = "memory"
    category: str = "general"
    importance: int = 3
    score: float = 0.0
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["text"] = redact_sensitive_text(self.text, max_chars=max(len(self.text), 120))
        return data


@dataclass(slots=True)
class MemoryReview:
    subject: str
    display_subject: str
    items: list[MemoryReviewItem] = field(default_factory=list)

    def to_panel_payload(self) -> dict[str, Any]:
        return {
            "panel_type": "memory_review",
            "subject": self.subject,
            "display_subject": self.display_subject,
            "item_count": len(self.items),
            "items": [item.to_dict() for item in self.items],
            "empty_message": f"I do not have anything saved about {self.display_subject}, sir.",
            "spoken_summary": (
                f"Here is everything I know about {self.display_subject}, sir."
                if self.items
                else f"I do not have anything saved about {self.display_subject}, sir."
            ),
        }


def build_memory_review(
    subject: str,
    *,
    long_term: Any | None = None,
    short_term_facts: Any | None = None,
    entity_memory: Any | None = None,
    limit: int = 24,
) -> MemoryReview:
    display = _display_subject(subject)
    review = MemoryReview(subject=" ".join(str(subject or "").split()), display_subject=display)
    seen: set[str] = set()

    def add(text: str, *, source: str, category: str = "general", importance: int = 3, score: float = 0.0, reason: str = "", metadata: dict[str, Any] | None = None) -> None:
        sentence = _sentence(text)
        if not sentence:
            return
        normalized = normalize_text(sentence)
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        review.items.append(
            MemoryReviewItem(
                text=sentence,
                source=source,
                category=category or "general",
                importance=max(1, min(5, int(importance or 3))),
                score=float(score or 0.0),
                reason=reason,
                metadata=metadata or {},
            )
        )

    if entity_memory is not None and hasattr(entity_memory, "search"):
        try:
            entity_matches = entity_memory.search(subject, limit=12)
        except Exception:
            entity_matches = []
        for match in entity_matches:
            record = getattr(match, "record", match)
            score = float(getattr(match, "score", 0.0) or 0.0)
            name = _entity_name(record)
            entity_type = str(getattr(record, "entity_type", "entity") or "entity")
            attributes = getattr(record, "attributes", {}) if isinstance(getattr(record, "attributes", {}), dict) else {}
            relation = _relationship_label(attributes.get("relationship"))
            if entity_type == "person" and relation:
                add(f"{name} is your {relation}", source="entity", category="relationship", importance=5, score=score, reason="relationship")
            if entity_type == "pet":
                species = str(attributes.get("species") or "").strip()
                breed = str(attributes.get("breed_or_note") or attributes.get("breed") or "").strip()
                if species and breed:
                    add(f"{name} is your {species}, {breed}", source="entity", category="pet", importance=5, score=score, reason="pet profile")
                elif species:
                    add(f"{name} is your {species}", source="entity", category="pet", importance=5, score=score, reason="pet profile")
            summary = str(getattr(record, "summary", "") or "")
            if summary:
                add(summary, source="entity", category=entity_type, importance=int(getattr(record, "importance", 3) or 3), score=score, reason="summary")
            for rel in getattr(record, "relationships", []) or []:
                if isinstance(rel, dict):
                    add(_edge_sentence(rel, default_source=name), source="relationship_graph", category="relationship", importance=4, score=score, reason="relationship edge")
            for key, value in sorted(attributes.items()):
                if key in {"relationship", "species", "breed", "breed_or_note"} or value in (None, "", [], {}):
                    continue
                add(f"{name} {str(key).replace('_', ' ')}: {value}", source="entity", category=entity_type, importance=3, score=score, reason="attribute")
            aliases = [str(alias) for alias in (getattr(record, "aliases", []) or []) if str(alias).strip()]
            if aliases:
                add(f"{name} also has these aliases: {', '.join(aliases[:8])}", source="entity", category="aliases", importance=2, score=score, reason="aliases")

    if long_term is not None and hasattr(long_term, "search"):
        try:
            long_matches = long_term.search(subject, limit=12)
        except Exception:
            long_matches = []
        for match in long_matches:
            record = getattr(match, "record", match)
            add(
                str(getattr(record, "text", "") or ""),
                source="long_term",
                category=str(getattr(record, "category", "general") or "general"),
                importance=int(getattr(record, "importance", 3) or 3),
                score=float(getattr(match, "score", 0.0) or 0.0),
                reason=str(getattr(match, "reason", "") or "long-term match"),
            )

    if short_term_facts is not None and hasattr(short_term_facts, "search"):
        try:
            short_matches = short_term_facts.search(subject, limit=12)
        except Exception:
            short_matches = []
        for match in short_matches:
            record = getattr(match, "record", match)
            add(
                str(getattr(record, "text", "") or ""),
                source="short_term",
                category=str(getattr(record, "category", "general") or "general"),
                importance=int(getattr(record, "importance", 2) or 2),
                score=float(getattr(match, "score", 0.0) or 0.0),
                reason=str(getattr(match, "reason", "") or "temporary match"),
            )

    source_rank = {"entity": 4, "relationship_graph": 3, "long_term": 2, "short_term": 1}
    review.items.sort(key=lambda item: (item.importance, item.score, source_rank.get(item.source, 0), item.text.lower()), reverse=True)
    review.items = review.items[: max(1, int(limit))]
    return review


def format_memory_review_spoken(review: MemoryReview) -> str:
    if not review.items:
        return f"I do not have anything saved about {review.display_subject}, sir."
    lines = [f"Here is everything I know about {review.display_subject}, sir:"]
    for index, item in enumerate(review.items, start=1):
        clean = re.sub(r"^[-•\d\.\s]+", "", item.text).strip()
        lines.append(f"{index}. {clean}")
    return "\n".join(lines)
