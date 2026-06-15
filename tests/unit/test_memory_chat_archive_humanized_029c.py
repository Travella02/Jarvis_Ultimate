"""Regression tests for 0.2.9c chat archive wording."""

import unittest

from jarvis.memory.always_on import ChatArchiveStore, ChatArchiveRecord, MemoryMatch


class MemoryChatArchiveHumanized029cTests(unittest.TestCase):
    def test_chat_archive_summary_starts_like_memory_not_database(self):
        archive = ChatArchiveStore.__new__(ChatArchiveStore)
        record = ChatArchiveRecord(
            timestamp="2026-06-15T00:00:00+00:00",
            user="memory status",
            assistant="Memory is online.",
            agent_name="test",
        )
        message = archive._summarize_recent_results(
            "memory",
            [MemoryMatch(record=record, score=1.0, reason="test", tier="chat_archive")],
        )
        self.assertIn("I remember", message)
        self.assertIn("recently talked about memory", message)
        self.assertLessEqual(len(message), 140)


if __name__ == "__main__":
    unittest.main()
