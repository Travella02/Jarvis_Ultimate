from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest
from jarvis.core.events import EventBus


class TestEventBus(unittest.TestCase):
    def test_emit_and_history(self):
        bus = EventBus()
        event = bus.emit("jarvis.test", source="unit", message="hello")
        self.assertEqual(event.event_type, "jarvis.test")
        self.assertEqual(len(bus.history()), 1)

    def test_subscribe(self):
        bus = EventBus()
        seen = []
        bus.subscribe("jarvis.test", lambda event: seen.append(event.event_type))
        bus.emit("jarvis.test")
        self.assertEqual(seen, ["jarvis.test"])


if __name__ == "__main__":
    unittest.main()
