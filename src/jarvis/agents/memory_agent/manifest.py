"""Manifest for memory_agent."""

MANIFEST = {
    "name": "memory_agent",
    "display_name": "Memory Agent",
    "enabled_by_default": True,
    "description": "Stores and retrieves useful user/project context.",
    "intents": ['memory_write', 'memory_search'],
    "permissions": ['memory_write'],
    "tools": ['memory_store', 'memory_search'],
}
