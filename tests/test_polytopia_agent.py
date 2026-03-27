"""
Tests for the Polytopia Strategy package.

Run with:
    python -m pytest tests/ -v
"""

import subprocess
import sys
import unittest
from pathlib import Path

# Make sure the project root is on the path when running tests directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strategy.tribes import get_tribe, list_tribe_names, TRIBES
from strategy.advisor import GameState, StrategyAdvisor, Recommendation
from strategy.image_analyzer import ImageAnalyzer, analyze_image


# ──────────────────────────────────────────────────────────────────────────
# Tribe data tests
# ──────────────────────────────────────────────────────────────────────────

class TestTribes(unittest.TestCase):

    def test_all_tribes_present(self):
        """At least the 13 known Polytopia tribes should be defined."""
        self.assertGreaterEqual(len(TRIBES), 13)

    def test_get_tribe_exact(self):
        tribe = get_tribe("bardur")
        self.assertIsNotNone(tribe)
        self.assertEqual(tribe.name, "Bardur")

    def test_get_tribe_case_insensitive(self):
        tribe = get_tribe("BARDUR")
        self.assertIsNotNone(tribe)
        self.assertEqual(tribe.name, "Bardur")

    def test_get_tribe_with_spaces(self):
        tribe = get_tribe("Ai Mo")
        self.assertIsNotNone(tribe)
        self.assertEqual(tribe.name, "Ai-Mo")

    def test_get_tribe_hyphenated(self):
        tribe = get_tribe("ai-mo")
        self.assertIsNotNone(tribe)

    def test_get_tribe_unknown(self):
        self.assertIsNone(get_tribe("nonexistent_tribe"))

    def test_list_tribe_names_sorted(self):
        names = list_tribe_names()
        self.assertEqual(names, sorted(names))
        self.assertIn("Bardur", names)
        self.assertIn("Oumaji", names)

    def test_tribe_fields_populated(self):
        """Every tribe should have required string fields filled."""
        for key, tribe in TRIBES.items():
            with self.subTest(tribe=key):
                self.assertTrue(tribe.name, f"{key} missing name")
                self.assertTrue(tribe.terrain, f"{key} missing terrain")
                self.assertTrue(tribe.starting_unit, f"{key} missing starting_unit")
                self.assertGreater(tribe.starting_stars, 0,
                                   f"{key} starting_stars must be > 0")
                self.assertTrue(tribe.strategy_notes,
                                f"{key} missing strategy_notes")

    def test_tribe_luxidoor_no_starting_tech(self):
        """Luxidoor's unique trait: no starting tech."""
        tribe = get_tribe("luxidoor")
        self.assertIsNone(tribe.starting_tech)
        self.assertEqual(tribe.starting_stars, 10)

    def test_tribe_vengir_starts_with_swordsman(self):
        tribe = get_tribe("vengir")
        self.assertEqual(tribe.starting_unit, "Swordsman")


# ──────────────────────────────────────────────────────────────────────────
# Advisor tests
# ──────────────────────────────────────────────────────────────────────────

