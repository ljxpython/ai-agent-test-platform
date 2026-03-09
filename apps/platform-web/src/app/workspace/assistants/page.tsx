"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ColumnResizeHandle, useResizableColumns } from "@/components/platform/column-resize";
import { ConfirmDialog } from "@/components/platform/confirm-dialog";
import { ListSearch } from "@/components/platform/list-search";
import { PageStateEmpty, PageStateError, PageStateLoading } from "@/components/platform/page-state";
import { DEFAULT_PAGE_SIZE_OPTIONS, PaginationControls } from "@/components/platform/pagination-controls";
import {
  deleteAssistant,
  listAssistantsPage,
  resyncAssistant,
  type ManagementAssistant,
  updateAssistant,
} from "@/lib/management-api/assistants";
import {
  listRuntimeModels,
  listRuntimeTools,
  type RuntimeModelItem,
  type RuntimeToolItem,
} from "@/lib/management-api/runtime";
import { useWorkspaceContext } from "@/providers/WorkspaceContext";

function stringifyJson(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2);
}

function parseObjectJson(raw: string, fieldName: string): Record<string, unknown> {
  const normalized = raw.trim();
  if (!normalized) {
    return {};
  }
  const parsed = JSON.parse(normalized);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error(`${fieldName} must be a JSON object`);
  }
  return parsed as Record<string, unknown>;
}

