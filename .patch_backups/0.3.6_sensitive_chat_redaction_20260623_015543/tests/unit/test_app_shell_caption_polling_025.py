import unittest
from pathlib import Path


class TestAppShellCaptionPolling025(unittest.TestCase):
    def test_renderer_uses_fast_adaptive_refresh_for_voice_captions(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("preferredRefreshDelay", renderer)
        self.assertIn("return voiceActive ? 180 : 700", renderer)
        self.assertIn("refreshInFlight", renderer)
        self.assertNotIn("setInterval(refreshState, 900)", renderer)

    def test_caption_typewriter_catches_up_to_short_tool_responses(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("remaining > 90 ? 7", renderer)
        self.assertIn("window.setTimeout(stepOrbCaption, 16)", renderer)


if __name__ == "__main__":
    unittest.main()
