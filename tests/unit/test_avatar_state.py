from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest
from jarvis.ui.avatar_state import AvatarState


class TestAvatarState(unittest.TestCase):
    def test_valid_state_change(self):
        state = AvatarState()
        state.set_state("thinking", expression="focused", message="Routing command")
        self.assertEqual(state.state, "thinking")
        self.assertEqual(state.expression, "focused")

    def test_invalid_state_rejected(self):
        state = AvatarState()
        with self.assertRaises(ValueError):
            state.set_state("flying")


if __name__ == "__main__":
    unittest.main()
