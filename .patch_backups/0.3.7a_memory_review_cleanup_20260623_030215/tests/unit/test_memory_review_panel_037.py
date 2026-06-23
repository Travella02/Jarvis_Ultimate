"""Tests for 0.3.7 memory review panel behavior."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from jarvis.agents.memory_agent.agent import Agent as MemoryAgent
from jarvis.brain.intent_classifier import IntentClassifier
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.memory.always_on import ShortTermFactStore
from jarvis.memory.entities import EntityMemoryStore
from jarvis.memory.long_term import LongTermMemoryStore
from jarvis.ui.workspace import UIWorkspaceState


class MemoryReviewPanel037Tests(unittest.TestCase):
    def test_version_and_capabilities_include_memory_review_panel(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.7")
        capabilities = set(app_shell_capabilities())
        self.assertIn("memory_review_panel", capabilities)
        self.assertIn("ranked_memory_review_bullets", capabilities)
        self.assertIn("spoken_memory_review_summary_control", capabilities)

    def test_show_everything_returns_short_spoken_message_and_panel_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            long_term = LongTermMemoryStore(path=root / "long.json")
            short_term = ShortTermFactStore(path=root / "short.json")
            entities = EntityMemoryStore(path=root / "entities.json")
            long_term.add("Kenleigh helps test the Jarvis memory system.", category="project", importance=3)
            short_term.add("Kenleigh tested the latest Jarvis patch today.", category="work", importance=2)
            entities.upsert_from_text("Kenleigh is my fiancée")
            agent = MemoryAgent()

            result = agent.handle(
                "Show everything you remember about Kenleigh.",
                context={
                    "long_term_memory": long_term,
                    "short_term_fact_memory": short_term,
                    "entity_memory": entities,
                },
            )

            self.assertTrue(result.success)
            self.assertEqual(result.action, "memory_review_show")
            self.assertEqual(result.message, "Here is everything I know about Kenleigh, sir.")
            self.assertNotIn("-", result.message)
            review = result.data["memory_review"]
            self.assertEqual(review["display_subject"], "Kenleigh")
            self.assertGreaterEqual(review["item_count"], 2)
            self.assertEqual(review["items"][0]["importance"], 5)
            self.assertIn("Kenleigh is your fiancée", review["items"][0]["text"])
            event_types = [event.event_type for event in result.events]
            self.assertIn("ui.open_panel", event_types)
            self.assertIn("ui.workspace_card", event_types)
            card_event = next(event for event in result.events if event.event_type == "ui.workspace_card")
            self.assertEqual(card_event.data["card_type"], "memory_review")
            self.assertEqual(card_event.data["payload"]["panel_type"], "memory_review")

    def test_speak_everything_reads_ranked_review_when_asked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entities = EntityMemoryStore(path=root / "entities.json")
            entities.upsert_from_text("Kenleigh is my fiancée")
            agent = MemoryAgent()

            result = agent.handle("Speak everything you remember about Kenleigh.", context={"entity_memory": entities})

            self.assertEqual(result.action, "memory_review_speak")
            self.assertIn("Here is everything I know about Kenleigh, sir:", result.message)
            self.assertIn("1. Kenleigh is your fiancée", result.message)

    def test_workspace_applies_memory_review_panel_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entities = EntityMemoryStore(path=Path(tmp) / "entities.json")
            entities.upsert_from_text("Nugget is my dog")
            result = MemoryAgent().handle("Show everything you remember about Nugget.", context={"entity_memory": entities})
            workspace = UIWorkspaceState()
            for event in result.events:
                workspace.apply_event(event)

            panel = workspace.snapshot()["panels"]["memory_review"]
            self.assertTrue(panel["is_open"])
            self.assertEqual(panel["panel_type"], "memory_review")
            self.assertEqual(panel["payload"]["display_subject"], "Nugget")
            self.assertEqual(workspace.snapshot()["workspace_cards"][-1]["type"], "memory_review")

    def test_intent_classifier_routes_show_everything_before_app_show(self) -> None:
        classifier = IntentClassifier()
        intent = classifier.classify("Show everything you remember about Kenleigh.")
        self.assertEqual(intent.intent, "memory_search")

    def test_renderer_contains_memory_review_card_surface(self) -> None:
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        styles = Path("app_shell/renderer/styles.css").read_text(encoding="utf-8")
        self.assertIn("renderMemoryReviewCard", renderer)
        self.assertIn("memory-review-list", renderer)
        self.assertIn("memory-review-card", styles)


if __name__ == "__main__":
    unittest.main()
