from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import unittest

from jarvis.ui.panels import UIPanelRegistry, UIPanelSpec, create_default_panel_registry


class TestUIPanelRegistry(unittest.TestCase):
    def test_default_registry_has_workspace_panel(self):
        registry = create_default_panel_registry()
        self.assertIn("workspace", registry.names())
        self.assertEqual(registry.get("workspace").panel_type, "workspace")

    def test_register_custom_panel_for_future_agent(self):
        registry = UIPanelRegistry()
        spec = registry.register(UIPanelSpec("image_results", "Image Results", "image_grid"))
        self.assertIs(registry.get("image_results"), spec)
        self.assertEqual(registry.names(), ["image_results"])

    def test_panel_requires_id(self):
        registry = UIPanelRegistry()
        with self.assertRaises(ValueError):
            registry.register(UIPanelSpec("", "Broken"))


if __name__ == "__main__":
    unittest.main()
