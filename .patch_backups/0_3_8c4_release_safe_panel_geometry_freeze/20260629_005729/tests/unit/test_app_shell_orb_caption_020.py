from __future__ import annotations

import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.api.local_server import LocalJarvisAPI


class AppShellOrbCaption020Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.index_html = (self.root / "app_shell" / "renderer" / "index.html").read_text(encoding="utf-8")
        self.styles_css = (self.root / "app_shell" / "renderer" / "styles.css").read_text(encoding="utf-8")
        self.renderer_js = (self.root / "app_shell" / "renderer" / "renderer.js").read_text(encoding="utf-8")

    def test_version_and_capabilities_include_orb_caption_controls(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.8c3")
        capabilities = app_shell_capabilities()
        self.assertIn("continuous_js_orb_motion", capabilities)
        self.assertIn("orb_speech_caption_typewriter", capabilities)
        self.assertIn("true_orb_only_focus_mode", capabilities)
        self.assertIn("edge_only_holographic_panels", capabilities)

    def test_index_has_under_orb_speech_caption(self) -> None:
        self.assertIn('id="orbSpeechCaption"', self.index_html)
        self.assertIn('id="orbCaptionText"', self.index_html)
        self.assertNotIn('Jarvis Output', self.index_html)

    def test_renderer_uses_continuous_js_motion_and_typewriter(self) -> None:
        self.assertIn("requestAnimationFrame(animateOrbMotion)", self.renderer_js)
        self.assertIn("motionProfileForState", self.renderer_js)
        self.assertIn("--ring-a-rot", self.renderer_js)
        self.assertIn("resolveOrbCaptionText", self.renderer_js)
        self.assertIn("setOrbCaptionText", self.renderer_js)
        self.assertIn("live_response_text", self.renderer_js)
        self.assertIn("event.key === 'Escape'", self.renderer_js)

    def test_styles_keep_ring_geometry_stable_and_orb_only_minimal(self) -> None:
        self.assertIn("rotateX(70deg) rotateZ(var(--ring-a-rot))", self.styles_css)
        self.assertIn("rotateX(58deg) rotateZ(calc(56deg + var(--ring-b-rot)))", self.styles_css)
        self.assertIn("body.orb-focus .state-readout", self.styles_css)
        self.assertIn("display: none", self.styles_css)
        self.assertIn("orb-speech-caption", self.styles_css)
        self.assertIn("edge-only holographic panels", self.styles_css)

    def test_voice_session_snapshot_exposes_live_response_text(self) -> None:
        api = LocalJarvisAPI(project_root=self.root)
        session = api.voice_session_snapshot()
        self.assertIn("live_response_text", session)
        self.assertIn("live_response_started_at", session)


if __name__ == "__main__":
    unittest.main()
