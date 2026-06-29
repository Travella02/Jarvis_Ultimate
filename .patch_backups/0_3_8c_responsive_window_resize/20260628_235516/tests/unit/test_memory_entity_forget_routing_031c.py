"""Tests for 0.3.1c entity forget routing guard."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jarvis.brain.intent_classifier import IntentClassifier
from jarvis.brain.router import JarvisRouter
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.core.registry import AgentRegistry
from jarvis.memory.entities import EntityMemoryStore
from jarvis.memory.long_term import LongTermMemoryStore


class EntityMemoryForgetRouting031cTests(unittest.TestCase):
    def test_version_and_capability_include_forget_routing_guard(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.8b")
        self.assertIn("entity_memory_forget_routing_guard", set(app_shell_capabilities()))

    def test_classifier_routes_plain_forget_entity_commands_to_memory_agent(self) -> None:
        result = IntentClassifier().classify("Forget Scout.")
        self.assertEqual(result.intent, "memory_write")
        self.assertGreaterEqual(result.confidence, 0.9)

    def test_router_forget_scout_removes_entity_instead_of_conversation_claiming_it_did(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = AgentRegistry()
            registry.load_builtin_agents()
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            long_term = LongTermMemoryStore(path=Path(tmp) / "long.json")
            router = JarvisRouter(registry=registry, entity_memory=entity_memory, long_term_memory=long_term)

            remember_scout = router.handle("Remember that my dog Scout is a golden doodle.")
            remember_nugget = router.handle("Remember that my dog Nugget is a golden doodle.")
            forget_scout = router.handle("Forget Scout.")
            list_pets = router.handle("List remembered pets.")

            self.assertTrue(remember_scout.success)
            self.assertTrue(remember_nugget.success)
            self.assertTrue(forget_scout.success)
            self.assertEqual(forget_scout.data.get("selected_agent"), "memory_agent")
            self.assertEqual(forget_scout.data.get("intent"), "memory_write")
            self.assertTrue(list_pets.success)
            self.assertIn("Nugget", list_pets.message)
            self.assertNotIn("Scout", list_pets.message)
            self.assertEqual([record.name for record in entity_memory.list_records(entity_type="pet")], ["Nugget"])


if __name__ == "__main__":
    unittest.main()