export default function AssistantsPage() {
  const { projectId } = useWorkspaceContext();
  const [items, setItems] = useState<ManagementAssistant[]>([]);
  const [total, setTotal] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [offset, setOffset] = useState(0);
  const [query, setQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [customPage, setCustomPage] = useState("1");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [resyncingId, setResyncingId] = useState<string | null>(null);

  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editGraphId, setEditGraphId] = useState("");
  const [editStatus, setEditStatus] = useState<"active" | "disabled">("active");
  const [editConfig, setEditConfig] = useState("{}");
  const [editContext, setEditContext] = useState("{}");
  const [editMetadata, setEditMetadata] = useState("{}");
  const [saving, setSaving] = useState(false);
  const [runtimeModels, setRuntimeModels] = useState<RuntimeModelItem[]>([]);
  const [runtimeTools, setRuntimeTools] = useState<RuntimeToolItem[]>([]);
  const [runtimeError, setRuntimeError] = useState<string | null>(null);
  const [runtimeLoading, setRuntimeLoading] = useState(false);
  const [runtimeModelId, setRuntimeModelId] = useState("");
  const [runtimeEnableTools, setRuntimeEnableTools] = useState(false);
  const [runtimeToolNames, setRuntimeToolNames] = useState<string[]>([]);

  const { columnWidths, startResize, resetColumnWidth, resizingColumnIndex } = useResizableColumns(
    [70, 180, 180, 220, 160, 220, 260],
    { storageKey: "table-columns-assistants" },
  );
  const tableWidth = Math.max(960, columnWidths.reduce((sum, width) => sum + width, 0));

  const currentPage = Math.floor(offset / pageSize) + 1;
  const maxPage = Math.max(1, Math.ceil(total / pageSize));

  const editingItem = useMemo(
    () => items.find((item) => item.id === editingId) ?? null,
    [items, editingId],
  );

  useEffect(() => {
    let cancelled = false;
    async function loadRuntimeCapabilities() {
      setRuntimeLoading(true);
      setRuntimeError(null);
      try {
        const [models, tools] = await Promise.all([
          listRuntimeModels().catch(() => null),
          listRuntimeTools().catch(() => null),
        ]);
        if (cancelled) {
          return;
        }
        setRuntimeModels(models && Array.isArray(models.models) ? models.models : []);
        setRuntimeTools(tools && Array.isArray(tools.tools) ? tools.tools : []);
      } catch (err) {
        if (!cancelled) {
          setRuntimeError(err instanceof Error ? err.message : "Failed to load runtime capabilities");
          setRuntimeModels([]);
          setRuntimeTools([]);
        }
      } finally {
        if (!cancelled) {
          setRuntimeLoading(false);
        }
      }
    }

    void loadRuntimeCapabilities();

    return () => {
      cancelled = true;
    };
  }, []);

  const refresh = useCallback(async () => {
    if (!projectId) {
      setItems([]);
      setTotal(0);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const payload = await listAssistantsPage(projectId, {
        limit: pageSize,
        offset,
        query,
      });
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
      setError(err instanceof Error ? err.message : "Failed to load assistants");
    } finally {
      setLoading(false);
    }
  }, [projectId, pageSize, offset, query]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    setCustomPage(String(currentPage));
  }, [currentPage]);

  useEffect(() => {
    if (!editingItem) {
      return;
    }
    setEditName(editingItem.name);
    setEditDescription(editingItem.description || "");
    setEditGraphId(editingItem.graph_id);
    setEditStatus(editingItem.status || "active");
    setEditConfig(stringifyJson(editingItem.config));
    setEditContext(stringifyJson(editingItem.context));
    setEditMetadata(stringifyJson(editingItem.metadata));
    try {
      const configValue = editingItem.config ?? {};
      const configurable =
        configValue && typeof configValue === "object" && !Array.isArray(configValue)
          ? (configValue as Record<string, unknown>).configurable
          : undefined;
      const cfg =
        configurable && typeof configurable === "object" && !Array.isArray(configurable)
          ? (configurable as Record<string, unknown>)
          : {};
      const modelId = typeof cfg.model_id === "string" ? cfg.model_id : "";
      const enableTools = typeof cfg.enable_tools === "boolean" ? cfg.enable_tools : false;
      const toolsArray = Array.isArray(cfg.tools)
        ? (cfg.tools as unknown[]).map((value) => String(value)).filter((value) => value.trim().length > 0)
        : [];
      setRuntimeModelId(modelId);
      setRuntimeEnableTools(enableTools);
      setRuntimeToolNames(toolsArray);
    } catch {
      setRuntimeModelId("");
      setRuntimeEnableTools(false);
      setRuntimeToolNames([]);
    }
  }, [editingItem]);

  async function onSaveEdit() {
    if (!editingId || !projectId) {
      return;
    }
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const nextConfig = parseObjectJson(editConfig, "config");
      const configurableRaw =
        nextConfig && typeof nextConfig.configurable === "object" && !Array.isArray(nextConfig.configurable)
          ? (nextConfig.configurable as Record<string, unknown>)
          : {};
      const configurable: Record<string, unknown> = { ...configurableRaw };

      const trimmedModelId = runtimeModelId.trim();
      if (trimmedModelId) {
        configurable.model_id = trimmedModelId;
      } else {
        delete configurable.model_id;
      }

      const cleanedTools = runtimeToolNames.map((name) => name.trim()).filter((name) => name.length > 0);
      if (runtimeEnableTools && cleanedTools.length > 0) {
        configurable.enable_tools = true;
        configurable.tools = cleanedTools;
      } else {
        delete configurable.enable_tools;
        delete configurable.tools;
      }

      if (Object.keys(configurable).length > 0) {
        nextConfig.configurable = configurable;
      } else {
        delete (nextConfig as Record<string, unknown>).configurable;
      }

      const payload = {
        name: editName.trim(),
        description: editDescription.trim(),
        graph_id: editGraphId.trim(),
        status: editStatus,
        config: nextConfig,
        context: parseObjectJson(editContext, "context"),
        metadata: parseObjectJson(editMetadata, "metadata"),
      } as const;
      await updateAssistant(editingId, payload, projectId);
      setNotice("Assistant updated.");
      setEditingId(null);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update assistant");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete() {
    if (!deletingId || !projectId) {
      return;
    }
    try {
      await deleteAssistant(deletingId, {
        deleteRuntime: true,
        projectId,
      });
      setNotice("Assistant deleted.");
      setDeletingId(null);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete assistant");
    }
  }

  async function onResync(item: ManagementAssistant) {
    if (!projectId) {
      return;
    }
    setResyncingId(item.id);
    setError(null);
    setNotice(null);
    try {
      await resyncAssistant(item.id, projectId);
      setNotice(`Assistant resynced: ${item.name}`);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resync assistant");
    } finally {
      setResyncingId(null);
    }
  }

  return (
    <section className="p-4 sm:p-6">
      <h2 className="text-xl font-semibold tracking-tight">Assistants</h2>
      <p className="text-muted-foreground mt-2 text-sm">Manage assistants for current project, including dynamic parameters.</p>
      {runtimeError ? <p className="mt-2 text-xs text-amber-700">{runtimeError}</p> : null}

      <div className="mt-4 flex flex-wrap gap-2">
        <Link
          href="/workspace/assistants/new"
          className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background"
        >
          Go to Create Assistant
        </Link>
      </div>

      <ListSearch
        value={searchInput}
        placeholder="Search by name / graph / assistant id"
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
      {notice ? <p className="mt-3 text-sm text-emerald-700">{notice}</p> : null}
      {!loading && !error && items.length === 0 ? <PageStateEmpty message="No assistants found." /> : null}

      {!loading && !error && items.length > 0 ? (
        <div className="mt-4 overflow-auto rounded-lg border border-border/70" style={{ width: "100%" }}>
          <table className="min-w-full text-sm" style={{ width: tableWidth }}>
            <thead className="bg-muted/60 text-left">
              <tr>
                {["#", "Name", "Graph", "LangGraph Assistant ID", "Status", "Sync", "Actions"].map((title, columnIndex) => (
                  <th
                    key={title}
                    className="relative border-b border-border px-3 py-2 font-medium text-foreground"
                    style={{ width: columnWidths[columnIndex] }}
                  >
                    <div className="truncate pr-3">{title}</div>
                    <ColumnResizeHandle
                      onMouseDown={(event) => startResize(columnIndex, event)}
                      onDoubleClick={() => resetColumnWidth(columnIndex)}
                      active={resizingColumnIndex === columnIndex}
                    />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={item.id} className="border-b border-border/60">
                  <td className="px-3 py-2 text-muted-foreground">{offset + index + 1}</td>
                  <td className="px-3 py-2">{item.name}</td>
                  <td className="px-3 py-2">{item.graph_id}</td>
                  <td className="px-3 py-2 font-mono text-xs">{item.langgraph_assistant_id}</td>
                  <td className="px-3 py-2">{item.status}</td>
                  <td className="px-3 py-2 text-xs text-muted-foreground">
                    <div>{item.sync_status}</div>
                    {item.last_synced_at ? <div>{new Date(item.last_synced_at).toLocaleString()}</div> : null}
                    {item.last_sync_error ? <div className="text-red-600">{item.last_sync_error}</div> : null}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-2">
                      <Link
                        href={`/workspace/assistants/${encodeURIComponent(item.id)}`}
                        className="inline-flex h-8 items-center rounded-md border border-border px-2 text-xs"
                      >
                        Detail
                      </Link>
                      <Link
                        href={`/workspace/chat?targetType=assistant&assistantId=${encodeURIComponent(item.langgraph_assistant_id)}${projectId ? `&projectId=${encodeURIComponent(projectId)}` : ""}`}
                        className="inline-flex h-8 items-center rounded-md border border-border px-2 text-xs"
                      >
                        Open in Chat
                      </Link>
                      <Link
                        href={`/workspace/threads?${new URLSearchParams({
                          ...(projectId ? { projectId } : {}),
                          threadAssistantId: item.langgraph_assistant_id,
                        }).toString()}`}
                        className="inline-flex h-8 items-center rounded-md border border-border px-2 text-xs"
                      >
                        View Threads
                      </Link>
                      <button
                        type="button"
                        className="inline-flex h-8 items-center rounded-md border border-border px-2 text-xs"
                        disabled={resyncingId === item.id}
                        onClick={() => void onResync(item)}
                      >
                        {resyncingId === item.id ? "Resyncing..." : "Resync"}
                      </button>
                      <button
                        type="button"
                        className="inline-flex h-8 items-center rounded-md border border-border px-2 text-xs"
                        onClick={() => {
                          setEditingId(item.id);
                          setError(null);
                          setNotice(null);
                        }}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="inline-flex h-8 items-center rounded-md border border-red-300 px-2 text-xs text-red-600"
                        onClick={() => setDeletingId(item.id)}
                      >
                        Delete
                      </button>
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
          onApplyCustomPage={() => {
            const parsed = Number(customPage);
            if (!Number.isFinite(parsed)) {
              setCustomPage(String(currentPage));
              return;
            }
            const clamped = Math.min(Math.max(1, Math.floor(parsed)), maxPage);
            setOffset((clamped - 1) * pageSize);
            setCustomPage(String(clamped));
          }}
          onPrevious={() => setOffset((prev) => Math.max(0, prev - pageSize))}
          onNext={() => setOffset((prev) => prev + pageSize)}
          previousDisabled={loading || offset === 0}
          nextDisabled={loading || offset + pageSize >= total}
        />
      ) : null}

      {editingItem ? (
        <div className="mt-6 grid gap-3 rounded-lg border border-border/80 bg-card/70 p-4">
          <h3 className="text-base font-semibold">Edit Assistant</h3>
          <label className="grid gap-1 text-xs font-medium text-muted-foreground">
            Name
            <input
              className="h-9 rounded-md border border-border bg-background px-3 text-sm"
              value={editName}
              onChange={(event) => setEditName(event.target.value)}
              disabled={saving}
            />
          </label>
          <label className="grid gap-1 text-xs font-medium text-muted-foreground">
            Graph ID
            <input
              className="h-9 rounded-md border border-border bg-background px-3 text-sm"
              value={editGraphId}
              onChange={(event) => setEditGraphId(event.target.value)}
              disabled={saving}
            />
          </label>
          <label className="grid gap-1 text-xs font-medium text-muted-foreground">
            Description
            <textarea
              className="min-h-20 rounded-md border border-border bg-background px-3 py-2 text-sm"
              value={editDescription}
              onChange={(event) => setEditDescription(event.target.value)}
              disabled={saving}
            />
          </label>
          <label className="grid gap-1 text-xs font-medium text-muted-foreground">
            Status
            <select
              className="h-9 rounded-md border border-border bg-background px-3 text-sm"
              value={editStatus}
              onChange={(event) => setEditStatus(event.target.value === "disabled" ? "disabled" : "active")}
              disabled={saving}
            >
              <option value="active">active</option>
              <option value="disabled">disabled</option>
            </select>
          </label>
          <div className="grid gap-2 rounded-md border border-border/80 bg-background/40 p-3">
            <p className="text-xs font-semibold text-muted-foreground">Runtime configuration (config.configurable)</p>
            {runtimeLoading ? (
              <p className="text-xs text-muted-foreground">Loading runtime capabilities...</p>
            ) : null}
            <div className="grid gap-1">
              <label className="text-xs font-medium text-muted-foreground" htmlFor="assistant-runtime-model">
                Model group
              </label>
              <select
                id="assistant-runtime-model"
                className="h-9 rounded-md border border-border bg-background px-3 text-sm"
                value={runtimeModelId}
                onChange={(event) => setRuntimeModelId(event.target.value)}
                disabled={saving}
              >
                <option value="">Use runtime default</option>
                {runtimeModels.map((item) => (
                  <option key={item.model_id} value={item.model_id}>
                    {item.display_name}
                    {item.is_default ? " (default)" : ""}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input
                id="assistant-runtime-enable-tools"
                type="checkbox"
                className="h-4 w-4"
                checked={runtimeEnableTools}
                onChange={(event) => setRuntimeEnableTools(event.target.checked)}
                disabled={saving}
              />
              <label htmlFor="assistant-runtime-enable-tools" className="text-xs">
                Enable tools for this assistant
              </label>
            </div>
          <div className="grid gap-1">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-medium text-muted-foreground">Tools</p>
              <div className="flex gap-1">
                <button
                  type="button"
                  className="inline-flex items-center rounded border border-border bg-background px-2 py-0.5 text-[11px]"
                  onClick={() => {
                    const names = runtimeTools.map((tool) => tool.name).filter((name) => name.trim().length > 0);
                    setRuntimeToolNames(names);
                  }}
                  disabled={saving || !runtimeEnableTools || runtimeTools.length === 0}
                >
                  Select all
                </button>
                <button
                  type="button"
                  className="inline-flex items-center rounded border border-border bg-background px-2 py-0.5 text-[11px]"
                  onClick={() => setRuntimeToolNames([])}
                  disabled={saving || runtimeToolNames.length === 0}
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="h-40 overflow-auto rounded-md border border-border bg-background/60 p-2 text-xs">
                {runtimeTools.length === 0 ? (
                  <p className="text-muted-foreground">No tools reported by runtime.</p>
                ) : (
                  runtimeTools.map((tool) => {
                    const checked = runtimeToolNames.includes(tool.name);
                    return (
                      <label key={tool.name} className="flex items-center gap-2 py-1">
                        <input
                          type="checkbox"
                          className="h-3 w-3"
                          checked={checked}
                          onChange={() => {
                            setRuntimeToolNames((prev) => {
                              if (prev.includes(tool.name)) {
                                return prev.filter((name) => name !== tool.name);
                              }
                              return [...prev, tool.name];
                            });
                          }}
                          disabled={saving || !runtimeEnableTools}
                        />
                        <span className="font-mono text-[11px]">{tool.name}</span>
                        <span className="text-[11px] text-muted-foreground">({tool.source})</span>
                      </label>
                    );
                  })
                )}
              </div>
            </div>
            <p className="text-[11px] text-muted-foreground">
              Fields are written into <code>config.configurable.model_id / enable_tools / tools</code> when saving.
            </p>
          </div>
          <label className="grid gap-1 text-xs font-medium text-muted-foreground">
            Config (JSON object)
            <textarea
              className="min-h-24 rounded-md border border-border bg-background px-3 py-2 font-mono text-xs"
              value={editConfig}
              onChange={(event) => setEditConfig(event.target.value)}
              disabled={saving}
            />
          </label>
          <label className="grid gap-1 text-xs font-medium text-muted-foreground">
            Context (JSON object)
            <textarea
              className="min-h-24 rounded-md border border-border bg-background px-3 py-2 font-mono text-xs"
              value={editContext}
              onChange={(event) => setEditContext(event.target.value)}
              disabled={saving}
            />
          </label>
          <label className="grid gap-1 text-xs font-medium text-muted-foreground">
            Metadata (JSON object)
            <textarea
              className="min-h-24 rounded-md border border-border bg-background px-3 py-2 font-mono text-xs"
              value={editMetadata}
              onChange={(event) => setEditMetadata(event.target.value)}
              disabled={saving}
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background disabled:opacity-50"
              onClick={() => void onSaveEdit()}
              disabled={saving}
            >
              {saving ? "Saving..." : "Save"}
            </button>
            <button
              type="button"
              className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm"
              onClick={() => setEditingId(null)}
              disabled={saving}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : null}

      <ConfirmDialog
        open={Boolean(deletingId)}
        title="Delete assistant"
        description={
          <span>
            This removes assistant from platform metadata and deletes runtime assistant.
          </span>
        }
        confirmLabel="Delete"
        cancelLabel="Cancel"
        onConfirm={() => void onDelete()}
        onCancel={() => {
          setDeletingId(null);
        }}
      />
    </section>
  );
}
