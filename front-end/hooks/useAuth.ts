"use client";

import { useAuthStore } from "@/store/authStore";

export function useAuth() {
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);
  const isLoading = useAuthStore((s) => s.isLoading);
  const error = useAuthStore((s) => s.error);
  const _hasHydrated = useAuthStore((s) => s._hasHydrated);
  const login = useAuthStore((s) => s.login);
  const register = useAuthStore((s) => s.register);
  const logout = useAuthStore((s) => s.logout);
  const fetchUser = useAuthStore((s) => s.fetchUser);
  const clearError = useAuthStore((s) => s.clearError);

  return {
    user,
    token,
    isAuthenticated: !!token,
    isHydrated: _hasHydrated,
    isLoading,
    error,
    login,
    register,
    logout,
    fetchUser,
    clearError,
  };
}
