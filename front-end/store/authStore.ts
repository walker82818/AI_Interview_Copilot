import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";
import * as authService from "@/services/auth";
import { TOKEN_KEY } from "@/utils/constants";

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  _hasHydrated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      error: null,
      _hasHydrated: false,

      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const { user, token } = await authService.login({ email, password });
          localStorage.setItem(TOKEN_KEY, token);
          set({ user, token, isLoading: false });
        } catch (err) {
          set({
            error: err instanceof Error ? err.message : "登录失败",
            isLoading: false,
          });
          throw err;
        }
      },

      register: async (name, email, password) => {
        set({ isLoading: true, error: null });
        try {
          const { user, token } = await authService.register({
            name,
            email,
            password,
          });
          localStorage.setItem(TOKEN_KEY, token);
          set({ user, token, isLoading: false });
        } catch (err) {
          set({
            error: err instanceof Error ? err.message : "注册失败",
            isLoading: false,
          });
          throw err;
        }
      },

      logout: async () => {
        try {
          await authService.logout();
        } catch {
          // ignore logout API errors
        }
        localStorage.removeItem(TOKEN_KEY);
        set({ user: null, token: null });
      },

      fetchUser: async () => {
        const { token } = get();
        if (!token) return;
        set({ isLoading: true });
        try {
          const user = await authService.getCurrentUser();
          set({ user, isLoading: false });
        } catch {
          localStorage.removeItem(TOKEN_KEY);
          set({ user: null, token: null, isLoading: false });
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state._hasHydrated = true;
        }
      },
    },
  ),
);