class TestStrategyAdvisor(unittest.TestCase):

    def _make_state(self, **kwargs) -> GameState:
        defaults = dict(
            tribe_name="bardur", turn=1, stars=5, cities=1,
            city_level=1, opponent_distance=5, nearby_resources=[],
        )
        defaults.update(kwargs)
        return GameState(**defaults)

    def test_invalid_tribe_raises(self):
        with self.assertRaises(ValueError):
            StrategyAdvisor(self._make_state(tribe_name="fake_tribe"))

    def test_recommend_returns_list(self):
        state = self._make_state()
        advisor = StrategyAdvisor(state)
        recs = advisor.recommend()
        self.assertIsInstance(recs, list)
        self.assertGreater(len(recs), 0)

    def test_recommendations_are_sorted_by_priority(self):
        state = self._make_state(nearby_resources=["forest", "fish"])
        advisor = StrategyAdvisor(state)
        recs = advisor.recommend()
        order = {"high": 0, "medium": 1, "low": 2}
        priorities = [order.get(r.priority, 3) for r in recs]
        self.assertEqual(priorities, sorted(priorities))

    def test_stars_vs_borders_grow_early_game(self):
        """Early game with plenty of stars → grow city."""
        state = self._make_state(turn=2, stars=14, cities=1, opponent_distance=7)
        advisor = StrategyAdvisor(state)
        choice, _ = advisor.stars_vs_borders()
        self.assertEqual(choice, "grow_city")

    def test_stars_vs_borders_hold_when_enemy_close(self):
        """Opponent just 1 turn away → hold stars for units."""
        state = self._make_state(turn=5, stars=10, cities=2, opponent_distance=1)
        advisor = StrategyAdvisor(state)
        choice, _ = advisor.stars_vs_borders()
        self.assertEqual(choice, "hold_stars")

    def test_stars_vs_borders_hold_when_low_stars(self):
        """Many cities but few stars → save for tech."""
        state = self._make_state(turn=8, stars=4, cities=4, opponent_distance=6)
        advisor = StrategyAdvisor(state)
        choice, _ = advisor.stars_vs_borders()
        self.assertEqual(choice, "hold_stars")

    def test_best_next_tech_skips_researched(self):
        tribe = get_tribe("bardur")
        # Mark first early tech as researched
        already = [tribe.early_techs[0]]
        state = self._make_state(has_tech=already)
        advisor = StrategyAdvisor(state)
        next_tech = advisor.best_next_tech()
        self.assertNotIn(next_tech, already)

    def test_best_next_tech_returns_none_when_all_done(self):
        tribe = get_tribe("bardur")
        all_techs = tribe.early_techs + tribe.mid_techs
        state = self._make_state(has_tech=all_techs)
        advisor = StrategyAdvisor(state)
        self.assertIsNone(advisor.best_next_tech())

    def test_summary_contains_tribe_name(self):
        state = self._make_state(tribe_name="oumaji")
        advisor = StrategyAdvisor(state)
        summary = advisor.summary()
        self.assertIn("Oumaji", summary)

    def test_summary_contains_choice(self):
        state = self._make_state()
        advisor = StrategyAdvisor(state)
        summary = advisor.summary()
        self.assertIn("STARS vs CITY BORDERS", summary)

    def test_oumaji_rider_rush_recommendation(self):
        state = self._make_state(tribe_name="oumaji", turn=2)
        advisor = StrategyAdvisor(state)
        recs = advisor.recommend()
        actions = [r.action.lower() for r in recs]
        self.assertTrue(any("rider" in a for a in actions),
                        f"Expected rider rush rec, got: {actions}")

    def test_vengir_turn1_swordsman_recommendation(self):
        state = self._make_state(tribe_name="vengir", turn=1)
        advisor = StrategyAdvisor(state)
        recs = advisor.recommend()
        actions = [r.action.lower() for r in recs]
        self.assertTrue(any("swordsman" in a for a in actions),
                        f"Expected swordsman rec, got: {actions}")

    def test_forest_resource_triggers_forestry_rec(self):
        state = self._make_state(nearby_resources=["forest"])
        advisor = StrategyAdvisor(state)
        recs = advisor.recommend()
        actions = [r.action for r in recs]
        self.assertTrue(any("Forestry" in a for a in actions),
                        f"Expected Forestry rec, got: {actions}")

    def test_fish_resource_triggers_fishing_rec(self):
        state = self._make_state(nearby_resources=["fish"])
        advisor = StrategyAdvisor(state)
        recs = advisor.recommend()
        actions = [r.action for r in recs]
        self.assertTrue(any("Fishing" in a for a in actions),
                        f"Expected Fishing rec, got: {actions}")

    def test_recommendation_str_format(self):
        rec = Recommendation(
            priority="high", category="economy",
            action="Research Forestry", rationale="Forests nearby.",
            stars_cost=5,
        )
        s = str(rec)
        self.assertIn("[HIGH]", s)
        self.assertIn("Research Forestry", s)
        self.assertIn("[5★]", s)
        self.assertIn("Forests nearby.", s)

    def test_all_tribes_can_produce_recommendations(self):
        """Smoke test: every tribe should produce recommendations without error."""
        for tribe_key in TRIBES:
            with self.subTest(tribe=tribe_key):
                state = GameState(
                    tribe_name=tribe_key, turn=3, stars=10,
                    cities=2, city_level=1,
                    nearby_resources=["forest", "fish"],
                )
                advisor = StrategyAdvisor(state)
                recs = advisor.recommend()
                self.assertIsInstance(recs, list)
                summary = advisor.summary()
                self.assertIsInstance(summary, str)
                self.assertGreater(len(summary), 50)


