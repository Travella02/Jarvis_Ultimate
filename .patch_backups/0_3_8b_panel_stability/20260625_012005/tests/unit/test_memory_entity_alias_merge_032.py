"""Tests for 0.3.2 entity merge, rename, and alias correction."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jarvis.agents.memory_agent.agent import Agent as MemoryAgent
from jarvis.brain.intent_classifier import IntentClassifier
from jarvis.brain.router import JarvisRouter
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.core.registry import AgentRegistry
from jarvis.memory.entities import EntityMemoryStore
from jarvis.memory.long_term import LongTermMemoryStore


class EntityMemoryAliasMerge032Tests(unittest.TestCase):
    def test_version_and_capability_include_entity_alias_merge(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.8a")
        self.assertIn("entity_memory_merge_alias_correction", set(app_shell_capabilities()))

    def test_store_merges_two_existing_entities_and_preserves_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EntityMemoryStore(path=Path(tmp) / "entities.json")
            store.upsert("Ken Lee", entity_type="person", summary="Ken Lee is your fiancée.", attributes={"relationship": "fiancée"})
            store.upsert("Kenleigh", entity_type="person", summary="Kenleigh is your fiancée.", attributes={"relationship": "fiancée"})

            merged = store.merge("Ken Lee", "Kenleigh", entity_type="person")

            self.assertIsNotNone(merged)
            self.assertEqual(merged.name, "Kenleigh")
            self.assertIn("Ken Lee", merged.aliases)
            self.assertEqual(store.status()["records"], 1)
            self.assertEqual(store.search("Ken Lee")[0].record.name, "Kenleigh")

    def test_store_renames_existing_entity_and_keeps_old_name_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EntityMemoryStore(path=Path(tmp) / "entities.json")
            store.upsert("Lee", entity_type="person", summary="Lee is your fiancée.", attributes={"relationship": "fiancée"})

            renamed = store.rename("Lee", "Kenleigh")

            self.assertIsNotNone(renamed)
            self.assertEqual(renamed.name, "Kenleigh")
            self.assertIn("Lee", renamed.aliases)
            self.assertIn("Kenleigh", renamed.summary)
            self.assertEqual(store.search("Lee")[0].record.name, "Kenleigh")

    def test_store_adds_and_removes_alias_without_deleting_entity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EntityMemoryStore(path=Path(tmp) / "entities.json")
            store.upsert("Kenleigh", entity_type="person", summary="Kenleigh is your fiancée.", attributes={"relationship": "fiancée"})

            aliased = store.add_alias("Kenleigh", "Ken Lee")

            self.assertIsNotNone(aliased)
            self.assertIn("Ken Lee", aliased.aliases)

            removed = store.remove_alias("Ken Lee", keep_query="Kenleigh")
            self.assertEqual(removed["records_changed"], 1)
            self.assertEqual(removed["removed_aliases"], ["Ken Lee"])
            self.assertEqual(store.status()["records"], 1)
            self.assertEqual(store.search("Kenleigh")[0].record.name, "Kenleigh")

    def test_memory_agent_handles_same_person_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            long_term = LongTermMemoryStore(path=Path(tmp) / "long.json")
            entity_memory.upsert("Ken Lee", entity_type="person", summary="Ken Lee is your fiancée.", attributes={"relationship": "fiancée"})
            agent = MemoryAgent()

            merge_result = agent.handle(
                "Ken Lee and Kenleigh are the same person.",
                context={"entity_memory": entity_memory, "long_term_memory": long_term},
            )
            who_result = agent.handle("Who is Ken Lee?", context={"entity_memory": entity_memory})

            self.assertTrue(merge_result.success)
            self.assertEqual(merge_result.action, "memory_entity_merge")
            self.assertIn("same person", merge_result.message.lower())
            self.assertIn("Kenleigh", who_result.message)
            self.assertIn("fiancée", who_result.message)

    def test_memory_agent_handles_rename_and_alias_removal_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            entity_memory.upsert("Lee", entity_type="person", summary="Lee is your fiancée.", attributes={"relationship": "fiancée"})
            agent = MemoryAgent()

            rename_result = agent.handle("Change Lee to Kenleigh.", context={"entity_memory": entity_memory})
            alias_result = agent.handle("Add Ken Lee as an alias for Kenleigh.", context={"entity_memory": entity_memory})
            remove_alias = agent.handle("Forget the alias Ken Lee, but keep Kenleigh.", context={"entity_memory": entity_memory})

            self.assertTrue(rename_result.success)
            self.assertTrue(alias_result.success)
            self.assertTrue(remove_alias.success)
            record = entity_memory.search("Kenleigh")[0].record
            self.assertEqual(record.name, "Kenleigh")
            self.assertIn("Lee", record.aliases)
            self.assertNotIn("Ken Lee", record.aliases)
            self.assertEqual(entity_memory.status()["records"], 1)

    def test_intent_classifier_routes_entity_correction_commands_to_memory(self) -> None:
        classifier = IntentClassifier()
        self.assertEqual(classifier.classify("Ken Lee and Kenleigh are the same person.").intent, "memory_write")
        self.assertEqual(classifier.classify("Change Ken Lee to Kenleigh.").intent, "memory_write")
        self.assertEqual(classifier.classify("Add Ken Lee as an alias for Kenleigh.").intent, "memory_write")
        self.assertEqual(classifier.classify("Forget the alias Ken Lee, but keep Kenleigh.").intent, "memory_write")

    def test_router_entity_merge_keeps_followup_lookup_natural(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = AgentRegistry()
            registry.load_builtin_agents()
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            long_term = LongTermMemoryStore(path=Path(tmp) / "long.json")
            router = JarvisRouter(registry=registry, entity_memory=entity_memory, long_term_memory=long_term)

            remember = router.handle("Remember that Ken Lee is my fiancée.")
            merge = router.handle("Ken Lee and Kenleigh are the same person.")
            lookup = router.handle("Who is Ken Lee?")

            self.assertTrue(remember.success)
            self.assertTrue(merge.success)
            self.assertEqual(merge.data.get("selected_agent"), "memory_agent")
            self.assertIn("Kenleigh", lookup.message)
            self.assertNotIn("structured entity", lookup.message.lower())
            self.assertEqual(entity_memory.status()["records"], 1)


if __name__ == "__main__":
    unittest.main()
