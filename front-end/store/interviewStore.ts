import { create } from "zustand";
import type { InterviewSession, Message } from "@/types";
import * as interviewService from "@/services/interview";
import { API_BASE_URL, TOKEN_KEY } from "@/utils/constants";

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

    // 创建一个占位的 AI 回复消息
    const assistantId = crypto.randomUUID();
    const assistantPlaceholder: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      createdAt: new Date().toISOString(),
    };

    set((state) => ({
      session: state.session
        ? {
            ...state.session,
            messages: [...state.session.messages, userMessage, assistantPlaceholder],
          }
        : null,
      isTyping: true,
    }));

    try {
      const token =
        typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;
      const response = await fetch(
        `${API_BASE_URL}/interviews/${session.id}/messages/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ content }),
        },
      );

      if (!response.ok) {
        throw new Error("流式请求失败");
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("无法读取响应流");

      const decoder = new TextDecoder();
      let fullContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6);
          if (payload === "[DONE]" || payload === "[ERROR]") continue;

          fullContent += payload;
          set((state) => ({
            session: state.session
              ? {
                  ...state.session,
                  messages: state.session.messages.map((m) =>
                    m.id === assistantId ? { ...m, content: fullContent } : m,
                  ),
                }
              : null,
          }));
        }
      }

      set({ isTyping: false });
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
