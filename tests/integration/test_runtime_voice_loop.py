import tempfile
import unittest
from pathlib import Path

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

    def __init__(self, text="Hello Jarvis"):
        self.text = text
        self.calls = []

    def listen_once(self, *, duration_seconds=None, mode=None, silence_seconds=None):
        self.calls.append({"duration_seconds": duration_seconds, "mode": mode, "silence_seconds": silence_seconds})
        return STTResult.ok(
            "fake STT complete",
            provider="fake_stt",
            text=self.text,
            audio_path=Path("data/stt/fake.wav"),
            language="en",
            duration_seconds=1.0,
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
        return STTResult.ok("fake file STT", provider="fake_stt", text=self.text, audio_path=Path(path))

    def format_debug_last(self):
        return "fake STT debug"


class FakeTTSManager:
    def __init__(self):
        self.enabled = True
        self.auto_speak = False
        self.playback = True
        self.provider_name = "fake_tts"
        self.calls = []

    def say(self, text, *, play_audio=None):
        self.calls.append((text, play_audio))
        return TTSResult.ok("fake TTS generated", provider="fake_tts", played=bool(play_audio), data={"text": text})

    def stop_playback(self):
        return True

    def status(self):
        return "fake TTS status"


class TestRuntimeVoiceLoop(unittest.TestCase):
    def test_voice_loop_once_transcribes_routes_and_speaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            stt = FakeSTTManager(text="What is your status?")
            tts = FakeTTSManager()
            llm = MockLLMProvider(canned_response="Online, sir.")
            runtime = JarvisRuntime(project_root=tmp, llm_provider=llm, stt_manager=stt, tts_manager=tts)
            runtime.boot()
            printed = []
            heard = []

            result = runtime.voice_loop_once(
                mode="smart",
                silence_seconds=0.7,
                stream_callback=printed.append,
                transcript_callback=heard.append,
                speak=True,
            )
            self.assertTrue(result.success)
            self.assertEqual(result.action, "voice_loop_once")
            self.assertEqual(result.data["transcript"], "What is your status?")
            self.assertEqual(heard, ["What is your status?"])
            self.assertEqual("".join(printed), "Online, sir.")
            self.assertTrue(runtime.spoken_pipeline.wait_until_idle(timeout=3.0))
            self.assertEqual([call[0] for call in tts.calls], ["Online, sir."])
            self.assertEqual(stt.calls[0]["silence_seconds"], 0.7)
            runtime.spoken_pipeline.shutdown()

    def test_voice_loop_rejects_empty_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = JarvisRuntime(
                project_root=tmp,
                llm_provider=MockLLMProvider(canned_response="Should not run"),
                stt_manager=FakeSTTManager(text=""),
                tts_manager=FakeTTSManager(),
            )
            runtime.boot()
            result = runtime.voice_loop_once()
            self.assertFalse(result.success)
            self.assertIn("did not catch", result.message)

    def test_voice_loop_status_mentions_wake_word_not_implemented(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = JarvisRuntime(
                project_root=tmp,
                llm_provider=MockLLMProvider(canned_response="Online"),
                stt_manager=FakeSTTManager(),
                tts_manager=FakeTTSManager(),
            )
            status = runtime.voice_loop_status()
            self.assertIn("one-turn", status)
            self.assertIn("wake word: not implemented yet", status)


if __name__ == "__main__":
    unittest.main()
