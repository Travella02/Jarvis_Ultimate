import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class AppShellDockablePanels038Tests(unittest.TestCase):
    def test_version_and_capabilities_include_dockable_panels(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d")
        capabilities = set(app_shell_capabilities())
        self.assertIn("dockable_workspace_panels", capabilities)
        self.assertIn("resizable_workspace_panels", capabilities)
        self.assertIn("persistent_panel_layouts", capabilities)
        self.assertIn("floating_panel_popouts", capabilities)
        self.assertIn("saved_workspace_layout_presets", capabilities)
        self.assertIn("panel_lock_mode", capabilities)
        self.assertIn("panel_command_palette", capabilities)
        self.assertIn("multi_monitor_panel_popouts", capabilities)

    def test_renderer_contains_layout_persistence_and_popout_controls(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("PANEL_LAYOUT_STORAGE_KEY", renderer)
        self.assertIn("loadPanelLayout", renderer)
        self.assertIn("savePanelLayout", renderer)
        self.assertIn("beginPanelDrag", renderer)
        self.assertIn("beginPanelResize", renderer)
        self.assertIn("popOutPanel", renderer)
        self.assertIn("applyLayoutPreset", renderer)
        self.assertIn("panelCommandInput", renderer)

    def test_renderer_markup_has_layout_controls_and_layout_panel_attributes(self):
        html = Path("app_shell/renderer/index.html").read_text(encoding="utf-8")
        self.assertIn("layoutLockButton", html)
        self.assertIn("layoutResetButton", html)
        self.assertIn("layoutPresetSelect", html)
        self.assertIn("panelCommandInput", html)
        self.assertIn('data-layout-panel="runtime"', html)
        self.assertIn('data-layout-panel="core"', html)
        self.assertIn('data-layout-panel="conversation"', html)

    def test_styles_include_floating_resizable_panel_classes(self):
        css = Path("app_shell/renderer/styles.css").read_text(encoding="utf-8")
        self.assertIn(".dockable-panel.layout-floating", css)
        self.assertIn(".panel-resize-handle", css)
        self.assertIn(".panel-minimized", css)
        self.assertIn(".panel-popped", css)
        self.assertIn(".layout-toast", css)


if __name__ == "__main__":
    unittest.main()
