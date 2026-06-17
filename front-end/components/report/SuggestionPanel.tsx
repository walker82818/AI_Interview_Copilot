import type { Suggestion } from "@/types";

interface SuggestionPanelProps {
  suggestions: Suggestion[];
}

const priorityStyle: Record<Suggestion["priority"], string> = {
  high: "border-l-red-500 bg-red-50 dark:bg-red-900/10",
  medium: "border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/10",
  low: "border-l-green-500 bg-green-50 dark:bg-green-900/10",
};

const priorityLabel: Record<Suggestion["priority"], string> = {
  high: "高优先",
  medium: "中优先",
  low: "低优先",
};

export default function SuggestionPanel({ suggestions }: SuggestionPanelProps) {
  if (suggestions.length === 0) {
    return (
      <p className="text-sm text-zinc-400">暂无学习建议</p>
    );
  }

  return (
    <div className="space-y-3">
      {suggestions.map((item, i) => (
        <div
          key={i}
          className={`rounded-lg border-l-4 p-4 ${priorityStyle[item.priority]}`}
        >
          <div className="mb-1 flex items-center gap-2">
            <span className="text-xs font-medium text-zinc-500">
              {item.category}
            </span>
            <span className="rounded-full bg-white px-2 py-0.5 text-xs text-zinc-600 dark:bg-zinc-900 dark:text-zinc-400">
              {priorityLabel[item.priority]}
            </span>
          </div>
          <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
            {item.content}
          </p>
        </div>
      ))}
    </div>
  );
}
