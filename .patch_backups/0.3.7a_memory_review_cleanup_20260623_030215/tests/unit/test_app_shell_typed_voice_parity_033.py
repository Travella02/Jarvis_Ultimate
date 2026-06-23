from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from jarvis.api.local_server import LocalJarvisAPI
from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider
from jarvis.providers.stt.base import STTResult
from jarvis.providers.tts.base import TTSResult


class FakeSTTManager:
    enabled = True
    provider_name = "fake_stt"
    listen_mode = "smart"
    silence_seconds = 0.1
    record_seconds = 0.1
    start_timeout_seconds = 0.1
    max_audio_files = 30

    def listen_once(self, *, duration_seconds=None, mode=None, silence_seconds=None):
        return STTResult.ok("fake STT complete", provider="fake_stt", text="", audio_path=Path("fake.wav"), language="en", duration_seconds=0.1)

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
    def __init__(self) -> None:
        self.enabled = True
        self.auto_speak = False
        self.playback = True
        self.provider_name = "fake_tts"
        self.max_output_files = 30
        self.calls: list[tuple[str, bool | None]] = []

    def say(self, text, *, play_audio=None):
        self.calls.append((str(text), play_audio))
        return TTSResult.ok("fake TTS generated", provider="fake_tts", played=bool(play_audio), data={"text": text})

    def stop_playback(self):
        return True

    def status(self):
        return "fake TTS status"

    def warmup(self):
        return TTSResult.ok("fake warmup", provider="fake_tts", played=False)


class AlwaysAliveThread:
    def is_alive(self) -> bool:
        return True


class TestAppShellTypedVoiceParity033(unittest.TestCase):
    def _runtime(self, tmp: str, response: str = "Online, sir.") -> JarvisRuntime:
        return JarvisRuntime(
            project_root=tmp,
            llm_provider=MockLLMProvider(canned_response=response),
            stt_manager=FakeSTTManager(),
            tts_manager=FakeTTSManager(),
        )

    def test_version_and_capability_include_typed_input_voice_parity(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.7")
        capabilities = app_shell_capabilities()
        self.assertIn("typed_input_voice_parity", capabilities)
        self.assertIn("typed_input_visual_hold", capabilities)
        self.assertIn("humanized_memory_search_responses", capabilities)

    def test_typed_app_shell_command_speaks_response_without_wake_word(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self._runtime(tmp, "Typed input is connected, sir.")
            api = LocalJarvisAPI(runtime=runtime, project_root=tmp)

            response = api.handle_command("What is your status?", speak=True, input_mode="typed")
            session = response["data"]["state"]["voice"]
            runtime.spoken_pipeline.shutdown()

        self.assertTrue(response["success"])
        self.assertIn("Typed input is connected", response["data"]["response_text"])
        self.assertGreaterEqual(response["data"]["spoken_chunks"], 1)
        self.assertEqual(session["last_command"], "What is your status?")
        self.assertEqual(session["last_input_mode"], "typed")
        self.assertEqual(session["typed_turns_handled"], 1)
        self.assertTrue(runtime.tts_manager.calls)
        self.assertIn("Typed input is connected", runtime.tts_manager.calls[0][0])

    def test_typed_command_preserves_running_sleep_wake_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self._runtime(tmp, "Still listening after typed input, sir.")
            api = LocalJarvisAPI(runtime=runtime, project_root=tmp)
            api.boot()
            with api._voice_lock:
                api._voice_session = api._new_voice_session(mode="sleep_wake", options={"max_turns": 0, "speak": True})
                api._voice_session.update({"running": True, "last_status": "Listening while awake (1)..."})
                api._voice_thread = AlwaysAliveThread()  # type: ignore[assignment]
            with api._lock:
                api.workspace.avatar.set_state("listening", expression="focused", message="Listening while awake (1)...")

            response = api.handle_command("Who is Kenleigh?", speak=True, input_mode="typed")
            state = response["data"]["state"]
            session = state["voice"]
            runtime.spoken_pipeline.shutdown()

        self.assertTrue(response["success"])
        self.assertTrue(session["running"])
        self.assertTrue(session["thread_alive"])
        self.assertEqual(session["mode"], "sleep_wake")
        self.assertEqual(session["last_command"], "Who is Kenleigh?")
        self.assertEqual(session["typed_turns_handled"], 1)
        self.assertIn(state["avatar"]["state"], {"listening", "sleeping"})
        self.assertNotEqual(state["avatar"]["state"], "idle")

    def test_typed_visual_hold_prevents_background_sleep_wake_flicker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self._runtime(tmp, "Still here, sir.")
            api = LocalJarvisAPI(runtime=runtime, project_root=tmp)
            api.boot()
            with api._lock:
                api.workspace.avatar.set_state("speaking", expression="active", message="Jarvis is speaking...")
            api._set_typed_visual_hold(5.0)

            api._set_voice_visual("No wake phrase heard; staying asleep.", state="sleeping", expression="calm")
            snapshot = api.snapshot()
            runtime.spoken_pipeline.shutdown()

        self.assertEqual(snapshot["avatar"]["state"], "speaking")
        self.assertEqual(snapshot["voice"].get("background_last_status"), "No wake phrase heard; staying asleep.")
        self.assertNotEqual(snapshot["voice"].get("last_status"), "No wake phrase heard; staying asleep.")


if __name__ == "__main__":
    unittest.main()