# ──────────────────────────────────────────────────────────────────────────
# Image analyser tests
# ──────────────────────────────────────────────────────────────────────────

class TestImageAnalyzer(unittest.TestCase):

    def _make_image(self, r: int, g: int, b: int) -> Path:
        """Create a tiny solid-colour image and return its path."""
        from PIL import Image as PILImage
        import tempfile
        img = PILImage.new("RGB", (100, 80), color=(r, g, b))
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(tmp.name)
        return Path(tmp.name)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            ImageAnalyzer("/nonexistent/file.png").load()

    def test_dominant_terrain_forest(self):
        """Solid dark-green image → forest terrain."""
        path = self._make_image(50, 150, 50)
        analyzer = ImageAnalyzer(path).load()
        self.assertEqual(analyzer.dominant_terrain(), "forest")

    def test_dominant_terrain_water(self):
        """Solid blue image → water terrain."""
        path = self._make_image(50, 120, 220)
        analyzer = ImageAnalyzer(path).load()
        self.assertEqual(analyzer.dominant_terrain(), "water")

    def test_infer_tribe_forest(self):
        path = self._make_image(50, 150, 50)
        analyzer = ImageAnalyzer(path).load()
        self.assertEqual(analyzer.infer_tribe(), "bardur")

    def test_infer_tribe_water(self):
        path = self._make_image(50, 120, 220)
        analyzer = ImageAnalyzer(path).load()
        self.assertEqual(analyzer.infer_tribe(), "kickoo")

    def test_detect_resources_forest(self):
        path = self._make_image(50, 150, 50)
        analyzer = ImageAnalyzer(path).load()
        resources = analyzer.detect_resources()
        self.assertIn("forest", resources)

    def test_describe_returns_string(self):
        path = self._make_image(50, 150, 50)
        analyzer = ImageAnalyzer(path).load()
        desc = analyzer.describe()
        self.assertIsInstance(desc, str)
        self.assertIn("terrain", desc.lower())
        self.assertIn("tribe", desc.lower())

    def test_analyze_image_function(self):
        path = self._make_image(50, 120, 220)
        result = analyze_image(path)
        self.assertIn("terrain", result)
        self.assertIn("tribe_hint", result)
        self.assertIn("resources", result)
        self.assertIn("description", result)


# ──────────────────────────────────────────────────────────────────────────
# CLI integration test
# ──────────────────────────────────────────────────────────────────────────

class TestCLI(unittest.TestCase):

    def test_cli_basic_output(self):
        """CLI mode should print a summary to stdout without errors."""
        import subprocess
        result = subprocess.run(
            [
                sys.executable, "polytopia_agent.py",
                "--cli", "--tribe", "bardur",
                "--turn", "3", "--stars", "10", "--cities", "2",
            ],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Bardur", result.stdout)
        self.assertIn("STARS vs CITY BORDERS", result.stdout)

    def test_cli_oumaji_rider_rush(self):
        result = subprocess.run(
            [
                sys.executable, "polytopia_agent.py",
                "--cli", "--tribe", "oumaji", "--turn", "2", "--stars", "5",
            ],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Oumaji", result.stdout)

    def test_cli_unknown_tribe_exits_nonzero(self):
        result = subprocess.run(
            [sys.executable, "polytopia_agent.py", "--cli", "--tribe", "FAKEFAKEFAKE"],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent),
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
