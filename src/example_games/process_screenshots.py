#!/usr/bin/env python3
"""
Script to process Clues game screenshots and generate mock JSON data.
Extracts game state information from screenshots using OpenAI Vision API.
"""

import os
import json
import base64
from openai import OpenAI
from pathlib import Path

# Initialize OpenAI client
client = OpenAI()

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_screenshot(image_path, visible_character_name):
    """Analyze screenshot using OpenAI Vision API."""
    base64_image = encode_image(image_path)
    
    prompt = f"""
This is a screenshot of a Clues puzzle game with a 5x4 grid (5 columns A-E, 4 rows 1-4).

Please analyze this image and extract the following information for ALL 20 characters:

1. Their grid position (coordinate like A1, B2, etc.)
2. Their name
3. Their profession/occupation
4. Their final label (innocent or criminal)

The game starts with only ONE character visible: {visible_character_name}. All other characters start as unknown/hidden.

Please return the data in this exact JSON format:

{{
  "initial_state": {{
    "characters": [
      {{
        "name": "CharacterName",
        "profession": "occupation",
        "coord": "A1",
        "label": "innocent|criminal|unknown",
        "hint": "hint text if visible, otherwise null"
      }}
    ]
  }},
  "completed_state": {{
    "characters": [
      {{
        "name": "CharacterName", 
        "profession": "occupation",
        "coord": "A1",
        "label": "innocent|criminal",
        "hint": "hint text"
      }}
    ]
  }}
}}

For initial_state: Only {visible_character_name} should have label "innocent" or "criminal" and a hint. All others should have label "unknown" and hint null.

For completed_state: All characters should have their final labels (innocent/criminal) and hints.

Scan the grid systematically from A1, A2, A3, A4, then B1, B2, B3, B4, etc.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=4000
    )
    
    return response.choices[0].message.content

def extract_json_from_response(response_text):
    """Extract JSON from the API response."""
    # Find JSON content between ```json and ``` or just parse if it's already JSON
    if "```json" in response_text:
        start = response_text.find("```json") + 7
        end = response_text.find("```", start)
        json_text = response_text[start:end].strip()
    elif response_text.strip().startswith("{"):
        json_text = response_text.strip()
    else:
        # Try to find the first { and last }
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        json_text = response_text[start:end]
    
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Extracted text: {json_text}")
        return None

def process_screenshot(image_path):
    """Process a single screenshot and generate JSON files."""
    print(f"Processing {image_path}...")
    
    # Extract visible character name from filename
    filename = Path(image_path).stem
    # Remove "clues_solver__" prefix to get the character name
    visible_character = filename.replace("clues_solver__", "").title()
    
    print(f"Visible character: {visible_character}")
    
    # Analyze with OpenAI
    response = analyze_screenshot(image_path, visible_character)
    print("Raw response received:")
    print(response)
    print("\n" + "="*50 + "\n")
    
    # Extract and parse JSON
    game_data = extract_json_from_response(response)
    
    if not game_data:
        print(f"Failed to extract valid JSON from response for {image_path}")
        return
    
    # Save initial state
    initial_filename = filename + "_initial.json"
    initial_path = Path(image_path).parent / initial_filename
    with open(initial_path, 'w') as f:
        json.dump(game_data.get("initial_state", {}), f, indent=2)
    print(f"Saved initial state: {initial_path}")
    
    # Save completed state  
    completed_filename = filename + "_completed.json"
    completed_path = Path(image_path).parent / completed_filename
    with open(completed_path, 'w') as f:
        json.dump(game_data.get("completed_state", {}), f, indent=2)
    print(f"Saved completed state: {completed_path}")

def main():
    """Process all screenshots in the example_games directory."""
    script_dir = Path(__file__).parent
    
    # Find all PNG files
    png_files = list(script_dir.glob("*.png"))
    
    if not png_files:
        print("No PNG files found in the example_games directory")
        return
    
    print(f"Found {len(png_files)} screenshot(s) to process")
    
    for png_file in png_files:
        try:
            process_screenshot(png_file)
            print(f"✅ Successfully processed {png_file.name}\n")
        except Exception as e:
            print(f"❌ Error processing {png_file.name}: {e}\n")

if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        exit(1)
    
    main()
