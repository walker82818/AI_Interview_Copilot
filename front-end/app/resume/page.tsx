"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import AuthGuard from "@/components/auth/AuthGuard";
import AppShell from "@/components/common/AppShell";
import Loading from "@/components/common/Loading";
import ResumeUploader from "@/components/resume/ResumeUploader";
import ResumeCard from "@/components/resume/ResumeCard";
import ResumeAnalysisView from "@/components/resume/ResumeAnalysis";
import { useResumeStore } from "@/store/resumeStore";

function ProcessingIndicator() {
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
          AI 正在解析简历，已等待 {timeStr}...
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

export default function ResumePage() {
  const {
    resumes,
    currentResume,
    analysis,
    isLoading,
    isProcessing,
    error,
    fetchResumes,
    uploadResume,
    selectResume,
    fetchAnalysis,
    pollResumeStatus,
    deleteResume,
  } = useResumeStore();

  const cancelPollRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    fetchResumes();
  }, [fetchResumes]);

  // 当选中简历变为 parsed 时，加载分析
  useEffect(() => {
    if (currentResume?.status === "parsed") {
      fetchAnalysis(currentResume.id);
    }
  }, [currentResume, fetchAnalysis]);

  // 组件卸载时取消轮询
  useEffect(() => {
    return () => {
      cancelPollRef.current?.();
    };
  }, []);

  const handleUpload = useCallback(
    async (file: File) => {
      cancelPollRef.current?.();
      const resume = await uploadResume(file);
      // 启动轮询等待后端解析完成
      cancelPollRef.current = pollResumeStatus(resume.id);
    },
    [uploadResume, pollResumeStatus],
  );

  return (
    <AuthGuard>
    <AppShell title="简历管理">
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <ResumeUploader onUpload={handleUpload} isLoading={isLoading} />

          {error && (
            <p className="text-sm text-red-500">{error}</p>
          )}

          <div>
            <h2 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
              已上传简历
            </h2>
            {isLoading && resumes.length === 0 ? (
              <Loading label="加载简历..." />
            ) : resumes.length === 0 ? (
              <p className="text-sm text-zinc-400">暂无简历</p>
            ) : (
              <div className="space-y-3">
                {resumes.map((resume) => (
                  <ResumeCard
                    key={resume.id}
                    resume={resume}
                    selected={currentResume?.id === resume.id}
                    onSelect={selectResume}
                    onDelete={deleteResume}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="mb-4 text-lg font-medium text-zinc-900 dark:text-zinc-50">
            解析结果
          </h2>
          {!currentResume ? (
            <p className="text-sm text-zinc-400">请选择一份简历查看解析结果</p>
          ) : currentResume.status === "pending" || isProcessing ? (
            <ProcessingIndicator />
          ) : currentResume.status !== "parsed" ? (
            <p className="text-sm text-red-500">
              解析失败，请检查文件格式后重新上传
            </p>
          ) : isLoading && !analysis ? (
            <Loading label="加载解析结果..." />
          ) : analysis ? (
            <ResumeAnalysisView analysis={analysis} />
          ) : null}
        </div>
      </div>
    </AppShell>
    </AuthGuard>
  );
}
