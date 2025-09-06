from typing import List, Dict, Tuple, Optional, Set

from src.python.manual_solver.game_state import GameState, Suspect, Label
from src.python.manual_solver.constraints import Constraint, Position

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
    def parse_constraints(game_state: GameState) -> List[Constraint]:
        """Parse the constraints from the game state."""
        constraints = []
        # Build name to position mapping
        name_to_position = {}
        for cell_name, suspect in game_state.cell_map.items():
            row, col = game_state._to_cell_coords(cell_name)
            name_to_position[suspect.name] = Position(row, col)
        
        parser.set_name_mapping(name_to_position)
        
        # Parse constraints from all known suspects' hints
        for suspect in game_state.get_known_suspects():
            if suspect.hint:
                row, col = None, None
                for cell_name, s in game_state.cell_map.items():
                    if s.name == suspect.name:
                        row, col = game_state._to_cell_coords(cell_name)
                        break
                
                if row is not None and col is not None:
                    source_position = Position(row, col)
                    parsed_constraints = parser.parse_hint(suspect.hint, source_position)
                    constraints.extend(parsed_constraints)
        
        return constraints
    
    @staticmethod
    def find_certain_moves(game_state: GameState) -> List[CluesMove]:
        """Find moves based on elimination (only one possibility remains)."""
        elimination_moves = []
        
        # Check each unknown character
        for suspect in game_state.get_unknown_suspects():
            # Test both labels
            criminal_possible = CluesSolver._test_label_possibility(game_state, suspect, Label.CRIMINAL)
            innocent_possible = CluesSolver._test_label_possibility(game_state, suspect, Label.INNOCENT)
            
            # If only one label is possible, that's our move
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
    def _test_label_possibility(game_state: GameState, suspect: Suspect, label: Label) -> bool:
        """Test if assigning a label to a character is possible without contradiction."""
        # Create a test state
        test_state = game_state.copy()
        test_state.set_label(suspect, label)
        
        # Check if this creates any contradictions
        try:
            # Apply constraints to see if any contradictions arise
            constraints = CluesSolver.parse_constraints(test_state)
            for constraint in constraints:
                deductions = constraint.check(test_state)
                # If any constraint returns deductions, check if they're consistent
                for pos, deduced_label, reason in deductions:
                    # Find the suspect at this position
                    for cell_name, s in test_state.cell_map.items():
                        test_row, test_col = test_state._to_cell_coords(cell_name)
                        if test_row == pos.row and test_col == pos.col:
                            if s.is_visible and s.label != deduced_label:
                                return False  # Contradiction found
                            elif not s.is_visible:
                                # Apply the deduction to the test state
                                test_state.set_label(s, deduced_label)
                            break
            return True
        except Exception:
            return False
    
    @staticmethod
    def solve_step_by_step(game_state: GameState) -> List[CluesMove]:
        """Solve the game step by step, finding the next certain move."""
        moves = []
        current_state = game_state.copy()
        
        while True:
            # Find certain moves in current state
            certain_moves = CluesSolver.find_certain_moves(current_state)
            
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
    
    @staticmethod
    def analyze_hint(game_state: GameState, hint: str) -> str:
        """Analyze a specific hint and show what it tells us."""
        analysis = []
        analysis.append(f"=== Analyzing Hint: {hint} ===")
        
        # Parse the hint
        for constraint in CluesSolver.parse_constraints(game_state):
            if hasattr(constraint, 'parse_hint'):
                parsed = constraint.parse_hint(hint)
                if parsed:
                    analysis.append(f"Parsed: {parsed}")
        
        # Find implications from this hint
        for constraint in CluesSolver.parse_constraints(game_state):
            implications = constraint.check(game_state)
            for implication in implications:
                if implication.reason and hint.lower() in implication.reason.lower():
                    analysis.append(f"Implication: {implication.character.name} -> {implication.label.value}")
        
        return "\n".join(analysis)
