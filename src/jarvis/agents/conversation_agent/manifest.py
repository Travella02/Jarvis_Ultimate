"""Manifest for the general conversation agent."""

MANIFEST = {
    "name": "conversation_agent",
    "display_name": "Conversation Agent",
    "enabled_by_default": True,
    "description": "Handles normal chat fallback through the configured LLM provider, Jarvis status, and agent listing.",
    "intents": ["general_chat", "status", "list_agents", "empty"],
    "permissions": [],
    "tools": ["llm_chat"],
}
