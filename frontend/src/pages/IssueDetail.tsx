import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { api, ApiError } from '../api/client';
import type { ActivityList, Comment, Issue, IssuePriority, IssueStatus, Label, Project, Sprint, User } from '../api/types';
import { ActivityFeed } from '../components/ActivityFeed';
import { CommentList } from '../components/CommentList';
import { IssueForm, type IssueDraft } from '../components/IssueForm';
import { Avatar, ErrorBanner, LabelChips, PriorityBadge, SkeletonRows, StatusPill } from '../components/ui';
import { useApi, useDocumentTitle } from '../hooks/useApi';
import { PRIORITY_ORDER, STATUS_ORDER, formatDate, priorityLabel, relativeTime, statusLabel } from '../lib/format';

type Tab = 'comments' | 'activity';

export function IssueDetail() {
  useDocumentTitle('Issue');
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const issue = useApi<Issue>(id ? `/api/issues/${id}` : null);
  const comments = useApi<Comment[]>(id ? `/api/issues/${id}/comments` : null);
  const activity = useApi<ActivityList>(id ? `/api/issues/${id}/activity` : null);
  const users = useApi<User[]>('/api/users');
  const labels = useApi<Label[]>('/api/labels');
  const projects = useApi<Project[]>('/api/projects');
  const sprints = useApi<Sprint[]>('/api/sprints');

  const [tab, setTab] = useState<Tab>('comments');
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [commentDraft, setCommentDraft] = useState('');
  const [posting, setPosting] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const issueData = issue.data;

  async function patchIssue(patch: Record<string, unknown>) {
    if (!issueData) return;
    setSaving(true);
    setActionError(null);
    try {
      await api.patch<Issue>(`/api/issues/${issueData.id}`, patch);
      issue.reload();
      activity.reload();
    } catch (error) {
      setActionError(error instanceof ApiError ? error.message : 'Could not save the change.');
    } finally {
      setSaving(false);
    }
  }

  async function handleEdit(draft: IssueDraft) {
    if (!issueData) return;
    await patchIssue({
      title: draft.title,
      description: draft.description,
      status: draft.status,
      priority: draft.priority,
      sprint_id: draft.sprint_id,
      assignee_id: draft.assignee_id,
      estimate: draft.estimate,
      label_ids: draft.label_ids,
    });
    setEditOpen(false);
  }

  async function handleComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!issueData) return;
    const body = commentDraft.trim();
    if (!body) return;
    setPosting(true);
    setActionError(null);
    try {
      await api.post<Comment>(`/api/issues/${issueData.id}/comments`, { body });
      setCommentDraft('');
      comments.reload();
      activity.reload();
      issue.reload();
      setTab('comments');
    } catch (error) {
      setActionError(error instanceof ApiError ? error.message : 'Could not post the comment.');
    } finally {
      setPosting(false);
    }
  }

  async function handleDelete() {
    if (!issueData) return;
    setDeleting(true);
    try {
      await api.del(`/api/issues/${issueData.id}`);
      navigate('/issues', { replace: true });
    } catch (error) {
      setActionError(error instanceof ApiError ? error.message : 'Could not delete the issue.');
      setDeleting(false);
      setConfirmOpen(false);
    }
  }

  if (issue.error?.status === 404) {
    return (
      <main className="page stack">
        <div className="card">
          <div className="empty">
            <p className="empty__title">Issue not found</p>
            <p className="empty__text">
              There is no issue with id {id} in this workspace. It may have been deleted.
            </p>
            <Link className="btn btn--ghost" to="/issues">
              Back to issues
            </Link>
          </div>
        </div>
      </main>
    );
  }

  if (issue.error) {
    return (
      <main className="page stack">
        <ErrorBanner message={issue.error.message} onRetry={issue.reload} />
        <Link className="btn btn--ghost" to="/issues" style={{ justifySelf: 'start' }}>
          Back to issues
        </Link>
      </main>
    );
  }

  if (!issueData) {
    return (
      <main className="page stack">
        <div className="skeleton" style={{ height: 32, width: '40%' }} aria-hidden="true" />
        <div className="card">
          <SkeletonRows rows={6} />
        </div>
      </main>
    );
  }

  const editInitial: IssueDraft = {
    title: issueData.title,
    description: issueData.description,
    status: issueData.status,
    priority: issueData.priority,
    project_id: issueData.project.id,
    sprint_id: issueData.sprint?.id ?? null,
    assignee_id: issueData.assignee?.id ?? null,
    estimate: issueData.estimate,
    label_ids: issueData.labels.map((label) => label.id),
  };

  const commentItems = comments.data ?? [];
  const activityItems = activity.data?.items ?? [];

  return (
    <main className="page stack">
      <div className="page__head">
        <div>
          <p className="eyebrow">
            <Link to="/issues">Issues</Link> / {issueData.key} / {issueData.project.key}
          </p>
          <h1 className="detail__title">{issueData.title}</h1>
          <div className="cluster" style={{ marginTop: 8 }}>
            <StatusPill status={issueData.status} />
            <PriorityBadge priority={issueData.priority} />
            <Avatar user={issueData.assignee} size="sm" />
            <span className="muted" style={{ fontSize: 13 }}>
              {issueData.assignee ? issueData.assignee.name : 'Unassigned'}
            </span>
            <span className="muted" style={{ fontSize: 13 }}>
              · {issueData.sprint?.name ?? 'Backlog'}
            </span>
          </div>
        </div>
        <div className="page__actions">
          <Link className="btn btn--ghost" to="/issues">
            Back
          </Link>
          <button type="button" className="btn" onClick={() => setEditOpen(true)} disabled={saving}>
            Edit
          </button>
          <button type="button" className="btn btn--danger" onClick={() => setConfirmOpen(true)}>
            Delete
          </button>
        </div>
      </div>

      {actionError ? <ErrorBanner message={actionError} /> : null}

      <div className="detail">
        <div className="stack">
          <section className="card" aria-labelledby="description-heading">
            <div className="card__head">
              <h2 className="card__title" id="description-heading">
                Description
              </h2>
              <span className="card__meta">Updated {relativeTime(issueData.updated_at)}</span>
            </div>
            <p className="detail__desc">
              {issueData.description ? issueData.description : 'No description yet. Use Edit to add one.'}
            </p>
          </section>

          <section className="card" aria-labelledby="fields-heading">
            <div className="card__head">
              <h2 className="card__title" id="fields-heading">
                Fields
              </h2>
              <span className="card__meta">{saving ? 'Saving…' : 'Changes save immediately'}</span>
            </div>
            <div className="meta-list">
              <div className="meta-list__row">
                <span className="meta-list__label">
                  <label htmlFor="detail-status">Status</label>
                </span>
                <select
                  id="detail-status"
                  className="select"
                  value={issueData.status}
                  disabled={saving}
                  onChange={(event) => void patchIssue({ status: event.target.value as IssueStatus })}
                >
                  {STATUS_ORDER.map((option) => (
                    <option value={option} key={option}>
                      {statusLabel(option)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="meta-list__row">
                <span className="meta-list__label">
                  <label htmlFor="detail-priority">Priority</label>
                </span>
                <select
                  id="detail-priority"
                  className="select"
                  value={issueData.priority}
                  disabled={saving}
                  onChange={(event) => void patchIssue({ priority: event.target.value as IssuePriority })}
                >
                  {PRIORITY_ORDER.map((option) => (
                    <option value={option} key={option}>
                      {priorityLabel(option)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="meta-list__row">
                <span className="meta-list__label">
                  <label htmlFor="detail-assignee">Assignee</label>
                </span>
                <select
                  id="detail-assignee"
                  className="select"
                  value={issueData.assignee?.id ?? ''}
                  disabled={saving}
                  onChange={(event) =>
                    void patchIssue({ assignee_id: event.target.value ? Number(event.target.value) : null })
                  }
                >
                  <option value="">Unassigned</option>
                  {(users.data ?? []).map((user) => (
                    <option value={user.id} key={user.id}>
                      {user.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="meta-list__row">
                <span className="meta-list__label">Labels</span>
                <LabelChips labels={issueData.labels} emptyText="No labels" />
              </div>

              <div className="meta-list__row">
                <span className="meta-list__label">Sprint</span>
                <span>{issueData.sprint?.name ?? 'Backlog'}</span>
              </div>

              <div className="meta-list__row">
                <span className="meta-list__label">Estimate</span>
                <span>{issueData.estimate ? `${issueData.estimate} points` : 'No estimate'}</span>
              </div>

              <div className="meta-list__row">
                <span className="meta-list__label">Created</span>
                <span>
                  {formatDate(issueData.created_at)} · {issueData.created_by?.name ?? 'Unknown'}
                </span>
              </div>

              {issueData.completed_at ? (
                <div className="meta-list__row">
                  <span className="meta-list__label">Completed</span>
                  <span>{formatDate(issueData.completed_at)}</span>
                </div>
              ) : null}
            </div>
          </section>
        </div>

        <section className="card" aria-label="Conversation and history">
          <div className="tabs" role="tablist" aria-label="Issue timeline">
            <button
              type="button"
              className="tab"
              role="tab"
              id="tab-comments"
              aria-selected={tab === 'comments'}
              aria-controls="panel-comments"
              onClick={() => setTab('comments')}
            >
              Comments ({commentItems.length})
            </button>
            <button
              type="button"
              className="tab"
              role="tab"
              id="tab-activity"
              aria-selected={tab === 'activity'}
              aria-controls="panel-activity"
              onClick={() => setTab('activity')}
            >
              Activity ({activityItems.length})
            </button>
          </div>

          {tab === 'comments' ? (
            <div id="panel-comments" role="tabpanel" aria-labelledby="tab-comments" className="stack">
              {comments.loading && comments.data === null ? (
                <SkeletonRows rows={3} />
              ) : (
                <CommentList comments={commentItems} />
              )}

              <form className="stack" onSubmit={handleComment}>
                <div className="field">
                  <label className="field__label" htmlFor="comment-body">
                    Add a comment
                  </label>
                  <textarea
                    id="comment-body"
                    className="textarea"
                    value={commentDraft}
                    placeholder="Share an update, a decision or a blocker…"
                    onChange={(event) => setCommentDraft(event.target.value)}
                  />
                  <span className="field__hint">Plain text. Comments cannot be edited once posted.</span>
                </div>
                <div className="cluster" style={{ justifyContent: 'flex-end' }}>
                  <button
                    type="submit"
                    className="btn btn--primary"
                    disabled={posting || commentDraft.trim().length === 0}
                  >
                    {posting ? 'Posting…' : 'Post comment'}
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div id="panel-activity" role="tabpanel" aria-labelledby="tab-activity">
              {activity.loading && activity.data === null ? (
                <SkeletonRows rows={3} />
              ) : (
                <ActivityFeed events={activityItems} />
              )}
            </div>
          )}
        </section>
      </div>

      {editOpen ? (
        <div
          className="overlay"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setEditOpen(false);
          }}
        >
          <div className="dialog" role="dialog" aria-modal="true" aria-labelledby="edit-issue-title">
            <div className="dialog__head">
              <h2 className="dialog__title" id="edit-issue-title">
                Edit {issueData.key}
              </h2>
              <button type="button" className="icon-btn" onClick={() => setEditOpen(false)} aria-label="Close">
                ✕
              </button>
            </div>
            <div className="dialog__body">
              {projects.data && users.data && labels.data && sprints.data ? (
                <IssueForm
                  initial={editInitial}
                  projects={projects.data}
                  users={users.data}
                  labels={labels.data}
                  sprints={sprints.data}
                  submitLabel="Save changes"
                  busy={saving}
                  serverError={actionError}
                  onSubmit={handleEdit}
                  onCancel={() => setEditOpen(false)}
                />
              ) : (
                <SkeletonRows rows={5} />
              )}
            </div>
          </div>
        </div>
      ) : null}

      {confirmOpen ? (
        <div
          className="overlay"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setConfirmOpen(false);
          }}
        >
          <div
            className="dialog dialog--sm"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="confirm-delete-title"
            aria-describedby="confirm-delete-text"
          >
            <div className="dialog__head">
              <h2 className="dialog__title" id="confirm-delete-title">
                Delete {issueData.key}?
              </h2>
            </div>
            <div className="dialog__body">
              <p id="confirm-delete-text" className="muted">
                This removes the issue, its {commentItems.length} comments and its activity history. It
                cannot be undone.
              </p>
            </div>
            <div className="dialog__foot">
              <button
                type="button"
                className="btn btn--ghost"
                onClick={() => setConfirmOpen(false)}
                disabled={deleting}
              >
                Cancel
              </button>
              <button type="button" className="btn btn--danger" onClick={() => void handleDelete()} disabled={deleting}>
                {deleting ? 'Deleting…' : 'Delete issue'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}
