import unittest
from pathlib import Path


class TestAppShellCaptionPolling025a(unittest.TestCase):
    def test_renderer_uses_fast_adaptive_refresh_for_voice_captions(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("preferredRefreshDelay", renderer)
        self.assertIn("return voiceActive ? 75 : 700", renderer)
        self.assertIn("refreshInFlight", renderer)
        self.assertNotIn("setInterval(refreshState, 900)", renderer)

    def test_caption_typewriter_catches_up_to_short_tool_responses(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("remaining > 90 ? 10", renderer)
        self.assertIn("window.setTimeout(stepOrbCaption, 12)", renderer)


if __name__ == "__main__":
    unittest.main()


class TestLocalServerPreSpeechCaptionStaging025a(unittest.TestCase):
    def test_tool_response_caption_is_staged_before_tts(self):
        local_server = Path("src/jarvis/api/local_server.py").read_text(encoding="utf-8")
        self.assertIn("def _stage_live_speech_caption", local_server)
        self.assertIn("time.sleep(lead_seconds)", local_server)
        self.assertIn("self._stage_live_speech_caption(response_text)", local_server)
        self.assertLess(local_server.index("self._stage_live_speech_caption(response_text)"), local_server.index("self.runtime.tts_manager.say(response_text"))
