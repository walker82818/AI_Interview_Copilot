import type { InterviewReport } from "@/types";
import { apiRequest } from "@/utils/api";

export async function getReport(sessionId: string): Promise<InterviewReport> {
  return apiRequest<InterviewReport>(`/reports/${sessionId}`);
}

export async function generateReport(
  sessionId: string,
): Promise<InterviewReport> {
  return apiRequest<InterviewReport>(`/reports/${sessionId}/generate`, {
    method: "POST",
  });
}
