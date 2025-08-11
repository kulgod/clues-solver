import unittest

from src.python.game_state import GameState, Suspect, Label
from src.python.clues_solver import CluesSolver, CluesMove
from src.python.tests.example_game import example_board_2025_08_09

class TestPuzzleSolver(unittest.TestCase):
    """Test cases for the puzzle solver."""
    
    def test_example_game(self):
        game = GameState.from_grid(example_board_2025_08_09)
        print(CluesSolver.solve_step_by_step(game))
        

if __name__ == "__main__":
    unittest.main()