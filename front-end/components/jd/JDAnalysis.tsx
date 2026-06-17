import type { JDAnalysis } from "@/types";

interface JDAnalysisProps {
  analysis: JDAnalysis;
}

export default function JDAnalysisView({ analysis }: JDAnalysisProps) {
  return (
    <div className="space-y-6">
      {analysis.matchScore !== undefined && (
        <div className="rounded-lg bg-zinc-50 p-4 dark:bg-zinc-900">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">简历匹配度</p>
          <p className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
            {Math.round(analysis.matchScore)}%
          </p>
        </div>
      )}

      <section>
        <h3 className="mb-2 text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          必备技能
        </h3>
        <div className="flex flex-wrap gap-2">
          {analysis.requiredSkills.map((skill) => (
            <span
              key={skill}
              className="rounded-full bg-red-100 px-3 py-1 text-xs text-red-700 dark:bg-red-900/30 dark:text-red-400"
            >
              {skill}
            </span>
          ))}
        </div>
      </section>

      <section>
        <h3 className="mb-2 text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          加分技能
        </h3>
        <div className="flex flex-wrap gap-2">
          {analysis.preferredSkills.map((skill) => (
            <span
              key={skill}
              className="rounded-full bg-green-100 px-3 py-1 text-xs text-green-700 dark:bg-green-900/30 dark:text-green-400"
            >
              {skill}
            </span>
          ))}
        </div>
      </section>

      <section>
        <h3 className="mb-2 text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          职责描述
        </h3>
        <ul className="space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
          {analysis.responsibilities.map((item, i) => (
            <li key={i}>• {item}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
