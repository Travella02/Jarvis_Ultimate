import tempfile
import unittest
from pathlib import Path

from jarvis.clients.cli.cli_client import _parse_sleep_wake_command
from jarvis.core.config import JarvisConfig
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
    start_timeout_seconds = 3.0

    def __init__(self, items):
        self.items = list(items)
        self.calls = []

    def listen_once(self, *, duration_seconds=None, mode=None, silence_seconds=None):
        self.calls.append({"duration_seconds": duration_seconds, "mode": mode, "silence_seconds": silence_seconds})
        item = self.items.pop(0) if self.items else ""
        if isinstance(item, tuple):
            text, duration = item
        else:
            text, duration = item, 1.0
        return STTResult.ok("fake STT complete", provider="fake_stt", text=text, audio_path=Path("data/stt/fake.wav"), language="en", duration_seconds=duration)

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


class TestSleepWakeVoiceLoop(unittest.TestCase):
    def test_parse_sleep_wake_command(self):
        self.assertEqual(
            _parse_sleep_wake_command("always listening start max 10 timeout 45 silence 0.6"),
            {"max_turns": 10, "active_timeout_seconds": 45.0, "mode": None, "duration_seconds": None, "silence_seconds": 0.6},
        )

    def test_config_reads_sleep_wake_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text(
                "JARVIS_WAKE_WORDS=hey jarvis,jarvis,yo jarvis\n"
                "JARVIS_VOICE_SLEEP_TIMEOUT_SECONDS=30\n"
                "JARVIS_VOICE_SLEEP_PHRASES=that is all jarvis,go to sleep\n"
                "JARVIS_VOICE_EXIT_PHRASES=exit voice mode\n",
                encoding="utf-8",
            )
            config = JarvisConfig.from_project_root(root)
            self.assertEqual(config.wake_words, "hey jarvis,jarvis,yo jarvis")
            self.assertEqual(config.voice_sleep_timeout_seconds, 30.0)
            self.assertIn("go to sleep", config.voice_sleep_phrases)
            self.assertEqual(config.voice_exit_phrases, "exit voice mode")


    def test_sleep_phrase_tolerates_misheard_jarvis_name(self):
        phrases = ["that s all jarvis", "thats all jarvis", "go to sleep"]
        self.assertTrue(JarvisRuntime._voice_loop_sleep_phrase_matches("That's all Dervis.", phrases))
        self.assertTrue(JarvisRuntime._voice_loop_sleep_phrase_matches("That is all service", phrases))
        self.assertTrue(JarvisRuntime._voice_loop_sleep_phrase_matches("Thank you Jervis", phrases))
        self.assertTrue(JarvisRuntime._voice_loop_sleep_phrase_matches("go back to sleep", phrases))
        self.assertFalse(JarvisRuntime._voice_loop_sleep_phrase_matches("thanks for that", phrases))

    def test_sleep_wake_loop_wakes_then_accepts_followup_without_wake_then_sleeps(self):
        with tempfile.TemporaryDirectory() as tmp:
            stt = SequenceSTTManager([
                "random room speech",
                "Hey Jarvis, give me one sentence",
                "what did I just ask you",
                "that's all Jarvis",
                "more room speech without wake",
                "exit voice mode",
            ])
            tts = FakeTTSManager()
            runtime = JarvisRuntime(project_root=tmp, llm_provider=MockLLMProvider(canned_response="Online, sir."), stt_manager=stt, tts_manager=tts)
            runtime.boot()
            heard = []
            status = []
            printed = []
            result = runtime.voice_sleep_wake_loop(
                max_turns=6,
                active_timeout_seconds=30,
                transcript_callback=heard.append,
                status_callback=status.append,
                stream_callback=printed.append,
                speak=True,
            )
            self.assertTrue(result.success)
            self.assertEqual(result.action, "voice_sleep_wake_loop")
            self.assertEqual(result.data["wake_activations"], 1)
            self.assertEqual(result.data["turns_handled"], 2)
            self.assertEqual(result.data["sleep_transitions"], 1)
            self.assertEqual(result.data["final_state"], "asleep")
            self.assertEqual(result.data["stopped_by"], "spoken_exit_phrase")
            self.assertIn("Wake phrase not detected; staying asleep.", status)
            self.assertIn("Sleep phrase detected; returning to sleep mode.", status)
            self.assertIn("Online, sir.", "".join(printed))
            runtime.spoken_pipeline.shutdown()


    def test_sleep_wake_loop_sleeps_when_jarvis_name_is_misheard(self):
        with tempfile.TemporaryDirectory() as tmp:
            stt = SequenceSTTManager([
                "Hey Jarvis, give me one sentence",
                "That's all Dervis",
                "exit voice mode",
            ])
            runtime = JarvisRuntime(project_root=tmp, llm_provider=MockLLMProvider(canned_response="Online, sir."), stt_manager=stt, tts_manager=FakeTTSManager())
            runtime.boot()
            status = []
            result = runtime.voice_sleep_wake_loop(max_turns=3, active_timeout_seconds=30, status_callback=status.append, speak=False)
            self.assertTrue(result.success)
            self.assertEqual(result.data["wake_activations"], 1)
            self.assertEqual(result.data["sleep_transitions"], 1)
            self.assertEqual(result.data["final_state"], "asleep")
            self.assertIn("Sleep phrase detected; returning to sleep mode.", status)
            runtime.spoken_pipeline.shutdown()

    def test_sleep_wake_loop_returns_to_sleep_after_inactivity(self):
        with tempfile.TemporaryDirectory() as tmp:
            stt = SequenceSTTManager([
                "Hey Jarvis",
                ("", 2.0),
                ("", 2.0),
                "exit voice mode",
            ])
            runtime = JarvisRuntime(project_root=tmp, llm_provider=MockLLMProvider(canned_response="Online"), stt_manager=stt, tts_manager=FakeTTSManager())
            runtime.boot()
            status = []
            result = runtime.voice_sleep_wake_loop(max_turns=4, active_timeout_seconds=3.0, status_callback=status.append, speak=False)
            self.assertTrue(result.success)
            self.assertEqual(result.data["sleep_transitions"], 1)
            self.assertEqual(result.data["final_state"], "asleep")
            self.assertTrue(any("returning to sleep mode" in item for item in status))
            runtime.spoken_pipeline.shutdown()


if __name__ == "__main__":
    unittest.main()
