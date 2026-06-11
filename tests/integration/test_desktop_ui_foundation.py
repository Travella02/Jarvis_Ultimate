from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import unittest

from jarvis.clients.desktop.app import JarvisDesktopApp
from jarvis.ui.workspace import UIWorkspaceState


class TestDesktopUIFoundation(unittest.TestCase):
    def test_desktop_app_can_be_constructed_without_starting_tk(self):
        app = JarvisDesktopApp(project_root=ROOT)
        self.assertIsInstance(app.workspace, UIWorkspaceState)
        self.assertIn("workspace", app.workspace.panels)

    def test_workspace_supports_future_drop_in_panels(self):
        workspace = UIWorkspaceState()
        workspace.open_panel("generated_images", title="Generated Images", panel_type="image_grid", payload={"paths": ["a.png"]})
        snapshot = workspace.snapshot()
        self.assertEqual(snapshot["panels"]["generated_images"]["panel_type"], "image_grid")
        self.assertEqual(snapshot["panels"]["generated_images"]["payload"]["paths"], ["a.png"])


if __name__ == "__main__":
    unittest.main()
