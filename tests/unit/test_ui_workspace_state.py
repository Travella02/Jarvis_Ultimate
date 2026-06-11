from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import unittest

from jarvis.core.result import JarvisEvent
from jarvis.ui.workspace import UIWorkspaceState


class TestUIWorkspaceState(unittest.TestCase):
    def test_workspace_opens_dynamic_panel_from_event(self):
        workspace = UIWorkspaceState()
        workspace.apply_event(JarvisEvent("ui.open_panel", data={"panel_id": "web_results", "title": "Web Results", "payload": {"count": 3}}))
        panel = workspace.panels["web_results"]
        self.assertTrue(panel.is_open)
        self.assertEqual(panel.title, "Web Results")
        self.assertEqual(panel.payload["count"], 3)

    def test_workspace_maps_voice_events_to_avatar_state(self):
        workspace = UIWorkspaceState()
        workspace.apply_event(JarvisEvent("voice.sleep_wake_loop_started", message="Waiting for wake phrase"))
        self.assertEqual(workspace.avatar.state, "wake_listening")
        workspace.apply_event(JarvisEvent("lm_studio.first_chunk", message="Speaking"))
        self.assertEqual(workspace.avatar.state, "speaking")

    def test_snapshot_is_serializable_shape(self):
        workspace = UIWorkspaceState()
        workspace.add_chat_message("user", "hello")
        workspace.add_workspace_card("reminder", "Reminder", {"text": "test"})
        snapshot = workspace.snapshot()
        self.assertIn("avatar", snapshot)
        self.assertIn("panels", snapshot)
        self.assertEqual(snapshot["chat_messages"][0]["text"], "hello")
        self.assertEqual(snapshot["workspace_cards"][0]["type"], "reminder")


if __name__ == "__main__":
    unittest.main()
