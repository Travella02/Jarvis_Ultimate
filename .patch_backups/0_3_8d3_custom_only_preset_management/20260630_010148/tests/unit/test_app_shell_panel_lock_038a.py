import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class AppShellPanelLock038aTests(unittest.TestCase):
    def test_version_and_capability_include_per_panel_lock(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d")
        capabilities = set(app_shell_capabilities())
        self.assertIn("panel_lock_mode", capabilities)
        self.assertIn("per_panel_layout_lock_buttons", capabilities)

    def test_renderer_persists_and_toggles_individual_panel_locks(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("PANEL_LOCK_STORAGE_KEY", renderer)
        self.assertIn("loadPanelLocks", renderer)
        self.assertIn("savePanelLocks", renderer)
        self.assertIn("togglePanelLock", renderer)
        self.assertIn("data-layout-action=\"lock\"", renderer)
        self.assertIn("isPanelLocked(key)", renderer)
        self.assertIn("panel-layout-locked", renderer)

    def test_styles_show_locked_state_and_disable_resize_handle(self):
        css = Path("app_shell/renderer/styles.css").read_text(encoding="utf-8")
        self.assertIn(".panel-lock-button.is-active", css)
        self.assertIn(".dockable-panel.panel-layout-locked", css)
        self.assertIn("pointer-events: none", css)


if __name__ == "__main__":
    unittest.main()
