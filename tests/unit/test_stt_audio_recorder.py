import unittest
from pathlib import Path

from jarvis.providers.stt.audio_recorder import AudioRecordResult, format_record_result


class TestSTTAudioRecorder(unittest.TestCase):
    def test_format_record_result_includes_output(self):
        result = AudioRecordResult.ok(
            "Microphone recording saved.",
            output_path=Path("data/stt/sample.wav"),
            duration_seconds=1.25,
            sample_rate=16000,
            channels=1,
        )
        text = format_record_result(result)
        self.assertIn("Microphone recording saved", text)
        self.assertIn("data/stt/sample.wav", text)
        self.assertIn("16000", text)


if __name__ == "__main__":
    unittest.main()
