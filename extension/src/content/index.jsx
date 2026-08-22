/**
 * Content Script Entry Point
 *
 * Mounts the React coaching panel inside a Shadow DOM to fully
 * isolate styles from LeetCode's page CSS.
 */
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from '../panel/App.jsx';
import { initTreeSitter, attachEditorObserver } from './ASTParser.js';
import { connect, onMessage, onStatusChange } from './wsClient.js';

// ── Inline CSS via Vite's ?inline import ─────────────────────────────────────
// This bundles the CSS as a string at build time — the correct way to
// inject Tailwind into a Shadow DOM for Chrome extensions.
import panelCSS from '../panel/index.css?inline';

// ── Shadow DOM Setup ────────────────────────────────────────────────────────

const hostEl = document.createElement('div');
hostEl.id = 'lc-coach-host';
hostEl.style.cssText = 'position:fixed;top:0;left:0;z-index:2147483647;pointer-events:none;';
document.documentElement.appendChild(hostEl);

const shadow = hostEl.attachShadow({ mode: 'open' });

// Inject Tailwind + custom CSS into shadow root as a <style> tag
// (avoids cross-origin issues with <link> tags in shadow DOM)
const styleEl = document.createElement('style');
styleEl.textContent = panelCSS;
shadow.appendChild(styleEl);

// Google Fonts (safe to load as <link> since it's a network resource)
const fontsLink = document.createElement('link');
fontsLink.rel = 'stylesheet';
fontsLink.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap';
shadow.appendChild(fontsLink);

const mountEl = document.createElement('div');
mountEl.style.cssText = 'pointer-events:auto;';
shadow.appendChild(mountEl);

// ── SPA Navigation & Slug Detection ─────────────────────────────────────────

/**
 * Extract problem slug from current URL.
 * Returns null if not on a problem page.
 */
function getSlugFromURL() {
  const match = window.location.pathname.match(/\/problems\/([^/?#]+)/);
  return match ? match[1] : null;
}

/** Broadcast a slug change to the React panel */
function notifySlugChange(slug) {
  mountEl.dispatchEvent(
    new CustomEvent('lc-slug-change', { bubbles: false, detail: { slug } })
  );
}

// 1. Read slug on initial load
let currentSlug = getSlugFromURL();

// 2. Intercept history.pushState / replaceState (LeetCode uses these for SPA nav)
const _push    = history.pushState.bind(history);
const _replace = history.replaceState.bind(history);

history.pushState = function (...args) {
  _push(...args);
  handleURLChange();
};
history.replaceState = function (...args) {
  _replace(...args);
  handleURLChange();
};

// 3. Also handle browser back/forward
window.addEventListener('popstate', handleURLChange);

function handleURLChange() {
  const newSlug = getSlugFromURL();
  if (newSlug && newSlug !== currentSlug) {
    currentSlug = newSlug;
    console.log(`[LCCoach] Navigated to: ${newSlug}`);
    notifySlugChange(newSlug);
  }
}

// 4. Also listen for service worker SLUG_DETECTED (fires on full page load)
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'SLUG_DETECTED' && msg.slug !== currentSlug) {
    currentSlug = msg.slug;
    notifySlugChange(msg.slug);
  }
});

// Initialize tree-sitter (non-blocking)
initTreeSitter().then(() => {
  console.log('[LCCoach] tree-sitter initialized.');
  attachEditorObserver(({ code, language, astSummary }) => {
    // Broadcast AST updates to the React panel via a custom event
    mountEl.dispatchEvent(
      new CustomEvent('lc-ast-update', {
        bubbles: false,
        detail: { code, language, astSummary },
      })
    );
  });
}).catch((err) => {
  console.warn('[LCCoach] tree-sitter init failed (wasm not bundled yet):', err.message);
});

// Connect WebSocket (will silently fail if backend not running)
connect();
onStatusChange((status) => {
  mountEl.dispatchEvent(new CustomEvent('lc-ws-status', { bubbles: false, detail: { status } }));
});
onMessage((data) => {
  mountEl.dispatchEvent(new CustomEvent('lc-ws-message', { bubbles: false, detail: data }));
});

// ─── Mount React App ─────────────────────────────────────────────────────────

const root = createRoot(mountEl);
root.render(
  <React.StrictMode>
    <App mountEl={mountEl} />
  </React.StrictMode>
);
