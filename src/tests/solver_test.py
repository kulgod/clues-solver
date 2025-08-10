import pytest
from src.game_state import GameState, Character, Label
from src.constraints import CountConstraint, OccupationConstraint
from src.solver import PuzzleSolver, Move
from src.game_interface import MockGameInterface

class TestPuzzleSolver:
    """Test cases for the puzzle solver."""
    
    def setup_method(self):
        """Setup test environment."""
        self.game_state = GameState()
        self.constraints = [
            CountConstraint(max_criminals=3, min_criminals=1),
            OccupationConstraint({
                "Detective": {"type": "bias", "bias": 0.8},
                "Thief": {"type": "bias", "bias": -0.8}
            })
        ]
    
    def test_game_state_creation(self):
        """Test game state creation and character addition."""
        char = self.game_state.add_character(0, 0, "Alice", "Detective", Label.INNOCENT)
        assert char.name == "Alice"
        assert char.occupation == "Detective" 
        assert char.label == Label.INNOCENT
        assert char.position == (0, 0)
    
    def test_constraint_propagation(self):
        """Test that constraints properly propagate information."""
        # Add characters
        self.game_state.add_character(0, 0, "Alice", "Detective", Label.INNOCENT)
        self.game_state.add_character(0, 1, "Bob", "Thief", Label.UNKNOWN)
        
        solver = PuzzleSolver(self.game_state, self.constraints)
        moves = solver.solve()
        
        # Should suggest labeling the thief as criminal with high confidence
        bob_moves = [m for m in moves if m.character.name == "Bob"]
        assert len(bob_moves) > 0
        criminal_moves = [m for m in bob_moves if m.label == Label.CRIMINAL]
        assert len(criminal_moves) > 0
        assert criminal_moves[0].confidence > 0.6
    
    def test_count_constraint(self):
        """Test count constraint behavior."""
        # Add maximum criminals
        for i in range(3):
            self.game_state.add_character(0, i, f"Criminal{i}", "Thief", Label.CRIMINAL)
        
        # Add unknown character
        self.game_state.add_character(1, 0, "Unknown", "Teacher", Label.UNKNOWN)
        
        solver = PuzzleSolver(self.game_state, self.constraints)
        moves = solver.solve()
        
        # Should suggest innocent label since max criminals reached
        unknown_moves = [m for m in moves if m.character.name == "Unknown"]
        innocent_moves = [m for m in unknown_moves if m.label == Label.INNOCENT]
        assert len(innocent_moves) > 0
        assert innocent_moves[0].confidence == 1.0
    
    def test_mock_interface(self):
        """Test mock game interface."""
        interface = MockGameInterface()
        game_state = interface.get_game_state()
        
        assert len(game_state.known_characters) > 0
        assert interface.is_game_active()
        
        # Find an unknown character to test move
        unknown_chars = game_state.get_unknown_characters()
        if unknown_chars:
            success = interface.make_move(unknown_chars[0], Label.INNOCENT)
            assert success

if __name__ == "__main__":
    pytest.main([__file__])