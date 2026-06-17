"use client";

import { useRef, useState, type ChangeEvent, type DragEvent } from "react";

interface ResumeUploaderProps {
  onUpload: (file: File) => void;
  isLoading?: boolean;
  accept?: string;
}

export default function ResumeUploader({
  onUpload,
  isLoading = false,
  accept = ".pdf,.txt",
}: ResumeUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [inputKey, setInputKey] = useState(0);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFile = (file: File) => {
    onUpload(file);
    setInputKey((k) => k + 1);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isLoading) setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    if (isLoading) return;
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div
      onClick={() => !isLoading && inputRef.current?.click()}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition ${
        isDragOver
          ? "border-blue-400 bg-blue-50 dark:border-blue-500 dark:bg-blue-900/20"
          : "border-zinc-300 bg-zinc-50 hover:border-zinc-400 hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-900/50 dark:hover:border-zinc-500 dark:hover:bg-zinc-900"
      } ${isLoading ? "pointer-events-none opacity-50" : ""}`}
    >
      <input
        key={inputKey}
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        className="hidden"
      />
      <span className="text-3xl">{isDragOver ? "📥" : "📄"}</span>
      <p className="mt-2 text-sm font-medium text-zinc-700 dark:text-zinc-300">
        {isDragOver ? "松开以上传文件" : "点击或拖拽上传简历"}
      </p>
      <p className="mt-1 text-xs text-zinc-400">支持 PDF、TXT 格式</p>
    </div>
  );
}
