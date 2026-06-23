from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.memory.always_on import ChatArchiveStore, MemoryMaintenance, ShortTermFactStore
from jarvis.core.lifecycle import JarvisRuntime


class TestAlwaysOnMemory029(unittest.TestCase):
    def test_version_and_capabilities_include_always_on_memory(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.7")
        capabilities = set(app_shell_capabilities())
        self.assertIn("always_on_memory_tiers", capabilities)
        self.assertIn("daily_chat_archive_memory", capabilities)
        self.assertIn("crash_safe_memory_writes", capabilities)

    def test_short_term_fact_store_expires_and_searches(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ShortTermFactStore(path=Path(tmp) / "short_term.json", default_days=3)
            record = store.add("my test lunch is soup", tags=["food"], days=2)
            self.assertIsNotNone(record)
            matches = store.search("test lunch")
            self.assertEqual(len(matches), 1)
            self.assertIn("soup", matches[0].record.text)
            self.assertIn("temporarily remember", store.format_records(query="test lunch").lower())

            reloaded = ShortTermFactStore(path=Path(tmp) / "short_term.json", default_days=3)
            self.assertEqual(len(reloaded.records), 1)

    def test_chat_archive_writes_daily_jsonl_and_searches(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = ChatArchiveStore(root_dir=Path(tmp) / "chat_archive")
            record = archive.append_turn(user="What did we say about memory?", assistant="We added a chat archive.", session_id="test-session")
            self.assertIsNotNone(record)
            files = list((Path(tmp) / "chat_archive").glob("*.jsonl"))
            self.assertEqual(len(files), 1)
            self.assertIn("chat archive", files[0].read_text(encoding="utf-8"))
            matches = archive.search("chat archive")
            self.assertEqual(len(matches), 1)
            self.assertIn("chat archive", archive.format_search("chat archive").lower())

    def test_memory_maintenance_expires_and_writes_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            facts = ShortTermFactStore(path=Path(tmp) / "short_term.json", default_days=1)
            facts.add("temporary fact", days=1)
            # Force expiration for the record.
            facts._records[0].expires_at = "2000-01-01T00:00:00+00:00"
            archive = ChatArchiveStore(root_dir=Path(tmp) / "chat_archive")
            maintenance = MemoryMaintenance(short_term_facts=facts, chat_archive=archive, status_path=Path(tmp) / "maintenance.json", interval_seconds=30)
            status = maintenance.run()
            self.assertEqual(status["last_expired_short_term"], 1)
            self.assertTrue((Path(tmp) / "maintenance.json").exists())
            self.assertEqual(len(facts.records), 0)

    def test_runtime_archives_each_command_incrementally(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            # Minimal expected project folders.
            runtime = JarvisRuntime(project_root=root)
            runtime.boot()
            result = runtime.handle_command("memory status")
            self.assertTrue(result.success)
            status = runtime.chat_archive.status()
            self.assertGreaterEqual(status["daily_files"], 1)
            self.assertGreaterEqual(status["recent_turns_indexed"], 1)


if __name__ == "__main__":
    unittest.main()
