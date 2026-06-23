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
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.factory import create_llm_provider
from jarvis.providers.llm.lm_studio_provider import LMStudioProvider


class TestLoopbackSpeedCleanup(unittest.TestCase):
    def _make_root(self, env_text: str = "", providers_text: str | None = None) -> Path:
        root = Path(tempfile.mkdtemp())
        config_dir = root / "config"
        config_dir.mkdir()
        if providers_text is not None:
            (config_dir / "providers.yaml").write_text(providers_text, encoding="utf-8")
        if env_text:
            (root / ".env").write_text(env_text, encoding="utf-8")
        return root

    def test_default_lm_studio_urls_use_direct_loopback(self):
        root = self._make_root()

        with patch.dict(os.environ, {}, clear=True):
            config = JarvisConfig.from_project_root(root)

        self.assertEqual(config.llm_base_url, "http://127.0.0.1:1234/v1")
        self.assertEqual(config.llm_native_base_url, "http://127.0.0.1:1234")

    def test_reads_lm_studio_native_base_url_alias_from_env_file(self):
        root = self._make_root("JARVIS_LM_STUDIO_NATIVE_BASE_URL=http://127.0.0.1:1234\n")

        with patch.dict(os.environ, {}, clear=True):
            config = JarvisConfig.from_project_root(root)
            provider = create_llm_provider(config)

        self.assertEqual(config.llm_native_base_url, "http://127.0.0.1:1234")
        self.assertEqual(provider.native_base_url, "http://127.0.0.1:1234")

    def test_reads_canonical_lm_studio_native_base_url_alias_from_env_file(self):
        root = self._make_root("JARVIS_LLM_STUDIO_NATIVE_BASE_URL=http://127.0.0.1:1234\n")

        with patch.dict(os.environ, {}, clear=True):
            config = JarvisConfig.from_project_root(root)

        self.assertEqual(config.llm_native_base_url, "http://127.0.0.1:1234")

    def test_provider_derives_native_loopback_url_from_openai_loopback_url(self):
        provider = LMStudioProvider(base_url="http://127.0.0.1:1234/v1", model="test-model")

        self.assertEqual(provider.native_base_url, "http://127.0.0.1:1234")

    def test_prompt_diagnostics_warns_when_localhost_is_configured(self):
        root = self._make_root(
            "JARVIS_LM_STUDIO_BASE_URL=http://localhost:1234/v1\n"
            "JARVIS_LM_STUDIO_NATIVE_BASE_URL=http://localhost:1234\n"
        )

        with patch.dict(os.environ, {}, clear=True):
            runtime = JarvisRuntime(project_root=root)
            diagnostics = runtime.prompt_diagnostics()

        self.assertIn("base URL: http://localhost:1234/v1", diagnostics)
        self.assertIn("native base URL: http://localhost:1234", diagnostics)
        self.assertIn("warning: base URL uses localhost", diagnostics)
        self.assertIn("warning: native base URL uses localhost", diagnostics)

    def test_prompt_diagnostics_has_no_localhost_warning_with_loopback_urls(self):
        root = self._make_root(
            "JARVIS_LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1\n"
            "JARVIS_LM_STUDIO_NATIVE_BASE_URL=http://127.0.0.1:1234\n"
        )

        with patch.dict(os.environ, {}, clear=True):
            runtime = JarvisRuntime(project_root=root)
            diagnostics = runtime.prompt_diagnostics()

        self.assertIn("base URL: http://127.0.0.1:1234/v1", diagnostics)
        self.assertIn("native base URL: http://127.0.0.1:1234", diagnostics)
        self.assertNotIn("warning:", diagnostics)


if __name__ == "__main__":
    unittest.main()
