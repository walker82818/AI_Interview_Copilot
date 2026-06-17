import type { Resume } from "@/types";
import { formatDate } from "@/utils/format";

interface ResumeCardProps {
  resume: Resume;
  selected?: boolean;
  onSelect?: (id: string) => void;
  onDelete?: (id: string) => void;
}

const statusLabel: Record<Resume["status"], string> = {
  pending: "解析中",
  parsed: "已解析",
  failed: "解析失败",
};

export default function ResumeCard({
  resume,
  selected = false,
  onSelect,
  onDelete,
}: ResumeCardProps) {
  return (
    <div
      className={`rounded-lg border p-4 transition ${
        selected
          ? "border-zinc-900 bg-zinc-50 dark:border-zinc-100 dark:bg-zinc-900"
          : "border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <button
          type="button"
          onClick={() => onSelect?.(resume.id)}
          className="flex-1 text-left"
        >
          <p className="font-medium text-zinc-900 dark:text-zinc-50">
            {resume.fileName}
          </p>
          <p className="mt-1 text-xs text-zinc-400">
            {formatDate(resume.uploadedAt)}
          </p>
        </button>
        <span
          className={`rounded-full px-2 py-0.5 text-xs ${
            resume.status === "parsed"
              ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
              : resume.status === "failed"
                ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
          }`}
        >
          {statusLabel[resume.status]}
        </span>
      </div>
      {onDelete && (
        <button
          type="button"
          onClick={() => onDelete(resume.id)}
          className="mt-3 text-xs text-red-500 hover:text-red-600"
        >
          删除
        </button>
      )}
    </div>
  );
}
