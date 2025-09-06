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
        
        # Check each unknown character
        for suspect in game_state.get_unknown_suspects():
            criminal_possible = CluesSolver._test_label_possibility(game_state, suspect, Label.CRIMINAL, constraints)
            innocent_possible = CluesSolver._test_label_possibility(game_state, suspect, Label.INNOCENT)
            
            if criminal_possible and not innocent_possible:
                elimination_moves.append(CluesMove(
                    suspect=suspect,
                    label=Label.CRIMINAL,
                ))
            elif innocent_possible and not criminal_possible:
                elimination_moves.append(CluesMove(
                    suspect=suspect,
                    label=Label.INNOCENT,
                ))
        
        return elimination_moves
    
    @staticmethod
    def _test_label_possibility(game_state: GameState, suspect: Suspect, label: Label, constraints: List[Constraint]) -> bool:
        """Test if assigning a label to a character is possible without contradiction."""
        test_state = game_state.copy()
        test_state.set_label(suspect, label)
        try:
            for constraint in constraints:
                if not constraint.evaluate(test_state):
                    return False
            return True
        except Exception:
            return False

    @staticmethod
    def solve_step_by_step(game_state: GameState, parser: ConstraintParser) -> List[CluesMove]:
        """Solve the game step by step, finding the next certain move."""
        moves = []
        current_state = game_state.copy()
        
        while True:
            # Find certain moves in current state
            constraints = CluesSolver.parse_constraints(current_state, parser)
            if len(constraints) == 0:
                break

            certain_moves = CluesSolver.find_certain_moves(current_state, constraints)
            if not certain_moves:
                break
            
            # Take the first certain move
            next_move = certain_moves[0]
            moves.append(next_move)
            
            # Apply the move to our working state
            current_state.set_label(
                next_move.suspect,
                next_move.label,
            )
            
            # Update our game state for next iteration
            current_state = current_state.copy()
        
        return moves
