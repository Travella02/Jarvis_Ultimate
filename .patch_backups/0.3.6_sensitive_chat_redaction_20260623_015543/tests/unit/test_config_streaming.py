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


class TestConfigStreaming(unittest.TestCase):
    def test_reads_llm_streaming_setting_from_provider_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_dir = root / "config"
            config_dir.mkdir()
            (config_dir / "providers.yaml").write_text(
                "providers:\n  llm:\n    default: lm_studio\n    streaming: false\n",
                encoding="utf-8",
            )
            config = JarvisConfig.from_project_root(root)

        self.assertFalse(config.llm_streaming)


if __name__ == "__main__":
    unittest.main()
