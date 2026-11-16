import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { api, ApiError } from '../api/client';
import type { Burndown, Issue, IssueList, IssueStatus, Sprint } from '../api/types';
import { BurndownChart } from '../components/BurndownChart';
import { IssueCard } from '../components/IssueCard';
import { ErrorBanner, SkeletonRows } from '../components/ui';
import { useApi, useDocumentTitle } from '../hooks/useApi';
import { STATUS_ORDER, formatDateOnly, statusLabel } from '../lib/format';

export function Board() {
  useDocumentTitle('Sprint board');
  const sprints = useApi<Sprint[]>('/api/sprints');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [movingId, setMovingId] = useState<number | null>(null);
  const [moveError, setMoveError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedId !== null) return;
    const list = sprints.data ?? [];
    if (list.length === 0) return;
    const active = list.find((sprint) => sprint.status === 'active');
    setSelectedId(active ? active.id : list[0].id);
  }, [sprints.data, selectedId]);

  const issues = useApi<IssueList>(selectedId ? `/api/issues?sprint_id=${selectedId}&limit=200` : null);
  const burndown = useApi<Burndown>(selectedId ? `/api/sprints/${selectedId}/burndown` : null);

  const sprintList = sprints.data ?? [];
  const selected = sprintList.find((sprint) => sprint.id === selectedId) ?? null;
  const items = issues.data?.items ?? [];
  const sprintError = sprints.error ?? issues.error ?? burndown.error;

  async function moveIssue(issue: Issue, status: IssueStatus) {
    if (issue.status === status) return;
    setMovingId(issue.id);
    setMoveError(null);
    try {
      await api.patch<Issue>(`/api/issues/${issue.id}`, { status });
      issues.reload();
      burndown.reload();
      sprints.reload();
    } catch (error) {
      setMoveError(error instanceof ApiError ? error.message : 'Could not move the card.');
    } finally {
      setMovingId(null);
    }
  }

  return (
    <main className="page stack">
      <div className="page__head">
        <div>
          <p className="eyebrow">Sprint cycles</p>
          <h1 className="page__title">Board</h1>
          <p className="page__sub">
            {selected
              ? `${selected.name} · ${formatDateOnly(selected.start_date)} – ${formatDateOnly(
                  selected.end_date,
                )} · ${selected.issue_count} issues`
              : 'Pick a sprint to see its cards.'}
          </p>
        </div>
        <div className="page__actions">
          <div className="field" style={{ minWidth: 220 }}>
            <label className="field__label" htmlFor="sprint-select">
              Sprint
            </label>
            <select
              id="sprint-select"
              className="select"
              value={selectedId ?? ''}
              onChange={(event) => setSelectedId(Number(event.target.value))}
            >
              {sprintList.map((sprint) => (
                <option value={sprint.id} key={sprint.id}>
                  {sprint.project_key} · {sprint.name} ({sprint.status})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {sprintError ? (
        <ErrorBanner
          message={sprintError.message}
          onRetry={() => {
            sprints.reload();
            issues.reload();
            burndown.reload();
          }}
        />
      ) : null}
      {moveError ? <ErrorBanner message={moveError} /> : null}

      <section className="card" aria-labelledby="burndown-heading">
        <div className="card__head">
          <h2 className="card__title" id="burndown-heading">
            Burndown
          </h2>
          <span className="card__meta">
            {selected ? `${selected.goal}` : 'Ideal versus actual remaining points'}
          </span>
        </div>
        {burndown.loading && burndown.data === null ? (
          <SkeletonRows rows={4} />
        ) : burndown.data ? (
          <BurndownChart data={burndown.data} />
        ) : (
          <p className="muted">No burndown data for this sprint yet.</p>
        )}
      </section>

      {selected && items.length === 0 && !issues.loading ? (
        <div className="empty">
          <p className="empty__title">This sprint has no issues yet</p>
          <p className="empty__text">
            Populate {selected.name} from the issue list, or add a card directly into a column.
          </p>
          <Link className="btn btn--primary" to={`/issues?new=1&sprint=${selected.id}`}>
            Add the first issue
          </Link>
        </div>
      ) : null}

      <div className="board">
        {STATUS_ORDER.map((status) => {
          const columnIssues = items.filter((issue) => issue.status === status);
          return (
            <section className="column" key={status} aria-label={`${statusLabel(status)} column`}>
              <header className="column__head">
                <h2 className="column__title">
                  <span className={`pill__dot`} aria-hidden="true" />
                  {statusLabel(status)}
                </h2>
                <span className="column__count">{columnIssues.length}</span>
              </header>
              <div className="column__body">
                {issues.loading && issues.data === null ? (
                  <SkeletonRows rows={2} />
                ) : columnIssues.length === 0 ? (
                  <div className="lane__empty">
                    <p>No issues in this column.</p>
                    <Link
                      className="btn btn--ghost btn--sm"
                      to={`/issues?new=1&status=${status}${selectedId ? `&sprint=${selectedId}` : ''}`}
                      style={{ marginTop: 8 }}
                    >
                      Add issue
                    </Link>
                  </div>
                ) : (
                  columnIssues.map((issue) => (
                    <IssueCard
                      key={issue.id}
                      issue={issue}
                      busy={movingId === issue.id}
                      onMove={(target, nextStatus) => void moveIssue(target, nextStatus)}
                    />
                  ))
                )}
              </div>
            </section>
          );
        })}
      </div>
    </main>
  );
}
