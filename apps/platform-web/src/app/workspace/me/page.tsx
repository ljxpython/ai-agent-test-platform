"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ConfirmDialog } from "@/components/platform/confirm-dialog";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { changePassword } from "@/lib/management-api/auth";
import { getMe, updateMe, type ManagementUser } from "@/lib/management-api/users";
import { clearOidcTokenSet } from "@/lib/oidc-storage";

type LocalProfileExtras = {
  avatarUrl: string;
  signature: string;
};

function getProfileExtrasStorageKey(userId: string): string {
  return `profile:extras:${userId}`;
}

export default function MePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<ManagementUser | null>(null);
  const [loading, setLoading] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [confirmSignOutOpen, setConfirmSignOutOpen] = useState(false);

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [signature, setSignature] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      setLoading(true);
      setError(null);
      try {
        const me = await getMe();
        if (cancelled) {
          return;
        }
        setProfile(me);
        setUsername(me.username);
        setEmail(me.email || "");

        if (typeof window !== "undefined") {
          const storageKey = getProfileExtrasStorageKey(me.id);
          const raw = window.localStorage.getItem(storageKey);
          if (raw) {
            try {
              const parsed = JSON.parse(raw) as Partial<LocalProfileExtras>;
              setAvatarUrl(typeof parsed.avatarUrl === "string" ? parsed.avatarUrl : "");
              setSignature(typeof parsed.signature === "string" ? parsed.signature : "");
            } catch {
              window.localStorage.removeItem(storageKey);
            }
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load current profile");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    void run();
    return () => {
      cancelled = true;
    };
  }, []);

  const avatarFallback = useMemo(() => {
    const name = username.trim();
    if (!name) {
      return "U";
    }
    return name.slice(0, 1).toUpperCase();
  }, [username]);

  async function onSaveProfile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!profile) {
      return;
    }
    const normalizedUsername = username.trim();
    if (!normalizedUsername) {
      setError("Username is required");
      return;
    }

    setSavingProfile(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await updateMe({
        username: normalizedUsername,
        email: email.trim(),
      });
      setProfile(updated);

      if (typeof window !== "undefined") {
        const storageKey = getProfileExtrasStorageKey(updated.id);
        const payload: LocalProfileExtras = {
          avatarUrl: avatarUrl.trim(),
          signature: signature.trim(),
        };
        window.localStorage.setItem(storageKey, JSON.stringify(payload));
      }

      setNotice("Profile updated");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setSavingProfile(false);
    }
  }

  async function onChangePassword(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (newPassword.length < 8) {
      setError("New password must be at least 8 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match");
      return;
    }
    if (oldPassword === newPassword) {
      setError("New password must be different from current password");
      return;
    }

    setSavingPassword(true);
    setError(null);
    setNotice(null);
    try {
      await changePassword({ oldPassword, newPassword });
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setNotice("Password updated successfully");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update password");
    } finally {
      setSavingPassword(false);
    }
  }

  function signOutNow() {
    clearOidcTokenSet();
    router.replace("/auth/login");
  }

  return (
    <section className="p-6">
      <h1 className="text-xl font-semibold">My Profile</h1>
      <p className="text-muted-foreground mt-2 text-sm">Manage your personal profile, password, and session.</p>

      {loading ? <p className="mt-4 text-sm">Loading...</p> : null}
      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      {notice ? <p className="mt-4 text-sm text-emerald-700">{notice}</p> : null}

      <form className="mt-4 grid gap-3 rounded-lg border border-border/80 bg-card/70 p-4" onSubmit={onSaveProfile}>
        <h2 className="text-sm font-semibold">Profile</h2>
        <div className="flex items-center gap-3">
          <Avatar className="size-12 border border-border">
            {avatarUrl.trim() ? <AvatarImage src={avatarUrl.trim()} alt="avatar" /> : null}
            <AvatarFallback>{avatarFallback}</AvatarFallback>
          </Avatar>
          <div className="text-xs text-muted-foreground">Avatar preview</div>
        </div>
        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Avatar URL
          <input
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            value={avatarUrl}
            onChange={(event) => setAvatarUrl(event.target.value)}
            placeholder="https://..."
          />
        </label>
        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Username
          <input
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />
        </label>
        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Email
          <input
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="optional"
          />
        </label>
        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Signature
          <textarea
            className="min-h-20 rounded-md border border-border bg-background px-3 py-2 text-sm"
            value={signature}
            onChange={(event) => setSignature(event.target.value)}
            maxLength={200}
            placeholder="Write your signature"
          />
          <span className="text-[11px]">{signature.length}/200</span>
        </label>
        <button
          type="submit"
          className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background disabled:opacity-50"
          disabled={savingProfile || loading}
        >
          {savingProfile ? "Saving..." : "Save Profile"}
        </button>
      </form>

      <form className="mt-4 grid gap-3 rounded-lg border border-border/80 bg-card/70 p-4" onSubmit={onChangePassword} autoComplete="off">
        <h2 className="text-sm font-semibold">Security</h2>
        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Current Password
          <input
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            type="password"
            value={oldPassword}
            onChange={(event) => setOldPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          New Password
          <input
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            type="password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            autoComplete="new-password"
            required
          />
        </label>
        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Confirm New Password
          <input
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            autoComplete="new-password"
            required
          />
        </label>
        <button
          type="submit"
          className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background disabled:opacity-50"
          disabled={savingPassword || loading}
        >
          {savingPassword ? "Updating..." : "Update Password"}
        </button>
      </form>

      <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/5 p-4">
        <h2 className="text-sm font-semibold text-destructive">Session</h2>
        <p className="mt-1 text-xs text-destructive/90">Sign out from current session.</p>
        <button
          type="button"
          className="mt-3 inline-flex h-9 items-center justify-center rounded-md border border-destructive/40 bg-destructive/5 px-3 text-sm font-medium text-destructive"
          onClick={() => setConfirmSignOutOpen(true)}
        >
          Sign Out
        </button>
      </div>

      <ConfirmDialog
        open={confirmSignOutOpen}
        title="Sign out"
        description="Are you sure you want to sign out from current session?"
        confirmLabel="Sign Out"
        confirmLabelLoading="Signing Out..."
        onCancel={() => setConfirmSignOutOpen(false)}
        onConfirm={signOutNow}
      />
    </section>
  );
}
