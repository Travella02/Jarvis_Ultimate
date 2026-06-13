from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.tools.shared.app_discovery import resolve_app_target, start_app_index_warmup
from jarvis.tools.shared.process_tools import command_for_known_app


class TestAppDiscoverySpeed024(unittest.TestCase):
    def test_snipping_tool_resolves_as_fast_builtin_without_deep_scan(self) -> None:
        with TemporaryDirectory() as tmp, patch("jarvis.tools.shared.app_discovery.discover_apps") as discover:
            match = resolve_app_target("snipping tool", tmp, dry_run=True)

        self.assertIsNotNone(match.candidate)
        self.assertEqual(match.source, "builtin_alias")
        self.assertEqual(match.candidate.name, "snipping tool")
        discover.assert_not_called()

    def test_snipping_tool_has_windows_command(self) -> None:
        with patch("jarvis.tools.shared.process_tools.platform.system", return_value="Windows"):
            command = command_for_known_app("snipping tool")
        self.assertIsNotNone(command)
        self.assertTrue(any("snipping" in part.lower() or "screenclip" in part.lower() for part in command or []))

    def test_app_index_warmup_is_disabled_during_tests(self) -> None:
        with TemporaryDirectory() as tmp, patch("jarvis.tools.shared.app_discovery.discover_apps") as discover:
            started = start_app_index_warmup(tmp, force_refresh=True)
        self.assertFalse(started)
        discover.assert_not_called()


if __name__ == "__main__":
    unittest.main()
