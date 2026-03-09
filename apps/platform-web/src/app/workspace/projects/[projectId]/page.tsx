"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { useWorkspaceContext } from "@/providers/WorkspaceContext";


export default function ProjectDetailPage() {
  const params = useParams<{ projectId: string }>();
  const router = useRouter();
  const projectId = String(params.projectId || "");
  const { projects } = useWorkspaceContext();

  const project = projects.find((item) => item.id === projectId);

  return (
    <section className="p-6">
      <h1 className="text-xl font-semibold">Project Management</h1>
      <p className="text-muted-foreground mt-2 text-sm">Project-scoped management entry.</p>

      <div className="mt-4 rounded-lg border border-border/80 bg-card/70 p-4">
        <p className="text-sm"><span className="text-muted-foreground">ID:</span> <code>{projectId}</code></p>
        <p className="mt-2 text-sm"><span className="text-muted-foreground">Name:</span> {project?.name || "-"}</p>
        <p className="mt-1 text-sm"><span className="text-muted-foreground">Description:</span> {project?.description || "-"}</p>
        <p className="mt-1 text-sm"><span className="text-muted-foreground">Status:</span> {project?.status || "-"}</p>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm"
          onClick={() => router.push(`/workspace/projects/${projectId}/members`)}
        >
          Manage Members
        </button>
        <button
          type="button"
          className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm"
          onClick={() => router.push(`/workspace/audit?projectId=${encodeURIComponent(projectId)}`)}
        >
          View Audit
        </button>
        <Link href="/workspace/projects" className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm">
          Back to Projects
        </Link>
      </div>

      <div className="mt-6 rounded-lg border border-border/80 bg-card/70 p-4">
        <p className="text-xs text-muted-foreground">Project-scoped entry point. Runtime behavior is configured at the assistant level.</p>
      </div>
    </section>
  );
}
