/**
 * HintButtons.jsx
 *
 * Three progressive hint level buttons (L1 → L2 → L3).
 * Each level is only accessible after the previous one has been used,
 * enforcing the progressive Socratic disclosure model.
 */
import React from 'react';

const LEVELS = [
  {
    level: 1,
    id: 'lc-hint-l1',
    label: 'Hint L1',
    tooltip: 'Pinpoint the logic flaw (~50 words)',
    color: 'lc-coach-l1',
    activeBg: 'lc-bg-blue-50',
    activeBorder: 'lc-border-blue-200',
    activeText: 'lc-text-blue-700',
    hoverBg: 'hover:lc-bg-blue-50',
    hoverBorder: 'hover:lc-border-blue-200',
    icon: '💡',
  },
  {
    level: 2,
    id: 'lc-hint-l2',
    label: 'Hint L2',
    tooltip: 'Dry-run trace of failing edge case (~200 words)',
    activeBg: 'lc-bg-violet-50',
    activeBorder: 'lc-border-violet-200',
    activeText: 'lc-text-violet-700',
    hoverBg: 'hover:lc-bg-violet-50',
    hoverBorder: 'hover:lc-border-violet-200',
    icon: '🔍',
  },
  {
    level: 3,
    id: 'lc-hint-l3',
    label: 'Hint L3',
    tooltip: 'Full contrast with optimal pattern + reference code (~500 words)',
    activeBg: 'lc-bg-pink-50',
    activeBorder: 'lc-border-pink-200',
    activeText: 'lc-text-pink-700',
    hoverBg: 'hover:lc-bg-pink-50',
    hoverBorder: 'hover:lc-border-pink-200',
    icon: '🧠',
  },
];

export default function HintButtons({ strategySelected, maxUnlockedLevel, activeLevel, onHint, isLoading }) {
  return (
    <div className="lc-w-full">
      <label className="lc-block lc-text-xs lc-font-medium lc-text-coach-text-secondary lc-mb-1.5 lc-uppercase lc-tracking-wide">
        Progressive Hints
      </label>
      <div className="lc-flex lc-gap-2">
        {LEVELS.map(({ level, id, label, tooltip, activeBg, activeBorder, activeText, hoverBg, hoverBorder, icon }) => {
          const isUnlocked = strategySelected && level <= maxUnlockedLevel + 1;
          const isActive = activeLevel === level;
          const isLoadingThis = isLoading && isActive;

          return (
            <button
              key={level}
              id={id}
              title={tooltip}
              disabled={!isUnlocked || isLoading}
              onClick={() => isUnlocked && !isLoading && onHint(level)}
              className={`
                lc-flex-1 lc-flex lc-flex-col lc-items-center lc-gap-0.5
                lc-border lc-rounded-btn lc-px-2 lc-py-2 lc-text-xs lc-font-medium
                lc-transition-all lc-duration-150 lc-cursor-pointer
                ${isActive
                  ? `${activeBg} ${activeBorder} ${activeText} lc-shadow-btn`
                  : isUnlocked
                    ? `lc-bg-coach-surface lc-border-coach-border lc-text-coach-text ${hoverBg} ${hoverBorder}`
                    : 'lc-bg-gray-50 lc-border-gray-100 lc-text-gray-300 lc-cursor-not-allowed lc-opacity-50'
                }
              `}
            >
              <span className="lc-text-base lc-leading-none">{isLoadingThis ? '⏳' : icon}</span>
              <span>{label}</span>
            </button>
          );
        })}
      </div>
      {!strategySelected && (
        <p className="lc-mt-1.5 lc-text-xs lc-text-coach-text-muted">
          Select a strategy above to unlock hints.
        </p>
      )}
    </div>
  );
}
