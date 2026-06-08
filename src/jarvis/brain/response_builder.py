"""Response builder placeholder.

Later this will shape agent/tool results into Jarvis's natural speaking style.
"""

from __future__ import annotations

from jarvis.core.result import JarvisResult


class ResponseBuilder:
    def build(self, result: JarvisResult) -> str:
        return result.message
