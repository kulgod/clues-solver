from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional

from src.python.manual_solver.game_state import GameState, Suspect, Label

class GameInterface(ABC):
    """Abstract interface for connecting to the online game."""
    
    @abstractmethod
    def get_game_state(self) -> GameState:
        """Retrieve current game state from the online game."""
        pass
    
    @abstractmethod
    def make_move(self, suspect: Suspect, label: Label) -> bool:
        """Make a move in the online game. Returns True if successful."""
        pass
    
    @abstractmethod
    def is_game_active(self) -> bool:
        """Check if the game is still active."""
        pass