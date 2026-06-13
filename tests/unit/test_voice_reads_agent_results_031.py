from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider
from jarvis.providers.stt.base import STTResult
from jarvis.providers.tts.base import TTSResult


class FakeSTTManager:
    enabled = True
    provider_name = "fake_stt"
    listen_mode = "smart"
    silence_seconds = 0.8
    record_seconds = 2.0
    start_timeout_seconds = 3.0

    def __init__(self, text: str) -> None:
        self.text = text

    def listen_once(self, *, duration_seconds=None, mode=None, silence_seconds=None):
        return STTResult.ok("fake STT complete", provider="fake_stt", text=self.text, audio_path=Path("fake.wav"), language="en", duration_seconds=1.0)

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


class TestVoiceReadsAgentResults031(unittest.TestCase):
    def test_voice_loop_speaks_non_llm_agent_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {"JARVIS_APP_AGENT_DRY_RUN": "1"}), patch("jarvis.tools.shared.process_tools.subprocess.Popen") as popen:
            tts = FakeTTSManager()
            runtime = JarvisRuntime(
                project_root=tmp,
                llm_provider=MockLLMProvider(canned_response="This should not be used."),
                stt_manager=FakeSTTManager("open notepad"),
                tts_manager=tts,
            )
            runtime.boot()
            result = runtime.voice_loop_once(speak=True)
            runtime.spoken_pipeline.wait_until_idle(timeout=3.0)
            runtime.spoken_pipeline.shutdown()

        self.assertTrue(result.success)
        self.assertEqual(result.data["selected_agent"], "app_agent")
        self.assertTrue(tts.calls)
        self.assertIn(tts.calls[-1][0].lower(), {"ready to open notepad.", "opening notepad, sir."})
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
