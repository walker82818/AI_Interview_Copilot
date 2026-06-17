import { apiRequest } from "@/utils/api";

export interface GitHubProfile {
  login: string;
  name: string;
  bio: string;
  public_repos: number;
  followers: number;
  top_languages: { language: string; repos: number }[];
  top_repos: {
    name: string;
    description: string;
    language: string;
    stars: number;
    topics: string[];
  }[];
}

export interface GitHubRepo {
  full_name: string;
  description: string;
  language: string;
  stars: number;
  forks: number;
  open_issues: number;
  topics: string[];
  languages: Record<string, number>;
  created_at: string;
  updated_at: string;
}

export interface LeetCodeProfile {
  username: string;
  ranking: number;
  total_solved: number;
  easy: number;
  medium: number;
  hard: number;
  contest_rating: number;
  contests_attended: number;
  recent_submissions: { title: string; language: string }[];
}

export async function getGitHubProfile(username: string): Promise<GitHubProfile> {
  return apiRequest<GitHubProfile>(
    `/external/github/profile?username=${encodeURIComponent(username)}`,
  );
}

export async function getGitHubRepo(
  owner: string,
  repo: string,
): Promise<GitHubRepo> {
  return apiRequest<GitHubRepo>(
    `/external/github/repo?owner=${encodeURIComponent(owner)}&repo=${encodeURIComponent(repo)}`,
  );
}

export async function getLeetCodeProfile(
  username: string,
): Promise<LeetCodeProfile> {
  return apiRequest<LeetCodeProfile>(
    `/external/leetcode/profile?username=${encodeURIComponent(username)}`,
  );
}
