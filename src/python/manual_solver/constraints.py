from abc import ABC, abstractmethod
from typing import List, Set, Dict, Tuple, Union, Any
from dataclasses import dataclass

from src.python.manual_solver.game_state import GameState, Suspect, Label


@dataclass(frozen=True)
class Position:
    row: int
    col: int

# ============================================================================
# AST-BASED CONSTRAINT SYSTEM
# ============================================================================

class Expression(ABC):
    """Base class for all AST expressions in the constraint system."""
    
    @abstractmethod
    def evaluate(self, game_state: GameState) -> Any:
        """Evaluate this expression against the game state."""
        pass
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}(...)"

class Constraint:
    """A constraint is a boolean expression that must be satisfied."""
    
    def __init__(self, expression: Expression, description: str = ""):
        self.expression = expression
        self.description = description

    @classmethod
    def from_string(cls, description: str) -> "Constraint":
        """Create a constraint from a string."""
        expr = eval(description)
        return cls(expr, description)
    
    def evaluate(self, game_state: GameState) -> bool:
        """Check if this constraint is satisfied."""
        try:
            result = self.expression.evaluate(game_state)
            return bool(result)
        except Exception:
            # If evaluation fails (e.g., unknown character), constraint is not satisfied
            return False
    
    def __str__(self) -> str:
        return f"Constraint({self.expression}) - {self.description}"

# ============================================================================
# PRIMITIVE EXPRESSIONS
# ============================================================================

@dataclass(frozen=True)
class Character(Expression):
    """Reference to a specific character by name."""
    name: str
    
    def evaluate(self, game_state: GameState) -> Position:
        """Return the position of this character."""
        for cell_name, suspect in game_state.cell_map.items():
            if suspect.name.lower() == self.name.lower():
                row, col = game_state._to_cell_coords(cell_name)
                return Position(row, col)
        raise ValueError(f"Character '{self.name}' not found in game state")
    
    def __str__(self) -> str:
        return f"Character({self.name})"

@dataclass(frozen=True)
class CharacterHasLabel(Expression):
    """Check if a specific character has a given label."""
    character_name: str
    label: Label
    
    def evaluate(self, game_state: GameState) -> bool:
        """Return True if the character has the specified label."""
        for cell_name, suspect in game_state.cell_map.items():
            if suspect.name.lower() == self.character_name.lower():
                return suspect.is_visible and suspect.label == self.label
        return False  # Character not found or not visible
    
    def __str__(self) -> str:
        return f"CharacterHasLabel({self.character_name}, {self.label.value})"

@dataclass(frozen=True)
class AllCharacters(Expression):
    """All characters in the game."""
    
    def evaluate(self, game_state: GameState) -> Set[Position]:
        """Return positions of all characters."""
        positions = set()
        for cell_name in game_state.cell_map.keys():
            row, col = game_state._to_cell_coords(cell_name)
            positions.add(Position(row, col))
        return positions
    
    def __str__(self) -> str:
        return "AllCharacters()"

@dataclass(frozen=True)
class Literal(Expression):
    """A literal value (number, string, etc.)."""
    value: Any
    
    def evaluate(self, game_state: GameState) -> Any:
        return self.value
    
    def __str__(self) -> str:
        return f"Literal({self.value})"

# ============================================================================
# SET OPERATIONS
# ============================================================================

@dataclass(frozen=True)
class Filter(Expression):
    """Filter a set of positions by a predicate."""
    source: Expression  # Should evaluate to Set[Position]
    predicate: Expression  # Should be a predicate expression
    
    def evaluate(self, game_state: GameState) -> Set[Position]:
        positions = self.source.evaluate(game_state)
        if not isinstance(positions, set):
            raise ValueError(f"Filter source must evaluate to a set, got {type(positions)}")
        
        filtered = set()
        for pos in positions:
            if self.predicate.evaluate_at(game_state, pos):
                filtered.add(pos)
        return filtered
    
    def __str__(self) -> str:
        return f"Filter({self.source}, {self.predicate})"

