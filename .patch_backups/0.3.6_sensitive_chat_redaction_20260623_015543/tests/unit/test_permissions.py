from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest
from jarvis.core.permissions import PermissionManager


class TestPermissions(unittest.TestCase):
    def test_permission_defaults(self):
        manager = PermissionManager({"screenshot": "allow"})
        self.assertTrue(manager.is_allowed_without_confirmation("screenshot"))
        self.assertFalse(manager.is_allowed_without_confirmation("file_delete"))


if __name__ == "__main__":
    unittest.main()
