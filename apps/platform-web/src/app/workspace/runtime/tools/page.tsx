"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { ListSearch } from "@/components/platform/list-search";
import { PageStateEmpty, PageStateError, PageStateLoading } from "@/components/platform/page-state";
import { listRuntimeTools, refreshRuntimeTools, type RuntimeToolItem } from "@/lib/management-api/runtime";

export default function RuntimeToolsPage() {
  const [items, setItems] = useState<RuntimeToolItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);

  const refreshList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await listRuntimeTools();
      setItems(Array.isArray(payload.tools) ? payload.tools : []);
      setLastSyncedAt(payload.last_synced_at ?? null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Failed to load runtime tools");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshFromRuntime = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await refreshRuntimeTools();
      const payload = await listRuntimeTools();
      setItems(Array.isArray(payload.tools) ? payload.tools : []);
      setLastSyncedAt(payload.last_synced_at ?? null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Failed to refresh runtime tools");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshList();
  }, [refreshList]);

  const filteredItems = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return items;
    }
    return items.filter((item) => {
      return (
        item.name.toLowerCase().includes(normalized) ||
        item.source.toLowerCase().includes(normalized) ||
        item.description.toLowerCase().includes(normalized)
      );
    });
  }, [items, query]);

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold tracking-tight">Tools</h3>
          <p className="text-muted-foreground mt-1 text-sm">Available runtime tools, grouped in a searchable catalog.</p>
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
        placeholder="Search by name, source, or description"
        onValueChange={setSearchInput}
        onSearch={setQuery}
        onClear={() => setQuery("")}
      />

      {loading ? <PageStateLoading /> : null}
      {error ? <PageStateError message={error} /> : null}
      {!loading && !error && filteredItems.length === 0 ? (
        <PageStateEmpty message={items.length === 0 ? "No tools reported by runtime." : "No tools match your search."} />
      ) : null}

      {!loading && !error && filteredItems.length > 0 ? (
        <div className="mt-4 overflow-x-auto rounded-lg border border-border/80 bg-card/70">
          <table className="min-w-full text-sm">
            <thead className="bg-muted/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-2">#</th>
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Source</th>
                <th className="px-4 py-2">Description</th>
                <th className="px-4 py-2">Sync</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item, index) => (
                <tr key={`${item.source}:${item.name}`} className="border-t border-border/60 align-top transition-colors hover:bg-muted/30">
                  <td className="px-4 py-2 text-xs text-muted-foreground">{index + 1}</td>
                  <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{item.name}</td>
                  <td className="px-4 py-2 text-xs text-muted-foreground">{item.source}</td>
                  <td className="px-4 py-2">{item.description}</td>
                  <td className="px-4 py-2 text-xs text-muted-foreground">{item.sync_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
