"""Safe system status helpers."""

from __future__ import annotations

import platform
import sys
from typing import Any


def basic_system_status() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "python": sys.version.split()[0],
    }
