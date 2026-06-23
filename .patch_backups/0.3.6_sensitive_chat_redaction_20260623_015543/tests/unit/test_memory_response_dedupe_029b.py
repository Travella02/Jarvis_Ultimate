"""Tests for 0.2.9b memory response polish."""

from pathlib import Path
import unittest

from jarvis.agents.memory_agent.agent import Agent
from jarvis.memory.always_on import ChatArchiveStore


class _Record:
    def __init__(self, text):
        self.text = text


class _Match:
    def __init__(self, text):
        self.record = _Record(text)


class MemoryResponseDedupe029bTests(unittest.TestCase):
    def test_memory_search_dedupes_partial_favorite_fact(self):
        agent = Agent()
        message = agent._format_combined_search(
            "my favorite test color",
            long_matches=[_Match("my favorite test color"), _Match("my favorite test color is blue")],
            short_matches=[],
        )
        self.assertEqual(message, "I remember that your favorite test color is blue, sir.")

    def test_chat_archive_format_search_stays_concise(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            archive = ChatArchiveStore(root_dir=temp_dir)
            archive.append_turn(
                user="What do you remember about temporary memory?",
                assistant="Temporary memories: - you are testing temporary memory - You: Remember that I am testing temporary memory for a few days. Jarvis: I’ll remember that for the next 3 days, sir. - You: list agents Jarvis: Available agents: App Agent; Avatar Agent; Conversation Agent; File Agent; Memory Agent; Weather Agent.",
            )
            archive.append_turn(
                user="memory status",
                assistant="Short-term fact memory status: enabled: True saved temporary memories: 1 / 300 default lifetime: 3 days injected temporary memories path: C:/fake/path/short_term_memory.json Long-term memory status: Memory is enabled, sir.",
            )

            message = archive.format_search("memory", limit=5)
            self.assertNotIn("You:", message)
            self.assertNotIn("Jarvis:", message)
            self.assertNotIn("C:/", message)
            self.assertLess(len(message), 320)

    def test_chat_scroll_uses_manual_lock(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("CHAT_SCROLL_LOCK_MS", renderer)
        self.assertIn("lockChatScroll", renderer)
        self.assertIn("!isChatScrollLocked() && isNearScrollBottom", renderer)


if __name__ == "__main__":
    unittest.main()
