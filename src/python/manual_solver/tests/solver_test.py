import unittest

from src.python.game_state import GameState, Suspect, Label
from src.python.clues_solver import CluesSolver, CluesMove
from src.python.tests.example_game import example_board_2025_08_09

class TestPuzzleSolver(unittest.TestCase):
    """Test cases for the puzzle solver."""
    
    def test_example_game(self):
        game = GameState.from_grid(example_board_2025_08_09)
        certain_moves = CluesSolver.find_certain_moves(game)
        self.assertEqual(len(certain_moves), 1)
        self.assertEqual(certain_moves[0].suspect.name, "Tyler")
        self.assertEqual(certain_moves[0].label, Label.CRIMINAL)
        

if __name__ == "__main__":
    unittest.main()