import type { JobDescription, JDAnalysis } from "@/types";
import { apiRequest, apiUpload } from "@/utils/api";

export async function uploadJD(file: File): Promise<JobDescription> {
  return apiUpload<JobDescription>("/jd/upload", file);
}

export async function createJD(data: {
  title: string;
  company: string;
  content: string;
}): Promise<JobDescription> {
  return apiRequest<JobDescription>("/jd", {
    method: "POST",
    body: data,
  });
}

export async function getJDs(): Promise<JobDescription[]> {
  return apiRequest<JobDescription[]>("/jd");
}

export async function getJD(id: string): Promise<JobDescription> {
  return apiRequest<JobDescription>(`/jd/${id}`);
}

export async function getJDAnalysis(id: string): Promise<JDAnalysis> {
  return apiRequest<JDAnalysis>(`/jd/${id}/analysis`);
}

export async function deleteJD(id: string): Promise<void> {
  return apiRequest<void>(`/jd/${id}`, { method: "DELETE" });
}
