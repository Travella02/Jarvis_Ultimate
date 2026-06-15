"""Memory Agent implementation.

The Memory Agent owns explicit durable and temporary memory commands.  The
0.2.9 foundation adds always-on memory tiers: permanent long-term memory,
short-term facts that expire after a few days, and a daily chat archive that is
written incrementally while Jarvis runs.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jarvis.core.result import JarvisResult
from jarvis.memory.always_on import ChatArchiveStore, ShortTermFactStore
from jarvis.memory.long_term import LongTermMemoryStore


class Agent:
    name = "memory_agent"

    def __init__(self, *, manifest: dict[str, Any] | None = None, registry: Any | None = None) -> None:
        self.manifest = manifest or {}
        self.registry = registry

    def handle(self, command: str, context: dict[str, Any] | None = None) -> JarvisResult:
        context = context or {}
        config = context.get("config")
        long_term = context.get("long_term_memory") or self._fallback_long_term(config)
        short_term_facts = context.get("short_term_fact_memory") or self._fallback_short_term_facts(config)
        chat_archive = context.get("chat_archive") or self._fallback_chat_archive(config)

        text = " ".join(str(command or "").strip().split())
        lowered = text.lower()
        if not text:
            return JarvisResult.fail("I did not catch what you wanted me to remember, sir.", agent_name=self.name, action="memory_empty")

        if self._is_status(lowered):
            message = "\n\n".join([
                short_term_facts.format_status(),
                long_term.format_status(),
                chat_archive.format_status(),
            ])
            return JarvisResult.ok(
                message,
                agent_name=self.name,
                action="memory_status",
                data={"short_term_facts": short_term_facts.status(), "long_term_memory": long_term.status(), "chat_archive": chat_archive.status()},
            )

        chat_query = self._extract_chat_archive_query(text)
        if chat_query is not None:
            message = chat_archive.format_search(chat_query or text, limit=5)
            return JarvisResult.ok(
                message,
                agent_name=self.name,
                action="memory_chat_search",
                data={"query": chat_query or text, "matches": [item.to_dict() for item in chat_archive.search(chat_query or text, limit=5)]},
            )

        forget_query = self._extract_forget_query(text)
        if forget_query is not None:
            if not forget_query:
                return JarvisResult.confirmation(
                    "Do you want me to clear all long-term and temporary memories, sir?",
                    confirmation_prompt="Confirm clearing all saved long-term and temporary memories?",
                    agent_name=self.name,
                    action="memory_clear_confirm",
                    data={"requested_clear_all": True},
                )
            removed_long = long_term.forget(forget_query)
            removed_short = short_term_facts.forget(forget_query)
            removed_total = len(removed_long) + len(removed_short)
            if not removed_total:
                return JarvisResult.ok(
                    f"I could not find a saved memory matching {forget_query!r}, sir.",
                    agent_name=self.name,
                    action="memory_forget",
                    data={"query": forget_query, "removed": []},
                )
            message = "I forgot that memory, sir." if removed_total == 1 else f"I forgot {removed_total} matching memories, sir."
            return JarvisResult.ok(
                message,
                agent_name=self.name,
                action="memory_forget",
                data={
                    "query": forget_query,
                    "removed_long_term": [record.to_dict() for record in removed_long],
                    "removed_short_term": [record.to_dict() for record in removed_short],
                },
            )

        list_query = self._extract_list_query(text)
        if list_query is not None:
            long_matches = long_term.search(list_query, limit=5) if list_query else []
            short_matches = short_term_facts.search(list_query, limit=5) if list_query else []
            if list_query:
                message = self._format_combined_search(list_query, long_matches=long_matches, short_matches=short_matches)
            else:
                message = "\n\n".join([long_term.format_records(limit=7), short_term_facts.format_records(limit=7)])
            return JarvisResult.ok(
                message,
                agent_name=self.name,
                action="memory_list" if not list_query else "memory_search",
                data={
                    "query": list_query,
                    "long_term_matches": [item.to_dict() for item in long_matches],
                    "short_term_matches": [item.to_dict() for item in short_matches],
                },
            )

        memory_text = self._extract_memory_text(text)
        if memory_text:
            category = self._infer_category(memory_text)
            tags = self._infer_tags(memory_text, category=category)
            if self._is_short_term_request(text):
                days = self._extract_days(text) or getattr(short_term_facts, "default_days", 3)
                record = short_term_facts.add(memory_text, category=category, tags=tags, source="user", days=days, metadata={"source_command": text})
                if record is None:
                    return JarvisResult.fail(
                        "Temporary memory is disabled or I could not save that memory, sir.",
                        agent_name=self.name,
                        action="memory_store_short_term",
                        data={"memory_enabled": getattr(short_term_facts, "enabled", False)},
                    )
                return JarvisResult.ok(
                    f"I’ll remember that for the next {days} day{'s' if int(days) != 1 else ''}, sir.",
                    agent_name=self.name,
                    action="memory_store_short_term",
                    data={"memory": record.to_dict(), "short_term_facts": short_term_facts.status()},
                )

            record = long_term.add(memory_text, category=category, tags=tags, source="user", metadata={"source_command": text})
            if record is None:
                return JarvisResult.fail(
                    "Memory is disabled or I could not save that memory, sir.",
                    agent_name=self.name,
                    action="memory_store",
                    data={"memory_enabled": getattr(long_term, "enabled", False)},
                )
            return JarvisResult.ok(
                "I’ll remember that, sir.",
                agent_name=self.name,
                action="memory_store",
                data={"memory": record.to_dict(), "long_term_memory": long_term.status()},
            )

        return JarvisResult.ok(
            "I can save permanent memories, temporary memories, search recent chat archives, and forget saved memories now, sir.",
            agent_name=self.name,
            action="memory_help",
            data={"implemented": True, "long_term_memory": long_term.status(), "short_term_facts": short_term_facts.status(), "chat_archive": chat_archive.status()},
        )

    def _fallback_long_term(self, config: Any | None) -> LongTermMemoryStore:
        path = getattr(config, "data_dir", None) / "memory" / "long_term_memory.json" if getattr(config, "data_dir", None) else None
        return LongTermMemoryStore(path=path)

    def _fallback_short_term_facts(self, config: Any | None) -> ShortTermFactStore:
        path = getattr(config, "data_dir", None) / "memory" / "short_term_memory.json" if getattr(config, "data_dir", None) else None
        return ShortTermFactStore(path=path)

    def _fallback_chat_archive(self, config: Any | None) -> ChatArchiveStore:
        root = getattr(config, "data_dir", None) / "memory" / "chat_archive" if getattr(config, "data_dir", None) else None
        return ChatArchiveStore(root_dir=root)

    def _is_status(self, lowered: str) -> bool:
        return lowered in {
            "memory status",
            "jarvis memory status",
            "long term memory status",
            "long-term memory status",
            "chat archive status",
            "memory pipeline status",
        }

    def _extract_list_query(self, text: str) -> str | None:
        lowered = text.lower().strip(" ?.!\")'")
        list_phrases = (
            "what do you remember",
            "what memories do you have",
            "show memories",
            "list memories",
            "list memory",
            "show memory",
            "search memory",
            "search memories",
            "look up memory",
            "look up memories",
        )
        if not any(lowered.startswith(phrase) or phrase in lowered for phrase in list_phrases):
            return None
        about_match = re.search(r"(?:about|for)\s+(.+)$", text, flags=re.IGNORECASE)
        if about_match:
            return self._clean_tail(about_match.group(1))
        search_match = re.search(r"(?:search|look up)\s+memor(?:y|ies)\s+(?:for\s+)?(.+)$", text, flags=re.IGNORECASE)
        if search_match:
            return self._clean_tail(search_match.group(1))
        return ""

    def _extract_chat_archive_query(self, text: str) -> str | None:
        lowered = text.lower().strip(" ?.!\")'")
        chat_phrases = (
            "what did we talk about",
            "what were we talking about",
            "what did i say about",
            "what did you say about",
            "search chat",
            "search chats",
            "search conversation",
            "search conversations",
            "look through chat",
            "look through our chat",
            "chat archive",
            "conversation archive",
        )
        if not any(phrase in lowered for phrase in chat_phrases):
            return None
        about_match = re.search(r"(?:about|for)\s+(.+)$", text, flags=re.IGNORECASE)
        if about_match:
            return self._clean_tail(about_match.group(1))
        search_match = re.search(r"(?:search|look through)\s+(?:my\s+|our\s+)?(?:chat|chats|conversation|conversations)\s+(?:for\s+)?(.+)$", text, flags=re.IGNORECASE)
        if search_match:
            return self._clean_tail(search_match.group(1))
        return ""

    def _extract_forget_query(self, text: str) -> str | None:
        lowered = text.lower().strip(" ?.!\")'")
        if lowered in {"clear memory", "clear memories", "forget everything", "forget all memories", "delete all memories"}:
            return ""
        patterns = [
            r"^(?:jarvis,?\s*)?forget(?:\s+the)?\s+(?:memory|fact|preference|note)\s+(?:about\s+)?(.+)$",
            r"^(?:jarvis,?\s*)?forget\s+that\s+(.+)$",
            r"^(?:jarvis,?\s*)?forget\s+(.+)$",
            r"^(?:jarvis,?\s*)?(?:remove|delete)\s+(?:the\s+)?(?:memory|fact|preference|note)\s+(?:about\s+)?(.+)$",
            r"^(?:jarvis,?\s*)?do(?:\s+not|n't)\s+remember\s+(.+)$",
            r"^(?:jarvis,?\s*)?stop\s+remembering\s+(.+)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return self._clean_tail(match.group(1))
        return None

    def _extract_memory_text(self, text: str) -> str:
        patterns = [
            r"^(?:jarvis,?\s*)?remember\s+that\s+(.+)$",
            r"^(?:jarvis,?\s*)?remember\s+(.+)$",
            r"^(?:jarvis,?\s*)?(?:save|store)\s+this\s+(?:memory|fact|preference|note)?\s*:?\s*(.+)$",
            r"^(?:jarvis,?\s*)?(?:save|store)\s+that\s+(.+)$",
            r"^(?:jarvis,?\s*)?(?:make a note|note)\s+that\s+(.+)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return self._clean_memory_text(match.group(1))
        return ""

    def _is_short_term_request(self, text: str) -> bool:
        lowered = text.lower()
        return any(phrase in lowered for phrase in ["for a few days", "for the next few days", "temporarily", "short term", "short-term", "for now", "for today", "for tomorrow"])

    def _extract_days(self, text: str) -> int | None:
        lowered = text.lower()
        if "for today" in lowered:
            return 1
        if "for tomorrow" in lowered:
            return 2
        match = re.search(r"for\s+(\d+)\s+day", lowered)
        if match:
            return max(1, min(30, int(match.group(1))))
        if "few days" in lowered:
            return 3
        return None

    def _clean_memory_text(self, value: str) -> str:
        cleaned = self._clean_tail(value)
        cleaned = re.sub(r"\s+for\s+(?:a\s+)?few\s+days$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+for\s+the\s+next\s+few\s+days$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+temporarily$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+for\s+now$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+for\s+today$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+for\s+tomorrow$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+for\s+\d+\s+days?$", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip(" .?!")

    def _clean_tail(self, value: str) -> str:
        cleaned = " ".join(str(value or "").strip().split())
        cleaned = re.sub(r"^(that|about)\s+", "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned.strip(" .?!")

    def _infer_category(self, memory_text: str) -> str:
        lowered = memory_text.lower()
        if any(word in lowered for word in ["like", "prefer", "favorite", "favourite", "want", "from now on"]):
            return "preference"
        if any(word in lowered for word in ["jarvis", "project", "patch", "update", "commit", "version"]):
            return "project"
        if any(word in lowered for word in ["my name", "i am", "i'm", "fiance", "family", "dog", "car", "pet"]):
            return "personal"
        return "general"

    def _infer_tags(self, memory_text: str, *, category: str) -> list[str]:
        tags = [category]
        lowered = memory_text.lower()
        if "jarvis" in lowered:
            tags.append("jarvis")
        if "music" in lowered or "song" in lowered or "vocal" in lowered:
            tags.append("music")
        if "code" in lowered or "coding" in lowered or "python" in lowered:
            tags.append("coding")
        return tags

    def _format_combined_search(self, query: str, *, long_matches: list[Any], short_matches: list[Any]) -> str:
        if not long_matches and not short_matches:
            return f"I do not have any saved memories about {query}, sir."
        lines: list[str] = []
        if long_matches:
            if len(long_matches) == 1 and not short_matches:
                text = self._for_user(long_matches[0].record.text)
                return f"I remember that {text}, sir."
            lines.append("Permanent memories:")
            for item in long_matches:
                lines.append(f"- {self._for_user(item.record.text)}")
        if short_matches:
            lines.append("Temporary memories:")
            for item in short_matches:
                lines.append(f"- {self._for_user(item.record.text)}")
        return "\n".join(lines)

    @staticmethod
    def _for_user(text: str) -> str:
        cleaned = str(text or "").strip()
        replacements = [(r"\bmy\b", "your"), (r"\bi am\b", "you are"), (r"\bi'm\b", "you are"), (r"\bme\b", "you")]
        for pattern, replacement in replacements:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        return cleaned
