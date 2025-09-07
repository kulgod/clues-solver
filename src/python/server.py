#!/usr/bin/env python3
"""
Simple Flask server to analyze Clues game state using structured data.
Receives character data from Chrome extension and returns move recommendations.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the manual_solver directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'manual_solver'))

from src.python.manual_solver.game_state import GameState
from src.python.manual_solver.clues_solver import CluesSolver
from src.python.manual_solver.constraint_parser import ConstraintParser

app = Flask(__name__)
CORS(app)  # Allow requests from Chrome extension

# Load API key from environment
API_KEY = os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')
if not API_KEY:
    print("WARNING: No API key found in environment variables.")
    print("Please create a .env file with ANTHROPIC_API_KEY=your-key-here")
    print("Server will still start but constraint parsing will fail.")
else:
    print("✓ API key loaded successfully")

@app.route('/analyze', methods=['POST'])
def analyze_game():
    """
    Analyze game state and return move recommendation.
    
    Expected input:
    {
        "characters": [
            {
                "name": "Alice",
                "profession": "sleuth", 
                "coord": "A1",
                "label": "innocent",
                "hint": "My neighbor Bob is a criminal"
            },
            ...
        ]
    }
    
    Returns:
    {
        "success": true,
        "recommendation": {
            "character": "Bob",
            "label": "criminal",
            "reasoning": "Alice (innocent sleuth) states 'My neighbor Bob is a criminal'. Since everyone tells the truth, Bob must be criminal.",
            "confidence": "high"
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'characters' not in data:
            return jsonify({
                'success': False,
                'error': 'Invalid request: missing characters data'
            }), 400
        
        characters = data['characters']
        print(f"[SERVER] Received {len(characters)} characters")
        
        # Check if API key is available
        if not API_KEY:
            return jsonify({
                'success': False,
                'error': 'Server configuration error: No API key configured'
            }), 500
        
        # Create GameState from API data
        try:
            game_state = GameState.from_api_data(characters)
            parser = ConstraintParser(API_KEY)

            hints = game_state.get_available_hints()
            print(f"[SERVER] Hints:")
            for hint in hints:
                print(f"  - {hint}")
            constraints = parser.parse_all(hints)
            moves = CluesSolver.find_certain_moves(game_state, constraints)
            # Render grid for debugging (console output only)
            grid_text = game_state.render_as_text()
            
            # Print grid to console
            print("\n[SERVER] Reconstructed Grid:")
            print(grid_text)            
        except Exception as e:
            print(f"[SERVER] Error creating GameState or grid visualization: {e}")
        
        recommendations = [
            {
                'character': m.suspect.name,
                'label': m.label.value,
            }
            for m in moves
        ]
        print(f"[SERVER] Recommendations: {recommendations}")
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        print(f"[SERVER] Error analyzing game: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("Starting Clues Solver server on http://localhost:8000")
    print("Press Ctrl+C to stop")
    app.run(host='localhost', port=8000, debug=True)
