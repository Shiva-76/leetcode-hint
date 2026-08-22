/**
 * StrategyDropdown.jsx
 *
 * Lets the user select which algorithmic tier they are targeting.
 * NOTE: Complexity targets (e.g. O(N), O(log N)) are problem-specific and
 * will be fetched from the backend database in Phase 3.
 * The dropdown shows tier names only — no hardcoded complexity labels.
 */
import React from 'react';

const STRATEGIES = [
  {
    value: 'BRUTE_FORCE',
    label: 'Brute Force',
    description: 'Naive solution — correctness first',
    icon: '🐌',
    color: 'lc-text-coach-danger',
    dot: 'lc-bg-coach-danger',
  },
  {
    value: 'BETTER',
    label: 'Better',
    description: 'Improved approach — reduce redundant work',
    icon: '🔧',
    color: 'lc-text-coach-warning',
    dot: 'lc-bg-coach-warning',
  },
  {
    value: 'OPTIMAL',
    label: 'Optimal',
    description: 'Best known solution for this problem',
    icon: '⚡',
    color: 'lc-text-coach-success',
    dot: 'lc-bg-coach-success',
  },
];

export default function StrategyDropdown({ value, onChange, complexityHint }) {
  const selected = STRATEGIES.find((s) => s.value === value);

  return (
    <div className="lc-w-full">
      <label className="lc-block lc-text-xs lc-font-medium lc-text-coach-text-secondary lc-mb-1.5 lc-uppercase lc-tracking-wide">
        Target Strategy
      </label>
      <div className="lc-relative">
        <select
          id="lc-strategy-select"
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value || null)}
          className={`
            lc-w-full lc-appearance-none lc-bg-coach-surface lc-border lc-border-coach-border
            lc-rounded-btn lc-px-3 lc-py-2 lc-pr-8 lc-text-sm lc-font-medium
            lc-text-coach-text lc-cursor-pointer
            focus:lc-outline-none focus:lc-border-coach-accent focus:lc-ring-2
            focus:lc-ring-coach-accent focus:lc-ring-opacity-20
            hover:lc-border-coach-border-hover
            lc-transition-colors lc-duration-150
          `}
        >
          <option value="">— Select a strategy —</option>
          {STRATEGIES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.icon} {s.label}
            </option>
          ))}
        </select>
        {/* Custom dropdown arrow */}
        <div className="lc-pointer-events-none lc-absolute lc-inset-y-0 lc-right-2.5 lc-flex lc-items-center">
          <svg className="lc-w-4 lc-h-4 lc-text-coach-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Selected tier description */}
      {selected && (
        <div className="lc-mt-2 lc-flex lc-items-start lc-gap-1.5 lc-animate-fade-in">
          <span className={`lc-mt-0.5 lc-w-1.5 lc-h-1.5 lc-rounded-full lc-flex-shrink-0 ${selected.dot}`} />
          <div>
            <span className={`lc-text-xs lc-font-medium ${selected.color}`}>{selected.label}</span>
            <span className="lc-text-xs lc-text-coach-text-muted"> — {selected.description}</span>
            {/* Phase 3: complexity target from backend */}
            {complexityHint && (
              <div className="lc-text-xs lc-text-coach-accent lc-font-mono lc-mt-0.5">{complexityHint}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
