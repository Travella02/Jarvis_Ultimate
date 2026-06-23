from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.agents.conversation_agent.agent import Agent
from jarvis.brain.intent_classifier import IntentResult
from jarvis.memory.short_term import ShortTermMemory
from jarvis.providers.llm.mock_provider import MockLLMProvider


class CapturingLLMProvider(MockLLMProvider):
    def __init__(self):
        super().__init__(canned_response="I remember the recent context.")
        self.last_messages = []

    def chat(self, messages, **kwargs):
        self.last_messages = list(messages)
        return super().chat(messages, **kwargs)


class TestConversationShortTermMemory(unittest.TestCase):
    def test_conversation_agent_injects_recent_memory_before_current_user_message(self):
        memory = ShortTermMemory(max_turns=5, inject_last_turns=1)
        memory.add_turn(user="My dog is named Max.", assistant="Max sounds great.")
        provider = CapturingLLMProvider()
        agent = Agent()

        result = agent.handle(
            "What is my dog's name?",
            context={
                "intent": IntentResult("general_chat", 0.5, "test"),
                "llm_provider": provider,
                "short_term_memory": memory,
            },
        )

        self.assertTrue(result.success)
        self.assertEqual(result.data["short_term_memory_turns_used"], 1)
        self.assertEqual([message["role"] for message in provider.last_messages], ["user", "assistant", "user"])
        self.assertEqual(provider.last_messages[0]["content"], "My dog is named Max.")
        self.assertEqual(provider.last_messages[-1]["content"], "What is my dog's name?")


if __name__ == "__main__":
    unittest.main()
