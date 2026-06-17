import type { ResumeAnalysis } from "@/types";

interface ResumeAnalysisProps {
  analysis: ResumeAnalysis;
}

export default function ResumeAnalysisView({ analysis }: ResumeAnalysisProps) {
  return (
    <div className="space-y-6">
      <section>
        <h3 className="mb-2 text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          摘要
        </h3>
        <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          {analysis.summary}
        </p>
      </section>

      <section>
        <h3 className="mb-2 text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          技能
        </h3>
        <div className="flex flex-wrap gap-2">
          {analysis.skills.map((skill) => (
            <span
              key={skill}
              className="rounded-full bg-blue-100 px-3 py-1 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
            >
              {skill}
            </span>
          ))}
        </div>
      </section>

      <section>
        <h3 className="mb-2 text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          工作经历
        </h3>
        <ul className="space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
          {analysis.experience.map((item, i) => (
            <li key={i}>• {item}</li>
          ))}
        </ul>
      </section>

      <section>
        <h3 className="mb-2 text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          学历
        </h3>
        <ul className="space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
          {analysis.education.map((item, i) => (
            <li key={i}>• {item}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
