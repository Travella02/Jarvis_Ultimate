from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.memory.short_term import ShortTermMemory


class TestShortTermMemory(unittest.TestCase):
    def test_add_turn_and_convert_to_llm_messages(self):
        memory = ShortTermMemory(max_turns=5, inject_last_turns=3)
        stored = memory.add_turn(user="My name is Tanner.", assistant="Got it.")

        self.assertIsNotNone(stored)
        self.assertEqual(len(memory.turns), 1)
        self.assertEqual(
            memory.to_llm_messages(),
            [
                {"role": "user", "content": "My name is Tanner."},
                {"role": "assistant", "content": "Got it."},
            ],
        )

    def test_trim_by_max_turns(self):
        memory = ShortTermMemory(max_turns=2, inject_last_turns=5)
        memory.add_turn(user="one", assistant="reply one")
        memory.add_turn(user="two", assistant="reply two")
        memory.add_turn(user="three", assistant="reply three")

        self.assertEqual(len(memory.turns), 2)
        self.assertEqual(memory.turns[0].user, "two")
        self.assertEqual(memory.turns[1].user, "three")

    def test_clear_returns_removed_count(self):
        memory = ShortTermMemory(max_turns=5)
        memory.add_turn(user="hello", assistant="hi")
        self.assertEqual(memory.clear(), 1)
        self.assertEqual(len(memory.turns), 0)
        self.assertEqual(memory.format_last(), "Short-term memory is empty.")

    def test_disabled_memory_does_not_store(self):
        memory = ShortTermMemory(enabled=False)
        self.assertIsNone(memory.add_turn(user="hello", assistant="hi"))
        self.assertEqual(memory.to_llm_messages(), [])

    def test_autosave_loads_session_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "short_term_session.json"
            memory = ShortTermMemory(max_turns=5, persist_path=path, autosave=True, session_id="test-session")
            memory.add_turn(user="remember this session", assistant="I will keep it for this session.")

            loaded = ShortTermMemory(max_turns=5, persist_path=path, autosave=True)
            self.assertEqual(loaded.session_id, "test-session")
            self.assertEqual(len(loaded.turns), 1)
            self.assertEqual(loaded.turns[0].user, "remember this session")


if __name__ == "__main__":
    unittest.main()
