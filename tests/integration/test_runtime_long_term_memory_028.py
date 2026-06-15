from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from jarvis.core.lifecycle import JarvisRuntime


class RuntimeLongTermMemory028Tests(unittest.TestCase):
    def test_runtime_routes_memory_commands_to_memory_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text("JARVIS_LLM_PROVIDER=mock\nJARVIS_MEMORY_LONG_TERM_PATH=data/memory/test_ltm.json\n", encoding="utf-8")
            runtime = JarvisRuntime(project_root=root)
            runtime.boot()
            result = runtime.handle_command("Jarvis, remember that my test color is blue")
            self.assertTrue(result.success)
            self.assertEqual(result.agent_name, "memory_agent")
            self.assertEqual(result.action, "memory_store")
            self.assertEqual(len(runtime.long_term_memory.records), 1)
            self.assertTrue((root / "data" / "memory" / "test_ltm.json").exists())

    def test_conversation_uses_relevant_long_term_memory_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text("JARVIS_LLM_PROVIDER=mock\nJARVIS_MEMORY_LONG_TERM_PATH=data/memory/test_ltm.json\n", encoding="utf-8")
            runtime = JarvisRuntime(project_root=root)
            runtime.boot()
            runtime.long_term_memory.add("Tanner's test favorite snack is apples.", tags=["snack"])
            result = runtime.handle_command("What is my test favorite snack?")
            self.assertTrue(result.success)
            self.assertEqual(result.agent_name, "conversation_agent")
            self.assertGreaterEqual(result.data.get("long_term_memories_used", 0), 1)


if __name__ == "__main__":
    unittest.main()
