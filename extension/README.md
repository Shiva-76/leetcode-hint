# LeetCode Algo Coach — Chrome Extension

## Phase 1: Setup & Build

### Prerequisites
- Node.js ≥ 18 (install via https://nodejs.org)
- npm ≥ 9

### Install Dependencies
```bash
cd extension
npm install
```

### Download Language Wasm Grammars
After `npm install`, copy the wasm files into `public/wasm/`:

```bash
# tree-sitter.wasm is auto-copied by vite-plugin-static-copy on build
# Language grammars need to be downloaded manually:
mkdir -p public/wasm

# Python grammar
curl -L -o public/wasm/tree-sitter-python.wasm \
  https://github.com/nickel-lang/tree-sitter-nickel/releases/download/0.22.6/tree-sitter-python.wasm

# OR use the npm package if available:
# copy node_modules/tree-sitter-python/tree-sitter-python.wasm public/wasm/

# C++ grammar
# Download from: https://github.com/tree-sitter/tree-sitter-cpp/releases
```

> **Note:** For Phase 1 testing the extension loads without wasm errors —
> ASTParser falls back gracefully if grammar files are missing.

### Build for Chrome
```bash
npm run build
# Output → dist/
```

### Load in Chrome
1. Open `chrome://extensions`
2. Enable **Developer Mode** (top right)
3. Click **Load unpacked**
4. Select the `dist/` folder
5. Navigate to any `leetcode.com/problems/*` page
6. The floating coaching panel should appear in the bottom-right corner

### Development (watch mode)
```bash
npm run dev
# Rebuilds on file save — reload extension in Chrome after each build
```

## File Structure
```
extension/
├── manifest.json          ← MV3 manifest
├── src/
│   ├── background/
│   │   └── service-worker.js   ← Tab URL → slug tracking
│   ├── content/
│   │   ├── index.jsx           ← Shadow DOM injection + event bus
│   │   ├── ASTParser.js        ← web-tree-sitter + MutationObserver
│   │   └── wsClient.js         ← WebSocket stub (Phase 2)
│   └── panel/
│       ├── App.jsx             ← Draggable floating panel
│       ├── components/
│       │   ├── StrategyDropdown.jsx
│       │   ├── HintButtons.jsx
│       │   ├── UpgradeButton.jsx
│       │   └── ResponseDisplay.jsx
│       └── index.css           ← Tailwind + shadow DOM styles
├── public/wasm/           ← tree-sitter .wasm files (see above)
├── vite.config.js
├── tailwind.config.js
└── package.json
```
