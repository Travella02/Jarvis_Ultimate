from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest

from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider


class TestLMStudioConversationFlow(unittest.TestCase):
    def test_runtime_can_route_general_chat_to_llm_provider(self):
        runtime = JarvisRuntime(llm_provider=MockLLMProvider(canned_response="Mock LLM conversation works."))
        runtime.boot()
        result = runtime.handle_command("Can we talk normally now?")
        self.assertTrue(result.success)
        self.assertEqual(result.data["selected_agent"], "conversation_agent")
        self.assertEqual(result.action, "llm_chat")
        self.assertIn("Mock LLM conversation works", result.message)


if __name__ == "__main__":
    unittest.main()
