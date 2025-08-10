from typing import List, Dict, Tuple, Optional
import heapq
from .game_state import GameState, Character, Label
from .constraints import Constraint, Implication

class Move:
    """Represents a move (labeling a character)."""
    
    def __init__(self, character: Character, label: Label, confidence: float, reasoning: str):
        self.character = character
        self.label = label
        self.confidence = confidence
        self.reasoning = reasoning
        self.risk_score = 1.0 - confidence  # Higher risk for lower confidence
    
    def __lt__(self, other):
        return self.risk_score < other.risk_score

class PuzzleSolver:
    """Main solver for the puzzle game."""
    
    def __init__(self, game_state: GameState, constraints: List[Constraint]):
        self.game_state = game_state
        self.constraints = constraints
        self.solution_cache: Dict[str, List[Move]] = {}
    
    def solve(self) -> List[Move]:
        """Find the optimal sequence of moves."""
        # Apply constraint propagation first
        self._propagate_constraints()
        
        # Find all possible valid moves
        possible_moves = self._generate_possible_moves()
        
        # Sort by confidence/risk
        possible_moves.sort(key=lambda m: m.risk_score)
        
        return possible_moves
    
    def _propagate_constraints(self):
        """Apply all constraints to deduce new information."""
        changed = True
        iteration = 0
        max_iterations = 100  # Prevent infinite loops
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            for constraint in self.constraints:
                if not constraint.is_satisfied(self.game_state):
                    continue
                
                implications = constraint.get_implications(self.game_state)
                
                for implication in implications:
                    char = implication.character
                    if char.label == Label.UNKNOWN and implication.confidence > 0.8:
                        # High confidence implications are applied automatically
                        self.game_state.set_label(
                            char.position[0], 
                            char.position[1], 
                            implication.label, 
                            implication.confidence
                        )
                        changed = True
    
    def _generate_possible_moves(self) -> List[Move]:
        """Generate all possible moves with their confidence scores."""
        moves = []
        unknown_chars = self.game_state.get_unknown_characters()
        
        for char in unknown_chars:
            # Calculate confidence for each possible label
            criminal_confidence = self._calculate_label_confidence(char, Label.CRIMINAL)
            innocent_confidence = self._calculate_label_confidence(char, Label.INNOCENT)
            
            # Only suggest moves with reasonable confidence
            if criminal_confidence > 0.6:
                moves.append(Move(
                    character=char,
                    label=Label.CRIMINAL,
                    confidence=criminal_confidence,
                    reasoning=self._get_reasoning(char, Label.CRIMINAL)
                ))
            
            if innocent_confidence > 0.6:
                moves.append(Move(
                    character=char,
                    label=Label.INNOCENT,
                    confidence=innocent_confidence,
                    reasoning=self._get_reasoning(char, Label.INNOCENT)
                ))
        
        return moves
    
    def _calculate_label_confidence(self, character: Character, label: Label) -> float:
        """Calculate confidence for assigning a label to a character."""
        total_confidence = 0.0
        evidence_count = 0
        
        # Test the assignment in a copy of the game state
        test_state = self.game_state.copy()
        test_state.set_label(character.position[0], character.position[1], label, 1.0)
        
        # Check if this assignment violates any constraints
        for constraint in self.constraints:
            if not constraint.is_satisfied(test_state):
                return 0.0  # Invalid assignment
        
        # Collect evidence from constraint implications
        for constraint in self.constraints:
            implications = constraint.get_implications(self.game_state)
            for implication in implications:
                if (implication.character.position == character.position and 
                    implication.label == label):
                    total_confidence += implication.confidence
                    evidence_count += 1
        
        # Base confidence if no evidence
        if evidence_count == 0:
            return 0.5  # Neutral
        
        return min(total_confidence / evidence_count, 1.0)
    
    def _get_reasoning(self, character: Character, label: Label) -> str:
        """Get human-readable reasoning for a move."""
        reasons = []
        
        for constraint in self.constraints:
            implications = constraint.get_implications(self.game_state)
            for implication in implications:
                if (implication.character.position == character.position and 
                    implication.label == label):
                    reasons.append(implication.reason)
        
        if not reasons:
            return f"No strong evidence, assigning {label.value} to {character.name}"
        
        return "; ".join(reasons)
    
    def suggest_next_move(self) -> Optional[Move]:
        """Suggest the best next move."""
        moves = self.solve()
        return moves[0] if moves else None
    
    def evaluate_move(self, character: Character, label: Label) -> Tuple[float, str]:
        """Evaluate a potential move and return confidence and reasoning."""
        confidence = self._calculate_label_confidence(character, label)
        reasoning = self._get_reasoning(character, label)
        return confidence, reasoning