import type { InterviewSession, Message } from "@/types";
import { apiRequest } from "@/utils/api";

export async function createSession(data: {
  resumeId: string;
  jdId: string;
}): Promise<InterviewSession> {
  return apiRequest<InterviewSession>("/interviews", {
    method: "POST",
    body: data,
  });
}

export async function getSession(id: string): Promise<InterviewSession> {
  return apiRequest<InterviewSession>(`/interviews/${id}`);
}

export async function getRecentSessions(): Promise<InterviewSession[]> {
  return apiRequest<InterviewSession[]>("/interviews/recent");
}

export async function sendMessage(
  sessionId: string,
  content: string,
): Promise<Message> {
  return apiRequest<Message>(`/interviews/${sessionId}/messages`, {
    method: "POST",
    body: { content },
  });
}

export async function endSession(sessionId: string): Promise<InterviewSession> {
  return apiRequest<InterviewSession>(`/interviews/${sessionId}/end`, {
    method: "POST",
  });
}
