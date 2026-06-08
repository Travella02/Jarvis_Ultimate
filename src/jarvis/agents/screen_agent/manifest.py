"""Manifest for screen_agent."""

MANIFEST = {
    "name": "screen_agent",
    "display_name": "Screen Agent",
    "enabled_by_default": True,
    "description": "Reads screenshots, OCR, active windows, and screen context.",
    "intents": ['screen_question', 'read_screen', 'full_screen_ocr'],
    "permissions": ['screenshot', 'ocr'],
    "tools": ['screenshot', 'ocr', 'active_window'],
}
