"""
Clues Solver Package

A sophisticated solver for online puzzle games featuring character deduction.
"""

__version__ = "1.0.0"
__author__ = "Puzzle Solver Team"

from .game_state import GameState, Character, Label
from .solver import PuzzleSolver, Move
from .constraints import Constraint, CountConstraint, OccupationConstraint
from .game_interface import GameInterface, MockGameInterface

__all__ = [
    "GameState",
    "Character", 
    "Label",
    "PuzzleSolver",
    "Move",
    "Constraint",
    "CountConstraint",
    "OccupationConstraint", 
    "GameInterface",
    "MockGameInterface"
]