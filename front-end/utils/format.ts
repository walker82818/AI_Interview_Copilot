export function formatDate(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatScore(score: number, maxScore = 100): string {
  return `${Math.round(score)}/${maxScore}`;
}
