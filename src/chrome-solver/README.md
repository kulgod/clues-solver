# Clues Solver Chrome Extension

AI-powered solver for the Clues puzzle game at cluesbysam.com

## Setup Instructions

1. **Get OpenAI API Key**
   - Go to https://platform.openai.com/api-keys
   - Create a new API key
   - Copy the key (starts with `sk-...`)

2. **Install Extension**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)
   - Click "Load unpacked"
   - Select the `src/chrome-solver` folder
   - Extension should appear in your extensions list

3. **Use the Extension**
   - Navigate to https://cluesbysam.com
   - Start a new game
   - Click the Clues Solver extension icon in your toolbar
   - Enter your OpenAI API key (will be saved)
   - Click "Solve Next Move"

## How It Works

1. Takes a screenshot of the current game board
2. Sends the image to GPT-4 Vision for analysis
3. AI analyzes the clues and finds a logically certain move
4. Automatically clicks the character and selects innocent/criminal
5. Shows the result and reasoning in the popup

## Files

- `manifest.json` - Extension configuration
- `popup.html/js` - Extension popup interface  
- `content.js` - Runs on cluesbysam.com, handles game interaction
- `background.js` - Handles screenshot capture
- `icons/` - Extension icons (optional)

## Development

To modify the extension:
1. Edit the files
2. Go to `chrome://extensions/`
3. Click the refresh button on the Clues Solver extension
4. Test your changes

## Troubleshooting

- **"Please navigate to cluesbysam.com first"** - Make sure you're on the correct website
- **"Could not find character"** - The AI might have suggested an invalid character name
- **API errors** - Check your OpenAI API key and internet connection
- **Move rejected** - The AI's analysis might be incorrect; try again

## Requirements

- Chrome browser
- OpenAI API key with GPT-4 Vision access
- Internet connection
