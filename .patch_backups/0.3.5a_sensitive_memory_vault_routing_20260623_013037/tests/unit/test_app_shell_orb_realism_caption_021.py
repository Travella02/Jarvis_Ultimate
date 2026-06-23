from __future__ import annotations

import unittest
from pathlib import Path

from jarvis.api.local_server import _natural_sleep_reply_for_phrase
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class AppShellOrbRealismCaption021Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.index_html = (self.root / "app_shell" / "renderer" / "index.html").read_text(encoding="utf-8")
        self.styles_css = (self.root / "app_shell" / "renderer" / "styles.css").read_text(encoding="utf-8")
        self.renderer_js = (self.root / "app_shell" / "renderer" / "renderer.js").read_text(encoding="utf-8")

    def test_version_and_new_capabilities(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.5")
        capabilities = app_shell_capabilities()
        self.assertIn("realistic_3d_orb_core", capabilities)
        self.assertIn("soft_wake_sleep_brightness_ramp", capabilities)
        self.assertIn("caption_timing_lock", capabilities)
        self.assertIn("silent_natural_sleep_acknowledgement", capabilities)
        self.assertIn("stable_ring_particle_geometry", capabilities)

    def test_caption_is_centered_unboxed_and_label_removed(self) -> None:
        self.assertIn('id="orbSpeechCaption"', self.index_html)
        self.assertIn('id="orbCaptionText"', self.index_html)
        self.assertNotIn("Jarvis Output", self.index_html)
        self.assertIn("text-align: center", self.styles_css)
        self.assertIn("background: transparent !important", self.styles_css)
        self.assertIn("captionSignatureFor", self.renderer_js)
        self.assertIn("sameSpeechTurn", self.renderer_js)

    def test_orb_is_brighter_while_sleeping_and_core_is_realistic(self) -> None:
        self.assertIn("--orb-opacity: .72", self.styles_css)
        self.assertIn("ringA: 5.8", self.renderer_js)
        self.assertIn("realistic 3D orb", self.styles_css)
        self.assertIn(".orb-inner { display: none; }", self.styles_css)
        self.assertIn("sleepOrbBreathe 8.8s", self.styles_css)

    def test_state_color_blending_is_js_interpolated(self) -> None:
        self.assertIn("visualColors", self.renderer_js)
        self.assertIn("setColorTarget(next)", self.renderer_js)
        self.assertIn("applyColorVariables()", self.renderer_js)
        self.assertIn("colorCurrent[key] +=", self.renderer_js)

    def test_natural_sleep_acknowledgements_do_not_say_going_back_to_sleep(self) -> None:
        self.assertEqual(_natural_sleep_reply_for_phrase("thank you jarvis"), "Of course, sir.")
        self.assertEqual(_natural_sleep_reply_for_phrase("thanks Jarvis"), "Of course, sir.")
        self.assertEqual(_natural_sleep_reply_for_phrase("that's all Jarvis"), "Okay, sir.")
        self.assertNotIn("Going back to sleep", self.root.joinpath("src/jarvis/api/local_server.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
