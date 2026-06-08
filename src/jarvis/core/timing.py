"""Turn-level latency timing helpers for Jarvis.

The timer is intentionally tiny and dependency-free. It records named marks in
one user command turn so the CLI can show where latency is happening without
turning Jarvis into a heavy profiler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


@dataclass(slots=True)
class TimingMark:
    """A single timestamped timing mark within one Jarvis command turn."""

    name: str
    elapsed_ms: float
    delta_ms: float
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "elapsed_ms": round(self.elapsed_ms, 3),
            "delta_ms": round(self.delta_ms, 3),
            "data": self.data,
        }


class TurnTimer:
    """Records elapsed time for one user command turn."""

    def __init__(self, *, command: str = "") -> None:
        self.command = command
        self._start = perf_counter()
        self._last = self._start
        self.marks: list[TimingMark] = []
        self.mark("turn.start")

    def mark(self, name: str, **data: Any) -> TimingMark:
        now = perf_counter()
        mark = TimingMark(
            name=name,
            elapsed_ms=(now - self._start) * 1000,
            delta_ms=(now - self._last) * 1000,
            data={key: value for key, value in data.items() if value is not None},
        )
        self._last = now
        self.marks.append(mark)
        return mark

    @property
    def total_ms(self) -> float:
        if not self.marks:
            return 0.0
        return self.marks[-1].elapsed_ms

    def get_mark(self, name: str) -> TimingMark | None:
        for mark in self.marks:
            if mark.name == name:
                return mark
        return None

    def has_mark(self, name: str) -> bool:
        return self.get_mark(name) is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_preview": self.command[:120],
            "total_ms": round(self.total_ms, 3),
            "marks": [mark.to_dict() for mark in self.marks],
        }

    def summary_lines(self) -> list[str]:
        """Return readable CLI lines for the latest command timing."""
        lines = [f"Last command total: {self.total_ms:.1f} ms"]
        for mark in self.marks:
            extras = ""
            if mark.data:
                pairs = ", ".join(f"{key}={value}" for key, value in mark.data.items())
                extras = f" ({pairs})"
            lines.append(f"- {mark.name}: +{mark.delta_ms:.1f} ms / {mark.elapsed_ms:.1f} ms{extras}")

        prepare_finished = self.get_mark("lm_studio.prepare_finished")
        if prepare_finished:
            payload_bytes = prepare_finished.data.get("payload_bytes")
            prompt_chars = prepare_finished.data.get("prompt_chars")
            system_chars = prepare_finished.data.get("system_chars")
            user_chars = prepare_finished.data.get("user_chars")
            max_tokens = prepare_finished.data.get("max_tokens")
            api_mode = prepare_finished.data.get("api_mode")
            path = prepare_finished.data.get("path")
            reasoning = prepare_finished.data.get("reasoning")
            context_length = prepare_finished.data.get("context_length")
            mode_details = f", api_mode={api_mode}" if api_mode else ""
            if path:
                mode_details += f", path={path}"
            if reasoning:
                mode_details += f", reasoning={reasoning}"
            if context_length:
                mode_details += f", context_length={context_length}"
            lines.append(
                "LM Studio prompt payload: "
                f"{payload_bytes} bytes, {prompt_chars} prompt chars "
                f"(system={system_chars}, user={user_chars}), max_tokens={max_tokens}{mode_details}"
            )

        native_stats = self.get_mark("lm_studio.native_stats")
        if native_stats:
            stats = native_stats.data
            lines.append(
                "LM Studio native stats: "
                f"input_tokens={stats.get('input_tokens')}, "
                f"output_tokens={stats.get('total_output_tokens')}, "
                f"reasoning_tokens={stats.get('reasoning_output_tokens')}, "
                f"ttft={stats.get('time_to_first_token_seconds')}s, "
                f"tokens_per_second={stats.get('tokens_per_second')}"
            )

        request_start = self.get_mark("lm_studio.request_start")
        request_finish = self.get_mark("lm_studio.request_finished")
        first_chunk = self.get_mark("lm_studio.first_chunk")
        if request_start and request_finish:
            before_request = request_start.elapsed_ms
            request_time = max(0.0, request_finish.elapsed_ms - request_start.elapsed_ms)
            lines.append(f"Pre-LM Studio request time: {before_request:.1f} ms")
            if first_chunk:
                first_chunk_time = max(0.0, first_chunk.elapsed_ms - request_start.elapsed_ms)
                remaining_stream_time = max(0.0, request_finish.elapsed_ms - first_chunk.elapsed_ms)
                lines.append(f"LM Studio time to first streamed chunk: {first_chunk_time:.1f} ms")
                lines.append(f"LM Studio remaining stream time: {remaining_stream_time:.1f} ms")
            lines.append(f"LM Studio request/response time: {request_time:.1f} ms")
        elif request_start:
            lines.append(f"Pre-LM Studio request time: {request_start.elapsed_ms:.1f} ms")
            if first_chunk:
                first_chunk_time = max(0.0, first_chunk.elapsed_ms - request_start.elapsed_ms)
                lines.append(f"LM Studio time to first streamed chunk: {first_chunk_time:.1f} ms")
            lines.append("LM Studio request did not finish cleanly.")
        else:
            lines.append("No LM Studio request was recorded for the last command.")
        return lines


def format_timing_summary(timer: TurnTimer | None) -> str:
    """Format the latest timing summary for CLI output."""
    if timer is None:
        return "No command timing has been recorded yet. Send a normal message first, then run 'timing last'."
    return "\n".join(timer.summary_lines())
