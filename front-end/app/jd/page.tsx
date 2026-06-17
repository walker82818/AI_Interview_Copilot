"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import AuthGuard from "@/components/auth/AuthGuard";
import AppShell from "@/components/common/AppShell";
import Loading from "@/components/common/Loading";
import JDUploader from "@/components/jd/JDUploader";
import JDAnalysisView from "@/components/jd/JDAnalysis";
import type { JobDescription, JDAnalysis } from "@/types";
import * as jdService from "@/services/jd";
import { formatDate } from "@/utils/format";

function ProcessingIndicator({ label = "AI 正在分析，已等待" }: { label?: string }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  const timeStr =
    minutes > 0 ? `${minutes} 分 ${seconds} 秒` : `${seconds} 秒`;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="inline-block h-2 w-2 rounded-full bg-blue-500 animate-ping" />
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          {label} {timeStr}...
        </p>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-1000"
          style={{ width: `${Math.min(elapsed / 30 * 90, 90)}%` }}
        />
      </div>
    </div>
  );
}

export default function JDPage() {
  const [jds, setJds] = useState<JobDescription[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<JDAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchJDs = async () => {
    setIsLoading(true);
    try {
      const data = await jdService.getJDs();
      setJds(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载 JD 失败");
    } finally {
      setIsLoading(false);
    }
  };

  const loadAnalysis = useCallback(async (id: string) => {
    setIsLoading(true);
    try {
      const result = await jdService.getJDAnalysis(id);
      setAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载分析失败");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const startPolling = useCallback(
    (id: string) => {
      stopPolling();
      setIsProcessing(true);
      setAnalysis(null);

      const poll = async () => {
        try {
          const jd = await jdService.getJD(id);
          setJds((prev) => prev.map((j) => (j.id === id ? jd : j)));

          if (jd.status === "analyzed") {
            setIsProcessing(false);
            loadAnalysis(id);
            return;
          }
          if (jd.status === "failed") {
            setIsProcessing(false);
            setError("JD 分析失败，请重新上传");
            return;
          }
          pollTimerRef.current = setTimeout(poll, 2000);
        } catch (err) {
          setIsProcessing(false);
          setError(err instanceof Error ? err.message : "轮询 JD 状态失败");
        }
      };

      pollTimerRef.current = setTimeout(poll, 1000);
    },
    [loadAnalysis],
  );

  const stopPolling = () => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    setIsProcessing(false);
  };

  useEffect(() => {
    fetchJDs();
    return () => stopPolling();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSelect = async (id: string) => {
    setSelectedId(id);
    setAnalysis(null);
    const jd = jds.find((j) => j.id === id);
    if (jd?.status === "analyzed") {
      loadAnalysis(id);
    } else if (jd?.status === "pending") {
      startPolling(id);
    }
  };

  const handleUpload = async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const jd = await jdService.uploadJD(file);
      setJds((prev) => [jd, ...prev]);
      setSelectedId(jd.id);
      startPolling(jd.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitText = async (data: {
    title: string;
    company: string;
    content: string;
  }) => {
    setIsLoading(true);
    setError(null);
    try {
      const jd = await jdService.createJD(data);
      setJds((prev) => [jd, ...prev]);
      setSelectedId(jd.id);
      startPolling(jd.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthGuard>
    <AppShell title="JD 管理">
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <JDUploader
            onUpload={handleUpload}
            onSubmitText={handleSubmitText}
            isLoading={isLoading}
          />

          {error && <p className="text-sm text-red-500">{error}</p>}

          <div>
            <h2 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
              已上传 JD
            </h2>
            {isLoading && jds.length === 0 ? (
              <Loading label="加载 JD..." />
            ) : jds.length === 0 ? (
              <p className="text-sm text-zinc-400">暂无 JD</p>
            ) : (
              <div className="space-y-3">
                {jds.map((jd) => (
                  <button
                    key={jd.id}
                    type="button"
                    onClick={() => handleSelect(jd.id)}
                    className={`w-full rounded-lg border p-4 text-left transition ${
                      selectedId === jd.id
                        ? "border-zinc-900 bg-zinc-50 dark:border-zinc-100 dark:bg-zinc-900"
                        : "border-zinc-200 bg-white hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-950"
                    }`}
                  >
                    <p className="font-medium text-zinc-900 dark:text-zinc-50">
                      {jd.title}
                    </p>
                    {jd.company && (
                      <p className="text-sm text-zinc-500">{jd.company}</p>
                    )}
                    <p className="mt-1 text-xs text-zinc-400">
                      {formatDate(jd.uploadedAt)}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="mb-4 text-lg font-medium text-zinc-900 dark:text-zinc-50">
            技能分析
          </h2>
          {!selectedId ? (
            <p className="text-sm text-zinc-400">请选择一份 JD 查看分析结果</p>
          ) : isProcessing ? (
            <ProcessingIndicator label="AI 正在分析 JD，已等待" />
          ) : isLoading && !analysis ? (
            <Loading label="加载分析结果..." />
          ) : analysis ? (
            <JDAnalysisView analysis={analysis} />
          ) : jds.find((j) => j.id === selectedId)?.status === "failed" ? (
            <p className="text-sm text-red-500">
              分析失败，请检查内容后重新上传
            </p>
          ) : (
            <p className="text-sm text-zinc-400">JD 分析进行中或尚未完成</p>
          )}
        </div>
      </div>
    </AppShell>
    </AuthGuard>
  );
}
