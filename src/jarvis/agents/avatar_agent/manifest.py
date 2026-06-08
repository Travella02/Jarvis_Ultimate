"""Manifest for avatar_agent."""

MANIFEST = {
    "name": "avatar_agent",
    "display_name": "Avatar Agent",
    "enabled_by_default": True,
    "description": "Controls Jarvis visual body, avatar state, emotion, and expression.",
    "intents": ['avatar_control'],
    "permissions": ['avatar_config_write'],
    "tools": ['avatar_controller', 'emotion_mapper', 'animation_state', 'expression_controller'],
}
