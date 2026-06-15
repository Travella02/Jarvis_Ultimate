from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from jarvis.memory.always_on import ChatArchiveStore


class FakeLLMProvider:
    def __init__(self) -> None:
        self.calls = []

    def chat(self, messages, *, system_prompt=None, timing=None, stream_callback=None):
        self.calls.append({"messages": messages, "system_prompt": system_prompt, "timing": timing})
        return SimpleNamespace(success=True, content="I remember we were testing the memory system, including temporary memory and chat history, sir.")


class TestMemoryChatArchiveLLMSummary029d(unittest.TestCase):
    def test_chat_archive_search_prefers_llm_summary_when_available(self) -> None:
        with TemporaryDirectory() as tmp:
            archive = ChatArchiveStore(root_dir=Path(tmp))
            archive.append_turn(user="What did we talk about memory?", assistant="I found 3 related chat archive turns, sir: raw transcript dump")
            archive.append_turn(user="memory status", assistant="Short-term fact memory status: - enabled: True - saved temporary memories: 1 / 300")
            llm = FakeLLMProvider()
            message = archive.format_search("memory", llm_provider=llm)

        self.assertEqual(message, "I remember we were testing the memory system, including temporary memory and chat history, sir.")
        self.assertEqual(len(llm.calls), 1)
        self.assertIn("Relevant recent chat evidence", llm.calls[0]["messages"][0]["content"])
        self.assertNotIn("raw transcript dump", message.lower())

    def test_chat_archive_search_fallback_is_short_and_human(self) -> None:
        with TemporaryDirectory() as tmp:
            archive = ChatArchiveStore(root_dir=Path(tmp))
            archive.append_turn(user="Remember that I am testing temporary memory for a few days", assistant="I’ll remember that for the next 3 days, sir.")
            archive.append_turn(user="memory status", assistant="Short-term fact memory status: - enabled: True - saved temporary memories: 1 / 300")
            message = archive.format_search("memory")

        self.assertIn("I remember", message)
        self.assertLess(len(message), 180)
        self.assertNotIn("Short-term fact memory status", message)
        self.assertNotIn("User:", message)


if __name__ == "__main__":
    unittest.main()
