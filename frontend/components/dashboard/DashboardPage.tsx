"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Plus } from "lucide-react";

import { ProjectTile } from "@/components/dashboard/ProjectTile";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast-host";
import { createProject, getProject, listProjects } from "@/lib/api";
import type { ProjectDetail, ProjectSummary } from "@/lib/types";

export function DashboardPage() {
  const { showToast } = useToast();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [details, setDetails] = useState<Record<string, ProjectDetail>>({});
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const refresh = useCallback(async () => {
    const summaries = await listProjects();
    setProjects(summaries);
    const loaded = await Promise.all(summaries.map((project) => getProject(project.id)));
    setDetails(Object.fromEntries(loaded.map((detail) => [detail.id, detail])));
  }, []);

  useEffect(() => {
    void refresh()
      .catch(() => setProjects([]))
      .finally(() => setLoading(false));
  }, [refresh]);

  const handleCreateProject = async () => {
    const name = window.prompt("Project name");
    if (!name?.trim()) {
      return;
    }
    setCreating(true);
    try {
      await createProject(name.trim());
      await refresh();
      showToast({ title: "Project created", description: name.trim() });
    } catch (error) {
      showToast({
        title: "Could not create project",
        description: error instanceof Error ? error.message : "Unknown error",
      });
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Loading projects…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">DeliveryLint</h1>
          <p className="mt-1 text-muted-foreground">
            Review target documents against shared reference materials.
          </p>
        </div>
        <Button disabled={creating} onClick={() => void handleCreateProject()}>
          {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          New project
        </Button>
      </header>

      {projects.length === 0 ? (
        <div className="rounded-xl border border-dashed p-10 text-center">
          <p className="text-lg font-medium">No projects yet</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Create a project, upload reference documents, then lint target documents against them.
          </p>
          <Button className="mt-4" onClick={() => void handleCreateProject()}>
            Create your first project
          </Button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((project) => {
            const detail = details[project.id];
            if (!detail) {
              return null;
            }
            return (
              <ProjectTile
                key={project.id}
                project={detail}
                onRefresh={() => void refresh()}
                onDeleted={() => void refresh()}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
