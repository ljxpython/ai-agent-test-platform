"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { login } from "@/lib/management-api/auth";
import { ensureApiUrlSeeded, setOidcTokenSet } from "@/lib/oidc-storage";


export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <section className="mx-auto flex min-h-[70vh] max-w-xl flex-col items-center justify-center gap-4 p-6 text-center">
      <h1 className="text-2xl font-semibold">Sign in</h1>
      <p className="text-muted-foreground text-sm">Use your username and password to continue.</p>

      <form
        className="w-full rounded-md border p-4 text-left"
        onSubmit={async (event) => {
          event.preventDefault();
          setError(null);
          setLoading(true);
          const formData = new FormData(event.currentTarget);
          const username = String(formData.get("username") ?? "").trim();
          const password = String(formData.get("password") ?? "");

          try {
            const payload = await login({ username, password });
            if (!payload.access_token) {
              throw new Error("Account login failed");
            }

            setOidcTokenSet({
              access_token: payload.access_token,
              refresh_token: payload.refresh_token,
            });
            ensureApiUrlSeeded();
            const redirectParam =
              typeof window === "undefined"
                ? ""
                : new URLSearchParams(window.location.search).get("redirect") || "";
            const redirectTo = redirectParam.startsWith("/workspace")
              ? redirectParam
              : "/workspace/chat";
            router.replace(redirectTo);
          } catch (submitError) {
            setError(submitError instanceof Error ? submitError.message : "Account login failed");
          } finally {
            setLoading(false);
          }
        }}
      >
        <div className="mb-3 flex flex-col gap-1">
          <label htmlFor="username" className="text-xs text-muted-foreground">Username</label>
          <input id="username" name="username" required className="rounded-md border px-3 py-2 text-sm" />
        </div>
        <div className="mb-3 flex flex-col gap-1">
          <label htmlFor="password" className="text-xs text-muted-foreground">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            required
            className="rounded-md border px-3 py-2 text-sm"
          />
        </div>
        {error ? <p className="mb-2 text-xs text-red-600">{error}</p> : null}
        <button
          type="submit"
          disabled={loading}
          className="bg-foreground text-background rounded-md px-4 py-2 text-sm disabled:opacity-60"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </section>
  );
}
