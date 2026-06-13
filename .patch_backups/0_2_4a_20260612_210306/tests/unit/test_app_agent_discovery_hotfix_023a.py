from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from jarvis.agents.app_agent.agent import Agent as AppAgent
from jarvis.tools.shared.app_discovery import AppCandidate, close_app_match, resolve_app_target


class TestAppAgentDiscoveryHotfix023a(unittest.TestCase):
    def test_builtin_alias_uses_fast_known_path_before_deep_scan(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            chrome_path = root / "Google" / "Chrome" / "Application" / "chrome.exe"
            chrome_path.parent.mkdir(parents=True)
            chrome_path.write_text("fake", encoding="utf-8")
            common_paths = {"chrome": [str(chrome_path)]}
            with patch.dict("os.environ", {"JARVIS_ALLOW_OS_LAUNCH_DURING_TESTS": "1"}), \
                 patch("jarvis.tools.shared.app_discovery.WINDOWS_COMMON_EXECUTABLES", common_paths), \
                 patch("jarvis.tools.shared.app_discovery.discover_apps") as discover_apps, \
                 patch("jarvis.tools.shared.app_discovery.platform.system", return_value="Windows"), \
                 patch("jarvis.tools.shared.app_discovery.os.startfile", create=True) as startfile:
                result = AppAgent().handle("open google browser", context={"config": SimpleNamespace(project_root=root), "allow_os_launch_during_tests": True})

        self.assertTrue(result.success)
        self.assertEqual(result.data["target"], "chrome")
        self.assertEqual(result.data["app_match"]["source"], "builtin_alias")
        discover_apps.assert_not_called()
        startfile.assert_called_once_with(str(chrome_path))

    def test_resolve_refreshes_stale_cache_before_giving_up(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            app_path = root / "Rocket Painter.exe"
            app_path.write_text("fake", encoding="utf-8")
            candidate = AppCandidate(name="Rocket Painter", path=str(app_path), aliases=["rocket painter"], process_names=["RocketPainter.exe"])
            with patch("jarvis.tools.shared.app_discovery.discover_apps", side_effect=[[], [candidate]]):
                match = resolve_app_target("rocket painter", root)

        self.assertIsNotNone(match.candidate)
        self.assertEqual(match.candidate.name, "Rocket Painter")

    def test_close_calculator_matches_windows_calculator_process(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            match = resolve_app_target("calculator", root)
            with patch("jarvis.tools.shared.app_discovery.platform.system", return_value="Windows"), \
                 patch("jarvis.tools.shared.app_discovery._windows_running_processes", return_value=["CalculatorApp.exe"]), \
                 patch.dict("os.environ", {"JARVIS_ALLOW_OS_LAUNCH_DURING_TESTS": "1"}), \
                 patch("jarvis.tools.shared.app_discovery.subprocess.run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = "SUCCESS"
                run.return_value.stderr = ""
                result = close_app_match(match, project_root=root)

        self.assertTrue(result.success)
        command = run.call_args.args[0]
        self.assertEqual(command[:2], ["taskkill", "/IM"])
        self.assertEqual(command[2], "CalculatorApp.exe")


if __name__ == "__main__":
    unittest.main()
