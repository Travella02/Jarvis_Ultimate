from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.agents.app_agent.agent import Agent as AppAgent
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.tools.shared.app_discovery import (
    AppAliasStore,
    AppCandidate,
    AppMatch,
    launch_app_match,
)
from jarvis.tools.shared.process_tools import LaunchResult


class TestAppAgentLaunchVerification026(unittest.TestCase):
    def test_version_and_capabilities_include_launch_verification(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.8c")
        capabilities = set(app_shell_capabilities())
        self.assertIn("verified_app_launches", capabilities)
        self.assertIn("verified_app_closes", capabilities)
        self.assertIn("manual_app_alias_learning", capabilities)
        self.assertIn("stale_launcher_fallback_recovery", capabilities)

    def test_verified_launch_waits_for_expected_process(self) -> None:
        candidate = AppCandidate(name="Discord", path="C:/Discord/Discord.exe", launch_type="path", process_names=["Discord.exe"])
        match = AppMatch(candidate, score=1.0, source="test", query="discord")
        with TemporaryDirectory() as tmp, patch.dict("os.environ", {"JARVIS_ALLOW_OS_LAUNCH_DURING_TESTS": "1"}), patch(
            "jarvis.tools.shared.app_discovery.platform.system", return_value="Windows"
        ), patch(
            "jarvis.tools.shared.app_discovery._candidate_is_running", return_value=False
        ), patch(
            "jarvis.tools.shared.app_discovery._launch_path",
            return_value=LaunchResult(True, "Opening Discord, sir.", target="Discord", launch_type="path", command="C:/Discord/Discord.exe"),
        ) as launch_path, patch(
            "jarvis.tools.shared.app_discovery._wait_for_processes", return_value=True
        ) as wait_for_processes:
            result = launch_app_match(match, project_root=tmp, alias_to_learn="discord")

        self.assertTrue(result.success)
        self.assertEqual(result.target, "Discord")
        launch_path.assert_called_once()
        wait_for_processes.assert_called_once()
        self.assertIn("Discord.exe", wait_for_processes.call_args.args[0])

    def test_stale_launcher_retries_refreshed_real_app_path(self) -> None:
        stale = AppCandidate(name="discord", path="C:/Users/JarvisTest/AppData/Local/Discord/Update.exe", launch_type="path", aliases=["discord"], process_names=["Discord.exe"])
        real = AppCandidate(name="discord", path="C:/Users/JarvisTest/AppData/Local/Discord/app-1.0.999/Discord.exe", launch_type="path", aliases=["discord"], process_names=["Discord.exe"])
        match = AppMatch(stale, score=1.0, source="learned_alias", query="discord", learned=True)

        with TemporaryDirectory() as tmp, patch.dict("os.environ", {"JARVIS_ALLOW_OS_LAUNCH_DURING_TESTS": "1"}), patch(
            "jarvis.tools.shared.app_discovery.platform.system", return_value="Windows"
        ), patch(
            "jarvis.tools.shared.app_discovery._candidate_is_running", return_value=False
        ), patch(
            "jarvis.tools.shared.app_discovery._launch_path",
            side_effect=[
                LaunchResult(True, "Opening discord, sir.", target="discord", launch_type="path", command=stale.path),
                LaunchResult(True, "Opening discord, sir.", target="discord", launch_type="path", command=real.path),
            ],
        ) as launch_path, patch(
            "jarvis.tools.shared.app_discovery._wait_for_processes", side_effect=[False, True]
        ), patch(
            "jarvis.tools.shared.app_discovery.discover_apps", return_value=[stale, real]
        ):
            result = launch_app_match(match, project_root=tmp, alias_to_learn="discord")

        self.assertTrue(result.success)
        self.assertEqual(result.command, real.path)
        self.assertEqual(launch_path.call_count, 2)

    def test_manual_alias_teaching_saves_alias_without_opening_app(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = AppCandidate(name="spotify", path="C:/Spotify/Spotify.exe", launch_type="path", aliases=["spotify"], process_names=["Spotify.exe"])
            match = AppMatch(candidate, score=1.0, source="test", query="spotify")
            with patch("jarvis.agents.app_agent.agent.resolve_app_target", return_value=match):
                result = AppAgent().handle(
                    "Jarvis, when I say music, open Spotify",
                    context={"config": SimpleNamespace(project_root=root), "dry_run": True},
                )
            aliases = AppAliasStore(root).load_aliases()

        self.assertTrue(result.success)
        self.assertEqual(result.action, "learn_app_alias")
        self.assertIn("music", aliases)
        self.assertEqual(aliases["music"]["name"], "spotify")


if __name__ == "__main__":
    unittest.main()
