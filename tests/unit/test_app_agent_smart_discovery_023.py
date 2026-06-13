from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from jarvis.agents.app_agent.agent import Agent as AppAgent
from jarvis.tools.shared.app_discovery import AppAliasStore, AppCandidate, close_app_match, resolve_app_target


class TestAppAgentSmartDiscovery023(unittest.TestCase):
    def test_builtin_alias_resolves_chrome_for_google_phrase_without_opening_during_tests(self) -> None:
        with TemporaryDirectory() as tmp, patch("jarvis.tools.shared.process_tools.subprocess.Popen") as popen, patch(
            "jarvis.tools.shared.app_discovery.os.startfile", create=True
        ) as startfile:
            result = AppAgent().handle(
                "launch google browser",
                context={"config": SimpleNamespace(project_root=Path(tmp)), "dry_run": True},
            )

        self.assertTrue(result.success)
        self.assertEqual(result.action, "open_target")
        self.assertIn(result.data["target"], {"chrome", "Google Chrome", "Chrome"})
        self.assertEqual(result.data["app_match"]["source"], "builtin_alias")
        popen.assert_not_called()
        startfile.assert_not_called()

    def test_learned_alias_resolves_before_scanning(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            app_path = root / "Fake Paint.exe"
            app_path.write_text("fake", encoding="utf-8")
            candidate = AppCandidate(name="Fake Paint", path=str(app_path), aliases=["paint thing"], process_names=["Fake Paint.exe"])
            AppAliasStore(root).save_alias("paint thing", candidate, source="test")

            match = resolve_app_target("paint thing", root)

        self.assertIsNotNone(match.candidate)
        self.assertTrue(match.learned)
        self.assertEqual(match.candidate.name, "Fake Paint")

    def test_discovered_app_match_can_be_tested_with_dry_run_without_opening(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            app_path = root / "Rocket Editor.exe"
            app_path.write_text("fake", encoding="utf-8")
            candidate = AppCandidate(name="Rocket Editor", path=str(app_path), aliases=["rocket editor"], process_names=["Rocket Editor.exe"])
            with patch("jarvis.tools.shared.app_discovery.discover_apps", return_value=[candidate]), patch(
                "jarvis.tools.shared.app_discovery.platform.system", return_value="Windows"
            ), patch("jarvis.tools.shared.app_discovery.os.startfile", create=True) as startfile:
                result = AppAgent().handle(
                    "open my rocket editor",
                    context={"config": SimpleNamespace(project_root=root), "dry_run": True},
                )
                learned = AppAliasStore(root).load_aliases()

        self.assertTrue(result.success)
        self.assertIn("rocket editor", learned)
        self.assertEqual(result.data["launcher"]["message"], "Ready to open Rocket Editor.")
        startfile.assert_not_called()

    def test_close_app_uses_safe_running_process_match(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = AppCandidate(name="Fake Notes", path=str(root / "Fake Notes.exe"), aliases=["notes"], process_names=["FakeNotes.exe"])
            with patch.dict("os.environ", {"JARVIS_ALLOW_OS_LAUNCH_DURING_TESTS": "1"}), patch(
                "jarvis.agents.app_agent.agent.resolve_app_target",
                return_value=type("M", (), {"candidate": candidate, "query": "notes", "to_dict": lambda self: {"query": "notes"}})(),
            ), patch("jarvis.tools.shared.app_discovery._windows_running_processes", return_value=["FakeNotes.exe"]), patch(
                "jarvis.tools.shared.app_discovery.platform.system", return_value="Windows"
            ), patch("jarvis.tools.shared.app_discovery.subprocess.run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = "SUCCESS"
                run.return_value.stderr = ""
                result = AppAgent().handle("close notes", context={"config": SimpleNamespace(project_root=root), "allow_os_launch_during_tests": True})

        self.assertTrue(result.success)
        self.assertEqual(result.action, "close_target")
        run.assert_called_once()
        self.assertIn("taskkill", run.call_args.args[0][0])

    def test_close_blocks_critical_process_names(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = AppCandidate(name="System", aliases=["system"], process_names=["winlogon.exe"])
            match = type("M", (), {"candidate": candidate, "query": "system"})()
            result = close_app_match(match, project_root=root)

        self.assertFalse(result.success)
        self.assertIn("safe process", result.message)


if __name__ == "__main__":
    unittest.main()
