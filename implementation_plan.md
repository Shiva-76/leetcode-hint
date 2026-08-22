# Phase 1: Chrome Extension UI & WebAssembly AST

## Goal
Build the Chrome Extension shell (Manifest V3) with a React + TailwindCSS floating panel UI
and integrate `web-tree-sitter` (Wasm) for incremental AST parsing of user code on LeetCode/Codeforces.

## Proposed Changes

### Project Structure
```
leetcode-hint/
├── extension/               ← Chrome Extension root
│   ├── manifest.json        ← MV3 manifest
│   ├── public/
│   │   ├── icons/           ← extension icons (16, 48, 128px)
│   │   └── wasm/            ← tree-sitter.wasm + language .wasm files
│   ├── src/
│   │   ├── background/
│   │   │   └── service-worker.js   ← MV3 service worker (tab URL tracking)
│   │   ├── content/
│   │   │   ├── index.jsx           ← content script entry (mounts React panel)
│   │   │   ├── ASTParser.js        ← web-tree-sitter wrapper + MutationObserver
│   │   │   └── wsClient.js         ← WebSocket stub (for Phase 2 wiring)
│   │   └── panel/
│   │       ├── App.jsx             ← Floating panel root
│   │       ├── components/
│   │       │   ├── StrategyDropdown.jsx
│   │       │   ├── HintButtons.jsx
│   │       │   ├── UpgradeButton.jsx
│   │       │   └── ResponseDisplay.jsx
│   │       └── index.css           ← Tailwind + custom styles
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── vite.config.js       ← Vite bundler (MV3-compatible)
│   └── package.json
└── backend/                 ← (Phase 2+)
```

### Key Files

#### [NEW] manifest.json
- `manifest_version: 3`
- `content_scripts` targeting `*://leetcode.com/*` and `*://codeforces.com/*`
- `permissions`: `activeTab`, `storage`, `scripting`
- `web_accessible_resources` for `.wasm` files

#### [NEW] src/content/ASTParser.js
- Loads `web-tree-sitter` via dynamic import
- Initializes the Wasm module pointing to `public/wasm/tree-sitter.wasm`
- Loads language grammars (Python + C++)
- Sets up `MutationObserver` on the LeetCode/Codeforces code editor DOM node
- Exports `parseAST(codeText, language)` → returns a structured AST summary

#### [NEW] src/panel/App.jsx
- Floating draggable panel fixed on screen
- `StrategyDropdown` → BRUTE_FORCE | BETTER | OPTIMAL
- `HintButtons` → L1, L2, L3 buttons (disabled until strategy selected)
- `UpgradeButton` → Triggers UPGRADE action
- `ResponseDisplay` → Markdown renderer for streamed hints

#### [NEW] vite.config.js
- Multi-entry build (content script + panel)
- Copies `.wasm` to `dist/wasm/` via `vite-plugin-static-copy`
- Output format: `iife` for content scripts, `es` for panel

## Verification Plan
- Load unpacked extension in Chrome
- Navigate to a LeetCode problem
- Verify the floating panel appears
- Type code in the editor → confirm AST is parsed in the console
- Confirm all UI buttons render and the dropdown functions
