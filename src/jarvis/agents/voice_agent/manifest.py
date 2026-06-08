"""Manifest for voice_agent."""

MANIFEST = {
    "name": "voice_agent",
    "display_name": "Voice Agent",
    "enabled_by_default": True,
    "description": "Handles voice input, voice output, TTS, STT, and voice profile control.",
    "intents": ['voice_control'],
    "permissions": ['audio_output', 'microphone'],
    "tools": ['voice_selector', 'tts_engine', 'stt_engine', 'audio_output'],
}
