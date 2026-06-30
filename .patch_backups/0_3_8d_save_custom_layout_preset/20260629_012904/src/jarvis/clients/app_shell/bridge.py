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

APP_SHELL_VERSION = "0.3.8c4"
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
        "panel_visibility_controls",
        "orb_only_focus_mode",
        "auto_sleep_wake_startup",
        "state_color_palette_refinement",
        "dim_sleep_mode_motion",
        "constant_grey_sleep_mode",
        "holographic_transparent_panels",
        "blended_state_color_transitions",
        "voice_panel_overflow_fix",
        "continuous_js_orb_motion",
        "orb_speech_caption_typewriter",
        "true_orb_only_focus_mode",
        "edge_only_holographic_panels",
        "realistic_3d_orb_core",
        "soft_wake_sleep_brightness_ramp",
        "caption_timing_lock",
        "silent_natural_sleep_acknowledgement",
        "stable_ring_particle_geometry",
        "ability_registry_foundation",
        "safe_app_launcher_ability",
        "project_file_search_ability",
        "ui_action_cards",
        "test_safe_app_agent_dry_run",
        "registry_app_path_discovery",
        "app_shell_tool_response_tts_fallback",
        "thinking_state_purple_orb_fix",
        "background_app_index_warmup",
        "fast_known_app_alias_resolution",
        "llm_assisted_router_fallback_guard",
        "snipping_tool_fast_aliases",
        "general_app_discovery_speedup",
        "startup_app_index_warmup_fix",
        "discord_launch_path_fix",
        "fast_voice_caption_polling",
        "pre_speech_caption_staging",
        "verified_app_launches",
        "verified_app_closes",
        "manual_app_alias_learning",
        "stale_launcher_fallback_recovery",
        "manual_chat_scroll_preservation",
        "app_alias_teaching_router",
        "media_player_close_process_aliases",
        "multi_app_alias_management",
        "default_app_roles",
        "app_focus_existing_windows",
        "alias_forget_list_rename_commands",
        "long_term_memory_pipeline_foundation",
        "memory_agent_store_search_forget",
        "memory_context_injection",
        "project_handoff_file_maintained",
        "always_on_memory_tiers",
        "short_term_fact_memory",
        "daily_chat_archive_memory",
        "crash_safe_memory_writes",
        "memory_maintenance_foundation",
        "memory_auto_capture_candidate_review",
        "memory_candidate_queue",
        "memory_candidate_review_commands",
        "auto_short_term_memory_capture",
        "llm_ready_memory_tier_classification",
        "structured_entity_memory_foundation",
        "scalable_entity_type_registry",
        "entity_memory_context_injection",
        "entity_memory_humanized_responses",
        "entity_memory_forget_cleanup_guard",
        "entity_memory_forget_routing_guard",
        "entity_memory_merge_alias_correction",
        "typed_input_voice_parity",
        "typed_input_visual_hold",
        "humanized_memory_search_responses",
        "relationship_memory_graph",
        "relationship_memory_queries",
        "entity_phonetic_aliases",
        "relationship_label_normalization",
        "relationship_display_cleanup",
        "saas_ready_entity_relationship_edges",
        "memory_preferences_auto_remember_controls",
        "memory_policy_privacy_controls",
        "screen_setting_memory_policy_ready",
        "sensitive_memory_secure_vault_routing",
        "password_manager_agent_foundation",
        "normal_memory_secret_blocking",
        "sensitive_chat_archive_redaction",
        "sensitive_ui_history_redaction",
        "memory_review_panel",
        "ranked_memory_review_bullets",
        "spoken_memory_review_summary_control",
        "memory_log_hygiene_redaction",
        "memory_review_internal_label_cleanup",
        "memory_review_duplicate_relationship_cleanup",
        "dockable_workspace_panels",
        "resizable_workspace_panels",
        "persistent_panel_layouts",
        "floating_panel_popouts",
        "saved_workspace_layout_presets",
        "panel_lock_mode",
        "per_panel_layout_lock_buttons",
        "panel_header_no_overlap_guard",
        "panel_drag_placeholder_stabilization",
        "responsive_panel_resize_clamping",
        "floating_panel_viewport_bounds",
        "debounced_layout_resize_handler",
        "viewport_scaled_panel_restore",
        "last_active_panel_z_order",
        "floating_panel_content_containment",
        "runtime_panel_minimum_size_guard",
        "workspace_safe_area_panel_scaling",
        "maximize_restore_panel_ratio_preservation",
        "top_bar_overlap_prevention",
        "independent_panel_drag_freeze",
        "active_panel_only_drag_updates",
        "no_neighbor_panel_reflow_on_drag",
        "dom_geometry_panel_freeze",
        "post_drag_neighbor_snap_guard",
        "release_safe_panel_layout_restore",
        "panel_command_palette",
        "multi_monitor_panel_popouts",
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
            "ability_count": 0,
            "abilities": [],
        }

    registry = getattr(runtime, "registry", None)
    names: list[str] = []
    if registry is not None and hasattr(registry, "names"):
        try:
            names = list(registry.names(enabled_only=True))
        except Exception:  # pragma: no cover - defensive bridge boundary
            names = []

    ability_registry = getattr(runtime, "ability_registry", None)
    abilities: list[dict[str, Any]] = []
    if ability_registry is not None and hasattr(ability_registry, "to_list"):
        try:
            abilities = list(ability_registry.to_list(enabled_only=True))
        except Exception:  # pragma: no cover - defensive bridge boundary
            abilities = []

    long_term_memory = getattr(runtime, "long_term_memory", None)
    short_term_memory = getattr(runtime, "short_term_memory", None)
    short_term_facts = getattr(runtime, "short_term_facts", None)
    chat_archive = getattr(runtime, "chat_archive", None)
    memory_maintenance = getattr(runtime, "memory_maintenance", None)
    memory_candidates = getattr(runtime, "memory_candidates", None)
    entity_memory = getattr(runtime, "entity_memory", None)
    memory_preferences = getattr(runtime, "memory_preferences", None)
    secure_vault = getattr(runtime, "secure_vault", None)

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
        "ability_count": len(abilities),
        "abilities": abilities,
        "memory": {
            "short_term": short_term_memory.status() if short_term_memory is not None and hasattr(short_term_memory, "status") else {},
            "short_term_facts": short_term_facts.status() if short_term_facts is not None and hasattr(short_term_facts, "status") else {},
            "long_term": long_term_memory.status() if long_term_memory is not None and hasattr(long_term_memory, "status") else {},
            "chat_archive": chat_archive.status() if chat_archive is not None and hasattr(chat_archive, "status") else {},
            "candidates": memory_candidates.status() if memory_candidates is not None and hasattr(memory_candidates, "status") else {},
            "entities": entity_memory.status() if entity_memory is not None and hasattr(entity_memory, "status") else {},
            "preferences": memory_preferences.status() if memory_preferences is not None and hasattr(memory_preferences, "status") else {},
            "secure_vault": secure_vault.status() if secure_vault is not None and hasattr(secure_vault, "status") else {},
            "maintenance": memory_maintenance.status() if memory_maintenance is not None and hasattr(memory_maintenance, "status") else {},
        },
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
