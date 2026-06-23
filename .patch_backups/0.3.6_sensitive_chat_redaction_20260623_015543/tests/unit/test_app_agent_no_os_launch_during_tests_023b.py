from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from jarvis.agents.app_agent.agent import Agent as AppAgent
from jarvis.tools.shared.app_discovery import AppCandidate


class TestAppAgentNoOSLaunchDuringTests023b(unittest.TestCase):
    def test_dry_run_prevents_startfile_for_discovered_app(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            app_path = root / "Real Looking App.exe"
            app_path.write_text("fake", encoding="utf-8")
            candidate = AppCandidate(name="Real Looking App", path=str(app_path), aliases=["real looking app"], process_names=["Real Looking App.exe"])
            with patch("jarvis.tools.shared.app_discovery.discover_apps", return_value=[candidate]), patch(
                "jarvis.tools.shared.app_discovery.platform.system", return_value="Windows"
            ), patch("jarvis.tools.shared.app_discovery.os.startfile", create=True) as startfile:
                result = AppAgent().handle(
                    "open real looking app",
                    context={"config": SimpleNamespace(project_root=root), "dry_run": True},
                )

        self.assertTrue(result.success)
        self.assertEqual(result.data["launcher"]["message"], "Ready to open Real Looking App.")
        startfile.assert_not_called()

    def test_environment_dry_run_prevents_known_app_popen(self) -> None:
        with TemporaryDirectory() as tmp, patch.dict("os.environ", {"JARVIS_APP_AGENT_DRY_RUN": "1"}), patch(
            "jarvis.tools.shared.process_tools.subprocess.Popen"
        ) as popen:
            result = AppAgent().handle("open notepad", context={"config": SimpleNamespace(project_root=Path(tmp))})

        self.assertTrue(result.success)
        self.assertIn("Ready to open", result.message)
        popen.assert_not_called()

    def test_unittest_command_guard_prevents_known_app_popen(self) -> None:
        # The full test suite is launched with ``python -m unittest ...``.
        # In that mode Jarvis may resolve apps, but it must never spawn them.
        with TemporaryDirectory() as tmp, patch("jarvis.tools.shared.process_tools.subprocess.Popen") as popen:
            result = AppAgent().handle("open notepad", context={"config": SimpleNamespace(project_root=Path(tmp))})

        self.assertTrue(result.success)
        self.assertIn("ready to open", result.message.lower())
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
