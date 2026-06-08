from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest

from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider


class TestRuntimeStreamingFlow(unittest.TestCase):
    def test_runtime_passes_stream_callback_to_conversation_agent(self):
        chunks = []
        runtime = JarvisRuntime(llm_provider=MockLLMProvider(canned_response="streamed mock response"))
        runtime.boot()
        result = runtime.handle_command("Talk to me with streaming", stream_callback=chunks.append)

        self.assertTrue(result.success)
        self.assertEqual("".join(chunks), "streamed mock response")
        self.assertTrue(result.data["streamed_output"])
        self.assertTrue(runtime.last_timing.has_mark("mock_llm.first_chunk"))


if __name__ == "__main__":
    unittest.main()
