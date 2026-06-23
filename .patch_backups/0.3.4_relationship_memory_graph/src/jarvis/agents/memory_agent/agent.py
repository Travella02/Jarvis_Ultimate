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

        entity_edit_action = self._extract_entity_edit_action(text)
        if entity_edit_action is not None:
            handled = self._handle_entity_edit_action(entity_memory, entity_edit_action)
            if handled is not None:
                return handled

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
                records, match_data = self._select_entity_records(
                    entity_memory,
                    query=query,
                    entity_type=entity_type or None,
                    limit=8,
                )
                fallback_message = self._format_entity_records_naturally(
                    records,
                    query=query,
                    entity_type=entity_type or None,
                    action_name=action_name,
                )
                message = self._humanize_entity_response_with_llm(
                    command=text,
                    records=records,
                    fallback_message=fallback_message,
                    llm_provider=context.get("llm_provider"),
                    timing=context.get("timing"),
                )
                return JarvisResult.ok(
                    message,
                    agent_name=self.name,
                    action="memory_entity_search" if query else "memory_entity_list",
                    data={
                        "query": query,
                        "entity_type": entity_type,
                        "matches": match_data,
                        "entity_memory": entity_memory.status(),
                        "humanized_entity_response": message != entity_memory.format_records(query=query, entity_type=entity_type or None, limit=8),
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
                message = self._format_combined_search(
                    list_query,
                    long_matches=long_matches,
                    short_matches=short_matches,
                    entity_matches=entity_matches,
                    llm_provider=context.get("llm_provider"),
                    timing=context.get("timing"),
                )
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

    def _handle_entity_edit_action(self, entity_memory: EntityMemoryStore, action: dict[str, str]) -> JarvisResult | None:
        action_name = action.get("action", "")
        entity_type = action.get("entity_type") or None
        if action_name == "merge":
            source = action.get("source", "")
            target = action.get("target", "")
            record = entity_memory.merge(source, target, entity_type=entity_type)
            if record is None:
                return JarvisResult.ok(
                    f"I could not find enough saved entity memory to merge {source} and {target}, sir.",
                    agent_name=self.name,
                    action="memory_entity_merge",
                    data={"source": source, "target": target, "entity_type": entity_type, "merged": None, "entity_memory": entity_memory.status()},
                )
            return JarvisResult.ok(
                f"Understood, sir. I’ll treat {source} and {record.name} as the same {self._entity_label(record.entity_type)} now.",
                agent_name=self.name,
                action="memory_entity_merge",
                data={"source": source, "target": target, "entity_type": entity_type, "merged": record.to_dict(), "entity_memory": entity_memory.status()},
            )

        if action_name == "rename":
            source = action.get("source", "")
            target = action.get("target", "")
            record = entity_memory.rename(source, target, entity_type=entity_type)
            if record is None:
                return JarvisResult.ok(
                    f"I could not find an entity memory named {source}, sir.",
                    agent_name=self.name,
                    action="memory_entity_rename",
                    data={"source": source, "target": target, "entity_type": entity_type, "renamed": None, "entity_memory": entity_memory.status()},
                )
            return JarvisResult.ok(
                f"Understood, sir. I renamed {source} to {record.name} and kept the old name as an alias.",
                agent_name=self.name,
                action="memory_entity_rename",
                data={"source": source, "target": target, "entity_type": entity_type, "renamed": record.to_dict(), "entity_memory": entity_memory.status()},
            )

        if action_name == "add_alias":
            target = action.get("target", "")
            alias = action.get("alias", "")
            record = entity_memory.add_alias(target, alias, entity_type=entity_type)
            if record is None:
                return JarvisResult.ok(
                    f"I could not find an entity memory named {target}, sir.",
                    agent_name=self.name,
                    action="memory_entity_alias_add",
                    data={"target": target, "alias": alias, "entity_type": entity_type, "updated": None, "entity_memory": entity_memory.status()},
                )
            return JarvisResult.ok(
                f"Understood, sir. I added {alias} as another name for {record.name}.",
                agent_name=self.name,
                action="memory_entity_alias_add",
                data={"target": target, "alias": alias, "entity_type": entity_type, "updated": record.to_dict(), "entity_memory": entity_memory.status()},
            )

        if action_name == "remove_alias":
            alias = action.get("alias", "")
            keep = action.get("keep", "")
            result = entity_memory.remove_alias(alias, keep_query=keep or None, entity_type=entity_type)
            record = result.get("record") if isinstance(result, dict) else None
            removed = result.get("removed_aliases", []) if isinstance(result, dict) else []
            if not removed:
                target_phrase = f" on {keep}" if keep else ""
                return JarvisResult.ok(
                    f"I could not find the alias {alias}{target_phrase}, sir.",
                    agent_name=self.name,
                    action="memory_entity_alias_remove",
                    data={"alias": alias, "keep": keep, "entity_type": entity_type, "removed_aliases": [], "entity_memory": entity_memory.status()},
                )
            kept_name = getattr(record, "name", keep or "that entity")
            return JarvisResult.ok(
                f"Understood, sir. I removed {alias} as an alias and kept {kept_name} saved.",
                agent_name=self.name,
                action="memory_entity_alias_remove",
                data={"alias": alias, "keep": keep, "entity_type": entity_type, "removed_aliases": removed, "updated": record.to_dict() if hasattr(record, "to_dict") else None, "entity_memory": entity_memory.status()},
            )

        return None

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

    def _select_entity_records(
        self,
        entity_memory: EntityMemoryStore,
        *,
        query: str = "",
        entity_type: str | None = None,
        limit: int = 8,
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        if query:
            matches = entity_memory.search(query, entity_type=entity_type, limit=limit)
            return [match.record for match in matches], [match.to_dict() for match in matches]
        if hasattr(entity_memory, "list_records"):
            records = entity_memory.list_records(entity_type=entity_type, limit=limit)
        else:
            records = list(getattr(entity_memory, "records", ()))[-max(1, int(limit)) :]
            if entity_type:
                type_filter = normalize_entity_type(entity_type)
                records = [record for record in records if getattr(record, "entity_type", "") == type_filter]
        return list(records), [record.to_dict() for record in records if hasattr(record, "to_dict")]

    def _format_entity_records_naturally(
        self,
        records: list[Any],
        *,
        query: str = "",
        entity_type: str | None = None,
        action_name: str = "search",
    ) -> str:
        if not records:
            if query:
                return f"I do not have anything saved about {query}, sir."
            if entity_type:
                return f"I do not have any remembered {self._plural_entity_label(entity_type)} yet, sir."
            return "I do not have any structured entity memories yet, sir."
        if query and len(records) == 1:
            return self._single_entity_sentence(records[0])
        if len(records) == 1:
            record = records[0]
            label = self._entity_label(getattr(record, "entity_type", "entity"))
            sentence = self._single_entity_sentence(record)
            if action_name == "list":
                return f"I have {getattr(record, 'name', 'that')} saved as {self._article(label)} {label}. {sentence}"
            return sentence
        lines = ["Here is what I have saved, sir:"]
        for record in records:
            lines.append(f"- {self._display_entity_name(record)}: {self._entity_brief(record)}")
        return "\n".join(lines)

    def _humanize_entity_response_with_llm(
        self,
        *,
        command: str,
        records: list[Any],
        fallback_message: str,
        llm_provider: Any | None,
        timing: Any | None = None,
    ) -> str:
        if llm_provider is None or not hasattr(llm_provider, "chat"):
            return fallback_message
        facts = self._entity_facts_for_prompt(records)
        system_prompt = (
            "You are Jarvis, a natural personal assistant. Rewrite the entity-memory answer "
            "as a short, conversational reply to the user. Say 'your fiancée', 'your dog', "
            "or 'your project' instead of 'the user's fiancée', 'the user's dog', or database-style wording. "
            "Do not mention structured memory, records, search results, internal fields, confidence, or schemas. "
            "Only use the provided remembered facts. Do not invent details. End naturally with 'sir' when it fits."
        )
        user_prompt = (
            f"User asked: {command}\n\n"
            f"Remembered facts:\n{facts if facts else '(none)'}\n\n"
            f"Fallback answer:\n{fallback_message}\n\n"
            "Return only the natural Jarvis answer."
        )
        try:
            response = llm_provider.chat(
                [{"role": "user", "content": user_prompt}],
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=180,
                timing=timing,
                stream=False,
            )
        except Exception:
            return fallback_message
        if getattr(response, "success", False) is True:
            content = getattr(response, "content", "")
            if isinstance(content, str) and content.strip():
                cleaned = " ".join(content.strip().split())
                if cleaned and self._entity_llm_response_is_grounded(cleaned, records):
                    return cleaned
        return fallback_message

    def _entity_llm_response_is_grounded(self, response: str, records: list[Any]) -> bool:
        # The LLM is only used to polish wording. If it mentions a proper-name
        # entity that was not in the selected records, fall back to the safe
        # deterministic answer so stale names do not reappear after forgetting.
        allowed_names: set[str] = set()
        allowed_tokens: set[str] = {"i", "you", "your", "jarvis", "sir"}
        for record in records:
            values = [getattr(record, "name", "")]
            values.extend(getattr(record, "aliases", []) or [])
            for value in values:
                normalized = re.sub(r"[^a-z0-9\s]", " ", str(value or "").lower())
                normalized = " ".join(normalized.split())
                if not normalized:
                    continue
                allowed_names.add(normalized)
                allowed_tokens.update(normalized.split())

        candidate_words = re.findall(r"\b[A-Z][A-Za-z0-9_\-']{1,40}\b", response or "")
        safe_capitalized = {"I", "You", "Your", "Jarvis", "Sir", "Here"}
        for word in candidate_words:
            if word in safe_capitalized:
                continue
            normalized_word = re.sub(r"[^a-z0-9]", "", word.lower())
            if normalized_word and normalized_word not in allowed_tokens:
                return False
        return True

    def _entity_facts_for_prompt(self, records: list[Any]) -> str:
        lines: list[str] = []
        for record in records:
            name = self._display_entity_name(record)
            entity_type = getattr(record, "entity_type", "entity")
            summary = self._second_person_summary(getattr(record, "summary", ""))
            attributes = getattr(record, "attributes", {}) if isinstance(getattr(record, "attributes", {}), dict) else {}
            attr_parts = [f"{key}: {value}" for key, value in sorted(attributes.items()) if value not in (None, "", [], {})]
            parts = [f"name: {name}", f"type: {entity_type}"]
            if summary:
                parts.append(f"summary: {summary}")
            if attr_parts:
                parts.append("attributes: " + "; ".join(attr_parts))
            lines.append("- " + "; ".join(parts))
        return "\n".join(lines)

    def _single_entity_sentence(self, record: Any) -> str:
        name = self._display_entity_name(record)
        entity_type = getattr(record, "entity_type", "entity")
        attributes = getattr(record, "attributes", {}) if isinstance(getattr(record, "attributes", {}), dict) else {}
        relation = attributes.get("relationship")
        if entity_type == "person" and relation:
            return f"{name} is your {relation}, sir."
        species = attributes.get("species")
        if entity_type == "pet" and species:
            extra = attributes.get("breed_or_note") or attributes.get("breed")
            if extra:
                extra_phrase = self._lowercase_leading_article(str(extra))
                if extra_phrase.startswith("is "):
                    extra_phrase = extra_phrase[3:]
                return f"{name} is your {species}, {extra_phrase}, sir."
            return f"{name} is your {species}, sir."
        summary = self._second_person_summary(getattr(record, "summary", ""))
        if summary:
            return self._ensure_sir(summary)
        label = self._entity_label(entity_type)
        return f"{name} is saved as {self._article(label)} {label}, sir."

    def _entity_brief(self, record: Any) -> str:
        sentence = self._single_entity_sentence(record)
        sentence = sentence.strip()
        if sentence.lower().endswith(", sir."):
            sentence = sentence[:-6] + "."
        elif sentence.lower().endswith(" sir."):
            sentence = sentence[:-5] + "."
        return sentence

    def _display_entity_name(self, record: Any) -> str:
        name = " ".join(str(getattr(record, "name", "") or "that").strip().split())
        entity_type = normalize_entity_type(str(getattr(record, "entity_type", "entity") or "entity"))
        if entity_type in {"person", "pet"} and name and name == name.lower():
            return name.title()
        return name or "that"

    def _entity_label(self, entity_type: str) -> str:
        label = normalize_entity_type(entity_type or "entity").replace("_", " ").strip()
        return label or "entity"

    def _plural_entity_label(self, entity_type: str) -> str:
        label = self._entity_label(entity_type)
        irregular = {"person": "people"}
        if label in irregular:
            return irregular[label]
        if label.endswith("s"):
            return label
        return label + "s"

    def _article(self, label: str) -> str:
        return "an" if label[:1].lower() in {"a", "e", "i", "o", "u"} else "a"

    def _lowercase_leading_article(self, text: str) -> str:
        cleaned = " ".join(str(text or "").strip().strip(" .").split())
        if not cleaned:
            return ""
        lowered = cleaned[:1].lower() + cleaned[1:]
        if lowered.startswith(("a ", "an ", "the ")):
            return f"is {lowered}"
        return lowered

    def _second_person_summary(self, summary: str) -> str:
        text = " ".join(str(summary or "").split())
        replacements = [
            ("the user's", "your"),
            ("The user's", "Your"),
            ("user's", "your"),
            ("User's", "Your"),
            ("the user", "you"),
            ("The user", "You"),
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        return text

    def _ensure_sir(self, sentence: str) -> str:
        text = " ".join(str(sentence or "").strip().split())
        if not text:
            return "Yes, sir."
        if text.lower().endswith("sir.") or text.lower().endswith("sir"):
            return text if text.endswith(".") else text + "."
        text = text.rstrip(".")
        return f"{text}, sir."

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

    def _extract_entity_edit_action(self, text: str) -> dict[str, str] | None:
        cleaned_text = re.sub(r"^(?:jarvis,?\s*)?(?:remember\s+that\s+)?", "", text.strip(), flags=re.IGNORECASE).strip(" .?!\"'")
        lowered = cleaned_text.lower()
        type_words = (
            "person|people|dog|dogs|cat|cats|pet|pets|project|projects|app|apps|tool|tools|place|places|"
            "device|devices|vehicle|vehicles|car|cars|organization|organizations|company|companies|team|teams"
        )

        same_match = re.search(rf"^(.+?)\s+and\s+(.+?)\s+are\s+the\s+same\s+({type_words})$", cleaned_text, flags=re.IGNORECASE)
        if same_match:
            source = self._clean_tail(same_match.group(1))
            target = self._clean_tail(same_match.group(2))
            entity_type = normalize_entity_type(same_match.group(3))
            return {"action": "merge", "source": source, "target": target, "entity_type": entity_type}

        same_as_match = re.search(rf"^(.+?)\s+is\s+the\s+same(?:\s+({type_words}))?\s+as\s+(.+)$", cleaned_text, flags=re.IGNORECASE)
        if same_as_match:
            source = self._clean_tail(same_as_match.group(1))
            target = self._clean_tail(same_as_match.group(3))
            entity_type = normalize_entity_type(same_as_match.group(2) or "") if same_as_match.group(2) else ""
            return {"action": "merge", "source": source, "target": target, "entity_type": entity_type}

        rename_match = re.search(r"^(?:rename|change)\s+(.+?)\s+to\s+(.+)$", cleaned_text, flags=re.IGNORECASE)
        if rename_match:
            return {"action": "rename", "source": self._clean_tail(rename_match.group(1)), "target": self._clean_tail(rename_match.group(2)), "entity_type": ""}

        add_alias_match = re.search(r"^(?:add\s+)?(.+?)\s+as\s+(?:an?\s+)?(?:alias|nickname|name)\s+for\s+(.+)$", cleaned_text, flags=re.IGNORECASE)
        if add_alias_match:
            return {"action": "add_alias", "alias": self._clean_tail(add_alias_match.group(1)), "target": self._clean_tail(add_alias_match.group(2)), "entity_type": ""}

        alias_for_match = re.search(r"^(.+?)\s+is\s+(?:an?\s+)?(?:alias|nickname|another\s+name)\s+for\s+(.+)$", cleaned_text, flags=re.IGNORECASE)
        if alias_for_match:
            return {"action": "add_alias", "alias": self._clean_tail(alias_for_match.group(1)), "target": self._clean_tail(alias_for_match.group(2)), "entity_type": ""}

        call_match = re.search(r"^call\s+(.+?)\s+(.+)$", cleaned_text, flags=re.IGNORECASE)
        if call_match and " app" not in lowered and " program" not in lowered and " tool" not in lowered:
            return {"action": "add_alias", "target": self._clean_tail(call_match.group(1)), "alias": self._clean_tail(call_match.group(2)), "entity_type": ""}

        remove_alias_match = re.search(r"^(?:forget|remove|delete)\s+(?:the\s+)?(?:alias|nickname|name)\s+(.+?)(?:,?\s+but\s+keep\s+(.+))?$", cleaned_text, flags=re.IGNORECASE)
        if remove_alias_match:
            return {"action": "remove_alias", "alias": self._clean_tail(remove_alias_match.group(1)), "keep": self._clean_tail(remove_alias_match.group(2) or ""), "entity_type": ""}

        remove_from_match = re.search(r"^(?:remove|delete)\s+(.+?)\s+as\s+(?:an?\s+)?(?:alias|nickname|name)\s+(?:from|for)\s+(.+)$", cleaned_text, flags=re.IGNORECASE)
        if remove_from_match:
            return {"action": "remove_alias", "alias": self._clean_tail(remove_from_match.group(1)), "keep": self._clean_tail(remove_from_match.group(2)), "entity_type": ""}

        return None

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

    def _format_combined_search(
        self,
        query: str,
        *,
        long_matches: list[Any],
        short_matches: list[Any],
        entity_matches: list[Any] | None = None,
        llm_provider: Any | None = None,
        timing: Any | None = None,
    ) -> str:
        entity_matches = entity_matches or []
        entity_records = [item.record for item in entity_matches if getattr(item, "record", None) is not None]
        if not long_matches and not short_matches and not entity_records:
            return f"I do not have any saved memories about {query}, sir."

        permanent = [self._for_user(item.record.text) for item in long_matches if getattr(item, "record", None) is not None]
        temporary = [self._for_user(item.record.text) for item in short_matches if getattr(item, "record", None) is not None]
        entities = [self._entity_brief(record) for record in entity_records]
        permanent = self._dedupe_phrases(permanent)
        temporary = self._dedupe_phrases(temporary)
        entities = self._dedupe_phrases(entities)

        if entity_records and not permanent and not temporary:
            fallback = self._format_entity_records_naturally(entity_records, query=query, action_name="search")
            return self._humanize_entity_response_with_llm(
                command=f"What do you remember about {query}?",
                records=entity_records,
                fallback_message=fallback,
                llm_provider=llm_provider,
                timing=timing,
            )

        parts: list[str] = []
        if permanent:
            parts.append(f"permanently, {self._join_memory_phrases(permanent)}")
        if temporary:
            parts.append(f"for now, {self._join_memory_phrases(temporary)}")
        if entities:
            parts.append(f"about {query}, {self._join_memory_phrases(entities)}")

        if len(parts) == 1:
            if permanent:
                fallback = f"I remember that {self._join_memory_phrases(permanent)}, sir."
            elif temporary:
                fallback = f"For now, I remember that {self._join_memory_phrases(temporary)}, sir."
            else:
                fallback = f"I remember that {self._join_memory_phrases(entities)}, sir."
        else:
            fallback = "I remember a couple things, sir: " + "; and ".join(parts) + "."

        return self._humanize_memory_search_response_with_llm(
            command=f"What do you remember about {query}?",
            query=query,
            permanent=permanent,
            temporary=temporary,
            entity_records=entity_records,
            fallback_message=fallback,
            llm_provider=llm_provider,
            timing=timing,
        )

    def _humanize_memory_search_response_with_llm(
        self,
        *,
        command: str,
        query: str,
        permanent: list[str],
        temporary: list[str],
        entity_records: list[Any],
        fallback_message: str,
        llm_provider: Any | None,
        timing: Any | None = None,
    ) -> str:
        if llm_provider is None or not hasattr(llm_provider, "chat"):
            return fallback_message
        fact_lines: list[str] = []
        fact_lines.extend(f"- permanent memory: {item}" for item in permanent)
        fact_lines.extend(f"- temporary memory: {item}" for item in temporary)
        entity_facts = self._entity_facts_for_prompt(entity_records)
        if entity_facts:
            fact_lines.append(entity_facts)
        system_prompt = (
            "You are Jarvis, a natural personal assistant. Rewrite the memory answer as a short, "
            "normal conversational reply to the user. Do not mention structured entity memory, records, "
            "database fields, schemas, search results, or internal tiers unless the user asks for diagnostics. "
            "Use second-person wording like 'your fiancée', 'your dog', and 'your project'. "
            "Only use the provided facts and do not invent details. End naturally with 'sir' when it fits."
        )
        facts_text = "\n".join(fact_lines) if fact_lines else "(none)"
        user_prompt = (
            f"User asked: {command}\n\n"
            f"Search query: {query}\n\n"
            f"Remembered facts:\n{facts_text}\n\n"
            f"Fallback answer:\n{fallback_message}\n\n"
            "Return only the natural Jarvis answer."
        )
        try:
            response = llm_provider.chat(
                [{"role": "user", "content": user_prompt}],
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=220,
                timing=timing,
                stream=False,
            )
        except Exception:
            return fallback_message
        if getattr(response, "success", False) is True:
            content = getattr(response, "content", "")
            if isinstance(content, str) and content.strip():
                cleaned = " ".join(content.strip().split())
                forbidden = ("structured entity", "database", "schema", "search result", "internal tier")
                if cleaned and not any(term in cleaned.lower() for term in forbidden):
                    return cleaned
        return fallback_message

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
