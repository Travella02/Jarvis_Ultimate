"""Manifest for app_agent."""

MANIFEST = {
    "name": "app_agent",
    "display_name": "App Agent",
    "enabled_by_default": True,
    "description": "Opens, closes, switches, and verifies apps/windows.",
    "intents": ['app_control'],
    "permissions": ['app_control'],
    "tools": ['launcher', 'process_checker', 'window_controller'],
}
