import { Link } from 'react-router-dom';

import type { RoadmapCard } from '../api/types';
import { Avatar, PriorityBadge } from './ui';

export function RoadmapLane({
  title,
  count,
  cards,
  emptyText,
}: {
  title: string;
  count: number;
  cards: RoadmapCard[];
  emptyText: string;
}) {
  return (
    <section className="lane" aria-label={`${title} lane`}>
      <header className="lane__head">
        <h4 className="lane__title">{title}</h4>
        <span className="column__count">{count}</span>
      </header>
      {cards.length === 0 ? (
        <p className="lane__empty">{emptyText}</p>
      ) : (
        <div className="lane__body">
          {cards.map((card) => (
            <article className="lane-card" key={card.id}>
              <div className="cluster" style={{ justifyContent: 'space-between' }}>
                <span className="issue-card__key">{card.key}</span>
                <PriorityBadge priority={card.priority} showLabel={false} />
              </div>
              <Link className="lane-card__title" to={`/issues/${card.id}`}>
                {card.title}
              </Link>
              <div className="cluster" style={{ justifyContent: 'space-between' }}>
                <Avatar user={card.assignee} size="sm" />
                <span className="muted" style={{ fontSize: 11 }}>
                  {card.estimate ? `${card.estimate} pts` : 'No estimate'}
                </span>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
