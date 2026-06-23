from __future__ import annotations

import unittest

from jarvis.abilities.registry import AbilityRegistry
from jarvis.core.registry import AgentRegistry


class TestAbilityFramework030(unittest.TestCase):
    def test_ability_registry_builds_from_agent_manifests(self) -> None:
        agent_registry = AgentRegistry()
        agent_registry.load_builtin_agents()
        ability_registry = AbilityRegistry()
        ability_registry.load_from_agent_registry(agent_registry)

        names = ability_registry.names(enabled_only=True)
        self.assertIn("app_agent.launcher", names)
        self.assertIn("file_agent.file_search", names)
        self.assertIn("weather_agent.weather_lookup", names)
        self.assertGreaterEqual(ability_registry.count(enabled_only=True), 8)

    def test_ability_selection_uses_trigger_matching(self) -> None:
        agent_registry = AgentRegistry()
        agent_registry.load_builtin_agents()
        ability_registry = AbilityRegistry()
        ability_registry.load_from_agent_registry(agent_registry)

        selection = ability_registry.select_for_command("open VS Code", intent="app_control")
        self.assertIsNotNone(selection.ability)
        self.assertEqual(selection.ability.name, "app_agent.launcher")
        self.assertGreater(selection.confidence, 0.5)

    def test_permission_policy_separates_safe_confirm_and_external(self) -> None:
        agent_registry = AgentRegistry()
        agent_registry.load_builtin_agents()
        ability_registry = AbilityRegistry()
        ability_registry.load_from_agent_registry(agent_registry)

        safe = ability_registry.permission_decision("app_agent.launcher")
        self.assertTrue(safe.allowed)
        self.assertFalse(safe.needs_confirmation)

        file_write = ability_registry.permission_decision("file_agent.file_ops")
        self.assertFalse(file_write.allowed)
        self.assertTrue(file_write.needs_confirmation)

        weather = ability_registry.permission_decision("weather_agent.weather_lookup")
        self.assertFalse(weather.allowed)
        self.assertTrue(weather.needs_confirmation)


if __name__ == "__main__":
    unittest.main()
