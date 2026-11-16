import type { Burndown } from '../api/types';
import { formatDateOnly, statusLabel } from '../lib/format';

const WIDTH = 640;
const HEIGHT = 220;
const PADDING = { top: 14, right: 14, bottom: 28, left: 36 };

export function BurndownChart({ data }: { data: Burndown }) {
  const points = data.points;
  const innerWidth = WIDTH - PADDING.left - PADDING.right;
  const innerHeight = HEIGHT - PADDING.top - PADDING.bottom;
  const maxValue = Math.max(data.total_points, ...points.map((point) => Math.max(point.ideal, point.actual)), 1);
  const stepX = points.length > 1 ? innerWidth / (points.length - 1) : 0;
  const x = (index: number) => PADDING.left + index * stepX;
  const y = (value: number) => PADDING.top + innerHeight - (value / maxValue) * innerHeight;
  const path = (key: 'ideal' | 'actual') =>
    points
      .map((point, index) => `${index === 0 ? 'M' : 'L'}${x(index).toFixed(1)},${y(point[key]).toFixed(1)}`)
      .join(' ');

  const ticks = [1, 0.75, 0.5, 0.25, 0].map((fraction) => Math.round(maxValue * fraction));
  const remaining = points.length > 0 ? points[points.length - 1].actual : data.total_points;
  const labelIndexes = Array.from(new Set([0, Math.floor((points.length - 1) / 2), points.length - 1])).filter(
    (index) => index >= 0 && index < points.length,
  );

  if (points.length === 0) {
    return <p className="muted">This sprint has no date range to chart yet.</p>;
  }

  return (
    <div className="chart">
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={`Burndown for ${data.sprint_name}: ${data.total_points} points total, ${remaining} remaining`}
      >
        {ticks.map((tick) => (
          <g key={tick}>
            <line
              x1={PADDING.left}
              x2={WIDTH - PADDING.right}
              y1={y(tick)}
              y2={y(tick)}
              stroke="#2d2d34"
              strokeWidth="1"
            />
            <text x={PADDING.left - 8} y={y(tick) + 4} textAnchor="end" fontSize="11" fill="#9d9da6">
              {tick}
            </text>
          </g>
        ))}

        <path d={path('ideal')} fill="none" stroke="#7e7e8a" strokeWidth="2" strokeDasharray="5 4" />
        <path d={path('actual')} fill="none" stroke="#9884f3" strokeWidth="2.5" strokeLinejoin="round" />

        {points.map((point, index) => (
          <circle key={point.date} cx={x(index)} cy={y(point.actual)} r={index === points.length - 1 ? 4 : 2.5} fill="#9884f3">
            <title>
              {formatDateOnly(point.date)}: {point.actual} remaining (ideal {point.ideal})
            </title>
          </circle>
        ))}

        {labelIndexes.map((index) => (
          <text
            key={points[index].date}
            x={x(index)}
            y={HEIGHT - 8}
            textAnchor={index === 0 ? 'start' : index === points.length - 1 ? 'end' : 'middle'}
            fontSize="11"
            fill="#9d9da6"
          >
            {formatDateOnly(points[index].date)}
          </text>
        ))}
      </svg>

      <div className="chart__legend">
        <span className="chart__legend-item">
          <span className="chart__swatch" aria-hidden="true" /> Actual remaining
        </span>
        <span className="chart__legend-item">
          <span className="chart__swatch chart__swatch--ideal" aria-hidden="true" /> Ideal burn
        </span>
      </div>

      <div className="chart__summary">
        <span>
          Total <strong>{data.total_points} pts</strong>
        </span>
        <span>
          Completed <strong>{data.completed_points} pts</strong>
        </span>
        <span>
          Remaining <strong>{remaining} pts</strong>
        </span>
        <span>
          {data.days} days · {statusLabel(data.sprint_status)}
        </span>
      </div>
    </div>
  );
}
