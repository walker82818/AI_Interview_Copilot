import type { Resume, ResumeAnalysis } from "@/types";
import { apiRequest, apiUpload } from "@/utils/api";

export async function uploadResume(file: File): Promise<Resume> {
  return apiUpload<Resume>("/resumes/upload", file);
}

export async function getResumes(): Promise<Resume[]> {
  return apiRequest<Resume[]>("/resumes");
}

export async function getResume(id: string): Promise<Resume> {
  return apiRequest<Resume>(`/resumes/${id}`);
}

export async function getResumeAnalysis(id: string): Promise<ResumeAnalysis> {
  return apiRequest<ResumeAnalysis>(`/resumes/${id}/analysis`);
}

export async function deleteResume(id: string): Promise<void> {
  return apiRequest<void>(`/resumes/${id}`, { method: "DELETE" });
}
