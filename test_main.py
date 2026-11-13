"""Route and calculation tests. Run python test_main.py before publishing."""

import os
import unittest
from copy import deepcopy

# Set skip before importing main so tests never start a web server.
os.environ["DRAFTER_SKIP"] = "1"
import main


def text(result: main.Page) -> str:
    """Read component text for visible-output assertions."""
    return str(result.content)


class ToolboxTests(unittest.TestCase):
    """Exercise every route, rejected input, and meaningful State updates."""

    def test_action_refresh(self) -> None:
        """Missing form arguments after a browser refresh never mutate State."""
        state = main.new_state()
        original = deepcopy(state)
        for action in (main.save_session, main.delete_session, main.save_settings,
                       main.convert_sensitivity, main.filter_gear):
            self.assertIsInstance(action(state), main.Page)
            self.assertEqual(state, original)

    def test_index(self) -> None:
        """Empty logs and mixed-game totals use the saved game."""
        state = main.new_state()
        self.assertIn("empty", text(main.index(state)))
        state.sessions = [
            main.TrainingSession("CS2", "Tracking", 30, 60.0),
            main.TrainingSession("CS2", "Tracking", 30, 80.0),
            main.TrainingSession("VALORANT", "Tracking", 200, 100.0),
        ]
        result = text(main.index(state))
        self.assertIn("60 / 60", result)
        self.assertIn("70.0%", result)
        self.assertIn("Goal reached", result)

    def test_add_session(self) -> None:
        """The training form uses the selected game."""
        state = main.new_state()
        state.selected_game = "VALORANT"
        result = main.add_session(state)
        self.assertIn("VALORANT", text(result))
        self.assertIn("Save Session", text(result))
        self.assertEqual(state.sessions, [])

    def test_save_session(self) -> None:
        """Valid inputs create a typed dataclass in the log."""
        state = main.new_state()
        result = main.save_session(state, "VALORANT", " Tracking ", "30", "75")
        self.assertEqual(state.sessions, [main.TrainingSession("VALORANT", "Tracking", 30, 75.0)])
        self.assertIn("Training History", text(result))

    def test_bad_sessions(self) -> None:
        """Invalid durations and accuracy never change State."""
        for minutes, accuracy in [("0", "50"), ("-2", "50"), ("1.5", "50"),
                                  ("3", "101"), ("3", "nan"), ("3", "inf"), ("", "")]:
            state = main.new_state()
            before = deepcopy(state)
            result = main.save_session(state, "CS2", "Tracking", minutes, accuracy)
            self.assertEqual(state, before)
            self.assertIn("Enter a drill", text(result))
        state = main.new_state()
        main.save_session(state, "other", "", "30", "70")
        self.assertEqual(state.sessions, [])

    def test_history(self) -> None:
        """History shows all games and distinct deletion indices."""
        state = main.new_state()
        main.save_session(state, "CS2", "Tracking", "10", "0")
        main.save_session(state, "VALORANT", "Flicking", "20", "100")
        result = text(main.history(state))
        self.assertIn("CS2", result)
        self.assertIn("VALORANT", result)
        self.assertIn("'session_index': 1", result)

    def test_delete_session(self) -> None:
        """Delete exactly one entry and reject negative or out-of-range indices."""
        state = main.new_state()
        main.save_session(state, "CS2", "Tracking", "10", "50")
        main.save_session(state, "VALORANT", "Flicking", "20", "100")
        main.delete_session(state, 0)
        self.assertEqual(state.sessions[0].game, "VALORANT")
        before = deepcopy(state)
        self.assertIn("unavailable", text(main.delete_session(state, -1)))
        main.delete_session(state, 9)
        self.assertEqual(state, before)

    def test_settings(self) -> None:
        """Show both current settings."""
        state = main.new_state()
        result = text(main.settings(state))
        self.assertIn("practice_goal", result)
        self.assertIn("selected_game", result)

    def test_save_settings(self) -> None:
        """Only a valid pair changes the goal and dashboard filter."""
        state = main.new_state()
        main.save_settings(state, "VALORANT", "90")
        self.assertEqual((state.selected_game, state.practice_goal), ("VALORANT", 90))
        before = deepcopy(state)
        for game, goal in [("CS2", "0"), ("other", "60"), ("CS2", "x")]:
            main.save_settings(state, game, goal)
            self.assertEqual(state, before)

    def test_converter(self) -> None:
        """The converter displays all settings and its result action."""
        self.assertIn("Convert Sensitivity", text(main.converter(main.new_state())))

    def test_convert_sensitivity(self) -> None:
        """Known examples preserve cm/360 and a round trip returns the source."""
        state = main.new_state()
        values = main.sensitivity_result("CS2", "VALORANT", 800, 1)
        self.assertAlmostEqual(values[0], 0.3142857142857143)
        self.assertAlmostEqual(values[3], 51.95454545454545)
        back = main.sensitivity_result("VALORANT", "CS2", 800, values[0])
        self.assertAlmostEqual(back[0], 1)
        self.assertAlmostEqual(back[3], values[3])
        result = main.convert_sensitivity(state, "CS2", "VALORANT", "800", "1")
        self.assertIn("0.314286", text(result))
        before = deepcopy(state)
        for dpi, sensitivity in [("0", "1"), ("800", "nan"), ("x", "1"), ("800", "-2")]:
            result = main.convert_sensitivity(state, "CS2", "VALORANT", dpi, sensitivity)
            self.assertIn("Use whole DPI", text(result))
            self.assertEqual(state, before)

    def test_gear(self) -> None:
        """Opening the finder reuses the saved budget."""
        state = main.new_state()
        state.gear_budget = 45.0
        self.assertIn("45.0", text(main.gear(state)))

    def test_filter_gear(self) -> None:
        """Budget and wireless filtering work and invalid budgets are rejected."""
        state = main.new_state()
        result = text(main.filter_gear(state, "Mouse", "60", True))
        self.assertEqual(state.gear_budget, 60.0)
        self.assertIn("Logitech G305", result)
        self.assertNotIn("DeathAdder", result)
        self.assertIn("No matches", text(main.filter_gear(state, "Mouse", "0", False)))
        before = deepcopy(state)
        for budget in ["-50", "nan", "hello", "inf", ""]:
            self.assertIn("enter a budget", text(main.filter_gear(state, "Mouse", budget, False)))
            self.assertEqual(state, before)
        self.assertIn("Gigantus", text(main.filter_gear(state, "Mousepad", "20", True)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
