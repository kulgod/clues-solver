// Get DOM elements
const apiKeyInput = document.getElementById('api-key');
const solveButton = document.getElementById('solve-button');
const statusDiv = document.getElementById('status');
const toggleVisibilityButton = document.getElementById('toggle-visibility');
const solverModeSelect = document.getElementById('solver-mode');
const apiKeySection = document.getElementById('api-key-section');
const apiKeyLabel = document.getElementById('api-key-label');

// Load saved API key and solver mode
chrome.storage.local.get(['apiKey', 'solverMode'], function(result) {
  if (result.apiKey) {
    apiKeyInput.value = result.apiKey;
  }
  
  // Set solver mode (default to GPT-4o if not set)
  const savedMode = result.solverMode || 'gpt-4o';
  solverModeSelect.value = savedMode;
  updateUIForMode(savedMode);
});

// Save API key when it changes
apiKeyInput.addEventListener('input', function() {
  chrome.storage.local.set({apiKey: apiKeyInput.value});
});

// Handle solver mode changes
solverModeSelect.addEventListener('change', function() {
  const selectedMode = this.value;
  chrome.storage.local.set({solverMode: selectedMode});
  updateUIForMode(selectedMode);
});

// Update UI based on selected mode
function updateUIForMode(mode) {
  if (mode === 'python') {
    apiKeySection.style.display = 'none';
  } else {
    apiKeySection.style.display = 'block';
    
    // Update label and placeholder based on model
    if (mode.startsWith('claude')) {
      apiKeyLabel.textContent = 'Anthropic API Key:';
      apiKeyInput.placeholder = 'sk-ant-...';
    } else {
      apiKeyLabel.textContent = 'OpenAI API Key:';
      apiKeyInput.placeholder = 'sk-...';
    }
  }
  solveButton.textContent = 'Get Recommendation';
}

// Toggle API key visibility
toggleVisibilityButton.addEventListener('click', function() {
  if (apiKeyInput.type === 'password') {
    apiKeyInput.type = 'text';
    toggleVisibilityButton.textContent = '🙈';
  } else {
    apiKeyInput.type = 'password';
    toggleVisibilityButton.textContent = '👁️';
  }
});

// Handle solve button click
solveButton.addEventListener('click', async function() {
  const solverMode = solverModeSelect.value;
  const apiKey = apiKeyInput.value.trim();
  
  // Only require API key for AI models (not python analyzer)
  if (solverMode !== 'python' && !apiKey) {
    const provider = solverMode.startsWith('claude') ? 'Anthropic' : 'OpenAI';
    showStatus(`Please enter your ${provider} API key`, 'error');
    return;
  }
  
  // Disable button and show analyzing status
  solveButton.disabled = true;
  solveButton.textContent = 'Analyzing...';
  showStatus('Taking screenshot and analyzing game...', 'analyzing');
  
  try {
    // Get the active tab
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    
    // Check if we're on the right website
    if (!tab.url.includes('cluesbysam.com')) {
      throw new Error('Please navigate to cluesbysam.com first');
    }
    
    // Send message to content script to start analysis
    const response = await new Promise((resolve) => {
      chrome.tabs.sendMessage(tab.id, {
        action: 'solveMove',
        apiKey: apiKey,
        solverMode: solverMode
      }, (response) => {
        if (chrome.runtime.lastError) {
          resolve({success: false, error: chrome.runtime.lastError.message});
        } else {
          resolve(response || {success: false, error: 'No response from content script'});
        }
      });
    });
    
    // Handle array of recommendations from content script
    if (Array.isArray(response)) {
      if (response.length > 0 && response[0].success) {
        showRecommendations(response);
      } else {
        throw new Error('No valid recommendations received');
      }
    } else if (response.success) {
      // Backward compatibility for single recommendation
      showRecommendations([response]);
    } else {
      throw new Error(response.error || 'Unknown error occurred');
    }
    
  } catch (error) {
    console.error('Error:', error);
    showStatus(`Error: ${error.message}`, 'error');
  } finally {
    // Re-enable button
    solveButton.disabled = false;
    solveButton.textContent = 'Get Recommendation';
  }
});

function showStatus(message, type) {
  statusDiv.innerHTML = message;
  statusDiv.className = `status ${type}`;
}

function showRecommendations(recommendations) {
  if (!recommendations || recommendations.length === 0) {
    showStatus('No recommendations available', 'error');
    return;
  }

  // Generate HTML for all recommendations
  const recommendationsHtml = recommendations.map((response, index) => {
    const labelClass = response.label === 'criminal' ? 'label-criminal' : 'label-innocent';
    const title = recommendations.length > 1 ? `Recommendation #${index + 1}` : 'Recommendation';
    
    return `
      <div class="recommendation">
        <h3>${title}</h3>
        <div class="move-info">
          <span class="character-name">${response.character}</span>
          <span class="label-badge ${labelClass}">${response.label.toUpperCase()}</span>
        </div>
        ${response.reasoning ? `
        <div class="reasoning">
          <strong>Reasoning:</strong><br>
          ${response.reasoning}
        </div>
        ` : ''}
        ${response.confidence ? `
        <div class="confidence">
          Confidence: ${response.confidence}
        </div>
        ` : ''}
      </div>
    `;
  }).join('');
  
  statusDiv.innerHTML = recommendationsHtml;
  statusDiv.className = 'status';
}
