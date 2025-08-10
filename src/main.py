#!/usr/bin/env python3
"""
Main entry point for the puzzle solver.
"""

from typing import List
import argparse
import logging
from .game_state import GameState, Label
from .constraints import CountConstraint, OccupationConstraint, AdjacentConstraint
from .solver import PuzzleSolver
from .game_interface import MockGameInterface, GameInterface

def setup_logging(level=logging.INFO):
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_default_constraints() -> List:
    """Create default constraints for the game."""
    constraints = []
    
    # Assume maximum 4 criminals out of 20 characters (adjust based on game rules)
    constraints.append(CountConstraint(max_criminals=4, min_criminals=1))
    
    # Occupation-based constraints (customize based on actual game)
    occupation_rules = {
        "Detective": {"type": "bias", "bias": 0.8},  # Likely innocent
        "Police": {"type": "bias", "bias": 0.7},     # Likely innocent
        "Judge": {"type": "bias", "bias": 0.6},      # Likely innocent
        "Teacher": {"type": "bias", "bias": 0.5},    # Neutral
        "Banker": {"type": "bias", "bias": -0.2},    # Slightly suspicious
        "Politician": {"type": "bias", "bias": -0.3}, # More suspicious
    }
    constraints.append(OccupationConstraint(occupation_rules))
    
    # Add adjacency constraints if relevant to your game
    constraints.append(AdjacentConstraint("basic"))
    
    return constraints

def run_solver(game_interface: GameInterface, max_moves: int = 10):
    """Run the solver on a game."""
    logger = logging.getLogger(__name__)
    
    constraints = create_default_constraints()
    moves_made = 0
    
    while game_interface.is_game_active() and moves_made < max_moves:
        # Get current game state
        game_state = game_interface.get_game_state()
        logger.info(f"Current game state:\n{game_state}")
        
        # Create solver and find best move
        solver = PuzzleSolver(game_state, constraints)
        next_move = solver.suggest_next_move()
        
        if not next_move:
            logger.info("No confident moves available. Manual intervention may be needed.")
            break
        
        logger.info(f"Suggested move: {next_move.character.name} -> {next_move.label.value}")
        logger.info(f"Confidence: {next_move.confidence:.2f}")
        logger.info(f"Reasoning: {next_move.reasoning}")
        
        # Make the move
        if next_move.confidence > 0.7:  # Only make high-confidence moves
            success = game_interface.make_move(next_move.character, next_move.label)
            if success:
                logger.info("Move executed successfully")
                moves_made += 1
            else:
                logger.error("Failed to execute move")
                break
        else:
            logger.info("Move confidence too low, skipping automatic execution")
            # Could prompt user for manual decision here
            break
    
    logger.info(f"Solver finished. Made {moves_made} moves.")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Puzzle Game Solver")
    parser.add_argument("--mode", choices=["mock", "web"], default="mock",
                       help="Interface mode (mock for testing, web for actual game)")
    parser.add_argument("--url", type=str, help="Game URL (for web mode)")
    parser.add_argument("--max-moves", type=int, default=10, help="Maximum moves to make")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create game interface
    if args.mode == "mock":
        game_interface = MockGameInterface()
        logger.info("Using mock game interface for testing")
    elif args.mode == "web":
        if not args.url:
            logger.error("URL required for web mode")
            return
        # game_interface = WebGameInterface(args.url)
        logger.error("Web interface not yet implemented")
        return
    
    # Run the solver
    try:
        run_solver(game_interface, args.max_moves)
    except KeyboardInterrupt:
        logger.info("Solver interrupted by user")
    except Exception as e:
        logger.error(f"Error running solver: {e}")

if __name__ == "__main__":
    main()