chrome.action.onClicked.addListener((tab) => {
  if (!tab.url || !tab.url.startsWith('http')) return;

  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ['content.js']
  }).then(() => {
    chrome.action.setIcon({ path: { 128: 'icon-active.png' }, tabId: tab.id });
  });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'picker-done' && sender.tab) {
    chrome.action.setIcon({ path: { 128: 'icon.png' }, tabId: sender.tab.id });
  }
  if (message.type === 'get-react-components' && sender.tab) {
    chrome.scripting.executeScript({
      target: { tabId: sender.tab.id },
      world: 'MAIN',
      args: [message.probeIds],
      func: (probeIds) => probeIds.map(probeId => {
        const el = document.querySelector(`[data-probe="${probeId}"]`);
        const key = el && Object.keys(el).find(k => k.startsWith('__reactFiber'));
        let node = key ? el[key] : null;
        while (node) {
          if (typeof node.type === 'function' && node.type.name) return node.type.name;
          node = node.return;
        }
        return null;
      })
    }).then(results => sendResponse(results?.[0]?.result || null))
      .catch(() => sendResponse(null));
    return true;
  }
});
