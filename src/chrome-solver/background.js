// Background service worker for Chrome extension
console.log('Clues Solver background worker loaded');

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'takeScreenshot') {
    takeScreenshot(sender.tab.id)
      .then(screenshot => sendResponse({success: true, screenshot}))
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
