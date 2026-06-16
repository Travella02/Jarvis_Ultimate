from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.agents.app_agent.agent import Agent as AppAgent
from jarvis.brain.intent_classifier import IntentClassifier
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.tools.shared.app_discovery import AppAliasStore, AppCandidate, AppMatch, focus_app_match, launch_app_match


class TestAppAgentAliasRoles027(unittest.TestCase):
    def test_version_and_capabilities_include_alias_roles(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.2.9")
        capabilities = set(app_shell_capabilities())
        self.assertIn("multi_app_alias_management", capabilities)
        self.assertIn("default_app_roles", capabilities)
        self.assertIn("app_focus_existing_windows", capabilities)
        self.assertIn("alias_forget_list_rename_commands", capabilities)

    def test_multiple_aliases_for_one_app_are_saved(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = AppCandidate(name="spotify", path="C:/Spotify/Spotify.exe", launch_type="path", aliases=["spotify"], process_names=["Spotify.exe"])
            match = AppMatch(candidate, score=1.0, source="test", query="spotify")
            with patch("jarvis.agents.app_agent.agent.resolve_app_target", return_value=match):
                result = AppAgent().handle("Jarvis, when I say music or jams, open Spotify", context={"config": SimpleNamespace(project_root=root), "dry_run": True})
            aliases = AppAliasStore(root).load_aliases()

        self.assertTrue(result.success)
        self.assertEqual(result.action, "learn_app_alias")
        self.assertIn("music", aliases)
        self.assertIn("jams", aliases)
        self.assertEqual(aliases["music"]["name"], "spotify")
        self.assertEqual(aliases["jams"]["name"], "spotify")

    def test_default_browser_role_saves_browser_alias(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = AppCandidate(name="edge", path="C:/Edge/msedge.exe", launch_type="path", aliases=["edge", "microsoft edge"], process_names=["msedge.exe"])
            match = AppMatch(candidate, score=1.0, source="test", query="microsoft edge")
            with patch("jarvis.agents.app_agent.agent.resolve_app_target", return_value=match):
                result = AppAgent().handle("Jarvis, use Microsoft Edge as my main browser", context={"config": SimpleNamespace(project_root=root), "dry_run": True})
            store = AppAliasStore(root)
            aliases = store.load_aliases()
            roles = store.load_roles()

        self.assertTrue(result.success)
        self.assertEqual(result.action, "set_default_app_role")
        self.assertIn("browser", aliases)
        self.assertIn("main browser", aliases)
        self.assertIn("browser", roles)
        self.assertEqual(aliases["browser"]["name"], "edge")

    def test_learned_role_alias_beats_builtin_browser(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            edge_path = root / "msedge.exe"
            edge_path.write_text("fake edge", encoding="utf-8")
            edge = AppCandidate(name="edge", path=str(edge_path), launch_type="path", aliases=["edge"], process_names=["msedge.exe"])
            AppAliasStore(root).save_role("browser", edge, source="test")
            result = AppAgent().handle("open browser", context={"config": SimpleNamespace(project_root=root), "dry_run": True})

        self.assertTrue(result.success)
        self.assertEqual(result.data["app_match"]["source"], "learned_alias")
        self.assertEqual(result.data["app_match"]["candidate"]["name"], "edge")

    def test_forget_alias_understands_nickname_wording(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            spotify = AppCandidate(name="spotify", path="C:/Spotify/Spotify.exe", launch_type="path", aliases=["spotify"], process_names=["Spotify.exe"])
            store = AppAliasStore(root)
            store.save_aliases(["music", "jams"], spotify, source="test")
            result = AppAgent().handle("Jarvis, forget the nickname jams", context={"config": SimpleNamespace(project_root=root), "dry_run": True})
            aliases = store.load_aliases()

        self.assertTrue(result.success)
        self.assertIn("music", aliases)
        self.assertNotIn("jams", aliases)

    def test_rename_alias_moves_to_new_name(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            spotify = AppCandidate(name="spotify", path="C:/Spotify/Spotify.exe", launch_type="path", aliases=["spotify"], process_names=["Spotify.exe"])
            store = AppAliasStore(root)
            store.save_alias("music", spotify, source="test")
            result = AppAgent().handle("Jarvis, rename music to jams", context={"config": SimpleNamespace(project_root=root), "dry_run": True})
            aliases = store.load_aliases()

        self.assertTrue(result.success)
        self.assertNotIn("music", aliases)
        self.assertIn("jams", aliases)
        self.assertEqual(aliases["jams"]["name"], "spotify")

    def test_list_aliases_reports_grouped_names(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            spotify = AppCandidate(name="spotify", path="C:/Spotify/Spotify.exe", launch_type="path", aliases=["spotify"], process_names=["Spotify.exe"])
            AppAliasStore(root).save_aliases(["music", "jams"], spotify, source="test")
            result = AppAgent().handle("Jarvis, what app aliases do you remember?", context={"config": SimpleNamespace(project_root=root), "dry_run": True})

        self.assertTrue(result.success)
        self.assertEqual(result.action, "list_app_aliases")
        self.assertIn("spotify", result.message.lower())
        self.assertIn("music", result.message.lower())
        self.assertIn("jams", result.message.lower())

    def test_focus_command_uses_focus_action_without_launching(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            code = AppCandidate(name="vs code", path="C:/VSCode/Code.exe", launch_type="path", aliases=["vs code"], process_names=["Code.exe"])
            match = AppMatch(code, score=1.0, source="test", query="vs code")
            with patch("jarvis.agents.app_agent.agent.resolve_app_target", return_value=match):
                result = AppAgent().handle("Jarvis, switch to VS Code", context={"config": SimpleNamespace(project_root=root), "dry_run": True})

        self.assertTrue(result.success)
        self.assertEqual(result.action, "focus_target")
        self.assertEqual(result.data["launch_type"], "focus")

    def test_open_existing_running_app_focuses_instead_of_launching(self) -> None:
        candidate = AppCandidate(name="chrome", path="C:/Chrome/chrome.exe", launch_type="path", aliases=["chrome"], process_names=["chrome.exe"])
        match = AppMatch(candidate, score=1.0, source="test", query="chrome")
        with TemporaryDirectory() as tmp, patch("jarvis.tools.shared.app_discovery._candidate_is_running", return_value=True), patch(
            "jarvis.tools.shared.app_discovery.focus_app_match",
            return_value=focus_app_match(match, dry_run=True),
        ) as focus_mock, patch("jarvis.tools.shared.app_discovery._launch_path") as launch_mock:
            result = launch_app_match(match, project_root=tmp, dry_run=True)

        self.assertTrue(result.success)
        self.assertEqual(result.launch_type, "focus")
        focus_mock.assert_called_once()
        launch_mock.assert_not_called()

    def test_alias_management_phrases_route_to_app_control(self) -> None:
        classifier = IntentClassifier()
        phrases = [
            "Jarvis, when I say music or jams, open Spotify",
            "Jarvis, use Microsoft Edge as my main browser",
            "Jarvis, forget the nickname jams",
            "Jarvis, what app aliases do you remember",
        ]
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                result = classifier.classify(phrase)
                self.assertEqual(result.intent, "app_control")
                self.assertGreaterEqual(result.confidence, 0.85)


if __name__ == "__main__":
    unittest.main()
