"""Tests for 0.3.4 relationship memory graph foundation."""

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from jarvis.agents.memory_agent.agent import Agent as MemoryAgent
from jarvis.brain.intent_classifier import IntentClassifier
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.memory.entities import EntityMemoryStore, infer_entity_from_text


class RelationshipMemory034Tests(unittest.TestCase):
    def test_version_and_capability_include_relationship_graph(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.8")
        capabilities = set(app_shell_capabilities())
        self.assertIn("relationship_memory_graph", capabilities)
        self.assertIn("relationship_memory_queries", capabilities)
        self.assertIn("saas_ready_entity_relationship_edges", capabilities)

    def test_inferred_people_and_pets_produce_relationship_edges(self) -> None:
        person = infer_entity_from_text("Kenleigh is my fiancée")
        self.assertIsNotNone(person)
        self.assertEqual(person["relationships"][0]["type"], "fiancée")
        self.assertEqual(person["relationships"][0]["to"], "user")

        pet = infer_entity_from_text("my dog Nugget is a golden doodle")
        self.assertIsNotNone(pet)
        self.assertEqual(pet["relationships"][0]["type"], "dog")
        self.assertEqual(pet["relationships"][0]["to"], "user")

    def test_store_can_query_relationships_as_graph_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EntityMemoryStore(path=Path(tmp) / "entities.json")
            store.upsert_from_text("Kenleigh is my fiancée")
            store.upsert_from_text("my dog Nugget is a golden doodle")

            fiancee_records = store.find_by_relationship("fiancee", target_query="me", entity_type="person")
            dog_records = store.find_by_relationship("dogs", target_query="user", entity_type="pet")
            self.assertEqual([record.name for record in fiancee_records], ["Kenleigh"])
            self.assertEqual([record.name for record in dog_records], ["Nugget"])

            edges = store.relationship_edges(target_query="me")
            summaries = " ".join(edge["summary"] for edge in edges)
            self.assertIn("Kenleigh is your fiancée", summaries)
            self.assertIn("Nugget is your dog", summaries)

    def test_memory_agent_answers_relationship_queries_naturally(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            agent = MemoryAgent()
            agent.handle("Remember that Kenleigh is my fiancée.", context={"entity_memory": entity_memory})
            agent.handle("Remember that my dog Nugget is a golden doodle.", context={"entity_memory": entity_memory})

            fiancee = agent.handle("Who is my fiancée?", context={"entity_memory": entity_memory})
            relation = agent.handle("How is Kenleigh related to me?", context={"entity_memory": entity_memory})
            dogs = agent.handle("What dogs do I have?", context={"entity_memory": entity_memory})

            self.assertEqual(fiancee.action, "memory_relationship_search")
            self.assertIn("Kenleigh is your fiancée", fiancee.message)
            self.assertEqual(relation.action, "memory_relationship_lookup")
            self.assertIn("Kenleigh is your fiancée", relation.message)
            self.assertIn("Nugget", dogs.message)
            self.assertNotIn("structured entity", dogs.message.lower())

    def test_cross_entity_project_relationships_are_queryable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EntityMemoryStore(path=Path(tmp) / "entities.json")
            store.upsert_from_text("Kenleigh works on Jarvis")
            agent = MemoryAgent()

            result = agent.handle("Who works on Jarvis?", context={"entity_memory": store})

            self.assertEqual(result.action, "memory_relationship_lookup")
            self.assertIn("Kenleigh works on Jarvis", result.message)

    def test_intent_classifier_routes_relationship_queries_to_memory(self) -> None:
        classifier = IntentClassifier()
        self.assertEqual(classifier.classify("How is Kenleigh related to me?").intent, "memory_search")
        self.assertEqual(classifier.classify("Who is my fiancée?").intent, "memory_search")
        self.assertEqual(classifier.classify("What dogs do I have?").intent, "memory_search")


if __name__ == "__main__":
    unittest.main()
