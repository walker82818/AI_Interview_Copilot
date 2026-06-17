import { create } from "zustand";
import type { Resume, ResumeAnalysis } from "@/types";
import * as resumeService from "@/services/resume";

interface ResumeState {
  resumes: Resume[];
  currentResume: Resume | null;
  analysis: ResumeAnalysis | null;
  isLoading: boolean;
  isProcessing: boolean;
  error: string | null;
  fetchResumes: () => Promise<void>;
  uploadResume: (file: File) => Promise<Resume>;
  selectResume: (id: string) => Promise<void>;
  fetchAnalysis: (id: string) => Promise<void>;
  pollResumeStatus: (id: string) => () => void;
  deleteResume: (id: string) => Promise<void>;
  clearError: () => void;
}

export const useResumeStore = create<ResumeState>((set, get) => ({
  resumes: [],
  currentResume: null,
  analysis: null,
  isLoading: false,
  isProcessing: false,
  error: null,

  fetchResumes: async () => {
    set({ isLoading: true, error: null });
    try {
      const resumes = await resumeService.getResumes();
      set({ resumes, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "加载简历失败",
        isLoading: false,
      });
    }
  },

  uploadResume: async (file) => {
    set({ isLoading: true, error: null });
    try {
      const resume = await resumeService.uploadResume(file);
      set((state) => ({
        resumes: [resume, ...state.resumes],
        currentResume: resume,
        isLoading: false,
      }));
      return resume;
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "上传简历失败",
        isLoading: false,
      });
      throw err;
    }
  },

  selectResume: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const resume = await resumeService.getResume(id);
      set({ currentResume: resume, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "加载简历失败",
        isLoading: false,
      });
    }
  },

  fetchAnalysis: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const analysis = await resumeService.getResumeAnalysis(id);
      set({ analysis, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "加载解析结果失败",
        isLoading: false,
      });
    }
  },

  pollResumeStatus: (id) => {
    let cancelled = false;
    set({ isProcessing: true });

    const poll = async () => {
      if (cancelled) return;
      try {
        const resume = await resumeService.getResume(id);
        if (cancelled) return;

        // 更新列表中对应简历的状态
        set((state) => {
          const resumes = state.resumes.map((r) =>
            r.id === id ? resume : r,
          );
          const currentResume =
            state.currentResume?.id === id ? resume : state.currentResume;
          return { resumes, currentResume };
        });

        if (resume.status === "parsed") {
          set({ isProcessing: false });
          // 触发分析加载
          const { fetchAnalysis } = get();
          fetchAnalysis(id);
          return;
        }
        if (resume.status === "failed") {
          set({
            isProcessing: false,
            error: "简历解析失败，请检查文件格式后重新上传",
          });
          return;
        }
        // 仍在 pending，继续轮询
        setTimeout(poll, 2000);
      } catch (err) {
        if (!cancelled) {
          set({
            isProcessing: false,
            error:
              err instanceof Error ? err.message : "轮询简历状态失败",
          });
        }
      }
    };

    // 延迟 1 秒后开始第一次轮询
    setTimeout(poll, 1000);

    // 返回取消函数
    return () => {
      cancelled = true;
      set({ isProcessing: false });
    };
  },

  deleteResume: async (id) => {
    await resumeService.deleteResume(id);
    const { currentResume } = get();
    set((state) => ({
      resumes: state.resumes.filter((r) => r.id !== id),
      currentResume: currentResume?.id === id ? null : currentResume,
      analysis: currentResume?.id === id ? null : state.analysis,
    }));
  },

  clearError: () => set({ error: null }),
}));
