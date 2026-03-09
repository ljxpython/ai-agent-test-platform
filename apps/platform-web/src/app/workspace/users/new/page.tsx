"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { createUser } from "@/lib/management-api/users";


export default function CreateUserPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createUser({
        username: username.trim(),
        password,
        is_super_admin: isSuperAdmin,
      });
      router.replace("/workspace/users");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create user");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="p-6">
      <h1 className="text-xl font-semibold">Create User</h1>
      <p className="text-muted-foreground mt-2 text-sm">Create a new system user in a dedicated page.</p>

      <form className="mt-4 grid gap-3 rounded-lg border border-border/80 bg-card/70 p-4" onSubmit={onSubmit} autoComplete="off">
        <input
          className="h-9 rounded-md border border-border bg-background px-3 text-sm"
          name="create-user-username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          placeholder="username"
          autoComplete="off"
          required
        />
        <input
          className="h-9 rounded-md border border-border bg-background px-3 text-sm"
          name="create-user-password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="password"
          autoComplete="new-password"
          required
        />
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={isSuperAdmin} onChange={(event) => setIsSuperAdmin(event.target.checked)} />
          Super admin
        </label>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background disabled:opacity-50"
          >
            {submitting ? "Creating..." : "Create user"}
          </button>
          <Link href="/workspace/users" className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm">
            Back to Users
          </Link>
        </div>
      </form>

      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
    </section>
  );
}
