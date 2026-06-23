from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from jarvis.memory.long_term import LongTermMemoryStore


class LongTermMemory028Tests(unittest.TestCase):
    def test_store_search_and_persist_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.json"
            memory = LongTermMemoryStore(path=path, max_records=20, inject_limit=3)
            record = memory.add("Tanner prefers Jarvis patch steps directly in chat.", category="preference", tags=["jarvis"])
            self.assertIsNotNone(record)
            self.assertTrue(path.exists())

            matches = memory.search("patch steps", limit=5)
            self.assertEqual(len(matches), 1)
            self.assertIn("patch steps", matches[0].record.text)

            loaded = LongTermMemoryStore(path=path, max_records=20, inject_limit=3)
            self.assertEqual(len(loaded.records), 1)
            self.assertIn("patch steps", loaded.relevant_context("How should you deliver patches?"))

    def test_forget_removes_matching_memory_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = LongTermMemoryStore(path=Path(tmp) / "memory.json")
            memory.add("Tanner likes Spotify for music.", category="preference", tags=["music"])
            memory.add("Tanner likes VS Code for coding.", category="preference", tags=["coding"])

            removed = memory.forget("Spotify")
            self.assertEqual(len(removed), 1)
            self.assertEqual(len(memory.records), 1)
            self.assertIn("VS Code", memory.records[0].text)


if __name__ == "__main__":
    unittest.main()
