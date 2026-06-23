from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest

from jarvis.core.timing import TurnTimer, format_timing_summary


class TestTurnTiming(unittest.TestCase):
    def test_records_named_marks(self):
        timer = TurnTimer(command="hello")
        timer.mark("custom.step", value="ok")
        data = timer.to_dict()
        self.assertEqual(data["command_preview"], "hello")
        self.assertTrue(timer.has_mark("turn.start"))
        self.assertTrue(timer.has_mark("custom.step"))
        self.assertEqual(data["marks"][-1]["data"]["value"], "ok")

    def test_summary_separates_lm_studio_request_time(self):
        timer = TurnTimer(command="hello")
        timer.mark("lm_studio.request_start", path="/chat/completions")
        timer.mark("lm_studio.request_finished", path="/chat/completions")
        summary = format_timing_summary(timer)
        self.assertIn("Pre-LM Studio request time", summary)
        self.assertIn("LM Studio request/response time", summary)


if __name__ == "__main__":
    unittest.main()
