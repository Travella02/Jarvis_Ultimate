"""Desktop UI shell for Jarvis Ultimate.

This is intentionally a lightweight, dependency-free Tkinter shell. It gives
Jarvis a first visual body/workspace while keeping the brain headless-capable.
Future UI panels can be added through the UIWorkspaceState/UIPanelRegistry
without rewriting the core runtime.
"""

from __future__ import annotations

from pathlib import Path
import threading
from typing import Any

from jarvis.core.lifecycle import JarvisRuntime
from jarvis.core.result import JarvisEvent
from jarvis.ui.themes import get_theme
from jarvis.ui.workspace import UIWorkspaceState


class JarvisDesktopApp:
    """First desktop body for Jarvis.

    The desktop is a client/body attached to the same JarvisRuntime used by the
    CLI. 0.1.6a adds a background sleep/wake voice runtime so the window can be
    Jarvis's normal always-ready interface instead of only a typed chat shell.
    """

    def __init__(self, *, runtime: JarvisRuntime | None = None, project_root: str | Path | None = None) -> None:
        self.runtime = runtime or JarvisRuntime(project_root=project_root)
        self.workspace = UIWorkspaceState()
        self.theme = get_theme()
        self._tk: Any | None = None
        self._root: Any | None = None
        self._widgets: dict[str, Any] = {}
        self._command_lock = threading.Lock()
        self._voice_lock = threading.Lock()
        self._voice_thread: threading.Thread | None = None
        self._voice_stop_event: threading.Event | None = None
        self._voice_state_message = "Voice runtime is stopped."
        self._voice_response_active = False

        self.runtime.events.subscribe("*", self._on_runtime_event)

    def boot(self) -> str:
        result = self.runtime.boot()
        self.workspace.add_chat_message("jarvis", result.message)
        self._hydrate_agent_status()
        if self._should_auto_start_voice():
            self.start_voice_runtime(auto=True)
        return result.message

    def run(self) -> None:
        """Run the Tkinter UI. Tkinter is imported lazily for testability."""

        import tkinter as tk
        from tkinter import ttk

        self._tk = tk
        root = tk.Tk()
        self._root = root
        root.title("Jarvis Ultimate")
        root.geometry("1180x760")
        root.configure(bg=self.theme["background"])
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Jarvis.TFrame", background=self.theme["background"])
        style.configure("Panel.TFrame", background=self.theme["panel"], relief="flat")
        style.configure("Jarvis.TLabel", background=self.theme["background"], foreground=self.theme["text"])
        style.configure("Panel.TLabel", background=self.theme["panel"], foreground=self.theme["text"])
        style.configure("Accent.TLabel", background=self.theme["panel"], foreground=self.theme["accent"], font=("Segoe UI", 12, "bold"))
        style.configure("Jarvis.TButton", background=self.theme["panel_alt"], foreground=self.theme["text"])

        self._build_layout(root, ttk)
        self.boot()
        self.refresh()
        root.after(500, self._periodic_refresh)
        root.mainloop()

    def _build_layout(self, root: Any, ttk: Any) -> None:
        root.grid_columnconfigure(0, weight=2)
        root.grid_columnconfigure(1, weight=4)
        root.grid_columnconfigure(2, weight=3)
        root.grid_rowconfigure(0, weight=1)

        left = ttk.Frame(root, style="Jarvis.TFrame", padding=10)
        center = ttk.Frame(root, style="Jarvis.TFrame", padding=10)
        right = ttk.Frame(root, style="Jarvis.TFrame", padding=10)
        left.grid(row=0, column=0, sticky="nsew")
        center.grid(row=0, column=1, sticky="nsew")
        right.grid(row=0, column=2, sticky="nsew")

        self._build_avatar_panel(left, ttk)
        self._build_status_panel(left, ttk)
        self._build_chat_panel(center, ttk)
        self._build_workspace_panel(right, ttk)
        self._build_events_panel(right, ttk)

    def _build_avatar_panel(self, parent: Any, ttk: Any) -> None:
        frame = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        frame.pack(fill="x", pady=(0, 10))
        ttk.Label(frame, text="JARVIS", style="Accent.TLabel").pack(anchor="w")
        canvas = self._tk.Canvas(frame, width=220, height=220, bg=self.theme["panel"], highlightthickness=0)
        canvas.pack(pady=8)
        state_label = ttk.Label(frame, text="State: sleeping", style="Panel.TLabel")
        state_label.pack(anchor="w")
        message_label = ttk.Label(frame, text="Waiting for wake phrase.", style="Panel.TLabel", wraplength=240)
        message_label.pack(anchor="w", pady=(4, 0))

        controls = ttk.Frame(frame, style="Panel.TFrame")
        controls.pack(fill="x", pady=(10, 0))
        ttk.Button(controls, text="Start Voice", command=self.start_voice_runtime, style="Jarvis.TButton").pack(side="left")
        ttk.Button(controls, text="Stop Voice", command=self.stop_voice_runtime, style="Jarvis.TButton").pack(side="left", padx=(6, 0))
        ttk.Button(controls, text="Warm Up", command=self.warmup_voice_runtime, style="Jarvis.TButton").pack(side="left", padx=(6, 0))

        self._widgets["avatar_canvas"] = canvas
        self._widgets["avatar_state"] = state_label
        self._widgets["avatar_message"] = message_label

    def _build_status_panel(self, parent: Any, ttk: Any) -> None:
        frame = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="STATUS", style="Accent.TLabel").pack(anchor="w")
        text = self._make_text(frame, height=18)
        text.pack(fill="both", expand=True, pady=(8, 0))
        self._widgets["status_text"] = text

    def _build_chat_panel(self, parent: Any, ttk: Any) -> None:
        frame = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="CHAT", style="Accent.TLabel").pack(anchor="w")
        chat = self._make_text(frame, height=28)
        chat.pack(fill="both", expand=True, pady=(8, 8))

        input_frame = ttk.Frame(frame, style="Panel.TFrame")
        input_frame.pack(fill="x")
        entry = ttk.Entry(input_frame)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _event: self.submit_command())
        button = ttk.Button(input_frame, text="Send", command=self.submit_command, style="Jarvis.TButton")
        button.pack(side="left", padx=(8, 0))
        self._widgets["chat_text"] = chat
        self._widgets["command_entry"] = entry

    def _build_workspace_panel(self, parent: Any, ttk: Any) -> None:
        frame = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        frame.pack(fill="both", expand=True, pady=(0, 10))
        ttk.Label(frame, text="WORKSPACE", style="Accent.TLabel").pack(anchor="w")
        text = self._make_text(frame, height=16)
        text.pack(fill="both", expand=True, pady=(8, 0))
        self._widgets["workspace_text"] = text

    def _build_events_panel(self, parent: Any, ttk: Any) -> None:
        frame = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="EVENTS", style="Accent.TLabel").pack(anchor="w")
        text = self._make_text(frame, height=14)
        text.pack(fill="both", expand=True, pady=(8, 0))
        self._widgets["events_text"] = text

    def _make_text(self, parent: Any, *, height: int) -> Any:
        text = self._tk.Text(
            parent,
            height=height,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            wrap="word",
        )
        text.configure(state="disabled")
        return text

    def _should_auto_start_voice(self) -> bool:
        return bool(getattr(self.runtime.config, "desktop_auto_start_voice", True)) and bool(
            getattr(self.runtime.config, "voice_always_listening_on_startup", False)
        )

    def voice_runtime_running(self) -> bool:
        thread = self._voice_thread
        return bool(thread and thread.is_alive())

    def start_voice_runtime(self, *, auto: bool = False) -> str:
        """Start the sleep/wake voice runtime in a background thread."""

        with self._voice_lock:
            if self.voice_runtime_running():
                message = "Voice runtime is already running, sir."
                if not auto:
                    self.workspace.add_chat_message("jarvis", message)
                    self._schedule_refresh()
                return message
            self._voice_stop_event = threading.Event()
            self._voice_state_message = "Starting sleep/wake voice runtime..."
            self.workspace.avatar.set_state("wake_listening", expression="calm", message="Starting voice runtime...")
            if not auto:
                self.workspace.add_chat_message("jarvis", "Starting voice runtime. I will wait in sleep mode for your wake phrase, sir.")
            else:
                self.workspace.add_chat_message("jarvis", "Desktop voice runtime is starting. I will wait in sleep mode for your wake phrase, sir.")
            self._voice_thread = threading.Thread(target=self._run_voice_runtime_thread, name="jarvis-desktop-voice", daemon=True)
            self._voice_thread.start()
            self._schedule_refresh()
            return "Voice runtime started."

    def stop_voice_runtime(self) -> str:
        """Request the background voice runtime to stop."""

        with self._voice_lock:
            if self._voice_stop_event is not None:
                self._voice_stop_event.set()
            running = self.voice_runtime_running()
        self.runtime.tts_stop()
        if running:
            message = "Stopping voice runtime after the current listen turn, sir."
        else:
            message = "Voice runtime is not running, sir."
        self._voice_state_message = message
        self.workspace.add_chat_message("jarvis", message)
        self.workspace.avatar.set_state("idle", expression="neutral", message=message)
        self._schedule_refresh()
        return message

    def warmup_voice_runtime(self) -> str:
        """Warm STT/TTS in the background so the UI stays responsive."""

        def warmup() -> None:
            self.workspace.avatar.set_state("working", expression="focused", message="Warming voice systems...")
            self._voice_state_message = "Warming voice systems..."
            self._schedule_refresh()
            try:
                summary = self.runtime.warmup_all()
                self.workspace.add_chat_message("jarvis", summary)
                self._voice_state_message = "Voice warmup complete."
                self.workspace.avatar.set_state("idle", expression="neutral", message="Voice warmup complete, sir.")
            except Exception as exc:  # pragma: no cover - defensive UI boundary
                self.workspace.add_chat_message("jarvis", f"Voice warmup failed, sir: {exc}")
                self.workspace.avatar.set_state("error", expression="alert", message=str(exc))
            finally:
                self._schedule_refresh()

        threading.Thread(target=warmup, name="jarvis-desktop-warmup", daemon=True).start()
        return "Voice warmup started."

    def _run_voice_runtime_thread(self) -> None:
        stop_event = self._voice_stop_event or threading.Event()
        self._voice_response_active = False

        def status_callback(message: str) -> None:
            self._voice_state_message = message
            lowered = message.lower()
            if "sleep" in lowered or "wake phrase" in lowered:
                self.workspace.avatar.set_state("wake_listening", expression="calm", message=message)
            elif "wake detected" in lowered or "awake" in lowered:
                self.workspace.avatar.set_state("listening", expression="active", message=message)
            elif "returning to sleep" in lowered:
                self.workspace.avatar.set_state("sleeping", expression="calm", message=message)
            elif "stt failed" in lowered or "failed" in lowered:
                self.workspace.avatar.set_state("error", expression="alert", message=message)
            else:
                self.workspace.avatar.set_state("listening", expression="focused", message=message)
            self.runtime.events.emit("ui.voice_status", source="desktop", message=message, data={"running": True})
            self._schedule_refresh()

        def transcript_callback(transcript: str) -> None:
            self._voice_response_active = False
            self.workspace.add_chat_message("user", transcript)
            self.workspace.avatar.set_state("transcribing", expression="focused", message="Heard voice input.")
            self._schedule_refresh()

        def stream_callback(chunk: str) -> None:
            if not self._voice_response_active:
                self.workspace.add_chat_message("jarvis", "")
                self._voice_response_active = True
            try:
                self.workspace.chat_messages[-1]["text"] += chunk
            except IndexError:  # pragma: no cover - defensive
                self.workspace.add_chat_message("jarvis", chunk)
            self.workspace.avatar.set_state("speaking", expression="active", message="Speaking response...")
            self._schedule_refresh()

        try:
            result = self.runtime.voice_sleep_wake_loop(
                max_turns=int(getattr(self.runtime.config, "voice_always_listening_max_turns", 0) or 0),
                active_timeout_seconds=float(getattr(self.runtime.config, "voice_sleep_timeout_seconds", 45.0) or 45.0),
                duration_seconds=None,
                mode=getattr(self.runtime.config, "stt_listen_mode", "smart"),
                silence_seconds=float(getattr(self.runtime.config, "stt_silence_seconds", 0.65) or 0.65),
                stream_callback=stream_callback,
                transcript_callback=transcript_callback,
                status_callback=status_callback,
                speak=True,
                stop_event=stop_event,
            )
            self._voice_state_message = result.message
            if result.data.get("final_state") == "asleep":
                self.workspace.avatar.set_state("sleeping", expression="calm", message=result.message)
            else:
                self.workspace.avatar.set_state("idle", expression="neutral", message=result.message)
            self.workspace.add_chat_message("jarvis", result.message)
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            self._voice_state_message = f"Voice runtime error: {exc}"
            self.workspace.avatar.set_state("error", expression="alert", message=str(exc))
            self.workspace.add_chat_message("jarvis", f"Voice runtime error, sir: {exc}")
        finally:
            self._voice_response_active = False
            self.runtime.events.emit("ui.voice_status", source="desktop", message=self._voice_state_message, data={"running": False})
            self._schedule_refresh()

    def submit_command(self) -> None:
        entry = self._widgets.get("command_entry")
        if entry is None:
            return
        command = entry.get().strip()
        if not command:
            return
        entry.delete(0, "end")
        normalized = command.lower()
        if normalized in {"start voice", "voice start", "start listening", "start always listening"}:
            self.start_voice_runtime()
            return
        if normalized in {"stop voice", "voice stop", "stop listening", "stop always listening", "exit voice mode"}:
            self.stop_voice_runtime()
            return
        if normalized in {"warmup", "warm up", "warmup all", "warm voice", "voice warmup"}:
            self.warmup_voice_runtime()
            return
        self.workspace.add_chat_message("user", command)
        self.workspace.avatar.set_state("thinking", expression="focused", message="Routing command...")
        self.refresh()

        thread = threading.Thread(target=self._run_command_thread, args=(command,), daemon=True)
        thread.start()

    def _run_command_thread(self, command: str) -> None:
        if not self._command_lock.acquire(blocking=False):
            self.workspace.add_chat_message("jarvis", "I am still working on the previous request, sir.")
            self._schedule_refresh()
            return
        try:
            chunks: list[str] = []

            def on_chunk(chunk: str) -> None:
                chunks.append(chunk)
                self.workspace.avatar.set_state("speaking", expression="active", message="Streaming response...")
                self._schedule_refresh()

            result = self.runtime.handle_command(command, stream_callback=on_chunk)
            response_text = "".join(chunks).strip() or result.message
            self.workspace.add_chat_message("jarvis", response_text)
            self.workspace.avatar.set_state("idle", expression="neutral", message="Ready, sir.")
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            self.workspace.avatar.set_state("error", expression="alert", message=str(exc))
            self.workspace.add_chat_message("jarvis", f"I ran into a desktop UI error, sir: {exc}")
        finally:
            self._command_lock.release()
            self._schedule_refresh()

    def _on_runtime_event(self, event: JarvisEvent) -> None:
        self.workspace.apply_event(event)
        self._schedule_refresh()

    def _hydrate_agent_status(self) -> None:
        for record in self.runtime.registry.enabled_records():
            self.workspace.set_agent_status(record.name, "registered")

    def _periodic_refresh(self) -> None:
        self.refresh()
        if self._root is not None:
            self._root.after(1000, self._periodic_refresh)

    def _schedule_refresh(self) -> None:
        if self._root is not None:
            self._root.after(0, self.refresh)

    def refresh(self) -> None:
        if self._root is None:
            return
        self._render_avatar()
        self._render_chat()
        self._render_status()
        self._render_workspace()
        self._render_events()

    def _render_avatar(self) -> None:
        canvas = self._widgets.get("avatar_canvas")
        if canvas is None:
            return
        canvas.delete("all")
        state = self.workspace.avatar.state
        colors = {
            "sleeping": "#155e75",
            "wake_listening": "#0891b2",
            "listening": "#22d3ee",
            "transcribing": "#60a5fa",
            "thinking": "#a78bfa",
            "speaking": "#34d399",
            "working": "#fbbf24",
            "error": "#fb7185",
            "idle": "#38bdf8",
        }
        color = colors.get(state, self.theme["accent"])
        canvas.create_oval(35, 35, 185, 185, outline=color, width=4)
        canvas.create_oval(65, 65, 155, 155, outline=self.theme["accent_soft"], width=2)
        canvas.create_text(110, 110, text="◉", fill=color, font=("Segoe UI", 40, "bold"))
        self._widgets["avatar_state"].configure(text=f"State: {self.workspace.avatar.label}")
        self._widgets["avatar_message"].configure(text=self.workspace.avatar.message or "Ready, sir.")

    def _render_chat(self) -> None:
        lines = []
        for msg in self.workspace.chat_messages:
            prefix = "You" if msg["role"] == "user" else "Jarvis"
            lines.append(f"{prefix}: {msg['text']}")
        self._set_text("chat_text", "\n\n".join(lines))

    def _render_status(self) -> None:
        lines = [
            f"Avatar: {self.workspace.avatar.label}",
            f"Desktop voice runtime: {'running' if self.voice_runtime_running() else 'stopped'}",
            f"Voice status: {self._voice_state_message}",
            f"Auto-start voice: {getattr(self.runtime.config, 'desktop_auto_start_voice', True)}",
            f"LLM: {getattr(self.runtime.llm_provider, 'provider_name', 'unknown')} / {getattr(self.runtime.llm_provider, 'model', 'unknown')}",
            f"TTS: {self.runtime.tts_manager.provider_name} (enabled={self.runtime.tts_manager.enabled})",
            f"STT: {self.runtime.stt_manager.provider_name} (enabled={self.runtime.stt_manager.enabled})",
            f"Wake words: {', '.join(self.runtime.wake_word_manager.wake_words)}",
            f"Short-term memory turns: {self.runtime.short_term_memory.status().get('turns', 0)}",
            "",
            "Agents:",
        ]
        for name in self.runtime.registry.names(enabled_only=True):
            lines.append(f"- {name}: {self.workspace.agent_status.get(name, 'registered')}")
        self._set_text("status_text", "\n".join(lines))

    def _render_workspace(self) -> None:
        lines = ["Drop-in panels:"]
        for panel in self.workspace.panel_registry.all():
            state = "open" if self.workspace.panels.get(panel.panel_id, None) and self.workspace.panels[panel.panel_id].is_open else "closed"
            lines.append(f"- {panel.title} ({panel.panel_id}) [{state}]")
        lines.append("")
        lines.append("Future Jarvis tools can open panels with ui.open_panel events:")
        lines.append("- reminders")
        lines.append("- web results")
        lines.append("- generated images")
        lines.append("- file results")
        lines.append("- screen/OCR context")
        lines.append("- agent dashboards")
        if self.workspace.workspace_cards:
            lines.append("")
            lines.append("Workspace cards:")
            for card in self.workspace.workspace_cards:
                lines.append(f"- {card['title']} ({card['type']})")
        self._set_text("workspace_text", "\n".join(lines))

    def _render_events(self) -> None:
        lines = []
        for event in list(self.workspace.events)[-30:]:
            lines.append(f"{event.timestamp} | {event.event_type} | {event.source} | {event.message}")
        self._set_text("events_text", "\n".join(lines))

    def _set_text(self, key: str, value: str) -> None:
        widget = self._widgets.get(key)
        if widget is None:
            return
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")
        widget.see("end")

    def _on_close(self) -> None:
        self.stop_voice_runtime()
        if self._root is not None:
            self._root.after(150, self._root.destroy)


def main() -> None:
    app = JarvisDesktopApp()
    app.run()


if __name__ == "__main__":
    main()
