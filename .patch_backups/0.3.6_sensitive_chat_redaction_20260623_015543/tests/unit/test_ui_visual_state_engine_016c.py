from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import unittest

from jarvis.ui.visual_state import (
    available_visual_states,
    classify_voice_status,
    normalize_visual_state,
    orb_profile_for_state,
    profile_summary,
    state_label,
)


class TestUIVisualStateEngine016c(unittest.TestCase):
    def test_known_states_have_animation_profiles(self):
        states = available_visual_states()
        self.assertIn("sleeping", states)
        self.assertIn("thinking", states)
        self.assertIn("speaking", states)
        for state in states:
            profile = orb_profile_for_state(state)
            self.assertEqual(profile.state, state)
            self.assertGreater(profile.ring_speed, 0)
            self.assertGreaterEqual(profile.glow_strength, 0)

    def test_state_aliases_normalize_for_runtime_values(self):
        self.assertEqual(normalize_visual_state("wake-listening"), "wake_listening")
        self.assertEqual(normalize_visual_state("ready"), "idle")
        self.assertEqual(normalize_visual_state("totally unknown"), "idle")

    def test_voice_status_messages_classify_to_visual_states(self):
        self.assertEqual(classify_voice_status("Listening turn 2/∞ (sleeping)..."), "wake_listening")
        self.assertEqual(classify_voice_status("Wake detected: hey jarvis. Jarvis is awake."), "listening")
        self.assertEqual(classify_voice_status("STT failed: No speech detected."), "error")
        self.assertEqual(classify_voice_status("Warming voice systems..."), "working")

    def test_state_label_and_summary_are_serializable(self):
        self.assertEqual(state_label("thinking"), "Thinking")
        summary = profile_summary(orb_profile_for_state("speaking"))
        self.assertEqual(summary["state"], "speaking")
        self.assertIn("ring_speed", summary)


if __name__ == "__main__":
    unittest.main()
