export interface Resume {
  id: string;
  fileName: string;
  uploadedAt: string;
  status: "pending" | "parsed" | "failed";
}

export interface ResumeAnalysis {
  resumeId: string;
  skills: string[];
  experience: string[];
  education: string[];
  summary: string;
}