@dataclass(frozen=True)
class Neighbors(Expression):
    """Get all neighbors (including diagonal) of a character or position."""
    target: Expression  # Should evaluate to Position
    
    def evaluate(self, game_state: GameState) -> Set[Position]:
        pos = self.target.evaluate(game_state)
        if not isinstance(pos, Position):
            raise ValueError(f"Neighbors target must evaluate to Position, got {type(pos)}")
        
        neighbors = set()
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue  # Skip self
                new_row, new_col = pos.row + dr, pos.col + dc
                if 1 <= new_row <= 5 and 0 <= new_col <= 3:  # Grid bounds: rows 1-5, cols 0-3
                    neighbors.add(Position(new_row, new_col))
        return neighbors
    
    def __str__(self) -> str:
        return f"Neighbors({self.target})"

@dataclass(frozen=True)
class Above(Expression):
    """Get all positions above a character (same column, lower row numbers)."""
    target: Expression  # Should evaluate to Position
    
    def evaluate(self, game_state: GameState) -> Set[Position]:
        pos = self.target.evaluate(game_state)
        if not isinstance(pos, Position):
            raise ValueError(f"Above target must evaluate to Position, got {type(pos)}")
        
        above_positions = set()
        for row in range(1, pos.row):  # All rows above (1 to pos.row-1)
            above_positions.add(Position(row, pos.col))
        return above_positions
    
    def __str__(self) -> str:
        return f"Above({self.target})"

@dataclass(frozen=True)
class Below(Expression):
    """Get all positions below a character (same column, higher row numbers)."""
    target: Expression  # Should evaluate to Position
    
    def evaluate(self, game_state: GameState) -> Set[Position]:
        pos = self.target.evaluate(game_state)
        if not isinstance(pos, Position):
            raise ValueError(f"Below target must evaluate to Position, got {type(pos)}")
        
        below_positions = set()
        for row in range(pos.row + 1, 6):  # All rows below (pos.row+1 to 5)
            below_positions.add(Position(row, pos.col))
        return below_positions
    
    def __str__(self) -> str:
        return f"Below({self.target})"

@dataclass(frozen=True)
class LeftOf(Expression):
    """Get all positions to the left of a character (same row, lower column numbers)."""
    target: Expression  # Should evaluate to Position
    
    def evaluate(self, game_state: GameState) -> Set[Position]:
        pos = self.target.evaluate(game_state)
        if not isinstance(pos, Position):
            raise ValueError(f"LeftOf target must evaluate to Position, got {type(pos)}")
        
        left_positions = set()
        for col in range(pos.col):  # All columns to the left (0 to pos.col-1)
            left_positions.add(Position(pos.row, col))
        return left_positions
    
    def __str__(self) -> str:
        return f"LeftOf({self.target})"

@dataclass(frozen=True)
class RightOf(Expression):
    """Get all positions to the right of a character (same row, higher column numbers)."""
    target: Expression  # Should evaluate to Position
    
    def evaluate(self, game_state: GameState) -> Set[Position]:
        pos = self.target.evaluate(game_state)
        if not isinstance(pos, Position):
            raise ValueError(f"RightOf target must evaluate to Position, got {type(pos)}")
        
        right_positions = set()
        for col in range(pos.col + 1, 4):  # All columns to the right (pos.col+1 to 3)
            right_positions.add(Position(pos.row, col))
        return right_positions
    
    def __str__(self) -> str:
        return f"RightOf({self.target})"

@dataclass(frozen=True)
class Column(Expression):
    """Get all positions in a specific column."""
    column_letter: str  # Column letter (A-D)
    
    def evaluate(self, game_state: GameState) -> Set[Position]:
        if self.column_letter not in ['A', 'B', 'C', 'D']:
            raise ValueError(f"Column letter must be A, B, C, or D, got {self.column_letter}")
        
        # Convert letter to 0-based index
        column_number = ord(self.column_letter) - ord('A')
        
        column_positions = set()
        for row in range(1, 6):  # Rows 1-5
            column_positions.add(Position(row, column_number))
        return column_positions
    
    def __str__(self) -> str:
        return f"Column({self.column_letter})"

@dataclass(frozen=True)
class Row(Expression):
    """Get all positions in a specific row."""
    row_number: int  # Row number (1-indexed)
    
    def evaluate(self, game_state: GameState) -> Set[Position]:
        if not (1 <= self.row_number <= 5):
            raise ValueError(f"Row number must be between 1 and 5, got {self.row_number}")
        
        row_positions = set()
        for col in range(4):  # Columns 0-3
            row_positions.add(Position(self.row_number, col))
        return row_positions
    
    def __str__(self) -> str:
        return f"Row({self.row_number})"

