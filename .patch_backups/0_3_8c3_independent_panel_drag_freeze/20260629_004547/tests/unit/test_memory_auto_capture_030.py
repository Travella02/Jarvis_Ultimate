"""Tests for 0.3.0 memory auto-capture and candidate review."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from jarvis.agents.memory_agent.agent import Agent as MemoryAgent
from jarvis.brain.intent_classifier import IntentClassifier
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities, build_app_shell_snapshot
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.core.result import JarvisResult
from jarvis.memory.always_on import MemoryAutoCaptureEngine, MemoryCandidateStore, ShortTermFactStore
from jarvis.memory.long_term import LongTermMemoryStore


class MemoryAutoCapture030Tests(unittest.TestCase):
    def test_version_and_capabilities_include_auto_capture(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.8c2")
        capabilities = app_shell_capabilities()
        self.assertIn("memory_auto_capture_candidate_review", capabilities)
        self.assertIn("memory_candidate_queue", capabilities)
        self.assertIn("llm_ready_memory_tier_classification", capabilities)

    def test_candidate_store_saves_crash_safe_pending_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "memory_candidates.json"
            store = MemoryCandidateStore(path=path)
            record = store.add(
                "I prefer Jarvis patch zips with installer scripts",
                suggested_tier="long_term",
                category="preference",
                tags=["jarvis", "patches"],
                importance=5,
                confidence=0.9,
                reason="stable Jarvis workflow preference",
            )
            self.assertIsNotNone(record)
            self.assertTrue(path.exists())
            reloaded = MemoryCandidateStore(path=path)
            self.assertEqual(reloaded.status()["pending"], 1)
            self.assertIn("patch zips", reloaded.pending()[0].text)

    def test_auto_capture_classifies_stable_preference_as_long_term_candidate(self) -> None:
        engine = MemoryAutoCaptureEngine()
        decision = engine.classify_turn("From now on, always include apply steps directly in chat.")
        self.assertEqual(decision["decision"], "long_term")
        self.assertGreaterEqual(decision["importance"], 4)
        self.assertIn("stable", decision["reason"])

    def test_auto_capture_classifies_recent_testing_as_short_term(self) -> None:
        engine = MemoryAutoCaptureEngine()
        decision = engine.classify_turn("We are testing the memory pipeline right now.")
        self.assertEqual(decision["decision"], "short_term")
        self.assertEqual(decision["category"], "project")

    def test_memory_agent_can_review_approve_and_reject_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate_store = MemoryCandidateStore(path=Path(temp_dir) / "candidates.json")
            long_term = LongTermMemoryStore(path=Path(temp_dir) / "long.json")
            short_term = ShortTermFactStore(path=Path(temp_dir) / "short.json")
            candidate_store.add("my favorite IDE is VS Code", suggested_tier="long_term", category="preference")
            agent = MemoryAgent()
            context = {
                "memory_candidates": candidate_store,
                "long_term_memory": long_term,
                "short_term_fact_memory": short_term,
            }
            listed = agent.handle("Jarvis, what memories are waiting for review?", context=context)
            self.assertTrue(listed.success)
            self.assertIn("waiting for review", listed.message)
            approved = agent.handle("Jarvis, save that permanently", context=context)
            self.assertTrue(approved.success)
            self.assertIn("saved", approved.message.lower())
            self.assertEqual(long_term.status()["records"], 1)
            self.assertEqual(candidate_store.status()["approved"], 1)

    def test_runtime_auto_capture_saves_candidate_without_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = JarvisRuntime(project_root=temp_dir, llm_provider=Mock())
            runtime.started = True
            runtime.router = Mock()
            runtime.router.handle.return_value = JarvisResult.ok(
                "Understood, sir.",
                agent_name="conversation_agent",
                action="llm_chat",
                data={"intent": "general_chat"},
            )
            runtime.memory_preferences.set_policy("projects", "ask")
            result = runtime.handle_command("From now on, always keep Jarvis memory local-first.")
            self.assertTrue(result.success)
            self.assertGreaterEqual(runtime.memory_candidates.status()["pending"], 1)

    def test_runtime_auto_short_term_saves_recent_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = JarvisRuntime(project_root=temp_dir, llm_provider=Mock())
            runtime.started = True
            runtime.router = Mock()
            runtime.router.handle.return_value = JarvisResult.ok(
                "Testing note received, sir.",
                agent_name="conversation_agent",
                action="llm_chat",
                data={"intent": "general_chat"},
            )
            runtime.handle_command("We are testing temporary memory right now.")
            self.assertGreaterEqual(runtime.short_term_facts.status()["records"], 1)

    def test_intent_classifier_routes_candidate_review_to_memory(self) -> None:
        intent = IntentClassifier().classify("Jarvis, what memories are waiting for review?")
        self.assertEqual(intent.intent, "memory_search")

    def test_app_shell_snapshot_includes_candidate_status(self) -> None:
        class RuntimeStub:
            started = True
            registry = None
            ability_registry = None
            llm_provider = Mock(provider_name="mock", model="mock")
            tts_manager = Mock(provider_name="mock", enabled=True)
            stt_manager = Mock(provider_name="mock", enabled=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            store = MemoryCandidateStore(path=Path(temp_dir) / "candidates.json")
            store.add("test candidate", suggested_tier="review")
            runtime = RuntimeStub()
            runtime.long_term_memory = None
            runtime.short_term_memory = None
            runtime.short_term_facts = None
            runtime.chat_archive = None
            runtime.memory_maintenance = None
            runtime.memory_candidates = store
            snapshot = build_app_shell_snapshot(runtime=runtime)
            self.assertEqual(snapshot["runtime"]["memory"]["candidates"]["pending"], 1)


if __name__ == "__main__":
    unittest.main()
