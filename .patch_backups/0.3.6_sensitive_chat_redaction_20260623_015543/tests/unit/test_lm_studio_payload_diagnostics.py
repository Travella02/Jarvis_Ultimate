from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import json
import unittest

from jarvis.core.timing import TurnTimer
from jarvis.providers.llm.lm_studio_provider import LMStudioProvider


class FakeStreamResponse:
    def __init__(self, lines):
        self.lines = lines

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def __iter__(self):
        for line in self.lines:
            yield line.encode("utf-8")


class TestLMStudioPayloadDiagnostics(unittest.TestCase):
    def test_prepare_mark_includes_prompt_and_payload_sizes(self):
        captured = {}
        lines = [
            'data: {"choices":[{"delta":{"content":"OK"},"finish_reason":null}]}\n',
            'data: [DONE]\n',
        ]

        def fake_urlopen(request, timeout):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeStreamResponse(lines)

        timer = TurnTimer(command="hello")
        provider = LMStudioProvider(base_url="http://localhost:1234/v1", model="test-model", urlopen=fake_urlopen)
        response = provider.chat(
            [{"role": "user", "content": "hello"}],
            system_prompt="abc",
            max_tokens=12,
            timing=timer,
            stream_callback=lambda chunk: None,
        )

        self.assertTrue(response.success)
        prepare = timer.get_mark("lm_studio.prepare_finished")
        request_start = timer.get_mark("lm_studio.request_start")
        self.assertIsNotNone(prepare)
        self.assertIsNotNone(request_start)
        self.assertEqual(prepare.data["system_chars"], 3)
        self.assertEqual(prepare.data["user_chars"], 5)
        self.assertEqual(prepare.data["prompt_chars"], 8)
        self.assertEqual(prepare.data["max_tokens"], 12)
        self.assertGreater(prepare.data["payload_bytes"], 0)
        self.assertEqual(request_start.data["payload_bytes"], len(json.dumps(captured["body"]).encode("utf-8")))
        self.assertIn("LM Studio prompt payload", "\n".join(timer.summary_lines()))


if __name__ == "__main__":
    unittest.main()
