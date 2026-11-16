import { useState } from 'react';
import { Link } from 'react-router-dom';

import type { Project, Roadmap, RoadmapLaneKey } from '../api/types';
import { RoadmapLane } from '../components/RoadmapLane';
import { ErrorBanner, SkeletonRows } from '../components/ui';
import { useApi, useDocumentTitle } from '../hooks/useApi';
import { pluralize } from '../lib/format';

const LANES: { key: RoadmapLaneKey; title: string; empty: string }[] = [
  { key: 'now', title: 'Now', empty: 'No active-sprint work. Start a sprint to fill this lane.' },
  { key: 'next', title: 'Next', empty: 'Nothing planned yet. Groom the backlog into a planned sprint.' },
  { key: 'later', title: 'Later', empty: 'Backlog is empty — nothing waiting to be groomed.' },
  { key: 'done', title: 'Done', empty: 'No completed issues in this project yet.' },
];

export function Roadmap() {
  useDocumentTitle('Roadmap');
  const projects = useApi<Project[]>('/api/projects');
  const [projectFilter, setProjectFilter] = useState('');
  const roadmap = useApi<Roadmap>(
    projectFilter ? `/api/roadmap?project_id=${projectFilter}` : '/api/roadmap',
  );

  const rows = roadmap.data?.projects ?? [];
  const error = projects.error ?? roadmap.error;
  const loading = roadmap.loading && roadmap.data === null;

  return (
    <main className="page stack">
      <div className="page__head">
        <div>
          <p className="eyebrow">Planning</p>
          <h1 className="page__title">Roadmap</h1>
          <p className="page__sub">
            Every project placed on Now, Next, Later and Done from live sprint and issue state.
          </p>
        </div>
        <div className="page__actions">
          <div className="field" style={{ minWidth: 220 }}>
            <label className="field__label" htmlFor="roadmap-project">
              Project
            </label>
            <select
              id="roadmap-project"
              className="select"
              value={projectFilter}
              onChange={(event) => setProjectFilter(event.target.value)}
            >
              <option value="">All projects</option>
              {(projects.data ?? []).map((project) => (
                <option value={project.id} key={project.id}>
                  {project.key} · {project.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error ? (
        <ErrorBanner
          message={error.message}
          onRetry={() => {
            projects.reload();
            roadmap.reload();
          }}
        />
      ) : null}

      {loading ? (
        <div className="card">
          <SkeletonRows rows={6} />
        </div>
      ) : rows.length === 0 ? (
        <div className="empty">
          <p className="empty__title">Nothing on the roadmap yet</p>
          <p className="empty__text">
            Create a project with issues and they will appear here, grouped by sprint state.
          </p>
          <Link className="btn btn--primary" to="/issues?new=1">
            New issue
          </Link>
        </div>
      ) : (
        <div className="roadmap">
          {rows.map((row) => {
            const total = Object.values(row.counts).reduce((sum, count) => sum + count, 0);
            return (
              <section className="card" key={row.project.id} aria-labelledby={`project-${row.project.id}`}>
                <div className="roadmap__head">
                  <span
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: 3,
                      background: row.project.color,
                      flex: 'none',
                    }}
                    aria-hidden="true"
                  />
                  <h2 className="card__title" id={`project-${row.project.id}`}>
                    {row.project.key} · {row.project.name}
                  </h2>
                  <span className="card__meta">
                    {total} {pluralize(total, 'issue')}
                  </span>
                </div>
                <p className="muted" style={{ fontSize: 13, marginTop: 4 }}>
                  {row.project.description}
                </p>

                <div className="roadmap__lanes" style={{ marginTop: 12 }}>
                  {LANES.map((lane) => (
                    <RoadmapLane
                      key={lane.key}
                      title={lane.title}
                      count={row.counts[lane.key]}
                      cards={row.lanes[lane.key]}
                      emptyText={lane.empty}
                    />
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </main>
  );
}
