from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import unittest

from jarvis.core.result import JarvisEvent
from jarvis.ui.components import panel_header, summarize_payload
from jarvis.ui.panels import create_default_panel_registry
from jarvis.ui.workspace import UIWorkspaceState


class TestUIWorkspacePanels016b(unittest.TestCase):
    def test_default_registry_has_future_workspace_panels(self):
        registry = create_default_panel_registry()
        for name in ["web_results", "generated_images", "file_results", "screen_context", "agent_dashboard"]:
            self.assertIn(name, registry.names())

    def test_close_panel_event_closes_panel(self):
        workspace = UIWorkspaceState()
        workspace.apply_event(JarvisEvent("ui.open_panel", data={"panel_id": "web_results", "title": "Web Results"}))
        self.assertTrue(workspace.panels["web_results"].is_open)
        workspace.apply_event(JarvisEvent("ui.close_panel", data={"panel_id": "web_results"}))
        self.assertFalse(workspace.panels["web_results"].is_open)

    def test_workspace_card_event_creates_card(self):
        workspace = UIWorkspaceState()
        workspace.apply_event(JarvisEvent("ui.workspace_card", message="Image ready", data={"card_type": "image", "title": "Generated Image", "payload": {"path": "x.png"}}))
        self.assertEqual(workspace.workspace_cards[0]["type"], "image")
        self.assertEqual(workspace.workspace_cards[0]["payload"]["path"], "x.png")

    def test_component_helpers_format_panel_text(self):
        self.assertEqual(panel_header("web results", "◎"), "◎ WEB RESULTS")
        lines = summarize_payload({"paths": ["a.png", "b.png"], "count": 2})
        self.assertIn("paths: 2 item(s)", lines)


if __name__ == "__main__":
    unittest.main()
