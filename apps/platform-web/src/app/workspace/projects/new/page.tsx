"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { createProject } from "@/lib/management-api/projects";
import { useWorkspaceContext } from "@/providers/WorkspaceContext";


export default function CreateProjectPage() {
  const router = useRouter();
  const { setProjectId } = useWorkspaceContext();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedName = name.trim();
    if (!normalizedName) {
      return;
    }

    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const created = await createProject({
        name: normalizedName,
        description: description.trim() || undefined,
      });
      setProjectId(created.id);
      setNotice(`Created project: ${created.name}`);
      if (typeof window !== "undefined") {
        window.location.href = "/workspace/projects";
        return;
      }
      router.replace("/workspace/projects");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="p-4 sm:p-6">
      <h2 className="text-xl font-semibold tracking-tight">Create Project</h2>
      <p className="text-muted-foreground mt-2 text-sm">Create a new project in a dedicated management page.</p>

      <form className="mt-4 grid gap-3 rounded-lg border border-border/80 bg-card/70 p-4" onSubmit={onSubmit}>
        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Project name
          <input
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            placeholder="Project name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            disabled={submitting}
            required
            minLength={1}
            maxLength={128}
          />
        </label>

        <label className="grid gap-1 text-xs font-medium text-muted-foreground">
          Description (optional)
          <textarea
            className="min-h-24 rounded-md border border-border bg-background px-3 py-2 text-sm"
            placeholder="Project description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            disabled={submitting}
          />
        </label>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="submit"
            className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background disabled:opacity-50"
            disabled={submitting}
          >
            {submitting ? "Creating..." : "Create Project"}
          </button>
          <Link
            href="/workspace/projects"
            className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm"
          >
            Back to Projects
          </Link>
        </div>
      </form>

      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      {notice ? <p className="mt-4 text-sm text-emerald-700">{notice}</p> : null}
    </section>
  );
}
