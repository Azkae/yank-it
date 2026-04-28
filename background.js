chrome.action.onClicked.addListener((tab) => {
  if (!tab.url || !tab.url.startsWith('http')) return;

  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ['content.js']
  }).then(() => {
    chrome.action.setIcon({ path: { 128: 'icon-active.png' }, tabId: tab.id });
  });
});

chrome.runtime.onMessage.addListener((message, sender) => {
  if (message.type === 'picker-done' && sender.tab) {
    chrome.action.setIcon({ path: { 128: 'icon.png' }, tabId: sender.tab.id });
  }
});
