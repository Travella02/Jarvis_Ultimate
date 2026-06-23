from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import tempfile
import unittest
from pathlib import Path

from jarvis.core.config import JarvisConfig
from jarvis.providers.llm.factory import create_llm_provider


class TestNativeConfig(unittest.TestCase):
    def test_env_file_reads_native_lm_studio_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text(
                "\n".join(
                    [
                        "JARVIS_LM_API_MODE=native",
                        "JARVIS_LM_NATIVE_BASE_URL=http://localhost:1234",
                        "JARVIS_LM_REASONING=off",
                        "JARVIS_LM_CONTEXT_LENGTH=4096",
                        "JARVIS_LM_STORE_NATIVE_CHATS=false",
                    ]
                ),
                encoding="utf-8",
            )
            config = JarvisConfig.from_project_root(root)

        self.assertEqual(config.llm_api_mode, "native")
        self.assertEqual(config.llm_native_base_url, "http://localhost:1234")
        self.assertEqual(config.llm_reasoning, "off")
        self.assertEqual(config.llm_context_length, 4096)
        self.assertFalse(config.llm_store_native_chats)

    def test_factory_passes_native_settings_to_lm_studio_provider(self):
        config = JarvisConfig(
            llm_provider="lm_studio",
            llm_model="test-model",
            llm_api_mode="native",
            llm_native_base_url="http://localhost:1234",
            llm_reasoning="off",
            llm_context_length=2048,
        )
        provider = create_llm_provider(config)

        self.assertEqual(provider.api_mode, "native")
        self.assertEqual(provider.native_base_url, "http://localhost:1234")
        self.assertEqual(provider.reasoning, "off")
        self.assertEqual(provider.context_length, 2048)


if __name__ == "__main__":
    unittest.main()
