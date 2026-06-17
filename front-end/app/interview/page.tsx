"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AuthGuard from "@/components/auth/AuthGuard";
import AppShell from "@/components/common/AppShell";
import ChatBox from "@/components/chat/ChatBox";
import Loading from "@/components/common/Loading";
import { useInterview } from "@/hooks/useInterview";
import { useResumeStore } from "@/store/resumeStore";
import * as jdService from "@/services/jd";
import type { JobDescription } from "@/types";

export default function InterviewPage() {
  const {
    session,
    isLoading,
    isTyping,
    error,
    startSession,
    sendMessage,
    endSession,
  } = useInterview();

  const { resumes, fetchResumes } = useResumeStore();
  const [jds, setJds] = useState<JobDescription[]>([]);
  const [resumeId, setResumeId] = useState("");
  const [jdId, setJdId] = useState("");

  useEffect(() => {
    fetchResumes();
    jdService.getJDs().then(setJds).catch(() => {});
  }, [fetchResumes]);

  const handleStart = async () => {
    if (!resumeId || !jdId) return;
    await startSession(resumeId, jdId);
  };

  const handleEnd = async () => {
    await endSession();
  };

  return (
    <AuthGuard>
    <AppShell title="模拟面试">
      {!session ? (
        <div className="mx-auto max-w-lg space-y-6">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            选择简历与 JD，开始 AI 模拟面试。面试官会根据 JD 即时追问。
          </p>

          <div>
            <label className="mb-1 block text-sm text-zinc-600 dark:text-zinc-400">
              选择简历
            </label>
            <select
              value={resumeId}
              onChange={(e) => setResumeId(e.target.value)}
              className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            >
              <option value="">请选择</option>
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.fileName}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm text-zinc-600 dark:text-zinc-400">
              选择 JD
            </label>
            <select
              value={jdId}
              onChange={(e) => setJdId(e.target.value)}
              className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            >
              <option value="">请选择</option>
              {jds.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title}
                </option>
              ))}
            </select>
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <button
            type="button"
            onClick={handleStart}
            disabled={!resumeId || !jdId || isLoading}
            className="w-full rounded-lg bg-zinc-900 py-2.5 text-sm text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
          >
            {isLoading ? "准备中..." : "开始面试"}
          </button>
        </div>
      ) : (
        <div className="flex h-[calc(100vh-12rem)] flex-col gap-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-zinc-500">
              面试进行中 · {session.messages.length} 条消息
            </p>
            <div className="flex gap-2">
              {session.status === "completed" && (
                <Link
                  href={`/report?sessionId=${session.id}`}
                  className="rounded-lg border border-zinc-200 px-3 py-1.5 text-sm dark:border-zinc-700"
                >
                  查看报告
                </Link>
              )}
              <button
                type="button"
                onClick={handleEnd}
                disabled={isLoading || session.status === "completed"}
                className="rounded-lg bg-red-600 px-3 py-1.5 text-sm text-white disabled:opacity-50"
              >
                结束面试
              </button>
            </div>
          </div>

          <div className="flex-1">
            <ChatBox
              messages={session.messages}
              isTyping={isTyping}
              disabled={session.status === "completed"}
              onSend={sendMessage}
            />
          </div>
        </div>
      )}
    </AppShell>
    </AuthGuard>
  );
}
