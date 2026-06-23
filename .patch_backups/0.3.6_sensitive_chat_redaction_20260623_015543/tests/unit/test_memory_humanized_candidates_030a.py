"""Tests for 0.3.0a memory candidate response humanization."""

import tempfile
import unittest
from pathlib import Path

from jarvis.agents.memory_agent.agent import Agent as MemoryAgent
from jarvis.memory.always_on import MemoryAutoCaptureEngine, MemoryCandidateStore, ShortTermFactStore
from jarvis.memory.long_term import LongTermMemoryStore


class MemoryHumanizedCandidates030aTests(unittest.TestCase):
    def test_candidate_review_uses_user_context_not_raw_first_person(self) -> None:
        store = MemoryCandidateStore()
        store.add(
            "From now on, I prefer short direct patch instructions",
            suggested_tier="long_term",
            confidence=0.82,
        )

        message = store.format_pending()

        self.assertIn("you prefer short direct patch instructions", message)
        self.assertNotIn("I prefer", message)
        self.assertNotIn("From now on", message)
        self.assertNotIn("confidence", message.lower())

    def test_auto_capture_strips_command_framing_from_candidate_text(self) -> None:
        decision = MemoryAutoCaptureEngine().classify_turn(
            "From now on, I prefer short direct patch instructions."
        )

        self.assertEqual(decision["decision"], "long_term")
        self.assertEqual(decision["text"], "I prefer short direct patch instructions")

    def test_approved_candidate_reads_back_as_you_prefer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            candidates = MemoryCandidateStore(path=Path(temp_dir) / "candidates.json")
            long_term = LongTermMemoryStore(path=Path(temp_dir) / "long_term.json")
            short_term = ShortTermFactStore(path=Path(temp_dir) / "short.json")
            candidates.add(
                "From now on, I prefer short direct patch instructions",
                suggested_tier="long_term",
                category="preference",
            )
            agent = MemoryAgent()
            context = {
                "memory_candidates": candidates,
                "long_term_memory": long_term,
                "short_term_fact_memory": short_term,
            }

            approved = agent.handle("Jarvis, save that permanently", context=context)
            self.assertTrue(approved.success)
            recalled = agent.handle("Jarvis, what do you remember about patch instructions?", context=context)

            self.assertIn("you prefer short direct patch instructions", recalled.message)
            self.assertNotIn("I prefer", recalled.message)
            self.assertNotIn("From now on", recalled.message)


if __name__ == "__main__":
    unittest.main()
