/**
 * ASTParser.js
 *
 * Wraps web-tree-sitter (Wasm) for incremental AST parsing of code
 * inside the LeetCode Monaco editor.
 *
 * Key responsibilities:
 * 1. Initialize tree-sitter Wasm engine once
 * 2. Load language grammars (Python, C++) on demand
 * 3. Parse code → produce a structured ASTSummary
 * 4. Observe LeetCode's Monaco editor via MutationObserver
 */

import TreeSitter from 'web-tree-sitter';

/** @type {TreeSitter | null} */
let pythonParser = null;
/** @type {TreeSitter | null} */
let cppParser = null;
let initialized = false;

/**
 * Initialize tree-sitter Wasm. Must be called once before any parsing.
 */
export async function initTreeSitter() {
  if (initialized) return;
  await TreeSitter.init({
    locateFile(scriptName) {
      // Point to our bundled wasm file inside the extension
      if (scriptName === 'tree-sitter.wasm') {
        return chrome.runtime.getURL('wasm/tree-sitter.wasm');
      }
      return scriptName;
    },
  });
  initialized = true;
}

/**
 * Lazily load the Python grammar.
 * @returns {Promise<TreeSitter>}
 */
async function getPythonParser() {
  if (pythonParser) return pythonParser;
  const lang = await TreeSitter.Language.load(
    chrome.runtime.getURL('wasm/tree-sitter-python.wasm')
  );
  pythonParser = new TreeSitter();
  pythonParser.setLanguage(lang);
  return pythonParser;
}

/**
 * Lazily load the C++ grammar.
 * @returns {Promise<TreeSitter>}
 */
async function getCppParser() {
  if (cppParser) return cppParser;
  const lang = await TreeSitter.Language.load(
    chrome.runtime.getURL('wasm/tree-sitter-cpp.wasm')
  );
  cppParser = new TreeSitter();
  cppParser.setLanguage(lang);
  return cppParser;
}

/**
 * Detect language from LeetCode's language selector.
 * @returns {'python' | 'cpp' | 'unknown'}
 */
function detectLanguage() {
  // LeetCode language selector button has data-cy="lang-select" or similar
  const langEl =
    document.querySelector('[data-track-load="description_content"] ~ * button[id*="headlessui-listbox-button"]') ||
    document.querySelector('.ant-select-selection-item') ||
    document.querySelector('[data-cy="lang-select"]');

  if (!langEl) return 'unknown';
  const text = langEl.textContent.toLowerCase();
  if (text.includes('python')) return 'python';
  if (text.includes('c++') || text.includes('cpp')) return 'cpp';
  return 'unknown';
}

/**
 * Extract code text from Monaco editor.
 * Tries the Monaco API first, falls back to DOM scraping.
 * @returns {string}
 */
export function extractCodeFromMonaco() {
  try {
    // LeetCode exposes monaco globally
    if (window.monaco?.editor) {
      const models = window.monaco.editor.getModels();
      if (models.length > 0) {
        return models[models.length - 1].getValue();
      }
    }
  } catch (_) {
    // Fall through to DOM approach
  }

  // DOM fallback: scrape visible lines from Monaco view-lines
  const lines = document.querySelectorAll('.view-line');
  if (lines.length > 0) {
    return Array.from(lines)
      .map((l) => l.textContent)
      .join('\n');
  }

  return '';
}

/**
 * Walk the parse tree and collect a high-level structural summary.
 * @param {TreeSitter.SyntaxNode} node
 * @param {number} depth
 * @returns {object}
 */
function summarizeNode(node, depth = 0) {
  const summary = {
    type: node.type,
    startLine: node.startPosition.row + 1,
    endLine: node.endPosition.row + 1,
  };

  if (node.type === 'for_statement' || node.type === 'for_range_loop' ||
      node.type === 'while_statement') {
    summary.isLoop = true;
  }
  if (node.type === 'call_expression' || node.type === 'function_definition' ||
      node.type === 'function_definition') {
    summary.isCallOrDef = true;
  }

  return summary;
}

/**
 * Parse code and return a compact ASTSummary for the backend.
 * @param {string} codeText
 * @param {'python' | 'cpp' | 'unknown'} language
 * @returns {Promise<ASTSummary>}
 */
export async function parseAST(codeText, language) {
  if (!initialized) await initTreeSitter();
  if (!codeText.trim()) {
    return { language, nodeCount: 0, loops: [], functions: [], hasNestedLoops: false, raw: '' };
  }

  let parser;
  try {
    parser = language === 'python' ? await getPythonParser() : await getCppParser();
  } catch (err) {
    console.warn('[ASTParser] Grammar wasm unavailable, returning stub:', err);
    return { language, nodeCount: 0, loops: [], functions: [], hasNestedLoops: false, raw: codeText };
  }

  const tree = parser.parse(codeText);
  const root = tree.rootNode;

  const loops = [];
  const functions = [];
  let nodeCount = 0;

  function walk(node, parentIsLoop = false) {
    nodeCount++;
    const isLoop = ['for_statement', 'while_statement', 'for_range_loop',
                    'for_in_clause'].includes(node.type);
    const isFunc = ['function_definition', 'function_declarator'].includes(node.type);

    if (isLoop) {
      loops.push({ type: node.type, line: node.startPosition.row + 1, nested: parentIsLoop });
    }
    if (isFunc) {
      const nameNode = node.childForFieldName('name');
      functions.push({ name: nameNode?.text ?? 'anonymous', line: node.startPosition.row + 1 });
    }

    for (let i = 0; i < node.childCount; i++) {
      walk(node.child(i), isLoop || parentIsLoop);
    }
  }

  walk(root);
  tree.delete();

  const hasNestedLoops = loops.some((l) => l.nested);

  return {
    language,
    nodeCount,
    loops,
    functions,
    hasNestedLoops,
    loopDepth: computeMaxLoopDepth(loops),
  };
}

/**
 * Compute maximum loop nesting depth as a proxy for time-complexity tier.
 * 0 loops → O(1), 1 → O(N), 2 → O(N²), etc.
 */
function computeMaxLoopDepth(loops) {
  if (loops.length === 0) return 0;
  let max = 0, depth = 0;
  for (const l of loops) {
    if (l.nested) depth++;
    else depth = 1;
    if (depth > max) max = depth;
  }
  return max;
}

// ─── MutationObserver ────────────────────────────────────────────────────────

let observerCallback = null;
let _observer = null;

/**
 * Attach a MutationObserver to Monaco's container.
 * Re-parses the AST on every editor change and calls cb(astSummary).
 * @param {function(object): void} cb
 */
export function attachEditorObserver(cb) {
  observerCallback = cb;
  tryAttach();
}

function tryAttach() {
  // Monaco's lines container — most reliable target for change detection
  const target = document.querySelector('.monaco-editor .overflow-guard');
  if (!target) {
    // Editor not mounted yet — retry
    setTimeout(tryAttach, 800);
    return;
  }

  if (_observer) _observer.disconnect();

  _observer = new MutationObserver(debounce(async () => {
    const code = extractCodeFromMonaco();
    const lang = detectLanguage();
    const summary = await parseAST(code, lang);
    observerCallback?.({ code, language: lang, astSummary: summary });
  }, 600));

  _observer.observe(target, { childList: true, subtree: true, characterData: true });
  console.log('[ASTParser] MutationObserver attached to Monaco editor.');
}

function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}
