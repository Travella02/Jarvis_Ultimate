import json
import unittest
from pathlib import Path


class TestAppShellAssets017(unittest.TestCase):
    def test_electron_app_shell_files_exist(self):
        root = Path(__file__).resolve().parents[2]
        expected = [
            root / "app_shell" / "package.json",
            root / "app_shell" / "main.js",
            root / "app_shell" / "preload.js",
            root / "app_shell" / "renderer" / "index.html",
            root / "app_shell" / "renderer" / "styles.css",
            root / "app_shell" / "renderer" / "renderer.js",
        ]
        for path in expected:
            self.assertTrue(path.exists(), f"missing app-shell asset: {path}")

    def test_package_json_declares_electron_start_script(self):
        root = Path(__file__).resolve().parents[2]
        package = json.loads((root / "app_shell" / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["name"], "jarvis-ultimate-app-shell")
        self.assertEqual(package["scripts"]["start"], "electron .")
        self.assertIn("electron", package["devDependencies"])

    def test_renderer_contains_state_and_api_hooks(self):
        root = Path(__file__).resolve().parents[2]
        renderer_js = (root / "app_shell" / "renderer" / "renderer.js").read_text(encoding="utf-8")
        styles_css = (root / "app_shell" / "renderer" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("/api/state", renderer_js)
        self.assertIn("/api/command", renderer_js)
        self.assertIn("state-thinking", styles_css)
        self.assertIn("orb-sphere", styles_css)


if __name__ == "__main__":
    unittest.main()
