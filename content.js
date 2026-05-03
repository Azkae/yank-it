(function () {
  // De-duplication guard: if picker is already active, cancel it
  if (window.__domPickerActive) {
    window.__domPickerActive = false;
    const existing = document.getElementById('__domPickerOverlay');
    if (existing) existing.remove();
    document.body.style.cursor = '';
    document.removeEventListener('mousemove', onMousemove);
    document.removeEventListener('click', onClick, true);
    document.removeEventListener('keydown', onKeydown, true);
    chrome.runtime.sendMessage({ type: 'picker-done' });
    return;
  }
  window.__domPickerActive = true;

  // --- Overlay ---
  const overlay = document.createElement('div');
  overlay.id = '__domPickerOverlay';
  Object.assign(overlay.style, {
    position: 'fixed',
    pointerEvents: 'none',
    zIndex: '2147483647',
    border: '2px solid #4A90E2',
    backgroundColor: 'rgba(74, 144, 226, 0.15)',
    borderRadius: '2px',
    boxSizing: 'border-box',
    display: 'none',
  });
  document.body.appendChild(overlay);

  // --- Cursor ---
  const prevCursor = document.body.style.cursor;
  document.body.style.cursor = 'crosshair';

  // --- Element path builder ---
  function getElementPath(el) {
    const parts = [], els = [];
    let current = el;
    for (let i = 0; i < 4; i++) {
      if (!current || current === document.body || current === document.documentElement) break;
      const tag = current.tagName.toLowerCase();
      const rawClass = current.classList[0] || '';
      const cssModuleClass = rawClass.match(/^_(.+)_[a-z0-9]{5,}_\d+$/i);
      const cleanClass = rawClass ? '.' + (cssModuleClass ? cssModuleClass[1] : rawClass) : '';
      parts.unshift(tag + cleanClass);
      els.unshift(current);
      current = current.parentElement;
    }
    return { parts, els };
  }

  // --- React component probe (batched) ---
  function getReactComponents(els) {
    const ids = els.map((_, i) => '__react_probe_' + Date.now() + '_' + i);
    els.forEach((el, i) => el.setAttribute('data-probe', ids[i]));
    const cleanup = () => els.forEach(el => el.removeAttribute('data-probe'));
    return chrome.runtime.sendMessage({ type: 'get-react-components', probeIds: ids })
      .then(names => { cleanup(); return names || ids.map(() => null); })
      .catch(() => { cleanup(); return ids.map(() => null); });
  }

  // --- Overlay positioning ---
  function positionOverlay(el) {
    if (!el || el === document.body || el === document.documentElement) {
      overlay.style.display = 'none';
      return;
    }
    const rect = el.getBoundingClientRect();
    Object.assign(overlay.style, {
      display: 'block',
      top: rect.top + 'px',
      left: rect.left + 'px',
      width: rect.width + 'px',
      height: rect.height + 'px',
    });
  }

  // --- Toast ---
  function showToast(message) {
    const toast = document.createElement('div');
    Object.assign(toast.style, {
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      background: '#323232',
      color: '#fff',
      padding: '10px 16px',
      borderRadius: '6px',
      fontSize: '13px',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      zIndex: '2147483647',
      boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
      opacity: '0',
      transition: 'opacity 0.2s ease',
      maxWidth: '360px',
      wordBreak: 'break-all',
      lineHeight: '1.4',
    });
    toast.textContent = message;
    document.body.appendChild(toast);

    // Double rAF to trigger transition
    requestAnimationFrame(() => {
      requestAnimationFrame(() => { toast.style.opacity = '1'; });
    });

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 250);
    }, 2500);
  }

  // --- Cleanup ---
  function cleanup() {
    document.removeEventListener('mousemove', onMousemove);
    document.removeEventListener('click', onClick, true);
    document.removeEventListener('keydown', onKeydown, true);
    overlay.remove();
    document.body.style.cursor = prevCursor;
    window.__domPickerActive = false;
    chrome.runtime.sendMessage({ type: 'picker-done' });
  }

  // --- Event handlers ---
  function onMousemove(e) {
    positionOverlay(e.target);
  }

  function buildText(parts, components) {
    let prev;
    return parts.map((part, i) => {
      const comp = components[i];
      const prefix = comp && comp !== prev ? comp + ':' : '';
      prev = comp;
      return prefix + part;
    }).join(' > ');
  }

  async function onClick(e) {
    e.preventDefault();
    e.stopPropagation();
    const { parts, els } = getElementPath(e.target);
    const components = await getReactComponents(els);
    const text = buildText(parts, components);
    cleanup();
    navigator.clipboard.writeText('`' + text + '`')
      .then(() => showToast('Copied: ' + text))
      .catch(() => showToast('Failed to copy to clipboard'));
  }

  function onKeydown(e) {
    if (e.key === 'Escape') {
      cleanup();
    }
  }

  document.addEventListener('mousemove', onMousemove);
  document.addEventListener('click', onClick, true);
  document.addEventListener('keydown', onKeydown, true);
})();
