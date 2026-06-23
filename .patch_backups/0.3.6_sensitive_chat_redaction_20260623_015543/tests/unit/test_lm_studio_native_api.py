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


class FakeResponse:
    def __init__(self, *, lines=None, body=None):
        self.lines = lines or []
        self.body = body or b""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def __iter__(self):
        for line in self.lines:
            yield line.encode("utf-8")

    def read(self):
        return self.body


class TestLMStudioNativeAPI(unittest.TestCase):
    def test_native_streaming_sends_reasoning_off_to_api_v1_chat(self):
        captured = {}
        lines = [
            "event: chat.start\n",
            'data: {"type":"chat.start","model_instance_id":"test-model"}\n',
            "\n",
            "event: prompt_processing.start\n",
            'data: {"type":"prompt_processing.start"}\n',
            "\n",
            "event: message.delta\n",
            'data: {"type":"message.delta","content":"Hi"}\n',
            "\n",
            "event: chat.end\n",
            'data: {"type":"chat.end","result":{"output":[{"type":"message","content":"Hi"}],"stats":{"input_tokens":5,"total_output_tokens":1,"reasoning_output_tokens":0,"tokens_per_second":50.0,"time_to_first_token_seconds":0.05}}}\n',
            "\n",
        ]

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse(lines=lines)

        chunks = []
        timer = TurnTimer(command="native test")
        provider = LMStudioProvider(
            base_url="http://localhost:1234/v1",
            model="test-model",
            api_mode="native",
            reasoning="off",
            context_length=4096,
            urlopen=fake_urlopen,
        )
        response = provider.chat(
            [{"role": "user", "content": "hello"}],
            system_prompt="Be quick.",
            max_tokens=8,
            timing=timer,
            stream_callback=chunks.append,
        )

        self.assertTrue(response.success)
        self.assertEqual(response.content, "Hi")
        self.assertEqual(chunks, ["Hi"])
        self.assertEqual(captured["url"], "http://localhost:1234/api/v1/chat")
        self.assertEqual(captured["body"]["input"], "hello")
        self.assertEqual(captured["body"]["system_prompt"], "Be quick.")
        self.assertEqual(captured["body"]["max_output_tokens"], 8)
        self.assertEqual(captured["body"]["reasoning"], "off")
        self.assertEqual(captured["body"]["context_length"], 4096)
        self.assertFalse(captured["body"]["store"])
        self.assertTrue(timer.has_mark("lm_studio.first_chunk"))
        self.assertTrue(timer.has_mark("lm_studio.native_stats"))
        self.assertIn("api_mode=native", "\n".join(timer.summary_lines()))
        self.assertIn("reasoning_tokens=0", "\n".join(timer.summary_lines()))

    def test_native_non_streaming_extracts_message_output(self):
        captured = {}
        body = {
            "output": [
                {"type": "reasoning", "content": "hidden"},
                {"type": "message", "content": "Visible answer."},
            ],
            "stats": {"reasoning_output_tokens": 3},
        }

        def fake_urlopen(request, timeout):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse(body=json.dumps(body).encode("utf-8"))

        provider = LMStudioProvider(base_url="http://localhost:1234/v1", model="test-model", api_mode="native", reasoning="auto", urlopen=fake_urlopen)
        response = provider.chat([{"role": "user", "content": "hello"}], stream=False)

        self.assertTrue(response.success)
        self.assertEqual(response.content, "Visible answer.")
        self.assertNotIn("reasoning", captured["body"])
        self.assertEqual(captured["body"]["max_output_tokens"], 512)


if __name__ == "__main__":
    unittest.main()
