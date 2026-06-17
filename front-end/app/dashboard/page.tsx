"use client";

import { useEffect } from "react";
import Link from "next/link";
import AuthGuard from "@/components/auth/AuthGuard";
import AppShell from "@/components/common/AppShell";
import Loading from "@/components/common/Loading";
import ResumeCard from "@/components/resume/ResumeCard";
import { useResumeStore } from "@/store/resumeStore";
import { useInterviewStore } from "@/store/interviewStore";
import { formatDate } from "@/utils/format";

export default function DashboardPage() {
  const {
    resumes,
    fetchResumes,
    isLoading: resumeLoading,
    selectResume,
    currentResume,
  } = useResumeStore();
  const {
    recentSessions,
    fetchRecentSessions,
    isLoading: interviewLoading,
  } = useInterviewStore();

  useEffect(() => {
    fetchResumes();
    fetchRecentSessions();
  }, [fetchResumes, fetchRecentSessions]);

  const isLoading = resumeLoading || interviewLoading;

  return (
    <AuthGuard>
    <AppShell title="仪表板">
      {isLoading && resumes.length === 0 ? (
        <Loading />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
                我的简历
              </h2>
              <Link
                href="/resume"
                className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
              >
                管理 →
              </Link>
            </div>
            {resumes.length === 0 ? (
              <p className="text-sm text-zinc-400">
                尚未上传简历，{" "}
                <Link href="/resume" className="underline">
                  立即上传
                </Link>
              </p>
            ) : (
              <div className="space-y-3">
                {resumes.slice(0, 3).map((resume) => (
                  <ResumeCard
                    key={resume.id}
                    resume={resume}
                    selected={currentResume?.id === resume.id}
                    onSelect={selectResume}
                  />
                ))}
              </div>
            )}
          </section>

          <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
                我的 JD
              </h2>
              <Link
                href="/jd"
                className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
              >
                管理 →
              </Link>
            </div>
            <p className="text-sm text-zinc-400">
              前往{" "}
              <Link href="/jd" className="underline">
                JD 管理
              </Link>{" "}
              上传并分析岗位描述
            </p>
          </section>

          <section className="rounded-xl border border-zinc-200 bg-white p-6 lg:col-span-2 dark:border-zinc-800 dark:bg-zinc-950">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
                最近面试
              </h2>
              <Link
                href="/interview"
                className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
              >
                开始面试 →
              </Link>
            </div>
            {recentSessions.length === 0 ? (
              <p className="text-sm text-zinc-400">暂无面试记录</p>
            ) : (
              <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {recentSessions.slice(0, 5).map((session) => (
                  <div
                    key={session.id}
                    className="flex items-center justify-between py-3"
                  >
                    <div>
                      <p className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                        面试 #{session.id.slice(0, 8)}
                      </p>
                      {session.startedAt && (
                        <p className="text-xs text-zinc-400">
                          {formatDate(session.startedAt)}
                        </p>
                      )}
                    </div>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        session.status === "completed"
                          ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                          : session.status === "active"
                            ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                            : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                      }`}
                    >
                      {session.status === "completed"
                        ? "已完成"
                        : session.status === "active"
                          ? "进行中"
                          : "待开始"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </AppShell>
    </AuthGuard>
  );
}
