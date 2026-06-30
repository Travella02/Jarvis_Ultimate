"""Tests for 0.3.5 memory preferences and auto-remember controls."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from jarvis.agents.memory_agent.agent import Agent as MemoryAgent
from jarvis.brain.intent_classifier import IntentClassifier
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities, build_app_shell_snapshot
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.core.result import JarvisResult
from jarvis.core.events import EventBus
from jarvis.memory.always_on import MemoryAutoCaptureEngine, MemoryCandidateStore, ShortTermFactStore
from jarvis.memory.entities import EntityMemoryStore
from jarvis.memory.long_term import LongTermMemoryStore
from jarvis.memory.preferences import MemoryPreferenceStore, infer_memory_category


class MemoryPreferences035Tests(unittest.TestCase):
    def test_version_and_capabilities_include_memory_preferences(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d3")
        capabilities = set(app_shell_capabilities())
        self.assertIn("memory_preferences_auto_remember_controls", capabilities)
        self.assertIn("memory_policy_privacy_controls", capabilities)
        self.assertIn("screen_setting_memory_policy_ready", capabilities)

    def test_preference_store_persists_and_blocks_sensitive_categories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory_preferences.json"
            store = MemoryPreferenceStore(path=path)
            self.assertEqual(store.policy_for("projects"), "auto")
            self.assertEqual(store.policy_for_text("my password is hunter2"), "never")

            store.set_policy("people", "auto")
            self.assertEqual(store.policy_for("person"), "auto")

            reloaded = MemoryPreferenceStore(path=path)
            self.assertEqual(reloaded.policy_for("people"), "auto")

    def test_memory_agent_handles_preference_commands_naturally(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prefs = MemoryPreferenceStore(path=Path(tmp) / "prefs.json")
            agent = MemoryAgent()

            project_result = agent.handle("Jarvis, remember project rules automatically.", context={"memory_preferences": prefs})
            people_result = agent.handle("Ask me before remembering people.", context={"memory_preferences": prefs})
            financial_result = agent.handle("Never remember financial information.", context={"memory_preferences": prefs})
            status = agent.handle("Show my memory preferences.", context={"memory_preferences": prefs})

            self.assertEqual(project_result.action, "memory_preferences_set")
            self.assertIn("automatically", project_result.message)
            self.assertEqual(prefs.policy_for("projects"), "auto")
            self.assertEqual(people_result.action, "memory_preferences_set")
            self.assertEqual(prefs.policy_for("people"), "ask")
            self.assertEqual(financial_result.action, "memory_preferences_set")
            self.assertEqual(prefs.policy_for("financial"), "never")
            self.assertEqual(status.action, "memory_preferences_status")
            self.assertIn("Memory preferences are online", status.message)

    def test_explicit_memory_respects_never_policy_and_short_term_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prefs = MemoryPreferenceStore(path=Path(tmp) / "prefs.json")
            prefs.set_policy("financial", "never")
            prefs.set_policy("daily life", "short_term")
            long_term = LongTermMemoryStore(path=Path(tmp) / "long.json")
            short_term = ShortTermFactStore(path=Path(tmp) / "short.json")
            agent = MemoryAgent()

            blocked = agent.handle(
                "Remember that my bank balance is a test value.",
                context={"memory_preferences": prefs, "long_term_memory": long_term, "short_term_fact_memory": short_term},
            )
            temporary = agent.handle(
                "Remember that today I ate pancakes.",
                context={"memory_preferences": prefs, "long_term_memory": long_term, "short_term_fact_memory": short_term},
            )

            self.assertEqual(blocked.action, "secure_vault_storage_not_enabled")
            self.assertEqual(long_term.status()["records"], 0)
            self.assertEqual(temporary.action, "memory_store_short_term")
            self.assertEqual(short_term.status()["records"], 1)

    def test_future_screen_settings_request_is_policy_ready_without_saving_vague_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prefs = MemoryPreferenceStore(path=Path(tmp) / "prefs.json")
            long_term = LongTermMemoryStore(path=Path(tmp) / "long.json")
            agent = MemoryAgent()

            result = agent.handle(
                "Jarvis, remember these settings.",
                context={"memory_preferences": prefs, "long_term_memory": long_term},
            )

            self.assertEqual(result.action, "memory_settings_future_ready")
            self.assertIn("screen awareness", result.message)
            self.assertEqual(long_term.status()["records"], 0)
            self.assertEqual(infer_memory_category("remember these settings"), "app_settings")

    def test_auto_capture_uses_preferences_for_auto_save_review_short_term_and_never(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = JarvisRuntime.__new__(JarvisRuntime)
            runtime.config = SimpleNamespace(memory_auto_capture_enabled=True, memory_auto_short_term_enabled=True)
            runtime.memory_auto_capture = MemoryAutoCaptureEngine()
            runtime.memory_preferences = MemoryPreferenceStore(path=Path(tmp) / "prefs.json")
            runtime.memory_preferences.set_policy("projects", "auto")
            runtime.memory_preferences.set_policy("people", "ask")
            runtime.memory_preferences.set_policy("daily_life", "short_term")
            runtime.memory_preferences.set_policy("financial", "never")
            runtime.long_term_memory = LongTermMemoryStore(path=Path(tmp) / "long.json")
            runtime.short_term_facts = ShortTermFactStore(path=Path(tmp) / "short.json")
            runtime.memory_candidates = MemoryCandidateStore(path=Path(tmp) / "candidates.json")
            runtime.entity_memory = EntityMemoryStore(path=Path(tmp) / "entities.json")
            runtime.events = EventBus()
            runtime.llm_provider = None

            JarvisRuntime._auto_capture_memory_candidate(runtime, "From now on, Jarvis patches include tests.", JarvisResult.ok("Done"))
            JarvisRuntime._auto_capture_memory_candidate(runtime, "My brother is a test person.", JarvisResult.ok("Done"))
            JarvisRuntime._auto_capture_memory_candidate(runtime, "Today I ate pancakes.", JarvisResult.ok("Done"))
            JarvisRuntime._auto_capture_memory_candidate(runtime, "My bank account number is 123.", JarvisResult.ok("Done"))

            self.assertEqual(runtime.long_term_memory.status()["records"], 1)
            self.assertEqual(runtime.memory_candidates.status()["pending"], 1)
            self.assertEqual(runtime.short_term_facts.status()["records"], 1)
            self.assertEqual(runtime.memory_candidates.records[0].metadata["memory_preference"]["policy"], "ask")

    def test_intent_classifier_routes_memory_preference_commands(self) -> None:
        classifier = IntentClassifier()
        self.assertEqual(classifier.classify("Remember project rules automatically.").intent, "memory_write")
        self.assertEqual(classifier.classify("Ask me before remembering people.").intent, "memory_write")
        self.assertEqual(classifier.classify("Show my memory preferences.").intent, "memory_search")

    def test_app_shell_snapshot_exposes_memory_preferences_status(self) -> None:
        runtime = SimpleNamespace(
            started=True,
            llm_provider=SimpleNamespace(provider_name="mock", model="mock"),
            tts_manager=SimpleNamespace(provider_name="mock", enabled=True),
            stt_manager=SimpleNamespace(provider_name="mock", enabled=True),
            registry=SimpleNamespace(names=lambda enabled_only=True: []),
            ability_registry=SimpleNamespace(to_list=lambda enabled_only=True: [], count=lambda enabled_only=True: 0),
            long_term_memory=LongTermMemoryStore(path=Path(tempfile.gettempdir()) / "jarvis_test_ltm_unused.json"),
            short_term_memory=SimpleNamespace(status=lambda: {}),
            short_term_facts=ShortTermFactStore(path=Path(tempfile.gettempdir()) / "jarvis_test_stf_unused.json"),
            chat_archive=SimpleNamespace(status=lambda: {}),
            memory_candidates=MemoryCandidateStore(path=Path(tempfile.gettempdir()) / "jarvis_test_candidates_unused.json"),
            entity_memory=EntityMemoryStore(path=Path(tempfile.gettempdir()) / "jarvis_test_entities_unused.json"),
            memory_preferences=MemoryPreferenceStore(path=Path(tempfile.gettempdir()) / "jarvis_test_prefs_unused.json"),
            memory_maintenance=SimpleNamespace(status=lambda: {}),
        )
        snapshot = build_app_shell_snapshot(runtime=runtime)
        self.assertIn("preferences", snapshot["runtime"]["memory"])
        self.assertIn("policies", snapshot["runtime"]["memory"]["preferences"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
