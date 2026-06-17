"use client";

import { useInterviewStore } from "@/store/interviewStore";

export function useInterview() {
  const session = useInterviewStore((s) => s.session);
  const recentSessions = useInterviewStore((s) => s.recentSessions);
  const isLoading = useInterviewStore((s) => s.isLoading);
  const isTyping = useInterviewStore((s) => s.isTyping);
  const error = useInterviewStore((s) => s.error);
  const startSession = useInterviewStore((s) => s.startSession);
  const fetchRecentSessions = useInterviewStore((s) => s.fetchRecentSessions);
  const sendMessage = useInterviewStore((s) => s.sendMessage);
  const endSession = useInterviewStore((s) => s.endSession);
  const clearSession = useInterviewStore((s) => s.clearSession);
  const clearError = useInterviewStore((s) => s.clearError);

  return {
    session,
    recentSessions,
    isLoading,
    isTyping,
    error,
    startSession,
    fetchRecentSessions,
    sendMessage,
    endSession,
    clearSession,
    clearError,
  };
}