@dataclass(frozen=True)
class EdgePositions(Expression):
    """Get all positions on the edge of the grid."""
    
    def evaluate(self, game_state: GameState) -> Set[Position]:
        edge_positions = set()
        # Top and bottom rows
        for col in range(4):
            edge_positions.add(Position(1, col))  # Top row (row 1)
            edge_positions.add(Position(5, col))  # Bottom row (row 5)
        # Left and right columns (excluding corners already added)
        for row in range(2, 5):
            edge_positions.add(Position(row, 0))  # Left column
            edge_positions.add(Position(row, 3))  # Right column
        return edge_positions
    
    def __str__(self) -> str:
        return "EdgePositions()"

# ============================================================================
# PREDICATES
# ============================================================================

class Predicate(Expression):
    """Base class for predicate expressions that can be evaluated at a position."""
    
    @abstractmethod
    def evaluate_at(self, game_state: GameState, position: Position) -> bool:
        """Evaluate this predicate at a specific position."""
        pass
    
    def evaluate(self, game_state: GameState) -> bool:
        """Default evaluation - not meaningful for predicates without position."""
        raise NotImplementedError("Predicates must be evaluated at a specific position")

@dataclass(frozen=True)
class HasLabel(Predicate):
    """Check if a character at a position has a specific label."""
    label: Label
    
    def evaluate_at(self, game_state: GameState, position: Position) -> bool:
        for cell_name, suspect in game_state.cell_map.items():
            row, col = game_state._to_cell_coords(cell_name)
            if row == position.row and col == position.col:
                return suspect.is_visible and suspect.label == self.label
        return False
    
    def __str__(self) -> str:
        return f"HasLabel({self.label.value})"

@dataclass(frozen=True)
class HasProfession(Predicate):
    """Check if a character at a position has a specific profession."""
    profession: str
    
    def evaluate_at(self, game_state: GameState, position: Position) -> bool:
        for cell_name, suspect in game_state.cell_map.items():
            row, col = game_state._to_cell_coords(cell_name)
            if row == position.row and col == position.col:
                return suspect.occupation.lower() == self.profession.lower()
        return False
    
    def __str__(self) -> str:
        return f"HasProfession({self.profession})"

@dataclass(frozen=True)
class IsEdge(Predicate):
    """Check if a position is on the edge of the grid."""
    
    def evaluate_at(self, game_state: GameState, position: Position) -> bool:
        return (position.row == 1 or position.row == 5 or 
                position.col == 0 or position.col == 3)
    
    def __str__(self) -> str:
        return "IsEdge()"

@dataclass(frozen=True)
class IsUnknown(Predicate):
    """Check if a character at a position has unknown label."""
    
    def evaluate_at(self, game_state: GameState, position: Position) -> bool:
        for cell_name, suspect in game_state.cell_map.items():
            row, col = game_state._to_cell_coords(cell_name)
            if row == position.row and col == position.col:
                return not suspect.is_visible
        return False
    
    def __str__(self) -> str:
        return "IsUnknown()"

# ============================================================================
# AGGREGATIONS
# ============================================================================

@dataclass(frozen=True)
class Count(Expression):
    """Count the number of elements in a set."""
    source: Expression  # Should evaluate to Set[Position]
    
    def evaluate(self, game_state: GameState) -> int:
        result = self.source.evaluate(game_state)
        if isinstance(result, set):
            return len(result)
        elif isinstance(result, (list, tuple)):
            return len(result)
        else:
            raise ValueError(f"Count source must evaluate to a collection, got {type(result)}")
    
    def __str__(self) -> str:
        return f"Count({self.source})"

@dataclass(frozen=True)
class Sum(Expression):
    """Sum numeric values from a collection."""
    source: Expression  # Should evaluate to collection of numbers
    
    def evaluate(self, game_state: GameState) -> Union[int, float]:
        result = self.source.evaluate(game_state)
        if isinstance(result, (set, list, tuple)):
            return sum(result)
        else:
            raise ValueError(f"Sum source must evaluate to a collection, got {type(result)}")
    
    def __str__(self) -> str:
        return f"Sum({self.source})"

