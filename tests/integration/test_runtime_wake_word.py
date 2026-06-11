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

    def __init__(self, text="Hey Jarvis, what is your status?"):
        self.text = text
        self.calls = []

    def listen_once(self, *, duration_seconds=None, mode=None, silence_seconds=None):
        self.calls.append({"duration_seconds": duration_seconds, "mode": mode, "silence_seconds": silence_seconds})
        return STTResult.ok("fake STT complete", provider="fake_stt", text=self.text, audio_path=Path("data/stt/fake.wav"), language="en", duration_seconds=1.0)

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


class TestRuntimeWakeWord(unittest.TestCase):
    def test_runtime_wake_test_reports_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = JarvisRuntime(project_root=tmp, llm_provider=MockLLMProvider(canned_response="Online, sir."), stt_manager=FakeSTTManager(), tts_manager=FakeTTSManager())
            output = runtime.wake_test("Hey Jarvis, status")
            self.assertIn("Detected: True", output)
            self.assertIn("Command after wake word: status", output)

    def test_wake_voice_once_routes_command_after_wake_word(self):
        with tempfile.TemporaryDirectory() as tmp:
            stt = FakeSTTManager(text="Hey Jarvis, what is your status?")
            tts = FakeTTSManager()
            runtime = JarvisRuntime(project_root=tmp, llm_provider=MockLLMProvider(canned_response="Online, sir."), stt_manager=stt, tts_manager=tts)
            runtime.boot()
            printed = []
            heard = []
            result = runtime.wake_voice_once(stream_callback=printed.append, transcript_callback=heard.append, speak=True)
            self.assertTrue(result.success)
            self.assertEqual(result.action, "wake_voice_once")
            self.assertEqual(result.data["wake_word"], "hey jarvis")
            self.assertEqual(result.data["wake_command"], "what is your status")
            self.assertEqual(heard, ["Hey Jarvis, what is your status?"])
            self.assertEqual("".join(printed), "Online, sir.")
            self.assertTrue(runtime.spoken_pipeline.wait_until_idle(timeout=3.0))
            self.assertEqual([call[0] for call in tts.calls], ["Online, sir."])
            runtime.spoken_pipeline.shutdown()

    def test_wake_voice_once_rejects_missing_wake_word(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = JarvisRuntime(project_root=tmp, llm_provider=MockLLMProvider(canned_response="Should not run"), stt_manager=FakeSTTManager(text="What is your status?"), tts_manager=FakeTTSManager())
            runtime.boot()
            result = runtime.wake_voice_once()
            self.assertFalse(result.success)
            self.assertIn("Wake word was not detected", result.message)

    def test_wake_voice_once_empty_wake_says_yes_sir(self):
        with tempfile.TemporaryDirectory() as tmp:
            tts = FakeTTSManager()
            runtime = JarvisRuntime(project_root=tmp, llm_provider=MockLLMProvider(canned_response="Should not run"), stt_manager=FakeSTTManager(text="Hey Jarvis"), tts_manager=tts)
            runtime.boot()
            result = runtime.wake_voice_once(speak=True)
            self.assertTrue(result.success)
            self.assertEqual(result.message, "Yes, sir?")
            self.assertEqual(tts.calls[0][0], "Yes, sir?")


if __name__ == "__main__":
    unittest.main()
