import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen, Request

from jarvis.api.local_server import LocalJarvisAPI, make_local_api_server


class TestLocalAPIAppShell017(unittest.TestCase):
    def _temp_project(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / ".env").write_text("JARVIS_LLM_PROVIDER=mock\nJARVIS_TTS_PROVIDER=mock\nJARVIS_STT_PROVIDER=mock\n", encoding="utf-8")
        (root / "config").mkdir(exist_ok=True)
        return temp, root

    def test_local_api_builds_state_snapshot(self):
        temp, root = self._temp_project()
        with temp:
            api = LocalJarvisAPI(project_root=root, api_url="http://127.0.0.1:8765")
            snapshot = api.snapshot()
            self.assertEqual(snapshot["app"]["bridge_status"], "online")
            self.assertTrue(snapshot["runtime"]["started"])
            self.assertGreaterEqual(snapshot["runtime"]["agent_count"], 1)
            self.assertEqual(snapshot["runtime"]["llm_provider"], "mock")

    def test_local_http_server_exposes_health_and_state(self):
        temp, root = self._temp_project()
        with temp:
            server, _api = make_local_api_server(host="127.0.0.1", port=0, project_root=root)
            thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
            thread.start()
            try:
                base = f"http://{server.server_address[0]}:{server.server_address[1]}"
                health = json.loads(urlopen(base + "/api/health", timeout=5).read().decode("utf-8"))
                self.assertTrue(health["success"])
                state = json.loads(urlopen(base + "/api/state", timeout=5).read().decode("utf-8"))
                self.assertEqual(state["data"]["app"]["bridge_status"], "online")
                self.assertIn("avatar", state["data"])
            finally:
                server.shutdown()
                server.server_close()

    def test_local_http_server_accepts_command(self):
        temp, root = self._temp_project()
        with temp:
            server, _api = make_local_api_server(host="127.0.0.1", port=0, project_root=root)
            thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
            thread.start()
            try:
                base = f"http://{server.server_address[0]}:{server.server_address[1]}"
                request = Request(
                    base + "/api/command",
                    data=json.dumps({"command": "list agents"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                response = json.loads(urlopen(request, timeout=5).read().decode("utf-8"))
                self.assertTrue(response["success"])
                self.assertIn("state", response["data"])
                self.assertIn("jarvis", [m["role"] for m in response["data"]["state"]["workspace"]["chat_messages"]])
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
