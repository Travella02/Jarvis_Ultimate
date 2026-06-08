"""Spoken response pipeline for non-blocking Jarvis voice output.

0.0.8 keeps speech output outside the brain. The CLI can stream text to the
user while this pipeline extracts speakable sentence chunks and hands them to
TTS on a background worker thread.
"""

from __future__ import annotations

import queue
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from jarvis.core.events import EventBus
from jarvis.providers.tts.base import TTSResult


DisplayCallback = Callable[[str], None]
_SENTENCE_ENDINGS = {".", "!", "?", "…"}
_CLOSING_QUOTES = {'"', "'", ")", "]", "}"}
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(slots=True)
class SpokenChunk:
    """A queued chunk of assistant text to speak."""

    text: str
    source: str = "assistant_response"
    created_at: float = field(default_factory=time.perf_counter)


@dataclass(slots=True)
class SpokenPipelineStats:
    """Runtime counters for spoken response diagnostics."""

    queued: int = 0
    completed: int = 0
    failed: int = 0
    dropped: int = 0
    last_message: str = ""
    last_provider: str = ""
    last_elapsed_ms: float = 0.0


class SpokenResponsePipeline:
    """Background TTS queue used for normal Jarvis spoken responses."""

    def __init__(
        self,
        tts_manager: Any,
        *,
        events: EventBus | None = None,
        chunk_max_chars: int = 320,
        queue_max_size: int = 12,
        play_audio: bool = True,
    ) -> None:
        self.tts_manager = tts_manager
        self.events = events or EventBus()
        self.chunk_max_chars = max(80, int(chunk_max_chars or 320))
        self.queue_max_size = max(1, int(queue_max_size or 12))
        self.play_audio = bool(play_audio)
        self._queue: queue.Queue[SpokenChunk | None] = queue.Queue(maxsize=self.queue_max_size)
        self._thread: threading.Thread | None = None
        self._shutdown = threading.Event()
        self._lock = threading.Lock()
        self._active_chunk: SpokenChunk | None = None
        self._active = False
        self.stats = SpokenPipelineStats()
        self.last_result: TTSResult | None = None

    def enqueue_text(self, text: str, *, source: str = "assistant_response") -> int:
        """Split and enqueue text for background speech."""
        chunks = split_text_for_tts(text, max_chars=self.chunk_max_chars)
        count = 0
        for chunk in chunks:
            if self.enqueue_chunk(chunk, source=source):
                count += 1
        return count

    def enqueue_chunk(self, text: str, *, source: str = "assistant_response") -> bool:
        """Enqueue one chunk. Drops the oldest pending chunk if the queue is full."""
        clean = normalize_tts_text(text)
        if not clean:
            return False
        self._ensure_worker()
        item = SpokenChunk(text=clean, source=source)
        try:
            self._queue.put_nowait(item)
        except queue.Full:
            try:
                dropped = self._queue.get_nowait()
                self._queue.task_done()
                if dropped is not None:
                    self.stats.dropped += 1
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(item)
            except queue.Full:
                self.stats.dropped += 1
                return False
        self.stats.queued += 1
        self.events.emit("voice.queue_chunk_added", source="tts.pipeline", message="Spoken response chunk queued.", data={"chars": len(clean), "queue_size": self.pending_count()})
        return True

    def create_stream_adapter(self, display_callback: DisplayCallback | None = None, *, enabled: bool = True) -> "SpokenStreamAdapter":
        """Create an LLM stream callback that also queues sentence chunks."""
        return SpokenStreamAdapter(
            pipeline=self,
            display_callback=display_callback,
            enabled=enabled,
            max_chars=self.chunk_max_chars,
        )

    def stop(self, *, clear_pending: bool = True) -> int:
        """Stop queued speech as much as the current platform/provider allows."""
        removed = 0
        if clear_pending:
            removed = self._clear_pending()
        stop_method = getattr(self.tts_manager, "stop_playback", None)
        if callable(stop_method):
            stop_method()
        self.events.emit("voice.queue_stopped", source="tts.pipeline", message="Spoken response queue stopped.", data={"removed": removed})
        return removed

    def shutdown(self) -> None:
        """Request worker shutdown. Used by CLI exit/tests."""
        self._shutdown.set()
        self.stop(clear_pending=True)
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            self._clear_pending()
            self._queue.put_nowait(None)
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=1.0)

    def pending_count(self) -> int:
        return self._queue.qsize()

    def is_active(self) -> bool:
        with self._lock:
            return bool(self._active)

    def wait_until_idle(self, timeout: float = 10.0) -> bool:
        """Block until pending/background speech finishes. Intended for tests/manual diagnostics."""
        end = time.perf_counter() + timeout
        while time.perf_counter() < end:
            if self.pending_count() == 0 and not self.is_active():
                return True
            time.sleep(0.025)
        return self.pending_count() == 0 and not self.is_active()

    def status(self) -> str:
        """Return user-facing queue diagnostics."""
        active = self._active_chunk.text if self._active_chunk else ""
        lines = [
            "Spoken response pipeline status:",
            f"- auto speak: {bool(getattr(self.tts_manager, 'auto_speak', False))}",
            f"- playback: {bool(getattr(self.tts_manager, 'playback', False))}",
            f"- provider: {getattr(self.tts_manager, 'provider_name', 'unknown')}",
            f"- pending chunks: {self.pending_count()}",
            f"- active: {self.is_active()}",
            f"- queued total: {self.stats.queued}",
            f"- completed: {self.stats.completed}",
            f"- failed: {self.stats.failed}",
            f"- dropped: {self.stats.dropped}",
        ]
        if active:
            lines.append(f"- speaking now: {active[:80]}")
        if self.stats.last_message:
            lines.append(f"- last result: {self.stats.last_message}")
        if self.stats.last_provider:
            lines.append(f"- last provider: {self.stats.last_provider}")
        if self.stats.last_elapsed_ms:
            lines.append(f"- last TTS time: {self.stats.last_elapsed_ms:.1f} ms")
        return "\n".join(lines)

    def _ensure_worker(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._shutdown.clear()
        self._thread = threading.Thread(target=self._worker_loop, name="jarvis-tts-worker", daemon=True)
        self._thread.start()

    def _worker_loop(self) -> None:
        while not self._shutdown.is_set():
            item = self._queue.get()
            if item is None:
                self._queue.task_done()
                break
            with self._lock:
                self._active = True
                self._active_chunk = item
            started = time.perf_counter()
            self.events.emit("voice.speech_chunk_started", source="tts.pipeline", message="Speech chunk started.", data={"chars": len(item.text), "source": item.source})
            try:
                result = self.tts_manager.say(item.text, play_audio=self.play_audio)
                elapsed_ms = (time.perf_counter() - started) * 1000.0
                self.last_result = result
                self.stats.last_message = result.message
                self.stats.last_provider = result.provider
                self.stats.last_elapsed_ms = elapsed_ms
                if result.success:
                    self.stats.completed += 1
                    self.events.emit(
                        "voice.speech_chunk_finished",
                        source="tts.pipeline",
                        message="Speech chunk finished.",
                        data={"provider": result.provider, "played": result.played, "elapsed_ms": elapsed_ms},
                    )
                else:
                    self.stats.failed += 1
                    self.events.emit("voice.speech_chunk_failed", source="tts.pipeline", message=result.message, data={"error": result.error or result.message})
            except Exception as exc:  # Keep always-running Jarvis alive if TTS fails.
                elapsed_ms = (time.perf_counter() - started) * 1000.0
                self.stats.failed += 1
                self.stats.last_message = f"TTS worker failed: {exc}"
                self.stats.last_elapsed_ms = elapsed_ms
                self.events.emit("voice.speech_chunk_failed", source="tts.pipeline", message=str(exc), data={"exception_type": type(exc).__name__})
            finally:
                with self._lock:
                    self._active = False
                    self._active_chunk = None
                self._queue.task_done()

    def _clear_pending(self) -> int:
        removed = 0
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            self._queue.task_done()
            if item is not None:
                removed += 1
        return removed


class SpokenStreamAdapter:
    """LLM stream callback that prints text and queues speech by sentence."""

    def __init__(self, *, pipeline: SpokenResponsePipeline, display_callback: DisplayCallback | None = None, enabled: bool = True, max_chars: int = 320) -> None:
        self.pipeline = pipeline
        self.display_callback = display_callback
        self.enabled = enabled
        self.max_chars = max_chars
        self._buffer = ""
        self.enqueued_chunks = 0
        self.total_chars = 0
        self.closed = False

    def __call__(self, chunk: str) -> None:
        text = str(chunk or "")
        if self.display_callback is not None:
            self.display_callback(text)
        if not self.enabled or self.closed:
            return
        self.total_chars += len(text)
        self._buffer += text
        ready, remainder = extract_ready_tts_chunks(self._buffer, max_chars=self.max_chars, force=False)
        self._buffer = remainder
        for piece in ready:
            if self.pipeline.enqueue_chunk(piece, source="llm_stream"):
                self.enqueued_chunks += 1

    def finish(self, *, speak_remaining: bool = True) -> int:
        """Flush any final partial sentence after the LLM response ends."""
        if self.closed:
            return self.enqueued_chunks
        self.closed = True
        if self.enabled and speak_remaining:
            ready, remainder = extract_ready_tts_chunks(self._buffer, max_chars=self.max_chars, force=True)
            self._buffer = remainder
            for piece in ready:
                if self.pipeline.enqueue_chunk(piece, source="llm_stream_final"):
                    self.enqueued_chunks += 1
        else:
            self._buffer = ""
        return self.enqueued_chunks

    def cancel(self) -> None:
        self.closed = True
        self._buffer = ""


def normalize_tts_text(text: str) -> str:
    """Normalize streamed text into a clean speakable line."""
    return _WHITESPACE_RE.sub(" ", str(text or "")).strip()


def split_text_for_tts(text: str, *, max_chars: int = 320) -> list[str]:
    """Split response text into sentence-ish chunks suitable for TTS."""
    ready, remainder = extract_ready_tts_chunks(text, max_chars=max_chars, force=True)
    if remainder.strip():
        ready.append(normalize_tts_text(remainder))
    return [chunk for chunk in ready if chunk]


def extract_ready_tts_chunks(text: str, *, max_chars: int = 320, force: bool = False) -> tuple[list[str], str]:
    """Return speakable chunks that are ready plus an unsent remainder.

    During streaming, a chunk becomes ready at a sentence boundary or when it
    grows beyond ``max_chars``. On final flush, the remaining partial sentence is
    also returned.
    """
    buffer = str(text or "")
    chunks: list[str] = []
    max_chars = max(80, int(max_chars or 320))

    while buffer:
        boundary = _find_sentence_boundary(buffer)
        if boundary < 0 and len(buffer) > max_chars:
            boundary = _find_soft_boundary(buffer, max_chars)
        if boundary < 0:
            break
        piece = normalize_tts_text(buffer[:boundary])
        if piece:
            chunks.append(piece)
        buffer = buffer[boundary:].lstrip()

    if force and buffer.strip():
        while len(buffer) > max_chars:
            boundary = _find_soft_boundary(buffer, max_chars)
            piece = normalize_tts_text(buffer[:boundary])
            if piece:
                chunks.append(piece)
            buffer = buffer[boundary:].lstrip()
        final = normalize_tts_text(buffer)
        if final:
            chunks.append(final)
        buffer = ""

    return chunks, buffer


def _find_sentence_boundary(text: str) -> int:
    for index, char in enumerate(text):
        if char not in _SENTENCE_ENDINGS:
            continue
        end = index + 1
        while end < len(text) and text[end] in _CLOSING_QUOTES:
            end += 1
        if end >= len(text) or text[end].isspace():
            return end
    return -1


def _find_soft_boundary(text: str, max_chars: int) -> int:
    window = text[: max_chars + 1]
    for marker in ("; ", ": ", ", ", " - ", " "):
        index = window.rfind(marker)
        if index >= max_chars // 2:
            return index + len(marker)
    return min(len(text), max_chars)
