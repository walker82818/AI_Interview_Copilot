import type { ScoreDimension } from "@/types";

interface RadarChartProps {
  dimensions: ScoreDimension[];
  size?: number;
}

export default function RadarChart({ dimensions, size = 240 }: RadarChartProps) {
  const center = size / 2;
  const radius = size * 0.35;
  const count = dimensions.length;

  if (count === 0) {
    return (
      <div className="flex h-60 items-center justify-center text-sm text-zinc-400">
        暂无评分数据
      </div>
    );
  }

  const angleStep = (2 * Math.PI) / count;

  const getPoint = (index: number, value: number, max: number) => {
    const angle = index * angleStep - Math.PI / 2;
    const r = (value / max) * radius;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  };

  const gridLevels = [0.25, 0.5, 0.75, 1];

  const dataPoints = dimensions
    .map((d, i) => {
      const p = getPoint(i, d.score, d.maxScore);
      return `${p.x},${p.y}`;
    })
    .join(" ");

  return (
    <svg width={size} height={size} className="mx-auto">
      {gridLevels.map((level) => {
        const points = dimensions
          .map((_, i) => {
            const p = getPoint(i, level * 100, 100);
            return `${p.x},${p.y}`;
          })
          .join(" ");
        return (
          <polygon
            key={level}
            points={points}
            fill="none"
            stroke="currentColor"
            strokeOpacity={0.15}
            className="text-zinc-400"
          />
        );
      })}

      {dimensions.map((d, i) => {
        const outer = getPoint(i, 100, 100);
        const label = getPoint(i, 115, 100);
        return (
          <g key={d.name}>
            <line
              x1={center}
              y1={center}
              x2={outer.x}
              y2={outer.y}
              stroke="currentColor"
              strokeOpacity={0.15}
              className="text-zinc-400"
            />
            <text
              x={label.x}
              y={label.y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-zinc-500 text-[10px]"
            >
              {d.name}
            </text>
          </g>
        );
      })}

      <polygon
        points={dataPoints}
        fill="currentColor"
        fillOpacity={0.2}
        stroke="currentColor"
        strokeWidth={2}
        className="text-zinc-900 dark:text-zinc-100"
      />
    </svg>
  );
}
