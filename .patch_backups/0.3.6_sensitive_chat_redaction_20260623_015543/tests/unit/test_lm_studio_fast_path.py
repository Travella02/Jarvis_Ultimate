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


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class TestLMStudioFastPath(unittest.TestCase):
    def test_auto_model_fast_path_skips_models_lookup_before_chat(self):
        requested_urls = []

        def fake_urlopen(request, timeout):
            requested_urls.append(request.full_url)
            return FakeHTTPResponse({"choices": [{"message": {"content": "fast response"}}]})

        timer = TurnTimer(command="hello")
        provider = LMStudioProvider(model="auto", urlopen=fake_urlopen)
        response = provider.chat([{"role": "user", "content": "hello"}], timing=timer)

        self.assertTrue(response.success)
        self.assertEqual(response.model, "local-model")
        self.assertEqual(requested_urls, ["http://127.0.0.1:1234/v1/chat/completions"])
        self.assertTrue(timer.has_mark("lm_studio.request_start"))
        self.assertTrue(timer.has_mark("lm_studio.model_resolved"))

    def test_auto_model_lookup_can_be_enabled_when_needed(self):
        requested_urls = []

        def fake_urlopen(request, timeout):
            requested_urls.append(request.full_url)
            if request.full_url.endswith("/models"):
                return FakeHTTPResponse({"data": [{"id": "loaded-model"}]})
            return FakeHTTPResponse({"choices": [{"message": {"content": "lookup response"}}]})

        provider = LMStudioProvider(model="auto", resolve_auto_model=True, urlopen=fake_urlopen)
        response = provider.chat([{"role": "user", "content": "hello"}])

        self.assertTrue(response.success)
        self.assertEqual(response.model, "loaded-model")
        self.assertEqual(requested_urls[0], "http://127.0.0.1:1234/v1/models")
        self.assertEqual(requested_urls[1], "http://127.0.0.1:1234/v1/chat/completions")


if __name__ == "__main__":
    unittest.main()
