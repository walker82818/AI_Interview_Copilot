import type { ScoreDimension } from "@/types";
import { formatScore } from "@/utils/format";

interface ScoreCardProps {
  overallScore: number;
  dimensions: ScoreDimension[];
}

export default function ScoreCard({ overallScore, dimensions }: ScoreCardProps) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="mb-6 text-center">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">综合评分</p>
        <p className="text-5xl font-bold text-zinc-900 dark:text-zinc-50">
          {Math.round(overallScore)}
        </p>
      </div>

      <div className="space-y-4">
        {dimensions.map((dim) => {
          const percent = (dim.score / dim.maxScore) * 100;
          return (
            <div key={dim.name}>
              <div className="mb-1 flex justify-between text-sm">
                <span className="text-zinc-700 dark:text-zinc-300">{dim.name}</span>
                <span className="text-zinc-500">{formatScore(dim.score, dim.maxScore)}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                <div
                  className="h-full rounded-full bg-zinc-900 transition-all dark:bg-zinc-100"
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
