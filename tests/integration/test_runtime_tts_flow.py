from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.clients.cli.cli_client import _parse_tts_reference_command, _parse_tts_say_command
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider


class TestRuntimeTTSFlow(unittest.TestCase):
    def test_runtime_tts_status_and_mock_say(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "config").mkdir()
            (root / "config" / "providers.yaml").write_text(
                "providers:\n  llm:\n    default: mock\n  tts:\n    default: mock\n    enabled: true\n    output_dir: data/tts\n",
                encoding="utf-8",
            )
            runtime = JarvisRuntime(project_root=root, llm_provider=MockLLMProvider(canned_response="Hello."))
            runtime.boot()

            status = runtime.tts_status()
            say_result = runtime.tts_say("hello tts")

            self.assertIn("TTS status", status)
            self.assertIn("preferred provider: mock", status)
            self.assertIn("Provider: mock", say_result)
            self.assertTrue((root / "data" / "tts").exists())

    def test_cli_tts_say_parser_preserves_original_text(self):
        self.assertEqual(_parse_tts_say_command("tts say Hello Tanner"), "Hello Tanner")
        self.assertEqual(_parse_tts_say_command("speak Keep My Case"), "Keep My Case")
        self.assertIsNone(_parse_tts_say_command("tts status"))

    def test_cli_tts_reference_parser_preserves_windows_paths(self):
        parsed = _parse_tts_reference_command(r'tts reference import "C:\\voice refs\\jarvis.wav"')

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["path"], r"C:\\voice refs\\jarvis.wav")
        self.assertTrue(parsed["import_to_default"])

    def test_runtime_playback_and_reference_commands(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "config").mkdir()
            (root / "config" / "providers.yaml").write_text(
                "providers:\n  llm:\n    default: mock\n  tts:\n    default: mock\n    enabled: true\n    output_dir: data/tts\n",
                encoding="utf-8",
            )
            runtime = JarvisRuntime(project_root=root, llm_provider=MockLLMProvider(canned_response="Hello."))
            runtime.boot()

            on_message = runtime.tts_playback_on()
            ref_status = runtime.tts_reference_status()
            no_last = runtime.tts_play_last()

            self.assertIn("playback is on", on_message.lower())
            self.assertIn("XTTS speaker reference status", ref_status)
            self.assertIn("No generated TTS audio", no_last)


if __name__ == "__main__":
    unittest.main()
