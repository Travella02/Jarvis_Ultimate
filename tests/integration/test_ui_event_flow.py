from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest
from jarvis.core.events import EventBus
from jarvis.ui.avatar_state import AvatarState


class TestUIEventFlow(unittest.TestCase):
    def test_avatar_can_react_to_event(self):
        bus = EventBus()
        avatar = AvatarState()

        def on_thinking(event):
            avatar.set_state("thinking", message=event.message)

        bus.subscribe("brain.routing_started", on_thinking)
        bus.emit("brain.routing_started", source="test", message="Routing")
        self.assertEqual(avatar.state, "thinking")


if __name__ == "__main__":
    unittest.main()
