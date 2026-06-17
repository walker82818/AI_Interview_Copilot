"use client";

import { useState } from "react";
import AuthGuard from "@/components/auth/AuthGuard";
import AppShell from "@/components/common/AppShell";
import type { GitHubProfile, LeetCodeProfile } from "@/services/external";
import * as externalService from "@/services/external";

type Tab = "github" | "leetcode";

export default function ExternalAnalysisPage() {
  const [tab, setTab] = useState<Tab>("github");
  const [githubUser, setGithubUser] = useState("");
  const [githubData, setGithubData] = useState<GitHubProfile | null>(null);
  const [leetcodeUser, setLeetcodeUser] = useState("");
  const [leetcodeData, setLeetcodeData] = useState<LeetCodeProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGitHubSearch = async () => {
    if (!githubUser.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await externalService.getGitHubProfile(githubUser.trim());
      setGithubData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "查询失败");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLeetCodeSearch = async () => {
    if (!leetcodeUser.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await externalService.getLeetCodeProfile(leetcodeUser.trim());
      setLeetcodeData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "查询失败");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthGuard>
      <AppShell title="外部分析">
        <div className="mx-auto max-w-2xl space-y-6">
          {/* Tab 切换 */}
          <div className="flex gap-1 rounded-lg bg-zinc-100 p-1 dark:bg-zinc-800">
            {(["github", "leetcode"] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition ${
                  tab === t
                    ? "bg-white text-zinc-900 shadow-sm dark:bg-zinc-700 dark:text-zinc-50"
                    : "text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
                }`}
              >
                {t === "github" ? "GitHub 分析" : "LeetCode 分析"}
              </button>
            ))}
          </div>

          {tab === "github" && (
            <GitHubPanel
              username={githubUser}
              setUsername={setGithubUser}
              data={githubData}
              isLoading={isLoading}
              error={error}
              onSearch={handleGitHubSearch}
            />
          )}

          {tab === "leetcode" && (
            <LeetCodePanel
              username={leetcodeUser}
              setUsername={setLeetcodeUser}
              data={leetcodeData}
              isLoading={isLoading}
              error={error}
              onSearch={handleLeetCodeSearch}
            />
          )}
        </div>
      </AppShell>
    </AuthGuard>
  );
}

/* ── GitHub Panel ──────────────────────────────────── */

function GitHubPanel({
  username,
  setUsername,
  data,
  isLoading,
  error,
  onSearch,
}: {
  username: string;
  setUsername: (v: string) => void;
  data: GitHubProfile | null;
  isLoading: boolean;
  error: string | null;
  onSearch: () => void;
}) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-500 dark:text-zinc-400">
        输入 GitHub 用户名，分析候选人的开源贡献和技术栈偏好。
      </p>
      <div className="flex gap-2">
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
          placeholder="GitHub 用户名，如 torvalds"
          className="flex-1 rounded-lg border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        />
        <button
          onClick={onSearch}
          disabled={isLoading || !username.trim()}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {isLoading ? "查询中..." : "分析"}
        </button>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {data && (
        <div className="space-y-4 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
          <div>
            <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
              {data.name || data.login}
            </h3>
            {data.bio && (
              <p className="mt-1 text-sm text-zinc-500">{data.bio}</p>
            )}
            <div className="mt-2 flex gap-4 text-sm text-zinc-400">
              <span>📦 {data.public_repos} repos</span>
              <span>👥 {data.followers} followers</span>
            </div>
          </div>

          {data.top_languages && data.top_languages.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-zinc-600 dark:text-zinc-400">
                语言偏好
              </h4>
              <div className="flex flex-wrap gap-2">
                {data.top_languages.map((l) => (
                  <span
                    key={l.language}
                    className="rounded-full bg-zinc-100 px-3 py-1 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                  >
                    {l.language} ({l.repos})
                  </span>
                ))}
              </div>
            </div>
          )}

          {data.top_repos && data.top_repos.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-zinc-600 dark:text-zinc-400">
                Top 仓库
              </h4>
              <div className="space-y-2">
                {data.top_repos.map((repo) => (
                  <div
                    key={repo.name}
                    className="rounded-lg border border-zinc-100 p-3 dark:border-zinc-800"
                  >
                    <p className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                      {repo.name}
                      {repo.language && (
                        <span className="ml-2 text-xs text-zinc-400">
                          {repo.language}
                        </span>
                      )}
                    </p>
                    {repo.description && (
                      <p className="mt-1 text-xs text-zinc-500 line-clamp-2">
                        {repo.description}
                      </p>
                    )}
                    <div className="mt-1 flex gap-3 text-xs text-zinc-400">
                      <span>⭐ {repo.stars}</span>
                      {repo.topics.slice(0, 3).map((t) => (
                        <span key={t} className="text-blue-500">
                          #{t}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── LeetCode Panel ──────────────────────────────────── */

function LeetCodePanel({
  username,
  setUsername,
  data,
  isLoading,
  error,
  onSearch,
}: {
  username: string;
  setUsername: (v: string) => void;
  data: LeetCodeProfile | null;
  isLoading: boolean;
  error: string | null;
  onSearch: () => void;
}) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-500 dark:text-zinc-400">
        输入 LeetCode 用户名，分析候选人的算法能力和刷题统计。
      </p>
      <div className="flex gap-2">
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
          placeholder="LeetCode 用户名"
          className="flex-1 rounded-lg border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        />
        <button
          onClick={onSearch}
          disabled={isLoading || !username.trim()}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {isLoading ? "查询中..." : "分析"}
        </button>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {data && (
        <div className="space-y-4 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
          <div>
            <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
              {data.username}
            </h3>
            <div className="mt-2 flex gap-4 text-sm text-zinc-400">
              {data.ranking && <span>🏆 排名 #{data.ranking.toLocaleString()}</span>}
              {data.contest_rating && (
                <span>📊 Rating {Math.round(data.contest_rating)}</span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-4 gap-3">
            <StatCard label="总解题" value={data.total_solved} color="bg-zinc-100 dark:bg-zinc-800" />
            <StatCard label="简单" value={data.easy} color="bg-green-100 dark:bg-green-900/30" />
            <StatCard label="中等" value={data.medium} color="bg-yellow-100 dark:bg-yellow-900/30" />
            <StatCard label="困难" value={data.hard} color="bg-red-100 dark:bg-red-900/30" />
          </div>

          {data.recent_submissions && data.recent_submissions.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-zinc-600 dark:text-zinc-400">
                最近提交
              </h4>
              <div className="space-y-1">
                {data.recent_submissions.map((s, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded px-3 py-1.5 text-sm"
                  >
                    <span className="text-zinc-700 dark:text-zinc-300">
                      {s.title}
                    </span>
                    <span className="text-xs text-zinc-400">{s.language}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className={`rounded-lg p-3 text-center ${color}`}>
      <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">
        {value}
      </p>
      <p className="text-xs text-zinc-500">{label}</p>
    </div>
  );
}
