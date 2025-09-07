import itertools
from collections import defaultdict
from platform import java_ver
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
    def find_certain_moves(game_state: GameState, constraints: List[Constraint]) -> List[CluesMove]:
        """Find moves based on elimination (only one possibility remains)."""
        # 1. Compute all possible board states. Keep a map of all labels of each suspect that are found in valid board states.
        initial_unknowns = game_state.get_unknown_suspects()
        candidate_game = game_state.copy()
        valid_labels = defaultdict(set)

        final_state_masks = list(itertools.product([0, 1], repeat=len(initial_unknowns)))
        def _apply_mask(game: GameState, mask: Tuple[int]):
            labels = {}
            for suspect, binary_label in zip(initial_unknowns, mask):
                label = Label.CRIMINAL if binary_label else Label.INNOCENT
                game.set_label(suspect, label, is_visible=True)
                labels[suspect.name] = label
            return labels

        for mask in final_state_masks:
            candidate_labels = _apply_mask(candidate_game, mask)
            is_valid_state = all([c.evaluate(candidate_game) for c in constraints])
            if is_valid_state:
                for name, label in candidate_labels.items():
                    valid_labels[name].add(label)

            # reset game
            for suspect in initial_unknowns:
                candidate_game.set_label(suspect, None, is_visible=False)

        # Filter to unknowns
        valid_labels_for_unknowns = {s.name: valid_labels[s.name] for s in initial_unknowns}
        # Filter to unknowns with only 1 valid label
        certain_moves = {
            name: list(labels)[0] 
            for name, labels in valid_labels_for_unknowns.items()
            if len(labels) == 1
        }

        # Convert to CluesMove output
        return [
            CluesMove(game_state.get_suspect(name), label) 
            for name, label in certain_moves.items()
        ]
