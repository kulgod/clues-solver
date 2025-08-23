#!/usr/bin/env python3
"""
Simple Flask server to analyze Clues game state using structured data.
Receives character data from Chrome extension and returns move recommendations.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # Allow requests from Chrome extension

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
                "row": 0,
                "col": 0,
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
        print(f"Received {len(characters)} characters")
        
        # For now, simple analysis - just log the data and return a placeholder
        for char in characters:
            print(f"  {char['coord']}: {char['name']} ({char['profession']}) - {char['label']}")
            if char.get('hint'):
                print(f"    Hint: {char['hint']}")
        
        # TODO: Integrate with actual constraint solving logic
        
        # Placeholder response for testing
        return jsonify({
            'success': True,
            'recommendation': {
                'character': 'TestCharacter',
                'label': 'criminal',
                'reasoning': 'Placeholder response - server is working but constraint logic not yet integrated',
                'confidence': 'high'
            }
        })
        
    except Exception as e:
        print(f"Error analyzing game: {e}")
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
