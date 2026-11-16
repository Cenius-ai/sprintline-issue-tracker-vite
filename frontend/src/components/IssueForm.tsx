import { useMemo, useRef, useState, type FormEvent } from 'react';

import type { IssuePriority, IssueStatus, Label, Project, Sprint, User } from '../api/types';
import { PRIORITY_ORDER, STATUS_ORDER, priorityLabel, statusLabel } from '../lib/format';
import { ErrorBanner } from './ui';

export interface IssueDraft {
  title: string;
  description: string;
  status: IssueStatus;
  priority: IssuePriority;
  project_id: number;
  sprint_id: number | null;
  assignee_id: number | null;
  estimate: number;
  label_ids: number[];
}

interface IssueFormProps {
  initial?: Partial<IssueDraft>;
  projects: Project[];
  users: User[];
  labels: Label[];
  sprints: Sprint[];
  submitLabel: string;
  busy: boolean;
  serverError?: string | null;
  onSubmit: (draft: IssueDraft) => void;
  onCancel: () => void;
}

export function IssueForm({
  initial,
  projects,
  users,
  labels,
  sprints,
  submitLabel,
  busy,
  serverError,
  onSubmit,
  onCancel,
}: IssueFormProps) {
  const [title, setTitle] = useState(initial?.title ?? '');
  const [description, setDescription] = useState(initial?.description ?? '');
  const [status, setStatus] = useState<IssueStatus>(initial?.status ?? 'todo');
  const [priority, setPriority] = useState<IssuePriority>(initial?.priority ?? 'medium');
  // The reference lists load asynchronously; keep an explicit selection but fall
  // back to the first project so the form is always submittable.
  const [selectedProjectId, setSelectedProjectId] = useState<number>(initial?.project_id ?? 0);
  const projectId = selectedProjectId || projects[0]?.id || 0;
  const [sprintId, setSprintId] = useState<number | null>(initial?.sprint_id ?? null);
  const [assigneeId, setAssigneeId] = useState<number | null>(initial?.assignee_id ?? null);
  const [estimate, setEstimate] = useState<string>(String(initial?.estimate ?? 3));
  const [labelIds, setLabelIds] = useState<number[]>(initial?.label_ids ?? []);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const titleRef = useRef<HTMLInputElement>(null);

  const projectSprints = useMemo(
    () => sprints.filter((sprint) => sprint.project_id === projectId),
    [sprints, projectId],
  );

  function handleProjectChange(nextProjectId: number) {
    setSelectedProjectId(nextProjectId);
    const sprintStillValid = sprints.some(
      (sprint) => sprint.id === sprintId && sprint.project_id === nextProjectId,
    );
    if (!sprintStillValid) {
      setSprintId(null);
    }
  }

  function toggleLabel(labelId: number) {
    setLabelIds((current) =>
      current.includes(labelId) ? current.filter((id) => id !== labelId) : [...current, labelId],
    );
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const errors: Record<string, string> = {};
    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      errors.title = 'Title is required.';
    } else if (trimmedTitle.length > 200) {
      errors.title = 'Keep the title under 200 characters.';
    }
    if (!projectId) {
      errors.project_id = 'Choose a project.';
    }
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      titleRef.current?.focus();
      return;
    }
    const parsedEstimate = Number(estimate);
    onSubmit({
      title: trimmedTitle,
      description: description.trim(),
      status,
      priority,
      project_id: projectId,
      sprint_id: sprintId,
      assignee_id: assigneeId,
      estimate: Number.isFinite(parsedEstimate) ? Math.min(Math.max(Math.round(parsedEstimate), 0), 100) : 0,
      label_ids: labelIds,
    });
  }

  return (
    <form className="stack" onSubmit={handleSubmit} noValidate>
      {serverError ? <ErrorBanner message={serverError} /> : null}

      <div className="field">
        <label className="field__label" htmlFor="issue-title">
          Title
        </label>
        <input
          id="issue-title"
          ref={titleRef}
          className="input"
          value={title}
          autoComplete="off"
          aria-invalid={Boolean(fieldErrors.title)}
          aria-describedby={fieldErrors.title ? 'issue-title-error' : undefined}
          onChange={(event) => setTitle(event.target.value)}
        />
        {fieldErrors.title ? (
          <span className="field__error" id="issue-title-error" role="alert">
            {fieldErrors.title}
          </span>
        ) : (
          <span className="field__hint">Short and specific — it shows up on the board card.</span>
        )}
      </div>

      <div className="field">
        <label className="field__label" htmlFor="issue-description">
          Description
        </label>
        <textarea
          id="issue-description"
          className="textarea"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
      </div>

      <div className="field-grid">
        <div className="field">
          <label className="field__label" htmlFor="issue-project">
            Project
          </label>
          <select
            id="issue-project"
            className="select"
            value={projectId}
            aria-invalid={Boolean(fieldErrors.project_id)}
            aria-describedby={fieldErrors.project_id ? 'issue-project-error' : undefined}
            onChange={(event) => handleProjectChange(Number(event.target.value))}
          >
            {projects.length === 0 ? <option value={0}>Loading projects…</option> : null}
            {projects.map((project) => (
              <option value={project.id} key={project.id}>
                {project.key} · {project.name}
              </option>
            ))}
          </select>
          {fieldErrors.project_id ? (
            <span className="field__error" id="issue-project-error" role="alert">
              {fieldErrors.project_id}
            </span>
          ) : null}
        </div>

        <div className="field">
          <label className="field__label" htmlFor="issue-sprint">
            Sprint
          </label>
          <select
            id="issue-sprint"
            className="select"
            value={sprintId ?? ''}
            onChange={(event) => setSprintId(event.target.value ? Number(event.target.value) : null)}
          >
            <option value="">Backlog (no sprint)</option>
            {projectSprints.map((sprint) => (
              <option value={sprint.id} key={sprint.id}>
                {sprint.name}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label className="field__label" htmlFor="issue-status">
            Status
          </label>
          <select
            id="issue-status"
            className="select"
            value={status}
            onChange={(event) => setStatus(event.target.value as IssueStatus)}
          >
            {STATUS_ORDER.map((option) => (
              <option value={option} key={option}>
                {statusLabel(option)}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label className="field__label" htmlFor="issue-priority">
            Priority
          </label>
          <select
            id="issue-priority"
            className="select"
            value={priority}
            onChange={(event) => setPriority(event.target.value as IssuePriority)}
          >
            {PRIORITY_ORDER.map((option) => (
              <option value={option} key={option}>
                {priorityLabel(option)}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label className="field__label" htmlFor="issue-assignee">
            Assignee
          </label>
          <select
            id="issue-assignee"
            className="select"
            value={assigneeId ?? ''}
            onChange={(event) => setAssigneeId(event.target.value ? Number(event.target.value) : null)}
          >
            <option value="">Unassigned</option>
            {users.map((user) => (
              <option value={user.id} key={user.id}>
                {user.name}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label className="field__label" htmlFor="issue-estimate">
            Estimate (points)
          </label>
          <input
            id="issue-estimate"
            className="input"
            type="number"
            inputMode="numeric"
            min={0}
            max={100}
            step={1}
            value={estimate}
            onChange={(event) => setEstimate(event.target.value)}
          />
        </div>
      </div>

      <fieldset className="field" style={{ border: 0, margin: 0, padding: 0 }}>
        <legend className="field__label" style={{ padding: 0, marginBottom: 6 }}>
          Labels
        </legend>
        <div className="checkbox-grid">
          {labels.map((label) => (
            <label className="checkbox" key={label.id}>
              <input
                type="checkbox"
                checked={labelIds.includes(label.id)}
                onChange={() => toggleLabel(label.id)}
              />
              <span className="chip__dot" style={{ background: label.color }} aria-hidden="true" />
              {label.name}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="dialog__foot" style={{ margin: '0 -20px -20px', paddingTop: 16 }}>
        <button type="button" className="btn btn--ghost" onClick={onCancel} disabled={busy}>
          Cancel
        </button>
        <button type="submit" className="btn btn--primary" disabled={busy}>
          {busy ? 'Saving…' : submitLabel}
        </button>
      </div>
    </form>
  );
}
