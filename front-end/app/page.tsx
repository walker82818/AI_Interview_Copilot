import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
          AI Interview Copilot
        </h1>
        <p className="mt-3 max-w-md text-lg text-zinc-500 dark:text-zinc-400">
          上传简历与 JD，进行 AI 模拟面试，获取专业评分与学习建议
        </p>
      </div>

      <div className="flex gap-4">
        <Link
          href="/login"
          className="rounded-lg bg-zinc-900 px-6 py-2.5 text-sm text-white transition hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          登录
        </Link>
        <Link
          href="/register"
          className="rounded-lg border border-zinc-200 px-6 py-2.5 text-sm text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
        >
          注册
        </Link>
        <Link
          href="/dashboard"
          className="rounded-lg border border-zinc-200 px-6 py-2.5 text-sm text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
        >
          进入仪表板
        </Link>
      </div>
    </div>
  );
}
