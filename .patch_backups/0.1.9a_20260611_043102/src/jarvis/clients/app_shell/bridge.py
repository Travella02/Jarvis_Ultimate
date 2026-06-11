"""Framework-neutral bridge helpers for Jarvis's native app shell.

The app shell is the path toward the real Jarvis interface: HTML/CSS/JS for
smooth visuals, wrapped by Electron so the UI opens as a desktop app instead of
a browser tab.  This module deliberately keeps the Python side dependency-free
and serializable so the same snapshot can be served over the local API, written
to disk, or used by future UI clients.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from jarvis.ui.visual_state import available_visual_states, orb_profile_for_state, profile_summary
from jarvis.ui.workspace import UIWorkspaceState

APP_SHELL_VERSION = "0.1.9"
APP_SHELL_MODE = "electron_native_app_shell"
DEFAULT_API_URL = "http://127.0.0.1:8765"


def app_shell_capabilities() -> tuple[str, ...]:
    """Return the current app-shell capability list for tests/status panels."""

    return (
        "native_desktop_window",
        "html_css_js_renderer",
        "electron_shell_ready",
        "local_api_bridge",
        "state_reactive_orb",
        "smooth_state_transitions",
        "tkinter_fallback_preserved",
        "real_voice_once_control",
        "sleep_wake_voice_control",
        "voice_stop_control",
        "live_voice_session_status",
        "app_shell_voice_warmup_gate",
        "speaking_state_tracks_playback",
        "stable_voice_control_layout",
        "cinematic_main_interface_layout",
        "collapsible_diagnostics_drawer",
        "conversation_dock_chat_bubbles",
        "state_specific_orb_motion",
        "startup_readiness_status_strip",
    )


def app_shell_assets(project_root: str | Path | None = None) -> dict[str, str]:
    """Return important app-shell paths as strings.

    Keeping this centralized makes tests and launchers agree about where the
    Electron app lives without hard-coding paths in multiple places.
    """

    root = Path(project_root) if project_root else Path.cwd()
    shell_root = root / "app_shell"
    renderer_root = shell_root / "renderer"
    return {
        "shell_root": str(shell_root),
        "package_json": str(shell_root / "package.json"),
        "main_js": str(shell_root / "main.js"),
        "preload_js": str(shell_root / "preload.js"),
        "renderer_root": str(renderer_root),
        "index_html": str(renderer_root / "index.html"),
        "styles_css": str(renderer_root / "styles.css"),
        "renderer_js": str(renderer_root / "renderer.js"),
    }


def _runtime_summary(runtime: Any | None) -> dict[str, Any]:
    if runtime is None:
        return {
            "started": False,
            "llm_provider": "unknown",
            "llm_model": "unknown",
            "tts_provider": "unknown",
            "stt_provider": "unknown",
            "agent_count": 0,
            "agents": [],
        }

    registry = getattr(runtime, "registry", None)
    names: list[str] = []
    if registry is not None and hasattr(registry, "names"):
        try:
            names = list(registry.names(enabled_only=True))
        except Exception:  # pragma: no cover - defensive bridge boundary
            names = []

    return {
        "started": bool(getattr(runtime, "started", False)),
        "llm_provider": getattr(getattr(runtime, "llm_provider", None), "provider_name", "unknown"),
        "llm_model": getattr(getattr(runtime, "llm_provider", None), "model", "unknown"),
        "tts_provider": getattr(getattr(runtime, "tts_manager", None), "provider_name", "unknown"),
        "tts_enabled": bool(getattr(getattr(runtime, "tts_manager", None), "enabled", False)),
        "stt_provider": getattr(getattr(runtime, "stt_manager", None), "provider_name", "unknown"),
        "stt_enabled": bool(getattr(getattr(runtime, "stt_manager", None), "enabled", False)),
        "agent_count": len(names),
        "agents": names,
    }


def build_app_shell_snapshot(
    workspace: UIWorkspaceState | Mapping[str, Any] | None = None,
    runtime: Any | None = None,
    *,
    api_url: str = DEFAULT_API_URL,
    bridge_status: str = "offline",
) -> dict[str, Any]:
    """Build a JSON-serializable snapshot for the app shell.

    ``workspace`` can be a real ``UIWorkspaceState`` or an already-built
    snapshot mapping.  This keeps local API responses and future bridge writers
    using the same schema.
    """

    if workspace is None:
        workspace_snapshot = UIWorkspaceState().snapshot()
    elif hasattr(workspace, "snapshot"):
        workspace_snapshot = workspace.snapshot()  # type: ignore[assignment]
    else:
        workspace_snapshot = dict(workspace)

    avatar = dict(workspace_snapshot.get("avatar", {}))
    state = str(avatar.get("state", "idle"))
    profile = orb_profile_for_state(state)
    avatar["profile"] = profile_summary(profile)

    return {
        "app": {
            "name": "Jarvis Ultimate",
            "version": APP_SHELL_VERSION,
            "mode": APP_SHELL_MODE,
            "api_url": api_url,
            "bridge_status": bridge_status,
            "capabilities": list(app_shell_capabilities()),
        },
        "avatar": avatar,
        "runtime": _runtime_summary(runtime),
        "workspace": workspace_snapshot,
        "visual_states": list(available_visual_states()),
    }
