from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from jarvis.agents.app_agent.agent import Agent as AppAgent
from jarvis.core.config import JarvisConfig
from jarvis.tools.shared.app_discovery import AppCandidate, close_app_match


class TestAppAgentTaskkillAndSTT023e(unittest.TestCase):
    def test_close_uses_taskkill_force_tree_for_known_app(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = AppCandidate(name="chrome", aliases=["chrome", "google chrome"], process_names=["chrome.exe"])
            match = type("M", (), {"candidate": candidate, "query": "chrome", "to_dict": lambda self: {"query": "chrome"}})()
            with patch.dict("os.environ", {"JARVIS_ALLOW_OS_LAUNCH_DURING_TESTS": "1"}), patch(
                "jarvis.agents.app_agent.agent.resolve_app_target", return_value=match
            ), patch("jarvis.tools.shared.app_discovery.platform.system", return_value="Windows"), patch(
                "jarvis.tools.shared.app_discovery._windows_running_processes", return_value=["chrome.exe"]
            ), patch("jarvis.tools.shared.app_discovery.subprocess.run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = "SUCCESS"
                run.return_value.stderr = ""
                result = AppAgent().handle("close chrome", context={"config": SimpleNamespace(project_root=root), "allow_os_launch_during_tests": True})

        self.assertTrue(result.success)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], ["taskkill", "/IM", "chrome.exe", "/T", "/F"])

    def test_close_blocks_jarvis_terminal_processes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = AppCandidate(name="Python", aliases=["python"], process_names=["python.exe", "powershell.exe"])
            match = type("M", (), {"candidate": candidate, "query": "python"})()
            result = close_app_match(match, project_root=root)

        self.assertFalse(result.success)
        self.assertIn("safe process", result.message)

    def test_default_stt_config_prefers_clearer_auto_model(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config" / "providers.yaml").write_text(
                "\n".join([
                    "providers:",
                    "  stt:",
                    "    default: faster_whisper",
                    "    model: medium.en",
                    "    device: auto",
                    "    compute_type: auto",
                    "    gpu_fallback_to_cpu: true",
                ]),
                encoding="utf-8",
            )
            config = JarvisConfig.from_project_root(root)

        self.assertEqual(config.stt_model, "medium.en")
        self.assertEqual(config.stt_device, "auto")
        self.assertEqual(config.stt_compute_type, "auto")
        self.assertTrue(config.stt_gpu_fallback_to_cpu)


if __name__ == "__main__":
    unittest.main()
