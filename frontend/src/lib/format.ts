import type { IssuePriority, IssueStatus } from '../api/types';

const STATUS_LABELS: Record<IssueStatus, string> = {
  backlog: 'Backlog',
  todo: 'Todo',
  in_progress: 'In progress',
  in_review: 'In review',
  done: 'Done',
};

const PRIORITY_LABELS: Record<IssuePriority, string> = {
  urgent: 'Urgent',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  none: 'No priority',
};

export const STATUS_ORDER: IssueStatus[] = ['backlog', 'todo', 'in_progress', 'in_review', 'done'];
export const PRIORITY_ORDER: IssuePriority[] = ['urgent', 'high', 'medium', 'low', 'none'];

export function statusLabel(status: string | null | undefined): string {
  if (!status) return 'None';
  return STATUS_LABELS[status as IssueStatus] ?? status;
}

export function priorityLabel(priority: string | null | undefined): string {
  if (!priority) return 'No priority';
  return PRIORITY_LABELS[priority as IssuePriority] ?? priority;
}

/** Parse an API timestamp; the backend sends UTC ISO strings. */
export function parseApiDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const normalized = /[zZ]|[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

const DATE_FORMAT = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
});
const DAY_FORMAT = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short' });

export function formatDate(value: string | null | undefined): string {
  const date = parseApiDate(value);
  return date ? DATE_FORMAT.format(date) : '—';
}

export function formatShortDate(value: string | null | undefined): string {
  const date = parseApiDate(value);
  return date ? DAY_FORMAT.format(date) : '—';
}

/** Format a date-only string ("2026-11-11") without a timezone shift. */
export function formatDateOnly(value: string | null | undefined): string {
  if (!value) return '—';
  const parts = value.slice(0, 10).split('-').map(Number);
  if (parts.length !== 3 || parts.some((part) => Number.isNaN(part))) return '—';
  const [year, month, day] = parts;
  return DAY_FORMAT.format(new Date(year, month - 1, day));
}

export function formatDateOnlyLong(value: string | null | undefined): string {
  if (!value) return '—';
  const parts = value.slice(0, 10).split('-').map(Number);
  if (parts.length !== 3 || parts.some((part) => Number.isNaN(part))) return '—';
  const [year, month, day] = parts;
  return DATE_FORMAT.format(new Date(year, month - 1, day));
}

export function relativeTime(value: string | null | undefined): string {
  const date = parseApiDate(value);
  if (!date) return '—';
  const deltaMs = Date.now() - date.getTime();
  if (!Number.isFinite(deltaMs) || deltaMs < 45_000) return 'just now';
  const minutes = Math.round(deltaMs / 60_000);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(deltaMs / 3_600_000);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.round(deltaMs / 86_400_000);
  if (days === 1) return 'yesterday';
  if (days < 7) return `${days} d ago`;
  return formatDate(value);
}

export function initials(name: string): string {
  const parts = name
    .replace(/\(.*?\)/g, '')
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export function pluralize(count: number, singular: string, plural?: string): string {
  return count === 1 ? singular : (plural ?? `${singular}s`);
}

export function greeting(date = new Date()): string {
  const hour = date.getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

/** Days between two ISO date-only strings, inclusive. */
export function daySpan(start: string, end: string): number {
  const startDate = parseApiDate(`${start.slice(0, 10)}T00:00:00Z`);
  const endDate = parseApiDate(`${end.slice(0, 10)}T00:00:00Z`);
  if (!startDate || !endDate) return 0;
  return Math.max(Math.round((endDate.getTime() - startDate.getTime()) / 86_400_000) + 1, 1);
}

export function sprintProgress(start: string, end: string): { day: number; total: number } {
  const total = daySpan(start, end);
  const startDate = parseApiDate(`${start.slice(0, 10)}T00:00:00Z`);
  if (!startDate) return { day: 1, total };
  const elapsed = Math.floor((Date.now() - startDate.getTime()) / 86_400_000) + 1;
  return { day: Math.min(Math.max(elapsed, 1), total), total };
}
