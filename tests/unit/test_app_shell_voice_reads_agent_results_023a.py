from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jarvis.api.local_server import LocalJarvisAPI
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider
from jarvis.providers.stt.base import STTResult
from jarvis.providers.tts.base import TTSResult


class FakeSTTManager:
    enabled = True
    provider_name = "fake_stt"
    listen_mode = "smart"
    silence_seconds = 0.4
    record_seconds = 1.0
    start_timeout_seconds = 1.0

    def listen_once(self, *, duration_seconds=None, mode=None, silence_seconds=None):
        return STTResult.ok("fake STT complete", provider="fake_stt", text="hey jarvis open notepad", audio_path=Path("fake.wav"), language="en", duration_seconds=1.0)

    def status(self):
        return "fake STT status"

    def warmup(self):
        return STTResult.ok("fake warmup", provider="fake_stt", text="")


class FakeTTSManager:
    def __init__(self) -> None:
        self.enabled = True
        self.auto_speak = False
        self.playback = True
        self.provider_name = "fake_tts"
        self.max_output_files = 30
        self.calls: list[tuple[str, bool | None]] = []

    def say(self, text, *, play_audio=None):
        self.calls.append((text, play_audio))
        return TTSResult.ok("fake TTS generated", provider="fake_tts", played=bool(play_audio), data={"text": text})

    def stop_playback(self):
        return True

    def status(self):
        return "fake TTS status"

    def warmup(self):
        return TTSResult.ok("fake warmup", provider="fake_tts", played=False)


class TestAppShellVoiceReadsAgentResults023a(unittest.TestCase):
    def test_app_shell_sleep_wake_speaks_non_llm_agent_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {"JARVIS_APP_AGENT_DRY_RUN": "1"}), patch("jarvis.tools.shared.process_tools.subprocess.Popen") as popen:
            tts = FakeTTSManager()
            runtime = JarvisRuntime(
                project_root=tmp,
                llm_provider=MockLLMProvider(canned_response="This should not be used."),
                stt_manager=FakeSTTManager(),
                tts_manager=tts,
            )
            runtime.boot()
            api = LocalJarvisAPI(runtime=runtime)
            api._run_sleep_wake_session({"max_turns": 1, "speak": True, "duration_seconds": 1, "mode": "smart", "silence_seconds": 0.1})
            runtime.spoken_pipeline.wait_until_idle(timeout=3.0)
            runtime.spoken_pipeline.shutdown()

        self.assertTrue(tts.calls)
        spoken = [call[0].lower() for call in tts.calls]
        self.assertTrue({"ready to open notepad.", "opening notepad, sir."} & set(spoken))
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
