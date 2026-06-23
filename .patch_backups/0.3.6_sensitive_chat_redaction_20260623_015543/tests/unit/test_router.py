from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest
from jarvis.brain.router import JarvisRouter
from jarvis.core.events import EventBus
from jarvis.core.registry import AgentRegistry


class TestRouter(unittest.TestCase):
    def make_router(self):
        registry = AgentRegistry()
        registry.load_builtin_agents()
        return JarvisRouter(registry=registry, events=EventBus())

    def test_status_routes_to_conversation_agent(self):
        router = self.make_router()
        result = router.handle("status")
        self.assertTrue(result.success)
        self.assertEqual(result.data["selected_agent"], "conversation_agent")
        self.assertIn("online", result.message.lower())

    def test_screen_routes_to_screen_agent(self):
        router = self.make_router()
        result = router.handle("screen check")
        self.assertTrue(result.success)
        self.assertEqual(result.data["selected_agent"], "screen_agent")
        self.assertIn("registered", result.message.lower())


if __name__ == "__main__":
    unittest.main()
