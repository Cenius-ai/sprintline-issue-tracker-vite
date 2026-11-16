import { Link } from 'react-router-dom';

import type { ActivityList, IssueList, Sprint, User } from '../api/types';
import { useAuth } from '../auth/AuthContext';
import { StatTile } from '../components/StatTile';
import { ActivityFeed } from '../components/ActivityFeed';
import { ErrorBanner, PriorityBadge, SkeletonRows, StatusPill } from '../components/ui';
import { useApi, useDocumentTitle } from '../hooks/useApi';
import { PRIORITY_ORDER, greeting, pluralize, priorityLabel, sprintProgress } from '../lib/format';

export function Dashboard() {
  useDocumentTitle('Overview');
  const { user } = useAuth();
  const issues = useApi<IssueList>('/api/issues?limit=200');
  const sprints = useApi<Sprint[]>('/api/sprints');
  const users = useApi<User[]>('/api/users');
  const activity = useApi<ActivityList>('/api/activity?limit=8');

  const items = issues.data?.items ?? [];
  const totalIssues = issues.data?.total ?? items.length;
  const activeSprint = (sprints.data ?? []).find((sprint) => sprint.status === 'active') ?? null;
  const loading = issues.loading && issues.data === null;
  const error = issues.error ?? sprints.error ?? users.error ?? activity.error;

  const openCount = items.filter((issue) => issue.status === 'backlog' || issue.status === 'todo').length;
  const activeCount = items.filter(
    (issue) => issue.status === 'in_progress' || issue.status === 'in_review',
  ).length;
  const doneCount = items.filter((issue) => issue.status === 'done').length;
  const points = items.reduce((sum, issue) => sum + (issue.estimate || 0), 0);

  const priorityCounts = PRIORITY_ORDER.map((priority) => ({
    priority,
    count: items.filter((issue) => issue.priority === priority).length,
  }));
  const priorityMax = Math.max(...priorityCounts.map((entry) => entry.count), 1);

  const workload = [
    ...(users.data ?? []).map((member) => ({
      id: `user-${member.id}`,
      label: member.name,
      color: member.avatar_color,
      count: items.filter((issue) => issue.assignee?.id === member.id && issue.status !== 'done').length,
    })),
    {
      id: 'unassigned',
      label: 'Unassigned',
      color: '#8b8b95',
      count: items.filter((issue) => !issue.assignee && issue.status !== 'done').length,
    },
  ].sort((a, b) => b.count - a.count);
  const workloadMax = Math.max(...workload.map((entry) => entry.count), 1);

  const myIssues = items
    .filter((issue) => issue.assignee?.id === user?.id && issue.status !== 'done')
    .slice(0, 6);

  const firstName = (user?.name ?? 'there').split(' ')[0];
  const sprintState = activeSprint ? sprintProgress(activeSprint.start_date, activeSprint.end_date) : null;
  const sprintPercent =
    activeSprint && activeSprint.issue_count > 0
      ? Math.round((activeSprint.done_count / activeSprint.issue_count) * 100)
      : 0;
  const projectCount = new Set(items.map((issue) => issue.project.id)).size;
  const subtitle = loading
    ? 'Loading the workspace…'
    : `${totalIssues} ${pluralize(totalIssues, 'issue')} across ${projectCount} ${pluralize(
        projectCount,
        'project',
      )}${activeSprint ? ` · ${activeSprint.name} is in flight` : ''}`;

  return (
    <main>
      <header className="masthead">
        <div className="masthead__inner">
          <div className="page__head">
            <div>
              <p className="eyebrow">Shared workspace</p>
              <h1 className="page__title">
                {greeting()}, {firstName}
              </h1>
              <p className="page__sub">{subtitle}</p>
            </div>
            <div className="page__actions">
              <Link className="btn btn--ghost" to="/board">
                Open board
              </Link>
              <Link className="btn btn--primary" to="/issues?new=1">
                New issue
              </Link>
            </div>
          </div>

          <div className="stats">
            {loading ? (
              Array.from({ length: 4 }).map((_, index) => (
                <div className="skeleton skeleton--tile" key={index} aria-hidden="true" />
              ))
            ) : (
              <>
                <StatTile label="Open" value={openCount} hint="Backlog and todo" />
                <StatTile label="In progress" value={activeCount} hint="In progress and in review" />
                <StatTile label="Done" value={doneCount} hint="Completed issues" />
                <StatTile label="Points" value={points} hint={`Estimated across ${totalIssues} issues`} />
              </>
            )}
          </div>
        </div>
      </header>

      <div className="page stack">
        {error && items.length === 0 ? (
          <ErrorBanner
            message={error.message}
            onRetry={() => {
              issues.reload();
              sprints.reload();
              users.reload();
              activity.reload();
            }}
          />
        ) : null}

        {!loading && totalIssues === 0 ? (
          <div className="card">
            <div className="empty">
              <p className="empty__title">No issues yet</p>
              <p className="empty__text">
                The workspace is empty. Create the first issue and it will show up here, on the board
                and in the roadmap.
              </p>
              <Link className="btn btn--primary" to="/issues?new=1">
                Create the first issue
              </Link>
            </div>
          </div>
        ) : null}

        <div className="grid-2">
          <section className="card" aria-labelledby="priority-heading">
            <div className="card__head">
              <h2 className="card__title" id="priority-heading">
                Issues by priority
              </h2>
              <span className="card__meta">{totalIssues} total</span>
            </div>
            {loading ? (
              <SkeletonRows rows={5} />
            ) : (
              <div className="bar-list">
                {priorityCounts.map((entry) => (
                  <div className="bar-row" key={entry.priority}>
                    <span className="bar-row__label">
                      <PriorityBadge priority={entry.priority} showLabel={false} />
                      {priorityLabel(entry.priority)}
                    </span>
                    <span className="bar-row__track">
                      <span
                        className="bar-row__fill"
                        style={{ width: `${Math.round((entry.count / priorityMax) * 100)}%` }}
                      />
                    </span>
                    <span className="bar-row__value">{entry.count}</span>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="card" aria-labelledby="workload-heading">
            <div className="card__head">
              <h2 className="card__title" id="workload-heading">
                Open work by assignee
              </h2>
              <span className="card__meta">Not done</span>
            </div>
            {loading ? (
              <SkeletonRows rows={5} />
            ) : (
              <div className="bar-list">
                {workload.map((entry) => (
                  <div className="bar-row" key={entry.id}>
                    <span className="bar-row__label" title={entry.label}>
                      <span
                        className="chip__dot"
                        style={{ background: entry.color, width: 8, height: 8 }}
                        aria-hidden="true"
                      />
                      <span className="truncate">{entry.label}</span>
                    </span>
                    <span className="bar-row__track">
                      <span
                        className="bar-row__fill"
                        style={{ width: `${Math.round((entry.count / workloadMax) * 100)}%` }}
                      />
                    </span>
                    <span className="bar-row__value">{entry.count}</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>

        <div className="grid-2">
          <section className="card card--interactive" aria-labelledby="sprint-heading">
            <div className="card__head">
              <h2 className="card__title" id="sprint-heading">
                Active sprint
              </h2>
              {activeSprint ? <span className="card__meta">{activeSprint.project_key}</span> : null}
            </div>
            {!activeSprint ? (
              <p className="muted">No sprint is active right now.</p>
            ) : (
              <div className="stack">
                <div>
                  <p className="glyph" style={{ fontWeight: 700 }}>
                    {activeSprint.name}
                  </p>
                  <p className="muted" style={{ fontSize: 13 }}>
                    {activeSprint.goal}
                  </p>
                </div>
                <div className="progress">
                  <div className="progress__track">
                    <div className="progress__fill" style={{ width: `${sprintPercent}%` }} />
                  </div>
                  <div className="cluster" style={{ justifyContent: 'space-between' }}>
                    <span className="muted" style={{ fontSize: 13 }}>
                      {activeSprint.done_count} of {activeSprint.issue_count} issues done
                    </span>
                    <span className="muted" style={{ fontSize: 13 }}>
                      {sprintState ? `Day ${sprintState.day} of ${sprintState.total}` : ''}
                    </span>
                  </div>
                </div>
                <div className="cluster">
                  <Link className="btn btn--ghost btn--sm" to="/board">
                    View board →
                  </Link>
                  <span className="muted" style={{ fontSize: 13 }}>
                    {activeSprint.point_count} points in the sprint
                  </span>
                </div>
              </div>
            )}
          </section>

          <section className="card" aria-labelledby="activity-heading">
            <div className="card__head">
              <h2 className="card__title" id="activity-heading">
                Recent activity
              </h2>
              <span className="card__meta">Last 8 events</span>
            </div>
            {activity.loading && activity.data === null ? (
              <SkeletonRows rows={5} />
            ) : (
              <ActivityFeed events={activity.data?.items ?? []} showIssue />
            )}
          </section>
        </div>

        <section className="card" aria-labelledby="mine-heading">
          <div className="card__head">
            <h2 className="card__title" id="mine-heading">
              Assigned to you
            </h2>
            <span className="card__meta">{user?.name ?? 'You'}</span>
          </div>
          {myIssues.length === 0 ? (
            <p className="muted">Nothing open is assigned to you. Pick something up from the board.</p>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <caption className="sr-only">Issues assigned to the signed-in user</caption>
                <thead>
                  <tr>
                    <th scope="col">Key</th>
                    <th scope="col">Title</th>
                    <th scope="col">Status</th>
                    <th scope="col">Priority</th>
                    <th scope="col">Sprint</th>
                  </tr>
                </thead>
                <tbody>
                  {myIssues.map((issue) => (
                    <tr key={issue.id}>
                      <td className="cell-key">{issue.key}</td>
                      <td>
                        <Link className="row-title" to={`/issues/${issue.id}`}>
                          {issue.title}
                        </Link>
                      </td>
                      <td>
                        <StatusPill status={issue.status} />
                      </td>
                      <td>
                        <PriorityBadge priority={issue.priority} />
                      </td>
                      <td className="muted">{issue.sprint?.name ?? 'Backlog'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
