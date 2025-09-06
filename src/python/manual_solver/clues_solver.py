from re import L
from typing import List, Dict, Tuple, Optional, Set

from src.python.manual_solver.game_state import GameState, Suspect, Label
from src.python.manual_solver.constraints import Constraint, Position
from src.python.manual_solver.constraint_parser import ConstraintParser

class CluesMove:
    """Represents a move in the Clues game."""
    def __init__(self, suspect: Suspect, label: Label):
        self.suspect = suspect
        self.label = label
    
    def __str__(self):
        return f"{self.suspect.name} ({self.suspect.occupation}) -> {self.label.value.upper()}"

class CluesSolver:
    """Specialized solver for the Clues game that finds 100% certain moves."""

    @staticmethod
    def parse_constraints(game_state: GameState, parser: ConstraintParser) -> List[Constraint]:
        """Parse the constraints from the game state."""
        hints = [suspect.hint for suspect in game_state.get_known_suspects()]
        constraints = parser.parse_all(hints)
        return constraints
    
    @staticmethod
    def find_certain_moves(game_state: GameState, constraints: List[Constraint]) -> List[CluesMove]:
        """Find moves based on elimination (only one possibility remains)."""
        elimination_moves = []

        # 1. Compute all possible board states. Keep a map of all labels of each suspect that are found in valid board states.
        label_possibilities = {}  # map suspect name -> Set[Label]
        def _evaluate_board(game_solution: GameState) -> None:
            remaining_unknowns = game_solution.get_unknown_suspects()
            if len(remaining_unknowns) == 0:
                is_valid_solution = all([c.evaluate(game_solution) for c in constraints])
                if is_valid_solution:
                    for s in game_solution.get_known_suspects():
                        label_possibilities[s].add(s.label)
            else:
                game_solution.set_label(remaining_unknowns[0], Label.INNOCENT)
                _evaluate_board(game_solution)
                # Backtrack from completed solution
                for s in remaining_unknowns:
                    game_solution.set_label(s, None) 
                game_solution.set_label(remaining_unknowns[0], Label.CRIMINAL)
                for s in remaining_unknowns:
                    game_solution.set_label(s, None)

        # 2. Extract certain moves from label possibilities
        label_possibilities = _evaluate_board(game_state.copy(), label_possibilities)
        possibilities_for_unknowns = {
            s: label_possibilities[s]
            for s in game_state.get_unknown_suspects()
        }
        elimination_moves = [
            CluesMove(
                game_state.get_suspect(s), 
                list(labels)[0]
            )
            for s, labels in possibilities_for_unknowns.items()
            if len(labels) == 1
        ]
        return elimination_moves
