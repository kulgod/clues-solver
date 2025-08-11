import re
from typing import List, Dict, Optional, Tuple
from .constraints import (
    Constraint, CountConstraint, PositionalConstraint, NeighborConstraint, 
    RelativeConstraint, ExistenceConstraint, Position, Label
)

class ConstraintParser:
    """Parser that converts natural language hints into structured constraints."""
    
    def __init__(self):
        # Name to position mapping (will be set when parsing)
        self.name_to_position: Dict[str, Position] = {}
        self.position_to_name: Dict[Position, str] = {}
    
    def set_name_mapping(self, name_to_position: Dict[str, Position]):
        """Set the mapping from character names to positions."""
        self.name_to_position = name_to_position
        self.position_to_name = {pos: name for name, pos in name_to_position.items()}
    
    def parse_hint(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse a hint into one or more constraints."""
        hint_lower = hint.lower()
        constraints = []
        
        # Count constraints
        if "equal number" in hint_lower:
            constraints.extend(self._parse_equal_count(hint_lower, source_position))
        elif "more" in hint_lower and "than" in hint_lower:
            constraints.extend(self._parse_more_than(hint_lower, source_position))
        elif "exactly" in hint_lower:
            constraints.extend(self._parse_exactly(hint_lower, source_position))
        elif "in total" in hint_lower:
            constraints.extend(self._parse_total_count(hint_lower, source_position))
        elif "one of" in hint_lower:
            constraints.extend(self._parse_one_of(hint_lower, source_position))
        
        # Positional constraints
        elif "above" in hint_lower:
            constraints.extend(self._parse_above_below(hint_lower, source_position, "above"))
        elif "below" in hint_lower:
            constraints.extend(self._parse_above_below(hint_lower, source_position, "below"))
        elif "left" in hint_lower:
            constraints.extend(self._parse_left_right(hint_lower, source_position, "left"))
        elif "right" in hint_lower:
            constraints.extend(self._parse_left_right(hint_lower, source_position, "right"))
        elif "between" in hint_lower:
            constraints.extend(self._parse_between(hint_lower, source_position))
        
        # Neighbor constraints
        elif "neighbor" in hint_lower:
            constraints.extend(self._parse_neighbor(hint_lower, source_position))
        elif "connected" in hint_lower:
            constraints.extend(self._parse_connected(hint_lower, source_position))
        
        # Relative constraints
        elif "more" in hint_lower and "than" in hint_lower and "neighbor" in hint_lower:
            constraints.extend(self._parse_relative_neighbors(hint_lower, source_position))
        elif "closer to" in hint_lower:
            constraints.extend(self._parse_closer_to(hint_lower, source_position))
        
        # Existence constraints
        elif "only" in hint_lower:
            constraints.extend(self._parse_only(hint_lower, source_position))
        elif "both" in hint_lower:
            constraints.extend(self._parse_both(hint_lower, source_position))
        elif "all" in hint_lower:
            constraints.extend(self._parse_all(hint_lower, source_position))
        
        return constraints
    
    def _parse_equal_count(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse 'equal number of criminals in columns B and D'"""
        constraints = []
        
        # Extract label (criminal/innocent)
        if "criminal" in hint:
            label = Label.CRIMINAL
        elif "innocent" in hint:
            label = Label.INNOCENT
        else:
            return constraints
        
        # Extract columns
        col_match = re.search(r'columns? ([a-d]) and ([a-d])', hint)
        if col_match:
            col1, col2 = col_match.group(1), col_match.group(2)
            area1 = self._get_column_positions(ord(col1) - ord('a'))
            area2 = self._get_column_positions(ord(col2) - ord('a'))
            
            constraints.append(CountConstraint(
                count_type=CountConstraint.CountType.EQUAL,
                target_label=label,
                areas=[area1, area2],
                source_position=source_position
            ))
        
        return constraints
    
    def _parse_more_than(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse 'Column C has more innocents than any other column'"""
        constraints = []
        
        # Extract label
        if "criminal" in hint:
            label = Label.CRIMINAL
        elif "innocent" in hint:
            label = Label.INNOCENT
        else:
            return constraints
        
        # Extract column
        col_match = re.search(r'column ([a-d])', hint)
        if col_match:
            target_col = ord(col_match.group(1)) - ord('a')
            target_area = self._get_column_positions(target_col)
            other_areas = [self._get_column_positions(col) for col in range(4) if col != target_col]
            
            constraints.append(CountConstraint(
                count_type=CountConstraint.CountType.MORE_THAN,
                target_label=label,
                areas=[target_area] + other_areas,
                source_position=source_position
            ))
        
        return constraints
    
    def _parse_exactly(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse 'Bruce has exactly 2 innocent neighbors'"""
        constraints = []
        
        # Extract number
        num_match = re.search(r'exactly (\d+)', hint)
        if not num_match:
            return constraints
        
        count = int(num_match.group(1))
        
        # Extract label
        if "criminal" in hint:
            label = Label.CRIMINAL
        elif "innocent" in hint:
            label = Label.INNOCENT
        else:
            return constraints
        
        # Extract character name
        name_match = re.search(r'(\w+) has exactly', hint)
        if name_match:
            char_name = name_match.group(1)
            if char_name in self.name_to_position:
                char_pos = self.name_to_position[char_name]
                neighbors = self._get_neighbors(char_pos)
                
                constraints.append(CountConstraint(
                    count_type=CountConstraint.CountType.EXACTLY,
                    target_label=label,
                    areas=[neighbors],
                    count=count,
                    source_position=source_position
                ))
        
        return constraints
    
    def _parse_total_count(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse 'There are 11 innocents in total'"""
        constraints = []
        
        # Extract number
        num_match = re.search(r'(\d+) (criminal|innocent)', hint)
        if not num_match:
            return constraints
        
        count = int(num_match.group(1))
        label = Label.CRIMINAL if num_match.group(2) == "criminal" else Label.INNOCENT
        
        # Get all positions
        all_positions = list(self.name_to_position.values())
        
        constraints.append(CountConstraint(
            count_type=CountConstraint.CountType.TOTAL,
            target_label=label,
            areas=[all_positions],
            count=count,
            source_position=source_position
        ))
        
        return constraints
    
    def _parse_one_of(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse 'Tyler is one of 2 criminals below Karen'"""
        constraints = []
        
        # Extract number
        num_match = re.search(r'one of (\d+)', hint)
        if not num_match:
            return constraints
        
        count = int(num_match.group(1))
        
        # Extract label
        if "criminal" in hint:
            label = Label.CRIMINAL
        elif "innocent" in hint:
            label = Label.INNOCENT
        else:
            return constraints
        
        # Extract direction and reference character
        if "below" in hint:
            direction = "below"
        elif "above" in hint:
            direction = "above"
        else:
            return constraints
        
        # Find reference character (e.g., "Karen")
        for name, pos in self.name_to_position.items():
            if name.lower() in hint and name.lower() != "one":
                ref_pos = pos
                target_positions = self._get_positions_in_direction(ref_pos, direction)
                
                constraints.append(PositionalConstraint(
                    direction=PositionalConstraint.Direction.BELOW if direction == "below" else PositionalConstraint.Direction.ABOVE,
                    source_position=source_position,
                    target_positions=target_positions,
                    target_label=label,
                    count=count
                ))
                break
        
        return constraints
    
    def _parse_above_below(self, hint: str, source_position: Position, direction: str) -> List[Constraint]:
        """Parse 'There is one innocent cop above Susan'"""
        constraints = []
        
        # Extract number
        num_match = re.search(r'(\d+)', hint)
        count = int(num_match.group(1)) if num_match else 1
        
        # Extract label
        if "criminal" in hint:
            label = Label.CRIMINAL
        elif "innocent" in hint:
            label = Label.INNOCENT
        else:
            return constraints
        
        # Extract occupation filter
        occupation = None
        if "cop" in hint:
            occupation = "cop"
        elif "judge" in hint:
            occupation = "judge"
        # Add more occupations as needed
        
        # Find reference character
        for name, pos in self.name_to_position.items():
            if name.lower() in hint:
                ref_pos = pos
                target_positions = self._get_positions_in_direction(ref_pos, direction)
                
                constraints.append(PositionalConstraint(
                    direction=PositionalConstraint.Direction.ABOVE if direction == "above" else PositionalConstraint.Direction.BELOW,
                    source_position=source_position,
                    target_positions=target_positions,
                    target_label=label,
                    count=count,
                    occupation_filter=occupation
                ))
                break
        
        return constraints
    
    def _parse_neighbor(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse 'Both innocents above Wanda are Isaac's neighbors'"""
        constraints = []
        
        # Extract label
        if "criminal" in hint:
            label = Label.CRIMINAL
        elif "innocent" in hint:
            label = Label.INNOCENT
        else:
            return constraints
        
        # Find reference character (e.g., "Isaac")
        ref_pos = None
        for name, pos in self.name_to_position.items():
            if name.lower() in hint and "'s" in hint:
                ref_pos = pos
                break
        
        if ref_pos:
            # Find target character (e.g., "Wanda")
            target_pos = None
            for name, pos in self.name_to_position.items():
                if name.lower() in hint and name.lower() != self.position_to_name[ref_pos].lower():
                    target_pos = pos
                    break
            
            if target_pos:
                # Get positions above/below target
                if "above" in hint:
                    target_positions = self._get_positions_in_direction(target_pos, "above")
                elif "below" in hint:
                    target_positions = self._get_positions_in_direction(target_pos, "below")
                else:
                    return constraints
                
                constraints.append(NeighborConstraint(
                    neighbor_type=NeighborConstraint.NeighborType.COMMON_NEIGHBORS,
                    source_position=source_position,
                    target_positions=target_positions,
                    target_label=label,
                    reference_position=ref_pos
                ))
        
        return constraints
    
    def _parse_connected(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse 'All innocents below Carl are connected'"""
        constraints = []
        
        # Extract label
        if "criminal" in hint:
            label = Label.CRIMINAL
        elif "innocent" in hint:
            label = Label.INNOCENT
        else:
            return constraints
        
        # Find reference character
        for name, pos in self.name_to_position.items():
            if name.lower() in hint:
                ref_pos = pos
                
                # Get positions in direction
                if "above" in hint:
                    target_positions = self._get_positions_in_direction(ref_pos, "above")
                elif "below" in hint:
                    target_positions = self._get_positions_in_direction(ref_pos, "below")
                elif "left" in hint:
                    target_positions = self._get_positions_in_direction(ref_pos, "left")
                elif "right" in hint:
                    target_positions = self._get_positions_in_direction(ref_pos, "right")
                else:
                    return constraints
                
                constraints.append(NeighborConstraint(
                    neighbor_type=NeighborConstraint.NeighborType.CONNECTED,
                    source_position=source_position,
                    target_positions=target_positions,
                    target_label=label
                ))
                break
        
        return constraints
    
    def _parse_relative_neighbors(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse 'Bruce has more criminal neighbors than Vicky'"""
        constraints = []
        
        # Extract label
        if "criminal" in hint:
            label = Label.CRIMINAL
        elif "innocent" in hint:
            label = Label.INNOCENT
        else:
            return constraints
        
        # Find the two characters being compared
        char1_pos = None
        char2_pos = None
        
        for name, pos in self.name_to_position.items():
            if name.lower() in hint:
                if char1_pos is None:
                    char1_pos = pos
                else:
                    char2_pos = pos
                    break
        
        if char1_pos and char2_pos:
            constraints.append(RelativeConstraint(
                comparison_type=RelativeConstraint.ComparisonType.MORE_THAN,
                source_position=source_position,
                character1=char1_pos,
                character2=char2_pos,
                target_label=label,
                metric="neighbors"
            ))
        
        return constraints
    
    def _parse_only(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse 'The only criminal below Ollie'"""
        constraints = []
        
        # Extract label
        if "criminal" in hint:
            label = Label.CRIMINAL
        elif "innocent" in hint:
            label = Label.INNOCENT
        else:
            return constraints
        
        # Find reference character
        for name, pos in self.name_to_position.items():
            if name.lower() in hint:
                ref_pos = pos
                
                # Get positions in direction
                if "above" in hint:
                    target_positions = self._get_positions_in_direction(ref_pos, "above")
                elif "below" in hint:
                    target_positions = self._get_positions_in_direction(ref_pos, "below")
                else:
                    return constraints
                
                constraints.append(ExistenceConstraint(
                    existence_type=ExistenceConstraint.ExistenceType.ONLY,
                    source_position=source_position,
                    target_positions=target_positions,
                    target_label=label
                ))
                break
        
        return constraints
    
    def _parse_both(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse 'Both innocents above Wanda'"""
        constraints = []
        
        # Extract label
        if "criminal" in hint:
            label = Label.CRIMINAL
        elif "innocent" in hint:
            label = Label.INNOCENT
        else:
            return constraints
        
        # Find reference character
        for name, pos in self.name_to_position.items():
            if name.lower() in hint:
                ref_pos = pos
                
                # Get positions in direction
                if "above" in hint:
                    target_positions = self._get_positions_in_direction(ref_pos, "above")
                elif "below" in hint:
                    target_positions = self._get_positions_in_direction(ref_pos, "below")
                else:
                    return constraints
                
                constraints.append(ExistenceConstraint(
                    existence_type=ExistenceConstraint.ExistenceType.BOTH,
                    source_position=source_position,
                    target_positions=target_positions,
                    target_label=label
                ))
                break
        
        return constraints
    
    def _parse_all(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse 'All innocents in row 3'"""
        constraints = []
        
        # Extract label
        if "criminal" in hint:
            label = Label.CRIMINAL
        elif "innocent" in hint:
            label = Label.INNOCENT
        else:
            return constraints
        
        # Extract row/column
        row_match = re.search(r'row (\d+)', hint)
        if row_match:
            row = int(row_match.group(1)) - 1  # Convert to 0-indexed
            target_positions = self._get_row_positions(row)
            
            constraints.append(ExistenceConstraint(
                existence_type=ExistenceConstraint.ExistenceType.ALL,
                source_position=source_position,
                target_positions=target_positions,
                target_label=label
            ))
        
        return constraints
    
    def _parse_left_right(self, hint: str, source_position: Position, direction: str) -> List[Constraint]:
        """Parse left/right constraints"""
        # Similar to above/below but for horizontal directions
        return []
    
    def _parse_between(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse 'between Bruce and Rob'"""
        # Extract two characters and find positions between them
        return []
    
    def _parse_closer_to(self, hint: str, source_position: Position) -> List[Constraint]:
        """Parse 'closer to Floyd than to Bruce'"""
        # Extract two reference characters and calculate distances
        return []
    
    # Helper methods
    def _get_column_positions(self, col: int) -> List[Position]:
        """Get all positions in a column."""
        return [Position(row, col) for row in range(5)]
    
    def _get_row_positions(self, row: int) -> List[Position]:
        """Get all positions in a row."""
        return [Position(row, col) for col in range(4)]
    
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
    
    def _get_positions_in_direction(self, position: Position, direction: str) -> List[Position]:
        """Get positions in a specific direction from a position."""
        positions = []
        
        if direction == "above":
            for row in range(position.row):
                positions.append(Position(row, position.col))
        elif direction == "below":
            for row in range(position.row + 1, 5):
                positions.append(Position(row, position.col))
        elif direction == "left":
            for col in range(position.col):
                positions.append(Position(position.row, col))
        elif direction == "right":
            for col in range(position.col + 1, 4):
                positions.append(Position(position.row, col))
        
        return positions

