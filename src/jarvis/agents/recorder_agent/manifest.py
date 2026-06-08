"""Manifest for recorder_agent."""

MANIFEST = {
    "name": "recorder_agent",
    "display_name": "Recorder Agent",
    "enabled_by_default": True,
    "description": "Manages recording, replay buffer, and clip saving.",
    "intents": ['recording_task'],
    "permissions": ['recording'],
    "tools": ['screen_recorder', 'replay_buffer', 'clip_saver'],
}
