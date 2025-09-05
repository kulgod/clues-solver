// Background service worker for Chrome extension
console.log('🚀 Clues Solver background worker loaded');
console.log('Background script is ready to receive messages');

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'takeScreenshot') {
    takeScreenshot(sender.tab.id)
      .then(screenshot => sendResponse({success: true, screenshot}))
      .catch(error => sendResponse({success: false, error: error.message}));
    
    // Return true to indicate we'll send response asynchronously
    return true;
  }
  
  if (request.action === 'analyzeWithClaude') {
    console.log('Background: Starting Claude analysis with model:', request.model);
    analyzeWithClaude(request.screenshot, request.apiKey, request.model)
      .then(result => {
        console.log('Background: Claude analysis successful');
        sendResponse({success: true, result});
      })
      .catch(error => {
        console.error('Background: Claude analysis failed:', error);
        sendResponse({success: false, error: error.message});
      });
    
    // Return true to indicate we'll send response asynchronously
    return true;
  }
  
  if (request.action === 'analyzeWithOpenAI') {
    analyzeWithOpenAI(request.screenshot, request.apiKey)
      .then(result => sendResponse({success: true, result}))
      .catch(error => sendResponse({success: false, error: error.message}));
    
    // Return true to indicate we'll send response asynchronously
    return true;
  }
});

async function takeScreenshot(tabId) {
  try {
    // Capture the visible area of the tab
    const screenshot = await chrome.tabs.captureVisibleTab(null, {
      format: 'png',
      quality: 90
    });
    
    // Convert data URL to base64 string (remove data:image/png;base64, prefix)
    const base64Screenshot = screenshot.replace(/^data:image\/png;base64,/, '');
    
    return base64Screenshot;
  } catch (error) {
    console.error('Error taking screenshot:', error);
    throw new Error('Failed to capture screenshot');
  }
}

async function analyzeWithClaude(screenshot, apiKey, model) {
  const prompt = `This is a screenshot of a Clues puzzle game by Sam. The game has a 5x4 grid of characters arranged in rows and columns.

GRID LAYOUT:
- 5 rows (numbered 1-5 from top to bottom)
- 4 columns (lettered A-D from left to right)
- Each cell contains a character with their name and occupation

SPATIAL RELATIONSHIPS:
- "Above" = in a higher row (smaller row number, 1 is the top row)
- "Below" = in a lower row (larger row number, 5 is the bottom row)  
- "Left" = in a column to the left (A is leftmost)
- "Right" = in a column to the right (D is rightmost)
- "Directly above/below" = same column, adjacent row (1 is above 2, 2 is below 1)
- "Neighbors" = adjacent cells (including diagonals, each cell has up to 8 neighbors)

VISUAL INDICATORS:
- Green background = known innocent
- Red background = known criminal
- Gray background = unknown (need to determine)
- Character names are clearly visible in each cell
- Hints/clues are visible as text on the known characters

GAME RULES:
- Everyone is either criminal or innocent
- Everyone tells the truth, even criminals
- You can only make moves that are 100% logically certain
- Read all visible hints carefully for spatial clues

TASK: Analyze this board and find ONE UNKNOWN character (gray background) that can be determined with absolute logical certainty based on the hints from the known characters (green/red backgrounds).

IMPORTANT: 
- Only recommend moves for characters with GRAY backgrounds (unknown)
- DO NOT recommend moves for characters with GREEN (innocent) or RED (criminal) backgrounds
- Use the hints from known characters to deduce unknown characters
- Pay close attention to character names and their exact positions when interpreting spatial hints like "directly below", "above", etc.

Return JSON in this exact format:
{
  "character": "ExactCharacterName", 
  "label": "criminal" or "innocent",
  "reasoning": "detailed explanation including spatial analysis and which known character's hint led to this conclusion",
  "confidence": "high"
}

Only suggest a move if you are completely certain. If no certain move exists, return {"error": "No certain moves available"}.`;

  // Map model names to Claude API model identifiers
  const modelMapping = {
    'claude-sonnet-4': 'claude-sonnet-4-20250514',
    'claude-opus-4-1': 'claude-opus-4-1-20250805'
  };

  const claudeModel = modelMapping[model] || 'claude-sonnet-4-20250514';
  
  console.log('Claude API: Using model:', claudeModel);
  console.log('Claude API: API key format check:', apiKey.substring(0, 10) + '...');
  
  if (!apiKey.startsWith('sk-ant-')) {
    throw new Error('Invalid Anthropic API key format. Must start with "sk-ant-"');
  }

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
        'anthropic-dangerous-direct-browser-access': true,
      },
      body: JSON.stringify({
        model: claudeModel,
        max_tokens: 1000,
        messages: [
          {
            role: 'user',
            content: [
              {
                type: 'text',
                text: prompt
              },
              {
                type: 'image',
                source: {
                  type: 'base64',
                  media_type: 'image/png',
                  data: screenshot // Should already be base64 without prefix
                }
              }
            ]
          }
        ]
      })
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`Claude API error: ${response.status} ${response.statusText} - ${errorData}`);
    }

    const data = await response.json();
    const content = data.content[0].text;

         console.log('Raw Claude response:', content);

     // Find the last JSON object in the response (the final answer)
     let jsonMatch = content.match(/\{[^{}]*"character"[^{}]*"label"[^{}]*"reasoning"[^{}]*"confidence"[^{}]*\}/);
     if (!jsonMatch) {
       // Fallback: try to find any JSON with the required fields
       jsonMatch = content.match(/\{[\s\S]*?"character"[\s\S]*?"label"[\s\S]*?"reasoning"[\s\S]*?\}/);
     }
     if (!jsonMatch) {
       throw new Error('No valid recommendation JSON found in response');
     }

     const jsonStr = jsonMatch[0];
     console.log('Extracted JSON:', jsonStr);
     
     let result;
     try {
       result = JSON.parse(jsonStr);
     } catch (parseError) {
       console.error('JSON parse error:', parseError);
       console.error('Failed to parse JSON string:', jsonStr);
       throw new Error(`Failed to parse Claude response JSON: ${parseError.message}`);
     }

    if (result.error) {
      throw new Error(result.error);
    }

    return {
      character: result.character,
      label: result.label,
      reasoning: result.reasoning,
      confidence: result.confidence || 'medium'
    };
  } catch (fetchError) {
    console.error('Claude API fetch error:', fetchError);
    throw new Error(`Claude API fetch failed: ${fetchError.message}`);
  }
}

