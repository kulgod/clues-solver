from abc import ABC, abstractmethod
from typing import List, Set, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum

from src.python.manual_solver.game_state import GameState, Suspect, Label


@dataclass(frozen=True)
class Position:
    row: int
    col: int

class Constraint(ABC):
    """Base class for all game constraints."""
    
    @abstractmethod
    def check(self, game_state: GameState) -> List[Tuple[Position, Label, str]]:
        """
        Check this constraint against the current game state.
        Returns list of (position, label, reason) tuples for certain deductions.
        """
        pass

# ============================================================================
# COUNT CONSTRAINTS
# ============================================================================

@dataclass
class CountConstraint(Constraint):
    """Constraints about counts of criminals/innocents in specific areas."""
    
    class CountType(Enum):
        EQUAL = "equal"           # "equal number of criminals in columns B and D"
        MORE_THAN = "more_than"   # "Column C has more innocents than any other column"
        EXACTLY = "exactly"       # "Bruce has exactly 2 innocent neighbors"
        TOTAL = "total"           # "There are 11 innocents in total"
        ONE_OF = "one_of"        # "Tyler is one of 2 criminals below Karen"
    
    count_type: CountType
    target_label: Label  # CRIMINAL or INNOCENT
    areas: List[List[Position]]  # List of areas to compare (e.g., columns, rows, etc.)
    count: Optional[int] = None  # For EXACTLY and TOTAL
    source_position: Optional[Position] = None  # Who gave this hint
    
    def check(self, game_state: GameState) -> List[Tuple[Position, Label, str]]:
        deductions = []
        
        if self.count_type == CountConstraint.CountType.EQUAL:
            # "equal number of criminals in columns B and D"
            if len(self.areas) == 2:
                area1, area2 = self.areas
                count1 = self._count_in_area(game_state, area1, self.target_label)
                count2 = self._count_in_area(game_state, area2, self.target_label)
                
                # If one area has more known, the other must have more unknowns
                if count1 > count2:
                    # Area2 needs more of target_label
                    unknowns = self._get_unknowns_in_area(game_state, area2)
                    if len(unknowns) == count1 - count2:
                        for pos in unknowns:
                            deductions.append((pos, self.target_label, f"Equal count constraint: {self.count_type.value}"))
        
        elif self.count_type == CountConstraint.CountType.MORE_THAN:
            # "Column C has more innocents than any other column"
            target_area = self.areas[0]
            other_areas = self.areas[1:]
            
            target_count = self._count_in_area(game_state, target_area, self.target_label)
            target_unknowns = self._get_unknowns_in_area(game_state, target_area)
            
            # Find max possible count in other areas
            max_other_count = 0
            for area in other_areas:
                area_count = self._count_in_area(game_state, area, self.target_label)
                area_unknowns = self._get_unknowns_in_area(game_state, area)
                max_other_count = max(max_other_count, area_count + len(area_unknowns))
            
            # If target can't possibly have more, this is a contradiction
            if target_count + len(target_unknowns) <= max_other_count:
                # This would indicate an error in our understanding
                pass
        
        elif self.count_type == CountConstraint.CountType.EXACTLY:
            # "Bruce has exactly 2 innocent neighbors"
            target_area = self.areas[0]
            current_count = self._count_in_area(game_state, target_area, self.target_label)
            unknowns = self._get_unknowns_in_area(game_state, target_area)
            
            if current_count + len(unknowns) == self.count:
                # All unknowns must be the target label
                for pos in unknowns:
                    deductions.append((pos, self.target_label, f"Exactly {self.count} constraint"))
        
        elif self.count_type == CountConstraint.CountType.TOTAL:
            # "There are 11 innocents in total"
            current_count = 0
            unknowns = []
            for cell_name, suspect in game_state.cell_map.items():
                if suspect.is_visible and suspect.label == self.target_label:
                    current_count += 1
                elif not suspect.is_visible:
                    row, col = game_state._to_cell_coords(cell_name)
                    unknowns.append(Position(row, col))
            
            if current_count + len(unknowns) == self.count:
                # All unknowns must be the target label
                for pos in unknowns:
                    deductions.append((pos, self.target_label, f"Total count constraint: {self.count}"))
        
        return deductions
    
    def _count_in_area(self, game_state: GameState, area: List[Position], label: Label) -> int:
        """Count characters with specific label in an area."""
        count = 0
        for pos in area:
            for cell_name, suspect in game_state.cell_map.items():
                row, col = game_state._to_cell_coords(cell_name)
                if row == pos.row and col == pos.col:
                    if suspect.is_visible and suspect.label == label:
                        count += 1
                    break
        return count
    
    def _get_unknowns_in_area(self, game_state: GameState, area: List[Position]) -> List[Position]:
        """Get unknown characters in an area."""
        unknowns = []
        for pos in area:
            for cell_name, suspect in game_state.cell_map.items():
                row, col = game_state._to_cell_coords(cell_name)
                if row == pos.row and col == pos.col:
                    if not suspect.is_visible:
                        unknowns.append(pos)
                    break
        return unknowns

