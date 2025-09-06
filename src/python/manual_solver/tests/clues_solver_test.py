import unittest
import json

from src.python.manual_solver.game_state import GameState, Label
from src.python.manual_solver.constraints import Constraint
from src.python.manual_solver.clues_solver import CluesSolver, CluesMove


class TestCluesSolver(unittest.TestCase):
    """Test cases for the puzzle solver."""
    
    def test_parse_constraints(self):
        # Get constraints from src/example_games/clues_solver__olivia_constraints.json
        with open("src/example_games/clues_solver__olivia_constraints.json") as f:
            constraints_raw = f.read()
        all_constraints = json.loads(constraints_raw)["characters"]

        # Load initial game state from src/example_games/clues_solver__olivia_initial.json
        with open("src/example_games/clues_solver__olivia_initial.json") as f:
            initial_game_raw = f.read()
        initial_game = GameState.from_api_data(json.loads(initial_game_raw)["characters"])

        # Find certain moves
        initially_visible_cells = [id for id, c in initial_game.cell_map.items() if c.is_visible]
        self.assertEqual(len(initially_visible_cells), 1)
        initially_visible_constraints = filter(lambda c: c["hint_id"] in initially_visible_cells, all_constraints)
        parsed_constraints = [
            Constraint.from_string(exp) for c in initially_visible_constraints for exp in c["expressions"]
        ]
        suggested_clues = CluesSolver.find_certain_moves(initial_game, parsed_constraints)

        expected_clues = [
            CluesMove(initial_game.cell_map["D2"], Label.INNOCENT),
            CluesMove(initial_game.cell_map["D4"], Label.CRIMINAL),
            CluesMove(initial_game.cell_map["D5"], Label.CRIMINAL),
        ]
        self.assertEqual(len(suggested_clues), 3)
        for c in suggested_clues:
            self.assertIn(c, expected_clues)
        

if __name__ == "__main__":
    unittest.main()