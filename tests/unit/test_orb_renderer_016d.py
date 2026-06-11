import unittest

from jarvis.ui.orb_renderer import (
    blend_hex,
    hex_to_rgb,
    orbital_ring_plan,
    particle_positions,
    renderer_capabilities,
    solid_orb_layers,
    state_orb_palette,
)
from jarvis.ui.themes import get_theme


class TestOrbRenderer016d(unittest.TestCase):
    def test_color_helpers_are_stable(self):
        self.assertEqual(hex_to_rgb("#00E5FF"), (0, 229, 255))
        blended = blend_hex("#000000", "#FFFFFF", 0.5)
        self.assertTrue(blended.startswith("#"))
        self.assertEqual(len(blended), 7)

    def test_solid_orb_layers_create_dimensional_core(self):
        theme = get_theme("jarvis_dark")
        layers = solid_orb_layers(100, "thinking", theme, layer_count=18)
        self.assertGreaterEqual(len(layers), 18)
        self.assertGreater(layers[0]["radius"], layers[-1]["radius"])
        self.assertIn("fill", layers[0])
        self.assertIn("offset_x", layers[-1])

    def test_state_palette_changes_for_speaking(self):
        theme = get_theme("jarvis_dark")
        sleeping = state_orb_palette("sleeping", theme)
        speaking = state_orb_palette("speaking", theme)
        self.assertNotEqual(sleeping["base"], speaking["base"])
        self.assertIn("highlight", speaking)

    def test_ring_and_particle_plans_are_bounded(self):
        rings = orbital_ring_plan(100, 45, 1.4)
        particles = particle_positions(99, 45, 1.4, 100)
        self.assertEqual(len(rings), 4)
        self.assertLessEqual(len(particles), 36)
        self.assertIn("rx", rings[0])
        self.assertIn("size", particles[0])

    def test_renderer_capabilities_describe_solid_orb(self):
        caps = renderer_capabilities()
        self.assertIn("solid_layered_orb", caps)
        self.assertIn("state_reactive_motion", caps)


if __name__ == "__main__":
    unittest.main()
