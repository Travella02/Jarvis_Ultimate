"""Memory Agent implementation.

The Memory Agent owns explicit durable memory commands.  In this foundation
milestone Jarvis saves only what the user asks him to remember, using a local
JSON-backed long-term memory store.
"""

from __future__ import annotations

import re
from typing import Any

from jarvis.core.result import JarvisResult
from jarvis.memory.long_term import LongTermMemoryStore


class Agent:
    name = "memory_agent"

    def __init__(self, *, manifest: dict[str, Any] | None = None, registry: Any | None = None) -> None:
        self.manifest = manifest or {}
        self.registry = registry

    def handle(self, command: str, context: dict[str, Any] | None = None) -> JarvisResult:
        context = context or {}
        memory = context.get("long_term_memory")
        if memory is None:
            config = context.get("config")
            path = getattr(config, "data_dir", None) / "memory" / "long_term_memory.json" if getattr(config, "data_dir", None) else None
            memory = LongTermMemoryStore(path=path)

        text = " ".join(str(command or "").strip().split())
        lowered = text.lower()
        if not text:
            return JarvisResult.fail("I did not catch what you wanted me to remember, sir.", agent_name=self.name, action="memory_empty")

        if self._is_status(lowered):
            return JarvisResult.ok(memory.format_status(), agent_name=self.name, action="memory_status", data={"long_term_memory": memory.status()})

        list_query = self._extract_list_query(text)
        if list_query is not None:
            message = memory.format_records(limit=10, query=list_query)
            return JarvisResult.ok(
                message,
                agent_name=self.name,
                action="memory_list" if not list_query else "memory_search",
                data={"query": list_query, "matches": [item.to_dict() for item in memory.search(list_query, limit=10)] if list_query else []},
            )

        forget_query = self._extract_forget_query(text)
        if forget_query is not None:
            if not forget_query:
                return JarvisResult.confirmation(
                    "Do you want me to clear all long-term memories, sir?",
                    confirmation_prompt="Confirm clearing all saved long-term memories?",
                    agent_name=self.name,
                    action="memory_clear_confirm",
                    data={"requested_clear_all": True},
                )
            removed = memory.forget(forget_query)
            if not removed:
                return JarvisResult.ok(
                    f"I could not find a saved memory matching {forget_query!r}, sir.",
                    agent_name=self.name,
                    action="memory_forget",
                    data={"query": forget_query, "removed": []},
                )
            message = "I forgot that memory, sir." if len(removed) == 1 else f"I forgot {len(removed)} matching memories, sir."
            return JarvisResult.ok(
                message,
                agent_name=self.name,
                action="memory_forget",
                data={"query": forget_query, "removed": [record.to_dict() for record in removed]},
            )

        memory_text = self._extract_memory_text(text)
        if memory_text:
            category = self._infer_category(memory_text)
            tags = self._infer_tags(memory_text, category=category)
            record = memory.add(memory_text, category=category, tags=tags, source="user", metadata={"source_command": text})
            if record is None:
                return JarvisResult.fail(
                    "Memory is disabled or I could not save that memory, sir.",
                    agent_name=self.name,
                    action="memory_store",
                    data={"memory_enabled": getattr(memory, "enabled", False)},
                )
            return JarvisResult.ok(
                "I’ll remember that, sir.",
                agent_name=self.name,
                action="memory_store",
                data={"memory": record.to_dict(), "long_term_memory": memory.status()},
            )

        # Last resort: if the classifier routed here because of a memory word,
        # show helpful status rather than a placeholder.
        return JarvisResult.ok(
            "I can save, search, list, and forget explicit long-term memories now. Try: ‘Jarvis, remember that my favorite color is blue’ or ‘what do you remember about my favorite color?’",
            agent_name=self.name,
            action="memory_help",
            data={"implemented": True, "long_term_memory": memory.status()},
        )

    def _is_status(self, lowered: str) -> bool:
        return lowered in {"memory status", "jarvis memory status", "long term memory status", "long-term memory status"}

    def _extract_list_query(self, text: str) -> str | None:
        lowered = text.lower().strip(" ?.!")
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

    def _extract_forget_query(self, text: str) -> str | None:
        lowered = text.lower().strip(" ?.!")
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
                return self._clean_tail(match.group(1))
        return ""

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
        if any(word in lowered for word in ["my name", "i am", "i'm", "fiance", "family", "dog", "car"]):
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
