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
from jarvis.memory.always_on import ChatArchiveStore, MemoryCandidateStore, ShortTermFactStore
from jarvis.memory.long_term import LongTermMemoryStore
from jarvis.memory.entities import EntityMemoryStore, normalize_entity_type


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
        memory_candidates = context.get("memory_candidates") or self._fallback_memory_candidates(config)
        entity_memory = context.get("entity_memory") or self._fallback_entity_memory(config)

        text = " ".join(str(command or "").strip().split())
        lowered = text.lower()
        if not text:
            return JarvisResult.fail("I did not catch what you wanted me to remember, sir.", agent_name=self.name, action="memory_empty")

        if self._is_status(lowered):
            message = "\n\n".join([
                short_term_facts.format_status(),
                long_term.format_status(),
                chat_archive.format_status(),
                entity_memory.format_status(),
            ])
            return JarvisResult.ok(
                message,
                agent_name=self.name,
                action="memory_status",
                data={"short_term_facts": short_term_facts.status(), "long_term_memory": long_term.status(), "chat_archive": chat_archive.status(), "memory_candidates": memory_candidates.status(), "entity_memory": entity_memory.status()},
            )

        entity_action = self._extract_entity_action(text)
        if entity_action is not None:
            action_name, query, entity_type = entity_action
            if action_name == "status":
                return JarvisResult.ok(
                    entity_memory.format_status(),
                    agent_name=self.name,
                    action="memory_entity_status",
                    data={"entity_memory": entity_memory.status()},
                )
            if action_name in {"list", "search"}:
                message = entity_memory.format_records(query=query, entity_type=entity_type or None, limit=8)
                return JarvisResult.ok(
                    message,
                    agent_name=self.name,
                    action="memory_entity_search" if query else "memory_entity_list",
                    data={
                        "query": query,
                        "entity_type": entity_type,
                        "matches": [match.to_dict() for match in entity_memory.search(query, entity_type=entity_type or None, limit=8)] if query else [],
                        "entity_memory": entity_memory.status(),
                    },
                )

        candidate_action = self._extract_candidate_action(text)
        if candidate_action is not None:
            action_name, query, all_matches = candidate_action
            if action_name == "list":
                return JarvisResult.ok(
                    memory_candidates.format_pending(),
                    agent_name=self.name,
                    action="memory_candidates_list",
                    data={"memory_candidates": memory_candidates.status(), "pending": [record.to_dict() for record in memory_candidates.pending()]},
                )
            if action_name == "approve":
                approved = memory_candidates.approve(query, all_matches=all_matches)
                if not approved:
                    return JarvisResult.ok(
                        "I do not have a matching memory candidate waiting for review, sir.",
                        agent_name=self.name,
                        action="memory_candidate_approve",
                        data={"approved": []},
                    )
                saved: list[dict[str, Any]] = []
                temporary: list[dict[str, Any]] = []
                entity_updates: list[dict[str, Any]] = []
                seen_saved_keys: set[str] = set()
                seen_temp_keys: set[str] = set()
                for candidate in approved:
                    candidate_key = self._memory_phrase_key(candidate.text)
                    if candidate.suggested_tier in {"short_term", "temporary"}:
                        record = short_term_facts.add(
                            candidate.text,
                            category=candidate.category,
                            tags=candidate.tags,
                            source="candidate_review",
                            importance=candidate.importance,
                            metadata={"candidate_id": candidate.id},
                        )
                        if record is not None and candidate_key not in seen_temp_keys:
                            temporary.append(record.to_dict())
                            seen_temp_keys.add(candidate_key)
                    else:
                        record = long_term.add(
                            candidate.text,
                            category=candidate.category,
                            tags=candidate.tags,
                            source="candidate_review",
                            importance=candidate.importance,
                            metadata={"candidate_id": candidate.id, "candidate_reason": candidate.reason},
                        )
                        if record is not None and candidate_key not in seen_saved_keys:
                            saved.append(record.to_dict())
                            seen_saved_keys.add(candidate_key)
                    entity_record = self._upsert_entity_from_text(
                        entity_memory,
                        candidate.text,
                        source="candidate_review",
                        metadata={"candidate_id": candidate.id, "candidate_tier": candidate.suggested_tier},
                        confidence=candidate.confidence,
                    )
                    if entity_record is not None:
                        entity_updates.append(entity_record.to_dict())
                if saved and not temporary:
                    message = "I saved that permanently, sir." if len(saved) == 1 else f"I saved {len(saved)} memories permanently, sir."
                elif temporary and not saved:
                    message = "I saved that as a temporary memory, sir." if len(temporary) == 1 else f"I saved {len(temporary)} temporary memories, sir."
                else:
                    message = f"I approved {len(approved)} memory candidate(s), sir."
                return JarvisResult.ok(
                    message,
                    agent_name=self.name,
                    action="memory_candidate_approve",
                    data={"approved": [record.to_dict() for record in approved], "saved_long_term": saved, "saved_short_term": temporary, "entity_updates": entity_updates},
                )
            if action_name == "reject":
                rejected = memory_candidates.reject(query, all_matches=all_matches)
                if not rejected:
                    return JarvisResult.ok(
                        "I do not have a matching memory candidate waiting for review, sir.",
                        agent_name=self.name,
                        action="memory_candidate_reject",
                        data={"rejected": []},
                    )
                message = "I rejected that memory candidate, sir." if len(rejected) == 1 else f"I rejected {len(rejected)} memory candidates, sir."
                return JarvisResult.ok(
                    message,
                    agent_name=self.name,
                    action="memory_candidate_reject",
                    data={"rejected": [record.to_dict() for record in rejected]},
                )

        chat_query = self._extract_chat_archive_query(text)
        if chat_query is not None:
            message = chat_archive.format_search(chat_query or text, limit=5, llm_provider=context.get("llm_provider"), timing=context.get("timing"))
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
            removed_entities = entity_memory.forget(forget_query)
            removed_total = len(removed_long) + len(removed_short) + len(removed_entities)
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
                    "removed_entities": [record.to_dict() for record in removed_entities],
                },
            )

        list_query = self._extract_list_query(text)
        if list_query is not None:
            long_matches = long_term.search(list_query, limit=5) if list_query else []
            short_matches = short_term_facts.search(list_query, limit=5) if list_query else []
            entity_matches = entity_memory.search(list_query, limit=5) if list_query else []
            if list_query:
                message = self._format_combined_search(list_query, long_matches=long_matches, short_matches=short_matches, entity_matches=entity_matches)
            else:
                message = "\n\n".join([long_term.format_records(limit=7), short_term_facts.format_records(limit=7), entity_memory.format_records(limit=7)])
            return JarvisResult.ok(
                message,
                agent_name=self.name,
                action="memory_list" if not list_query else "memory_search",
                data={
                    "query": list_query,
                    "long_term_matches": [item.to_dict() for item in long_matches],
                    "short_term_matches": [item.to_dict() for item in short_matches],
                    "entity_matches": [item.to_dict() for item in entity_matches],
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
            entity_record = self._upsert_entity_from_text(
                entity_memory,
                memory_text,
                source="user",
                metadata={"source_command": text},
                confidence=0.9,
            )
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
                data={"memory": record.to_dict(), "long_term_memory": long_term.status(), "entity_memory": entity_memory.status(), "entity_update": entity_record.to_dict() if entity_record is not None else None},
            )

        return JarvisResult.ok(
            "I can save permanent memories, temporary memories, search recent chat archives, and forget saved memories now, sir.",
            agent_name=self.name,
            action="memory_help",
            data={"implemented": True, "long_term_memory": long_term.status(), "short_term_facts": short_term_facts.status(), "chat_archive": chat_archive.status(), "memory_candidates": memory_candidates.status(), "entity_memory": entity_memory.status()},
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

    def _fallback_memory_candidates(self, config: Any | None) -> MemoryCandidateStore:
        path = getattr(config, "data_dir", None) / "memory" / "memory_candidates.json" if getattr(config, "data_dir", None) else None
        return MemoryCandidateStore(path=path)

    def _fallback_entity_memory(self, config: Any | None) -> EntityMemoryStore:
        path = getattr(config, "data_dir", None) / "memory" / "entities.json" if getattr(config, "data_dir", None) else None
        return EntityMemoryStore(path=path)

    def _is_status(self, lowered: str) -> bool:
        return lowered in {
            "memory status",
            "jarvis memory status",
            "long term memory status",
            "long-term memory status",
            "chat archive status",
            "memory pipeline status",
            "entity memory status",
            "structured memory status",
        }

    def _extract_entity_action(self, text: str) -> tuple[str, str, str] | None:
        lowered = text.lower().strip(" ?.!)\"'")
        if lowered in {"entity memory status", "structured memory status"}:
            return ("status", "", "")
        type_lookup = {
            "people": "person",
            "persons": "person",
            "person": "person",
            "pets": "pet",
            "pet": "pet",
            "projects": "project",
            "project": "project",
            "apps": "app",
            "app": "app",
            "tools": "app",
            "places": "place",
            "place": "place",
            "devices": "device",
            "device": "device",
            "vehicles": "vehicle",
            "vehicle": "vehicle",
            "cars": "vehicle",
            "organizations": "organization",
            "organization": "organization",
        }
        if any(phrase in lowered for phrase in ["entity memory", "structured memory", "remembered entities", "what entities"]):
            about_match = re.search(r"(?:about|for)\s+(.+)$", text, flags=re.IGNORECASE)
            if about_match:
                return ("search", self._clean_tail(about_match.group(1)), "")
            return ("list", "", "")
        list_match = re.search(r"(?:list|show)\s+(?:remembered\s+)?(people|persons|person|pets|pet|projects|project|apps|app|tools|places|place|devices|device|vehicles|vehicle|cars|organizations|organization)\b", lowered)
        if list_match:
            return ("list", "", normalize_entity_type(list_match.group(1)))
        who_match = re.search(r"^(?:jarvis,?\s*)?(?:who|what)\s+is\s+(.+)$", text, flags=re.IGNORECASE)
        if who_match:
            query = self._clean_tail(who_match.group(1))
            if query.lower() not in {"it", "that", "this"}:
                return ("search", query, "")
        know_match = re.search(r"^(?:jarvis,?\s*)?what\s+(?:do\s+you\s+know|entities?\s+do\s+you\s+remember)\s+about\s+(.+)$", text, flags=re.IGNORECASE)
        if know_match:
            return ("search", self._clean_tail(know_match.group(1)), "")
        return None

    def _extract_candidate_action(self, text: str) -> tuple[str, str, bool] | None:
        lowered = text.lower().strip(" ?.!)\"'")
        list_phrases = (
            "what memories are waiting for review",
            "what memory candidates",
            "memory candidates",
            "review memory candidates",
            "what did you learn recently",
            "what have you learned recently",
            "show memory candidates",
            "list memory candidates",
        )
        if any(phrase in lowered for phrase in list_phrases):
            return ("list", "", False)

        approve_phrases = ("save that permanently", "promote that", "approve that", "approve the memory", "save it permanently")
        if any(phrase in lowered for phrase in approve_phrases):
            return ("approve", "that", False)
        if "approve all" in lowered or "save all" in lowered or "promote all" in lowered:
            return ("approve", "", True)
        approve_match = re.search(r"(?:approve|promote|save)\s+(?:the\s+)?(?:candidate|memory candidate|memory)\s+(?:about\s+)?(.+)$", text, flags=re.IGNORECASE)
        if approve_match:
            return ("approve", self._clean_tail(approve_match.group(1)), False)

        reject_phrases = ("reject that", "forget that candidate", "do not remember that", "don't remember that", "dont remember that")
        if any(phrase in lowered for phrase in reject_phrases):
            return ("reject", "that", False)
        if "reject all" in lowered or "forget all candidates" in lowered or "clear memory candidates" in lowered:
            return ("reject", "", True)
        reject_match = re.search(r"(?:reject|forget|remove|delete)\s+(?:the\s+)?(?:candidate|memory candidate)\s+(?:about\s+)?(.+)$", text, flags=re.IGNORECASE)
        if reject_match:
            return ("reject", self._clean_tail(reject_match.group(1)), False)
        return None

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
        if any(word in lowered for word in ["my name", "i am", "i'm", "fiance", "fiancée", "family", "dog", "cat", "car", "pet", "wife", "brother"]):
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

    def _upsert_entity_from_text(
        self,
        entity_memory: EntityMemoryStore,
        text: str,
        *,
        source: str,
        metadata: dict[str, Any] | None = None,
        confidence: float | None = None,
    ) -> Any | None:
        if entity_memory is None or not hasattr(entity_memory, "upsert_from_text"):
            return None
        try:
            return entity_memory.upsert_from_text(text, source=source, metadata=metadata or {}, confidence=confidence)
        except Exception:
            # Entity memory should never break the core memory command.
            return None

    def _format_combined_search(self, query: str, *, long_matches: list[Any], short_matches: list[Any], entity_matches: list[Any] | None = None) -> str:
        entity_matches = entity_matches or []
        if not long_matches and not short_matches and not entity_matches:
            return f"I do not have any saved memories about {query}, sir."

        permanent = [self._for_user(item.record.text) for item in long_matches if getattr(item, "record", None) is not None]
        temporary = [self._for_user(item.record.text) for item in short_matches if getattr(item, "record", None) is not None]
        entities = []
        for item in entity_matches:
            record = getattr(item, "record", None)
            if record is None:
                continue
            summary = getattr(record, "summary", "") or f"{record.name} is remembered as {record.entity_type}"
            entities.append(f"{record.name} ({record.entity_type}): {summary}")
        permanent = self._dedupe_phrases(permanent)
        temporary = self._dedupe_phrases(temporary)
        entities = self._dedupe_phrases(entities)

        parts: list[str] = []
        if permanent:
            parts.append(f"permanently, {self._join_memory_phrases(permanent)}")
        if temporary:
            parts.append(f"for now, {self._join_memory_phrases(temporary)}")
        if entities:
            parts.append(f"as structured entity memory, {self._join_memory_phrases(entities)}")

        if len(parts) == 1:
            if permanent:
                return f"I remember that {self._join_memory_phrases(permanent)}, sir."
            if temporary:
                return f"For now, I remember that {self._join_memory_phrases(temporary)}, sir."
            return f"I have this structured entity memory, sir: {self._join_memory_phrases(entities)}."
        return "I remember a couple things, sir: " + "; and ".join(parts) + "."

    def _join_memory_phrases(self, phrases: list[str]) -> str:
        cleaned = [phrase.strip(" .?!") for phrase in phrases if phrase.strip()]
        if not cleaned:
            return "that"
        if len(cleaned) == 1:
            return cleaned[0]
        if len(cleaned) == 2:
            return f"{cleaned[0]} and {cleaned[1]}"
        shown = cleaned[:3]
        return ", ".join(shown[:-1]) + f", and {shown[-1]}"

    def _dedupe_phrases(self, phrases: list[str]) -> list[str]:
        # Prefer the most complete version of a memory fact.  For example,
        # keep "your favorite test color is blue" instead of also saying the
        # partial match "your favorite test color."
        normalized_pairs: list[tuple[int, str, str]] = []
        for index, phrase in enumerate(phrases):
            normalized = re.sub(r"[^a-z0-9\s]", " ", phrase.lower())
            normalized = " ".join(normalized.split())
            if normalized:
                normalized_pairs.append((index, phrase, normalized))

        sorted_pairs = sorted(normalized_pairs, key=lambda item: len(item[2]), reverse=True)
        kept: list[tuple[int, str, str]] = []
        for index, phrase, normalized in sorted_pairs:
            if any(normalized == old or normalized in old or old in normalized for _, _, old in kept):
                continue
            kept.append((index, phrase, normalized))

        kept.sort(key=lambda item: item[0])
        return [phrase for _, phrase, _ in kept]

    def _memory_phrase_key(self, text: str) -> str:
        return re.sub(r"[^a-z0-9\s]", " ", self._for_user(text).lower()).strip()

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
