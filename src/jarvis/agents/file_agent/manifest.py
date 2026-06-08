"""Manifest for file_agent."""

MANIFEST = {
    "name": "file_agent",
    "display_name": "File Agent",
    "enabled_by_default": True,
    "description": "Finds, opens, moves, organizes, and reports on files/storage.",
    "intents": ['file_task'],
    "permissions": ['file_read', 'file_write'],
    "tools": ['file_search', 'file_ops', 'storage_usage'],
}
