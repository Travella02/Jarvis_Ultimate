from pathlib import Path
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.clients.cli.cli_client import (
    _parse_tts_say_as_command,
    _parse_tts_voice_import_command,
    _parse_tts_voice_test_command,
    _parse_tts_voice_use_command,
)
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider


def write_test_wav(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 16000)


class TestRuntimeTTSVoiceProfiles(unittest.TestCase):
    def test_cli_voice_profile_parsers(self):
        parsed = _parse_tts_voice_import_command(r'tts voice import jarvis "C:\\voices\\jarvis.wav"')
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["voice_name"], "jarvis")
        self.assertEqual(parsed["path"], r"C:\\voices\\jarvis.wav")
        self.assertEqual(_parse_tts_voice_use_command("tts voice use mom"), "mom")
        test = _parse_tts_voice_test_command("tts voice test jarvis play")
        self.assertEqual(test["voice_name"], "jarvis")
        self.assertTrue(test["play_audio"])
        say_as = _parse_tts_say_as_command("tts say as jarvis Hello sir")
        self.assertEqual(say_as["voice_name"], "jarvis")
        self.assertEqual(say_as["text"], "Hello sir")

    def test_runtime_imports_voice_profile(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "config").mkdir()
            (root / "config" / "providers.yaml").write_text(
                "providers:\n  llm:\n    default: mock\n  tts:\n    default: mock\n    enabled: true\n    output_dir: data/tts\n    voice_profiles_dir: data/tts/voices\n",
                encoding="utf-8",
            )
            source = root / "jarvis.wav"
            write_test_wav(source)
            runtime = JarvisRuntime(project_root=root, llm_provider=MockLLMProvider(canned_response="Hello."))
            runtime.boot()

            imported = runtime.tts_voice_import("jarvis", str(source))
            listed = runtime.tts_voice_list()
            current = runtime.tts_voice_current()

            self.assertIn("Imported XTTS voice profile", imported)
            self.assertIn("jarvis", listed)
            self.assertIn("current xtts voice", current.lower())
            self.assertTrue((root / "data" / "tts" / "voices" / "jarvis" / "reference.wav").exists())


if __name__ == "__main__":
    unittest.main()
