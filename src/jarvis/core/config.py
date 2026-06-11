"""Config helpers for Jarvis 3.

The project intentionally keeps config dependency-free right now. Environment
variables always win. Jarvis also reads a simple project-root ``.env`` file so
local LM Studio settings can be changed without touching committed YAML.
The simple providers.yaml reader supports the small subset of YAML used by
Jarvis's starter config.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


_ENV_ALIASES = {
    "environment": ("JARVIS_ENV",),
    "llm_provider": ("JARVIS_LLM_PROVIDER", "JARVIS_LM_PROVIDER"),
    "llm_model": ("JARVIS_LLM_MODEL", "JARVIS_LM_MODEL"),
    "llm_base_url": ("JARVIS_LM_STUDIO_BASE_URL", "JARVIS_LLM_STUDIO_BASE_URL", "JARVIS_LLM_BASE_URL"),
    "llm_timeout_seconds": ("JARVIS_LLM_TIMEOUT_SECONDS", "JARVIS_LM_TIMEOUT_SECONDS"),
    "llm_temperature": ("JARVIS_LLM_TEMPERATURE", "JARVIS_LM_TEMPERATURE"),
    "llm_max_tokens": ("JARVIS_LLM_MAX_TOKENS", "JARVIS_LM_MAX_TOKENS"),
    "llm_resolve_auto_model": ("JARVIS_LLM_RESOLVE_AUTO_MODEL", "JARVIS_LM_RESOLVE_AUTO_MODEL"),
    "llm_streaming": ("JARVIS_LLM_STREAMING", "JARVIS_LM_STREAMING"),
    "llm_api_mode": ("JARVIS_LLM_API_MODE", "JARVIS_LM_API_MODE"),
    "llm_native_base_url": ("JARVIS_LM_STUDIO_NATIVE_BASE_URL", "JARVIS_LLM_STUDIO_NATIVE_BASE_URL", "JARVIS_LLM_NATIVE_BASE_URL", "JARVIS_LM_NATIVE_BASE_URL"),
    "llm_reasoning": ("JARVIS_LLM_REASONING", "JARVIS_LM_REASONING", "JARVIS_LM_THINKING"),
    "llm_context_length": ("JARVIS_LLM_CONTEXT_LENGTH", "JARVIS_LM_CONTEXT_LENGTH"),
    "llm_store_native_chats": ("JARVIS_LLM_STORE_NATIVE_CHATS", "JARVIS_LM_STORE_NATIVE_CHATS"),
    "conversation_prompt_mode": ("JARVIS_CONVERSATION_PROMPT_MODE", "JARVIS_CHAT_SYSTEM_PROMPT_MODE", "JARVIS_LLM_PROMPT_MODE"),
    "llm_benchmark_max_tokens": ("JARVIS_LLM_BENCHMARK_MAX_TOKENS", "JARVIS_LM_BENCHMARK_MAX_TOKENS"),
    "llm_benchmark_prompt": ("JARVIS_LLM_BENCHMARK_PROMPT", "JARVIS_LM_BENCHMARK_PROMPT"),
    "memory_short_term_enabled": ("JARVIS_MEMORY_SHORT_TERM_ENABLED", "JARVIS_STM_ENABLED"),
    "memory_short_term_max_turns": ("JARVIS_MEMORY_SHORT_TERM_MAX_TURNS", "JARVIS_STM_MAX_TURNS"),
    "memory_short_term_max_chars": ("JARVIS_MEMORY_SHORT_TERM_MAX_CHARS", "JARVIS_STM_MAX_CHARS"),
    "memory_short_term_inject_last_turns": ("JARVIS_MEMORY_SHORT_TERM_INJECT_LAST_TURNS", "JARVIS_STM_INJECT_LAST_TURNS"),
    "memory_short_term_autosave": ("JARVIS_MEMORY_SHORT_TERM_AUTOSAVE", "JARVIS_STM_AUTOSAVE"),
    "tts_enabled": ("JARVIS_TTS_ENABLED",),
    "tts_provider": ("JARVIS_TTS_PROVIDER",),
    "tts_fallback_providers": ("JARVIS_TTS_FALLBACK_PROVIDERS",),
    "tts_output_dir": ("JARVIS_TTS_OUTPUT_DIR",),
    "tts_voice_name": ("JARVIS_TTS_VOICE_NAME", "JARVIS_VOICE_NAME"),
    "tts_voice_profiles_dir": ("JARVIS_TTS_VOICE_PROFILES_DIR",),
    "tts_language": ("JARVIS_TTS_LANGUAGE",),
    "tts_device": ("JARVIS_TTS_DEVICE",),
    "tts_use_gpu": ("JARVIS_TTS_USE_GPU",),
    "tts_playback": ("JARVIS_TTS_PLAYBACK",),
    "tts_auto_speak": ("JARVIS_TTS_AUTO_SPEAK", "JARVIS_VOICE_AUTO_SPEAK"),
    "tts_xtts_model_name": ("JARVIS_TTS_XTTS_MODEL_NAME",),
    "tts_xtts_speaker_wav": ("JARVIS_TTS_XTTS_SPEAKER_WAV", "JARVIS_XTTS_SPEAKER_WAV"),
    "tts_kokoro_voice": ("JARVIS_TTS_KOKORO_VOICE",),
    "tts_kokoro_lang_code": ("JARVIS_TTS_KOKORO_LANG_CODE",),
    "tts_auto_speak_chunk_chars": ("JARVIS_TTS_AUTO_SPEAK_CHUNK_CHARS", "JARVIS_VOICE_CHUNK_CHARS"),
    "tts_queue_max_size": ("JARVIS_TTS_QUEUE_MAX_SIZE", "JARVIS_VOICE_QUEUE_MAX_SIZE"),
    "stt_enabled": ("JARVIS_STT_ENABLED",),
    "stt_provider": ("JARVIS_STT_PROVIDER",),
    "stt_fallback_providers": ("JARVIS_STT_FALLBACK_PROVIDERS",),
    "stt_model": ("JARVIS_STT_MODEL", "JARVIS_WHISPER_MODEL"),
    "stt_device": ("JARVIS_STT_DEVICE",),
    "stt_compute_type": ("JARVIS_STT_COMPUTE_TYPE",),
    "stt_gpu_fallback_to_cpu": ("JARVIS_STT_GPU_FALLBACK_TO_CPU",),
    "stt_device_index": ("JARVIS_STT_DEVICE_INDEX",),
    "stt_warmup_on_boot": ("JARVIS_STT_WARMUP_ON_BOOT",),
    "stt_language": ("JARVIS_STT_LANGUAGE",),
    "stt_output_dir": ("JARVIS_STT_OUTPUT_DIR",),
    "stt_record_seconds": ("JARVIS_STT_RECORD_SECONDS", "JARVIS_MIC_RECORD_SECONDS"),
    "stt_listen_mode": ("JARVIS_STT_LISTEN_MODE", "JARVIS_MIC_LISTEN_MODE"),
    "stt_max_listen_seconds": ("JARVIS_STT_MAX_LISTEN_SECONDS", "JARVIS_MIC_MAX_LISTEN_SECONDS"),
    "stt_silence_seconds": ("JARVIS_STT_SILENCE_SECONDS", "JARVIS_MIC_SILENCE_SECONDS"),
    "stt_min_record_seconds": ("JARVIS_STT_MIN_RECORD_SECONDS", "JARVIS_MIC_MIN_RECORD_SECONDS"),
    "stt_start_timeout_seconds": ("JARVIS_STT_START_TIMEOUT_SECONDS", "JARVIS_MIC_START_TIMEOUT_SECONDS"),
    "stt_energy_threshold": ("JARVIS_STT_ENERGY_THRESHOLD", "JARVIS_MIC_ENERGY_THRESHOLD"),
    "stt_pre_roll_seconds": ("JARVIS_STT_PRE_ROLL_SECONDS", "JARVIS_MIC_PRE_ROLL_SECONDS"),
    "stt_frame_ms": ("JARVIS_STT_FRAME_MS", "JARVIS_MIC_FRAME_MS"),
    "stt_sample_rate": ("JARVIS_STT_SAMPLE_RATE", "JARVIS_MIC_SAMPLE_RATE"),
    "stt_channels": ("JARVIS_STT_CHANNELS", "JARVIS_MIC_CHANNELS"),
    "stt_microphone_device": ("JARVIS_STT_MICROPHONE_DEVICE", "JARVIS_MIC_DEVICE"),
    "stt_vad_filter": ("JARVIS_STT_VAD_FILTER",),
    "stt_mock_text": ("JARVIS_STT_MOCK_TEXT",),
    "wake_word_enabled": ("JARVIS_WAKE_WORD_ENABLED", "JARVIS_WAKE_ENABLED"),
    "wake_word_provider": ("JARVIS_WAKE_WORD_PROVIDER", "JARVIS_WAKE_PROVIDER"),
    "wake_words": ("JARVIS_WAKE_WORDS", "JARVIS_WAKE_PHRASES"),
    "wake_require_wake_word": ("JARVIS_WAKE_REQUIRE_WAKE_WORD", "JARVIS_WAKE_REQUIRED"),
    "wake_strip_wake_word": ("JARVIS_WAKE_STRIP_WAKE_WORD",),
    "wake_empty_response": ("JARVIS_WAKE_EMPTY_RESPONSE",),
}



def _read_simple_provider_config(path: Path) -> dict[str, Any]:
    """Read the small providers.yaml shape Jarvis uses without PyYAML.

    Supported shape:

        providers:
          llm:
            default: lm_studio
            model: auto
            base_url: http://localhost:1234/v1
            streaming: true
    """
    if not path.exists():
        return {}

    data: dict[str, Any] = {}
    in_llm = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        if indent == 2 and stripped == "llm:":
            in_llm = True
            continue
        if indent <= 2 and stripped.endswith(":") and stripped != "llm:":
            in_llm = False
        if in_llm and indent >= 4 and ":" in stripped:
            key, value = stripped.split(":", 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data




def _read_simple_provider_section_config(path: Path, section_name: str) -> dict[str, Any]:
    """Read a named provider section from the starter providers.yaml.

    This deliberately supports only the simple Jarvis config shape and avoids a
    YAML dependency during the early rebuild.
    """
    if not path.exists():
        return {}

    data: dict[str, Any] = {}
    in_section = False
    section_header = f"{section_name}:"
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        if indent == 2 and stripped == section_header:
            in_section = True
            continue
        if indent <= 2 and stripped.endswith(":") and stripped != section_header:
            in_section = False
        if in_section and indent >= 4 and ":" in stripped:
            key, value = stripped.split(":", 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data

def _read_simple_env_file(path: Path) -> dict[str, str]:
    """Read a small KEY=value .env file without adding a dependency.

    This intentionally supports only the normal Jarvis settings style. It skips
    comments and blank lines, strips optional single/double quotes, and does not
    modify ``os.environ``.
    """
    if not path.exists():
        return {}

    data: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        data[key] = value
    return data


def _setting(names: Iterable[str], env_file: dict[str, str], default: Any) -> Any:
    """Resolve a config value with OS environment taking highest priority."""
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value
    for name in names:
        if name in env_file:
            return env_file[name]
    return default


def _normalize_prompt_mode(value: Any) -> str:
    text = str(value or "normal").strip().lower().replace("-", "_")
    if text in {"minimal", "small", "short", "fast"}:
        return "minimal"
    if text in {"off", "none", "no_system", "disabled", "false", "0"}:
        return "off"
    return "normal"


def _as_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"auto", "default", "none", "off", "0"}:
        return None
    try:
        number = int(text)
    except ValueError:
        return None
    return number if number > 0 else None


def _as_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


@dataclass(slots=True)
class JarvisConfig:
    project_root: Path = field(default_factory=lambda: Path.cwd())
    logs_dir: Path = field(default_factory=lambda: Path("logs"))
    data_dir: Path = field(default_factory=lambda: Path("data"))
    environment: str = "development"
    debug: bool = True

    llm_provider: str = "lm_studio"
    llm_model: str = "auto"
    llm_base_url: str = "http://127.0.0.1:1234/v1"
    llm_timeout_seconds: float = 90.0
    llm_temperature: float = 0.7
    llm_max_tokens: int = 512
    llm_resolve_auto_model: bool = False
    llm_streaming: bool = True
    llm_api_mode: str = "openai"
    llm_native_base_url: str = "http://127.0.0.1:1234"
    llm_reasoning: str = "auto"
    llm_context_length: int | None = None
    llm_store_native_chats: bool = False
    conversation_prompt_mode: str = "normal"
    llm_benchmark_max_tokens: int = 64
    llm_benchmark_prompt: str = "Reply with exactly one short sentence saying you are ready."

    memory_short_term_enabled: bool = True
    memory_short_term_max_turns: int = 20
    memory_short_term_max_chars: int = 12_000
    memory_short_term_inject_last_turns: int = 8
    memory_short_term_autosave: bool = False

    tts_enabled: bool = True
    tts_provider: str = "kokoro"
    tts_fallback_providers: str = "mock"
    tts_output_dir: str = "data/tts"
    tts_voice_name: str = "jarvis"
    tts_voice_profiles_dir: str = "data/tts/voices"
    tts_language: str = "en"
    tts_device: str = "auto"
    tts_use_gpu: bool = False
    tts_playback: bool = False
    tts_auto_speak: bool = False
    tts_xtts_model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    tts_xtts_speaker_wav: str = "assets/voices/jarvis_reference.wav"
    tts_kokoro_voice: str = "af_heart"
    tts_kokoro_lang_code: str = "a"
    tts_auto_speak_chunk_chars: int = 320
    tts_queue_max_size: int = 12

    stt_enabled: bool = True
    stt_provider: str = "faster_whisper"
    stt_fallback_providers: str = "mock"
    stt_model: str = "base.en"
    stt_device: str = "auto"
    stt_compute_type: str = "auto"
    stt_gpu_fallback_to_cpu: bool = True
    stt_device_index: int = 0
    stt_warmup_on_boot: bool = False
    stt_language: str = "en"
    stt_output_dir: str = "data/stt"
    stt_record_seconds: float = 2.0
    stt_listen_mode: str = "smart"
    stt_max_listen_seconds: float = 8.0
    stt_silence_seconds: float = 1.0
    stt_min_record_seconds: float = 0.35
    stt_start_timeout_seconds: float = 5.0
    stt_energy_threshold: float = 0.012
    stt_pre_roll_seconds: float = 0.25
    stt_frame_ms: int = 30
    stt_sample_rate: int = 16000
    stt_channels: int = 1
    stt_microphone_device: str = ""
    stt_vad_filter: bool = True
    stt_mock_text: str = "Hello sir, this is a mock transcription."

    wake_word_enabled: bool = True
    wake_word_provider: str = "phrase"
    wake_words: str = "hey jarvis,jarvis"
    wake_require_wake_word: bool = True
    wake_strip_wake_word: bool = True
    wake_empty_response: str = "Yes, sir?"

    @classmethod
    def from_project_root(cls, project_root: str | Path | None = None) -> "JarvisConfig":
        root = Path(project_root) if project_root else Path.cwd()
        provider_config = _read_simple_provider_config(root / "config" / "providers.yaml")
        tts_config = _read_simple_provider_section_config(root / "config" / "providers.yaml", "tts")
        stt_config = _read_simple_provider_section_config(root / "config" / "providers.yaml", "stt")
        wake_config = _read_simple_provider_section_config(root / "config" / "providers.yaml", "wake_word")
        env_file = _read_simple_env_file(root / ".env")

        return cls(
            project_root=root,
            logs_dir=root / "logs",
            data_dir=root / "data",
            environment=str(_setting(_ENV_ALIASES["environment"], env_file, "development")),
            llm_provider=str(_setting(_ENV_ALIASES["llm_provider"], env_file, provider_config.get("default", "lm_studio"))),
            llm_model=str(_setting(_ENV_ALIASES["llm_model"], env_file, provider_config.get("model", "auto"))),
            llm_base_url=str(_setting(_ENV_ALIASES["llm_base_url"], env_file, provider_config.get("base_url", "http://127.0.0.1:1234/v1"))),
            llm_timeout_seconds=float(_setting(_ENV_ALIASES["llm_timeout_seconds"], env_file, provider_config.get("timeout_seconds", "90"))),
            llm_temperature=float(_setting(_ENV_ALIASES["llm_temperature"], env_file, provider_config.get("temperature", "0.7"))),
            llm_max_tokens=int(_setting(_ENV_ALIASES["llm_max_tokens"], env_file, provider_config.get("max_tokens", "512"))),
            llm_resolve_auto_model=_as_bool(
                _setting(_ENV_ALIASES["llm_resolve_auto_model"], env_file, provider_config.get("resolve_auto_model", "false")),
                default=False,
            ),
            llm_streaming=_as_bool(
                _setting(_ENV_ALIASES["llm_streaming"], env_file, provider_config.get("streaming", "true")),
                default=True,
            ),
            llm_api_mode=str(_setting(_ENV_ALIASES["llm_api_mode"], env_file, provider_config.get("api_mode", "openai"))).strip().lower(),
            llm_native_base_url=str(
                _setting(_ENV_ALIASES["llm_native_base_url"], env_file, provider_config.get("native_base_url", "http://127.0.0.1:1234"))
            ),
            llm_reasoning=str(_setting(_ENV_ALIASES["llm_reasoning"], env_file, provider_config.get("reasoning", "auto"))).strip().lower(),
            llm_context_length=_as_optional_int(_setting(_ENV_ALIASES["llm_context_length"], env_file, provider_config.get("context_length", ""))),
            llm_store_native_chats=_as_bool(
                _setting(_ENV_ALIASES["llm_store_native_chats"], env_file, provider_config.get("store_native_chats", "false")),
                default=False,
            ),
            conversation_prompt_mode=_normalize_prompt_mode(
                _setting(_ENV_ALIASES["conversation_prompt_mode"], env_file, provider_config.get("conversation_prompt_mode", "normal"))
            ),
            llm_benchmark_max_tokens=int(
                _setting(_ENV_ALIASES["llm_benchmark_max_tokens"], env_file, provider_config.get("benchmark_max_tokens", "64"))
            ),
            llm_benchmark_prompt=str(
                _setting(
                    _ENV_ALIASES["llm_benchmark_prompt"],
                    env_file,
                    provider_config.get("benchmark_prompt", "Reply with exactly one short sentence saying you are ready."),
                )
            ),
            memory_short_term_enabled=_as_bool(
                _setting(_ENV_ALIASES["memory_short_term_enabled"], env_file, provider_config.get("memory_short_term_enabled", "true")),
                default=True,
            ),
            memory_short_term_max_turns=int(
                _setting(_ENV_ALIASES["memory_short_term_max_turns"], env_file, provider_config.get("memory_short_term_max_turns", "20"))
            ),
            memory_short_term_max_chars=int(
                _setting(_ENV_ALIASES["memory_short_term_max_chars"], env_file, provider_config.get("memory_short_term_max_chars", "12000"))
            ),
            memory_short_term_inject_last_turns=int(
                _setting(
                    _ENV_ALIASES["memory_short_term_inject_last_turns"],
                    env_file,
                    provider_config.get("memory_short_term_inject_last_turns", "8"),
                )
            ),
            memory_short_term_autosave=_as_bool(
                _setting(_ENV_ALIASES["memory_short_term_autosave"], env_file, provider_config.get("memory_short_term_autosave", "false")),
                default=False,
            ),
            tts_enabled=_as_bool(_setting(_ENV_ALIASES["tts_enabled"], env_file, tts_config.get("enabled", "true")), default=True),
            tts_provider=str(_setting(_ENV_ALIASES["tts_provider"], env_file, tts_config.get("default", "kokoro"))).strip().lower(),
            tts_fallback_providers=str(_setting(_ENV_ALIASES["tts_fallback_providers"], env_file, tts_config.get("fallback_providers", "mock"))),
            tts_output_dir=str(_setting(_ENV_ALIASES["tts_output_dir"], env_file, tts_config.get("output_dir", "data/tts"))),
            tts_voice_name=str(_setting(_ENV_ALIASES["tts_voice_name"], env_file, tts_config.get("voice_name", "jarvis"))),
            tts_language=str(_setting(_ENV_ALIASES["tts_language"], env_file, tts_config.get("language", "en"))),
            tts_voice_profiles_dir=str(_setting(_ENV_ALIASES["tts_voice_profiles_dir"], env_file, tts_config.get("voice_profiles_dir", "data/tts/voices"))),
            tts_device=str(_setting(_ENV_ALIASES["tts_device"], env_file, tts_config.get("device", "auto"))),
            tts_use_gpu=_as_bool(_setting(_ENV_ALIASES["tts_use_gpu"], env_file, tts_config.get("use_gpu", "false")), default=False),
            tts_playback=_as_bool(_setting(_ENV_ALIASES["tts_playback"], env_file, tts_config.get("playback", "false")), default=False),
            tts_auto_speak=_as_bool(_setting(_ENV_ALIASES["tts_auto_speak"], env_file, tts_config.get("auto_speak", "false")), default=False),
            tts_xtts_model_name=str(
                _setting(
                    _ENV_ALIASES["tts_xtts_model_name"],
                    env_file,
                    tts_config.get("xtts_model_name", "tts_models/multilingual/multi-dataset/xtts_v2"),
                )
            ),
            tts_xtts_speaker_wav=str(_setting(_ENV_ALIASES["tts_xtts_speaker_wav"], env_file, tts_config.get("xtts_speaker_wav", "assets/voices/jarvis_reference.wav"))),
            tts_kokoro_voice=str(_setting(_ENV_ALIASES["tts_kokoro_voice"], env_file, tts_config.get("kokoro_voice", "af_heart"))),
            tts_kokoro_lang_code=str(_setting(_ENV_ALIASES["tts_kokoro_lang_code"], env_file, tts_config.get("kokoro_lang_code", "a"))),
            tts_auto_speak_chunk_chars=int(_setting(_ENV_ALIASES["tts_auto_speak_chunk_chars"], env_file, tts_config.get("auto_speak_chunk_chars", "320"))),
            tts_queue_max_size=int(_setting(_ENV_ALIASES["tts_queue_max_size"], env_file, tts_config.get("queue_max_size", "12"))),
            stt_enabled=_as_bool(_setting(_ENV_ALIASES["stt_enabled"], env_file, stt_config.get("enabled", "true")), default=True),
            stt_provider=str(_setting(_ENV_ALIASES["stt_provider"], env_file, stt_config.get("default", "faster_whisper"))).strip().lower(),
            stt_fallback_providers=str(_setting(_ENV_ALIASES["stt_fallback_providers"], env_file, stt_config.get("fallback_providers", "mock"))),
            stt_model=str(_setting(_ENV_ALIASES["stt_model"], env_file, stt_config.get("model", "base.en"))),
            stt_device=str(_setting(_ENV_ALIASES["stt_device"], env_file, stt_config.get("device", "auto"))).strip().lower(),
            stt_compute_type=str(_setting(_ENV_ALIASES["stt_compute_type"], env_file, stt_config.get("compute_type", "auto"))).strip().lower(),
            stt_gpu_fallback_to_cpu=_as_bool(_setting(_ENV_ALIASES["stt_gpu_fallback_to_cpu"], env_file, stt_config.get("gpu_fallback_to_cpu", "true")), default=True),
            stt_device_index=int(_setting(_ENV_ALIASES["stt_device_index"], env_file, stt_config.get("device_index", "0"))),
            stt_warmup_on_boot=_as_bool(_setting(_ENV_ALIASES["stt_warmup_on_boot"], env_file, stt_config.get("warmup_on_boot", "false")), default=False),
            stt_language=str(_setting(_ENV_ALIASES["stt_language"], env_file, stt_config.get("language", "en"))),
            stt_output_dir=str(_setting(_ENV_ALIASES["stt_output_dir"], env_file, stt_config.get("output_dir", "data/stt"))),
            stt_record_seconds=float(_setting(_ENV_ALIASES["stt_record_seconds"], env_file, stt_config.get("record_seconds", "2.0"))),
            stt_listen_mode=str(_setting(_ENV_ALIASES["stt_listen_mode"], env_file, stt_config.get("listen_mode", "smart"))).strip().lower(),
            stt_max_listen_seconds=float(_setting(_ENV_ALIASES["stt_max_listen_seconds"], env_file, stt_config.get("max_listen_seconds", "8.0"))),
            stt_silence_seconds=float(_setting(_ENV_ALIASES["stt_silence_seconds"], env_file, stt_config.get("silence_seconds", "1.0"))),
            stt_min_record_seconds=float(_setting(_ENV_ALIASES["stt_min_record_seconds"], env_file, stt_config.get("min_record_seconds", "0.35"))),
            stt_start_timeout_seconds=float(_setting(_ENV_ALIASES["stt_start_timeout_seconds"], env_file, stt_config.get("start_timeout_seconds", "5.0"))),
            stt_energy_threshold=float(_setting(_ENV_ALIASES["stt_energy_threshold"], env_file, stt_config.get("energy_threshold", "0.012"))),
            stt_pre_roll_seconds=float(_setting(_ENV_ALIASES["stt_pre_roll_seconds"], env_file, stt_config.get("pre_roll_seconds", "0.25"))),
            stt_frame_ms=int(_setting(_ENV_ALIASES["stt_frame_ms"], env_file, stt_config.get("frame_ms", "30"))),
            stt_sample_rate=int(_setting(_ENV_ALIASES["stt_sample_rate"], env_file, stt_config.get("sample_rate", "16000"))),
            stt_channels=int(_setting(_ENV_ALIASES["stt_channels"], env_file, stt_config.get("channels", "1"))),
            stt_microphone_device=str(_setting(_ENV_ALIASES["stt_microphone_device"], env_file, stt_config.get("microphone_device", ""))),
            stt_vad_filter=_as_bool(_setting(_ENV_ALIASES["stt_vad_filter"], env_file, stt_config.get("vad_filter", "true")), default=True),
            stt_mock_text=str(_setting(_ENV_ALIASES["stt_mock_text"], env_file, stt_config.get("mock_text", "Hello sir, this is a mock transcription."))),
            wake_word_enabled=_as_bool(_setting(_ENV_ALIASES["wake_word_enabled"], env_file, wake_config.get("enabled", "true")), default=True),
            wake_word_provider=str(_setting(_ENV_ALIASES["wake_word_provider"], env_file, wake_config.get("default", "phrase"))).strip().lower(),
            wake_words=str(_setting(_ENV_ALIASES["wake_words"], env_file, wake_config.get("wake_words", "hey jarvis,jarvis"))),
            wake_require_wake_word=_as_bool(_setting(_ENV_ALIASES["wake_require_wake_word"], env_file, wake_config.get("require_wake_word", "true")), default=True),
            wake_strip_wake_word=_as_bool(_setting(_ENV_ALIASES["wake_strip_wake_word"], env_file, wake_config.get("strip_wake_word", "true")), default=True),
            wake_empty_response=str(_setting(_ENV_ALIASES["wake_empty_response"], env_file, wake_config.get("empty_response", "Yes, sir?"))),
        )
