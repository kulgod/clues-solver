# Clues Solver Python Server

## Quick Start

1. **Install dependencies:**
   ```bash
   cd src/python
   pip install -r ../requirements.txt
   ```

2. **Start the server:**
   ```bash
   python server.py
   ```

3. **Test the server:**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Use with Chrome extension:**
   - Server must be running on localhost:8000
   - Extension will automatically send game state to server
   - Server returns move recommendations

## API Endpoints

### POST /analyze
Analyzes game state and returns move recommendation.

**Request:**
```json
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
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "recommendation": {
    "character": "Bob",
    "label": "criminal", 
    "reasoning": "Alice states Bob is criminal. Since everyone tells the truth, Bob must be criminal.",
    "confidence": "high"
  }
}
```

### GET /health
Health check endpoint.

## Next Steps

1. Integrate with existing constraint solving logic in `manual_solver/`
2. Add proper error handling and validation
3. Implement actual game analysis (currently returns placeholder)

## Development

The server currently logs all received character data and returns a placeholder response. This allows testing the DOM parsing and communication between extension and server before implementing the full constraint logic.
