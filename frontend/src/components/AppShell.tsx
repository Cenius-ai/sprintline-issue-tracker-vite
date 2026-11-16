import { useEffect, useState, type ReactNode } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext';
import { CommandPalette } from './CommandPalette';
import { Avatar } from './ui';

const NAV = [
  { to: '/', label: 'Overview', end: true },
  { to: '/issues', label: 'Issues', end: false },
  { to: '/board', label: 'Board', end: false },
  { to: '/roadmap', label: 'Roadmap', end: false },
];

function breadcrumbFor(pathname: string): string {
  if (pathname === '/') return 'Overview';
  if (pathname.startsWith('/issues/')) return 'Issue detail';
  if (pathname.startsWith('/issues')) return 'Issues';
  if (pathname.startsWith('/board')) return 'Board';
  if (pathname.startsWith('/roadmap')) return 'Roadmap';
  return 'Sprintline';
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [paletteOpen, setPaletteOpen] = useState(false);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setPaletteOpen((current) => !current);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar__inner">
          <Link className="brand" to="/">
            <span className="brand__glyph" aria-hidden="true">
              ◆
            </span>
            Sprintline
          </Link>
          <span className="crumb" aria-label="Current page">
            {breadcrumbFor(location.pathname)}
          </span>

          <nav className="topbar__nav" aria-label="Primary">
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className="navlink">
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="topbar__actions">
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              onClick={() => setPaletteOpen(true)}
              aria-label="Search issues and pages"
            >
              Search <span className="kbd" aria-hidden="true">⌘K</span>
            </button>
            <span className="who">
              <Avatar user={user} size="sm" />
              <span className="who__name">{user?.name ?? 'Signed in'}</span>
            </span>
            <button type="button" className="btn btn--ghost btn--sm" onClick={logout}>
              Sign out
            </button>
          </div>
        </div>
      </header>

      {children}

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </div>
  );
}
