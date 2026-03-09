"use client";

import { useEffect, useState } from "react";

import { ColumnResizeHandle, useResizableColumns } from "@/components/platform/column-resize";
import { DEFAULT_PAGE_SIZE_OPTIONS, PaginationControls } from "@/components/platform/pagination-controls";
import { listAudit, type ManagementAuditRow } from "@/lib/management-api/audit";
import { useWorkspaceContext } from "@/providers/WorkspaceContext";

export default function AuditPage() {
  const auditColumnKeys = ["index", "time", "method", "path", "status", "action", "target"] as const;
  const { projectId } = useWorkspaceContext();
  const [items, setItems] = useState<ManagementAuditRow[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [customPage, setCustomPage] = useState("1");
  const [action, setAction] = useState("");
  const [targetType, setTargetType] = useState("");
  const [targetId, setTargetId] = useState("");
  const [method, setMethod] = useState("");
  const [statusCode, setStatusCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { columnWidths, startResize, resetColumnWidth, resizingColumnIndex } = useResizableColumns([80, 180, 110, 300, 110, 160, 220], {
    storageKey: "table-columns-audit",
  });
  const tableWidth = Math.max(920, columnWidths.reduce((sum, width) => sum + width, 0));

  useEffect(() => {
    let cancelled = false;
    async function run() {
      setLoading(true);
      setError(null);
      try {
        const payload = await listAudit(projectId || null, {
          limit: pageSize,
          offset,
          action,
          targetType,
          targetId,
          method,
          statusCode: statusCode.trim() ? Number(statusCode) : null,
        });
        if (!cancelled) {
          setItems(payload.items);
          setTotal(payload.total);
          if (payload.total > 0 && offset >= payload.total) {
            const fallbackOffset = Math.max(0, (Math.ceil(payload.total / pageSize) - 1) * pageSize);
            if (fallbackOffset !== offset) {
              setOffset(fallbackOffset);
            }
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load audit logs");
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
  }, [action, method, offset, pageSize, projectId, statusCode, targetId, targetType]);

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
      <h2 className="text-xl font-semibold">Audit</h2>
      <p className="text-muted-foreground mt-2 text-sm">Project-scoped audit logs.</p>

      {!projectId ? <p className="mt-4 text-sm">No project selected. Showing latest global audit logs.</p> : null}
      {loading ? <p className="mt-4 text-sm">Loading...</p> : null}
      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

      <div className="mt-4 grid gap-2 rounded-lg border border-border/80 bg-card/70 p-3 sm:grid-cols-2 lg:grid-cols-5">
        <input
          className="h-9 rounded-md border border-border bg-background px-3 text-sm"
          placeholder="action"
          value={action}
          onChange={(event) => {
            setOffset(0);
            setAction(event.target.value);
          }}
        />
        <input
          className="h-9 rounded-md border border-border bg-background px-3 text-sm"
          placeholder="target type"
          value={targetType}
          onChange={(event) => {
            setOffset(0);
            setTargetType(event.target.value);
          }}
        />
        <input
          className="h-9 rounded-md border border-border bg-background px-3 text-sm"
          placeholder="target id"
          value={targetId}
          onChange={(event) => {
            setOffset(0);
            setTargetId(event.target.value);
          }}
        />
        <select
          className="h-9 rounded-md border border-border bg-background px-3 text-sm"
          value={method}
          onChange={(event) => {
            setOffset(0);
            setMethod(event.target.value);
          }}
        >
          <option value="">method (all)</option>
          <option value="GET">GET</option>
          <option value="POST">POST</option>
          <option value="PATCH">PATCH</option>
          <option value="DELETE">DELETE</option>
          <option value="PUT">PUT</option>
        </select>
        <input
          className="h-9 rounded-md border border-border bg-background px-3 text-sm"
          placeholder="status code"
          value={statusCode}
          onChange={(event) => {
            setOffset(0);
            setStatusCode(event.target.value);
          }}
        />
      </div>

      {!loading && !error && items.length > 0 ? (
        <div className="mt-4 overflow-x-auto rounded-lg border border-border/80 bg-card/70">
          <table className="min-w-[920px] table-fixed text-sm" style={{ width: `max(100%, ${tableWidth}px)` }}>
            <colgroup>
              {columnWidths.map((width, index) => (
                <col key={auditColumnKeys[index]} style={{ width }} />
              ))}
            </colgroup>
            <thead className="bg-muted/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="relative px-3 py-2">#<ColumnResizeHandle active={resizingColumnIndex === 0} onMouseDown={(event) => startResize(0, event)} onDoubleClick={() => resetColumnWidth(0)} /></th>
                <th className="relative px-3 py-2">Time<ColumnResizeHandle active={resizingColumnIndex === 1} onMouseDown={(event) => startResize(1, event)} onDoubleClick={() => resetColumnWidth(1)} /></th>
                <th className="relative px-3 py-2">Method<ColumnResizeHandle active={resizingColumnIndex === 2} onMouseDown={(event) => startResize(2, event)} onDoubleClick={() => resetColumnWidth(2)} /></th>
                <th className="relative px-3 py-2">Path<ColumnResizeHandle active={resizingColumnIndex === 3} onMouseDown={(event) => startResize(3, event)} onDoubleClick={() => resetColumnWidth(3)} /></th>
                <th className="relative px-3 py-2">Status<ColumnResizeHandle active={resizingColumnIndex === 4} onMouseDown={(event) => startResize(4, event)} onDoubleClick={() => resetColumnWidth(4)} /></th>
                <th className="relative px-3 py-2">Action<ColumnResizeHandle active={resizingColumnIndex === 5} onMouseDown={(event) => startResize(5, event)} onDoubleClick={() => resetColumnWidth(5)} /></th>
                <th className="relative px-3 py-2">Target<ColumnResizeHandle active={resizingColumnIndex === 6} onMouseDown={(event) => startResize(6, event)} onDoubleClick={() => resetColumnWidth(6)} /></th>
              </tr>
            </thead>
            <tbody>
              {items.map((row, index) => (
                <tr key={row.id} className="border-t">
                  <td className="px-3 py-2 font-mono text-xs text-muted-foreground">{offset + index + 1}</td>
                  <td className="px-3 py-2 text-xs text-muted-foreground">{new Date(row.created_at).toLocaleString()}</td>
                  <td className="px-3 py-2">{row.method}</td>
                  <td className="px-3 py-2 font-mono text-xs">{row.path}</td>
                  <td className="px-3 py-2">{row.status_code}</td>
                  <td className="px-3 py-2">{row.action ?? "-"}</td>
                  <td className="px-3 py-2 text-xs text-muted-foreground">
                    {row.target_type ? `${row.target_type}:${row.target_id ?? "-"}` : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {!loading && !error ? (
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
      ) : null}
    </section>
  );
}
