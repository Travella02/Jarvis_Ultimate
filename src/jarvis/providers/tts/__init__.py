"""Swappable text-to-speech providers for Jarvis."""

from jarvis.providers.tts.base import TTSProvider, TTSProviderStatus, TTSRequest, TTSResult
from jarvis.providers.tts.manager import TTSManager, format_tts_result

__all__ = ["TTSProvider", "TTSProviderStatus", "TTSRequest", "TTSResult", "TTSManager", "format_tts_result"]
