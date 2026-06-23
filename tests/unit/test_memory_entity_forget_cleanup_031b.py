"""Tests for 0.3.1c entity forget cleanup and hallucination guard."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jarvis.agents.memory_agent.agent import Agent as MemoryAgent
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.memory.entities import EntityMemoryStore
from jarvis.memory.long_term import LongTermMemoryStore
from jarvis.providers.llm.base import LLMResponse


class FakeEntityLLM:
    provider_name = "fake_llm"
    model = "fake-entity-humanizer"

    def __init__(self, content: str) -> None:
        self.content = content

    def chat(self, messages, **kwargs):
        return LLMResponse.ok(self.content, provider=self.provider_name, model=self.model)


class EntityMemoryForgetCleanup031bTests(unittest.TestCase):
    def test_version_and_capability_include_forget_cleanup_guard(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.5a")
        self.assertIn("entity_memory_forget_cleanup_guard", set(app_shell_capabilities()))

    def test_forget_removes_duplicate_entity_records_by_name_alias_and_source_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EntityMemoryStore(path=Path(tmp) / "entities.json")
            store.upsert("Scout", entity_type="pet", summary="Scout is your dog.", attributes={"species": "dog"})
            store.upsert("Scout Old Record", entity_type="pet", summary="Scout is another saved pet record.", attributes={"species": "dog"})
            store.upsert("Nugget", entity_type="pet", summary="Nugget is your dog.", attributes={"species": "dog"})

            removed = store.forget("Scout")

            self.assertEqual(len(removed), 2)
            self.assertEqual(store.status()["records"], 1)
            self.assertEqual(store.list_records(entity_type="pet")[0].name, "Nugget")
            self.assertFalse(store.search("Scout"))

    def test_memory_agent_forget_then_list_pets_does_not_show_removed_pet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            long_term = LongTermMemoryStore(path=Path(tmp) / "long.json")
            agent = MemoryAgent()
            context = {"long_term_memory": long_term, "entity_memory": entity_memory}

            agent.handle("Remember that my dog Scout is a golden doodle", context=context)
            agent.handle("Remember that my dog Nugget is a golden doodle", context=context)
            forget_result = agent.handle("Forget Scout", context=context)
            list_result = agent.handle("List remembered pets", context=context)

            self.assertTrue(forget_result.success)
            self.assertTrue(list_result.success)
            self.assertIn("Nugget", list_result.message)
            self.assertNotIn("Scout", list_result.message)
            self.assertEqual([record.name for record in entity_memory.list_records(entity_type="pet")], ["Nugget"])

    def test_llm_humanizer_falls_back_if_it_mentions_stale_unselected_entity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            entity_memory.upsert("Nugget", entity_type="pet", summary="Nugget is your dog.", attributes={"species": "dog"})
            stale_llm = FakeEntityLLM("You have two dogs: Nugget and Scout, sir.")

            result = MemoryAgent().handle(
                "List remembered pets",
                context={"entity_memory": entity_memory, "llm_provider": stale_llm},
            )

            self.assertTrue(result.success)
            self.assertIn("Nugget", result.message)
            self.assertNotIn("Scout", result.message)
            self.assertIn("your dog", result.message)


if __name__ == "__main__":
    unittest.main()
