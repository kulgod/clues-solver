from abc import ABC, abstractmethod
from typing import List, Set, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum

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
    
    @abstractmethod
    def get_dependencies(self) -> Set[str]:
        """Return character names this expression depends on."""
        pass
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}(...)"

class Constraint:
    """A constraint is a boolean expression that must be satisfied."""
    
    def __init__(self, expression: Expression, description: str = ""):
        self.expression = expression
        self.description = description
    
    def evaluate(self, game_state: GameState) -> bool:
        """Check if this constraint is satisfied."""
        try:
            result = self.expression.evaluate(game_state)
            return bool(result)
        except Exception:
            # If evaluation fails (e.g., unknown character), constraint is not satisfied
            return False
    
    def get_dependencies(self) -> Set[str]:
        """Get all character names this constraint depends on."""
        return self.expression.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return {self.name}
    
    def __str__(self) -> str:
        return f"Character({self.name})"

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
    
    def get_dependencies(self) -> Set[str]:
        return set()  # Doesn't depend on specific characters
    
    def __str__(self) -> str:
        return "AllCharacters()"

@dataclass(frozen=True)
class Literal(Expression):
    """A literal value (number, string, etc.)."""
    value: Any
    
    def evaluate(self, game_state: GameState) -> Any:
        return self.value
    
    def get_dependencies(self) -> Set[str]:
        return set()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.source.get_dependencies() | self.predicate.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.target.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.target.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.target.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.target.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.target.get_dependencies()
    
    def __str__(self) -> str:
        return f"RightOf({self.target})"

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
    
    def get_dependencies(self) -> Set[str]:
        return set()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return set()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return set()
    
    def __str__(self) -> str:
        return f"HasProfession({self.profession})"

@dataclass(frozen=True)
class IsEdge(Predicate):
    """Check if a position is on the edge of the grid."""
    
    def evaluate_at(self, game_state: GameState, position: Position) -> bool:
        return (position.row == 1 or position.row == 5 or 
                position.col == 0 or position.col == 3)
    
    def get_dependencies(self) -> Set[str]:
        return set()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return set()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.source.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.source.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.source.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.left.get_dependencies() | self.right.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.left.get_dependencies() | self.right.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.left.get_dependencies() | self.right.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.left.get_dependencies() | self.right.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        return self.left.get_dependencies() | self.right.get_dependencies()
    
    def __str__(self) -> str:
        return f"LessEqual({self.left}, {self.right})"

@dataclass(frozen=True)
class IsOdd(Expression):
    """Check if a number is odd."""
    number: Expression
    
    def evaluate(self, game_state: GameState) -> bool:
        return self.number.evaluate(game_state) % 2 == 1
    
    def get_dependencies(self) -> Set[str]:
        return self.number.get_dependencies()
    
    def __str__(self) -> str:
        return f"IsOdd({self.number})"

@dataclass(frozen=True)
class IsEven(Expression):
    """Check if a number is even."""
    number: Expression
    
    def evaluate(self, game_state: GameState) -> bool:
        return self.number.evaluate(game_state) % 2 == 0

    def get_dependencies(self) -> Set[str]:
        return self.number.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        deps = set()
        for expr in self.expressions:
            deps |= expr.get_dependencies()
        return deps
    
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
    
    def get_dependencies(self) -> Set[str]:
        deps = set()
        for expr in self.expressions:
            deps |= expr.get_dependencies()
        return deps
    
    def __str__(self) -> str:
        return f"Or({', '.join(str(expr) for expr in self.expressions)})"

@dataclass(frozen=True)
class Not(Expression):
    """Logical NOT of an expression."""
    expression: Expression
    
    def evaluate(self, game_state: GameState) -> bool:
        return not self.expression.evaluate(game_state)
    
    def get_dependencies(self) -> Set[str]:
        return self.expression.get_dependencies()
    
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
    
    def get_dependencies(self) -> Set[str]:
        deps = set()
        for expr in self.expressions:
            deps |= expr.get_dependencies()
        return deps
    
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
    
    def get_dependencies(self) -> Set[str]:
        deps = set()
        for expr in self.expressions:
            deps |= expr.get_dependencies()
        return deps
    
    def __str__(self) -> str:
        return f"Intersection({', '.join(str(expr) for expr in self.expressions)})"

# ============================================================================
# CONSTRAINT EVALUATION ENGINE
# ============================================================================

