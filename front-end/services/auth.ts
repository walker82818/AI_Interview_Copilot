import type { AuthResponse, LoginRequest, RegisterRequest, User } from "@/types";
import { apiRequest } from "@/utils/api";

export async function login(data: LoginRequest): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/auth/login", {
    method: "POST",
    body: data,
  });
}

export async function register(data: RegisterRequest): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/auth/register", {
    method: "POST",
    body: data,
  });
}

export async function getCurrentUser(): Promise<User> {
  return apiRequest<User>("/auth/me");
}

export async function logout(): Promise<void> {
  return apiRequest<void>("/auth/logout", { method: "POST" });
}
