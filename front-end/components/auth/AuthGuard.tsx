"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import Loading from "@/components/common/Loading";

interface AuthGuardProps {
  children: React.ReactNode;
}

export default function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const { isAuthenticated, isHydrated } = useAuth();

  useEffect(() => {
    if (isHydrated && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isHydrated, isAuthenticated, router]);

  // 等待 store 从 localStorage 恢复完成
  if (!isHydrated) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loading label="加载中..." />
      </div>
    );
  }

  // 未登录，不渲染页面内容（由 useEffect 负责跳转）
  if (!isAuthenticated) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loading label="正在跳转..." />
      </div>
    );
  }

  return <>{children}</>;
}
