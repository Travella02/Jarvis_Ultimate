from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider


class TestRuntimeSpokenResponsePipeline(unittest.TestCase):
    def _runtime(self, root: Path) -> JarvisRuntime:
        (root / "config").mkdir()
        (root / "config" / "providers.yaml").write_text(
            "providers:\n"
            "  llm:\n"
            "    default: mock\n"
            "  tts:\n"
            "    default: mock\n"
            "    enabled: true\n"
            "    playback: false\n"
            "    auto_speak: false\n"
            "    output_dir: data/tts\n"
            "    auto_speak_chunk_chars: 120\n"
            "    queue_max_size: 4\n",
            encoding="utf-8",
        )
        runtime = JarvisRuntime(project_root=root, llm_provider=MockLLMProvider(canned_response="Hello sir. I am ready."))
        runtime.boot()
        return runtime

    def test_voice_on_off_and_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = self._runtime(Path(temp_dir))

            enabled = runtime.voice_on()
            status = runtime.voice_status()
            disabled = runtime.voice_off()

            self.assertIn("auto-speak", enabled)
            self.assertIn("Spoken response pipeline status", status)
            self.assertIn("Voice auto-speak", disabled)

    def test_runtime_spoken_stream_enqueues_chat_response(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = self._runtime(Path(temp_dir))
            runtime.voice_on()
            printed = []
            spoken_stream = runtime.create_spoken_stream(printed.append)

            result = runtime.handle_command("hello", stream_callback=spoken_stream)
            spoken_stream.finish(speak_remaining=result.success and result.action == "llm_chat")
            self.assertTrue(runtime.spoken_pipeline.wait_until_idle(timeout=3.0))
            queue_status = runtime.tts_queue_status()
            runtime.spoken_pipeline.shutdown()

            self.assertTrue(result.success)
            self.assertIn("Hello sir", "".join(printed))
            self.assertIn("completed", queue_status)
            self.assertGreaterEqual(runtime.spoken_pipeline.stats.completed, 1)

    def test_tts_stop_reports_cleared_chunks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = self._runtime(Path(temp_dir))
            runtime.voice_on()
            message = runtime.tts_stop()
            runtime.spoken_pipeline.shutdown()

            self.assertIn("Stopped spoken response output", message)


if __name__ == "__main__":
    unittest.main()
