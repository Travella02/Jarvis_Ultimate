import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class AppShellCustomLayoutPresetManagement038d3Tests(unittest.TestCase):
    def test_version_and_capabilities_include_custom_only_preset_management(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d3")
        capabilities = set(app_shell_capabilities())
        self.assertIn("custom_only_layout_presets", capabilities)
        self.assertIn("unlimited_user_layout_presets", capabilities)
        self.assertIn("user_renamable_layout_presets", capabilities)
        self.assertIn("user_deletable_layout_presets", capabilities)
        self.assertIn("electron_safe_preset_delete_confirmation", capabilities)

    def test_builtin_layout_presets_are_removed_from_markup(self):
        html = Path("app_shell/renderer/index.html").read_text(encoding="utf-8")
        self.assertNotIn('value="gaming"', html)
        self.assertNotIn('value="coding"', html)
        self.assertNotIn('value="music"', html)
        self.assertNotIn('value="minimal"', html)
        self.assertIn("layoutSavePresetButton", html)
        self.assertIn("layoutRenamePresetButton", html)
        self.assertIn("layoutDeletePresetButton", html)

    def test_renderer_manages_custom_presets_without_builtin_builder(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("renameSelectedLayoutPreset", renderer)
        self.assertIn("deleteSelectedLayoutPreset", renderer)
        self.assertIn("requestLayoutConfirmation", renderer)
        self.assertIn("selectedCustomLayoutPresetId", renderer)
        self.assertIn("syncPresetManagementControls", renderer)
        self.assertNotIn("function buildPresetLayout", renderer)
        self.assertNotIn("new Set(['gaming', 'coding', 'music', 'minimal'])", renderer)

    def test_styles_include_custom_preset_management_controls(self):
        css = Path("app_shell/renderer/styles.css").read_text(encoding="utf-8")
        self.assertIn(".layout-preset-manage-button", css)
        self.assertIn(".layout-preset-confirm-backdrop", css)


if __name__ == "__main__":
    unittest.main()
