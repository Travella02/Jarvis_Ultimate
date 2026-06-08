import tempfile
import unittest
from pathlib import Path

from jarvis.core.lifecycle import JarvisRuntime


class TestRuntimeSTTFlow(unittest.TestCase):
    def test_runtime_stt_status_and_mock_transcribe_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config" / "providers.yaml").write_text(
                "\n".join(
                    [
                        "providers:",
                        "  llm:",
                        "    default: mock",
                        "  tts:",
                        "    default: mock",
                        "  stt:",
                        "    default: mock",
                        "    mock_text: hello from mic",
                    ]
                ),
                encoding="utf-8",
            )
            audio = root / "sample.wav"
            audio.write_bytes(b"fake wav")
            runtime = JarvisRuntime(project_root=root)
            runtime.boot()
            status = runtime.stt_status()
            self.assertIn("STT/microphone status", status)
            self.assertIn("mock", status)
            output = runtime.stt_transcribe_file(str(audio))
            self.assertIn("Heard: hello from mic", output)
            self.assertIn("Provider: mock", output)
            debug = runtime.stt_debug_last()
            self.assertIn("final success: True", debug)


if __name__ == "__main__":
    unittest.main()
