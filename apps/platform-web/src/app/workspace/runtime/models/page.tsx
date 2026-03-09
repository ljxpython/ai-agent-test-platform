"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { ListSearch } from "@/components/platform/list-search";
import { PageStateEmpty, PageStateError, PageStateLoading } from "@/components/platform/page-state";
import { listRuntimeModels, refreshRuntimeModels, type RuntimeModelItem } from "@/lib/management-api/runtime";

export default function RuntimeModelsPage() {
  const [items, setItems] = useState<RuntimeModelItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);

  const refreshList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await listRuntimeModels();
      setItems(Array.isArray(payload.models) ? payload.models : []);
      setLastSyncedAt(payload.last_synced_at ?? null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Failed to load runtime models");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshFromRuntime = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await refreshRuntimeModels();
      const payload = await listRuntimeModels();
      setItems(Array.isArray(payload.models) ? payload.models : []);
      setLastSyncedAt(payload.last_synced_at ?? null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Failed to refresh runtime models");
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
      return item.model_id.toLowerCase().includes(normalized) || item.display_name.toLowerCase().includes(normalized);
    });
  }, [items, query]);

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold tracking-tight">Models</h3>
          <p className="text-muted-foreground mt-1 text-sm">Available runtime models and the current default option.</p>
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
        placeholder="Search by model id or display name"
        onValueChange={setSearchInput}
        onSearch={setQuery}
        onClear={() => setQuery("")}
      />

      {loading ? <PageStateLoading /> : null}
      {error ? <PageStateError message={error} /> : null}
      {!loading && !error && filteredItems.length === 0 ? (
        <PageStateEmpty message={items.length === 0 ? "No models reported by runtime." : "No models match your search."} />
      ) : null}

      {!loading && !error && filteredItems.length > 0 ? (
        <div className="mt-4 overflow-x-auto rounded-lg border border-border/80 bg-card/70">
          <table className="min-w-full text-sm">
            <thead className="bg-muted/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-2">#</th>
                <th className="px-4 py-2">Model ID</th>
                <th className="px-4 py-2">Display Name</th>
                <th className="px-4 py-2">Default</th>
                <th className="px-4 py-2">Sync</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item, index) => (
                <tr key={item.model_id} className="border-t border-border/60 transition-colors hover:bg-muted/30">
                  <td className="px-4 py-2 text-xs text-muted-foreground">{index + 1}</td>
                  <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{item.model_id}</td>
                  <td className="px-4 py-2">{item.display_name}</td>
                  <td className="px-4 py-2 text-xs">{item.is_default ? "Yes" : ""}</td>
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
