import { Link } from 'react-router-dom';

import type { Activity } from '../api/types';
import { priorityLabel, relativeTime, statusLabel } from '../lib/format';
import { Avatar } from './ui';

function describe(event: Activity): string {
  switch (event.kind) {
    case 'created':
      return 'created this issue';
    case 'comment_added':
      return 'commented';
    case 'status_changed':
      return `changed status from ${statusLabel(event.from_value)} to ${statusLabel(event.to_value)}`;
    case 'priority_changed':
      return `changed priority from ${priorityLabel(event.from_value)} to ${priorityLabel(event.to_value)}`;
    case 'assignee_changed':
      return `reassigned from ${event.from_value ?? 'Unassigned'} to ${event.to_value ?? 'Unassigned'}`;
    case 'sprint_changed':
      return `moved sprint from ${event.from_value ?? 'Backlog'} to ${event.to_value ?? 'Backlog'}`;
    default:
      return 'updated the issue';
  }
}

export function ActivityFeed({
  events,
  showIssue = false,
}: {
  events: Activity[];
  showIssue?: boolean;
}) {
  if (events.length === 0) {
    return (
      <div className="empty">
        <p className="empty__title">No activity yet</p>
        <p className="empty__text">Status, priority, assignee and sprint changes will appear here as they happen.</p>
      </div>
    );
  }

  return (
    <ol className="activity">
      {events.map((event) => (
        <li className="activity__item" key={event.id}>
          <Avatar user={event.actor} size="sm" />
          <span className="activity__text">
            <strong>{event.actor.name}</strong> {describe(event)}
            {showIssue ? (
              <>
                {': '}
                <Link to={`/issues/${event.issue_id}`}>
                  {event.issue_key} {event.issue_title}
                </Link>
              </>
            ) : null}
          </span>
          <time className="activity__time" dateTime={event.created_at}>
            {relativeTime(event.created_at)}
          </time>
        </li>
      ))}
    </ol>
  );
}
