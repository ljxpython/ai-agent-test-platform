"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { getOidcTokenSet } from "@/lib/oidc-storage";


export default function Page() {
  const router = useRouter();

  useEffect(() => {
    const tokenSet = getOidcTokenSet();
    if (tokenSet?.access_token) {
      router.replace("/workspace/projects");
      return;
    }
    router.replace("/auth/login");
  }, [router]);

  return null;
}
