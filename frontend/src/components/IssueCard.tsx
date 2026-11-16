import { Link } from 'react-router-dom';

import type { Issue, IssueStatus } from '../api/types';
import { STATUS_ORDER, statusLabel } from '../lib/format';
import { Avatar, PriorityBadge } from './ui';

interface IssueCardProps {
  issue: Issue;
  onMove: (issue: Issue, status: IssueStatus) => void;
  busy: boolean;
}

export function IssueCard({ issue, onMove, busy }: IssueCardProps) {
  return (
    <article className="issue-card">
      <div className="cluster" style={{ justifyContent: 'space-between' }}>
        <span className="issue-card__key">{issue.key}</span>
        <PriorityBadge priority={issue.priority} showLabel={false} />
      </div>
      <Link className="issue-card__title" to={`/issues/${issue.id}`}>
        {issue.title}
      </Link>
      <div className="issue-card__meta">
        <span className="cluster" style={{ gap: 6 }}>
          <Avatar user={issue.assignee} size="sm" />
          <span className="muted" style={{ fontSize: 12 }}>
            {issue.assignee ? issue.assignee.name.split(' ')[0] : 'Unassigned'}
          </span>
        </span>
        <span className="muted" style={{ fontSize: 12 }}>
          {issue.estimate ? `${issue.estimate} pts` : '— pts'}
        </span>
      </div>
      <label className="sr-only" htmlFor={`move-${issue.id}`}>
        Move {issue.key} to another column
      </label>
      <select
        id={`move-${issue.id}`}
        className="issue-card__move"
        value={issue.status}
        disabled={busy}
        onChange={(event) => onMove(issue, event.target.value as IssueStatus)}
      >
        {STATUS_ORDER.map((status) => (
          <option value={status} key={status}>
            Move to {statusLabel(status)}
          </option>
        ))}
      </select>
    </article>
  );
}
