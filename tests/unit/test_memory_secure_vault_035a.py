"""Tests for 0.3.6 sensitive memory secure-vault routing."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from jarvis.agents.memory_agent.agent import Agent as MemoryAgent
from jarvis.brain.intent_classifier import IntentClassifier
from jarvis.brain.router import JarvisRouter
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities, build_app_shell_snapshot
from jarvis.core.events import EventBus
from jarvis.core.registry import AgentRegistry
from jarvis.core.result import JarvisResult
from jarvis.memory.always_on import ChatArchiveStore, MemoryCandidateStore, ShortTermFactStore
from jarvis.memory.entities import EntityMemoryStore
from jarvis.memory.long_term import LongTermMemoryStore
from jarvis.memory.preferences import MemoryPreferenceStore
from jarvis.memory.secure_vault import SecureVaultStore, classify_vault_category, is_vault_like, redact_sensitive_text


class SecureVaultMemory035aTests(unittest.TestCase):
    def test_version_and_capabilities_include_secure_vault_routing(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d4")
        capabilities = set(app_shell_capabilities())
        self.assertIn("sensitive_memory_secure_vault_routing", capabilities)
        self.assertIn("password_manager_agent_foundation", capabilities)
        self.assertIn("normal_memory_secret_blocking", capabilities)

    def test_vault_classifier_finds_passwords_api_keys_and_financial_details(self) -> None:
        self.assertEqual(classify_vault_category("my password is hunter2"), "vault_password")
        self.assertEqual(classify_vault_category("my API key is sk-test-1234567890"), "vault_api_key")
        self.assertEqual(classify_vault_category("my bank account number is 123456789"), "vault_financial")
        self.assertTrue(is_vault_like("remember that my recovery code is 123456"))
        self.assertIn("[redacted", redact_sensitive_text("my password is hunter2"))

    def test_explicit_sensitive_memory_routes_to_vault_not_normal_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agent = MemoryAgent()
            prefs = MemoryPreferenceStore(path=Path(tmp) / "prefs.json")
            long_term = LongTermMemoryStore(path=Path(tmp) / "long.json")
            short_term = ShortTermFactStore(path=Path(tmp) / "short.json")
            entities = EntityMemoryStore(path=Path(tmp) / "entities.json")
            vault = SecureVaultStore(path=Path(tmp) / "vault.json")

            result = agent.handle(
                "Remember that my password is hunter2.",
                context={
                    "memory_preferences": prefs,
                    "long_term_memory": long_term,
                    "short_term_fact_memory": short_term,
                    "entity_memory": entities,
                    "secure_vault": vault,
                },
            )

            self.assertEqual(result.action, "secure_vault_storage_not_enabled")
            self.assertIn("normal memory", result.message)
            self.assertIn("not enabled yet", result.message)
            self.assertEqual(long_term.status()["records"], 0)
            self.assertEqual(short_term.status()["records"], 0)
            self.assertEqual(entities.status()["records"], 0)
            self.assertFalse((Path(tmp) / "vault.json").exists())
            decision = result.data["secure_vault_decision"]
            self.assertEqual(decision["vault_category"], "vault_password")
            self.assertIn("redacted", decision["redacted_preview"])
            self.assertNotIn("hunter2", decision["redacted_preview"])

    def test_financial_memory_routes_to_vault_even_when_policy_is_never(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agent = MemoryAgent()
            prefs = MemoryPreferenceStore(path=Path(tmp) / "prefs.json")
            prefs.set_policy("financial", "never")
            long_term = LongTermMemoryStore(path=Path(tmp) / "long.json")
            vault = SecureVaultStore(path=Path(tmp) / "vault.json")

            result = agent.handle(
                "Remember that my bank account number is 123456789.",
                context={"memory_preferences": prefs, "long_term_memory": long_term, "secure_vault": vault},
            )

            self.assertEqual(result.action, "secure_vault_storage_not_enabled")
            self.assertEqual(result.data["secure_vault_decision"]["vault_category"], "vault_financial")
            self.assertEqual(long_term.status()["records"], 0)

    def test_secure_vault_status_command(self) -> None:
        agent = MemoryAgent()
        vault = SecureVaultStore()
        result = agent.handle("Secure vault status.", context={"secure_vault": vault})
        self.assertEqual(result.action, "secure_vault_status")
        self.assertIn("encrypted vault storage is not enabled", result.message)

    def test_intent_classifier_routes_sensitive_vault_commands_to_memory(self) -> None:
        classifier = IntentClassifier()
        self.assertEqual(classifier.classify("Save my password for Netflix.").intent, "memory_write")
        self.assertEqual(classifier.classify("Secure vault status.").intent, "memory_search")

    def test_router_passes_secure_vault_to_memory_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = AgentRegistry()
            registry.register_from_manifest({"name": "memory_agent", "display_name": "Memory Agent", "enabled_by_default": True}, agent=MemoryAgent())
            vault = SecureVaultStore(path=Path(tmp) / "vault.json")
            router = JarvisRouter(
                registry=registry,
                events=EventBus(),
                secure_vault=vault,
                memory_preferences=MemoryPreferenceStore(path=Path(tmp) / "prefs.json"),
                long_term_memory=LongTermMemoryStore(path=Path(tmp) / "long.json"),
                short_term_fact_memory=ShortTermFactStore(path=Path(tmp) / "short.json"),
                chat_archive=ChatArchiveStore(root_dir=Path(tmp) / "archive"),
                memory_candidates=MemoryCandidateStore(path=Path(tmp) / "candidates.json"),
                entity_memory=EntityMemoryStore(path=Path(tmp) / "entities.json"),
            )

            result = router.handle("Remember that my API key is sk-test-1234567890.")
            self.assertEqual(result.action, "secure_vault_storage_not_enabled")
            self.assertEqual(result.data["secure_vault"]["stores_raw_values"], False)

    def test_app_shell_snapshot_exposes_secure_vault_status(self) -> None:
        runtime = SimpleNamespace(
            started=True,
            llm_provider=SimpleNamespace(provider_name="mock", model="mock"),
            tts_manager=SimpleNamespace(provider_name="mock", enabled=True),
            stt_manager=SimpleNamespace(provider_name="mock", enabled=True),
            registry=SimpleNamespace(names=lambda enabled_only=True: []),
            ability_registry=SimpleNamespace(to_list=lambda enabled_only=True: [], count=lambda enabled_only=True: 0),
            long_term_memory=LongTermMemoryStore(path=Path(tempfile.gettempdir()) / "jarvis_test_ltm_vault_unused.json"),
            short_term_memory=SimpleNamespace(status=lambda: {}),
            short_term_facts=ShortTermFactStore(path=Path(tempfile.gettempdir()) / "jarvis_test_stf_vault_unused.json"),
            chat_archive=SimpleNamespace(status=lambda: {}),
            memory_candidates=MemoryCandidateStore(path=Path(tempfile.gettempdir()) / "jarvis_test_candidates_vault_unused.json"),
            entity_memory=EntityMemoryStore(path=Path(tempfile.gettempdir()) / "jarvis_test_entities_vault_unused.json"),
            memory_preferences=MemoryPreferenceStore(path=Path(tempfile.gettempdir()) / "jarvis_test_prefs_vault_unused.json"),
            secure_vault=SecureVaultStore(path=Path(tempfile.gettempdir()) / "jarvis_test_secure_vault_unused.json"),
            memory_maintenance=SimpleNamespace(status=lambda: {}),
        )
        snapshot = build_app_shell_snapshot(runtime=runtime)
        self.assertIn("secure_vault", snapshot["runtime"]["memory"])
        self.assertFalse(snapshot["runtime"]["memory"]["secure_vault"]["stores_raw_values"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
