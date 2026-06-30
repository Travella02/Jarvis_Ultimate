"""Tests for 0.3.4a phonetic entity aliases and relationship label normalization."""

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from jarvis.agents.memory_agent.agent import Agent as MemoryAgent
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.memory.entities import EntityMemoryStore, infer_entity_from_text, phonetic_name_aliases


class EntityPhoneticRelationship034aTests(unittest.TestCase):
    def test_version_and_capabilities(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d4")
        capabilities = set(app_shell_capabilities())
        self.assertIn("entity_phonetic_aliases", capabilities)
        self.assertIn("relationship_label_normalization", capabilities)

    def test_fiance_variants_normalize_to_same_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EntityMemoryStore(path=Path(tmp) / "entities.json")
            store.upsert_from_text("Kenleigh is my fiance")

            for relation in ["fiance", "fiancee", "fiancé", "fiancée"]:
                records = store.find_by_relationship(relation, target_query="user", entity_type="person")
                self.assertEqual([record.name for record in records], ["Kenleigh"])

    def test_kenleigh_gets_conservative_phonetic_aliases(self) -> None:
        aliases = {alias.lower() for alias in phonetic_name_aliases("Kenleigh")}
        self.assertIn("ken lee", aliases)
        self.assertIn("kenley", aliases)

        with tempfile.TemporaryDirectory() as tmp:
            store = EntityMemoryStore(path=Path(tmp) / "entities.json")
            store.upsert_from_text("Kenleigh is my fiancée")

            self.assertEqual(store.resolve("Ken Lee", entity_type="person").name, "Kenleigh")
            self.assertEqual(store.resolve("Kenley", entity_type="person").name, "Kenleigh")

    def test_compact_spelling_replaces_split_stt_variant_when_user_corrects_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EntityMemoryStore(path=Path(tmp) / "entities.json")
            store.upsert_from_text("Ken Lee is my fiance")
            corrected = store.upsert_from_text("Kenleigh is my fiancée")

            people = store.list_records(entity_type="person")
            self.assertEqual(len(people), 1)
            self.assertEqual(corrected.name, "Kenleigh")
            self.assertEqual(people[0].name, "Kenleigh")
            self.assertIn("Ken Lee", people[0].aliases)

    def test_memory_agent_answers_who_is_my_fiance_with_any_spelling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            agent = MemoryAgent()
            agent.handle("Remember that Kenleigh is my fiance.", context={"entity_memory": entity_memory})

            result = agent.handle("Who is my fiancé?", context={"entity_memory": entity_memory})

            self.assertEqual(result.action, "memory_relationship_search")
            self.assertIn("Kenleigh is your fiancée", result.message)
            self.assertNotIn("I do not have anyone saved", result.message)

    def test_infer_person_relationship_includes_phonetic_aliases(self) -> None:
        inferred = infer_entity_from_text("Kenleigh is my fiance")
        self.assertIsNotNone(inferred)
        self.assertIn("Ken Lee", inferred["aliases"])
        self.assertEqual(inferred["relationships"][0]["type"], "fiancée")


if __name__ == "__main__":
    unittest.main()
