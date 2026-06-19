import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.tools.shared.app_discovery import (
    AppCandidate,
    _windows_common_executable_candidates,
    close_app_match,
    resolve_app_target,
    AppMatch,
)


class TestAppDiscoverySpeed025(unittest.TestCase):
    def test_version_and_capabilities_include_speed_polish(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.1")
        capabilities = set(app_shell_capabilities())
        self.assertIn("general_app_discovery_speedup", capabilities)
        self.assertIn("startup_app_index_warmup_fix", capabilities)
        self.assertIn("discord_launch_path_fix", capabilities)
        self.assertIn("fast_voice_caption_polling", capabilities)

    def test_discord_alias_resolves_without_deep_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app_dir = root / "Discord" / "app-1.0.999"
            app_dir.mkdir(parents=True)
            (app_dir / "Discord.exe").write_text("", encoding="utf-8")
            with patch.dict("os.environ", {"LOCALAPPDATA": str(root)}, clear=False):
                with patch("jarvis.tools.shared.app_discovery.platform.system", return_value="Windows"):
                    with patch("jarvis.tools.shared.app_discovery.discover_apps") as deep_scan:
                        match = resolve_app_target("open discord", tmp, dry_run=True)
            deep_scan.assert_not_called()
            self.assertIsNotNone(match.candidate)
            self.assertEqual(match.candidate.name, "discord")

    def test_discord_versioned_exe_beats_update_launcher_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app_dir = root / "Discord" / "app-1.0.999"
            app_dir.mkdir(parents=True)
            discord_exe = app_dir / "Discord.exe"
            discord_exe.write_text("", encoding="utf-8")
            update_exe = root / "Discord" / "Update.exe"
            update_exe.write_text("", encoding="utf-8")
            with patch.dict("os.environ", {"LOCALAPPDATA": str(root)}, clear=False):
                with patch("jarvis.tools.shared.app_discovery.platform.system", return_value="Windows"):
                    candidates = _windows_common_executable_candidates()
        discord_paths = [candidate.path for candidate in candidates if candidate.name == "discord"]
        self.assertTrue(any(path.endswith("Discord.exe") for path in discord_paths))

    def test_startup_app_index_warmup_uses_runtime_config(self):
        server = Path("src/jarvis/api/local_server.py").read_text(encoding="utf-8")
        self.assertIn("def _start_app_index_warmup", server)
        self.assertIn("start_app_index_warmup(self.runtime.config.project_root)", server)
        self.assertNotIn("start_app_index_warmup(self.config.project_root)", server)
        self.assertIn('self.runtime.events.emit("app.index_warmup_started"', server)

    def test_close_still_uses_safe_taskkill_path(self):
        candidate = AppCandidate(name="discord", process_names=["Discord.exe"])
        match = AppMatch(candidate, score=1.0, source="test", query="discord")
        with tempfile.TemporaryDirectory() as tmp:
            result = close_app_match(match, project_root=tmp, dry_run=True)
        self.assertTrue(result.success)
        self.assertIn("Discord.exe", result.command)


if __name__ == "__main__":
    unittest.main()
