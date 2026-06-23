"""Tests for 0.3.1 scalable entity memory foundation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from jarvis.agents.memory_agent.agent import Agent as MemoryAgent
from jarvis.brain.intent_classifier import IntentClassifier
from jarvis.brain.router import JarvisRouter
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities, build_app_shell_snapshot
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.core.registry import AgentRegistry
from jarvis.core.result import JarvisResult
from jarvis.memory.always_on import MemoryAutoCaptureEngine, MemoryCandidateStore, ShortTermFactStore
from jarvis.memory.entities import EntityMemoryStore, infer_entity_from_text
from jarvis.memory.long_term import LongTermMemoryStore


class EntityMemory031Tests(unittest.TestCase):
    def test_version_and_capabilities_include_entity_memory(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.5")
        capabilities = set(app_shell_capabilities())
        self.assertIn("structured_entity_memory_foundation", capabilities)
        self.assertIn("scalable_entity_type_registry", capabilities)
        self.assertIn("entity_memory_context_injection", capabilities)

    def test_entity_store_upserts_searches_and_persists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "entities.json"
            store = EntityMemoryStore(path=path)
            record = store.upsert(
                "Kenleigh",
                entity_type="person",
                summary="Kenleigh is your fiancée.",
                attributes={"relationship": "fiancée"},
                tags=["person", "relationship"],
            )
            self.assertIsNotNone(record)
            self.assertEqual(record.entity_type, "person")
            self.assertTrue(path.exists())

            reloaded = EntityMemoryStore(path=path)
            matches = reloaded.search("Kenleigh")
            self.assertEqual(len(matches), 1)
            self.assertIn("fiancée", matches[0].record.summary)
            self.assertEqual(reloaded.status()["by_type"]["person"], 1)

    def test_entity_registry_accepts_new_entity_types_without_schema_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EntityMemoryStore(path=Path(tmp) / "entities.json")
            definition = store.register_entity_type(
                "subscription",
                label="Subscription",
                aliases=["plan", "membership"],
                default_attributes=["renewal", "tier"],
            )
            self.assertIsNotNone(definition)
            store.upsert("Jarvis Pro", entity_type="subscription", summary="A SaaS billing plan.")
            self.assertIn("subscription", store.status()["entity_types"])
            self.assertEqual(store.search("billing plan")[0].record.entity_type, "subscription")

    def test_entity_inference_stays_conservative_and_skips_secrets(self) -> None:
        person = infer_entity_from_text("Kenleigh is my fiancée")
        self.assertIsNotNone(person)
        self.assertEqual(person["entity_type"], "person")
        self.assertEqual(person["name"], "Kenleigh")

        pet = infer_entity_from_text("my dog Scout is a golden doodle")
        self.assertIsNotNone(pet)
        self.assertEqual(pet["entity_type"], "pet")
        self.assertEqual(pet["name"], "Scout")

        self.assertIsNone(infer_entity_from_text("my password is hunter2"))

    def test_memory_agent_explicit_memory_updates_entity_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            long_term = LongTermMemoryStore(path=Path(tmp) / "long.json")
            agent = MemoryAgent()
            result = agent.handle(
                "Jarvis, remember that Kenleigh is my fiancée",
                context={"long_term_memory": long_term, "entity_memory": entity_memory},
            )
            self.assertTrue(result.success)
            self.assertEqual(long_term.status()["records"], 1)
            self.assertEqual(entity_memory.status()["records"], 1)
            self.assertEqual(entity_memory.search("Kenleigh")[0].record.entity_type, "person")

    def test_candidate_approval_promotes_entity_memory_when_inferable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate_store = MemoryCandidateStore(path=Path(tmp) / "candidates.json")
            candidate_store.add("my dog Scout is a golden doodle", suggested_tier="long_term", category="personal")
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            long_term = LongTermMemoryStore(path=Path(tmp) / "long.json")
            short_term = ShortTermFactStore(path=Path(tmp) / "short.json")
            agent = MemoryAgent()
            result = agent.handle(
                "Jarvis, save that permanently",
                context={
                    "memory_candidates": candidate_store,
                    "long_term_memory": long_term,
                    "short_term_fact_memory": short_term,
                    "entity_memory": entity_memory,
                },
            )
            self.assertTrue(result.success)
            self.assertEqual(entity_memory.status()["records"], 1)
            self.assertEqual(entity_memory.search("Scout")[0].record.entity_type, "pet")

    def test_memory_search_includes_entity_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            entity_memory.upsert("Jarvis Ultimate", entity_type="project", summary="Jarvis Ultimate is the SaaS assistant project.")
            agent = MemoryAgent()
            result = agent.handle("What do you remember about Jarvis Ultimate?", context={"entity_memory": entity_memory})
            self.assertTrue(result.success)
            self.assertIn("Jarvis Ultimate", result.message)
            self.assertEqual(result.data["entity_matches"][0]["entity_type"], "project")

    def test_auto_capture_decision_carries_entity_hint(self) -> None:
        decision = MemoryAutoCaptureEngine().classify_turn("Kenleigh is my fiancée")
        self.assertEqual(decision["decision"], "long_term")
        self.assertIsNotNone(decision.get("entity"))
        self.assertEqual(decision["entity"]["entity_type"], "person")

    def test_runtime_and_router_expose_entity_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = JarvisRuntime(project_root=tmp, llm_provider=Mock())
            self.assertTrue(hasattr(runtime, "entity_memory"))
            runtime.entity_memory.upsert("Jarvis Ultimate", entity_type="project", summary="Local-first assistant.")
            snapshot = build_app_shell_snapshot(runtime=runtime)
            self.assertEqual(snapshot["runtime"]["memory"]["entities"]["records"], 1)

    def test_intent_classifier_routes_entity_queries_to_memory(self) -> None:
        intent = IntentClassifier().classify("Who is Kenleigh?")
        self.assertEqual(intent.intent, "memory_search")

    def test_router_passes_entity_memory_to_memory_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = AgentRegistry()
            registry.load_builtin_agents()
            entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            router = JarvisRouter(registry=registry, entity_memory=entity_memory)
            result = router.handle("Jarvis, remember that Scout is my dog")
            self.assertTrue(result.success)
            self.assertEqual(entity_memory.status()["records"], 1)


if __name__ == "__main__":
    unittest.main()
