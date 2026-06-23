import json
import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import (
    APP_SHELL_MODE,
    app_shell_assets,
    app_shell_capabilities,
    build_app_shell_snapshot,
)
from jarvis.ui.workspace import UIWorkspaceState


class TestAppShellFoundation017(unittest.TestCase):
    def test_app_shell_capabilities_describe_native_html_shell(self):
        capabilities = app_shell_capabilities()
        self.assertIn("native_desktop_window", capabilities)
        self.assertIn("html_css_js_renderer", capabilities)
        self.assertIn("local_api_bridge", capabilities)
        self.assertIn("tkinter_fallback_preserved", capabilities)

    def test_snapshot_is_json_serializable_and_state_reactive(self):
        workspace = UIWorkspaceState()
        workspace.avatar.set_state("thinking", expression="focused", message="Testing app shell snapshot.")
        snapshot = build_app_shell_snapshot(workspace, api_url="http://127.0.0.1:9999", bridge_status="online")

        self.assertEqual(snapshot["app"]["mode"], APP_SHELL_MODE)
        self.assertEqual(snapshot["app"]["bridge_status"], "online")
        self.assertEqual(snapshot["avatar"]["state"], "thinking")
        self.assertEqual(snapshot["avatar"]["profile"]["state"], "thinking")
        self.assertIn("thinking", snapshot["visual_states"])
        json.dumps(snapshot)

    def test_app_shell_asset_manifest_uses_project_root(self):
        root = Path("C:/Jarvis_Ultimate")
        assets = app_shell_assets(root)
        self.assertTrue(assets["package_json"].endswith("app_shell/package.json") or assets["package_json"].endswith("app_shell\\package.json"))
        self.assertIn("renderer", assets["index_html"])


if __name__ == "__main__":
    unittest.main()
