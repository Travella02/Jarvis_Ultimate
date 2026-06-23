from __future__ import annotations

from pathlib import Path
import unittest

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class TestAppShellActionCards030(unittest.TestCase):
    def test_app_shell_version_and_capabilities_include_030_abilities(self) -> None:
        capabilities = app_shell_capabilities()
        self.assertEqual(APP_SHELL_VERSION, "0.3.3a")
        self.assertIn("ability_registry_foundation", capabilities)
        self.assertIn("safe_app_launcher_ability", capabilities)
        self.assertIn("ui_action_cards", capabilities)

    def test_renderer_contains_action_card_surface(self) -> None:
        index = Path("app_shell/renderer/index.html").read_text(encoding="utf-8")
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        styles = Path("app_shell/renderer/styles.css").read_text(encoding="utf-8")

        self.assertIn("actionCardList", index)
        self.assertIn("renderActionCards", renderer)
        self.assertIn("workspace_cards", renderer)
        self.assertIn("ability-action-card", styles)


if __name__ == "__main__":
    unittest.main()
