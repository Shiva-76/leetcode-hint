/**
 * UpgradeButton.jsx
 *
 * The "Upgrade My Code" CTA. Triggers the UPGRADE action which evaluates
 * the user's current AST tier against the strategy DAG and either
 * congratulates (optimal) or Socratically prompts toward the next tier.
 */
import React from 'react';

export default function UpgradeButton({ strategySelected, onUpgrade, isLoading, astSummary }) {
  const loopDepth = astSummary?.loopDepth ?? null;
  const tierHint =
    loopDepth === null ? null
    : loopDepth === 0   ? 'Detected: O(1) or O(N) — no nested loops'
    : loopDepth === 1   ? 'Detected: ~O(N) loop'
    : loopDepth >= 2    ? `Detected: ~O(N${loopDepth > 2 ? loopDepth : '²'}) — ${loopDepth} loop levels`
    : null;

  return (
    <div className="lc-w-full">
      <button
        id="lc-upgrade-btn"
        disabled={!strategySelected || isLoading}
        onClick={() => strategySelected && !isLoading && onUpgrade()}
        className={`
          lc-w-full lc-flex lc-items-center lc-justify-center lc-gap-2
          lc-rounded-btn lc-py-2.5 lc-px-4 lc-text-sm lc-font-semibold
          lc-transition-all lc-duration-200
          ${strategySelected && !isLoading
            ? `lc-bg-coach-success lc-text-white
               hover:lc-bg-emerald-700 lc-shadow-btn hover:lc-shadow-md
               active:lc-scale-95`
            : 'lc-bg-gray-100 lc-text-gray-400 lc-cursor-not-allowed'}
        `}
      >
        {isLoading ? (
          <>
            <LoadingDots />
            <span>Analyzing…</span>
          </>
        ) : (
          <>
            <span>⚡</span>
            <span>Upgrade My Code</span>
          </>
        )}
      </button>

      {tierHint && (
        <p className="lc-mt-1.5 lc-text-xs lc-text-coach-text-muted lc-text-center lc-animate-fade-in">
          {tierHint}
        </p>
      )}
    </div>
  );
}

function LoadingDots() {
  return (
    <span className="lc-flex lc-gap-0.5 lc-items-center">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="lc-w-1 lc-h-1 lc-rounded-full lc-bg-white lc-animate-pulse-dot"
          style={{ animationDelay: `${i * 0.16}s` }}
        />
      ))}
    </span>
  );
}
