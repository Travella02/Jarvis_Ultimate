from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest
from jarvis.core.lifecycle import JarvisRuntime


class TestBasicJarvisFlow(unittest.TestCase):
    def test_boot_and_status(self):
        runtime = JarvisRuntime()
        boot = runtime.boot()
        self.assertTrue(boot.success)
        result = runtime.handle_command("status")
        self.assertTrue(result.success)
        self.assertIn("online", result.message.lower())


if __name__ == "__main__":
    unittest.main()
