"use client";

import { listProjects, type ManagementProject } from "@/lib/management-api/projects";
import { logClient } from "@/lib/client-logger";
import { useQueryState } from "nuqs";
import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useMemo, useState } from "react";


type WorkspaceContextValue = {
  projectId: string;
  setProjectId: (value: string) => void;
  assistantId: string;
  setAssistantId: (value: string) => void;
  projects: ManagementProject[];
  loading: boolean;
};


const WorkspaceContext = createContext<WorkspaceContextValue | undefined>(undefined);


export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [projectId, setProjectId] = useQueryState("projectId", { defaultValue: "" });
  const [assistantId, setAssistantId] = useQueryState("assistantId", { defaultValue: "" });
  const [, setThreadId] = useQueryState("threadId", { defaultValue: "" });
  const [projects, setProjects] = useState<ManagementProject[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadProjects() {
      setLoading(true);
      try {
        const rows = await listProjects({ limit: 100, offset: 0 });
        if (cancelled) {
          return;
        }
        setProjects(rows);

        const projectStillValid = rows.some((item) => item.id === projectId);
        if ((!projectId || !projectStillValid) && rows.length > 0) {
          setProjectId(rows[0].id);
        }
        if (rows.length === 0) {
          setProjectId("");
        }
      } catch (err) {
        if (!cancelled) {
          setProjects([]);
        }
        logClient({
          level: "error",
          event: "workspace_load_projects_error",
          message: "Failed to load projects",
          context: { error: String(err) },
        });
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadProjects();

    return () => {
      cancelled = true;
    };
  }, [projectId, setProjectId]);

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      projectId: projectId ?? "",
      setProjectId: (value: string) => {
        setProjectId(value);
        setThreadId(null);
        setAssistantId("");
      },
      assistantId: assistantId ?? "",
      setAssistantId,
      projects,
      loading,
    }),
    [assistantId, loading, projectId, projects, setAssistantId, setProjectId, setThreadId],
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}


export function useWorkspaceContext() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspaceContext must be used within WorkspaceProvider");
  }
  return context;
}
