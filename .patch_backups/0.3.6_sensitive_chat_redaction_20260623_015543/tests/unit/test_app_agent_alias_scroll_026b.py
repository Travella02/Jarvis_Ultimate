from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.agents.app_agent.agent import Agent as AppAgent
from jarvis.brain.intent_classifier import IntentClassifier
from jarvis.brain.router import JarvisRouter
from jarvis.core.events import EventBus
from jarvis.core.registry import AgentRegistry
from jarvis.tools.shared.app_discovery import AppAliasStore, AppCandidate, AppMatch, _process_names_for_candidate


class TestAppAgentAliasScroll026b(unittest.TestCase):
    def test_when_i_say_alias_command_routes_to_app_control(self) -> None:
        result = IntentClassifier().classify("Jarvis, when I say music, open Spotify")
        self.assertEqual(result.intent, "app_control")
        self.assertGreaterEqual(result.confidence, 0.9)

    def test_router_learns_manual_app_alias_instead_of_chatting(self) -> None:
        candidate = AppCandidate(name="spotify", path="C:/Spotify/Spotify.exe", launch_type="path", aliases=["spotify"], process_names=["Spotify.exe"])
        match = AppMatch(candidate, score=1.0, source="test", query="spotify")
        with TemporaryDirectory() as tmp, patch("jarvis.agents.app_agent.agent.resolve_app_target", return_value=match):
            registry = AgentRegistry()
            registry.load_builtin_agents()
            router = JarvisRouter(registry=registry, events=EventBus(), config=SimpleNamespace(project_root=Path(tmp)))
            result = router.handle("Jarvis, when I say music, open Spotify")
            aliases = AppAliasStore(tmp).load_aliases()

        self.assertTrue(result.success)
        self.assertEqual(result.data["selected_agent"], "app_agent")
        self.assertEqual(result.action, "learn_app_alias")
        self.assertIn("music", aliases)
        self.assertEqual(aliases["music"]["name"], "spotify")

    def test_learned_alias_beats_media_player_for_music(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            spotify_path = root / "Spotify.exe"
            spotify_path.write_text("fake spotify launcher", encoding="utf-8")
            spotify = AppCandidate(name="spotify", path=str(spotify_path), launch_type="path", aliases=["spotify"], process_names=["Spotify.exe"])
            AppAliasStore(root).save_alias("music", spotify, source="test")
            result = AppAgent().handle("open music", context={"config": SimpleNamespace(project_root=root), "dry_run": True})

        self.assertTrue(result.success)
        self.assertEqual(result.data["app_match"]["candidate"]["name"], "spotify")
        self.assertEqual(result.data["app_match"]["source"], "learned_alias")

    def test_media_player_close_has_safe_process_names(self) -> None:
        media = AppCandidate(name="media player", launch_type="aumid", path="Microsoft.ZuneMusic_8wekyb3d8bbwe!Microsoft.ZuneMusic", aliases=["music", "media player"], process_names=[])
        names = _process_names_for_candidate(media)
        self.assertTrue(any(name.lower() in {"microsoft.media.player.exe", "wmplayer.exe", "music.ui.exe"} for name in names))

    def test_renderer_preserves_manual_chat_scroll_position(self) -> None:
        renderer = (ROOT / "app_shell" / "renderer" / "renderer.js").read_text(encoding="utf-8")
        self.assertIn("function isNearScrollBottom", renderer)
        self.assertIn("preserveOrAutoScroll(els.chatLog", renderer)
        self.assertIn("chatPreviousScrollTop", renderer)


if __name__ == "__main__":
    unittest.main()
