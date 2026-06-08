from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest
from jarvis.core.lifecycle import JarvisRuntime


class TestAgentRoutingFlow(unittest.TestCase):
    def test_list_agents(self):
        runtime = JarvisRuntime()
        runtime.boot()
        result = runtime.handle_command("list agents")
        self.assertTrue(result.success)
        self.assertIn("conversation_agent", result.data["agents"])
        self.assertIn("avatar_agent", result.data["agents"])

    def test_app_route_placeholder(self):
        runtime = JarvisRuntime()
        runtime.boot()
        result = runtime.handle_command("open chrome")
        self.assertTrue(result.success)
        self.assertEqual(result.data["selected_agent"], "app_agent")


if __name__ == "__main__":
    unittest.main()
