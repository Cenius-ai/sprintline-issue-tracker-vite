import { useEffect, useMemo, useRef, useState, type KeyboardEvent as ReactKeyboardEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import type { IssueList } from '../api/types';
import { useApi } from '../hooks/useApi';
import { statusLabel } from '../lib/format';

interface PaletteItem {
  id: string;
  label: string;
  hint?: string;
  group: string;
  to: string;
}

const NAV_ITEMS: PaletteItem[] = [
  { id: 'nav-overview', label: 'Go to overview', hint: 'Dashboard', group: 'Navigate', to: '/' },
  { id: 'nav-issues', label: 'Browse issues', hint: 'Filterable list', group: 'Navigate', to: '/issues' },
  { id: 'nav-board', label: 'Open sprint board', hint: 'Kanban + burndown', group: 'Navigate', to: '/board' },
  { id: 'nav-roadmap', label: 'View roadmap', hint: 'Now / Next / Later / Done', group: 'Navigate', to: '/roadmap' },
  { id: 'action-new', label: 'New issue', hint: 'Create', group: 'Actions', to: '/issues?new=1' },
];

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const issues = useApi<IssueList>(open ? '/api/issues?limit=100' : null);

  useEffect(() => {
    if (!open) return;
    setQuery('');
    setActiveIndex(0);
    const timer = window.setTimeout(() => inputRef.current?.focus(), 20);
    return () => window.clearTimeout(timer);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  const items = useMemo<PaletteItem[]>(() => {
    const needle = query.trim().toLowerCase();
    const navMatches = NAV_ITEMS.filter((item) => !needle || item.label.toLowerCase().includes(needle));
    const issueItems: PaletteItem[] = (issues.data?.items ?? [])
      .filter((issue) =>
        !needle
          ? true
          : issue.title.toLowerCase().includes(needle) || issue.key.toLowerCase().includes(needle),
      )
      .slice(0, 8)
      .map((issue) => ({
        id: `issue-${issue.id}`,
        label: issue.title,
        hint: `${issue.key} · ${statusLabel(issue.status)}`,
        group: 'Issues',
        to: `/issues/${issue.id}`,
      }));
    return [...navMatches, ...issueItems];
  }, [query, issues.data]);

  useEffect(() => {
    setActiveIndex((current) => (current >= items.length ? 0 : current));
  }, [items.length]);

  if (!open) return null;

  function choose(item: PaletteItem | undefined) {
    if (!item) return;
    navigate(item.to);
    onClose();
  }

  function handleKeyDown(event: ReactKeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActiveIndex((current) => Math.min(current + 1, items.length - 1));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex((current) => Math.max(current - 1, 0));
    } else if (event.key === 'Enter') {
      event.preventDefault();
      choose(items[activeIndex]);
    }
  }

  let lastGroup = '';

  return (
    <div
      className="overlay"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="palette" role="dialog" aria-modal="true" aria-label="Command palette">
        <input
          ref={inputRef}
          className="palette__input"
          type="text"
          value={query}
          placeholder="Search issues or jump to a page…"
          aria-label="Search issues or jump to a page"
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={handleKeyDown}
        />
        <div className="palette__list" role="listbox" aria-label="Results">
          {items.length === 0 ? (
            <p className="muted" style={{ padding: '12px 10px', fontSize: 13 }}>
              No matches. Try an issue key such as SPL-12.
            </p>
          ) : (
            items.map((item, index) => {
              const showGroup = item.group !== lastGroup;
              lastGroup = item.group;
              return (
                <div key={item.id}>
                  {showGroup ? <p className="palette__group">{item.group}</p> : null}
                  <button
                    type="button"
                    className="palette__item"
                    role="option"
                    aria-selected={index === activeIndex}
                    data-active={index === activeIndex}
                    onMouseEnter={() => setActiveIndex(index)}
                    onClick={() => choose(item)}
                  >
                    <span className="truncate">{item.label}</span>
                    {item.hint ? <span className="palette__hint">{item.hint}</span> : null}
                  </button>
                </div>
              );
            })
          )}
        </div>
        <div className="palette__foot">
          <span>↑↓ to move</span>
          <span>↵ to open</span>
          <span>esc to close</span>
        </div>
      </div>
    </div>
  );
}
