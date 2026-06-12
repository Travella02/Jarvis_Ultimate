"""Dependency-free local HTTP API for Jarvis's native app shell.

This standard-library server is the live bridge between the Electron
HTML/CSS/JS interface and the Python Jarvis runtime.  0.1.9a refines panel controls, state colors, and automatic sleep/wake startup and keeps diagnostics out of the way so the orb stays in the speaking
state for real playback, the controls remain visible, and the app shell warms
voice systems before accepting a conversation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from typing import Any
from urllib.parse import urlparse

from jarvis.api.schemas import api_error, api_ok
from jarvis.clients.app_shell.bridge import DEFAULT_API_URL, build_app_shell_snapshot
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.core.result import JarvisResult
from jarvis.providers.tts.base import TTSResult
from jarvis.ui.visual_state import classify_voice_status
from jarvis.ui.workspace import UIWorkspaceState


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float_or_none(value: Any) -> float | None:
    if value in (None, "", "none"):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


class LocalJarvisAPI:
    """Stateful local bridge between the app shell and JarvisRuntime."""

    def __init__(self, *, runtime: JarvisRuntime | None = None, project_root: str | Path | None = None, api_url: str = DEFAULT_API_URL) -> None:
        self.runtime = runtime or JarvisRuntime(project_root=project_root)
        self.workspace = UIWorkspaceState()
        self.api_url = api_url
        self._lock = threading.RLock()
        self._voice_lock = threading.RLock()
        self._voice_thread: threading.Thread | None = None
        self._voice_stop_requested = threading.Event()
        self._voice_session: dict[str, Any] = self._new_voice_session()
        self._app_shell_voice_warmed = False
        self._booted = bool(getattr(self.runtime, "started", False))
        self.runtime.events.subscribe("*", self._on_runtime_event)

    @property
    def booted(self) -> bool:
        return self._booted

    def boot(self) -> None:
        with self._lock:
            if self._booted:
                self._ensure_app_shell_voice_warmup()
                return
            result = self.runtime.boot()
            self.workspace.add_chat_message("jarvis", result.message)
            for record in self.runtime.registry.enabled_records():
                self.workspace.set_agent_status(record.name, "registered")
            self.workspace.add_notice("Local app-shell API bridge initialized.")
            self._ensure_app_shell_voice_warmup(result)
            self.workspace.add_notice("Voice bridge ready: one-turn and sleep/wake controls are available.")
            self._booted = True

    def health(self) -> dict[str, Any]:
        return {
            "name": "Jarvis Ultimate Local API",
            "booted": self._booted,
            "api_url": self.api_url,
            "runtime_started": bool(getattr(self.runtime, "started", False)),
            "voice": self.voice_session_snapshot(),
        }

    def _ensure_app_shell_voice_warmup(self, boot_result: JarvisResult | None = None) -> None:
        """Warm STT/TTS before the app shell accepts voice conversation.

        ``JarvisRuntime.boot`` already performs this when
        JARVIS_VOICE_WARMUP_ON_BOOT=true.  The app shell still enforces a
        readiness gate so Tanner does not get a "ready" interface while the
        first voice turn is about to pay model-loading cost.
        """

        with self._voice_lock:
            if self._app_shell_voice_warmed:
                return
            self._voice_session.update(
                {
                    "warmup_complete": False,
                    "warmup_status": "Warming voice systems before conversation...",
                    "last_status": "Warming voice systems before conversation...",
                }
            )
        with self._lock:
            self.workspace.avatar.set_state("working", expression="focused", message="Warming voice systems before conversation...")
            self.workspace.add_notice("App shell is warming voice systems before conversation.")

        summary = ""
        if boot_result is not None:
            data = getattr(boot_result, "data", {}) if boot_result is not None else {}
            voice_warmup = data.get("voice_warmup", {}) if isinstance(data, dict) else {}
            summary = str(voice_warmup.get("summary") or "").strip() if isinstance(voice_warmup, dict) else ""

        if not summary:
            summary = self._warm_voice_managers_for_app_shell()

        with self._voice_lock:
            self._app_shell_voice_warmed = True
            self._voice_session.update(
                {
                    "warmup_complete": True,
                    "warmup_status": "Voice systems warmed and ready.",
                    "warmup_summary": summary,
                    "last_status": "Voice systems warmed and ready.",
                }
            )
        with self._lock:
            self.workspace.add_notice("Voice systems warmed and ready.")
            self.workspace.avatar.set_state("sleeping", expression="calm", message="Voice systems warmed and ready. Entering sleep/wake mode, sir.")

    def _warm_voice_managers_for_app_shell(self) -> str:
        lines = ["App-shell voice warmup:"]
        if bool(getattr(self.runtime.config, "voice_warmup_stt", True)):
            stt_warmup = getattr(self.runtime.stt_manager, "warmup", None)
            if callable(stt_warmup):
                try:
                    result = stt_warmup()
                    lines.append("STT: " + str(getattr(result, "message", result)))
                except Exception as exc:  # pragma: no cover - defensive warmup boundary
                    lines.append(f"STT: warmup failed: {exc}")
            else:
                lines.append("STT: warmup unavailable for this manager")
        else:
            lines.append("STT: skipped")

        if bool(getattr(self.runtime.config, "voice_warmup_tts", True)):
            tts_warmup = getattr(self.runtime.tts_manager, "warmup", None)
            if callable(tts_warmup):
                try:
                    result = tts_warmup()
                    if isinstance(result, TTSResult):
                        lines.append("TTS: " + result.message)
                    else:
                        lines.append("TTS: " + str(getattr(result, "message", result)))
                except Exception as exc:  # pragma: no cover - defensive warmup boundary
                    lines.append(f"TTS: warmup failed: {exc}")
            else:
                lines.append("TTS: warmup unavailable for this manager")
        else:
            lines.append("TTS: skipped")

        if bool(getattr(self.runtime.config, "voice_warmup_llm", False)):
            lines.append("LLM: skipped; LM Studio stays warm through normal command use")
        else:
            lines.append("LLM: skipped")
        return "\n".join(lines)

    def snapshot(self) -> dict[str, Any]:
        self.boot()
        with self._lock:
            snapshot = build_app_shell_snapshot(self.workspace, self.runtime, api_url=self.api_url, bridge_status="online")
            snapshot["voice"] = self.voice_session_snapshot()
            return snapshot

    def events(self) -> list[dict[str, Any]]:
        self.boot()
        with self._lock:
            return [event.to_dict() for event in list(self.workspace.events)]

    def handle_command(self, command: str) -> dict[str, Any]:
        command = str(command or "").strip()
        if not command:
            return api_error("Command cannot be empty.", status=400)

        self.boot()
        with self._lock:
            self.workspace.add_chat_message("user", command)
            self.workspace.avatar.set_state("thinking", expression="focused", message="Routing command from app shell...")

        chunks: list[str] = []

        def on_chunk(chunk: str) -> None:
            chunks.append(chunk)
            with self._lock:
                self.workspace.avatar.set_state("speaking", expression="active", message="Streaming response to app shell...")

        try:
            result = self.runtime.handle_command(command, stream_callback=on_chunk)
            response_text = "".join(chunks).strip() or result.message
            with self._lock:
                self.workspace.add_chat_message("jarvis", response_text)
                next_state = "idle" if result.success else "error"
                expression = "neutral" if result.success else "alert"
                message = "Ready, sir." if result.success else result.message
                self.workspace.avatar.set_state(next_state, expression=expression, message=message)
            return api_ok({"result": result.to_dict(), "response_text": response_text, "state": self.snapshot()}, message=result.message)
        except Exception as exc:  # pragma: no cover - defensive API boundary
            with self._lock:
                self.workspace.avatar.set_state("error", expression="alert", message=str(exc))
                self.workspace.add_chat_message("jarvis", f"App-shell API error, sir: {exc}")
            return api_error(f"Jarvis API command failed: {exc}", status=500, data={"state": self.snapshot()})

    def voice_session_snapshot(self) -> dict[str, Any]:
        with self._voice_lock:
            session = dict(self._voice_session)
            thread_alive = self._voice_thread.is_alive() if self._voice_thread is not None else False
            session["thread_alive"] = thread_alive
            if not thread_alive and session.get("running") and session.get("mode") != "idle":
                session["running"] = False
            return session

    def voice_status(self) -> dict[str, Any]:
        self.boot()
        return api_ok({"voice": self.voice_session_snapshot(), "state": self.snapshot()}, message="voice status")

    def start_voice_once(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        options = {
            "duration_seconds": _safe_float_or_none(payload.get("duration_seconds")),
            "mode": str(payload.get("mode") or "").strip() or None,
            "silence_seconds": _safe_float_or_none(payload.get("silence_seconds")),
            "speak": _safe_bool(payload.get("speak"), True),
        }
        return self._start_voice_thread("one_turn", self._run_voice_once_session, options)

    def start_sleep_wake(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        default_max_turns = _safe_int(getattr(self.runtime.config, "voice_always_listening_max_turns", 0), 0)
        max_turns = _safe_int(payload.get("max_turns", default_max_turns), default_max_turns)
        options = {
            "max_turns": max_turns,
            "active_timeout_seconds": _safe_float_or_none(payload.get("active_timeout_seconds")) or float(getattr(self.runtime.config, "voice_sleep_timeout_seconds", 45.0) or 45.0),
            "duration_seconds": _safe_float_or_none(payload.get("duration_seconds")),
            "mode": str(payload.get("mode") or getattr(self.runtime.config, "stt_listen_mode", "smart") or "smart").strip() or None,
            "silence_seconds": _safe_float_or_none(payload.get("silence_seconds")) or float(getattr(self.runtime.config, "stt_silence_seconds", 0.65) or 0.65),
            "speak": _safe_bool(payload.get("speak"), True),
        }
        return self._start_voice_thread("sleep_wake", self._run_sleep_wake_session, options)

    def stop_voice(self) -> dict[str, Any]:
        self.boot()
        self._voice_stop_requested.set()
        try:
            stop_message = self.runtime.tts_stop()
        except Exception as exc:  # pragma: no cover - defensive cleanup
            stop_message = f"TTS stop failed: {exc}"
        with self._lock:
            self.workspace.avatar.set_state("idle", expression="neutral", message="Voice stop requested. Finishing the current microphone turn...")
            self.workspace.add_notice("Voice stop requested from the app shell.")
        self._update_voice_session(stop_requested=True, last_status=stop_message)
        return api_ok({"voice": self.voice_session_snapshot(), "state": self.snapshot()}, message="Voice stop requested.")

    def _start_voice_thread(self, mode: str, target: Any, options: dict[str, Any]) -> dict[str, Any]:
        self.boot()
        self._ensure_app_shell_voice_warmup()
        with self._voice_lock:
            if self._voice_thread is not None and self._voice_thread.is_alive():
                return api_error("A Jarvis voice session is already running.", status=409, data={"voice": self.voice_session_snapshot()})
            self._voice_stop_requested.clear()
            self._voice_session = self._new_voice_session(mode=mode, options=options)
            self._voice_thread = threading.Thread(target=target, args=(options,), name=f"jarvis-app-shell-{mode}", daemon=True)
            self._voice_thread.start()
        with self._lock:
            if mode == "one_turn":
                self.workspace.avatar.set_state("listening", expression="focused", message="Listening for one voice turn...")
            else:
                self.workspace.avatar.set_state("sleeping", expression="calm", message="Sleep/wake mode is running. Say a wake phrase to activate Jarvis.")
            self.workspace.add_notice(f"Voice session started from app shell: {mode}.")
        return api_ok({"voice": self.voice_session_snapshot(), "state": self.snapshot()}, message=f"Started {mode} voice session.")

    def _new_voice_session(self, *, mode: str = "idle", options: dict[str, Any] | None = None) -> dict[str, Any]:
        now = _utc_now_iso()
        return {
            "mode": mode,
            "running": mode != "idle",
            "stop_requested": False,
            "started_at": now if mode != "idle" else "",
            "stopped_at": "",
            "turns_heard": 0,
            "turns_handled": 0,
            "turns_ignored": 0,
            "failures": 0,
            "last_transcript": "",
            "last_command": "",
            "last_response": "",
            "last_status": "Ready.",
            "last_error": "",
            "final_state": "idle",
            "warmup_complete": self._app_shell_voice_warmed if hasattr(self, "_app_shell_voice_warmed") else False,
            "warmup_status": "Voice systems warmed and ready." if getattr(self, "_app_shell_voice_warmed", False) else "Voice warmup has not run yet.",
            "warmup_summary": "",
            "options": options or {},
        }

    def _update_voice_session(self, **updates: Any) -> None:
        with self._voice_lock:
            self._voice_session.update(updates)

    def _finish_voice_session(self, *, final_state: str = "idle", status: str = "Voice session finished.", error: str = "") -> None:
        with self._voice_lock:
            self._voice_session.update(
                {
                    "running": False,
                    "stop_requested": self._voice_stop_requested.is_set(),
                    "stopped_at": _utc_now_iso(),
                    "final_state": final_state,
                    "last_status": status,
                    "last_error": error,
                }
            )
        with self._lock:
            state = "error" if error else final_state
            expression = "alert" if error else "neutral"
            self.workspace.avatar.set_state(state, expression=expression, message=error or status)
            self.workspace.add_notice(status if not error else error)

    def _set_voice_visual(self, status_message: str, *, state: str | None = None, expression: str | None = None) -> None:
        visual_state = state or classify_voice_status(status_message)
        with self._lock:
            self.workspace.avatar.set_state(visual_state, expression=expression, message=status_message)
        self._update_voice_session(last_status=status_message)

    def _run_voice_once_session(self, options: dict[str, Any]) -> None:
        chunks: list[str] = []
        transcript_seen = {"value": ""}

        def on_transcript(transcript: str) -> None:
            transcript_seen["value"] = transcript
            self._update_voice_session(last_transcript=transcript, turns_heard=1)
            with self._lock:
                self.workspace.add_chat_message("user", transcript)
                self.workspace.avatar.set_state("transcribing", expression="focused", message=f"Heard: {transcript}")

        def on_chunk(chunk: str) -> None:
            chunks.append(chunk)
            self._set_voice_visual("Jarvis is speaking...", state="speaking", expression="active")

        try:
            self._set_voice_visual("Listening through the microphone...", state="listening", expression="focused")
            result = self.runtime.voice_loop_once(
                duration_seconds=options.get("duration_seconds"),
                mode=options.get("mode"),
                silence_seconds=options.get("silence_seconds"),
                stream_callback=on_chunk,
                transcript_callback=on_transcript,
                speak=bool(options.get("speak", True)),
            )
            response_text = "".join(chunks).strip() or result.message
            if bool(options.get("speak", True)) and self.runtime.tts_manager.enabled and result.success:
                self._set_voice_visual("Jarvis is finishing speech playback...", state="speaking", expression="active")
                self.runtime.spoken_pipeline.wait_until_idle(timeout=120.0)
            handled = 1 if result.success else 0
            failures = 0 if result.success else 1
            self._update_voice_session(
                turns_handled=handled,
                failures=failures,
                last_command=result.data.get("transcript", transcript_seen["value"]),
                last_response=response_text,
            )
            with self._lock:
                if response_text:
                    self.workspace.add_chat_message("jarvis", response_text)
            final_state = "idle" if result.success else "error"
            self._finish_voice_session(final_state=final_state, status=result.message, error="" if result.success else result.message)
        except Exception as exc:  # pragma: no cover - defensive thread boundary
            self._update_voice_session(failures=int(self._voice_session.get("failures", 0)) + 1)
            self._finish_voice_session(final_state="error", status="Voice turn failed.", error=f"Voice turn failed: {exc}")

    def _run_sleep_wake_session(self, options: dict[str, Any]) -> None:
        max_turns = int(options.get("max_turns") or 0)
        infinite = max_turns <= 0
        turn_limit = max_turns if not infinite else 10**9
        active_timeout_seconds = float(options.get("active_timeout_seconds") or 45.0)
        duration_seconds = options.get("duration_seconds")
        mode = options.get("mode")
        silence_seconds = options.get("silence_seconds")
        speak = bool(options.get("speak", True))
        state = "asleep"
        idle_seconds = 0.0
        turns_heard = 0
        turns_handled = 0
        turns_ignored = 0
        failures = 0
        stopped_by = "voice_stop_requested"
        last_transcript = ""
        last_command = ""
        last_response = ""

        self.runtime.events.emit(
            "voice.app_shell_sleep_wake_started",
            source="app_shell",
            message="App-shell sleep/wake voice session started.",
            data={"max_turns": max_turns, "infinite": infinite, "active_timeout_seconds": active_timeout_seconds},
        )
        self._set_voice_visual("Sleep mode is active. Waiting for wake phrase...", state="sleeping", expression="calm")

        try:
            for turn_index in range(1, turn_limit + 1):
                if self._voice_stop_requested.is_set():
                    stopped_by = "voice_stop_requested"
                    break
                label = f"Listening for wake phrase ({turn_index})..." if state == "asleep" else f"Listening while awake ({turn_index})..."
                self._set_voice_visual(label, state="sleeping" if state == "asleep" else "listening", expression="calm" if state == "asleep" else "focused")
                stt_result = self.runtime.stt_manager.listen_once(duration_seconds=duration_seconds, mode=mode, silence_seconds=silence_seconds)
                transcript = (getattr(stt_result, "text", "") or "").strip()
                last_transcript = transcript
                if transcript:
                    turns_heard += 1
                    self._update_voice_session(turns_heard=turns_heard, last_transcript=transcript)
                    with self._lock:
                        self.workspace.add_chat_message("heard", transcript)
                        self.workspace.avatar.set_state("transcribing", expression="focused", message=f"Heard: {transcript}")
                if not getattr(stt_result, "success", False):
                    failures += 1
                    self._update_voice_session(failures=failures)
                    self._set_voice_visual(f"STT failed: {getattr(stt_result, 'error', '') or getattr(stt_result, 'message', '')}", state="error", expression="alert")
                    continue
                if not transcript:
                    turns_ignored += 1
                    self._update_voice_session(turns_ignored=turns_ignored)
                    if state == "awake":
                        idle_seconds += float(getattr(stt_result, "duration_seconds", None) or getattr(self.runtime.stt_manager, "start_timeout_seconds", 3.0) or 3.0)
                        if idle_seconds >= active_timeout_seconds:
                            state = "asleep"
                            idle_seconds = 0.0
                            self._set_voice_visual(f"No response for {active_timeout_seconds:.0f}s; returning to sleep mode.", state="sleeping")
                        else:
                            self._set_voice_visual("No speech detected while awake.", state="listening")
                    else:
                        self._set_voice_visual("No wake phrase heard; staying asleep.", state="sleeping", expression="calm")
                    continue
                idle_seconds = 0.0
                normalized_transcript = self.runtime._voice_loop_normalize_phrase(transcript)
                if self.runtime._voice_loop_phrase_matches(normalized_transcript, self.runtime._voice_loop_exit_phrases()):
                    stopped_by = "spoken_exit_phrase"
                    break

                if state == "asleep":
                    match = self.runtime.wake_word_manager.detect(transcript)
                    if not match.detected:
                        turns_ignored += 1
                        self._update_voice_session(turns_ignored=turns_ignored)
                        self._set_voice_visual("Wake phrase not detected; staying asleep.", state="sleeping", expression="calm")
                        continue
                    state = "awake"
                    command = (match.command or "").strip()
                    self._set_voice_visual(f"Wake detected: {match.wake_word}. Jarvis is awake.", state="listening")
                    if not command:
                        prompt = self.runtime.wake_word_manager.empty_response
                        if speak and self.runtime.tts_manager.enabled:
                            self._set_voice_visual("Jarvis is speaking...", state="speaking", expression="active")
                            self.runtime.tts_manager.say(prompt, play_audio=True)
                        self._update_voice_session(last_command="", last_response=prompt)
                        with self._lock:
                            self.workspace.add_chat_message("jarvis", prompt)
                        continue
                else:
                    if self.runtime._voice_loop_sleep_phrase_matches(normalized_transcript, self.runtime._voice_loop_sleep_phrases()):
                        state = "asleep"
                        message = "Sleep phrase detected; returning to sleep mode."
                        if speak and self.runtime.tts_manager.enabled:
                            self._set_voice_visual("Jarvis is speaking...", state="speaking", expression="active")
                            self.runtime.tts_manager.say("Going back to sleep, sir.", play_audio=True)
                        self._set_voice_visual(message, state="sleeping")
                        continue
                    match = self.runtime.wake_word_manager.detect(transcript)
                    command = (match.command or "").strip() if match.detected else transcript
                    if not command:
                        command = transcript

                command_normalized = self.runtime._voice_loop_normalize_phrase(command)
                if self.runtime._voice_loop_sleep_phrase_matches(command_normalized, self.runtime._voice_loop_sleep_phrases()):
                    state = "asleep"
                    if speak and self.runtime.tts_manager.enabled:
                        self._set_voice_visual("Jarvis is speaking...", state="speaking", expression="active")
                        self.runtime.tts_manager.say("Going back to sleep, sir.", play_audio=True)
                    self._set_voice_visual("Sleep phrase detected; returning to sleep mode.", state="sleeping")
                    continue
                if self.runtime._voice_loop_phrase_matches(command_normalized, self.runtime._voice_loop_exit_phrases()):
                    stopped_by = "spoken_exit_phrase"
                    break

                last_command = command
                self._update_voice_session(last_command=command)
                with self._lock:
                    self.workspace.add_chat_message("user", command)
                    self.workspace.avatar.set_state("thinking", expression="focused", message=f"Thinking about: {command}")
                chunks: list[str] = []

                def on_chunk(chunk: str) -> None:
                    chunks.append(chunk)
                    self._set_voice_visual("Jarvis is speaking...", state="speaking", expression="active")

                spoken_stream = None
                callback: Any = on_chunk
                if speak and self.runtime.tts_manager.enabled:
                    spoken_stream = self.runtime.spoken_pipeline.create_stream_adapter(on_chunk, enabled=True)
                    callback = spoken_stream
                chat_result = self.runtime.handle_command(command, stream_callback=callback)
                spoken_chunks = 0
                if spoken_stream is not None:
                    spoken_chunks = spoken_stream.finish(speak_remaining=bool(chat_result.success and chat_result.action == "llm_chat"))
                    self._set_voice_visual("Jarvis is finishing speech playback...", state="speaking", expression="active")
                    self.runtime.spoken_pipeline.wait_until_idle(timeout=120.0)
                response_text = "".join(chunks).strip() or chat_result.message
                last_response = response_text
                with self._lock:
                    self.workspace.add_chat_message("jarvis", response_text)
                if chat_result.success:
                    turns_handled += 1
                    self._update_voice_session(turns_handled=turns_handled, last_response=last_response)
                    self.runtime.events.emit(
                        "voice.app_shell_sleep_wake_turn_finished",
                        source="app_shell",
                        message="App-shell sleep/wake voice turn finished.",
                        data={"turn": turn_index, "transcript": transcript, "command": command, "spoken_chunks": spoken_chunks},
                    )
                    self._set_voice_visual("Ready for the next command, sir.", state="listening")
                else:
                    failures += 1
                    self._update_voice_session(failures=failures, last_response=response_text, last_error=chat_result.message)
                    self._set_voice_visual(f"Command failed: {chat_result.message}", state="error", expression="alert")

                self._update_voice_session(
                    turns_heard=turns_heard,
                    turns_handled=turns_handled,
                    turns_ignored=turns_ignored,
                    failures=failures,
                    last_transcript=last_transcript,
                    last_command=last_command,
                    last_response=last_response,
                )

            else:
                stopped_by = "max_turns"

            final_state = "sleeping" if not self._voice_stop_requested.is_set() and stopped_by != "spoken_exit_phrase" else "idle"
            status = (
                f"Sleep/wake voice session stopped. Heard {turns_heard}, handled {turns_handled}, "
                f"ignored {turns_ignored}, failures {failures}. Stop reason: {stopped_by}."
            )
            self.runtime.events.emit(
                "voice.app_shell_sleep_wake_stopped",
                source="app_shell",
                message=status,
                data={
                    "turns_heard": turns_heard,
                    "turns_handled": turns_handled,
                    "turns_ignored": turns_ignored,
                    "failures": failures,
                    "stopped_by": stopped_by,
                    "last_transcript": last_transcript,
                    "last_command": last_command,
                },
            )
            self._update_voice_session(
                turns_heard=turns_heard,
                turns_handled=turns_handled,
                turns_ignored=turns_ignored,
                failures=failures,
                last_transcript=last_transcript,
                last_command=last_command,
                last_response=last_response,
            )
            self._finish_voice_session(final_state=final_state, status=status)
        except Exception as exc:  # pragma: no cover - defensive thread boundary
            failures += 1
            self._update_voice_session(failures=failures)
            self._finish_voice_session(final_state="error", status="Sleep/wake voice session failed.", error=f"Sleep/wake voice session failed: {exc}")

    def _on_runtime_event(self, event: Any) -> None:
        with self._lock:
            self.workspace.apply_event(event)
            if str(getattr(event, "event_type", "")) in {"voice.speech_chunk_started", "voice.speaking_finished", "voice.tts_generated"}:
                self.workspace.avatar.set_state("speaking", expression="active", message=getattr(event, "message", "Jarvis is speaking..."))


def _json_bytes(payload: dict[str, Any] | list[Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")


def make_handler(api: LocalJarvisAPI) -> type[BaseHTTPRequestHandler]:
    class JarvisLocalAPIHandler(BaseHTTPRequestHandler):
        server_version = "JarvisLocalAPI/0.1.9a"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
            return

        def _send(self, payload: dict[str, Any] | list[Any], *, status: int = 200) -> None:
            body = _json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib hook
            self._send(api_ok(message="ok"))

        def do_GET(self) -> None:  # noqa: N802 - stdlib hook
            path = urlparse(self.path).path.rstrip("/") or "/"
            if path == "/api/health":
                self._send(api_ok(api.health(), message="online"))
                return
            if path == "/api/state":
                self._send(api_ok(api.snapshot(), message="state"))
                return
            if path == "/api/events":
                self._send(api_ok({"events": api.events()}, message="events"))
                return
            if path == "/api/voice/status":
                self._send(api.voice_status())
                return
            self._send(api_error("Unknown API route.", status=404), status=404)

        def do_POST(self) -> None:  # noqa: N802 - stdlib hook
            path = urlparse(self.path).path.rstrip("/") or "/"
            payload = self._read_json_body()
            if payload is None:
                self._send(api_error("Request body must be valid JSON.", status=400), status=400)
                return

            if path == "/api/command":
                command = str(payload.get("command", "")).strip() if isinstance(payload, dict) else ""
                response = api.handle_command(command)
                self._send(response, status=int(response.get("status", 200) if not response.get("success", True) else 200))
                return
            if path == "/api/voice/once":
                response = api.start_voice_once(payload if isinstance(payload, dict) else {})
                self._send(response, status=int(response.get("status", 200) if not response.get("success", True) else 200))
                return
            if path == "/api/voice/sleep-wake/start":
                response = api.start_sleep_wake(payload if isinstance(payload, dict) else {})
                self._send(response, status=int(response.get("status", 200) if not response.get("success", True) else 200))
                return
            if path == "/api/voice/stop":
                response = api.stop_voice()
                self._send(response, status=int(response.get("status", 200) if not response.get("success", True) else 200))
                return
            self._send(api_error("Unknown API route.", status=404), status=404)

        def _read_json_body(self) -> dict[str, Any] | list[Any] | None:
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw_body = self.rfile.read(length) if length > 0 else b"{}"
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError:
                return None
            return payload

    return JarvisLocalAPIHandler


def make_local_api_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    project_root: str | Path | None = None,
    runtime: JarvisRuntime | None = None,
) -> tuple[ThreadingHTTPServer, LocalJarvisAPI]:
    api_url = f"http://{host}:{port}"
    api = LocalJarvisAPI(runtime=runtime, project_root=project_root, api_url=api_url)
    server = ThreadingHTTPServer((host, port), make_handler(api))
    actual_host, actual_port = server.server_address[:2]
    api.api_url = f"http://{actual_host}:{actual_port}"
    return server, api


def run_local_api_server(*, host: str = "127.0.0.1", port: int = 8765, project_root: str | Path | None = None) -> None:
    server, api = make_local_api_server(host=host, port=port, project_root=project_root)
    api.boot()
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
