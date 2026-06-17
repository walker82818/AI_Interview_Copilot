"use client";

import { useRef, useState, type ChangeEvent } from "react";

interface JDUploaderProps {
  onUpload: (file: File) => void;
  onSubmitText?: (data: {
    title: string;
    company: string;
    content: string;
  }) => void;
  isLoading?: boolean;
}

export default function JDUploader({
  onUpload,
  onSubmitText,
  isLoading = false,
}: JDUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [mode, setMode] = useState<"file" | "text">("file");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [content, setContent] = useState("");

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onUpload(file);
  };

  const handleTextSubmit = () => {
    if (!title.trim() || !content.trim()) return;
    onSubmitText?.({ title, company, content });
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setMode("file")}
          className={`rounded-lg px-3 py-1.5 text-sm ${
            mode === "file"
              ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
              : "border border-zinc-200 text-zinc-600 dark:border-zinc-700 dark:text-zinc-400"
          }`}
        >
          上传文件
        </button>
        <button
          type="button"
          onClick={() => setMode("text")}
          className={`rounded-lg px-3 py-1.5 text-sm ${
            mode === "text"
              ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
              : "border border-zinc-200 text-zinc-600 dark:border-zinc-700 dark:text-zinc-400"
          }`}
        >
          粘贴文字
        </button>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.doc,.docx,.txt"
        onChange={handleFileChange}
        className="hidden"
      />

      {mode === "file" ? (
        <div
          onClick={() => !isLoading && inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-zinc-300 bg-zinc-50 p-8 transition hover:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-900/50 ${
            isLoading ? "pointer-events-none opacity-50" : ""
          }`}
        >
          <span className="text-3xl">💼</span>
          <p className="mt-2 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            上传岗位 JD
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <input
            type="text"
            placeholder="职位名称"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
          />
          <input
            type="text"
            placeholder="公司名称（选填）"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
          />
          <textarea
            placeholder="粘贴 JD 内容..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={6}
            className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
          />
          <button
            type="button"
            onClick={handleTextSubmit}
            disabled={isLoading}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
          >
            提交分析
          </button>
        </div>
      )}
    </div>
  );
}
