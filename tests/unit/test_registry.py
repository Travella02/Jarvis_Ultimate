from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest
from jarvis.core.registry import AgentRegistry


class TestAgentRegistry(unittest.TestCase):
    def test_load_builtin_agents(self):
        registry = AgentRegistry()
        registry.load_builtin_agents()
        names = registry.names()
        self.assertIn("conversation_agent", names)
        self.assertIn("screen_agent", names)
        self.assertIn("avatar_agent", names)

    def test_get_agent(self):
        registry = AgentRegistry()
        registry.load_builtin_agents()
        agent = registry.get_agent("conversation_agent")
        self.assertIsNotNone(agent)
        self.assertTrue(hasattr(agent, "handle"))


if __name__ == "__main__":
    unittest.main()
