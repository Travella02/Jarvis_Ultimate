"""Manifest for memory_agent."""

MANIFEST = {
    "name": "memory_agent",
    "display_name": "Memory Agent",
    "enabled_by_default": True,
    "description": "Stores, searches, lists, forgets, and reviews long-term, temporary, archived chat, and candidate memories.",
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
        "memory_candidates_list",
        "memory_candidate_approve",
        "memory_candidate_reject",
    ],
}
