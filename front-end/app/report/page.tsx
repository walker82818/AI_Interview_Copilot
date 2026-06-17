"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import AuthGuard from "@/components/auth/AuthGuard";
import AppShell from "@/components/common/AppShell";
import Loading from "@/components/common/Loading";
import ScoreCard from "@/components/report/ScoreCard";
import RadarChart from "@/components/report/RadarChart";
import SuggestionPanel from "@/components/report/SuggestionPanel";
import type { InterviewReport } from "@/types";
import * as reportService from "@/services/report";

function ReportContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("sessionId");
  const [report, setReport] = useState<InterviewReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    setIsLoading(true);
    reportService
      .getReport(sessionId)
      .then(setReport)
      .catch(async () => {
        try {
          const generated = await reportService.generateReport(sessionId);
          setReport(generated);
        } catch (err) {
          setError(err instanceof Error ? err.message : "加载报告失败");
        }
      })
      .finally(() => setIsLoading(false));
  }, [sessionId]);

  if (!sessionId) {
    return (
      <p className="text-sm text-zinc-400">
        请从面试页面结束面试后查看报告，或在 URL 中提供 sessionId 参数。
      </p>
    );
  }

  if (isLoading) {
    return <Loading label="生成报告中..." />;
  }

  if (error) {
    return <p className="text-sm text-red-500">{error}</p>;
  }

  if (!report) {
    return <p className="text-sm text-zinc-400">找不到报告</p>;
  }

  return (
    <div className="space-y-6">
      <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
        {report.summary}
      </p>

      <div className="grid gap-6 lg:grid-cols-2">
        <ScoreCard
          overallScore={report.overallScore}
          dimensions={report.dimensions}
        />
        <div className="flex items-center justify-center rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
          <RadarChart dimensions={report.dimensions} />
        </div>
      </div>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="mb-4 text-lg font-medium text-zinc-900 dark:text-zinc-50">
          学习建议
        </h2>
        <SuggestionPanel suggestions={report.suggestions} />
      </section>
    </div>
  );
}

export default function ReportPage() {
  return (
    <AuthGuard>
    <AppShell title="评分报告">
      <Suspense fallback={<Loading label="加载报告..." />}>
        <ReportContent />
      </Suspense>
    </AppShell>
    </AuthGuard>
  );
}
