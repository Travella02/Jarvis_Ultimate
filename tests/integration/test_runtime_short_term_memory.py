from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider


class TestRuntimeShortTermMemory(unittest.TestCase):
    def test_runtime_records_successful_llm_chat_turns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = JarvisRuntime(project_root=temp_dir, llm_provider=MockLLMProvider(canned_response="Blue is your color."))
            runtime.boot()

            result = runtime.handle_command("My favorite color is blue.")

            self.assertTrue(result.success)
            self.assertEqual(result.action, "llm_chat")
            self.assertEqual(len(runtime.short_term_memory.turns), 1)
            self.assertIn("favorite color", runtime.memory_last())
            self.assertIn("stored turns: 1", runtime.memory_status())
            self.assertIn("memory.short_term_turn_saved", runtime.timing_last())

    def test_runtime_clear_memory_command_helper(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = JarvisRuntime(project_root=temp_dir, llm_provider=MockLLMProvider(canned_response="Stored for this session."))
            runtime.boot()
            runtime.handle_command("This is a normal chat turn.")

            message = runtime.memory_clear()

            self.assertIn("Removed 1 turn", message)
            self.assertEqual(len(runtime.short_term_memory.turns), 0)


if __name__ == "__main__":
    unittest.main()
