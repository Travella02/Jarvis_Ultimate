import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class AppShellCustomLayoutPresets038dTests(unittest.TestCase):
    def test_version_and_capabilities_include_custom_layout_presets(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d")
        capabilities = set(app_shell_capabilities())
        self.assertIn("custom_workspace_layout_presets", capabilities)
        self.assertIn("user_saved_layout_preset_button", capabilities)
        self.assertIn("viewport_scaled_custom_layout_restore", capabilities)

    def test_renderer_persists_named_custom_layout_presets(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("CUSTOM_LAYOUT_PRESETS_STORAGE_KEY", renderer)
        self.assertIn("loadCustomLayoutPresets", renderer)
        self.assertIn("saveCurrentLayoutPreset", renderer)
        self.assertIn("captureCurrentLayoutPresetRecords", renderer)
        self.assertIn("syncCustomLayoutPresetOptions", renderer)
        self.assertIn("applyCustomLayoutPreset", renderer)
        self.assertIn("scaleLayoutRecordsForViewport", renderer)
        self.assertIn("CUSTOM_LAYOUT_PRESET_PREFIX", renderer)

    def test_renderer_markup_has_save_preset_button(self):
        html = Path("app_shell/renderer/index.html").read_text(encoding="utf-8")
        self.assertIn("layoutSavePresetButton", html)
        self.assertIn("Save Preset", html)
        self.assertIn("layoutPresetSelect", html)

    def test_styles_include_custom_preset_controls(self):
        css = Path("app_shell/renderer/styles.css").read_text(encoding="utf-8")
        self.assertIn(".layout-save-preset-button", css)
        self.assertIn(".layout-preset-select optgroup", css)


if __name__ == "__main__":
    unittest.main()
