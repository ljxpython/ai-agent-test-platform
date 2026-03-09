"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ColumnResizeHandle, useResizableColumns } from "@/components/platform/column-resize";
import { ListSearch } from "@/components/platform/list-search";
import { Button } from "@/components/ui/button";
import {
  PageStateEmpty,
  PageStateError,
  PageStateLoading,
} from "@/components/platform/page-state";
import {
  DEFAULT_PAGE_SIZE_OPTIONS,
  PaginationControls,
} from "@/components/platform/pagination-controls";
import {
  refreshGraphsCatalog,
  listGraphsPage,
  type ManagementGraph,
} from "@/lib/management-api/graphs";
import { useWorkspaceContext } from "@/providers/WorkspaceContext";

export default function GraphsPage() {
  const router = useRouter();
  const { projectId } = useWorkspaceContext();
  const [items, setItems] = useState<ManagementGraph[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [customPage, setCustomPage] = useState("1");
  const [query, setQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);

  const graphColumnKeys = ["index", "graph_id", "description", "sync", "actions"] as const;
  const { columnWidths, startResize, resetColumnWidth, resizingColumnIndex } =
    useResizableColumns([80, 320, 300, 180, 220], {
      storageKey: "table-columns-graphs",
    });
  const tableWidth = Math.max(
    760,
    columnWidths.reduce((sum, width) => sum + width, 0),
  );

  const refreshList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await listGraphsPage(projectId, {
        limit: pageSize,
        offset,
        query,
      });
      setItems(payload.items);
      setTotal(payload.total);
      setLastSyncedAt(payload.last_synced_at ?? null);
      if (payload.total > 0 && offset >= payload.total) {
        const fallbackOffset = Math.max(
          0,
          (Math.ceil(payload.total / pageSize) - 1) * pageSize,
        );
        if (fallbackOffset !== offset) {
          setOffset(fallbackOffset);
        }
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Failed to load graphs",
      );
    } finally {
      setLoading(false);
    }
  }, [offset, pageSize, projectId, query]);

  const refreshFromRuntime = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await refreshGraphsCatalog(projectId || undefined);
      const payload = await listGraphsPage(projectId, {
        limit: pageSize,
        offset,
        query,
      });
      setItems(payload.items);
      setTotal(payload.total);
      setLastSyncedAt(payload.last_synced_at ?? null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Failed to refresh graphs");
    } finally {
      setLoading(false);
    }
  }, [offset, pageSize, projectId, query]);

  useEffect(() => {
    void refreshList();
  }, [refreshList]);

  function applyCustomPage() {
    const parsed = Number(customPage);
    if (!Number.isFinite(parsed)) {
      return;
    }
    const normalizedPage = Math.max(1, Math.floor(parsed));
    setOffset((normalizedPage - 1) * pageSize);
    setCustomPage(String(normalizedPage));
  }

  function openChatWithGraph(graphId: string) {
    const params = new URLSearchParams();
    if (projectId) {
      params.set("projectId", projectId);
    }
    params.set("targetType", "graph");
    params.set("assistantId", graphId);
    router.push(`/workspace/chat?${params.toString()}`);
  }

  const maxPage = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(maxPage, Math.floor(offset / pageSize) + 1);

  return (
    <section className="p-4 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">Graphs</h2>
          <p className="text-muted-foreground mt-2 text-sm">Graph catalog for current runtime catalog.</p>
          <p className="text-muted-foreground mt-1 text-xs">
            Last synced: {lastSyncedAt ? new Date(lastSyncedAt).toLocaleString() : "Never"}
          </p>
        </div>
        <Button variant="outline" onClick={() => void refreshFromRuntime()} disabled={loading}>
          Refresh
        </Button>
      </div>

      <ListSearch
        value={searchInput}
        placeholder="Search by graph id or description"
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

      {loading ? <PageStateLoading /> : null}
      {error ? <PageStateError message={error} /> : null}
      {!loading && !error && items.length === 0 ? (
        <PageStateEmpty message="No graphs found." />
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <div className="mt-4 overflow-x-auto rounded-lg border border-border/80 bg-card/70">
          <table
            className="min-w-[760px] table-fixed text-sm"
            style={{ width: `max(100%, ${tableWidth}px)` }}
          >
            <colgroup>
              {columnWidths.map((width, index) => (
                <col key={graphColumnKeys[index]} style={{ width }} />
              ))}
            </colgroup>
            <thead className="bg-muted/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="relative px-4 py-2">
                  #
                  <ColumnResizeHandle
                    active={resizingColumnIndex === 0}
                    onMouseDown={(event) => startResize(0, event)}
                    onDoubleClick={() => resetColumnWidth(0)}
                  />
                </th>
                <th className="relative px-4 py-2">
                  Graph ID
                  <ColumnResizeHandle
                    active={resizingColumnIndex === 1}
                    onMouseDown={(event) => startResize(1, event)}
                    onDoubleClick={() => resetColumnWidth(1)}
                  />
                </th>
                <th className="relative px-4 py-2">
                  Description
                  <ColumnResizeHandle
                    active={resizingColumnIndex === 2}
                    onMouseDown={(event) => startResize(2, event)}
                    onDoubleClick={() => resetColumnWidth(2)}
                  />
                </th>
                <th className="relative px-4 py-2">
                  Sync
                  <ColumnResizeHandle
                    active={resizingColumnIndex === 3}
                    onMouseDown={(event) => startResize(3, event)}
                    onDoubleClick={() => resetColumnWidth(3)}
                  />
                </th>
                <th className="relative px-4 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr
                  key={item.graph_id}
                  className="border-t transition-colors hover:bg-muted/30"
                >
                  <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                    {offset + index + 1}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                    {item.graph_id}
                  </td>
                  <td className="max-w-xl px-4 py-2 text-sm text-muted-foreground">
                    {item.description?.trim() ? item.description : "-"}
                  </td>
                  <td className="px-4 py-2 text-xs text-muted-foreground">
                    <div>{item.sync_status}</div>
                    {item.last_synced_at ? <div>{new Date(item.last_synced_at).toLocaleString()}</div> : null}
                  </td>
                  <td className="px-4 py-2">
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        className="inline-flex h-8 items-center justify-center rounded-md border border-border bg-background px-2 text-xs"
                        onClick={() => openChatWithGraph(item.graph_id)}
                      >
                        Open in Chat
                      </button>
                      <Link
                        href={`/workspace/threads?${new URLSearchParams({
                          ...(projectId ? { projectId } : {}),
                          threadGraphId: item.graph_id,
                        }).toString()}`}
                        className="inline-flex h-8 items-center justify-center rounded-md border border-border bg-background px-2 text-xs"
                      >
                        View Threads
                      </Link>
                    </div>
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