class ConstraintEngine:
    """Engine for evaluating constraints and finding deductions."""
    
    def __init__(self):
        self.constraints: List[Constraint] = []
    
    def add_constraint(self, constraint: Constraint):
        """Add a constraint to the engine."""
        self.constraints.append(constraint)
    
    def add_constraints(self, constraints: List[Constraint]):
        """Add multiple constraints to the engine."""
        self.constraints.extend(constraints)
    
    def clear_constraints(self):
        """Clear all constraints."""
        self.constraints.clear()
    
    def evaluate_all(self, game_state: GameState) -> Dict[str, bool]:
        """Evaluate all constraints and return their satisfaction status."""
        results = {}
        for i, constraint in enumerate(self.constraints):
            try:
                results[f"constraint_{i}"] = constraint.evaluate(game_state)
            except Exception as e:
                results[f"constraint_{i}"] = False
                print(f"Error evaluating constraint {i}: {e}")
        return results
    
    def find_violations(self, game_state: GameState) -> List[Tuple[int, Constraint, str]]:
        """Find constraints that are violated in the current game state."""
        violations = []
        for i, constraint in enumerate(self.constraints):
            try:
                if not constraint.evaluate(game_state):
                    violations.append((i, constraint, "Constraint not satisfied"))
            except Exception as e:
                violations.append((i, constraint, f"Evaluation error: {e}"))
        return violations
    
    def test_assignment(self, game_state: GameState, character_name: str, label: Label) -> bool:
        """Test if assigning a label to a character violates any constraints."""
        # Create a test game state
        test_state = game_state.copy()
        
        # Find the character and assign the label
        for cell_name, suspect in test_state.cell_map.items():
            if suspect.name.lower() == character_name.lower():
                test_state._set_label(cell_name, label)
                break
        else:
            raise ValueError(f"Character '{character_name}' not found")
        
        # Check if any constraints are violated
        violations = self.find_violations(test_state)
        return len(violations) == 0
    
    def find_forced_assignments(self, game_state: GameState) -> List[Tuple[str, Label, str]]:
        """Find character assignments that are forced by the constraints."""
        forced = []
        
        # Get all unknown characters
        unknown_characters = []
        for cell_name, suspect in game_state.cell_map.items():
            if not suspect.is_visible:
                unknown_characters.append(suspect.name)
        
        # Test each unknown character with both labels
        for char_name in unknown_characters:
            innocent_valid = self.test_assignment(game_state, char_name, Label.INNOCENT)
            criminal_valid = self.test_assignment(game_state, char_name, Label.CRIMINAL)
            
            if innocent_valid and not criminal_valid:
                forced.append((char_name, Label.INNOCENT, "Only innocent assignment is valid"))
            elif criminal_valid and not innocent_valid:
                forced.append((char_name, Label.CRIMINAL, "Only criminal assignment is valid"))
            elif not innocent_valid and not criminal_valid:
                forced.append((char_name, None, "No valid assignment - contradiction detected"))
        
        return forced

# ============================================================================
# CONSTRAINT BUILDER HELPERS
# ============================================================================

class ConstraintBuilder:
    """Helper class for building common constraint patterns."""
    
    @staticmethod
    def neighbor_count_comparison(char1_name: str, char2_name: str, label: Label, comparison: str) -> Constraint:
        """Build constraint like 'Jose has more innocent neighbors than Ethan'."""
        char1_neighbors = Count(Filter(Neighbors(Character(char1_name)), HasLabel(label)))
        char2_neighbors = Count(Filter(Neighbors(Character(char2_name)), HasLabel(label)))
        
        if comparison.lower() == "more":
            expr = Greater(char1_neighbors, char2_neighbors)
        elif comparison.lower() == "equal":
            expr = Equal(char1_neighbors, char2_neighbors)
        elif comparison.lower() == "less":
            expr = Less(char1_neighbors, char2_neighbors)
        else:
            raise ValueError(f"Unknown comparison: {comparison}")
        
        return Constraint(expr, f"{char1_name} has {comparison} {label.value} neighbors than {char2_name}")
    
    @staticmethod
    def exact_count_in_area(area_expr: Expression, label: Label, count: int) -> Constraint:
        """Build constraint like 'exactly N innocents in area'."""
        count_expr = Count(Filter(area_expr, HasLabel(label)))
        expr = Equal(count_expr, Literal(count))
        return Constraint(expr, f"Exactly {count} {label.value}s in area")
    
    @staticmethod
    def connectivity_constraint(area_expr: Expression, label: Label) -> Constraint:
        """Build constraint like 'all innocents in area are connected'."""
        filtered_area = Filter(area_expr, HasLabel(label))
        expr = AreConnected(filtered_area)
        return Constraint(expr, f"All {label.value}s in area are connected")
    
    @staticmethod
    def edge_constraint(area_expr: Expression, label: Label, count: int) -> Constraint:
        """Build constraint like 'N of the innocents in area are on edges'."""
        innocents_in_area = Filter(area_expr, HasLabel(label))
        innocents_on_edge = Intersection(innocents_in_area, EdgePositions())
        count_expr = Count(innocents_on_edge)
        expr = Equal(count_expr, Literal(count))
        return Constraint(expr, f"{count} of the {label.value}s in area are on edges")
    
    @staticmethod
    def total_profession_count(profession: str, label: Label, count: int) -> Constraint:
        """Build constraint like 'there are 4 innocent cops and sleuths'."""
        if isinstance(profession, str):
            professions = [profession]
        else:
            professions = profession
        
        # Filter all characters by profession and label
        profession_filters = []
        for prof in professions:
            profession_filters.append(Filter(AllCharacters(), 
                                           And(HasProfession(prof), HasLabel(label))))
        
        if len(profession_filters) == 1:
            filtered_chars = profession_filters[0]
        else:
            filtered_chars = Union(*profession_filters)
        
        count_expr = Count(filtered_chars)
        expr = Equal(count_expr, Literal(count))
        return Constraint(expr, f"Total of {count} {label.value} {'/'.join(professions)}")

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