@dataclass(frozen=True)
class AreConnected(Expression):
    """Check if all positions in a set are connected (adjacent to each other)."""
    source: Expression  # Should evaluate to Set[Position]
    
    def evaluate(self, game_state: GameState) -> bool:
        positions = self.source.evaluate(game_state)
        if not isinstance(positions, set):
            raise ValueError(f"AreConnected source must evaluate to a set, got {type(positions)}")
        
        if len(positions) <= 1:
            return True  # Single position or empty set is trivially connected
        
        # Use BFS to check connectivity
        positions_list = list(positions)
        visited = {positions_list[0]}
        queue = [positions_list[0]]
        
        while queue:
            current = queue.pop(0)
            # Check all neighbors of current position
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    neighbor = Position(current.row + dr, current.col + dc)
                    if neighbor in positions and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
        
        return len(visited) == len(positions)
    
    def __str__(self) -> str:
        return f"AreConnected({self.source})"

# ============================================================================
# COMPARISON OPERATIONS
# ============================================================================

@dataclass(frozen=True)
class Equal(Expression):
    """Check if two expressions evaluate to equal values."""
    left: Expression
    right: Expression
    
    def evaluate(self, game_state: GameState) -> bool:
        left_val = self.left.evaluate(game_state)
        right_val = self.right.evaluate(game_state)
        return left_val == right_val
    
    def __str__(self) -> str:
        return f"Equal({self.left}, {self.right})"

@dataclass(frozen=True)
class Greater(Expression):
    """Check if left expression is greater than right expression."""
    left: Expression
    right: Expression
    
    def evaluate(self, game_state: GameState) -> bool:
        left_val = self.left.evaluate(game_state)
        right_val = self.right.evaluate(game_state)
        return left_val > right_val
    
    def __str__(self) -> str:
        return f"Greater({self.left}, {self.right})"

@dataclass(frozen=True)
class GreaterEqual(Expression):
    """Check if left expression is greater than or equal to right expression."""
    left: Expression
    right: Expression
    
    def evaluate(self, game_state: GameState) -> bool:
        left_val = self.left.evaluate(game_state)
        right_val = self.right.evaluate(game_state)
        return left_val >= right_val
    
    def __str__(self) -> str:
        return f"GreaterEqual({self.left}, {self.right})"

@dataclass(frozen=True)
class Less(Expression):
    """Check if left expression is less than right expression."""
    left: Expression
    right: Expression
    
    def evaluate(self, game_state: GameState) -> bool:
        left_val = self.left.evaluate(game_state)
        right_val = self.right.evaluate(game_state)
        return left_val < right_val
    
    def __str__(self) -> str:
        return f"Less({self.left}, {self.right})"

@dataclass(frozen=True)
class LessEqual(Expression):
    """Check if left expression is less than or equal to right expression."""
    left: Expression
    right: Expression
    
    def evaluate(self, game_state: GameState) -> bool:
        left_val = self.left.evaluate(game_state)
        right_val = self.right.evaluate(game_state)
        return left_val <= right_val
    
    def __str__(self) -> str:
        return f"LessEqual({self.left}, {self.right})"

@dataclass(frozen=True)
class IsOdd(Expression):
    """Check if a number is odd."""
    number: Expression
    
    def evaluate(self, game_state: GameState) -> bool:
        return self.number.evaluate(game_state) % 2 == 1
    
    def __str__(self) -> str:
        return f"IsOdd({self.number})"

@dataclass(frozen=True)
class IsEven(Expression):
    """Check if a number is even."""
    number: Expression
    
    def evaluate(self, game_state: GameState) -> bool:
        return self.number.evaluate(game_state) % 2 == 0

    def __str__(self) -> str:
        return f"IsEven({self.number})"

# ============================================================================
# LOGICAL OPERATIONS
# ============================================================================

@dataclass(frozen=True)
class And(Expression):
    """Logical AND of multiple expressions."""
    expressions: Tuple[Expression, ...]
    
    def __init__(self, *expressions: Expression):
        object.__setattr__(self, 'expressions', expressions)
    
    def evaluate(self, game_state: GameState) -> bool:
        return all(expr.evaluate(game_state) for expr in self.expressions)
        
    def __str__(self) -> str:
        return f"And({', '.join(str(expr) for expr in self.expressions)})"

