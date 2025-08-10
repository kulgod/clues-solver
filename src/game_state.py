from abc import ABC, abstractmethod
from typing import List, Set
from .game_state import GameState, Character, Label

class Constraint(ABC):
    """Abstract base class for game constraints."""
    
    @abstractmethod
    def is_satisfied(self, game_state: GameState) -> bool:
        """Check if constraint is satisfied in current game state."""
        pass
    
    @abstractmethod
    def get_implications(self, game_state: GameState) -> List['Implication']:
        """Get logical implications from this constraint."""
        pass

class Implication:
    """Represents a logical implication: if conditions are met, then conclusion follows."""
    
    def __init__(self, character: Character, label: Label, confidence: float, reason: str):
        self.character = character
        self.label = label
        self.confidence = confidence
        self.reason = reason

class AdjacentConstraint(Constraint):
    """Constraint based on adjacent characters (common in grid puzzles)."""
    
    def __init__(self, rule_type: str):
        self.rule_type = rule_type
    
    def is_satisfied(self, game_state: GameState) -> bool:
        # Implementation depends on specific game rules
        return True
    
    def get_implications(self, game_state: GameState) -> List[Implication]:
        implications = []
        
        # Example: If a criminal is adjacent to someone, that person might be more likely innocent
        # This would be customized based on actual game rules
        
        return implications

class OccupationConstraint(Constraint):
    """Constraint based on character occupations."""
    
    def __init__(self, occupation_rules: dict):
        self.occupation_rules = occupation_rules
    
    def is_satisfied(self, game_state: GameState) -> bool:
        return True
    
    def get_implications(self, game_state: GameState) -> List[Implication]:
        implications = []
        
        # Example rules based on occupations:
        # - Police officers are more likely to be innocent
        # - Certain occupations might be mutually exclusive for criminals
        
        for char in game_state.get_unknown_characters():
            if char.occupation in self.occupation_rules:
                rule = self.occupation_rules[char.occupation]
                if rule['type'] == 'bias':
                    implications.append(Implication(
                        character=char,
                        label=Label.INNOCENT if rule['bias'] > 0 else Label.CRIMINAL,
                        confidence=abs(rule['bias']),
                        reason=f"Occupation bias: {char.occupation}"
                    ))
        
        return implications

class CountConstraint(Constraint):
    """Constraint based on total count of criminals/innocents."""
    
    def __init__(self, max_criminals: int, min_criminals: int = 1):
        self.max_criminals = max_criminals
        self.min_criminals = min_criminals
    
    def is_satisfied(self, game_state: GameState) -> bool:
        criminal_count = sum(1 for char in game_state.get_labeled_characters() 
                           if char.label == Label.CRIMINAL)
        innocent_count = sum(1 for char in game_state.get_labeled_characters() 
                           if char.label == Label.INNOCENT)
        
        total_chars = len(game_state.known_characters)
        remaining_unknown = len(game_state.get_unknown_characters())
        
        # Check if current state could lead to valid final state
        return (criminal_count <= self.max_criminals and 
                criminal_count + remaining_unknown >= self.min_criminals)
    
    def get_implications(self, game_state: GameState) -> List[Implication]:
        implications = []
        
        criminal_count = sum(1 for char in game_state.get_labeled_characters() 
                           if char.label == Label.CRIMINAL)
        unknown_chars = game_state.get_unknown_characters()
        
        # If we've reached max criminals, rest must be innocent
        if criminal_count >= self.max_criminals:
            for char in unknown_chars:
                implications.append(Implication(
                    character=char,
                    label=Label.INNOCENT,
                    confidence=1.0,
                    reason="Maximum criminals reached"
                ))
        
        # If we need more criminals and have limited unknowns
        elif criminal_count + len(unknown_chars) == self.min_criminals:
            for char in unknown_chars:
                implications.append(Implication(
                    character=char,
                    label=Label.CRIMINAL,
                    confidence=1.0,
                    reason="Minimum criminals required"
                ))
        
        return implications
