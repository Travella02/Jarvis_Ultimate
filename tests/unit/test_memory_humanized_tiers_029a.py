from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jarvis.agents.memory_agent.agent import Agent
from jarvis.memory.always_on import ChatArchiveStore, ShortTermFactStore
from jarvis.memory.long_term import LongTermMemoryStore


class MemoryHumanizedTiers029aTests(unittest.TestCase):
    def test_multiple_permanent_memory_search_is_humanized(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = LongTermMemoryStore(path=Path(tmp) / "long_term.json")
            memory.add("my favorite test color is blue", category="preference")
            memory.add("my favorite test color shade is navy", category="preference")
            agent = Agent()
            result = agent.handle(
                "What do you remember about my favorite test color?",
                context={"long_term_memory": memory},
            )
            self.assertTrue(result.success)
            self.assertIn("I remember that", result.message)
            self.assertIn("your favorite test color is blue", result.message)
            self.assertNotIn("Permanent memories:", result.message)
            self.assertNotIn("- ", result.message)

    def test_chat_archive_search_is_humanized(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = ChatArchiveStore(root_dir=Path(tmp) / "chat_archive")
            archive.append_turn(user="What did we say about memory?", assistant="We added an always-on chat archive.")
            archive.append_turn(user="Memory status", assistant="Memory is online.")
            message = archive.format_search("memory")
            self.assertIn("I remember", message)
            self.assertNotIn("related chat archive turn", message)
            self.assertNotIn("- You:", message)

    def test_memory_status_hides_raw_paths_and_unlimited_long_term_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            long_term = LongTermMemoryStore(path=Path(tmp) / "long_term.json", max_records=0)
            short_term = ShortTermFactStore(path=Path(tmp) / "short_term.json")
            archive = ChatArchiveStore(root_dir=Path(tmp) / "chat_archive")
            long_status = long_term.format_status()
            short_status = short_term.format_status()
            archive_status = archive.format_status()
            self.assertIn("no fixed long-term memory cap", long_status.lower())
            self.assertNotIn(str(Path(tmp)), long_status)
            self.assertNotIn(str(Path(tmp)), short_status)
            self.assertNotIn(str(Path(tmp)), archive_status)


if __name__ == "__main__":
    unittest.main()
