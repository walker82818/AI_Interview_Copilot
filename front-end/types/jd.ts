export interface JobDescription {
  id: string;
  title: string;
  company: string;
  uploadedAt: string;
  status: "pending" | "analyzed" | "failed";
}

export interface JDAnalysis {
  jdId: string;
  requiredSkills: string[];
  preferredSkills: string[];
  responsibilities: string[];
  matchScore?: number;
}
