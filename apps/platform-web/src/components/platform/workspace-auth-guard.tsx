"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { type ReactNode, useEffect, useMemo } from "react";

import { getValidAccessToken } from "@/lib/oidc-storage";

export function WorkspaceAuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const redirectTarget = useMemo(() => {
    const query = searchParams.toString();
    return query ? `${pathname}?${query}` : pathname;
  }, [pathname, searchParams]);

  const loggedIn = Boolean(getValidAccessToken());

  useEffect(() => {
    if (loggedIn) {
      return;
    }

    const params = new URLSearchParams();
    params.set("redirect", redirectTarget);
    router.replace(`/auth/login?${params.toString()}`);
  }, [loggedIn, redirectTarget, router]);

  if (!loggedIn) {
    return <div className="p-6">Redirecting to login...</div>;
  }

  return <>{children}</>;
}
