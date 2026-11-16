import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { api, ApiError } from '../api/client';
import type { Issue, IssueList, Label, Project, Sprint, User } from '../api/types';
import { IssueForm, type IssueDraft } from '../components/IssueForm';
import { Avatar, EmptyState, ErrorBanner, LabelChips, PriorityBadge, SkeletonRows, StatusPill } from '../components/ui';
import { useApi, useDocumentTitle } from '../hooks/useApi';
import { PRIORITY_ORDER, STATUS_ORDER, priorityLabel, statusLabel } from '../lib/format';

export function Issues() {
  useDocumentTitle('Issues');
  const [params, setParams] = useSearchParams();
  const status = params.get('status') ?? '';
  const priority = params.get('priority') ?? '';
  const assignee = params.get('assignee') ?? '';
  const label = params.get('label') ?? '';
  const project = params.get('project') ?? '';
  const search = params.get('q') ?? '';
  const showCreate = params.get('new') === '1';

  const [searchDraft, setSearchDraft] = useState(search);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const update = useCallback(
    (patch: Record<string, string | null>) => {
      setParams(
        (previous) => {
          const next = new URLSearchParams(previous);
          for (const [key, value] of Object.entries(patch)) {
            if (value) {
              next.set(key, value);
            } else {
              next.delete(key);
            }
          }
          return next;
        },
        { replace: true },
      );
    },
    [setParams],
  );

  useEffect(() => {
    setSearchDraft(search);
  }, [search]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (searchDraft.trim() !== search) {
        update({ q: searchDraft.trim() || null });
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [searchDraft, search, update]);

  const query = useMemo(() => {
    const builder = new URLSearchParams();
    if (status) builder.set('status', status);
    if (priority) builder.set('priority', priority);
    if (assignee) builder.set('assignee_id', assignee);
    if (label) builder.set('label_id', label);
    if (project) builder.set('project_id', project);
    if (search) builder.set('q', search);
    builder.set('limit', '100');
    return `/api/issues?${builder.toString()}`;
  }, [status, priority, assignee, label, project, search]);

  const issues = useApi<IssueList>(query);
  const users = useApi<User[]>('/api/users');
  const labels = useApi<Label[]>('/api/labels');
  const projects = useApi<Project[]>('/api/projects');
  const sprints = useApi<Sprint[]>('/api/sprints');

  const items = issues.data?.items ?? [];
  const total = issues.data?.total ?? items.length;
  const hasFilters = Boolean(status || priority || assignee || label || project || search);
  const initialLoading = issues.loading && issues.data === null;

  const filterSummary = [
    status ? `status: ${statusLabel(status)}` : null,
    priority ? `priority: ${priorityLabel(priority)}` : null,
    assignee
      ? `assignee: ${
          assignee === 'unassigned'
            ? 'Unassigned'
            : (users.data ?? []).find((user) => String(user.id) === assignee)?.name ?? 'unknown'
        }`
      : null,
    label ? `label: ${(labels.data ?? []).find((entry) => String(entry.id) === label)?.name ?? 'unknown'}` : null,
    project
      ? `project: ${(projects.data ?? []).find((entry) => String(entry.id) === project)?.key ?? 'unknown'}`
      : null,
    search ? `search: “${search}”` : null,
  ].filter(Boolean) as string[];

  function clearFilters() {
    setSearchDraft('');
    update({ status: null, priority: null, assignee: null, label: null, project: null, q: null });
  }

  function openCreate() {
    setCreateError(null);
    update({ new: '1' });
  }

  function closeCreate() {
    setCreateError(null);
    update({ new: null });
  }

  async function handleCreate(draft: IssueDraft) {
    setCreating(true);
    setCreateError(null);
    try {
      await api.post<Issue>('/api/issues', draft);
      setSearchDraft('');
      update({
        new: null,
        status: null,
        priority: null,
        assignee: null,
        label: null,
        project: null,
        q: null,
      });
      issues.reload();
    } catch (error) {
      setCreateError(error instanceof ApiError ? error.message : 'Could not create the issue.');
    } finally {
      setCreating(false);
    }
  }

  const createInitial = useMemo<Partial<IssueDraft>>(
    () => ({
      status: (params.get('status') as IssueDraft['status']) || 'todo',
      project_id: params.get('project') ? Number(params.get('project')) : undefined,
      sprint_id: params.get('sprint') ? Number(params.get('sprint')) : null,
    }),
    [params],
  );

  return (
    <main className="page stack">
      <div className="page__head">
        <div>
          <p className="eyebrow">Workspace</p>
          <h1 className="page__title">Issues</h1>
          <p className="page__sub">
            {initialLoading ? 'Loading issues…' : `${total} ${total === 1 ? 'issue' : 'issues'}`}
            {hasFilters ? ' match the current filters' : ' in the shared workspace'}
          </p>
        </div>
        <div className="page__actions">
          <button type="button" className="btn btn--primary" onClick={openCreate}>
            New issue
          </button>
        </div>
      </div>

      <section className="card" aria-label="Filters">
        <div className="filters">
          <div className="field">
            <label className="field__label" htmlFor="filter-search">
              Search
            </label>
            <input
              id="filter-search"
              className="input"
              type="search"
              placeholder="Title, description or key"
              value={searchDraft}
              onChange={(event) => setSearchDraft(event.target.value)}
            />
          </div>

          <div className="field">
            <label className="field__label" htmlFor="filter-status">
              Status
            </label>
            <select
              id="filter-status"
              className="select"
              value={status}
              onChange={(event) => update({ status: event.target.value || null })}
            >
              <option value="">All statuses</option>
              {STATUS_ORDER.map((option) => (
                <option value={option} key={option}>
                  {statusLabel(option)}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="filter-priority">
              Priority
            </label>
            <select
              id="filter-priority"
              className="select"
              value={priority}
              onChange={(event) => update({ priority: event.target.value || null })}
            >
              <option value="">All priorities</option>
              {PRIORITY_ORDER.map((option) => (
                <option value={option} key={option}>
                  {priorityLabel(option)}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="filter-assignee">
              Assignee
            </label>
            <select
              id="filter-assignee"
              className="select"
              value={assignee}
              onChange={(event) => update({ assignee: event.target.value || null })}
            >
              <option value="">Anyone</option>
              <option value="unassigned">Unassigned</option>
              {(users.data ?? []).map((user) => (
                <option value={user.id} key={user.id}>
                  {user.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="filter-label">
              Label
            </label>
            <select
              id="filter-label"
              className="select"
              value={label}
              onChange={(event) => update({ label: event.target.value || null })}
            >
              <option value="">Any label</option>
              {(labels.data ?? []).map((entry) => (
                <option value={entry.id} key={entry.id}>
                  {entry.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="filter-project">
              Project
            </label>
            <select
              id="filter-project"
              className="select"
              value={project}
              onChange={(event) => update({ project: event.target.value || null })}
            >
              <option value="">All projects</option>
              {(projects.data ?? []).map((entry) => (
                <option value={entry.id} key={entry.id}>
                  {entry.key}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            className="btn btn--ghost"
            onClick={clearFilters}
            disabled={!hasFilters}
          >
            Clear filters
          </button>
        </div>

        {hasFilters ? (
          <p className="muted" style={{ fontSize: 13, marginTop: 12 }}>
            Active filters — {filterSummary.join(' · ')}
          </p>
        ) : null}
      </section>

      {issues.error ? (
        <ErrorBanner message={issues.error.message} onRetry={issues.reload} />
      ) : null}

      {initialLoading ? (
        <div className="card">
          <SkeletonRows rows={8} />
        </div>
      ) : items.length === 0 ? (
        hasFilters ? (
          <EmptyState
            title="No issues match these filters"
            action={
              <button type="button" className="btn btn--ghost" onClick={clearFilters}>
                Clear filters
              </button>
            }
          >
            {filterSummary.join(' · ')}
          </EmptyState>
        ) : (
          <EmptyState
            title="No issues yet"
            action={
              <button type="button" className="btn btn--primary" onClick={openCreate}>
                Create the first issue
              </button>
            }
          >
            The workspace is empty. Create an issue to populate the list, the board and the roadmap.
          </EmptyState>
        )
      ) : (
        <div className="table-wrap">
          <table className="table">
            <caption className="sr-only">Issues in the shared workspace</caption>
            <thead>
              <tr>
                <th scope="col">Key</th>
                <th scope="col">Title</th>
                <th scope="col">Status</th>
                <th scope="col">Priority</th>
                <th scope="col">Assignee</th>
                <th scope="col">Labels</th>
                <th scope="col">Sprint</th>
              </tr>
            </thead>
            <tbody>
              {items.map((issue) => (
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
                  <td>
                    <span className="cluster" style={{ gap: 6 }}>
                      <Avatar user={issue.assignee} size="sm" />
                      <span className="muted" style={{ fontSize: 13 }}>
                        {issue.assignee ? issue.assignee.name : 'Unassigned'}
                      </span>
                    </span>
                  </td>
                  <td>
                    <LabelChips labels={issue.labels} />
                  </td>
                  <td className="muted" style={{ fontSize: 13 }}>
                    {issue.sprint?.name ?? 'Backlog'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreate ? (
        <div
          className="overlay"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeCreate();
          }}
        >
          <div className="dialog" role="dialog" aria-modal="true" aria-labelledby="create-issue-title">
            <div className="dialog__head">
              <h2 className="dialog__title" id="create-issue-title">
                New issue
              </h2>
              <button type="button" className="icon-btn" onClick={closeCreate} aria-label="Close">
                ✕
              </button>
            </div>
            <div className="dialog__body">
              {projects.data && users.data && labels.data && sprints.data ? (
                <IssueForm
                  initial={createInitial}
                  projects={projects.data}
                  users={users.data}
                  labels={labels.data}
                  sprints={sprints.data}
                  submitLabel="Create issue"
                  busy={creating}
                  serverError={createError}
                  onSubmit={handleCreate}
                  onCancel={closeCreate}
                />
              ) : (
                <SkeletonRows rows={5} />
              )}
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}
