from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class Label(Enum):
    INNOCENT = "innocent"
    CRIMINAL = "criminal"

@dataclass
class Suspect:
    name: str
    occupation: str
    is_visible: bool

    _hint: Optional[str]
    _label: Optional[Label]

    @classmethod
    def unknown(cls, name: str, occupation: str, hint: Optional[str] = None) -> "Suspect":
        return cls(name, occupation, is_visible=False, _hint=hint, _label=None)

    @classmethod
    def criminal(cls, name: str, occupation: str, hint: Optional[str] = None) -> "Suspect":
        return cls(name, occupation, is_visible=True, _hint=hint, _label=Label.CRIMINAL)
    
    @classmethod
    def innocent(cls, name: str, occupation: str, hint: Optional[str] = None) -> "Suspect":
        return cls(name, occupation, is_visible=True, _hint=hint, _label=Label.INNOCENT)

    @property
    def hint(self) -> Optional[str]:
        if self.is_visible:
            return self._hint

    @property
    def label(self) -> Optional[Label]:
        if self.is_visible:
            return self._label

    def set_label(self, label: Optional[Label]):
        self._label = label

    def set_visible(self, is_visible: bool):
        self.is_visible = is_visible
        
@dataclass
class GameState:
    cell_map: Dict[str, Suspect]

    _COL_NAMES = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    @staticmethod
    def from_grid(grid: List[List[Suspect]]) -> "GameState":
        cell_map = {}
        for row in range(len(grid)):
            for col in range(len(grid[row])):
                cell_map[GameState._to_cell_name(row, col)] = grid[row][col]

        return GameState(cell_map)
    
    @classmethod
    def from_api_data(cls, characters: List[Dict]) -> "GameState":
        """Create GameState from API character data."""
        cell_map = {}
        
        for char_data in characters:
            coord = char_data['coord']
            name = char_data['name']
            profession = char_data['profession']  # Maps to occupation
            label_str = char_data['label']
            hint = char_data.get('hint')
            
            # Create Suspect based on label
            if label_str == "innocent":
                suspect = Suspect.innocent(name, profession, hint)
            elif label_str == "criminal":
                suspect = Suspect.criminal(name, profession, hint)
            else:  # unknown
                suspect = Suspect.unknown(name, profession, hint)
            
            cell_map[coord] = suspect
        
        return cls(cell_map)

    @staticmethod
    def _to_cell_name(row: int, col: int) -> str:
        return f"{GameState._COL_NAMES[col]}{row}"

    def copy(self) -> "GameState":
        return GameState(self.cell_map.copy())

    def _to_cell_coords(self, cell_name: str) -> Tuple[int, int]:
        col = self._COL_NAMES.index(cell_name[0])
        row = int(cell_name[1:])
        return row, col

    def get_suspect(self, name: str) -> Suspect:
        matches = [s for s in self.cell_map.values() if s.name == name]
        if matches:
            return matches[0]
        else:
            raise ValueError(f"Could not find suspect '{name}'")

    def get_unknown_suspects(self) -> List[Suspect]:
        return [s for s in self.cell_map.values() if not s.is_visible]

    def get_known_suspects(self) -> List[Suspect]:
        return [s for s in self.cell_map.values() if s.is_visible]

    def set_label(self, suspect: Suspect, label: Optional[Label], is_visible: bool = True):
        matching_suspects = list(filter(lambda x: x[1].name == suspect.name, self.cell_map.items()))
        if len(matching_suspects) == 0:
            raise ValueError(f"Suspect {suspect.name} not found in game state")
        if len(matching_suspects) > 1:
            raise ValueError(f"Multiple suspects with name {suspect.name} found in game state")

        cell_name, _ = matching_suspects[0]
        self._set_label(cell_name, label, is_visible)

    def _set_label(self, cell_name: str, label: Optional[Label], is_visible: bool):
        self.cell_map[cell_name].set_label(label)
        self.cell_map[cell_name].set_visible(is_visible)
    
    def _parse_coord(self, coord: str) -> Tuple[int, int]:
        """Parse coordinate string (e.g., 'A1') into row, col indices."""
        if not coord or len(coord) < 2:
            raise ValueError(f"Invalid coordinate: {coord}")
        
        col = ord(coord[0].upper()) - ord('A')  # A=0, B=1, etc.
        row = int(coord[1:]) - 1                # 1=0, 2=1, etc.
        return row, col
    
    def get_grid_dimensions(self) -> Tuple[int, int]:
        """Get the dimensions of the grid (rows, cols)."""
        if not self.cell_map:
            return 0, 0
        
        max_row, max_col = 0, 0
        for coord in self.cell_map.keys():
            row, col = self._parse_coord(coord)
            max_row = max(max_row, row)
            max_col = max(max_col, col)
        
        return max_row + 1, max_col + 1
    
    def to_grid(self) -> List[List[Optional[Suspect]]]:
        """Convert the GameState to a 2D grid representation."""
        rows, cols = self.get_grid_dimensions()
        if rows == 0 or cols == 0:
            return []
        
        # Create empty grid
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        
        # Place suspects in grid
        for coord, suspect in self.cell_map.items():
            row, col = self._parse_coord(coord)
            grid[row][col] = suspect
        
        return grid
    
    def render_as_text(self) -> str:
        """Render the game state as a formatted text grid."""
        grid = self.to_grid()
        
        if not grid:
            return "Empty grid"
        
        lines = []
        lines.append("=" * 80)
        lines.append("CLUES GAME GRID")
        lines.append("=" * 80)
        lines.append("")
        
        # Header with column labels
        col_labels = "    " + " ".join(f"{chr(65 + i):^15}" for i in range(len(grid[0])))
        lines.append(col_labels)
        lines.append("    " + "-" * (16 * len(grid[0]) - 1))
        
        for row_idx, row in enumerate(grid):
            # Row number
            row_lines = [f"{row_idx + 1:2d} |"]
            
            # Character info for this row
            for col_idx, suspect in enumerate(row):
                if suspect:
                    name = suspect.name[:12]  # Truncate long names
                    profession = suspect.occupation[:12]
                    
                    # Determine label and marker
                    if suspect.is_visible and suspect.label:
                        label_str = suspect.label.value
                        label_marker = "✓" if suspect.label == Label.INNOCENT else "✗"
                    else:
                        label_str = "unknown"
                        label_marker = "?"
                    
                    coord = f"{chr(65 + col_idx)}{row_idx + 1}"
                    
                    cell = f"{name:^12}\n{profession:^12}\n{label_marker} {label_str:^9}\n{coord:^12}"
                else:
                    cell = f"{'':^12}\n{'[empty]':^12}\n{'':^12}\n{'':^12}"
                
                row_lines.append(cell)
            
            # Split multi-line cells and format
            for line_idx in range(4):  # 4 lines per cell
                line_parts = []
                for cell_idx, cell_data in enumerate(row_lines):
                    if cell_idx == 0:  # Row number
                        if line_idx == 1:  # Middle line for row number
                            line_parts.append(cell_data)
                        else:
                            line_parts.append("   |")
                    else:
                        cell_lines = cell_data.split('\n')
                        if line_idx < len(cell_lines):
                            line_parts.append(f"{cell_lines[line_idx]:^15}")
                        else:
                            line_parts.append(" " * 15)
                
                lines.append(" ".join(line_parts) + " |")
            
            # Separator between rows
            if row_idx < len(grid) - 1:
                lines.append("    " + "-" * (16 * len(grid[0]) - 1))
        
        lines.append("")
        lines.append("Legend: ✓ = Innocent, ✗ = Criminal, ? = Unknown")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def save_grid_to_file(self, filename: str = "debug_grid.txt") -> Optional[str]:
        """Save grid visualization to a file."""
        try:
            grid_text = self.render_as_text()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(grid_text)
            return filename
        except Exception as e:
            print(f"Error saving grid to file: {e}")
            return None
