from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest

from jarvis.agents.conversation_agent.agent import Agent
from jarvis.brain.intent_classifier import IntentResult
from jarvis.providers.llm.mock_provider import MockLLMProvider


class TestConversationAgentLLM(unittest.TestCase):
    def test_general_chat_uses_llm_provider(self):
        agent = Agent()
        result = agent.handle(
            "hello jarvis",
            context={
                "intent": IntentResult("general_chat", 0.5, "test"),
                "llm_provider": MockLLMProvider(canned_response="Online through mock LLM."),
            },
        )
        self.assertTrue(result.success)
        self.assertEqual(result.action, "llm_chat")
        self.assertIn("Online through mock LLM", result.message)
        self.assertTrue(result.data["llm_enabled"])


if __name__ == "__main__":
    unittest.main()
