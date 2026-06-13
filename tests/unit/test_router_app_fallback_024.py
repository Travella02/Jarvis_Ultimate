from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.abilities.registry import AbilityRegistry
from jarvis.brain.intent_classifier import IntentClassifier
from jarvis.brain.router import JarvisRouter
from jarvis.core.events import EventBus
from jarvis.core.registry import AgentRegistry


class TestRouterAppFallback024(unittest.TestCase):
    def test_natural_pull_up_phrase_routes_to_app_agent(self) -> None:
        classifier = IntentClassifier()
        self.assertEqual(classifier.classify("Can you pull up Chrome?").intent, "app_control")

    def test_ability_registry_loads_app_closer(self) -> None:
        registry = AgentRegistry()
        registry.load_builtin_agents()
        abilities = AbilityRegistry()
        abilities.load_from_agent_registry(registry)
        self.assertIsNotNone(abilities.get("app_agent.app_closer"))

    def test_router_uses_ability_fallback_for_unclear_app_phrase(self) -> None:
        registry = AgentRegistry()
        registry.load_builtin_agents()
        abilities = AbilityRegistry()
        abilities.load_from_agent_registry(registry)
        router = JarvisRouter(registry=registry, events=EventBus(), ability_registry=abilities)
        result = router.handle("Could you open Google Chrome for me?", stream_callback=None)
        self.assertEqual(result.data["selected_agent"], "app_agent")


if __name__ == "__main__":
    unittest.main()
