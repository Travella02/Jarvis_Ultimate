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


class TestEnvFileConfig(unittest.TestCase):
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

    def test_reads_short_lm_model_alias_from_project_env_file(self):
        root = self._make_root(
            "JARVIS_LM_PROVIDER=lm_studio\n"
            "JARVIS_LM_MODEL=google/gemma-4-12b-qat\n"
            "JARVIS_LM_TIMEOUT_SECONDS=75\n"
            "JARVIS_LM_TEMPERATURE=0.4\n"
            "JARVIS_LM_MAX_TOKENS=256\n"
        )

        with patch.dict(os.environ, {}, clear=True):
            config = JarvisConfig.from_project_root(root)

        self.assertEqual(config.llm_provider, "lm_studio")
        self.assertEqual(config.llm_model, "google/gemma-4-12b-qat")
        self.assertEqual(config.llm_timeout_seconds, 75.0)
        self.assertEqual(config.llm_temperature, 0.4)
        self.assertEqual(config.llm_max_tokens, 256)

    def test_reads_canonical_llm_values_from_project_env_file(self):
        root = self._make_root(
            "JARVIS_LLM_MODEL='configured-model'\n"
            "JARVIS_LLM_STREAMING=false\n"
            "JARVIS_LLM_RESOLVE_AUTO_MODEL=true\n"
        )

        with patch.dict(os.environ, {}, clear=True):
            config = JarvisConfig.from_project_root(root)

        self.assertEqual(config.llm_model, "configured-model")
        self.assertFalse(config.llm_streaming)
        self.assertTrue(config.llm_resolve_auto_model)

    def test_os_environment_overrides_project_env_file(self):
        root = self._make_root("JARVIS_LM_MODEL=dotenv-model\n")

        with patch.dict(os.environ, {"JARVIS_LLM_MODEL": "os-model"}, clear=True):
            config = JarvisConfig.from_project_root(root)

        self.assertEqual(config.llm_model, "os-model")


if __name__ == "__main__":
    unittest.main()