# ============================================================================
# POSITIONAL CONSTRAINTS
# ============================================================================

@dataclass
class PositionalConstraint(Constraint):
    """Constraints about relative positions (above, below, left, right, between)."""
    
    class Direction(Enum):
        ABOVE = "above"
        BELOW = "below"
        LEFT = "left"
        RIGHT = "right"
        BETWEEN = "between"
    
    direction: Direction
    source_position: Position  # Who gave this hint
    target_positions: List[Position]  # Positions being described
    target_label: Label
    count: Optional[int] = None  # For "one of N" type constraints
    occupation_filter: Optional[str] = None  # For "innocent cop above Susan"
    
    def check(self, game_state: GameState) -> List[Tuple[Position, Label, str]]:
        deductions = []
        
        if self.direction == PositionalConstraint.Direction.ABOVE:
            # "There is one innocent cop above Susan"
            if self.occupation_filter:
                # Filter by occupation
                matching_positions = []
                for pos in self.target_positions:
                    for cell_name, suspect in game_state.cell_map.items():
                        row, col = game_state._to_cell_coords(cell_name)
                        if row == pos.row and col == pos.col:
                            if suspect.occupation.lower() == self.occupation_filter.lower():
                                matching_positions.append(pos)
                            break
                
                if len(matching_positions) == self.count:
                    # All matching positions must be the target label
                    for pos in matching_positions:
                        # Check if this position is unknown
                        for cell_name, suspect in game_state.cell_map.items():
                            row, col = game_state._to_cell_coords(cell_name)
                            if row == pos.row and col == pos.col and not suspect.is_visible:
                                deductions.append((pos, self.target_label, f"Positional constraint: {self.direction.value}"))
                                break
        
        elif self.direction == PositionalConstraint.Direction.BELOW:
            # "Tyler is one of 2 criminals below Karen"
            if self.count:
                # Count how many of target_label are already known
                known_count = 0
                unknowns = []
                for pos in self.target_positions:
                    for cell_name, suspect in game_state.cell_map.items():
                        row, col = game_state._to_cell_coords(cell_name)
                        if row == pos.row and col == pos.col:
                            if suspect.is_visible and suspect.label == self.target_label:
                                known_count += 1
                            elif not suspect.is_visible:
                                unknowns.append(pos)
                            break
                
                if known_count + len(unknowns) == self.count:
                    # All unknowns must be the target label
                    for pos in unknowns:
                        deductions.append((pos, self.target_label, f"Positional constraint: {self.direction.value}"))
                elif known_count + len(unknowns) > self.count:
                    # We have more unknowns than needed, but we can still make deductions
                    # If we need exactly N criminals and have M unknowns, then M-N must be innocent
                    if known_count < self.count:
                        # We still need some criminals
                        needed_criminals = self.count - known_count
                        if len(unknowns) == needed_criminals + 1:
                            # We have exactly one more unknown than needed criminals
                            # This means exactly one of the unknowns must be innocent
                            # But we can't determine which one, so no deduction
                            pass
        
        return deductions

# ============================================================================
# NEIGHBOR CONSTRAINTS
# ============================================================================

@dataclass
class NeighborConstraint(Constraint):
    """Constraints about neighbors and connectivity."""
    
    class NeighborType(Enum):
        NEIGHBOR = "neighbor"           # "Ollie's neighbor"
        CONNECTED = "connected"         # "All innocents below Carl are connected"
        COMMON_NEIGHBORS = "common"     # "Both innocents above Wanda are Isaac's neighbors"
    
    neighbor_type: NeighborType
    source_position: Position  # Who gave this hint
    target_positions: List[Position]  # Positions being described
    target_label: Label
    reference_position: Optional[Position] = None  # For "Isaac's neighbors"
    
    def check(self, game_state: GameState) -> List[Tuple[Position, Label, str]]:
        deductions = []
        
        if self.neighbor_type == NeighborConstraint.NeighborType.NEIGHBOR:
            # "The only criminal below Ollie is Ollie's neighbor"
            # This is more complex and would need neighbor calculation
            pass
        
        elif self.neighbor_type == NeighborConstraint.NeighborType.CONNECTED:
            # "All innocents below Carl are connected"
            # Check if we can determine connectivity
            pass
        
        elif self.neighbor_type == NeighborConstraint.NeighborType.COMMON_NEIGHBORS:
            # "Both innocents above Wanda are Isaac's neighbors"
            if self.reference_position:
                isaac_neighbors = self._get_neighbors(self.reference_position)
                matching_positions = [pos for pos in self.target_positions
                                    if pos in isaac_neighbors]
                
                if len(matching_positions) == 2:  # "Both"
                    for pos in matching_positions:
                        if game_state[pos].label == Label.UNKNOWN:
                            deductions.append((pos, self.target_label, f"Common neighbor constraint"))
        
        return deductions
    
    def _get_neighbors(self, position: Position) -> List[Position]:
        """Get all 8 neighbors (including diagonal) for a position."""
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue  # Skip self
                new_pos = Position(position.row + dr, position.col + dc)
                if 0 <= new_pos.row < 5 and 0 <= new_pos.col < 4:
                    neighbors.append(new_pos)
        return neighbors

