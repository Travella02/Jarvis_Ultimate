import inspect
import unittest

from jarvis.clients.desktop.app import JarvisDesktopApp


class TestDesktopSolidOrb016d(unittest.TestCase):
    def test_desktop_imports_solid_orb_renderer(self):
        source = inspect.getsource(JarvisDesktopApp._render_avatar)
        self.assertIn("solid_orb_layers", source)
        self.assertIn("SOLID ORB RENDERER", source)
        self.assertIn("orbital_ring_plan", source)

    def test_layout_still_uses_central_orb_workspace(self):
        self.assertEqual(JarvisDesktopApp.layout_mode, "central_orb_workspace")


if __name__ == "__main__":
    unittest.main()
