from pathlib import Path
import unittest


class TestAppShellCaptionLiveBeforeTTS025d(unittest.TestCase):
    def test_non_streamed_tool_caption_is_staged_before_tts_finish_wait(self):
        source_path = Path(__file__).resolve().parents[2] / 'src' / 'jarvis' / 'api' / 'local_server.py'
        source = source_path.read_text(encoding='utf-8')
        stage_index = source.find('self._stage_live_speech_caption(early_response_text, lead_seconds=0.22)')
        finish_index = source.find('self.runtime._finish_spoken_result(')
        self.assertGreater(stage_index, -1)
        self.assertGreater(finish_index, -1)
        self.assertLess(stage_index, finish_index)

    def test_caption_bug_reason_is_documented_in_source(self):
        source_path = Path(__file__).resolve().parents[2] / 'src' / 'jarvis' / 'api' / 'local_server.py'
        source = source_path.read_text(encoding='utf-8')
        self.assertIn('caption appears only after Jarvis returns to listening', source)


if __name__ == '__main__':
    unittest.main()
