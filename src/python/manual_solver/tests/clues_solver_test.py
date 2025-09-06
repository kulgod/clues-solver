import unittest

from src.python.manual_solver.game_state import GameState, Label
from src.python.manual_solver.clues_solver import CluesSolver
from src.python.manual_solver.tests.example_game import example_board_2025_08_09

class TestCluesSolver(unittest.TestCase):
    """Test cases for the puzzle solver."""
    
    def test_parse_constraints(self):
        game = GameState.from_grid(example_board_2025_08_09)
        constraints = CluesSolver.parse_constraints(game)
        

if __name__ == "__main__":
    unittest.main()