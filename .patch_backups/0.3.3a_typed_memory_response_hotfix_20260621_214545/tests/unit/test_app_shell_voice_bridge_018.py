import json
import tempfile
import time
import unittest
from pathlib import Path
from urllib import request

from jarvis.api.local_server import LocalJarvisAPI, make_local_api_server
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider
from jarvis.providers.stt.base import STTResult
from jarvis.providers.tts.base import TTSResult


class SequenceSTTManager:
    enabled = True
    provider_name = "fake_stt"
    listen_mode = "smart"
    silence_seconds = 0.1
    record_seconds = 0.1
    max_audio_files = 30

    def __init__(self, texts):
        self.texts = list(texts)
        self.calls = []

    def listen_once(self, *, duration_seconds=None, mode=None, silence_seconds=None):
        self.calls.append({"duration_seconds": duration_seconds, "mode": mode, "silence_seconds": silence_seconds})
        text = self.texts.pop(0) if self.texts else "exit voice mode"
        return STTResult.ok(
            "fake STT complete",
            provider="fake_stt",
            text=text,
            audio_path=Path("data/stt/fake.wav"),
            language="en",
            duration_seconds=0.1,
        )

    def status(self):
        return "fake STT status"

    def providers_summary(self):
        return "fake STT providers"

    def gpu_status(self):
        return "fake GPU status"

    def warmup(self):
        return STTResult.ok("fake warmup", provider="fake_stt", text="")

    def listen_settings_summary(self):
        return "fake listen settings"

    def record_once(self):
        return "fake record"

    def transcribe_file(self, path):
        return STTResult.ok("fake file STT", provider="fake_stt", text="file text", audio_path=Path(path))

    def format_debug_last(self):
        return "fake STT debug"


class FakeTTSManager:
    def __init__(self):
        self.enabled = True
        self.auto_speak = False
        self.playback = True
        self.provider_name = "fake_tts"
        self.max_output_files = 30
        self.calls = []

    def say(self, text, *, play_audio=None):
        self.calls.append((text, play_audio))
        return TTSResult.ok("fake TTS generated", provider="fake_tts", played=bool(play_audio), data={"text": text})

    def stop_playback(self):
        return True

    def status(self):
        return "fake TTS status"


class TestAppShellVoiceBridge018(unittest.TestCase):
    def _runtime(self, tmp, texts):
        return JarvisRuntime(
            project_root=tmp,
            llm_provider=MockLLMProvider(canned_response="Online, sir."),
            stt_manager=SequenceSTTManager(texts),
            tts_manager=FakeTTSManager(),
        )

    def _wait_until_idle(self, api, timeout=3.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            session = api.voice_session_snapshot()
            if not session.get("running") and not session.get("thread_alive"):
                return session
            time.sleep(0.02)
        self.fail("voice session did not finish")

    def test_app_shell_version_and_capabilities_include_voice_bridge(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.3")
        capabilities = app_shell_capabilities()
        self.assertIn("real_voice_once_control", capabilities)
        self.assertIn("sleep_wake_voice_control", capabilities)
        self.assertIn("voice_stop_control", capabilities)

    def test_voice_once_runs_real_runtime_voice_pipeline_in_background(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self._runtime(tmp, ["What is your status?"])
            api = LocalJarvisAPI(runtime=runtime, project_root=tmp)
            started = api.start_voice_once({"speak": True, "silence_seconds": 0.2})
            self.assertTrue(started["success"])
            session = self._wait_until_idle(api)
            self.assertEqual(session["mode"], "one_turn")
            self.assertTrue(session["warmup_complete"])
            self.assertEqual(session["turns_heard"], 1)
            self.assertEqual(session["turns_handled"], 1)
            self.assertEqual(session["last_transcript"], "What is your status?")
            self.assertIn("Online, sir.", session["last_response"])
            self.assertEqual(runtime.stt_manager.calls[0]["silence_seconds"], 0.2)
            self.assertEqual([call[0] for call in runtime.tts_manager.calls], ["Online, sir."])
            runtime.spoken_pipeline.shutdown()

    def test_sleep_wake_session_handles_wake_command_and_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self._runtime(tmp, ["background noise", "Hey Jarvis what is your status", "exit voice mode"])
            api = LocalJarvisAPI(runtime=runtime, project_root=tmp)
            started = api.start_sleep_wake({"max_turns": 4, "speak": True, "silence_seconds": 0.15})
            self.assertTrue(started["success"])
            session = self._wait_until_idle(api)
            self.assertEqual(session["mode"], "sleep_wake")
            self.assertEqual(session["turns_heard"], 3)
            self.assertEqual(session["turns_handled"], 1)
            self.assertEqual(session["turns_ignored"], 1)
            self.assertIn("what is your status", session["last_command"].lower())
            self.assertIn("Online, sir.", session["last_response"])
            runtime.spoken_pipeline.shutdown()

    def test_http_voice_once_endpoint_starts_session_and_state_contains_voice(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self._runtime(tmp, ["What is your status?"])
            server, api = make_local_api_server(host="127.0.0.1", port=0, runtime=runtime, project_root=tmp)
            url = api.api_url
            try:
                import threading
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                req = request.Request(
                    f"{url}/api/voice/once",
                    data=json.dumps({"speak": False}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with request.urlopen(req, timeout=3) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                self.assertTrue(payload["success"])
                session = self._wait_until_idle(api)
                self.assertEqual(session["last_transcript"], "What is your status?")
                with request.urlopen(f"{url}/api/state", timeout=3) as response:
                    state_payload = json.loads(response.read().decode("utf-8"))
                self.assertIn("voice", state_payload["data"])
                self.assertEqual(state_payload["data"]["voice"]["mode"], "one_turn")
            finally:
                server.shutdown()
                server.server_close()
                runtime.spoken_pipeline.shutdown()


if __name__ == "__main__":
    unittest.main()
