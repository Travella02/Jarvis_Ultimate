import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class AppShellCustomLayoutVisibility038d4Tests(unittest.TestCase):
    def test_version_and_capabilities_include_preset_visibility_restore(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d4")
        capabilities = set(app_shell_capabilities())
        self.assertIn("custom_layout_panel_visibility_restore", capabilities)
        self.assertIn("custom_layout_open_closed_panel_state", capabilities)
        self.assertIn("preset_panel_visibility_sync", capabilities)

    def test_renderer_saves_panel_visibility_inside_custom_presets(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("capturePanelVisibilityPresetSnapshot", renderer)
        self.assertIn("visibility: capturePanelVisibilityPresetSnapshot()", renderer)
        self.assertIn("Save the current panel positions, sizes, open panels", renderer)

    def test_renderer_applies_saved_visibility_when_preset_is_selected(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("applyPanelVisibilityPresetSnapshot", renderer)
        self.assertIn("if (preset.visibility && typeof preset.visibility === 'object')", renderer)
        self.assertIn("panelVisibility = nextVisibility", renderer)
        self.assertIn("renderBodyClasses(activeVisualState)", renderer)
        self.assertIn("savePanelVisibility()", renderer)


if __name__ == "__main__":
    unittest.main()
