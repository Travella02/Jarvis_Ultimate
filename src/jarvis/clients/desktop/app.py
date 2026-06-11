"""Desktop UI shell for Jarvis Ultimate.

0.1.6c moves Jarvis toward the intended "AI body" design: the orb becomes the
centerpiece of the interface, surrounding panels orbit the core, and a shared
visual-state engine controls the avatar's animation language.  The UI remains a
client/body attached to JarvisRuntime, so the core can still run headless.
"""

from __future__ import annotations

import math
from pathlib import Path
import threading
from typing import Any

from jarvis.core.lifecycle import JarvisRuntime
from jarvis.core.result import JarvisEvent
from jarvis.ui.components import format_workspace_card, panel_header, summarize_payload
from jarvis.ui.themes import get_theme, state_color, status_color
from jarvis.ui.visual_state import classify_voice_status, orb_profile_for_state
from jarvis.ui.workspace import UIWorkspaceState


class JarvisDesktopApp:
    """Desktop body for Jarvis.

    The desktop is a client/body attached to the same JarvisRuntime used by the
    CLI.  It can run the sleep/wake voice runtime in the background, update the
    avatar state from events, and show future drop-in panels through the
    UIWorkspaceState panel registry.
    """

    layout_mode = "central_orb_workspace"

    def __init__(self, *, runtime: JarvisRuntime | None = None, project_root: str | Path | None = None, theme_name: str | None = None) -> None:
        self.runtime = runtime or JarvisRuntime(project_root=project_root)
        self.workspace = UIWorkspaceState()
        self.theme = get_theme(theme_name or self._resolve_theme_name())
        self._tk: Any | None = None
        self._root: Any | None = None
        self._widgets: dict[str, Any] = {}
        self._command_lock = threading.Lock()
        self._voice_lock = threading.Lock()
        self._voice_thread: threading.Thread | None = None
        self._voice_stop_event: threading.Event | None = None
        self._voice_state_message = "Voice runtime is stopped."
        self._voice_response_active = False
        self._orb_tick = 0
        self._avatar_canvas_size = (500, 360)

        self.runtime.events.subscribe("*", self._on_runtime_event)

    def desktop_layout_mode(self) -> str:
        """Return the desktop layout mode for tests and future UI launchers."""

        return self.layout_mode

    def avatar_canvas_size(self) -> tuple[int, int]:
        """Return the central avatar canvas size."""

        return self._avatar_canvas_size

    def _resolve_theme_name(self) -> str:
        """Resolve the UI theme from the project .env or config/ui.yaml if present."""

        root = getattr(self.runtime.config, "project_root", Path.cwd())
        env_path = Path(root) / ".env"
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped.startswith("JARVIS_UI_THEME="):
                        return stripped.split("=", 1)[1].strip().strip('"').strip("'") or "jarvis_dark"
            except OSError:
                pass
        ui_yaml = Path(root) / "config" / "ui.yaml"
        if ui_yaml.exists():
            try:
                for line in ui_yaml.read_text(encoding="utf-8").splitlines():
                    if line.strip().startswith("theme:"):
                        return line.split(":", 1)[1].strip() or "jarvis_dark"
            except OSError:
                pass
        return "jarvis_dark"

    def boot(self) -> str:
        result = self.runtime.boot()
        self.workspace.add_chat_message("jarvis", result.message)
        self.workspace.add_notice("Jarvis desktop body initialized.")
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
        root.geometry("1440x900")
        root.minsize(1180, 740)
        root.configure(bg=self.theme["background"])
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        font = self.theme["font_family"]
        mono = self.theme["mono_font_family"]
        style.configure("Jarvis.TFrame", background=self.theme["background"])
        style.configure("Surface.TFrame", background=self.theme["surface"])
        style.configure("Panel.TFrame", background=self.theme["panel"], relief="flat")
        style.configure("Jarvis.TLabel", background=self.theme["background"], foreground=self.theme["text"], font=(font, 10))
        style.configure("Panel.TLabel", background=self.theme["panel"], foreground=self.theme["text"], font=(font, 10))
        style.configure("Muted.TLabel", background=self.theme["panel"], foreground=self.theme["muted"], font=(font, 9))
        style.configure("Accent.TLabel", background=self.theme["panel"], foreground=self.theme["accent"], font=(font, 12, "bold"))
        style.configure("Core.TLabel", background=self.theme["panel"], foreground=self.theme["accent"], font=(font, 14, "bold"))
        style.configure("Header.TLabel", background=self.theme["background"], foreground=self.theme["accent"], font=(font, 18, "bold"))
        style.configure("Jarvis.TButton", background=self.theme["surface_raised"], foreground=self.theme["text"], borderwidth=1, focusthickness=0)
        style.configure("Jarvis.TEntry", fieldbackground=self.theme["panel_alt"], foreground=self.theme["text"], insertcolor=self.theme["accent"])

        self._build_layout(root, ttk, mono)
        self.boot()
        self.refresh()
        root.after(160, self._periodic_refresh)
        root.mainloop()

    def _build_layout(self, root: Any, ttk: Any, mono_font: str) -> None:
        """Build the central-orb workspace layout.

        The orb is now the visual core.  Runtime, workspace, chat, and events are
        arranged around it so future panels can feel like they are opening around
        Jarvis rather than replacing him.
        """

        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(root, style="Jarvis.TFrame", padding=(18, 12, 18, 4))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="JARVIS ULTIMATE", style="Header.TLabel").pack(side="left")
        self._widgets["top_badge"] = ttk.Label(header, text="SYSTEM ONLINE", style="Jarvis.TLabel")
        self._widgets["top_badge"].pack(side="right")

        shell = ttk.Frame(root, style="Jarvis.TFrame", padding=(12, 8, 12, 12))
        shell.grid(row=1, column=0, sticky="nsew")
        shell.grid_columnconfigure(0, weight=3)
        shell.grid_columnconfigure(1, weight=5)
        shell.grid_columnconfigure(2, weight=3)
        shell.grid_rowconfigure(0, weight=1)

        left = ttk.Frame(shell, style="Surface.TFrame", padding=8)
        center = ttk.Frame(shell, style="Surface.TFrame", padding=8)
        right = ttk.Frame(shell, style="Surface.TFrame", padding=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        center.grid(row=0, column=1, sticky="nsew", padx=4)
        right.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        self._build_status_panel(left, ttk, mono_font)
        self._build_events_panel(left, ttk, mono_font)
        self._build_avatar_panel(center, ttk)
        self._build_chat_panel(center, ttk, mono_font)
        self._build_workspace_panel(right, ttk, mono_font)

    def _panel(self, parent: Any, ttk: Any, title: str, *, icon: str = "", fill: str = "both", expand: bool = True, pady: tuple[int, int] = (0, 10)) -> Any:
        outer = ttk.Frame(parent, style="Panel.TFrame", padding=2)
        outer.pack(fill=fill, expand=expand, pady=pady)
        header = ttk.Frame(outer, style="Panel.TFrame")
        header.pack(fill="x", padx=10, pady=(8, 0))
        ttk.Label(header, text=panel_header(title, icon), style="Accent.TLabel").pack(side="left", anchor="w")
        body = ttk.Frame(outer, style="Panel.TFrame", padding=10)
        body.pack(fill="both", expand=True)
        return body

    def _build_avatar_panel(self, parent: Any, ttk: Any) -> None:
        frame = self._panel(parent, ttk, "Jarvis Core", icon="◎", pady=(0, 10), expand=False)
        width, height = self._avatar_canvas_size
        canvas = self._tk.Canvas(frame, width=width, height=height, bg=self.theme["panel"], highlightthickness=0)
        canvas.pack(pady=(0, 8), fill="both", expand=True)
        state_label = ttk.Label(frame, text="State: sleeping", style="Core.TLabel")
        state_label.pack(anchor="center")
        message_label = ttk.Label(frame, text="Waiting for wake phrase.", style="Muted.TLabel", wraplength=470)
        message_label.pack(anchor="center", pady=(4, 0))

        controls = ttk.Frame(frame, style="Panel.TFrame")
        controls.pack(anchor="center", pady=(12, 0))
        ttk.Button(controls, text="Start Voice", command=self.start_voice_runtime, style="Jarvis.TButton").pack(side="left")
        ttk.Button(controls, text="Stop Voice", command=self.stop_voice_runtime, style="Jarvis.TButton").pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="Warm Up", command=self.warmup_voice_runtime, style="Jarvis.TButton").pack(side="left", padx=(8, 0))

        self._widgets["avatar_canvas"] = canvas
        self._widgets["avatar_state"] = state_label
        self._widgets["avatar_message"] = message_label

    def _build_status_panel(self, parent: Any, ttk: Any, mono_font: str) -> None:
        frame = self._panel(parent, ttk, "Runtime Status", icon="◆", pady=(0, 10))
        text = self._make_text(frame, height=22, font_family=mono_font)
        text.pack(fill="both", expand=True)
        self._widgets["status_text"] = text

    def _build_chat_panel(self, parent: Any, ttk: Any, mono_font: str) -> None:
        frame = self._panel(parent, ttk, "Conversation", icon="▰", pady=(0, 0))
        chat = self._make_text(frame, height=15, font_family=mono_font)
        chat.pack(fill="both", expand=True, pady=(0, 10))

        input_frame = ttk.Frame(frame, style="Panel.TFrame")
        input_frame.pack(fill="x")
        entry = ttk.Entry(input_frame, style="Jarvis.TEntry")
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _event: self.submit_command())
        button = ttk.Button(input_frame, text="Send", command=self.submit_command, style="Jarvis.TButton")
        button.pack(side="left", padx=(8, 0))
        self._widgets["chat_text"] = chat
        self._widgets["command_entry"] = entry

    def _build_workspace_panel(self, parent: Any, ttk: Any, mono_font: str) -> None:
        frame = self._panel(parent, ttk, "Workspace", icon="▣", pady=(0, 10))
        text = self._make_text(frame, height=27, font_family=mono_font)
        text.pack(fill="both", expand=True)
        self._widgets["workspace_text"] = text

    def _build_events_panel(self, parent: Any, ttk: Any, mono_font: str) -> None:
        frame = self._panel(parent, ttk, "Event Stream", icon="☰", pady=(0, 0))
        text = self._make_text(frame, height=16, font_family=mono_font)
        text.pack(fill="both", expand=True)
        self._widgets["events_text"] = text

    def _make_text(self, parent: Any, *, height: int, font_family: str | None = None) -> Any:
        text = self._tk.Text(
            parent,
            height=height,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            selectbackground=self.theme["accent_soft"],
            relief="flat",
            wrap="word",
            padx=10,
            pady=8,
            font=(font_family or self.theme["font_family"], 9),
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
            visual_state = classify_voice_status(message)
            expression = "alert" if visual_state == "error" else ("calm" if visual_state in {"sleeping", "wake_listening"} else "focused")
            self.workspace.avatar.set_state(visual_state, expression=expression, message=message)
            self.runtime.events.emit("ui.voice_status", source="desktop", message=message, data={"running": True, "state": visual_state})
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
            self._root.after(160, self._periodic_refresh)

    def _schedule_refresh(self) -> None:
        if self._root is not None:
            self._root.after(0, self.refresh)

    def refresh(self) -> None:
        if self._root is None:
            return
        self._orb_tick = (self._orb_tick + 1) % 360
        self._render_avatar()
        self._render_chat()
        self._render_status()
        self._render_workspace()
        self._render_events()
        badge = self._widgets.get("top_badge")
        if badge is not None:
            status = "VOICE ONLINE" if self.voice_runtime_running() else "DESKTOP ONLINE"
            badge.configure(text=status)

    def _render_avatar(self) -> None:
        canvas = self._widgets.get("avatar_canvas")
        if canvas is None:
            return
        canvas.delete("all")
        state = self.workspace.avatar.state
        profile = orb_profile_for_state(state)
        color = state_color(profile.state, self.theme)
        width, height = self._avatar_canvas_size
        center_x, center_y = width // 2, int(height * 0.48)
        tick = self._orb_tick
        phase = (tick / 360.0) * math.tau
        pulse = (math.sin(phase * max(profile.pulse_speed, 0.1)) + 1.0) / 2.0
        breathing = 1.0 + (0.055 * math.sin(phase * 0.7) if profile.breathing else 0.0)
        core_scale = profile.core_scale * breathing
        glow = int(10 + 18 * profile.glow_strength + pulse * 10)
        outer_radius = int((118 + pulse * 12) * core_scale)
        mid_radius = int((84 + pulse * 5) * core_scale)
        inner_radius = int((32 + pulse * 6) * core_scale)

        # Holographic grid behind the core.
        for y in range(40, height - 55, 28):
            canvas.create_line(40, y, width - 40, y, fill=self.theme["panel_glow"], width=1)
        for x in range(60, width - 48, 46):
            canvas.create_line(x, 48, x, height - 68, fill=self.theme["panel_glow"], width=1)

        # Soft pseudo-3D glow shells.
        for layer in range(5, 0, -1):
            radius = outer_radius + layer * glow
            outline = self.theme["accent_soft"] if layer > 2 else color
            canvas.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius, outline=outline, width=1)

        # Rotating orbital arcs. Tk arcs make the 2D fallback feel like a 3D renderer.
        ring_specs = [
            (outer_radius + 16, 84, 220, 3),
            (outer_radius - 4, 265, 170, 2),
            (mid_radius + 12, 35, 130, 2),
            (mid_radius - 8, 195, 110, 1),
        ]
        speed = max(profile.ring_speed, 0.1)
        for index, (radius, base_start, extent, ring_width) in enumerate(ring_specs):
            start = (base_start + tick * speed * (1.4 + index * 0.28)) % 360
            canvas.create_arc(
                center_x - radius,
                center_y - int(radius * (0.72 + index * 0.03)),
                center_x + radius,
                center_y + int(radius * (0.72 + index * 0.03)),
                start=start,
                extent=extent,
                outline=color if index % 2 == 0 else self.theme["accent_soft"],
                width=ring_width,
                style="arc",
            )

        # Glass sphere/body.
        canvas.create_oval(center_x - outer_radius, center_y - outer_radius, center_x + outer_radius, center_y + outer_radius, outline=color, width=3)
        canvas.create_oval(center_x - mid_radius, center_y - mid_radius, center_x + mid_radius, center_y + mid_radius, outline=self.theme["accent_soft"], width=2)
        canvas.create_oval(center_x - inner_radius, center_y - inner_radius, center_x + inner_radius, center_y + inner_radius, outline=color, width=4)
        canvas.create_oval(center_x - 15, center_y - 15, center_x + 15, center_y + 15, fill=self.theme["panel"], outline=color, width=3)

        # Orbiting particle sparks.
        particle_count = min(profile.particle_count, 28)
        for index in range(particle_count):
            angle = phase * speed + (math.tau * index / max(particle_count, 1))
            radius = outer_radius + 26 + (index % 4) * 8
            px = center_x + math.cos(angle) * radius
            py = center_y + math.sin(angle) * radius * 0.62
            size = 1 + (index % 3)
            canvas.create_oval(px - size, py - size, px + size, py + size, fill=color, outline="")

        # State text and future-renderer notice.
        canvas.create_text(center_x, height - 52, text=profile.label.upper(), fill=color, font=(self.theme["font_family"], 12, "bold"))
        canvas.create_text(center_x, height - 28, text="CENTRAL ORB RENDERER · 3D AVATAR READY", fill=self.theme["muted"], font=(self.theme["font_family"], 8))

        self._widgets["avatar_state"].configure(text=f"State: {profile.label}")
        self._widgets["avatar_message"].configure(text=self.workspace.avatar.message or "Ready, sir.")

    def _render_chat(self) -> None:
        lines = []
        for msg in self.workspace.chat_messages:
            prefix = "YOU" if msg["role"] == "user" else "JARVIS"
            lines.append(f"{prefix}: {msg['text']}")
        self._set_text("chat_text", "\n\n".join(lines))

    def _render_status(self) -> None:
        voice = "running" if self.voice_runtime_running() else "stopped"
        visual_profile = orb_profile_for_state(self.workspace.avatar.state)
        lines = [
            f"Layout: {self.layout_mode}",
            f"Orb state: {visual_profile.label}",
            f"Desktop voice runtime: {voice}",
            f"Voice status: {self._voice_state_message}",
            f"Auto-start voice: {getattr(self.runtime.config, 'desktop_auto_start_voice', True)}",
            f"LLM: {getattr(self.runtime.llm_provider, 'provider_name', 'unknown')} / {getattr(self.runtime.llm_provider, 'model', 'unknown')}",
            f"TTS: {self.runtime.tts_manager.provider_name} (enabled={self.runtime.tts_manager.enabled})",
            f"STT: {self.runtime.stt_manager.provider_name} (enabled={self.runtime.stt_manager.enabled})",
            f"Wake words: {', '.join(self.runtime.wake_word_manager.wake_words)}",
            f"Short-term memory turns: {self.runtime.short_term_memory.status().get('turns', 0)}",
            "",
            "Orb animation profile:",
            f"- ring speed: {visual_profile.ring_speed}",
            f"- pulse speed: {visual_profile.pulse_speed}",
            f"- glow: {visual_profile.glow_strength}",
            "",
            "Status colors:",
            f"- voice: {status_color(voice, self.theme)}",
            f"- avatar: {state_color(visual_profile.state, self.theme)}",
            "",
            "Agents:",
        ]
        for name in self.runtime.registry.names(enabled_only=True):
            lines.append(f"- {name}: {self.workspace.agent_status.get(name, 'registered')}")
        if self.workspace.notices:
            lines.append("")
            lines.append("Notices:")
            for notice in list(self.workspace.notices)[-5:]:
                lines.append(f"- {notice}")
        self._set_text("status_text", "\n".join(lines))

    def _render_workspace(self) -> None:
        lines = [
            "Drop-in workspace panels:",
        ]
        for panel in self.workspace.panel_summaries():
            marker = "OPEN" if panel["is_open"] else "READY"
            lines.append(f"- {panel['title']} ({panel['panel_id']}) [{marker}] type={panel['panel_type']}")

        lines.append("")
        lines.append("Future Jarvis tools can open panels around the central core with ui.open_panel events:")
        lines.append("- reminders")
        lines.append("- web results")
        lines.append("- generated images")
        lines.append("- file results")
        lines.append("- screen/OCR context")
        lines.append("- agent dashboards")
        lines.append("")
        lines.append("Design direction:")
        lines.append("- the orb stays central")
        lines.append("- tools open around Jarvis")
        lines.append("- panels remain drop-in/modular")

        if self.workspace.workspace_cards:
            lines.append("")
            lines.append("Workspace cards:")
            for card in self.workspace.workspace_cards:
                lines.append(format_workspace_card(card))

        open_dynamic = [panel for panel in self.workspace.open_panels() if panel.panel_id not in {"avatar", "status", "chat", "workspace", "events"}]
        if open_dynamic:
            lines.append("")
            lines.append("Open dynamic panels:")
            for panel in open_dynamic:
                lines.append(f"{panel.title}:")
                for preview in summarize_payload(panel.payload):
                    lines.append(f"  {preview}")
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
