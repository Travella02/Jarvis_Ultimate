import tempfile
import unittest
from pathlib import Path

from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider
from jarvis.providers.stt.base import STTResult
from jarvis.providers.tts.base import TTSResult


class SequenceSTTManager:
    enabled = True
    provider_name = "fake_stt"
    listen_mode = "smart"
    silence_seconds = 0.65
    record_seconds = 2.0
    max_audio_files = 30

    def __init__(self, texts):
        self.texts = list(texts)
        self.calls = []

    def listen_once(self, *, duration_seconds=None, mode=None, silence_seconds=None):
        self.calls.append({"duration_seconds": duration_seconds, "mode": mode, "silence_seconds": silence_seconds})
        text = self.texts.pop(0) if self.texts else "stop listening"
        return STTResult.ok("fake STT complete", provider="fake_stt", text=text, audio_path=Path("data/stt/fake.wav"), language="en", duration_seconds=1.0)

    def status(self):
        return "fake STT status"

    def warmup(self):
        return STTResult.ok("fake warmup", provider="fake_stt", text="")


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


class TestRuntimeContinuousVoiceLoop(unittest.TestCase):
    def test_continuous_wake_loop_routes_wake_commands_until_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            stt = SequenceSTTManager([
                "background noise without wake",
                "Hey Jarvis, what is your status?",
                "Hey Jarvis stop listening",
            ])
            tts = FakeTTSManager()
            runtime = JarvisRuntime(project_root=tmp, llm_provider=MockLLMProvider(canned_response="Online, sir."), stt_manager=stt, tts_manager=tts)
            runtime.boot()
            heard = []
            status = []
            printed = []
            result = runtime.voice_loop_continuous(
                max_turns=5,
                require_wake_word=True,
                silence_seconds=0.55,
                transcript_callback=heard.append,
                status_callback=status.append,
                stream_callback=printed.append,
                speak=True,
            )
            self.assertTrue(result.success)
            self.assertEqual(result.action, "voice_loop_continuous")
            self.assertEqual(result.data["turns_heard"], 3)
            self.assertEqual(result.data["turns_handled"], 1)
            self.assertEqual(result.data["turns_ignored"], 1)
            self.assertEqual(result.data["stopped_by"], "spoken_stop_phrase")
            self.assertIn("Online, sir.", "".join(printed))
            self.assertEqual([call[0] for call in tts.calls], ["Online, sir."])
            self.assertEqual(stt.calls[0]["silence_seconds"], 0.55)
            self.assertIn("Wake word not detected; continuing.", status)
            runtime.spoken_pipeline.shutdown()

    def test_continuous_conversation_can_run_without_wake_word(self):
        with tempfile.TemporaryDirectory() as tmp:
            stt = SequenceSTTManager(["what is your status", "stop listening"])
            runtime = JarvisRuntime(project_root=tmp, llm_provider=MockLLMProvider(canned_response="Online, sir."), stt_manager=stt, tts_manager=FakeTTSManager())
            runtime.boot()
            result = runtime.voice_loop_continuous(max_turns=3, require_wake_word=False, speak=False)
            self.assertTrue(result.success)
            self.assertEqual(result.data["turns_handled"], 1)
            self.assertEqual(result.data["stopped_by"], "spoken_stop_phrase")
            self.assertEqual(result.data["last_command"], "what is your status")
            runtime.spoken_pipeline.shutdown()

    def test_continuous_status_mentions_stop_phrases(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = JarvisRuntime(project_root=tmp, llm_provider=MockLLMProvider(canned_response="Online"), stt_manager=SequenceSTTManager([]), tts_manager=FakeTTSManager())
            status = runtime.continuous_voice_loop_status()
            self.assertIn("Continuous hands-free loop status", status)
            self.assertIn("stop phrases", status)


if __name__ == "__main__":
    unittest.main()