@dataclass(frozen=True)
class Or(Expression):
    """Logical OR of multiple expressions."""
    expressions: Tuple[Expression, ...]
    
    def __init__(self, *expressions: Expression):
        object.__setattr__(self, 'expressions', expressions)
    
    def evaluate(self, game_state: GameState) -> bool:
        return any(expr.evaluate(game_state) for expr in self.expressions)
    
    def __str__(self) -> str:
        return f"Or({', '.join(str(expr) for expr in self.expressions)})"

@dataclass(frozen=True)
class Not(Expression):
    """Logical NOT of an expression."""
    expression: Expression
    
    def evaluate(self, game_state: GameState) -> bool:
        return not self.expression.evaluate(game_state)
    
    def __str__(self) -> str:
        return f"Not({self.expression})"

# ============================================================================
# SET OPERATIONS (ADDITIONAL)
# ============================================================================

@dataclass(frozen=True)
class Union(Expression):
    """Union of multiple sets."""
    expressions: Tuple[Expression, ...]
    
    def __init__(self, *expressions: Expression):
        object.__setattr__(self, 'expressions', expressions)
    
    def evaluate(self, game_state: GameState) -> Set[Position]:
        result = set()
        for expr in self.expressions:
            expr_result = expr.evaluate(game_state)
            if isinstance(expr_result, set):
                result |= expr_result
            else:
                raise ValueError(f"Union operand must evaluate to a set, got {type(expr_result)}")
        return result
        
    def __str__(self) -> str:
        return f"Union({', '.join(str(expr) for expr in self.expressions)})"

@dataclass(frozen=True)
class Intersection(Expression):
    """Intersection of multiple sets."""
    expressions: Tuple[Expression, ...]
    
    def __init__(self, *expressions: Expression):
        object.__setattr__(self, 'expressions', expressions)
    
    def evaluate(self, game_state: GameState) -> Set[Position]:
        if not self.expressions:
            return set()
        
        result = self.expressions[0].evaluate(game_state)
        if not isinstance(result, set):
            raise ValueError(f"Intersection operand must evaluate to a set, got {type(result)}")
        
        for expr in self.expressions[1:]:
            expr_result = expr.evaluate(game_state)
            if isinstance(expr_result, set):
                result &= expr_result
            else:
                raise ValueError(f"Intersection operand must evaluate to a set, got {type(expr_result)}")
        return result
    
    def __str__(self) -> str:
        return f"Intersection({', '.join(str(expr) for expr in self.expressions)})"

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def neighbors_of(character_name: str) -> Expression:
    """Convenience function to get neighbors of a character."""
    return Neighbors(Character(character_name))

def above(character_name: str) -> Expression:
    """Convenience function to get positions above a character."""
    return Above(Character(character_name))

def below(character_name: str) -> Expression:
    """Convenience function to get positions below a character."""
    return Below(Character(character_name))

def left_of(character_name: str) -> Expression:
    """Convenience function to get positions left of a character."""
    return LeftOf(Character(character_name))

def right_of(character_name: str) -> Expression:
    """Convenience function to get positions right of a character."""
    return RightOf(Character(character_name))

def innocents(area_expr: Expression) -> Expression:
    """Convenience function to filter for innocents in an area."""
    return Filter(area_expr, HasLabel(Label.INNOCENT))

def criminals(area_expr: Expression) -> Expression:
    """Convenience function to filter for criminals in an area."""
    return Filter(area_expr, HasLabel(Label.CRIMINAL))

def count_innocents(area_expr: Expression) -> Expression:
    """Convenience function to count innocents in an area."""
    return Count(innocents(area_expr))

def count_criminals(area_expr: Expression) -> Expression:
    """Convenience function to count criminals in an area."""
    return Count(criminals(area_expr))


if __name__ == "__main__":
    description = "Equal(Count(Filter(Filter(AllCharacters(), Or(HasProfession(\"cop\"), HasProfession(\"sleuth\"))), HasLabel(Label.INNOCENT))), Literal(4))"
    res = Constraint.from_string(description)
    print(res)