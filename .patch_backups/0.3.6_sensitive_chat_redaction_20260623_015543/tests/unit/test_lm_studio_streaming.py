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


class TestLMStudioStreaming(unittest.TestCase):
    def test_streaming_chat_sends_stream_payload_and_collects_chunks(self):
        captured = {}
        streamed_chunks = []
        lines = [
            'data: {"choices":[{"delta":{"role":"assistant"},"finish_reason":null}]}\n',
            'data: {"choices":[{"delta":{"content":"Hel"},"finish_reason":null}]}\n',
            'data: {"choices":[{"delta":{"content":"lo"},"finish_reason":null}]}\n',
            'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n',
            'data: [DONE]\n',
        ]

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeStreamResponse(lines)

        timer = TurnTimer(command="hello")
        provider = LMStudioProvider(base_url="http://localhost:1234/v1", model="test-model", urlopen=fake_urlopen)
        response = provider.chat(
            [{"role": "user", "content": "hello"}],
            timing=timer,
            stream_callback=streamed_chunks.append,
        )

        self.assertTrue(response.success)
        self.assertEqual(response.content, "Hello")
        self.assertEqual(streamed_chunks, ["Hel", "lo"])
        self.assertEqual(captured["url"], "http://localhost:1234/v1/chat/completions")
        self.assertTrue(captured["body"]["stream"])
        self.assertTrue(response.raw["streamed"])
        self.assertEqual(response.raw["chunk_count"], 2)
        self.assertTrue(timer.has_mark("lm_studio.first_chunk"))
        self.assertTrue(timer.has_mark("lm_studio.request_finished"))

    def test_streaming_can_be_disabled_per_call_even_with_callback(self):
        captured = {}

        class FakeJSONResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": "full response"}}]}).encode("utf-8")

        def fake_urlopen(request, timeout):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeJSONResponse()

        chunks = []
        provider = LMStudioProvider(base_url="http://localhost:1234/v1", model="test-model", urlopen=fake_urlopen)
        response = provider.chat([{"role": "user", "content": "hello"}], stream_callback=chunks.append, stream=False)

        self.assertTrue(response.success)
        self.assertEqual(response.content, "full response")
        self.assertNotIn("stream", captured["body"])
        self.assertEqual(chunks, [])


if __name__ == "__main__":
    unittest.main()
