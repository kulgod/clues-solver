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
    def label(self) -> Optional[str]:
        if self.is_visible:
            return self._label

    def set_label(self, label: Label):
        self._label = label
        
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

    @staticmethod
    def _to_cell_name(row: int, col: int) -> str:
        return f"{GameState._COL_NAMES[col]}{row}"

    def copy(self) -> "GameState":
        return GameState(self.cell_map.copy())

    def _to_cell_coords(self, cell_name: str) -> Tuple[int, int]:
        col = self._COL_NAMES.index(cell_name[0])
        row = int(cell_name[1:])
        return row, col

    def get_suspect(self, row: int, col: int) -> Suspect:
        return self.cell_map[self._to_cell_name(row, col)]

    def get_unknown_suspects(self) -> List[Suspect]:
        return [s for s in self.cell_map.values() if not s.is_visible]

    def get_known_suspects(self) -> List[Suspect]:
        return [s for s in self.cell_map.values() if s.is_visible]

    def set_label(self, suspect: Suspect, label: Label):
        matching_suspects = list(filter(lambda x: x[1].name == suspect.name, self.cell_map.items()))
        if len(matching_suspects) == 0:
            raise ValueError(f"Suspect {suspect.name} not found in game state")
        if len(matching_suspects) > 1:
            raise ValueError(f"Multiple suspects with name {suspect.name} found in game state")

        cell_name, found_suspect = matching_suspects[0]
        self._set_label(cell_name, label)

    def _set_label(self, cell_name: str, label: Label):
        self.cell_map[cell_name].set_label(label)