# ============================================================================
# RELATIVE CONSTRAINTS
# ============================================================================

@dataclass
class RelativeConstraint(Constraint):
    """Constraints about relative comparisons between characters."""
    
    class ComparisonType(Enum):
        MORE_THAN = "more_than"     # "Bruce has more criminal neighbors than Vicky"
        CLOSER_TO = "closer_to"     # "closer to Floyd than to Bruce"
    
    comparison_type: ComparisonType
    source_position: Position  # Who gave this hint
    character1: Position
    character2: Position
    target_label: Label
    metric: str  # "criminal neighbors", "distance", etc.
    
    def check(self, game_state: GameState) -> List[Tuple[Position, Label, str]]:
        deductions = []
        
        if self.comparison_type == RelativeConstraint.ComparisonType.MORE_THAN:
            # "Bruce has more criminal neighbors than Vicky"
            # This would require calculating neighbor counts
            pass
        
        elif self.comparison_type == RelativeConstraint.ComparisonType.CLOSER_TO:
            # "The only innocent above me is closer to Floyd than to Bruce"
            # This would require distance calculations
            pass
        
        return deductions

# ============================================================================
# SPECIFIC CHARACTER CONSTRAINTS
# ============================================================================

@dataclass
class SpecificCharacterConstraint(Constraint):
    """Constraints about specific characters being part of a group."""
    
    specific_character: Position  # The specific character (e.g., Tyler)
    target_positions: List[Position]  # All positions in the group
    target_label: Label  # The label the character must have
    count: int  # Total count in the group
    source_position: Position  # Who gave this hint
    
    def check(self, game_state: GameState) -> List[Tuple[Position, Label, str]]:
        deductions = []
        
        # Count how many of target_label are already known in the group
        known_count = 0
        unknowns = []
        for pos in self.target_positions:
            for cell_name, suspect in game_state.cell_map.items():
                row, col = game_state._to_cell_coords(cell_name)
                if row == pos.row and col == pos.col:
                    if suspect.is_visible and suspect.label == self.target_label:
                        known_count += 1
                    elif not suspect.is_visible:
                        unknowns.append(pos)
                    break
        
        # If the specific character is unknown, they must be the target label
        specific_unknown = False
        for cell_name, suspect in game_state.cell_map.items():
            row, col = game_state._to_cell_coords(cell_name)
            if row == self.specific_character.row and col == self.specific_character.col:
                if not suspect.is_visible:
                    specific_unknown = True
                break
        
        if specific_unknown:
            # The specific character must be the target label
            deductions.append((self.specific_character, self.target_label, 
                             f"Specific character constraint: must be {self.target_label.value}"))
        
        return deductions

# ============================================================================
# EXISTENCE CONSTRAINTS
# ============================================================================

@dataclass
class ExistenceConstraint(Constraint):
    """Constraints about existence and uniqueness."""
    
    class ExistenceType(Enum):
        ONLY = "only"           # "The only criminal below Ollie"
        BOTH = "both"           # "Both innocents above Wanda"
        ALL = "all"            # "All innocents in row 3"
    
    existence_type: ExistenceType
    source_position: Position  # Who gave this hint
    target_positions: List[Position]  # Positions being described
    target_label: Label
    additional_condition: Optional[str] = None  # "are Isaac's neighbors"
    
    def check(self, game_state: GameState) -> List[Tuple[Position, Label, str]]:
        deductions = []
        
        if self.existence_type == ExistenceConstraint.ExistenceType.ONLY:
            # "The only criminal below Ollie"
            # If we know there's exactly one criminal below, and we find one, others must be innocent
            pass
        
        elif self.existence_type == ExistenceConstraint.ExistenceType.BOTH:
            # "Both innocents above Wanda"
            # If we know there are exactly two, and we find two, others must be criminal
            pass
        
        elif self.existence_type == ExistenceConstraint.ExistenceType.ALL:
            # "All innocents in row 3"
            # If we know all innocents in row 3 are something, we can deduce others
            pass
        
        return deductions