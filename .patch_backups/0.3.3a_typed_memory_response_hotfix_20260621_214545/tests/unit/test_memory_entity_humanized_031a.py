"""Tests for 0.3.1a entity memory response humanization."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jarvis.agents.memory_agent.agent import Agent as MemoryAgent
from jarvis.memory.entities import EntityMemoryStore, infer_entity_from_text
from jarvis.memory.long_term import LongTermMemoryStore
from jarvis.providers.llm.base import LLMResponse


class FakeEntityLLM:
    provider_name = "fake_llm"
    model = "fake-entity-humanizer"

    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[dict[str, object]] = []

    def chat(self, messages, **kwargs):
        self.calls.append({"messages": messages, "kwargs": kwargs})
        return LLMResponse.ok(self.content, provider=self.provider_name, model=self.model)


class EntityMemoryHumanized031aTests(unittest.TestCase):
    def test_relationship_inference_keeps_multi_word_names_and_second_person_summary(self) -> None:
        inferred = infer_entity_from_text("Ken Lee is my fiance")
        self.assertIsNotNone(inferred)
        self.assertEqual(inferred["name"], "Ken Lee")
        self.assertEqual(inferred["entity_type"], "person")
        self.assertEqual(inferred["attributes"]["relationship"], "fiancée")
        self.assertIn("your fiancée", inferred["summary"])

    def test_entity_question_fallback_is_natural_not_database_style(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            long_term = LongTermMemoryStore(path=Path(tmp) / "long.json")
            agent = MemoryAgent()
            agent.handle(
                "Jarvis, remember that Ken Lee is my fiance",
                context={"long_term_memory": long_term, "entity_memory": entity_memory},
            )
            result = agent.handle("Who is Ken Lee?", context={"entity_memory": entity_memory})
            self.assertTrue(result.success)
            self.assertEqual(result.message, "Ken Lee is your fiancée, sir.")
            self.assertNotIn("the user's", result.message.lower())
            self.assertNotIn("structured entity", result.message.lower())

    def test_entity_question_uses_llm_humanizer_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            entity_memory.upsert("Kenleigh", entity_type="person", summary="Kenleigh is your fiancée.", attributes={"relationship": "fiancée"})
            llm = FakeEntityLLM("Kenleigh is your fiancée, sir.")
            result = MemoryAgent().handle(
                "Who is Kenleigh?",
                context={"entity_memory": entity_memory, "llm_provider": llm},
            )
            self.assertTrue(result.success)
            self.assertEqual(result.message, "Kenleigh is your fiancée, sir.")
            self.assertEqual(len(llm.calls), 1)
            self.assertFalse(llm.calls[0]["kwargs"].get("stream", True))

    def test_list_remembered_pets_uses_entity_store_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            long_term = LongTermMemoryStore(path=Path(tmp) / "long.json")
            agent = MemoryAgent()
            agent.handle(
                "Remember that my dog Nugget is a golden doodle",
                context={"long_term_memory": long_term, "entity_memory": entity_memory},
            )
            result = agent.handle("List remembered pets", context={"entity_memory": entity_memory})
            self.assertTrue(result.success)
            self.assertIn("Nugget", result.message)
            self.assertIn("your dog", result.message)
            self.assertNotIn("I do not have", result.message)


if __name__ == "__main__":
    unittest.main()
