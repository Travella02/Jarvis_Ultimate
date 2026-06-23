from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from jarvis.agents.app_agent.agent import Agent as AppAgent
from jarvis.agents.file_agent.agent import Agent as FileAgent


class TestAppFileAbilities030(unittest.TestCase):
    def test_app_agent_launches_known_app_with_action_card(self) -> None:
        """App-agent tests must resolve apps without launching real OS apps."""

        context = {"config": SimpleNamespace(project_root=Path.cwd()), "dry_run": True}
        with patch("jarvis.tools.shared.process_tools.subprocess.Popen") as process_popen, patch(
            "jarvis.tools.shared.app_discovery.subprocess.Popen"
        ) as discovery_popen:
            result = AppAgent().handle("open notepad", context=context)

        self.assertTrue(result.success)
        self.assertEqual(result.action, "open_target")
        self.assertTrue(result.data["implemented"])
        self.assertEqual(result.data["target"], "notepad")
        self.assertTrue(result.events)
        self.assertEqual(result.events[0].event_type, "ui.workspace_card")
        process_popen.assert_not_called()
        discovery_popen.assert_not_called()

    def test_file_agent_project_status_and_search_are_read_only(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src" / "jarvis" / "agents" / "app_agent").mkdir(parents=True)
            (root / "tests").mkdir()
            (root / "tests" / "test_sample.py").write_text("def test_sample(): pass", encoding="utf-8")
            (root / "app_shell" / "renderer").mkdir(parents=True)
            (root / "app_shell" / "renderer" / "renderer.js").write_text("console.log('renderer')", encoding="utf-8")

            config = SimpleNamespace(project_root=root)
            status_result = FileAgent().handle("Jarvis project status", context={"config": config})
            search_result = FileAgent().handle("search project files for renderer", context={"config": config})

        self.assertTrue(status_result.success)
        self.assertEqual(status_result.action, "project_status")
        self.assertIn("1 agents", status_result.message)
        self.assertTrue(status_result.events)
        self.assertTrue(search_result.success)
        self.assertEqual(search_result.action, "search_project_files")
        self.assertEqual(search_result.data["query"], "renderer")
        self.assertTrue(search_result.data["matches"])

    def test_file_agent_requires_confirmation_for_write_requests(self) -> None:
        result = FileAgent().handle("delete this file", context={"config": SimpleNamespace(project_root=Path.cwd())})
        self.assertTrue(result.needs_confirmation)
        self.assertEqual(result.action, "file_write_confirmation_required")


if __name__ == "__main__":
    unittest.main()
