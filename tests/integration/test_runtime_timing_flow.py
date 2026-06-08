from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest

from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider


class TestRuntimeTimingFlow(unittest.TestCase):
    def test_runtime_exposes_last_timing_after_command(self):
        runtime = JarvisRuntime(llm_provider=MockLLMProvider(canned_response="timed mock response"))
        runtime.boot()
        result = runtime.handle_command("Can we time this?")

        self.assertTrue(result.success)
        self.assertIsNotNone(runtime.last_timing)
        self.assertIn("timing", result.data)
        self.assertTrue(runtime.last_timing.has_mark("brain.classify_start"))
        self.assertTrue(runtime.last_timing.has_mark("agent.handle_finished"))
        self.assertIn("Last command total", runtime.timing_last())


if __name__ == "__main__":
    unittest.main()
