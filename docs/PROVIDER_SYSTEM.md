# Provider System

Providers make Jarvis swappable.

Examples:
- LLM providers: mock, Ollama, OpenAI, Claude, LM Studio
- OCR providers: mock, Tesseract, Windows OCR, local vision model
- TTS providers: mock, Windows TTS, Piper, ElevenLabs
- STT providers: mock, Whisper
- Avatar providers: image avatar, Live2D, VRM, animated orb

Agents should depend on provider interfaces, not hardcoded providers.
