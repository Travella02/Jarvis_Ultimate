import tempfile
import unittest
from pathlib import Path

from jarvis.agents.memory_agent.agent import Agent
from jarvis.memory.always_on import MemoryCandidateStore, ShortTermFactStore
from jarvis.memory.long_term import LongTermMemoryStore


class TestMemoryDuplicateFilter030b(unittest.TestCase):
    def test_long_term_recall_dedupes_first_and_second_person_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LongTermMemoryStore(path=Path(tmp) / "long_term.json")
            store.add("I prefer short direct patch instructions", category="preference")
            store.add("you prefer short direct patch instructions", category="preference")

            message = store.format_records(query="patch instructions")

            self.assertEqual(message.count("you prefer short direct patch instructions"), 1)
            self.assertEqual(message, "I remember that you prefer short direct patch instructions, sir.")

    def test_candidate_review_dedupes_equivalent_pending_memories(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MemoryCandidateStore(path=Path(tmp) / "candidates.json")
            store.add("I prefer short direct patch instructions", suggested_tier="long_term", confidence=0.82)
            store.add("From now on, I prefer short direct patch instructions", suggested_tier="long_term", confidence=0.82)

            message = store.format_pending()

            self.assertIn("I found one possible memory waiting for review", message)
            self.assertEqual(message.count("you prefer short direct patch instructions"), 1)

    def test_approving_duplicate_candidates_saves_one_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate_store = MemoryCandidateStore(path=Path(tmp) / "candidates.json")
            long_term = LongTermMemoryStore(path=Path(tmp) / "long_term.json")
            short_term = ShortTermFactStore(path=Path(tmp) / "short_term.json")
            candidate_store.add("I prefer short direct patch instructions", suggested_tier="long_term")
            candidate_store.add("From now on, I prefer short direct patch instructions", suggested_tier="long_term")

            result = Agent().handle(
                "save that permanently",
                {
                    "memory_candidates": candidate_store,
                    "long_term_memory": long_term,
                    "short_term_fact_memory": short_term,
                },
            )

            self.assertTrue(result.success)
            self.assertEqual(result.message, "I saved that permanently, sir.")
            self.assertEqual(len(long_term.records), 1)
            self.assertEqual(
                long_term.format_records(query="patch instructions"),
                "I remember that you prefer short direct patch instructions, sir.",
            )


if __name__ == "__main__":
    unittest.main()
