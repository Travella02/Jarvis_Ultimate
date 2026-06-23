from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from jarvis.agents.memory_agent.agent import Agent
from jarvis.memory.long_term import LongTermMemoryStore


class MemoryAgent028Tests(unittest.TestCase):
    def test_memory_agent_stores_searches_and_forgets(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = LongTermMemoryStore(path=Path(tmp) / "long_term.json")
            agent = Agent()

            stored = agent.handle("Jarvis, remember that my main music app is Spotify", context={"long_term_memory": memory})
            self.assertTrue(stored.success)
            self.assertEqual(stored.action, "memory_store")
            self.assertEqual(len(memory.records), 1)

            found = agent.handle("What do you remember about music?", context={"long_term_memory": memory})
            self.assertTrue(found.success)
            self.assertEqual(found.action, "memory_search")
            self.assertIn("Spotify", found.message)

            status = agent.handle("memory status", context={"long_term_memory": memory})
            self.assertTrue(status.success)
            self.assertIn("Long-term memory status", status.message)

            removed = agent.handle("forget the memory about Spotify", context={"long_term_memory": memory})
            self.assertTrue(removed.success)
            self.assertEqual(removed.action, "memory_forget")
            self.assertEqual(len(memory.records), 0)

    def test_empty_clear_requires_confirmation(self):
        memory = LongTermMemoryStore(enabled=True, path=Path(tempfile.gettempdir()) / "jarvis_memory_agent_clear_test.json")
        agent = Agent()
        result = agent.handle("clear memory", context={"long_term_memory": memory})
        self.assertTrue(result.needs_confirmation)
        self.assertEqual(result.action, "memory_clear_confirm")


if __name__ == "__main__":
    unittest.main()
