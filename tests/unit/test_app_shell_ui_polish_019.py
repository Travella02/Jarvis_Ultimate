import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class TestAppShellUIPolish019(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.index_html = (self.root / "app_shell" / "renderer" / "index.html").read_text(encoding="utf-8")
        self.styles_css = (self.root / "app_shell" / "renderer" / "styles.css").read_text(encoding="utf-8")
        self.renderer_js = (self.root / "app_shell" / "renderer" / "renderer.js").read_text(encoding="utf-8")

    def test_app_shell_version_and_capabilities_include_main_interface_polish(self):
        self.assertEqual(APP_SHELL_VERSION, "0.2.1")
        capabilities = app_shell_capabilities()
        self.assertIn("cinematic_main_interface_layout", capabilities)
        self.assertIn("collapsible_diagnostics_drawer", capabilities)
        self.assertIn("conversation_dock_chat_bubbles", capabilities)
        self.assertIn("state_specific_orb_motion", capabilities)
        self.assertIn("startup_readiness_status_strip", capabilities)

    def test_renderer_uses_jarvis_first_layout_sections(self):
        self.assertIn("interface-grid", self.index_html)
        self.assertIn("left-rail", self.index_html)
        self.assertIn("conversation-dock", self.index_html)
        self.assertIn("diagnostics-drawer", self.index_html)
        self.assertNotIn("bottom-grid", self.index_html)

    def test_styles_include_cinematic_orb_and_chat_polish(self):
        self.assertIn("radar-sweep", self.styles_css)
        self.assertIn("voice-wave", self.styles_css)
        self.assertIn("body.state-speaking .voice-wave", self.styles_css)
        self.assertIn(".chat-message.user", self.styles_css)
        self.assertIn("diagnostics-collapsed", self.styles_css)

    def test_renderer_keeps_diagnostics_collapsed_and_auto_scroll_chat(self):
        self.assertIn("toggleDiagnostics", self.renderer_js)
        self.assertIn("diagnostics-collapsed", self.renderer_js)
        self.assertIn("chatRoleClass", self.renderer_js)
        self.assertIn("els.chatLog.scrollTop = els.chatLog.scrollHeight", self.renderer_js)
        self.assertIn("Initializing Jarvis", self.renderer_js)


if __name__ == "__main__":
    unittest.main()
