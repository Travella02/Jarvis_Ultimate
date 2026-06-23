from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from jarvis.agents.memory_agent.agent import Agent
from jarvis.memory.long_term import LongTermMemoryStore


class MemoryAgentHumanResponses028aTests(unittest.TestCase):
    def test_memory_search_response_is_human_not_database_dump(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = LongTermMemoryStore(path=Path(tmp) / "long_term.json")
            agent = Agent()

            stored = agent.handle(
                "Jarvis, remember that my favorite test color is blue",
                context={"long_term_memory": memory},
            )
            self.assertTrue(stored.success)

            found = agent.handle(
                "What do you remember about my favorite test color?",
                context={"long_term_memory": memory},
            )

            self.assertTrue(found.success)
            self.assertEqual(found.action, "memory_search")
            self.assertIn("I remember that your favorite test color is blue, sir.", found.message)
            self.assertNotIn("Saved memories matching", found.message)
            self.assertNotIn("- my favorite test color is blue", found.message)

    def test_memory_status_keeps_required_prefix_but_reads_naturally(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = LongTermMemoryStore(path=Path(tmp) / "long_term.json")
            memory.add("my main music app is Spotify", category="preference", tags=["music"])
            status = memory.format_status()
            self.assertIn("Long-term memory status", status)
            self.assertIn("Long-term memory is online, sir", status)
            self.assertIn("1 permanent memory", status)


if __name__ == "__main__":
    unittest.main()
