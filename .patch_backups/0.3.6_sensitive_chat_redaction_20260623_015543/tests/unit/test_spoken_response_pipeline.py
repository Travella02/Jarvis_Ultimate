from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.providers.tts.base import TTSResult
from jarvis.providers.tts.pipeline import SpokenResponsePipeline, SpokenStreamAdapter, extract_ready_tts_chunks, split_text_for_tts


class FakeTTSManager:
    def __init__(self):
        self.enabled = True
        self.auto_speak = True
        self.playback = True
        self.provider_name = "fake"
        self.calls = []
        self.stop_calls = 0

    def say(self, text, *, play_audio=None):
        self.calls.append((text, play_audio))
        return TTSResult.ok("fake speech generated", provider="fake", played=bool(play_audio), data={"text": text})

    def stop_playback(self):
        self.stop_calls += 1
        return True


class TestSpokenResponsePipeline(unittest.TestCase):
    def test_split_text_for_tts_uses_sentence_boundaries(self):
        chunks = split_text_for_tts("Hello sir. I am online! How can I help?", max_chars=120)

        self.assertEqual(chunks, ["Hello sir.", "I am online!", "How can I help?"])

    def test_extract_ready_chunks_keeps_incomplete_remainder(self):
        ready, remainder = extract_ready_tts_chunks("Hello sir. I am still", max_chars=120, force=False)

        self.assertEqual(ready, ["Hello sir."])
        self.assertEqual(remainder, "I am still")

    def test_pipeline_speaks_queued_chunks_in_background(self):
        manager = FakeTTSManager()
        pipeline = SpokenResponsePipeline(manager, chunk_max_chars=120, queue_max_size=4, play_audio=True)

        count = pipeline.enqueue_text("Hello sir. I am ready.")
        self.assertEqual(count, 2)
        self.assertTrue(pipeline.wait_until_idle(timeout=3.0))
        pipeline.shutdown()

        self.assertEqual([call[0] for call in manager.calls], ["Hello sir.", "I am ready."])
        self.assertTrue(all(call[1] is True for call in manager.calls))

    def test_stream_adapter_prints_and_enqueues_sentence_chunks(self):
        manager = FakeTTSManager()
        pipeline = SpokenResponsePipeline(manager, chunk_max_chars=120, queue_max_size=4, play_audio=True)
        printed = []
        adapter = SpokenStreamAdapter(pipeline=pipeline, display_callback=printed.append, enabled=True, max_chars=120)

        adapter("Hello ")
        adapter("sir. This is")
        adapter(" Jarvis")
        adapter.finish()
        self.assertTrue(pipeline.wait_until_idle(timeout=3.0))
        pipeline.shutdown()

        self.assertEqual("".join(printed), "Hello sir. This is Jarvis")
        self.assertEqual([call[0] for call in manager.calls], ["Hello sir.", "This is Jarvis"])

    def test_stop_clears_pending_and_calls_manager_stop(self):
        manager = FakeTTSManager()
        pipeline = SpokenResponsePipeline(manager, chunk_max_chars=120, queue_max_size=4, play_audio=True)
        pipeline.enqueue_chunk("one")
        removed = pipeline.stop(clear_pending=True)
        pipeline.shutdown()

        self.assertGreaterEqual(removed, 0)
        self.assertEqual(manager.stop_calls, 2)  # stop() plus shutdown() cleanup


if __name__ == "__main__":
    unittest.main()
