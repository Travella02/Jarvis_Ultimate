from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import tempfile
import unittest
from pathlib import Path

from jarvis.agents.conversation_agent.prompts import MINIMAL_SYSTEM_PROMPT
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider


class TestLLMStructureDiagnostics(unittest.TestCase):
    def test_runtime_prompt_diagnostics_reports_config(self):
        runtime = JarvisRuntime(llm_provider=MockLLMProvider(canned_response="ready"))
        output = runtime.prompt_diagnostics()

        self.assertIn("LLM prompt/config diagnostics", output)
        self.assertIn("conversation prompt mode", output)
        self.assertIn("system prompt size", output)

    def test_runtime_direct_benchmark_sets_last_timing(self):
        runtime = JarvisRuntime(llm_provider=MockLLMProvider(canned_response="ready"))
        runtime.boot()
        output = runtime.benchmark_llm(prompt_mode="minimal")

        self.assertIn("Direct LLM benchmark complete", output)
        self.assertIn("Prompt mode: minimal", output)
        self.assertIsNotNone(runtime.last_timing)
        self.assertTrue(runtime.last_timing.has_mark("diagnostic.direct_lm_benchmark_start"))
        self.assertTrue(runtime.last_timing.has_mark("diagnostic.direct_lm_benchmark_finished"))

    def test_conversation_agent_uses_configured_prompt_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text("JARVIS_CONVERSATION_PROMPT_MODE=minimal\n", encoding="utf-8")
            runtime = JarvisRuntime(project_root=root, llm_provider=MockLLMProvider(canned_response="hello"))
            runtime.boot()
            result = runtime.handle_command("hello jarvis")

        self.assertTrue(result.success)
        self.assertEqual(result.data["prompt_mode"], "minimal")
        self.assertEqual(result.data["system_prompt_chars"], len(MINIMAL_SYSTEM_PROMPT))


class TestLMNativeDiagnostics(unittest.TestCase):
    def test_runtime_prompt_diagnostics_reports_native_controls(self):
        runtime = JarvisRuntime(llm_provider=MockLLMProvider(canned_response="ready"))
        output = runtime.prompt_diagnostics()

        self.assertIn("API mode", output)
        self.assertIn("reasoning/thinking", output)
        self.assertIn("context length override", output)

    def test_runtime_benchmark_accepts_native_reasoning_override(self):
        runtime = JarvisRuntime(llm_provider=MockLLMProvider(canned_response="ready"))
        runtime.boot()
        output = runtime.benchmark_llm(api_mode="native", reasoning="off")

        self.assertIn("API mode: native", output)
        self.assertIn("Reasoning: off", output)
        self.assertIsNotNone(runtime.last_timing)
        start = runtime.last_timing.get_mark("diagnostic.direct_lm_benchmark_start")
        self.assertIsNotNone(start)
        self.assertEqual(start.data["api_mode"], "native")
        self.assertEqual(start.data["reasoning"], "off")


if __name__ == "__main__":
    unittest.main()
