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


class TestRuntimeKokoroVoiceFlow(unittest.TestCase):
    def test_runtime_lists_and_switches_kokoro_voices(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "config").mkdir()
            (root / "config" / "providers.yaml").write_text(
                "providers:\n  llm:\n    default: mock\n  tts:\n    default: kokoro\n    enabled: true\n    fallback_providers: mock\n    output_dir: data/tts\n    kokoro_voice: af_heart\n",
                encoding="utf-8",
            )
            runtime = JarvisRuntime(project_root=root, llm_provider=MockLLMProvider(canned_response="Hello."))
            runtime.boot()

            listed = runtime.tts_voice_list()
            changed = runtime.tts_voice_use("af_bella")
            current = runtime.tts_voice_current()

            self.assertIn("Kokoro voice options", listed)
            self.assertIn("Kokoro voice set to 'af_bella'", changed)
            self.assertIn("af_bella", current)


if __name__ == "__main__":
    unittest.main()
