import type { ReactNode } from 'react';

import type { IssuePriority, IssueStatus, User } from '../api/types';
import { initials, priorityLabel, statusLabel } from '../lib/format';

export function Avatar({
  user,
  size = 'md',
}: {
  user: User | null;
  size?: 'sm' | 'md' | 'lg';
}) {
  const sizeClass = size === 'md' ? '' : ` avatar--${size}`;
  if (!user) {
    return (
      <span
        className={`avatar avatar--ghost${sizeClass}`}
        title="Unassigned"
        role="img"
        aria-label="Unassigned"
      >
        –
      </span>
    );
  }
  return (
    <span
      className={`avatar${sizeClass}`}
      style={{ background: user.avatar_color, color: '#111111' }}
      title={user.name}
      role="img"
      aria-label={user.name}
    >
      {initials(user.name)}
    </span>
  );
}

export function StatusPill({ status }: { status: IssueStatus }) {
  return (
    <span className={`pill pill--${status}`}>
      <span className="pill__dot" aria-hidden="true" />
      {statusLabel(status)}
    </span>
  );
}

export function LabelChips({
  labels,
  emptyText = '—',
}: {
  labels: { id: number; name: string; color: string }[];
  emptyText?: string;
}) {
  if (labels.length === 0) {
    return <span className="muted">{emptyText}</span>;
  }
  return (
    <span className="chips">
      {labels.map((label) => (
        <span className="chip" key={label.id}>
          <span className="chip__dot" style={{ background: label.color }} aria-hidden="true" />
          {label.name}
        </span>
      ))}
    </span>
  );
}

export function PriorityBadge({
  priority,
  showLabel = true,
}: {
  priority: IssuePriority;
  showLabel?: boolean;
}) {
  return (
    <span className={`priority priority--${priority}`} title={`Priority: ${priorityLabel(priority)}`}>
      <span className="priority__bars" aria-hidden="true">
        <span className="priority__bar" />
        <span className="priority__bar" />
        <span className="priority__bar" />
      </span>
      {showLabel ? <span>{priorityLabel(priority)}</span> : <span className="sr-only">{priorityLabel(priority)}</span>}
    </span>
  );
}

export function ErrorBanner({
  message,
  onRetry,
  retryLabel = 'Retry',
}: {
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
}) {
  return (
    <div className="banner banner--error" role="alert">
      <span>{message}</span>
      {onRetry ? (
        <button type="button" className="btn btn--ghost btn--sm" onClick={onRetry}>
          {retryLabel}
        </button>
      ) : null}
    </div>
  );
}

export function EmptyState({
  title,
  children,
  action,
}: {
  title: string;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <p className="empty__title">{title}</p>
      {children ? <p className="empty__text">{children}</p> : null}
      {action}
    </div>
  );
}

export function SkeletonRows({ rows = 6 }: { rows?: number }) {
  return (
    <div className="stack stack--tight" aria-hidden="true">
      {Array.from({ length: rows }).map((_, index) => (
        <div className="skeleton skeleton--row" key={index} />
      ))}
    </div>
  );
}
