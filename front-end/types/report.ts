export interface ScoreDimension {
  name: string;
  score: number;
  maxScore: number;
}

export interface Suggestion {
  category: string;
  content: string;
  priority: "high" | "medium" | "low";
}

export interface InterviewReport {
  id: string;
  sessionId: string;
  overallScore: number;
  dimensions: ScoreDimension[];
  suggestions: Suggestion[];
  summary: string;
  createdAt: string;
}
