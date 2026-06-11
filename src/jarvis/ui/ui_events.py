"""UI event helpers for Jarvis desktop clients."""

from __future__ import annotations

from typing import Any

from jarvis.core.result import JarvisEvent


_STATE_EVENT_MAP = {
    "jarvis.boot_started": "thinking",
    "jarvis.boot_finished": "idle",
    "voice.loop_started": "listening",
    "voice.loop_transcript_ready": "transcribing",
    "voice.loop_finished": "idle",
    "voice.loop_failed": "error",
    "voice.continuous_loop_started": "wake_listening",
    "voice.continuous_loop_finished": "sleeping",
    "voice.sleep_wake_loop_started": "wake_listening",
    "voice.sleep_wake_loop_finished": "sleeping",
    "wake.detected": "listening",
    "wake.rejected": "sleeping",
    "llm.request_started": "thinking",
    "lm_studio.request_start": "thinking",
    "lm_studio.first_chunk": "speaking",
    "lm_studio.stream_done": "speaking",
    "tts.speak_started": "speaking",
    "tts.speak_finished": "idle",
    "tts.speak_failed": "error",
    "memory.saved": "idle",
    "error.detected": "error",
}


def avatar_state_from_event(event_type: str) -> str | None:
    """Return the avatar state implied by an event type, if known."""

    return _STATE_EVENT_MAP.get(event_type)


def make_ui_open_panel_event(panel_id: str, *, title: str | None = None, payload: dict[str, Any] | None = None) -> JarvisEvent:
    """Create a standard event for future tools to open a UI panel."""

    return JarvisEvent(
        event_type="ui.open_panel",
        source="ui",
        message=f"Open panel: {title or panel_id}",
        data={"panel_id": panel_id, "title": title or panel_id, "payload": payload or {}},
    )


def make_ui_update_panel_event(panel_id: str, *, payload: dict[str, Any] | None = None) -> JarvisEvent:
    """Create a standard event for future tools to update a UI panel."""

    return JarvisEvent(
        event_type="ui.update_panel",
        source="ui",
        message=f"Update panel: {panel_id}",
        data={"panel_id": panel_id, "payload": payload or {}},
    )
