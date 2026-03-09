"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  getAssistant,
  getAssistantParameterSchema,
  resyncAssistant,
  type ManagementAssistant,
  updateAssistant,
} from "@/lib/management-api/assistants";
import { useWorkspaceContext } from "@/providers/WorkspaceContext";

type SchemaProperty = {
  type?: string;
  required?: boolean;
};

type SchemaSection = {
  key?: string;
  properties?: Record<string, SchemaProperty>;
};

type ParameterSchemaResponse = {
  graph_id?: string;
  schema_version?: string;
  sections?: SchemaSection[];
};

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

export default function AssistantDetailPage() {
  const params = useParams<{ assistantId: string }>();
  const router = useRouter();
  const { projectId } = useWorkspaceContext();
  const assistantId = String(params.assistantId || "");
  const [item, setItem] = useState<ManagementAssistant | null>(null);
  const [schema, setSchema] = useState<ParameterSchemaResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [resyncing, setResyncing] = useState(false);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editGraphId, setEditGraphId] = useState("");
  const [editStatus, setEditStatus] = useState<"active" | "disabled">("active");
  const [editConfig, setEditConfig] = useState("{}");
  const [editContext, setEditContext] = useState("{}");
  const [editMetadata, setEditMetadata] = useState("{}");
  const [configFields, setConfigFields] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!assistantId) {
      return;
    }
    setLoading(true);
    setError(null);
    setNotice(null);
    void getAssistant(assistantId, projectId || undefined)
      .then((payload) => {
        setItem(payload);
        setEditName(payload.name);
        setEditDescription(payload.description || "");
        setEditGraphId(payload.graph_id);
        setEditStatus(payload.status === "disabled" ? "disabled" : "active");
        setEditConfig(stringifyJson(payload.config));
        setEditContext(stringifyJson(payload.context));
        setEditMetadata(stringifyJson(payload.metadata));
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load assistant"))
      .finally(() => setLoading(false));
  }, [assistantId, projectId]);

  useEffect(() => {
    const normalizedGraphId = editGraphId.trim();
    if (!normalizedGraphId) {
      setSchema(null);
      return;
    }
    setSchemaLoading(true);
    void getAssistantParameterSchema(normalizedGraphId, projectId || undefined)
      .then((payload) => setSchema(payload as ParameterSchemaResponse))
      .catch(() => setSchema(null))
      .finally(() => setSchemaLoading(false));
  }, [editGraphId, projectId]);

  const configPropertyDefs = useMemo(() => {
    const sections = Array.isArray(schema?.sections) ? schema.sections : [];
    const configSection = sections.find((section) => section?.key === "config");
    const properties = configSection?.properties;
    if (!properties || typeof properties !== "object") {
      return [] as Array<{ key: string; type: string; required: boolean }>;
    }
    return Object.entries(properties).map(([key, value]) => ({
      key,
      type: typeof value?.type === "string" ? value.type : "string",
      required: Boolean(value?.required),
    }));
  }, [schema]);

  useEffect(() => {
    const baseConfig = parseObjectJson(editConfig, "config");
    const nextFields: Record<string, string> = {};
    for (const field of configPropertyDefs) {
      const rawValue = baseConfig[field.key];
      nextFields[field.key] =
        rawValue === null || rawValue === undefined
          ? ""
          : typeof rawValue === "string"
            ? rawValue
            : String(rawValue);
    }
    setConfigFields(nextFields);
  }, [editConfig, configPropertyDefs]);

  function applyConfigFieldValue(key: string, value: string, valueType: string) {
    setConfigFields((prev) => ({ ...prev, [key]: value }));
    const currentConfig = parseObjectJson(editConfig, "config");
    if (!value.trim()) {
      delete currentConfig[key];
      setEditConfig(JSON.stringify(currentConfig, null, 2));
      return;
    }
    if (valueType === "number") {
      const parsed = Number(value);
      if (!Number.isFinite(parsed)) {
        return;
      }
      currentConfig[key] = parsed;
      setEditConfig(JSON.stringify(currentConfig, null, 2));
      return;
    }
    if (valueType === "boolean") {
      currentConfig[key] = value === "true";
      setEditConfig(JSON.stringify(currentConfig, null, 2));
      return;
    }
    currentConfig[key] = value;
    setEditConfig(JSON.stringify(currentConfig, null, 2));
  }

  async function onSave() {
    if (!assistantId || !projectId) {
      return;
    }
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await updateAssistant(
        assistantId,
        {
          name: editName.trim(),
          description: editDescription.trim(),
          graph_id: editGraphId.trim(),
          status: editStatus,
          config: parseObjectJson(editConfig, "config"),
          context: parseObjectJson(editContext, "context"),
          metadata: parseObjectJson(editMetadata, "metadata"),
        },
        projectId,
      );
      setItem(updated);
      setNotice("Assistant updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update assistant");
    } finally {
      setSaving(false);
    }
  }

  async function onResync() {
    if (!assistantId || !projectId) {
      return;
    }
    setResyncing(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await resyncAssistant(assistantId, projectId);
      setItem(updated);
      setEditName(updated.name);
      setEditDescription(updated.description || "");
      setEditGraphId(updated.graph_id);
      setEditStatus(updated.status === "disabled" ? "disabled" : "active");
      setEditConfig(stringifyJson(updated.config));
      setEditContext(stringifyJson(updated.context));
      setEditMetadata(stringifyJson(updated.metadata));
      setNotice("Assistant resynced.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resync assistant");
    } finally {
      setResyncing(false);
    }
  }

  return (
    <section className="p-4 sm:p-6">
      <h2 className="text-xl font-semibold tracking-tight">Assistant Detail</h2>
      <p className="text-muted-foreground mt-2 text-sm">View assistant profile and dynamic parameters.</p>

      {loading ? <p className="mt-4 text-sm">Loading...</p> : null}
      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      {notice ? <p className="mt-4 text-sm text-emerald-700">{notice}</p> : null}

      {item ? (
        <div className="mt-4 grid gap-3 rounded-lg border border-border/80 bg-card/70 p-4">
          <p className="text-sm"><span className="text-muted-foreground">ID:</span> <code>{item.id}</code></p>
          <p className="text-sm"><span className="text-muted-foreground">LangGraph Assistant ID:</span> <code>{item.langgraph_assistant_id}</code></p>
          <p className="text-sm"><span className="text-muted-foreground">Sync:</span> <code>{item.sync_status}</code></p>
          {item.last_synced_at ? <p className="text-sm"><span className="text-muted-foreground">Last synced:</span> <code>{new Date(item.last_synced_at).toLocaleString()}</code></p> : null}
          {item.last_sync_error ? <p className="text-sm text-red-600">{item.last_sync_error}</p> : null}

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
            Description
            <textarea
              className="min-h-20 rounded-md border border-border bg-background px-3 py-2 text-sm"
              value={editDescription}
              onChange={(event) => setEditDescription(event.target.value)}
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

          <div className="grid gap-2 rounded-md border border-border/80 bg-background/50 p-3">
            <p className="text-xs font-medium text-muted-foreground">
              Parameter Schema {schemaLoading ? "(loading...)" : ""}
            </p>
            <p className="text-xs text-muted-foreground">
              graph={schema?.graph_id || editGraphId.trim() || "-"} · version={schema?.schema_version || "v1"}
            </p>
          </div>

          {configPropertyDefs.length > 0 ? (
            <div className="grid gap-2 rounded-md border border-border/80 bg-background/50 p-3">
              <p className="text-xs font-medium text-muted-foreground">Config Fields (schema-driven)</p>
              {configPropertyDefs.map((field) => (
                <label key={field.key} className="grid gap-1 text-xs font-medium text-muted-foreground">
                  {field.key}
                  <input
                    className="h-9 rounded-md border border-border bg-background px-3 text-sm"
                    value={configFields[field.key] ?? ""}
                    onChange={(event) => applyConfigFieldValue(field.key, event.target.value, field.type)}
                    placeholder={field.type}
                    required={field.required}
                    disabled={saving}
                  />
                </label>
              ))}
            </div>
          ) : null}

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
              onClick={() => void onSave()}
              disabled={saving}
            >
              {saving ? "Saving..." : "Save"}
            </button>
            <button
              type="button"
              className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm disabled:opacity-50"
              onClick={() => void onResync()}
              disabled={resyncing}
            >
              {resyncing ? "Resyncing..." : "Resync"}
            </button>
          </div>
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">
        {item ? (
          <button
            type="button"
            className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm"
            onClick={() => {
              const params = new URLSearchParams();
              params.set("targetType", "assistant");
              params.set("assistantId", item.langgraph_assistant_id);
              if (projectId) {
                params.set("projectId", projectId);
              }
              router.push(`/workspace/chat?${params.toString()}`);
            }}
          >
            Open in Chat
          </button>
        ) : null}
        <Link
          href="/workspace/assistants"
          className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm"
        >
          Back to Assistants
        </Link>
      </div>
    </section>
  );
}
