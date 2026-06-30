import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class AppShellCustomLayoutNameDialog038d2Tests(unittest.TestCase):
    def test_runtime_version_stays_038d_and_capability_notes_dialog_hotfix(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d3")
        capabilities = set(app_shell_capabilities())
        self.assertIn("custom_workspace_layout_presets", capabilities)
        self.assertIn("custom_layout_preset_name_dialog", capabilities)
        self.assertIn("electron_safe_custom_preset_naming", capabilities)

    def test_index_contains_in_shell_name_dialog(self):
        html = Path("app_shell/renderer/index.html").read_text(encoding="utf-8")
        self.assertIn("layoutPresetDialog", html)
        self.assertIn("layoutPresetForm", html)
        self.assertIn("layoutPresetNameInput", html)
        self.assertIn("layoutPresetCancelButton", html)
        self.assertIn("layoutPresetConfirmButton", html)
        self.assertIn("Name this layout", html)
        self.assertIn("role=\"dialog\"", html)

    def test_renderer_uses_dialog_instead_of_relying_on_native_prompt(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("requestCustomPresetName", renderer)
        self.assertIn("layoutPresetDialog", renderer)
        self.assertIn("layoutPresetNameInput", renderer)
        self.assertIn("await requestCustomPresetName", renderer)
        self.assertIn("layoutPresetDialogResolve", renderer)
        self.assertIn("document.body.classList.add('layout-preset-dialog-open')", renderer)

    def test_styles_include_custom_name_dialog(self):
        css = Path("app_shell/renderer/styles.css").read_text(encoding="utf-8")
        self.assertIn("in-shell custom layout preset naming dialog", css)
        self.assertIn(".layout-preset-dialog-backdrop", css)
        self.assertIn(".layout-preset-dialog-backdrop[hidden]", css)
        self.assertIn(".layout-preset-name-input", css)
        self.assertIn(".layout-preset-dialog-actions", css)


if __name__ == "__main__":
    unittest.main()
