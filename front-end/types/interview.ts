export type MessageRole = "user" | "assistant" | "system";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
}

export interface InterviewSession {
  id: string;
  resumeId: string;
  jdId: string;
  status: "idle" | "active" | "completed";
  messages: Message[];
  startedAt?: string;
  endedAt?: string;
}
