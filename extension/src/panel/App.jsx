/**
 * App.jsx — Main floating coaching panel
 *
 * Clean light minimal design (white/gray card).
 * Draggable, collapsible, with connection status indicator.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import StrategyDropdown from './components/StrategyDropdown.jsx';
import HintButtons from './components/HintButtons.jsx';
import UpgradeButton from './components/UpgradeButton.jsx';
import ResponseDisplay from './components/ResponseDisplay.jsx';
import { sendPayload } from '../content/wsClient.js';

export default function App({ mountEl }) {
  // ── Panel visibility & drag ────────────────────────────────────────────────
  const [collapsed, setCollapsed] = useState(false);
  const [position, setPosition] = useState({ x: 16, y: 80 });
  const dragging = useRef(false);
  const dragOffset = useRef({ x: 0, y: 0 });

  // ── State ──────────────────────────────────────────────────────────────────
  const [strategy, setStrategy]             = useState(null);
  const [maxUnlockedLevel, setMaxUnlocked]  = useState(0);
  const [activeLevel, setActiveLevel]       = useState(null);
  const [activeAction, setActiveAction]     = useState(null);
  const [isLoading, setIsLoading]           = useState(false);
  const [response, setResponse]             = useState('');
  const [wsStatus, setWsStatus]             = useState('disconnected');
  const [astSummary, setAstSummary]         = useState(null);
  const [slug, setSlug]                     = useState(null);
  const [problemData, setProblemData]       = useState(null);  // Phase 3: from DB

  // ── Listen for CustomEvents from content script ────────────────────────────
  useEffect(() => {
    if (!mountEl) return;

    const onAstUpdate = (e) => {
      setAstSummary(e.detail.astSummary);
    };
    const onWsStatus = (e) => {
      setWsStatus(e.detail.status);
    };
    const onWsMessage = (e) => {
      const data = e.detail;
      if (data.type === 'TOKEN') {
        setResponse((prev) => prev + data.token);
      } else if (data.type === 'DONE') {
        setIsLoading(false);
      } else if (data.type === 'CACHE_HIT') {
        setResponse('⚡ _Cached response_ \n\n');
      } else if (data.type === 'PROBLEM_CTX') {
        // Phase 3: backend confirmed real complexity targets
        // Update problemData with live tier info from DB
        setProblemData((prev) => ({
          ...prev,
          title: data.title,
          difficulty: data.difficulty,
          complexity_targets: {
            ...(prev?.complexity_targets ?? {}),
            [data.tier_info?.tier]: data.tier_info,
          },
        }));
      } else if (data.type === 'RATE_LIMIT') {
        setIsLoading(false);
        setResponse(`\n\n_⏳ Rate limit reached. Try again in ${data.retry_after}s._`);
      } else if (data.type === 'ERROR') {
        setIsLoading(false);
        setResponse((prev) => prev + '\n\n_⚠️ ' + data.message + '_');
      }
    };
    // Reset all state when user navigates to a new LeetCode problem
    const onSlugChange = (e) => {
      const newSlug = e.detail.slug;
      setSlug(newSlug);
      setStrategy(null);
      setMaxUnlocked(0);
      setActiveLevel(null);
      setActiveAction(null);
      setResponse('');
      setIsLoading(false);
      setAstSummary(null);
      setProblemData(null);
      // Phase 3: fetch problem metadata from backend DB
      fetch(`http://localhost:8000/api/problems/${newSlug}`)
        .then((r) => r.ok ? r.json() : null)
        .then((data) => { if (data) setProblemData(data); })
        .catch(() => {});
      console.log(`[LCCoach] Panel reset for new problem: ${newSlug}`);
    };

    mountEl.addEventListener('lc-ast-update', onAstUpdate);
    mountEl.addEventListener('lc-ws-status', onWsStatus);
    mountEl.addEventListener('lc-ws-message', onWsMessage);
    mountEl.addEventListener('lc-slug-change', onSlugChange);

    return () => {
      mountEl.removeEventListener('lc-ast-update', onAstUpdate);
      mountEl.removeEventListener('lc-ws-status', onWsStatus);
      mountEl.removeEventListener('lc-ws-message', onWsMessage);
      mountEl.removeEventListener('lc-slug-change', onSlugChange);
    };
  }, [mountEl]);

  // Get slug from URL on mount + fetch problem data
  useEffect(() => {
    const match = window.location.pathname.match(/\/problems\/([^/]+)/);
    if (match) {
      setSlug(match[1]);
      fetch(`http://localhost:8000/api/problems/${match[1]}`)
        .then((r) => r.ok ? r.json() : null)
        .then((data) => { if (data) setProblemData(data); })
        .catch(() => {});
    }
  }, []);

  // Compute complexity hint for current strategy from DB data
  const complexityHint = strategy && problemData?.complexity_targets?.[strategy]
    ? `${problemData.complexity_targets[strategy].time_complexity} · ${problemData.complexity_targets[strategy].approach_name}`
    : null;

  // ── Drag logic ─────────────────────────────────────────────────────────────
  const onMouseDown = useCallback((e) => {
    if (e.target.closest('button, select')) return;
    dragging.current = true;
    dragOffset.current = { x: e.clientX - position.x, y: e.clientY - position.y };
    e.preventDefault();
  }, [position]);

  useEffect(() => {
    const onMouseMove = (e) => {
      if (!dragging.current) return;
      const newX = Math.max(0, Math.min(window.innerWidth - 360, e.clientX - dragOffset.current.x));
      const newY = Math.max(0, Math.min(window.innerHeight - 60, e.clientY - dragOffset.current.y));
      setPosition({ x: newX, y: newY });
    };
    const onMouseUp = () => { dragging.current = false; };
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
    return () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };
  }, []);

  // ── Actions ────────────────────────────────────────────────────────────────
  const buildPayload = (action, hintLevel = null) => ({
    problem_slug: slug ?? window.__lcCoachSlug ?? 'unknown',
    action,
    hint_level: hintLevel,
    selected_tier: strategy,
    ast_summary: astSummary,
    code_text: astSummary?.raw ?? '',
  });

  const handleHint = (level) => {
    setActiveLevel(level);
    setActiveAction('HINT');
    setResponse('');
    setIsLoading(true);
    if (level > maxUnlockedLevel) setMaxUnlocked(level);
    sendPayload(buildPayload('HINT', level));
  };

  const handleUpgrade = () => {
    setActiveAction('UPGRADE');
    setActiveLevel(null);
    setResponse('');
    setIsLoading(true);
    sendPayload(buildPayload('UPGRADE'));
  };

  const handleStrategyChange = (val) => {
    setStrategy(val);
    setResponse('');
    setActiveLevel(null);
    setActiveAction(null);
    setMaxUnlocked(0);
  };

  // ── Connection status dot ──────────────────────────────────────────────────
  const statusColor = wsStatus === 'connected'
    ? 'lc-bg-coach-success'
    : wsStatus === 'connecting'
      ? 'lc-bg-coach-warning lc-animate-pulse'
      : 'lc-bg-gray-300';

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div
      style={{
        position: 'fixed',
        left: position.x,
        top: position.y,
        width: 350,
        zIndex: 2147483646,
        fontFamily: 'Inter, system-ui, sans-serif',
      }}
      className="lc-animate-fade-in"
    >
      <div className="lc-bg-coach-bg lc-rounded-panel lc-shadow-panel lc-border lc-border-coach-border lc-overflow-hidden lc-transition-shadow lc-duration-200 hover:lc-shadow-panel-hover">

        {/* ── Header ────────────────────────────────────────────────────── */}
        <div
          className="lc-flex lc-items-center lc-justify-between lc-px-4 lc-py-3 lc-border-b lc-border-coach-border lc-cursor-grab active:lc-cursor-grabbing lc-select-none"
          onMouseDown={onMouseDown}
        >
          <div className="lc-flex lc-items-center lc-gap-2">
            {/* Logo mark */}
            <div className="lc-w-6 lc-h-6 lc-rounded lc-bg-coach-accent lc-flex lc-items-center lc-justify-center">
              <span className="lc-text-white lc-text-xs lc-font-bold">AI</span>
            </div>
            <span className="lc-text-sm lc-font-semibold lc-text-coach-text">Algo Coach</span>
            {/* WS status */}
            <div className="lc-flex lc-items-center lc-gap-1">
              <span className={`lc-w-1.5 lc-h-1.5 lc-rounded-full ${statusColor}`} />
            </div>
          </div>

          <div className="lc-flex lc-items-center lc-gap-1">
            {slug && (
              <span className="lc-text-xs lc-text-coach-text-muted lc-bg-coach-surface lc-px-2 lc-py-0.5 lc-rounded-full lc-border lc-border-coach-border">
                {slug}
              </span>
            )}
            {/* Collapse toggle */}
            <button
              id="lc-collapse-btn"
              onClick={() => setCollapsed((c) => !c)}
              className="lc-p-1 lc-rounded lc-text-coach-text-muted hover:lc-text-coach-text hover:lc-bg-coach-surface lc-transition-colors lc-duration-100"
              title={collapsed ? 'Expand' : 'Collapse'}
            >
              <svg className={`lc-w-4 lc-h-4 lc-transition-transform lc-duration-200 ${collapsed ? '' : 'lc-rotate-180'}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        </div>

        {/* ── Body (collapsible) ─────────────────────────────────────────── */}
        {!collapsed && (
          <div className="lc-p-4 lc-flex lc-flex-col lc-gap-4">

            {/* Strategy Dropdown — Phase 3: shows real complexity from DB */}
            <StrategyDropdown
              value={strategy}
              onChange={handleStrategyChange}
              complexityHint={complexityHint}
            />

            {/* Divider */}
            <div className="lc-border-t lc-border-coach-border" />

            {/* Hint Buttons */}
            <HintButtons
              strategySelected={!!strategy}
              maxUnlockedLevel={maxUnlockedLevel}
              activeLevel={activeLevel}
              onHint={handleHint}
              isLoading={isLoading && activeAction === 'HINT'}
            />

            {/* Upgrade Button */}
            <UpgradeButton
              strategySelected={!!strategy}
              onUpgrade={handleUpgrade}
              isLoading={isLoading && activeAction === 'UPGRADE'}
              astSummary={astSummary}
            />

            {/* Response Display */}
            <ResponseDisplay
              content={response}
              isLoading={isLoading}
              activeAction={activeAction}
              activeLevel={activeLevel}
            />

            {/* Footer */}
            <div className="lc-flex lc-items-center lc-justify-between lc-pt-1">
              <span className="lc-text-xs lc-text-coach-text-muted">
                {astSummary
                  ? `AST: ${astSummary.nodeCount} nodes · ${astSummary.language}`
                  : 'AST: awaiting code…'}
              </span>
              {response && (
                <button
                  id="lc-clear-btn"
                  onClick={() => { setResponse(''); setActiveAction(null); setActiveLevel(null); }}
                  className="lc-text-xs lc-text-coach-text-muted hover:lc-text-coach-danger lc-transition-colors"
                >
                  Clear
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
