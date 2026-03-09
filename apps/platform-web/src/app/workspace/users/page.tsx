"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ColumnResizeHandle, useResizableColumns } from "@/components/platform/column-resize";
import { ListSearch } from "@/components/platform/list-search";
import { DEFAULT_PAGE_SIZE_OPTIONS, PaginationControls } from "@/components/platform/pagination-controls";
import { listUsersPage, type ManagementUser, updateUser } from "@/lib/management-api/users";

export default function UsersPage() {
  const userColumnKeys = ["index", "username", "status", "superAdmin", "actions"] as const;
  const [items, setItems] = useState<ManagementUser[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [customPage, setCustomPage] = useState("1");
  const [query, setQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);
  const [status, setStatus] = useState<"active" | "disabled">("active");
  const [editingUserId, setEditingUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const { columnWidths, startResize, resetColumnWidth, resizingColumnIndex } = useResizableColumns([80, 220, 160, 160, 220], {
    storageKey: "table-columns-users",
  });
  const tableWidth = Math.max(520, columnWidths.reduce((sum, width) => sum + width, 0));

  const refreshUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await listUsersPage({ limit: pageSize, offset, query });
      setItems(payload.items);
      setTotal(payload.total);
      if (payload.total > 0 && offset >= payload.total) {
        const fallbackOffset = Math.max(0, (Math.ceil(payload.total / pageSize) - 1) * pageSize);
        if (fallbackOffset !== offset) {
          setOffset(fallbackOffset);
          return;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, [offset, pageSize, query]);

  useEffect(() => {
    void refreshUsers();
  }, [refreshUsers]);

  async function onUpdate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingUserId) {
      setError("Please select a user to edit");
      return;
    }

    setError(null);
    setNotice(null);
    try {
      const normalizedUsername = username.trim();
      const updated = await updateUser(editingUserId, {
        username: normalizedUsername,
        status,
        is_super_admin: isSuperAdmin,
        ...(password.trim() ? { password } : {}),
      });
      setNotice(`Updated user: ${updated.username}`);
      resetForm();
      await refreshUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user");
    }
  }

  function startEdit(item: ManagementUser) {
    setEditingUserId(item.id);
    setUsername(item.username);
    setPassword("");
    setIsSuperAdmin(item.is_super_admin);
    setStatus(item.status === "disabled" ? "disabled" : "active");
    setNotice(null);
    setError(null);
  }

  function resetForm() {
    setEditingUserId(null);
    setUsername("");
    setPassword("");
    setIsSuperAdmin(false);
    setStatus("active");
  }

  function applyCustomPage() {
    const parsed = Number(customPage);
    if (!Number.isFinite(parsed)) {
      return;
    }
    const normalizedPage = Math.max(1, Math.floor(parsed));
    setOffset((normalizedPage - 1) * pageSize);
    setCustomPage(String(normalizedPage));
  }

  const maxPage = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(maxPage, Math.floor(offset / pageSize) + 1);

  return (
    <section className="p-6">
      <h1 className="text-xl font-semibold">User Management</h1>
      <p className="text-muted-foreground mt-2 text-sm">System-level account management only.</p>

      <div className="mt-4">
        <Link
          href="/workspace/users/new"
          className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background"
        >
          Go to Create User
        </Link>
      </div>

      <ListSearch
        value={searchInput}
        placeholder="Search by username"
        onValueChange={setSearchInput}
        onSearch={(keyword) => {
          setOffset(0);
          setCustomPage("1");
          setQuery(keyword);
        }}
        onClear={() => {
          setQuery("");
          setOffset(0);
          setCustomPage("1");
        }}
      />

      {editingUserId ? (
        <form className="mt-4 grid gap-3 rounded-lg border border-border/80 bg-card/70 p-4" onSubmit={onUpdate}>
          <input
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="username"
            required
          />
          <input
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="new password (optional)"
          />
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
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={isSuperAdmin} onChange={(event) => setIsSuperAdmin(event.target.checked)} />
            Super admin
          </label>
          <button type="submit" className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background">
            Update user
          </button>
          <button
            type="button"
            className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm"
            onClick={resetForm}
          >
            Cancel edit
          </button>
        </form>
      ) : null}

      {loading ? <p className="mt-4 text-sm">Loading...</p> : null}
      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      {notice ? <p className="mt-4 text-sm text-emerald-700">{notice}</p> : null}

      <div className="mt-4 overflow-x-auto rounded-lg border border-border/80 bg-card/70">
        <table className="min-w-[520px] table-fixed text-sm" style={{ width: `max(100%, ${tableWidth}px)` }}>
          <colgroup>
            {columnWidths.map((width, index) => (
              <col key={userColumnKeys[index]} style={{ width }} />
            ))}
          </colgroup>
          <thead className="bg-muted/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="relative px-4 py-2">#<ColumnResizeHandle active={resizingColumnIndex === 0} onMouseDown={(event) => startResize(0, event)} onDoubleClick={() => resetColumnWidth(0)} /></th>
              <th className="relative px-4 py-2">Username<ColumnResizeHandle active={resizingColumnIndex === 1} onMouseDown={(event) => startResize(1, event)} onDoubleClick={() => resetColumnWidth(1)} /></th>
              <th className="relative px-4 py-2">Status<ColumnResizeHandle active={resizingColumnIndex === 2} onMouseDown={(event) => startResize(2, event)} onDoubleClick={() => resetColumnWidth(2)} /></th>
              <th className="relative px-4 py-2">Super Admin<ColumnResizeHandle active={resizingColumnIndex === 3} onMouseDown={(event) => startResize(3, event)} onDoubleClick={() => resetColumnWidth(3)} /></th>
              <th className="relative px-4 py-2">Actions<ColumnResizeHandle active={resizingColumnIndex === 4} onMouseDown={(event) => startResize(4, event)} onDoubleClick={() => resetColumnWidth(4)} /></th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={item.id} className="border-t">
                <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{offset + index + 1}</td>
                <td className="px-4 py-2 font-medium">{item.username}</td>
                <td className="px-4 py-2">{item.status}</td>
                <td className="px-4 py-2">{item.is_super_admin ? "yes" : "no"}</td>
                <td className="px-4 py-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      href={`/workspace/users/${item.id}`}
                      className="inline-flex h-7 items-center justify-center rounded-md border border-border bg-background px-2 text-xs"
                    >
                      Detail
                    </Link>
                    <button
                      type="button"
                      className="inline-flex h-7 items-center justify-center rounded-md border border-border bg-background px-2 text-xs"
                      onClick={() => startEdit(item)}
                    >
                      Edit
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <PaginationControls
        total={total}
        offset={offset}
        pageSize={pageSize}
        customPage={customPage}
        currentPage={currentPage}
        maxPage={maxPage}
        loading={loading}
        pageSizeOptions={DEFAULT_PAGE_SIZE_OPTIONS}
        onPageSizeChange={(next) => {
          setOffset(0);
          setPageSize(next);
          setCustomPage("1");
        }}
        onCustomPageChange={setCustomPage}
        onApplyCustomPage={applyCustomPage}
        onPrevious={() => setOffset((prev) => Math.max(0, prev - pageSize))}
        onNext={() => setOffset((prev) => prev + pageSize)}
        previousDisabled={loading || offset === 0}
        nextDisabled={loading || offset + pageSize >= total}
      />
    </section>
  );
}
