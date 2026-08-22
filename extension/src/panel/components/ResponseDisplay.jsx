/**
 * ResponseDisplay.jsx
 *
 * Renders streamed markdown tokens from the LangGraph backend.
 * Shows a typing indicator while waiting, then progressively displays content.
 */
import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

export default function ResponseDisplay({ content, isLoading, activeAction, activeLevel }) {
  const scrollRef = useRef(null);

  // Auto-scroll to bottom as tokens stream in
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [content]);

  if (!isLoading && !content) return null;

  const headerLabel =
    activeAction === 'UPGRADE'
      ? '⚡ Upgrade Analysis'
      : activeLevel === 1
        ? '💡 Hint — Level 1'
        : activeLevel === 2
          ? '🔍 Hint — Level 2'
          : '🧠 Hint — Level 3';

  return (
    <div className="lc-w-full lc-animate-slide-up">
      {/* Header bar */}
      <div className="lc-flex lc-items-center lc-justify-between lc-mb-2">
        <span className="lc-text-xs lc-font-semibold lc-text-coach-accent lc-uppercase lc-tracking-wide">
          {headerLabel}
        </span>
        {isLoading && (
          <span className="lc-flex lc-items-center lc-gap-1 lc-text-xs lc-text-coach-text-muted">
            <span className="lc-w-1.5 lc-h-1.5 lc-rounded-full lc-bg-coach-accent lc-animate-pulse" />
            streaming
          </span>
        )}
      </div>

      {/* Scrollable content pane */}
      <div
        ref={scrollRef}
        className={`
          lc-max-h-64 lc-overflow-y-auto lc-rounded-btn
          lc-bg-coach-surface lc-border lc-border-coach-border
          lc-p-3 lc-text-sm lc-text-coach-text
          lc-leading-relaxed
        `}
      >
        {isLoading && !content ? (
          /* Skeleton shimmer while waiting for first token */
          <SkeletonLines />
        ) : (
          <div className="lc-prose lc-prose-sm lc-max-w-none lc-coach-markdown">
            <ReactMarkdown
              components={{
                code({ inline, children, ...props }) {
                  return inline ? (
                    <code
                      className="lc-bg-gray-100 lc-rounded lc-px-1 lc-py-0.5 lc-font-mono lc-text-xs lc-text-coach-accent"
                      {...props}
                    >
                      {children}
                    </code>
                  ) : (
                    <pre className="lc-bg-gray-900 lc-rounded-btn lc-p-3 lc-overflow-x-auto lc-my-2">
                      <code className="lc-font-mono lc-text-xs lc-text-gray-100" {...props}>
                        {children}
                      </code>
                    </pre>
                  );
                },
                p: ({ children }) => (
                  <p className="lc-mb-2 last:lc-mb-0">{children}</p>
                ),
                ul: ({ children }) => (
                  <ul className="lc-list-disc lc-pl-4 lc-mb-2">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="lc-list-decimal lc-pl-4 lc-mb-2">{children}</ol>
                ),
                strong: ({ children }) => (
                  <strong className="lc-font-semibold lc-text-coach-text">{children}</strong>
                ),
              }}
            >
              {content}
            </ReactMarkdown>
            {/* Blinking cursor while streaming */}
            {isLoading && (
              <span className="lc-inline-block lc-w-0.5 lc-h-4 lc-bg-coach-accent lc-animate-pulse lc-ml-0.5 lc-align-text-bottom" />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function SkeletonLines() {
  return (
    <div className="lc-space-y-2 lc-animate-pulse">
      {[85, 100, 70, 90, 55].map((w, i) => (
        <div
          key={i}
          className="lc-h-3 lc-bg-gray-200 lc-rounded-full"
          style={{ width: `${w}%` }}
        />
      ))}
    </div>
  );
}
