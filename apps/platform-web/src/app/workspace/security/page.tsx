"use client";

import { useState } from "react";

import { changePassword } from "@/lib/management-api/auth";


export default function SecurityPage() {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      await changePassword({ oldPassword, newPassword });
      setOldPassword("");
      setNewPassword("");
      setNotice("Password updated. Please login again on other sessions.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to change password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="p-6">
      <h1 className="text-xl font-semibold">Security</h1>
      <p className="text-muted-foreground mt-2 text-sm">Change password via `/_management/auth/change-password`.</p>

      <form className="mt-4 grid gap-3 rounded-lg border border-border/80 bg-card/70 p-4" onSubmit={onSubmit}>
        <input
          className="h-9 rounded-md border border-border bg-background px-3 text-sm"
          type="password"
          placeholder="old password"
          value={oldPassword}
          onChange={(event) => setOldPassword(event.target.value)}
          required
        />
        <input
          className="h-9 rounded-md border border-border bg-background px-3 text-sm"
          type="password"
          placeholder="new password"
          value={newPassword}
          onChange={(event) => setNewPassword(event.target.value)}
          required
        />
        <button type="submit" disabled={loading} className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background disabled:opacity-50">
          {loading ? "Updating..." : "Update password"}
        </button>
      </form>

      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      {notice ? <p className="mt-4 text-sm text-emerald-700">{notice}</p> : null}
    </section>
  );
}
