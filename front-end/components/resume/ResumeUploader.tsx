"use client";

import { useRef, useState, type ChangeEvent } from "react";

interface ResumeUploaderProps {
  onUpload: (file: File) => void;
  isLoading?: boolean;
}

export default function ResumeUploader({
  onUpload,
  isLoading = false,
}: ResumeUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [inputKey, setInputKey] = useState(0);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      setInputKey((k) => k + 1);
    }
  };

  return (
    <div
      onClick={() => !isLoading && inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-zinc-300 bg-zinc-50 p-8 transition hover:border-zinc-400 hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-900/50 dark:hover:border-zinc-500 dark:hover:bg-zinc-900 ${
        isLoading ? "pointer-events-none opacity-50" : ""
      }`}
    >
      <input
        key={inputKey}
        ref={inputRef}
        type="file"
        accept=".pdf,.doc,.docx,.txt"
        onChange={handleChange}
        className="hidden"
      />
      <span className="text-3xl">📄</span>
      <p className="mt-2 text-sm font-medium text-zinc-700 dark:text-zinc-300">
        点击或拖拽上传简历
      </p>
      <p className="mt-1 text-xs text-zinc-400">支持 PDF、Word、TXT</p>
    </div>
  );
}
