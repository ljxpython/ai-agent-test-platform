"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ColumnResizeHandle, useResizableColumns } from "@/components/platform/column-resize";
import { ConfirmDialog } from "@/components/platform/confirm-dialog";
import { ListSearch } from "@/components/platform/list-search";
import { deleteMember, listMembers, upsertMember, type ManagementProjectMember } from "@/lib/management-api/members";
import { listUsersPage, type ManagementUser } from "@/lib/management-api/users";

export default function ProjectMembersPage() {
  const memberColumnKeys = ["index", "userId", "username", "role", "actions"] as const;
  const params = useParams<{ projectId: string }>();
  const projectId = String(params.projectId || "");

  const [items, setItems] = useState<ManagementProjectMember[]>([]);
  const [memberQuery, setMemberQuery] = useState("");
  const [memberSearchInput, setMemberSearchInput] = useState("");
  const [userId, setUserId] = useState("");
  const [userSearch, setUserSearch] = useState("");
  const [userCandidates, setUserCandidates] = useState<ManagementUser[]>([]);
  const [searchingUsers, setSearchingUsers] = useState(false);
  const [role, setRole] = useState<"admin" | "editor" | "executor">("executor");
  const [loading, setLoading] = useState(false);
  const [removingUserId, setRemovingUserId] = useState<string | null>(null);
  const [pendingDeleteMember, setPendingDeleteMember] = useState<ManagementProjectMember | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const { columnWidths, startResize, resetColumnWidth, resizingColumnIndex } = useResizableColumns([80, 230, 220, 140, 220], {
    storageKey: "table-columns-project-members",
  });
  const tableWidth = Math.max(640, columnWidths.reduce((sum, width) => sum + width, 0));
  const existingMemberUserIds = useMemo(() => new Set(items.map((item) => item.user_id)), [items]);
  const adminCount = items.filter((item) => item.role === "admin").length;
  const targetExistingMember = items.find((item) => item.user_id === userId.trim());
  const downgradeLastAdminBlocked =
    targetExistingMember?.role === "admin" && role !== "admin" && adminCount <= 1;

  const refreshMembers = useCallback(async () => {
    if (!projectId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const rows = await listMembers(projectId, { query: memberQuery });
      setItems(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load members");
    } finally {
      setLoading(false);
    }
  }, [memberQuery, projectId]);

  useEffect(() => {
    void refreshMembers();
  }, [refreshMembers]);

  useEffect(() => {
    let cancelled = false;
    if (!userSearch.trim()) {
      setUserCandidates([]);
      return () => {
        cancelled = true;
      };
    }

    const timerId = window.setTimeout(async () => {
      setSearchingUsers(true);
      try {
        const payload = await listUsersPage({
          limit: 20,
          offset: 0,
          query: userSearch,
          status: "active",
          excludeUserIds: Array.from(existingMemberUserIds),
        });
        if (!cancelled) {
          setUserCandidates(payload.items.filter((candidate) => !existingMemberUserIds.has(candidate.id)));
        }
      } catch {
        if (!cancelled) {
          setUserCandidates([]);
        }
      } finally {
        if (!cancelled) {
          setSearchingUsers(false);
        }
      }
    }, 300);

    return () => {
      cancelled = true;
      window.clearTimeout(timerId);
    };
  }, [existingMemberUserIds, userSearch]);

  async function onUpsert(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (downgradeLastAdminBlocked) {
      setError("Cannot downgrade the last project admin");
      return;
    }
    setError(null);
    setNotice(null);
    try {
      const row = await upsertMember({
        projectId,
        userId: userId.trim(),
        role,
      });
      setNotice(`Saved member: ${row.username}`);
      setUserId("");
      await refreshMembers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save member");
    }
  }

  async function onDelete(member: ManagementProjectMember) {
    setRemovingUserId(member.user_id);
    setError(null);
    setNotice(null);
    try {
      await deleteMember(projectId, member.user_id);
      setNotice(`Removed member: ${member.username}`);
      await refreshMembers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete member");
    } finally {
      setPendingDeleteMember((current) => (current?.user_id === member.user_id ? null : current));
      setRemovingUserId(null);
    }
  }

  return (
    <section className="p-6">
      <h1 className="text-xl font-semibold">Project Members</h1>
      <p className="text-muted-foreground mt-2 text-sm">Project: <code>{projectId}</code></p>

      <form className="mt-4 grid gap-3 rounded-lg border border-border/80 bg-card/70 p-4" onSubmit={onUpsert}>
        <div className="grid gap-2">
          <label htmlFor="member-user-search" className="text-xs font-medium text-muted-foreground">Search user by username</label>
          <input
            id="member-user-search"
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            placeholder="type username to search"
            value={userSearch}
            onChange={(event) => setUserSearch(event.target.value)}
          />
          {searchingUsers ? <p className="text-xs text-muted-foreground">Searching...</p> : null}
          {!searchingUsers && userCandidates.length > 0 ? (
            <div className="max-h-40 overflow-auto rounded-md border border-border bg-background/80 p-1">
              {userCandidates.map((candidate) => (
                <button
                  key={candidate.id}
                  type="button"
                  className="flex w-full items-center justify-between rounded px-2 py-1 text-left text-xs hover:bg-accent"
                  onClick={() => {
                    setUserId(candidate.id);
                    setUserSearch(candidate.username);
                  }}
                >
                  <span>{candidate.username}</span>
                  <span className="font-mono text-[10px] text-muted-foreground">{candidate.id}</span>
                </button>
              ))}
            </div>
          ) : null}
        </div>
        <input
          className="h-9 rounded-md border border-border bg-background px-3 text-sm"
          placeholder="user id (manual input still supported)"
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
          required
        />
        <select
          className="h-9 rounded-md border border-border bg-background px-3 text-sm"
          value={role}
          onChange={(event) => setRole(event.target.value as "admin" | "editor" | "executor")}
        >
          <option value="admin">admin</option>
          <option value="editor">editor</option>
          <option value="executor">executor</option>
        </select>
        <button type="submit" className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background">
          Save member
        </button>
        {adminCount <= 1 ? <p className="text-xs text-amber-700">Last admin protection is active for this project.</p> : null}
      </form>

      {loading ? <p className="mt-4 text-sm">Loading...</p> : null}
      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      {notice ? <p className="mt-4 text-sm text-emerald-700">{notice}</p> : null}

      <ListSearch
        value={memberSearchInput}
        placeholder="Search member by username"
        onValueChange={setMemberSearchInput}
        onSearch={setMemberQuery}
        onClear={() => setMemberQuery("")}
      />

      <div className="mt-4 overflow-x-auto rounded-lg border border-border/80 bg-card/70">
        <table className="min-w-[640px] table-fixed text-sm" style={{ width: `max(100%, ${tableWidth}px)` }}>
          <colgroup>
            {columnWidths.map((width, index) => (
              <col key={memberColumnKeys[index]} style={{ width }} />
            ))}
          </colgroup>
          <thead className="bg-muted/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="relative px-4 py-2">#<ColumnResizeHandle active={resizingColumnIndex === 0} onMouseDown={(event) => startResize(0, event)} onDoubleClick={() => resetColumnWidth(0)} /></th>
              <th className="relative px-4 py-2">User ID<ColumnResizeHandle active={resizingColumnIndex === 1} onMouseDown={(event) => startResize(1, event)} onDoubleClick={() => resetColumnWidth(1)} /></th>
              <th className="relative px-4 py-2">Username<ColumnResizeHandle active={resizingColumnIndex === 2} onMouseDown={(event) => startResize(2, event)} onDoubleClick={() => resetColumnWidth(2)} /></th>
              <th className="relative px-4 py-2">Role<ColumnResizeHandle active={resizingColumnIndex === 3} onMouseDown={(event) => startResize(3, event)} onDoubleClick={() => resetColumnWidth(3)} /></th>
              <th className="relative px-4 py-2">Actions<ColumnResizeHandle active={resizingColumnIndex === 4} onMouseDown={(event) => startResize(4, event)} onDoubleClick={() => resetColumnWidth(4)} /></th>
            </tr>
          </thead>
          <tbody>
            {items.map((member, index) => (
              <tr key={member.user_id} className="border-t">
                <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{index + 1}</td>
                <td className="px-4 py-2 font-mono text-xs">{member.user_id}</td>
                <td className="px-4 py-2 font-medium">{member.username}</td>
                <td className="px-4 py-2">{member.role}</td>
                <td className="px-4 py-2">
                  <button
                    type="button"
                    className="inline-flex h-8 items-center justify-center rounded-md border border-destructive/40 bg-destructive/5 px-2 text-xs text-destructive"
                    onClick={() => setPendingDeleteMember(member)}
                    disabled={(member.role === "admin" && adminCount <= 1) || removingUserId === member.user_id}
                  >
                    {member.role === "admin" && adminCount <= 1
                      ? "Last admin"
                      : removingUserId === member.user_id
                        ? "Removing..."
                        : "Remove"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ConfirmDialog
        open={pendingDeleteMember !== null}
        title="Remove project member"
        description={pendingDeleteMember ? `Remove ${pendingDeleteMember.username} from this project?` : undefined}
        confirmLabel="Remove"
        confirmLabelLoading="Removing..."
        loading={pendingDeleteMember ? removingUserId === pendingDeleteMember.user_id : false}
        onCancel={() => setPendingDeleteMember(null)}
        onConfirm={() => {
          if (!pendingDeleteMember) {
            return;
          }
          void onDelete(pendingDeleteMember);
        }}
      />
    </section>
  );
}
