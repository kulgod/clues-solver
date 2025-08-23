// Get DOM elements
const apiKeyInput = document.getElementById('api-key');
const solveButton = document.getElementById('solve-button');
const statusDiv = document.getElementById('status');
const toggleVisibilityButton = document.getElementById('toggle-visibility');
const solverModeSelect = document.getElementById('solver-mode');
const apiKeySection = document.getElementById('api-key-section');

// Load saved API key and solver mode
chrome.storage.local.get(['apiKey', 'solverMode'], function(result) {
  if (result.apiKey) {
    apiKeyInput.value = result.apiKey;
  }
  
  // Set solver mode (default to OpenAI if not set)
  const savedMode = result.solverMode || 'openai';
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
  
  // Only require API key for OpenAI mode
  if (solverMode === 'openai' && !apiKey) {
    showStatus('Please enter your OpenAI API key', 'error');
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
    
    if (response.success) {
      showRecommendation(response);
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

function showRecommendation(response) {
  const labelClass = response.label === 'criminal' ? 'label-criminal' : 'label-innocent';
  
  const html = `
    <div class="recommendation">
      <h3>AI Recommendation</h3>
      <div class="move-info">
        <span class="character-name">${response.character}</span>
        <span class="label-badge ${labelClass}">${response.label.toUpperCase()}</span>
      </div>
      <div class="reasoning">
        <strong>Reasoning:</strong><br>
        ${response.reasoning}
      </div>
      <div class="confidence">
        Confidence: ${response.confidence || 'high'}
      </div>
    </div>
  `;
  
  statusDiv.innerHTML = html;
  statusDiv.className = 'status';
}
