from types import SimpleNamespace
import time
import unittest

from jarvis.clients.desktop.app import JarvisDesktopApp
from jarvis.core.result import JarvisResult


class FakeEvents:
    def __init__(self):
        self.subscribers = []
        self.emitted = []

    def subscribe(self, pattern, callback):
        self.subscribers.append((pattern, callback))

    def emit(self, event_type, *, source="test", message="", data=None):
        self.emitted.append((event_type, source, message, data or {}))


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
        self.config = SimpleNamespace(
            desktop_auto_start_voice=True,
            voice_always_listening_on_startup=True,
            voice_always_listening_max_turns=0,
            voice_sleep_timeout_seconds=45.0,
            stt_listen_mode="smart",
            stt_silence_seconds=0.65,
        )
        self.events = FakeEvents()
        self.registry = FakeRegistry()
        self.llm_provider = SimpleNamespace(provider_name="mock", model="mock")
        self.tts_manager = SimpleNamespace(enabled=True, provider_name="mock")
        self.stt_manager = SimpleNamespace(enabled=True, provider_name="mock")
        self.wake_word_manager = SimpleNamespace(wake_words=["hey jarvis"])
        self.short_term_memory = FakeMemory()
        self.loop_kwargs = None
        self.stop_called = False
        self.boot_called = False

    def boot(self):
        self.boot_called = True
        return JarvisResult.ok("Jarvis is online.", agent_name="lifecycle", action="boot")

    def voice_sleep_wake_loop(self, **kwargs):
        self.loop_kwargs = kwargs
        kwargs["status_callback"]("Listening turn 1/∞ (sleeping)...")
        kwargs["transcript_callback"]("Hey Jarvis, test")
        kwargs["stream_callback"]("Ready, sir.")
        stop_event = kwargs.get("stop_event")
        if stop_event is not None:
            stop_event.wait(0.2)
        return JarvisResult.ok(
            "Sleep/wake voice loop stopped, sir.",
            agent_name="voice_agent",
            action="voice_sleep_wake_loop",
            data={"final_state": "asleep"},
        )

    def tts_stop(self):
        self.stop_called = True
        return "stopped"

    def warmup_all(self):
        return "warmup complete"


class DesktopFullRuntimeTests(unittest.TestCase):
    def test_boot_auto_starts_background_voice_runtime(self):
        runtime = FakeRuntime()
        app = JarvisDesktopApp(runtime=runtime)
        message = app.boot()
        self.assertIn("online", message)
        self.assertTrue(runtime.boot_called)

        deadline = time.time() + 1.0
        while runtime.loop_kwargs is None and time.time() < deadline:
            time.sleep(0.01)
        self.assertIsNotNone(runtime.loop_kwargs)
        self.assertEqual(runtime.loop_kwargs["max_turns"], 0)
        self.assertIsNotNone(runtime.loop_kwargs["stop_event"])
        self.assertTrue(any(msg["role"] == "user" for msg in app.workspace.chat_messages))

        app.stop_voice_runtime()
        if app._voice_thread is not None:
            app._voice_thread.join(timeout=1.0)
        self.assertTrue(runtime.stop_called)
        self.assertFalse(app.voice_runtime_running())

    def test_start_voice_runtime_does_not_start_twice(self):
        runtime = FakeRuntime()
        runtime.config.voice_always_listening_on_startup = False
        app = JarvisDesktopApp(runtime=runtime)
        app.start_voice_runtime()
        first_thread = app._voice_thread
        duplicate = app.start_voice_runtime()
        self.assertIn("already running", duplicate)
        self.assertIs(app._voice_thread, first_thread)
        app.stop_voice_runtime()


if __name__ == "__main__":
    unittest.main()
