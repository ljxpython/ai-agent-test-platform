"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ColumnResizeHandle, useResizableColumns } from "@/components/platform/column-resize";
import { ConfirmDialog } from "@/components/platform/confirm-dialog";
import { ListSearch } from "@/components/platform/list-search";
import { listAudit, type ManagementAuditRow } from "@/lib/management-api/audit";
import { getUser, listUserProjects, type ManagementUser, type ManagementUserProject, updateUser } from "@/lib/management-api/users";

export default function UserDetailPage() {
  const projectAccessColumnKeys = ["index", "project", "role", "status", "joinedAt"] as const;
  const userAuditColumnKeys = ["index", "time", "action", "path", "status"] as const;
  const params = useParams<{ userId: string }>();
  const userId = String(params.userId || "");

  const [user, setUser] = useState<ManagementUser | null>(null);
  const [projects, setProjects] = useState<ManagementUserProject[]>([]);
  const [audits, setAudits] = useState<ManagementAuditRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [updatingPassword, setUpdatingPassword] = useState(false);
  const [statusDialogTarget, setStatusDialogTarget] = useState<"active" | "disabled" | null>(null);

  const [username, setUsername] = useState("");
  const [status, setStatus] = useState<"active" | "disabled">("active");
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [projectSearchInput, setProjectSearchInput] = useState("");
  const [projectQuery, setProjectQuery] = useState("");
  const [auditSearchInput, setAuditSearchInput] = useState("");
  const [auditQuery, setAuditQuery] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const {
    columnWidths: projectColumnWidths,
    startResize: startProjectResize,
    resetColumnWidth: resetProjectColumnWidth,
    resizingColumnIndex: resizingProjectColumnIndex,
  } = useResizableColumns([80, 320, 140, 140, 180], {
    storageKey: "table-columns-user-detail-projects",
  });
  const {
    columnWidths: auditColumnWidths,
    startResize: startAuditResize,
    resetColumnWidth: resetAuditColumnWidth,
    resizingColumnIndex: resizingAuditColumnIndex,
  } = useResizableColumns([80, 180, 220, 280, 120], {
    storageKey: "table-columns-user-detail-audit",
  });
  const projectTableWidth = Math.max(760, projectColumnWidths.reduce((sum, width) => sum + width, 0));
  const auditTableWidth = Math.max(760, auditColumnWidths.reduce((sum, width) => sum + width, 0));

  const reload = useCallback(async () => {
    if (!userId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [userRow, projectsPayload, auditPayload] = await Promise.all([
        getUser(userId),
        listUserProjects(userId),
        listAudit(null, { limit: 10, offset: 0, targetId: userId }),
      ]);
      setUser(userRow);
      setProjects(projectsPayload.items);
      setAudits(auditPayload.items);
      setUsername(userRow.username);
      setStatus(userRow.status === "disabled" ? "disabled" : "active");
      setIsSuperAdmin(Boolean(userRow.is_super_admin));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load user detail");
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const statusActionLabel = useMemo(() => {
    if (!user) {
      return "Update Status";
    }
    return user.status === "active" ? "Disable User" : "Enable User";
  }, [user]);

  const filteredProjects = useMemo(() => {
    if (!projectQuery.trim()) {
      return projects;
    }
    const keyword = projectQuery.trim().toLowerCase();
    return projects.filter((item) => {
      return (
        item.project_name.toLowerCase().includes(keyword) ||
        item.project_description.toLowerCase().includes(keyword) ||
        item.role.toLowerCase().includes(keyword)
      );
    });
  }, [projectQuery, projects]);

  const filteredAudits = useMemo(() => {
    if (!auditQuery.trim()) {
      return audits;
    }
    const keyword = auditQuery.trim().toLowerCase();
    return audits.filter((item) => {
      const action = item.action?.toLowerCase() || "";
      const path = item.path.toLowerCase();
      const method = item.method.toLowerCase();
      return action.includes(keyword) || path.includes(keyword) || method.includes(keyword);
    });
  }, [auditQuery, audits]);

  async function onSaveProfile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user) {
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
      const updated = await updateUser(user.id, {
        username: normalizedUsername,
        status,
        is_super_admin: isSuperAdmin,
      });
      setUser(updated);
      setNotice("Profile updated");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user profile");
    } finally {
      setSavingProfile(false);
    }
  }

  async function onUpdatePassword(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user) {
      return;
    }
    if (newPassword.length < 8) {
      setError("New password must be at least 8 characters");
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setError("New password and confirmation do not match");
      return;
    }
    setUpdatingPassword(true);
    setError(null);
    setNotice(null);
    try {
      await updateUser(user.id, { password: newPassword });
      setNewPassword("");
      setConfirmNewPassword("");
      setNotice("Password updated successfully");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update password");
    } finally {
      setUpdatingPassword(false);
    }
  }

  async function onConfirmStatusChange() {
    if (!user || !statusDialogTarget) {
      return;
    }
    setSavingProfile(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await updateUser(user.id, { status: statusDialogTarget });
      setUser(updated);
      setStatus(updated.status === "disabled" ? "disabled" : "active");
      setNotice(statusDialogTarget === "disabled" ? "User disabled" : "User enabled");
      setStatusDialogTarget(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user status");
    } finally {
      setSavingProfile(false);
    }
  }

  return (
    <section className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">User Detail</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            {user ? `${user.username} · ${user.id}` : "Loading user..."}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm"
            onClick={() => setStatusDialogTarget(user?.status === "active" ? "disabled" : "active")}
            disabled={!user || savingProfile}
          >
            {statusActionLabel}
          </button>
          <Link
            href="/workspace/users"
            className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm"
          >
            Back to Users
          </Link>
        </div>
      </div>

      {loading ? <p className="mt-4 text-sm">Loading...</p> : null}
      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      {notice ? <p className="mt-4 text-sm text-emerald-700">{notice}</p> : null}

      <form className="mt-4 grid gap-3 rounded-lg border border-border/80 bg-card/70 p-4" onSubmit={onSaveProfile}>
        <h2 className="text-sm font-semibold">Profile</h2>
        <div className="grid gap-3 sm:grid-cols-2">
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
            Status
            <select
              className="h-9 rounded-md border border-border bg-background px-3 text-sm"
              value={status}
              onChange={(event) => setStatus(event.target.value as "active" | "disabled")}
            >
              <option value="active">active</option>
              <option value="disabled">disabled</option>
            </select>
          </label>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={isSuperAdmin} onChange={(event) => setIsSuperAdmin(event.target.checked)} />
          Super admin
        </label>
        <div className="grid gap-1 text-xs text-muted-foreground">
          <p>Created: {user?.created_at ? new Date(user.created_at).toLocaleString() : "-"}</p>
          <p>Updated: {user?.updated_at ? new Date(user.updated_at).toLocaleString() : "-"}</p>
          <p>Email: {user?.email || "-"}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="submit"
            className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background disabled:opacity-50"
            disabled={savingProfile || loading}
          >
            {savingProfile ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </form>

      <form className="mt-4 grid gap-3 rounded-lg border border-border/80 bg-card/70 p-4" onSubmit={onUpdatePassword} autoComplete="off">
        <h2 className="text-sm font-semibold">Security & Password</h2>
        <div className="grid gap-3 sm:grid-cols-2">
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
              value={confirmNewPassword}
              onChange={(event) => setConfirmNewPassword(event.target.value)}
              autoComplete="new-password"
              required
            />
          </label>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="submit"
            className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background disabled:opacity-50"
            disabled={updatingPassword || loading}
          >
            {updatingPassword ? "Updating..." : "Update Password"}
          </button>
          <button
            type="button"
            className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm"
            onClick={() => {
              setNewPassword("");
              setConfirmNewPassword("");
            }}
            disabled={updatingPassword}
          >
            Clear
          </button>
        </div>
      </form>

      <div className="mt-4 rounded-lg border border-border/80 bg-card/70 p-4">
        <h2 className="text-sm font-semibold">Project Access</h2>
        <ListSearch
          className="mt-3 flex flex-wrap items-center gap-2"
          value={projectSearchInput}
          placeholder="Search project access"
          onValueChange={setProjectSearchInput}
          onSearch={setProjectQuery}
          onClear={() => setProjectQuery("")}
        />
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-[760px] table-fixed text-sm" style={{ width: `max(100%, ${projectTableWidth}px)` }}>
            <colgroup>
              {projectColumnWidths.map((width, index) => (
                <col key={projectAccessColumnKeys[index]} style={{ width }} />
              ))}
            </colgroup>
            <thead className="bg-muted/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="relative px-3 py-2">#<ColumnResizeHandle active={resizingProjectColumnIndex === 0} onMouseDown={(event) => startProjectResize(0, event)} onDoubleClick={() => resetProjectColumnWidth(0)} /></th>
                <th className="relative px-3 py-2">Project<ColumnResizeHandle active={resizingProjectColumnIndex === 1} onMouseDown={(event) => startProjectResize(1, event)} onDoubleClick={() => resetProjectColumnWidth(1)} /></th>
                <th className="relative px-3 py-2">Role<ColumnResizeHandle active={resizingProjectColumnIndex === 2} onMouseDown={(event) => startProjectResize(2, event)} onDoubleClick={() => resetProjectColumnWidth(2)} /></th>
                <th className="relative px-3 py-2">Status<ColumnResizeHandle active={resizingProjectColumnIndex === 3} onMouseDown={(event) => startProjectResize(3, event)} onDoubleClick={() => resetProjectColumnWidth(3)} /></th>
                <th className="relative px-3 py-2">Joined At<ColumnResizeHandle active={resizingProjectColumnIndex === 4} onMouseDown={(event) => startProjectResize(4, event)} onDoubleClick={() => resetProjectColumnWidth(4)} /></th>
              </tr>
            </thead>
            <tbody>
              {filteredProjects.map((item, index) => (
                <tr key={item.project_id} className="border-t">
                  <td className="px-3 py-2 font-mono text-xs text-muted-foreground">{index + 1}</td>
                  <td className="px-3 py-2">
                    <Link href={`/workspace/projects/${item.project_id}`} className="text-primary underline-offset-2 hover:underline">
                      {item.project_name}
                    </Link>
                    <p className="text-muted-foreground mt-1 text-xs">{item.project_description || "-"}</p>
                  </td>
                  <td className="px-3 py-2">{item.role}</td>
                  <td className="px-3 py-2">{item.project_status}</td>
                  <td className="px-3 py-2 text-xs text-muted-foreground">{new Date(item.joined_at).toLocaleString()}</td>
                </tr>
              ))}
              {filteredProjects.length === 0 ? (
                <tr>
                  <td className="px-3 py-3 text-sm text-muted-foreground" colSpan={5}>No project membership found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-border/80 bg-card/70 p-4">
        <h2 className="text-sm font-semibold">Recent Audit</h2>
        <ListSearch
          className="mt-3 flex flex-wrap items-center gap-2"
          value={auditSearchInput}
          placeholder="Search audit by action/path/method"
          onValueChange={setAuditSearchInput}
          onSearch={setAuditQuery}
          onClear={() => setAuditQuery("")}
        />
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-[760px] table-fixed text-sm" style={{ width: `max(100%, ${auditTableWidth}px)` }}>
            <colgroup>
              {auditColumnWidths.map((width, index) => (
                <col key={userAuditColumnKeys[index]} style={{ width }} />
              ))}
            </colgroup>
            <thead className="bg-muted/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="relative px-3 py-2">#<ColumnResizeHandle active={resizingAuditColumnIndex === 0} onMouseDown={(event) => startAuditResize(0, event)} onDoubleClick={() => resetAuditColumnWidth(0)} /></th>
                <th className="relative px-3 py-2">Time<ColumnResizeHandle active={resizingAuditColumnIndex === 1} onMouseDown={(event) => startAuditResize(1, event)} onDoubleClick={() => resetAuditColumnWidth(1)} /></th>
                <th className="relative px-3 py-2">Action<ColumnResizeHandle active={resizingAuditColumnIndex === 2} onMouseDown={(event) => startAuditResize(2, event)} onDoubleClick={() => resetAuditColumnWidth(2)} /></th>
                <th className="relative px-3 py-2">Path<ColumnResizeHandle active={resizingAuditColumnIndex === 3} onMouseDown={(event) => startAuditResize(3, event)} onDoubleClick={() => resetAuditColumnWidth(3)} /></th>
                <th className="relative px-3 py-2">Status<ColumnResizeHandle active={resizingAuditColumnIndex === 4} onMouseDown={(event) => startAuditResize(4, event)} onDoubleClick={() => resetAuditColumnWidth(4)} /></th>
              </tr>
            </thead>
            <tbody>
              {filteredAudits.map((item, index) => (
                <tr key={item.id} className="border-t">
                  <td className="px-3 py-2 font-mono text-xs text-muted-foreground">{index + 1}</td>
                  <td className="px-3 py-2 text-xs text-muted-foreground">{new Date(item.created_at).toLocaleString()}</td>
                  <td className="px-3 py-2">{item.action || "-"}</td>
                  <td className="px-3 py-2 font-mono text-xs">{item.path}</td>
                  <td className="px-3 py-2">{item.status_code}</td>
                </tr>
              ))}
              {filteredAudits.length === 0 ? (
                <tr>
                  <td className="px-3 py-3 text-sm text-muted-foreground" colSpan={5}>No audit records.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/5 p-4">
        <h2 className="text-sm font-semibold text-destructive">Danger Zone</h2>
        <p className="mt-1 text-xs text-destructive/90">Disable this account to block future access while retaining audit history.</p>
        <div className="mt-3">
          <button
            type="button"
            className="inline-flex h-9 items-center justify-center rounded-md border border-destructive/40 bg-destructive/5 px-3 text-sm font-medium text-destructive"
            onClick={() => setStatusDialogTarget(user?.status === "active" ? "disabled" : "active")}
            disabled={!user || savingProfile}
          >
            {statusActionLabel}
          </button>
        </div>
      </div>

      <ConfirmDialog
        open={statusDialogTarget !== null}
        title={statusDialogTarget === "disabled" ? "Disable user" : "Enable user"}
        description={
          statusDialogTarget === "disabled"
            ? "Are you sure you want to disable this user account?"
            : "Are you sure you want to enable this user account?"
        }
        confirmLabel={statusDialogTarget === "disabled" ? "Disable" : "Enable"}
        confirmLabelLoading="Updating..."
        loading={savingProfile}
        onCancel={() => setStatusDialogTarget(null)}
        onConfirm={() => {
          void onConfirmStatusChange();
        }}
      />
    </section>
  );
}
