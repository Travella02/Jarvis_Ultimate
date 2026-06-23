"""User-controlled memory preference policy for Jarvis.

The 0.3.5 memory preference layer decides whether possible memories should be
stored automatically, queued for review, kept temporarily, or ignored.  It is
local-first, crash-safe, and intentionally category-based so future SaaS tenants
can expose safe controls without changing the core memory pipeline.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def normalize_text(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", str(value or "").lower())
    return " ".join(cleaned.split())


VALID_POLICIES = {"auto", "ask", "never", "short_term"}


CATEGORY_ALIASES: dict[str, str] = {
    "person": "people",
    "people": "people",
    "human": "people",
    "family": "people",
    "friends": "people",
    "friend": "people",
    "team": "people",
    "teammates": "people",
    "pet": "pets",
    "pets": "pets",
    "dog": "pets",
    "dogs": "pets",
    "cat": "pets",
    "cats": "pets",
    "project": "projects",
    "projects": "projects",
    "jarvis": "projects",
    "app": "apps",
    "apps": "apps",
    "application": "apps",
    "applications": "apps",
    "tool": "apps",
    "tools": "apps",
    "program": "apps",
    "programs": "apps",
    "app preference": "apps",
    "application preference": "apps",
    "app setting": "app_settings",
    "app settings": "app_settings",
    "application setting": "app_settings",
    "application settings": "app_settings",
    "software settings": "app_settings",
    "setting": "app_settings",
    "settings": "app_settings",
    "game setting": "game_settings",
    "game settings": "game_settings",
    "gaming setting": "game_settings",
    "gaming settings": "game_settings",
    "screen setting": "screen_context",
    "screen settings": "screen_context",
    "screen": "screen_context",
    "screen context": "screen_context",
    "ocr": "screen_context",
    "vision": "screen_context",
    "device": "devices",
    "devices": "devices",
    "hardware": "devices",
    "computer": "devices",
    "laptop": "devices",
    "desktop": "devices",
    "vehicle": "vehicles",
    "vehicles": "vehicles",
    "car": "vehicles",
    "cars": "vehicles",
    "place": "places",
    "places": "places",
    "location": "places",
    "locations": "places",
    "relationship": "relationships",
    "relationships": "relationships",
    "relation": "relationships",
    "preference": "preferences",
    "preferences": "preferences",
    "likes": "preferences",
    "favorites": "preferences",
    "work": "work",
    "job": "work",
    "jobs": "work",
    "career": "work",
    "health": "health",
    "medical": "health",
    "medicine": "health",
    "financial": "financial",
    "finance": "financial",
    "money": "financial",
    "bank": "financial",
    "banking": "financial",
    "credit": "financial",
    "payment": "financial",
    "payments": "financial",
    "secret": "secrets",
    "secrets": "secrets",
    "password": "secrets",
    "passwords": "secrets",
    "api key": "secrets",
    "api keys": "secrets",
    "token": "secrets",
    "tokens": "secrets",
    "private": "private",
    "sensitive": "private",
    "personal": "people",
    "daily life": "daily_life",
    "daily_life": "daily_life",
    "general": "general",
}


DEFAULT_POLICIES: dict[str, str] = {
    "projects": "auto",
    "apps": "auto",
    "preferences": "ask",
    "people": "ask",
    "pets": "ask",
    "relationships": "ask",
    "devices": "ask",
    "vehicles": "ask",
    "places": "ask",
    "work": "ask",
    "app_settings": "ask",
    "game_settings": "ask",
    "screen_context": "ask",
    "daily_life": "short_term",
    "health": "ask",
    "financial": "never",
    "secrets": "never",
    "private": "ask",
    "general": "ask",
}


SENSITIVE_PATTERNS = (
    r"\bpassword\b",
    r"\bpasscode\b",
    r"\bapi\s*key\b",
    r"\bsecret\s*key\b",
    r"\baccess\s*token\b",
    r"\bbearer\s+[a-z0-9_\-\.]{12,}\b",
    r"\bssn\b",
    r"\bsocial\s+security\b",
    r"\bcredit\s+card\b",
    r"\bcard\s+number\b",
    r"\bcvv\b",
    r"\brouting\s+number\b",
    r"\baccount\s+number\b",
    r"\bseed\s+phrase\b",
    r"\bprivate\s+key\b",
)


@dataclass(slots=True)
class MemoryPreferenceDecision:
    """Result of applying user memory preferences to a candidate memory."""

    category: str
    policy: str
    action: str
    reason: str
    explicit: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MemoryPreferenceStore:
    """Crash-safe category policy store for memory auto-capture."""

    enabled: bool = True
    path: str | Path | None = None
    policies: dict[str, str] = field(default_factory=dict)
    schema_version: int = 1
    updated_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        self.path = Path(self.path) if self.path else Path("data/memory/memory_preferences.json")
        self.policies = dict(DEFAULT_POLICIES) | {canonical_category(k): normalize_policy(v) for k, v in dict(self.policies or {}).items()}
        self.load()

    def load(self) -> None:
        if not self.path or not self.path.exists():
            self.policies = dict(DEFAULT_POLICIES) | dict(self.policies or {})
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(payload, dict):
            return
        raw = payload.get("policies")
        if isinstance(raw, dict):
            merged = dict(DEFAULT_POLICIES)
            for key, value in raw.items():
                category = canonical_category(str(key))
                if category:
                    merged[category] = normalize_policy(str(value))
            self.policies = merged
        self.updated_at = str(payload.get("updated_at") or self.updated_at)

    def save(self) -> None:
        if not self.enabled or not self.path:
            return
        self.updated_at = utc_now_iso()
        atomic_write_json(Path(self.path), self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "updated_at": self.updated_at,
            "policies": dict(sorted(self.policies.items())),
        }

    def status(self) -> dict[str, Any]:
        counts: dict[str, int] = {policy: 0 for policy in sorted(VALID_POLICIES)}
        for policy in self.policies.values():
            counts[normalize_policy(policy)] = counts.get(normalize_policy(policy), 0) + 1
        return {
            "enabled": self.enabled,
            "path": str(self.path),
            "categories": len(self.policies),
            "policies": dict(sorted(self.policies.items())),
            "counts": counts,
            "updated_at": self.updated_at,
        }

    def set_policy(self, category: str, policy: str) -> str:
        canonical = canonical_category(category)
        normalized_policy = normalize_policy(policy)
        self.policies[canonical] = normalized_policy
        self.save()
        return canonical

    def reset(self) -> None:
        self.policies = dict(DEFAULT_POLICIES)
        self.save()

    def policy_for(self, category: str) -> str:
        return normalize_policy(self.policies.get(canonical_category(category), DEFAULT_POLICIES.get(canonical_category(category), "ask")))

    def policy_for_text(self, text: str, *, category: str = "general", entity_hint: Any | None = None) -> str:
        inferred = infer_memory_category(text, category=category, entity_hint=entity_hint)
        if is_secret_like(text):
            return "never"
        return self.policy_for(inferred)

    def decide(self, text: str, *, category: str = "general", entity_hint: Any | None = None, suggested_tier: str = "review", explicit: bool = False) -> MemoryPreferenceDecision:
        inferred = infer_memory_category(text, category=category, entity_hint=entity_hint)
        if is_secret_like(text):
            return MemoryPreferenceDecision(inferred, "never", "ignore", "secret-like data is never saved automatically", explicit=explicit)
        policy = self.policy_for(inferred)
        tier = str(suggested_tier or "review").strip().lower().replace("-", "_")
        if policy == "never":
            return MemoryPreferenceDecision(inferred, policy, "ignore", f"{inferred} memories are set to never remember", explicit=explicit)
        if explicit:
            if policy == "short_term":
                return MemoryPreferenceDecision(inferred, policy, "short_term", f"explicit {inferred} memories are kept temporarily by preference", explicit=True)
            return MemoryPreferenceDecision(inferred, policy, "save", f"explicit user memory request", explicit=True)
        if policy == "auto":
            if tier == "short_term":
                return MemoryPreferenceDecision(inferred, policy, "short_term", f"{inferred} memories are set to remember automatically", explicit=False)
            return MemoryPreferenceDecision(inferred, policy, "save", f"{inferred} memories are set to remember automatically", explicit=False)
        if policy == "short_term":
            return MemoryPreferenceDecision(inferred, policy, "short_term", f"{inferred} memories are set to temporary memory", explicit=False)
        return MemoryPreferenceDecision(inferred, policy, "review", f"{inferred} memories are set to ask before saving", explicit=False)

    def format_status(self) -> str:
        grouped: dict[str, list[str]] = {"auto": [], "ask": [], "short_term": [], "never": []}
        for category, policy in sorted(self.policies.items()):
            grouped.setdefault(normalize_policy(policy), []).append(display_category(category))
        parts: list[str] = ["Memory preferences are online, sir."]
        if grouped.get("auto"):
            parts.append("I can remember these automatically: " + join_words(grouped["auto"]) + ".")
        if grouped.get("ask"):
            parts.append("I will ask before saving these: " + join_words(grouped["ask"]) + ".")
        if grouped.get("short_term"):
            parts.append("I keep these temporary by default: " + join_words(grouped["short_term"]) + ".")
        if grouped.get("never"):
            parts.append("I will not save these: " + join_words(grouped["never"]) + ".")
        return " ".join(parts)


def normalize_policy(policy: str) -> str:
    normalized = normalize_text(policy).replace(" ", "_")
    aliases = {
        "automatic": "auto",
        "automatically": "auto",
        "always": "auto",
        "save": "auto",
        "remember": "auto",
        "ask_first": "ask",
        "review": "ask",
        "manual": "ask",
        "candidate": "ask",
        "do_not": "never",
        "dont": "never",
        "don_t": "never",
        "no": "never",
        "never_remember": "never",
        "temporary": "short_term",
        "temporarily": "short_term",
        "short": "short_term",
        "shortterm": "short_term",
        "short_term": "short_term",
    }
    return aliases.get(normalized, normalized if normalized in VALID_POLICIES else "ask")


def canonical_category(category: str) -> str:
    cleaned = normalize_text(str(category or "general").replace("_", " "))
    if not cleaned:
        return "general"
    if cleaned in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[cleaned]
    if cleaned.endswith(" details"):
        cleaned = cleaned[: -len(" details")]
    return CATEGORY_ALIASES.get(cleaned, cleaned.replace(" ", "_"))


def display_category(category: str) -> str:
    labels = {
        "app_settings": "app settings",
        "game_settings": "game settings",
        "screen_context": "screen context",
        "daily_life": "daily life",
    }
    return labels.get(canonical_category(category), canonical_category(category).replace("_", " "))


def is_secret_like(text: str) -> bool:
    lowered = str(text or "").lower()
    return any(re.search(pattern, lowered, flags=re.IGNORECASE) for pattern in SENSITIVE_PATTERNS)


def infer_memory_category(text: str, *, category: str = "general", entity_hint: Any | None = None) -> str:
    lowered = normalize_text(text)
    if is_secret_like(text):
        return "secrets"

    if isinstance(entity_hint, dict):
        entity_type = canonical_category(str(entity_hint.get("entity_type") or ""))
        if entity_type in {"people", "pets", "projects", "apps", "places", "devices", "vehicles"}:
            if entity_type == "people" and any(word in lowered for word in ["fiance", "fiancee", "wife", "girlfriend", "brother", "sister", "mother", "father", "relationship"]):
                return "relationships"
            return entity_type

    if any(phrase in lowered for phrase in ["my fiance", "my fiancee", "my wife", "my girlfriend", "my brother", "my sister", "related to me", "relationship"]):
        return "relationships"
    if any(word in lowered for word in ["dog", "cat", "pet", "golden doodle", "goldendoodle"]):
        return "pets"
    if any(word in lowered for word in ["jarvis", "project", "patch", "update", "commit", "version", "repo", "repository"]):
        return "projects"
    if any(phrase in lowered for phrase in ["game settings", "graphics settings", "sensitivity settings", "crosshair", "keybind", "keybinds", "fps setting"]):
        return "game_settings"
    if any(phrase in lowered for phrase in ["app settings", "application settings", "software settings", "these settings", "current settings", "remember this settings"]):
        return "app_settings"
    if any(word in lowered for word in ["screen", "ocr", "vision", "screenshot"]):
        return "screen_context"
    if any(word in lowered for word in ["spotify", "discord", "edge", "chrome", "studio one", "browser", "music app", "editor", "app"]):
        return "apps"
    if any(word in lowered for word in ["laptop", "desktop", "monitor", "gpu", "cpu", "microphone", "mic", "router", "phone", "device"]):
        return "devices"
    if any(word in lowered for word in ["car", "fusion", "vehicle", "truck"]):
        return "vehicles"
    if any(word in lowered for word in ["home", "work", "school", "office", "city", "place", "location"]):
        return "places"
    if any(word in lowered for word in ["prefer", "favorite", "like", "want", "style", "tone", "from now on", "going forward"]):
        return "preferences"
    if any(word in lowered for word in ["job", "career", "client", "customer", "work"]):
        return "work"
    if any(word in lowered for word in ["doctor", "headache", "medicine", "medical", "health"]):
        return "health"
    if any(word in lowered for word in ["bank", "credit", "loan", "debt", "income", "paycheck", "financial", "money"]):
        return "financial"
    if any(word in lowered for word in ["today", "right now", "dinner", "lunch", "breakfast", "ate"]):
        return "daily_life"
    return canonical_category(category)


def join_words(items: Iterable[str]) -> str:
    cleaned = [str(item) for item in items if str(item).strip()]
    if not cleaned:
        return "nothing"
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return ", ".join(cleaned[:-1]) + f", and {cleaned[-1]}"
