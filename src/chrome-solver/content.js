// Content script that runs on cluesbysam.com
console.log('Clues Solver content script loaded');



// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'ping') {
        sendResponse({
            success: true,
            message: 'Content script is loaded'
        });
        return true;
    }

    if (request.action === 'solveMove') {
        // Wrap in try-catch to ensure we always send a response
        (async () => {
            try {
                const result = await handleSolveMove(request.apiKey, request.solverMode);
                sendResponse(result);
            } catch (error) {
                console.error('Error in handleSolveMove:', error);
                sendResponse({
                    success: false,
                    error: error.message || 'An unexpected error occurred'
                });
            }
        })();

        // Return true to indicate we'll send response asynchronously
        return true;
    }
});

async function handleSolveMove(apiKey, solverMode = 'gpt-4o') {
    console.log('Starting analysis with mode:', solverMode);
    
    try {
        if (solverMode === 'python') {
            // Step 1: Parse game state from DOM
            console.log('Parsing game state from DOM...');
            const gameState = parseGameState();

            // Step 2: Send to Python server for analysis
            console.log('Sending to Python server...');
            const analysis = await analyzeWithPythonServer(gameState);

            // Step 3: Return the recommendation
            console.log('Server recommendation:', analysis);

            return {
                success: true,
                character: analysis.character,
                label: analysis.label,
                reasoning: analysis.reasoning,
                confidence: analysis.confidence,
                source: 'py-analyzer'
            };
        } else {
            // AI model mode - use screenshot analysis
            console.log('Taking screenshot...');
            const screenshot = await takeScreenshot();

            let analysis;
            if (solverMode.startsWith('claude')) {
                console.log(`Analyzing with ${solverMode}...`);
                analysis = await analyzeWithClaudeViaBackground(screenshot, apiKey, solverMode);
            } else {
                console.log(`Analyzing with ${solverMode}...`);
                analysis = await analyzeWithOpenAIViaBackground(screenshot, apiKey);
            }

            console.log(`${solverMode} recommendation:`, analysis);

            return {
                success: true,
                character: analysis.character,
                label: analysis.label,
                reasoning: analysis.reasoning,
                confidence: analysis.confidence || 'medium',
                source: solverMode
            };
        }

    } catch (error) {
        console.error('Error in handleSolveMove:', error);
        throw error;
    }
}

function parseGameState() {
    const gameState = {
        characters: []
    };

    // Find the game grid container
    const gridContainer = document.querySelector('.card-grid');
    if (!gridContainer) {
        throw new Error('Game grid not found on page');
    }

    // Get all card containers
    const cardContainers = gridContainer.querySelectorAll('div > .card');

    for (const card of cardContainers) {
        try {
            const character = parseCharacterCard(card);
            if (character) {
                gameState.characters.push(character);
            }
        } catch (error) {
            console.warn('Failed to parse character card:', error);
            // Continue parsing other cards
        }
    }

    console.log('Parsed game state:', gameState);
    return gameState;
}

function parseCharacterCard(card) {
    // Get coordinate
    const coordElement = card.querySelector('.coord');
    if (!coordElement) {
        console.warn('No coordinate found for card');
        return null;
    }
    const coord = coordElement.textContent.trim();

    // Get name
    const nameElement = card.querySelector('.name h3');
    if (!nameElement) {
        console.warn('No name found for card at', coord);
        return null;
    }
    const name = nameElement.textContent.trim();

    // Get profession
    const professionElement = card.querySelector('.profession');
    if (!professionElement) {
        console.warn('No profession found for card at', coord);
        return null;
    }
    const profession = professionElement.textContent.trim();

    // Determine label (innocent/criminal/unknown)
    let label = 'unknown';
    if (card.classList.contains('flipped')) {
        if (card.classList.contains('innocent')) {
            label = 'innocent';
        } else if (card.classList.contains('criminal')) {
            label = 'criminal';
        }
    }

    // Get hint (only for revealed cards)
    let hint = null;
    const hintElement = card.querySelector('.hint');
    if (hintElement) {
        hint = hintElement.textContent.trim();
    }

    return {
        name: name,
        profession: profession,
        coord: coord,
        label: label,
        hint: hint
    };
}

