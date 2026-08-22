/**
 * Service Worker (MV3 Background Script)
 *
 * Responsibilities:
 * - Track the active LeetCode problem slug from the tab URL
 * - Relay messages between content script and future backend connections
 * - Store session state in chrome.storage.session
 */

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Fire on full-page load OR on SPA URL change (Chrome fires changeInfo.url for pushState)
  const url = changeInfo.url || (changeInfo.status === 'complete' ? tab.url : null);
  if (!url) return;

  const match = url.match(/leetcode\.com\/problems\/([^/]+)/);
  if (match) {
    const slug = match[1];
    chrome.storage.session.set({ [tabId]: { slug, timestamp: Date.now() } });
    // Notify content script — it will reset the panel UI for the new problem
    chrome.tabs.sendMessage(tabId, { type: 'SLUG_DETECTED', slug }).catch(() => {
      // Content script may not be ready yet — ignore silently
    });
  }
});

chrome.tabs.onRemoved.addListener((tabId) => {
  chrome.storage.session.remove(String(tabId));
});

// Handle messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_SLUG') {
    const tabId = sender.tab?.id;
    if (!tabId) { sendResponse({ slug: null }); return true; }
    chrome.storage.session.get(String(tabId), (result) => {
      sendResponse({ slug: result[tabId]?.slug ?? null });
    });
    return true; // Keep message channel open for async sendResponse
  }
});
