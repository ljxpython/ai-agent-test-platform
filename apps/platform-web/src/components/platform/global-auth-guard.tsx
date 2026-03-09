"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { type ReactNode, useEffect, useMemo } from "react";

import { getValidAccessToken } from "@/lib/oidc-storage";

const PUBLIC_PATH_PREFIXES = ["/auth/login", "/auth/callback"];

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATH_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

export function GlobalAuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const redirectTarget = useMemo(() => {
    const query = searchParams.toString();
    return query ? `${pathname}?${query}` : pathname;
  }, [pathname, searchParams]);

  const loggedIn = Boolean(getValidAccessToken());
  const publicPath = isPublicPath(pathname);

  useEffect(() => {
    if (publicPath) {
      if (loggedIn && pathname.startsWith("/auth/login")) {
        router.replace("/workspace/chat");
      }
      return;
    }

    if (!loggedIn) {
      const params = new URLSearchParams();
      params.set("redirect", redirectTarget);
      router.replace(`/auth/login?${params.toString()}`);
    }
  }, [loggedIn, pathname, publicPath, redirectTarget, router]);

  if (!publicPath && !loggedIn) {
    return <div className="p-6">Redirecting to login...</div>;
  }

  return <>{children}</>;
}
