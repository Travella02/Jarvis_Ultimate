from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import json
import unittest

from jarvis.providers.llm.lm_studio_provider import LMStudioProvider
from jarvis.providers.llm.mock_provider import MockLLMProvider


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class TestLLMProviders(unittest.TestCase):
    def test_mock_chat_response(self):
        provider = MockLLMProvider(canned_response="hello from mock")
        response = provider.chat([{"role": "user", "content": "hello"}])
        self.assertTrue(response.success)
        self.assertEqual(response.content, "hello from mock")
        self.assertEqual(response.provider, "mock")

    def test_lm_studio_chat_uses_openai_compatible_shape(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeHTTPResponse({
                "choices": [
                    {"message": {"content": "LM Studio says hello."}}
                ]
            })

        provider = LMStudioProvider(base_url="http://localhost:1234/v1", model="test-model", urlopen=fake_urlopen)
        response = provider.chat([{"role": "user", "content": "hello"}], system_prompt="system")

        self.assertTrue(response.success)
        self.assertEqual(response.content, "LM Studio says hello.")
        self.assertEqual(captured["url"], "http://localhost:1234/v1/chat/completions")
        self.assertEqual(captured["body"]["model"], "test-model")
        self.assertEqual(captured["body"]["messages"][0]["role"], "system")

    def test_lm_studio_list_models(self):
        def fake_urlopen(request, timeout):
            return FakeHTTPResponse({"data": [{"id": "loaded-model"}]})

        provider = LMStudioProvider(urlopen=fake_urlopen)
        self.assertEqual(provider.list_models(), ["loaded-model"])
        self.assertEqual(provider.resolve_model(), "loaded-model")


if __name__ == "__main__":
    unittest.main()
