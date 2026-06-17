import { create } from "zustand";
import type { InterviewSession, Message } from "@/types";
import * as interviewService from "@/services/interview";

interface InterviewState {
  session: InterviewSession | null;
  recentSessions: InterviewSession[];
  isLoading: boolean;
  isTyping: boolean;
  error: string | null;
  startSession: (resumeId: string, jdId: string) => Promise<void>;
  fetchRecentSessions: () => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  endSession: () => Promise<void>;
  clearSession: () => void;
  clearError: () => void;
}

export const useInterviewStore = create<InterviewState>((set, get) => ({
  session: null,
  recentSessions: [],
  isLoading: false,
  isTyping: false,
  error: null,

  startSession: async (resumeId, jdId) => {
    set({ isLoading: true, error: null });
    try {
      const session = await interviewService.createSession({ resumeId, jdId });
      set({ session, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "建立面试失败",
        isLoading: false,
      });
      throw err;
    }
  },

  fetchRecentSessions: async () => {
    set({ isLoading: true, error: null });
    try {
      const recentSessions = await interviewService.getRecentSessions();
      set({ recentSessions, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "加载面试记录失败",
        isLoading: false,
      });
    }
  },

  sendMessage: async (content) => {
    const { session } = get();
    if (!session) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      createdAt: new Date().toISOString(),
    };

    set((state) => ({
      session: state.session
        ? {
            ...state.session,
            messages: [...state.session.messages, userMessage],
          }
        : null,
      isTyping: true,
    }));

    try {
      const reply = await interviewService.sendMessage(session.id, content);
      set((state) => ({
        session: state.session
          ? {
              ...state.session,
              messages: [...state.session.messages, reply],
            }
          : null,
        isTyping: false,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "发送消息失败",
        isTyping: false,
      });
    }
  },

  endSession: async () => {
    const { session } = get();
    if (!session) return;
    set({ isLoading: true });
    try {
      const updated = await interviewService.endSession(session.id);
      set({ session: updated, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "结束面试失败",
        isLoading: false,
      });
    }
  },

  clearSession: () => set({ session: null }),
  clearError: () => set({ error: null }),
}));
