"""Manifest for memory_agent."""

MANIFEST = {
    "name": "memory_agent",
    "display_name": "Memory Agent",
    "enabled_by_default": True,
    "description": "Stores, searches, lists, and forgets explicit long-term, temporary, and archived chat memory.",
    "intents": ["memory_write", "memory_search"],
    "permissions": ["memory_write"],
    "tools": [
        "memory_store",
        "memory_store_short_term",
        "memory_search",
        "memory_list",
        "memory_forget",
        "memory_status",
        "memory_chat_search",
    ],
}