async function analyzeWithOpenAI(screenshot, apiKey) {
  const prompt = `This is a screenshot of a Clues puzzle game by Sam. The game has a 5x4 grid of characters arranged in rows and columns.

GRID LAYOUT:
- 5 rows (numbered 1-5 from top to bottom)
- 4 columns (lettered A-D from left to right)
- Each cell contains a character with their name and occupation

SPATIAL RELATIONSHIPS:
- "Above" = in a higher row (smaller row number, 1 is the top row)
- "Below" = in a lower row (larger row number, 5 is the bottom row)  
- "Left" = in a column to the left (A is leftmost)
- "Right" = in a column to the right (D is rightmost)
- "Directly above/below" = same column, adjacent row (1 is above 2, 2 is below 1)
- "Neighbors" = adjacent cells (including diagonals, each cell has up to 8 neighbors)

VISUAL INDICATORS:
- Green background = known innocent
- Red background = known criminal
- Gray background = unknown (need to determine)
- Character names are clearly visible in each cell
- Hints/clues are visible as text on the known characters

GAME RULES:
- Everyone is either criminal or innocent
- Everyone tells the truth, even criminals
- You can only make moves that are 100% logically certain
- Read all visible hints carefully for spatial clues

TASK: Analyze this board and find ONE UNKNOWN character (gray background) that can be determined with absolute logical certainty based on the hints from the known characters (green/red backgrounds).

IMPORTANT: 
- Only recommend moves for characters with GRAY backgrounds (unknown)
- DO NOT recommend moves for characters with GREEN (innocent) or RED (criminal) backgrounds
- Use the hints from known characters to deduce unknown characters
- Pay close attention to character names and their exact positions when interpreting spatial hints like "directly below", "above", etc.

Return JSON in this exact format:
{
  "character": "ExactCharacterName", 
  "label": "criminal" or "innocent",
  "reasoning": "detailed explanation including spatial analysis and which known character's hint led to this conclusion",
  "confidence": "high"
}

Only suggest a move if you are completely certain. If no certain move exists, return {"error": "No certain moves available"}.`;

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'gpt-4o',
      messages: [
        {
          role: 'user',
          content: [
            {
              type: 'text',
              text: prompt
            },
            {
              type: 'image_url',
              image_url: {
                url: `data:image/png;base64,${screenshot}`
              }
            }
          ]
        }
      ],
      max_tokens: 1000
    })
  });

  if (!response.ok) {
    const errorData = await response.text();
    throw new Error(`OpenAI API error: ${response.status} ${response.statusText} - ${errorData}`);
  }

  const data = await response.json();
  const content = data.choices[0].message.content;

  console.log('Raw OpenAI response:', content);

  // Extract JSON from the response
  let jsonMatch = content.match(/\{[\s\S]*\}/);
  if (!jsonMatch) {
    throw new Error('No JSON found in response');
  }

  const jsonStr = jsonMatch[0];
  const result = JSON.parse(jsonStr);

  if (result.error) {
    throw new Error(result.error);
  }

  return {
    character: result.character,
    label: result.label,
    reasoning: result.reasoning,
    confidence: result.confidence || 'medium'
  };
}
