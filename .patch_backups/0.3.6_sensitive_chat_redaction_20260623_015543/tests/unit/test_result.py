from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest
from jarvis.core.result import JarvisResult, JarvisEvent


class TestJarvisResult(unittest.TestCase):
    def test_ok_result(self):
        result = JarvisResult.ok("hello", agent_name="test_agent", action="test")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "hello")
        self.assertEqual(result.agent_name, "test_agent")
        self.assertEqual(result.action, "test")

    def test_fail_result(self):
        result = JarvisResult.fail("bad", errors=["bad thing"])
        self.assertFalse(result.success)
        self.assertEqual(result.errors, ["bad thing"])

    def test_event_serializes(self):
        event = JarvisEvent(event_type="test.event", source="unit")
        self.assertEqual(event.to_dict()["event_type"], "test.event")


if __name__ == "__main__":
    unittest.main()
