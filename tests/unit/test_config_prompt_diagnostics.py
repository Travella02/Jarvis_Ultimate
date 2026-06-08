from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.core.config import JarvisConfig


class TestConfigPromptDiagnostics(unittest.TestCase):
    def _make_root(self, env_text: str, providers_text: str | None = None) -> Path:
        root = Path(tempfile.mkdtemp())
        config_dir = root / "config"
        config_dir.mkdir()
        (config_dir / "providers.yaml").write_text(
            providers_text or "providers:\n  llm:\n    default: lm_studio\n    model: auto\n",
            encoding="utf-8",
        )
        (root / ".env").write_text(env_text, encoding="utf-8")
        return root

    def test_reads_prompt_mode_and_benchmark_settings_from_env_file(self):
        root = self._make_root(
            "JARVIS_CONVERSATION_PROMPT_MODE=fast\n"
            "JARVIS_LLM_BENCHMARK_MAX_TOKENS=24\n"
            "JARVIS_LLM_BENCHMARK_PROMPT=Say ready.\n"
        )

        with patch.dict(os.environ, {}, clear=True):
            config = JarvisConfig.from_project_root(root)

        self.assertEqual(config.conversation_prompt_mode, "minimal")
        self.assertEqual(config.llm_benchmark_max_tokens, 24)
        self.assertEqual(config.llm_benchmark_prompt, "Say ready.")

    def test_reads_prompt_mode_from_providers_yaml(self):
        root = self._make_root(
            "",
            providers_text=(
                "providers:\n"
                "  llm:\n"
                "    default: lm_studio\n"
                "    conversation_prompt_mode: off\n"
                "    benchmark_max_tokens: 16\n"
            ),
        )

        with patch.dict(os.environ, {}, clear=True):
            config = JarvisConfig.from_project_root(root)

        self.assertEqual(config.conversation_prompt_mode, "off")
        self.assertEqual(config.llm_benchmark_max_tokens, 16)


if __name__ == "__main__":
    unittest.main()
