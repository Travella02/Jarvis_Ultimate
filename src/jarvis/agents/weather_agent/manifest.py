"""Manifest for weather_agent."""

MANIFEST = {
    "name": "weather_agent",
    "display_name": "Weather Agent",
    "enabled_by_default": True,
    "description": "Handles weather and forecast lookups.",
    "intents": ['weather_lookup'],
    "permissions": ['network'],
    "tools": ['weather_lookup'],
}