async function analyzeWithPythonServer(gameState) {
    const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            characters: gameState.characters
        })
    });

    if (!response.ok) {
        throw new Error(`Server error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    if (!data.success) {
        throw new Error(data.error || 'Server analysis failed');
    }

    return data.recommendation;
}

async function takeScreenshot() {
    return new Promise((resolve, reject) => {
        chrome.runtime.sendMessage({
            action: 'takeScreenshot'
        }, (response) => {
            if (response.success) {
                resolve(response.screenshot);
            } else {
                reject(new Error(response.error || 'Failed to take screenshot'));
            }
        });
    });
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
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            model: 'gpt-4o',
            messages: [{
                role: 'user',
                content: [{
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
            }],
            max_completion_tokens: 3000
        })
    });

    if (!response.ok) {
        throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    let content = data.choices[0].message.content;

    // Check for empty content due to token limits
    if (!content || content.trim() === '') {
        console.log('Full API response:', JSON.stringify(data, null, 2));
        if (data.choices[0].finish_reason === 'length') {
            throw new Error('AI response was cut off due to token limit. The puzzle might be too complex for current settings.');
        }
        throw new Error('AI returned empty response');
    }

    // Remove markdown code blocks if present
    content = content.replace(/```json\s*/g, '').replace(/```\s*/g, '').trim();

    try {
        console.log('Raw AI response:', content);
        const analysis = JSON.parse(content);

        if (analysis.error) {
            throw new Error(analysis.error);
        }

        if (!analysis.character || !analysis.label) {
            throw new Error('Invalid response from OpenAI API - missing character or label');
        }

        return analysis;
    } catch (parseError) {
        console.error('Failed to parse OpenAI response:', content);
        console.error('Parse error details:', parseError);

        // Try to extract JSON from a longer response
        const jsonMatch = content.match(/\{[^{}]*"character"[^{}]*\}/);
        if (jsonMatch) {
            try {
                const analysis = JSON.parse(jsonMatch[0]);
                console.log('Extracted JSON successfully:', analysis);
                return analysis;
            } catch (extractError) {
                console.error('Failed to extract JSON as well:', extractError);
            }
        }

        throw new Error(`Failed to parse AI response. Raw response: ${content.substring(0, 200)}...`);
    }
}

async function analyzeWithClaudeViaBackground(screenshot, apiKey, model) {
    console.log('Content: Sending Claude request to background script:', model);
    return new Promise((resolve, reject) => {
        chrome.runtime.sendMessage({
            action: 'analyzeWithClaude',
            screenshot: screenshot,
            apiKey: apiKey,
            model: model
        }, (response) => {
            console.log('Content: Received response from background:', response);
            if (chrome.runtime.lastError) {
                console.error('Content: Chrome runtime error:', chrome.runtime.lastError);
                reject(new Error(chrome.runtime.lastError.message));
            } else if (response && response.success) {
                console.log('Content: Claude analysis successful');
                resolve(response.result);
            } else {
                console.error('Content: Background script error:', response);
                reject(new Error(response?.error || 'Unknown error from background script'));
            }
        });
    });
}

async function analyzeWithOpenAIViaBackground(screenshot, apiKey) {
    return new Promise((resolve, reject) => {
        chrome.runtime.sendMessage({
            action: 'analyzeWithOpenAI',
            screenshot: screenshot,
            apiKey: apiKey
        }, (response) => {
            if (chrome.runtime.lastError) {
                reject(new Error(chrome.runtime.lastError.message));
            } else if (response.success) {
                resolve(response.result);
            } else {
                reject(new Error(response.error));
            }
        });
    });
}

async function executeMove(characterName, label) {
    // Find the character element by text content
    const characterElements = document.querySelectorAll('[class*="character"], [class*="suspect"], [class*="person"]');

    let targetElement = null;
    for (const element of characterElements) {
        if (element.textContent.includes(characterName)) {
            targetElement = element;
            break;
        }
    }

    if (!targetElement) {
        // Fallback: try any element containing the character name
        const allElements = document.querySelectorAll('*');
        for (const element of allElements) {
            if (element.textContent.trim() === characterName ||
                element.textContent.includes(characterName)) {
                targetElement = element;
                break;
            }
        }
    }

    if (!targetElement) {
        throw new Error(`Could not find character "${characterName}" on the page`);
    }

    // Click the character
    targetElement.click();

    // Wait a moment for the options to appear
    await new Promise(resolve => setTimeout(resolve, 500));

    // Look for innocent/criminal buttons
    const labelText = label.toLowerCase();
    const buttons = document.querySelectorAll('button, [role="button"], .btn, [class*="button"]');

    let labelButton = null;
    for (const button of buttons) {
        const buttonText = button.textContent.toLowerCase();
        if (buttonText.includes(labelText) ||
            buttonText.includes(labelText === 'criminal' ? 'guilt' : 'innoc')) {
            labelButton = button;
            break;
        }
    }

    if (!labelButton) {
        throw new Error(`Could not find "${label}" button after clicking character`);
    }

    // Click the label button
    labelButton.click();

    // Wait a moment to see if the move was accepted
    await new Promise(resolve => setTimeout(resolve, 500));

    console.log(`Move executed: ${characterName} → ${label}`);
}