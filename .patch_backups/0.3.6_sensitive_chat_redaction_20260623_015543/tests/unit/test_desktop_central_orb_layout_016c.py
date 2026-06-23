from types import SimpleNamespace
import unittest

from jarvis.clients.desktop.app import JarvisDesktopApp
from jarvis.core.result import JarvisResult


class FakeEvents:
    def subscribe(self, pattern, callback):
        self.pattern = pattern
        self.callback = callback

    def emit(self, *args, **kwargs):
        pass


class FakeRegistry:
    def enabled_records(self):
        return []

    def names(self, enabled_only=True):
        return []


class FakeMemory:
    def status(self):
        return {"turns": 0}


class FakeRuntime:
    def __init__(self):
        self.config = SimpleNamespace(desktop_auto_start_voice=False, voice_always_listening_on_startup=False)
        self.events = FakeEvents()
        self.registry = FakeRegistry()
        self.llm_provider = SimpleNamespace(provider_name="mock", model="mock")
        self.tts_manager = SimpleNamespace(enabled=True, provider_name="mock")
        self.stt_manager = SimpleNamespace(enabled=True, provider_name="mock")
        self.wake_word_manager = SimpleNamespace(wake_words=["hey jarvis"])
        self.short_term_memory = FakeMemory()

    def boot(self):
        return JarvisResult.ok("Jarvis is online.", agent_name="lifecycle", action="boot")

    def tts_stop(self):
        return "stopped"

    def warmup_all(self):
        return "warmup complete"


class TestDesktopCentralOrbLayout016c(unittest.TestCase):
    def test_desktop_reports_central_orb_layout(self):
        app = JarvisDesktopApp(runtime=FakeRuntime())
        self.assertEqual(app.desktop_layout_mode(), "central_orb_workspace")
        width, height = app.avatar_canvas_size()
        self.assertGreaterEqual(width, 480)
        self.assertGreaterEqual(height, 340)

    def test_central_layout_still_boots_without_tk(self):
        app = JarvisDesktopApp(runtime=FakeRuntime())
        message = app.boot()
        self.assertIn("online", message)
        self.assertIn("Jarvis desktop body initialized.", app.workspace.notices)


if __name__ == "__main__":
    unittest.main()
