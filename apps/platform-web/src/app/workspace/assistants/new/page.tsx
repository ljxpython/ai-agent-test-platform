"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { createAssistant, getAssistantParameterSchema } from "@/lib/management-api/assistants";
import { listGraphsPage, type ManagementGraph } from "@/lib/management-api/graphs";
import { listRuntimeModels, listRuntimeTools, type RuntimeModelItem, type RuntimeToolItem } from "@/lib/management-api/runtime";
import { useWorkspaceContext } from "@/providers/WorkspaceContext";

type SchemaProperty = {
  type?: string;
  required?: boolean;
};

type SchemaSection = {
  key?: string;
  title?: string;
  type?: string;
  properties?: Record<string, SchemaProperty>;
};

type ParameterSchemaResponse = {
  graph_id?: string;
  schema_version?: string;
  sections?: SchemaSection[];
};

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

export default function CreateAssistantPage() {
  const router = useRouter();
  const { projectId } = useWorkspaceContext();
  const [graphId, setGraphId] = useState("assistant");
  const [graphOptions, setGraphOptions] = useState<ManagementGraph[]>([]);
  const [graphLoading, setGraphLoading] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [assistantId, setAssistantId] = useState("");
  const [config, setConfig] = useState("{}");
  const [context, setContext] = useState("{}");
  const [metadata, setMetadata] = useState("{}");
  const [schema, setSchema] = useState<ParameterSchemaResponse | null>(null);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [schemaError, setSchemaError] = useState<string | null>(null);
  const [configFields, setConfigFields] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [runtimeModels, setRuntimeModels] = useState<RuntimeModelItem[]>([]);
  const [runtimeTools, setRuntimeTools] = useState<RuntimeToolItem[]>([]);
  const [runtimeLoading, setRuntimeLoading] = useState(false);
  const [runtimeError, setRuntimeError] = useState<string | null>(null);
  const [runtimeModelId, setRuntimeModelId] = useState("");
  const [runtimeEnableTools, setRuntimeEnableTools] = useState(false);
  const [runtimeToolNames, setRuntimeToolNames] = useState<string[]>([]);

  const configPropertyDefs = useMemo(() => {
    const sections = Array.isArray(schema?.sections) ? schema?.sections : [];
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

  const requestBodyPreview = useMemo(() => {
    const normalizedGraphId = graphId.trim();
    const normalizedName = name.trim();
    const payload: Record<string, unknown> = {};
    if (normalizedGraphId) {
      payload.graph_id = normalizedGraphId;
    }
    if (normalizedName) {
      payload.name = normalizedName;
    }
    if (description.trim()) {
      payload.description = description.trim();
    }
    if (assistantId.trim()) {
      payload.assistant_id = assistantId.trim();
    }

    const configObject = parseObjectJson(config, "config");
    const configurableRaw =
      configObject && typeof configObject.configurable === "object" && !Array.isArray(configObject.configurable)
        ? (configObject.configurable as Record<string, unknown>)
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
      configObject.configurable = configurable;
    } else {
      delete (configObject as Record<string, unknown>).configurable;
    }

    if (Object.keys(configObject).length > 0) {
      payload.config = configObject;
    }

    const contextObject = parseObjectJson(context, "context");
    if (Object.keys(contextObject).length > 0) {
      payload.context = contextObject;
    }

    const metadataObject = parseObjectJson(metadata, "metadata");
    if (Object.keys(metadataObject).length > 0) {
      payload.metadata = metadataObject;
    }

    return payload;
  }, [assistantId, config, context, description, graphId, metadata, name, runtimeModelId, runtimeEnableTools, runtimeToolNames]);

  useEffect(() => {
    if (!projectId) {
      setGraphOptions([]);
      return;
    }
    setGraphLoading(true);
    void listGraphsPage(projectId, {
      limit: 30,
      offset: 0,
      query: graphId.trim() || undefined,
    })
      .then((payload) => {
        const next = payload.items
          .filter(
            (item): item is ManagementGraph =>
              typeof item.graph_id === "string" && item.graph_id.trim().length > 0,
          )
        setGraphOptions(next);
      })
      .catch(() => setGraphOptions([]))
      .finally(() => setGraphLoading(false));
  }, [graphId, projectId]);

  useEffect(() => {
    let cancelled = false;

    async function loadRuntime() {
      setRuntimeLoading(true);
      setRuntimeError(null);
      try {
        const [modelsResponse, toolsResponse] = await Promise.all([
          listRuntimeModels().catch(() => null),
          listRuntimeTools().catch(() => null),
        ]);
        if (cancelled) {
          return;
        }
        setRuntimeModels(modelsResponse && Array.isArray(modelsResponse.models) ? modelsResponse.models : []);
        setRuntimeTools(toolsResponse && Array.isArray(toolsResponse.tools) ? toolsResponse.tools : []);
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

    void loadRuntime();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const normalizedGraphId = graphId.trim();
    if (!normalizedGraphId) {
      setSchema(null);
      setSchemaError(null);
      return;
    }

    setSchemaLoading(true);
    setSchemaError(null);
    void getAssistantParameterSchema(normalizedGraphId, projectId || undefined)
      .then((payload) => {
        const normalized = payload as ParameterSchemaResponse;
        setSchema(normalized);
      })
      .catch((err) => {
        setSchema(null);
        setSchemaError(err instanceof Error ? err.message : "Failed to load parameter schema");
      })
      .finally(() => setSchemaLoading(false));
  }, [graphId, projectId]);

  useEffect(() => {
    const baseConfig = parseObjectJson(config, "config");
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
  }, [config, configPropertyDefs]);

  function applyConfigFieldValue(key: string, value: string, valueType: string) {
    setConfigFields((prev) => ({ ...prev, [key]: value }));
    const currentConfig = parseObjectJson(config, "config");
    if (!value.trim()) {
      delete currentConfig[key];
      setConfig(JSON.stringify(currentConfig, null, 2));
      return;
    }

    if (valueType === "number") {
      const parsed = Number(value);
      if (!Number.isFinite(parsed)) {
        return;
      }
      currentConfig[key] = parsed;
      setConfig(JSON.stringify(currentConfig, null, 2));
      return;
    }

    if (valueType === "boolean") {
      currentConfig[key] = value === "true";
      setConfig(JSON.stringify(currentConfig, null, 2));
      return;
    }

    currentConfig[key] = value;
    setConfig(JSON.stringify(currentConfig, null, 2));
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!projectId) {
      setError("Please select a project first.");
      return;
    }
    const normalizedName = name.trim();
    const normalizedGraphId = graphId.trim();
    if (!normalizedName || !normalizedGraphId) {
      setError("Name and graph id are required.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const configObject = parseObjectJson(config, "config");
      const contextObject = parseObjectJson(context, "context");
      const metadataObject = parseObjectJson(metadata, "metadata");
      const configurableRaw =
        configObject && typeof configObject.configurable === "object" && !Array.isArray(configObject.configurable)
          ? (configObject.configurable as Record<string, unknown>)
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
        configObject.configurable = configurable;
      } else {
        delete (configObject as Record<string, unknown>).configurable;
      }

      const payload: {
        graph_id: string;
        name: string;
        description?: string;
        assistant_id?: string;
        config?: Record<string, unknown>;
        context?: Record<string, unknown>;
        metadata?: Record<string, unknown>;
      } = {
        graph_id: normalizedGraphId,
        name: normalizedName,
      };
      if (description.trim()) {
        payload.description = description.trim();
      }
      if (assistantId.trim()) {
        payload.assistant_id = assistantId.trim();
      }
      if (Object.keys(configObject).length > 0) {
        payload.config = configObject;
      }
      if (Object.keys(contextObject).length > 0) {
        payload.context = contextObject;
      }
      if (Object.keys(metadataObject).length > 0) {
        payload.metadata = metadataObject;
      }

      const created = await createAssistant(projectId, {
        ...payload,
      });
      setNotice(`Created assistant: ${created.name}`);
      router.replace("/workspace/assistants");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create assistant");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="p-4 sm:p-6">
      <h2 className="text-xl font-semibold tracking-tight">Create Assistant</h2>
      <p className="text-muted-foreground mt-2 text-sm">Create a project-scoped assistant with dynamic parameters.</p>
      {runtimeError ? <p className="mt-2 text-xs text-amber-700">{runtimeError}</p> : null}

      <form className="mt-4 grid gap-3 rounded-lg border border-border/80 bg-card/70 p-4" onSubmit={onSubmit}>
        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Graph ID
          <input
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            list="assistant-graph-options"
            value={graphId}
            onChange={(event) => setGraphId(event.target.value)}
            placeholder={graphLoading ? "Searching graphs..." : "Type to fuzzy search, or pick from dropdown"}
            disabled={submitting}
            required
          />
          <datalist id="assistant-graph-options">
            {graphOptions.map((option) => (
              <option key={option.graph_id} value={option.graph_id} label={option.description?.trim() ? `${option.graph_id} — ${option.description}` : option.graph_id}>
                {option.description?.trim() ? `${option.graph_id} — ${option.description}` : option.graph_id}
              </option>
            ))}
          </datalist>
        </label>

        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Name
          <input
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            value={name}
            onChange={(event) => setName(event.target.value)}
            disabled={submitting}
            required
          />
        </label>

        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Description
          <textarea
            className="min-h-20 rounded-md border border-border bg-background px-3 py-2 text-sm"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            disabled={submitting}
          />
        </label>

        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Optional Assistant ID
          <input
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            value={assistantId}
            onChange={(event) => setAssistantId(event.target.value)}
            disabled={submitting}
            placeholder="If empty, upstream generates one"
          />
        </label>

        <div className="grid gap-2 rounded-md border border-border/80 bg-background/50 p-3">
          <p className="text-xs font-medium text-muted-foreground">Runtime configuration (config.configurable)</p>
          {runtimeLoading ? <p className="text-xs text-muted-foreground">Loading runtime capabilities...</p> : null}
          <div className="grid gap-1">
            <label className="text-xs font-medium text-muted-foreground" htmlFor="new-assistant-runtime-model">
              Model group
            </label>
            <select
              id="new-assistant-runtime-model"
              className="h-9 rounded-md border border-border bg-background px-3 text-sm"
              value={runtimeModelId}
              onChange={(event) => setRuntimeModelId(event.target.value)}
              disabled={submitting}
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
              id="new-assistant-runtime-enable-tools"
              type="checkbox"
              className="h-4 w-4"
              checked={runtimeEnableTools}
              onChange={(event) => setRuntimeEnableTools(event.target.checked)}
              disabled={submitting}
            />
            <label htmlFor="new-assistant-runtime-enable-tools" className="text-xs">
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
                  disabled={submitting || !runtimeEnableTools || runtimeTools.length === 0}
                >
                  Select all
                </button>
                <button
                  type="button"
                  className="inline-flex items-center rounded border border-border bg-background px-2 py-0.5 text-[11px]"
                  onClick={() => setRuntimeToolNames([])}
                  disabled={submitting || runtimeToolNames.length === 0}
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
                        disabled={submitting || !runtimeEnableTools}
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
            Fields are written into <code>config.configurable.model_id / enable_tools / tools</code> when creating.
          </p>
        </div>

        <div className="grid gap-2 rounded-md border border-border/80 bg-background/50 p-3">
          <p className="text-xs font-medium text-muted-foreground">Parameter Schema</p>
          {schemaLoading ? <p className="text-xs">Loading schema...</p> : null}
          {schemaError ? <p className="text-xs text-red-600">{schemaError}</p> : null}
          {!schemaLoading && !schemaError ? (
            <p className="text-xs text-muted-foreground">
              graph={schema?.graph_id || graphId.trim() || "-"} · version={schema?.schema_version || "v1"}
            </p>
          ) : null}
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
                  disabled={submitting}
                  required={field.required}
                />
              </label>
            ))}
          </div>
        ) : null}

        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Config (JSON object)
          <textarea
            className="min-h-28 rounded-md border border-border bg-background px-3 py-2 font-mono text-xs"
            value={config}
            onChange={(event) => setConfig(event.target.value)}
            disabled={submitting}
          />
        </label>

        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Context (JSON object)
          <textarea
            className="min-h-28 rounded-md border border-border bg-background px-3 py-2 font-mono text-xs"
            value={context}
            onChange={(event) => setContext(event.target.value)}
            disabled={submitting}
          />
        </label>

        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Metadata (JSON object)
          <textarea
            className="min-h-28 rounded-md border border-border bg-background px-3 py-2 font-mono text-xs"
            value={metadata}
            onChange={(event) => setMetadata(event.target.value)}
            disabled={submitting}
          />
        </label>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="submit"
            className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background disabled:opacity-50"
            disabled={submitting}
          >
            {submitting ? "Creating..." : "Create Assistant"}
          </button>
          <Link
            href="/workspace/assistants"
            className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm"
          >
            Back to Assistants
          </Link>
        </div>
      </form>

      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      {notice ? <p className="mt-4 text-sm text-emerald-700">{notice}</p> : null}

      <div className="mt-4 rounded-lg border border-border/80 bg-card/70 p-4">
        <p className="text-xs font-medium text-muted-foreground">Create assistant request body</p>
        <pre className="mt-2 overflow-auto rounded border border-border bg-background p-3 text-xs">
          {JSON.stringify(requestBodyPreview, null, 2)}
        </pre>
      </div>
    </section>
  );
}
