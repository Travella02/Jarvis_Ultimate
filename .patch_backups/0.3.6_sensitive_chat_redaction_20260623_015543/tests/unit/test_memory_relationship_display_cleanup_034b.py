"""Tests for 0.3.4b relationship display cleanup."""

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from jarvis.agents.memory_agent.agent import Agent as MemoryAgent
from jarvis.clients.app_shell.bridge import app_shell_capabilities
from jarvis.memory.entities import EntityMemoryStore


class RelationshipDisplayCleanup034bTests(unittest.TestCase):
    def test_capability_is_reported(self) -> None:
        self.assertIn("relationship_display_cleanup", set(app_shell_capabilities()))

    def test_merged_fiance_spellings_do_not_become_display_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EntityMemoryStore(path=Path(tmp) / "entities.json")
            store.upsert_from_text("Ken Lee is my fiance")
            store.upsert_from_text("Kenleigh is my fiancée")

            record = store.resolve("Ken Lee", entity_type="person")
            self.assertIsNotNone(record)
            self.assertEqual(record.name, "Kenleigh")
            self.assertEqual(record.attributes.get("relationship"), "fiancée")
            self.assertNotIsInstance(record.attributes.get("relationship"), list)

    def test_legacy_relationship_list_is_displayed_as_single_relation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EntityMemoryStore(path=Path(tmp) / "entities.json")
            store.upsert(
                "Kenleigh",
                entity_type="person",
                attributes={"relationship": ["fiance fiancee", "fiancée"]},
                relationships=[{"type": ["fiance fiancee", "fiancée"], "to": "user"}],
                summary="Kenleigh is your fiancée.",
            )
            agent = MemoryAgent()

            result = agent.handle("Who is Ken Lee?", context={"entity_memory": store})

            self.assertIn("Kenleigh is your fiancée", result.message)
            self.assertNotIn("[", result.message)
            self.assertNotIn("]", result.message)
            self.assertNotIn("fiance fiancee", result.message.lower())


if __name__ == "__main__":
    unittest.main()
