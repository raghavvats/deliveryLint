import type {
  AnalysisRunDetail,
  AnalysisRunSummary,
  ProjectDetail,
  ProjectSummary,
  ReferenceDocumentDetail,
  ReferenceDocumentSummary,
  TargetUploadResponse,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "/api";

export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  if (!API_BASE_URL || API_BASE_URL === "/api") {
    return `/api${normalizedPath}`;
  }
  return `${API_BASE_URL}${normalizedPath}`;
}

export async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch {
    throw new Error(
      "Could not reach the API. Make sure the backend is running and NEXT_PUBLIC_API_BASE_URL is correct.",
    );
  }
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (body?.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function parseUtcDate(value: string): Date {
  const hasTimezone = /[zZ]|[+-]\d{2}:\d{2}$/.test(value);
  return new Date(hasTimezone ? value : `${value}Z`);
}

export function formatRunTime(value: string): string {
  return parseUtcDate(value).toLocaleString();
}

export async function listProjects(): Promise<ProjectSummary[]> {
  return fetchJson<ProjectSummary[]>(apiUrl("/projects"));
}

export async function createProject(name: string): Promise<ProjectSummary> {
  return fetchJson<ProjectSummary>(apiUrl("/projects"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export async function getProject(projectId: string): Promise<ProjectDetail> {
  return fetchJson<ProjectDetail>(apiUrl(`/projects/${projectId}`));
}

export async function deleteProject(projectId: string): Promise<void> {
  await fetchJson<{ deleted: string }>(apiUrl(`/projects/${projectId}`), {
    method: "DELETE",
  });
}

export async function rerunTarget(
  projectId: string,
  runId: number,
  file: File,
  targetDocType?: string,
): Promise<TargetUploadResponse> {
  const form = new FormData();
  form.append("target_file", file);
  if (targetDocType) {
    form.append("target_doc_type", targetDocType);
  }
  return fetchJson<TargetUploadResponse>(apiUrl(`/projects/${projectId}/runs/${runId}/rerun`), {
    method: "POST",
    body: form,
  });
}

export async function pollProjectUntilSettled(
  projectId: string,
  options?: { intervalMs?: number; timeoutMs?: number },
): Promise<ProjectDetail> {
  const intervalMs = options?.intervalMs ?? 2500;
  const timeoutMs = options?.timeoutMs ?? 600000;
  const started = Date.now();

  while (Date.now() - started < timeoutMs) {
    const project = await getProject(projectId);
    const refsProcessing = project.references.some((ref) => ref.status === "processing");
    const runsProcessing = project.runs.some((run) => run.status === "processing");
    if (!refsProcessing && !runsProcessing) {
      return project;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error("Project processing timed out");
}

export async function uploadReference(
  projectId: string,
  file: File,
  metadata?: Record<string, unknown>,
): Promise<ReferenceDocumentSummary> {
  const form = new FormData();
  form.append("reference_file", file);
  if (metadata) {
    form.append("reference_metadata", JSON.stringify(metadata));
  }
  return fetchJson<ReferenceDocumentSummary>(apiUrl(`/projects/${projectId}/references`), {
    method: "POST",
    body: form,
  });
}

export async function getReferenceDocument(
  projectId: string,
  refId: string,
): Promise<ReferenceDocumentDetail> {
  return fetchJson<ReferenceDocumentDetail>(apiUrl(`/projects/${projectId}/references/${refId}`));
}

export async function uploadTarget(
  projectId: string,
  file: File,
  targetDocType: string,
  runName?: string,
): Promise<TargetUploadResponse> {
  const form = new FormData();
  form.append("target_file", file);
  form.append("target_doc_type", targetDocType);
  if (runName) {
    form.append("run_name", runName);
  }
  return fetchJson<TargetUploadResponse>(apiUrl(`/projects/${projectId}/targets`), {
    method: "POST",
    body: form,
  });
}

export async function getRun(runId: number): Promise<AnalysisRunDetail> {
  return fetchJson<AnalysisRunDetail>(apiUrl(`/analysis/runs/${runId}`));
}

export async function pollProjectUntilReferencesReady(
  projectId: string,
  refIds: string[],
  options?: { intervalMs?: number; timeoutMs?: number },
): Promise<ProjectDetail> {
  const intervalMs = options?.intervalMs ?? 2500;
  const timeoutMs = options?.timeoutMs ?? 600000;
  const started = Date.now();
  const pending = new Set(refIds);

  while (Date.now() - started < timeoutMs) {
    const project = await getProject(projectId);
    for (const refId of [...pending]) {
      const ref = project.references.find((item) => item.id === refId);
      if (!ref) {
        pending.delete(refId);
        continue;
      }
      if (ref.status === "ready" || !ref.status) {
        pending.delete(refId);
      }
      if (ref.status === "failed") {
        throw new Error(ref.error_message ?? `Reference ${ref.filename} failed to process`);
      }
    }
    if (pending.size === 0) {
      return project;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error("Reference processing timed out");
}

export async function pollRunUntilComplete(
  runId: number,
  options?: { intervalMs?: number; timeoutMs?: number },
): Promise<AnalysisRunDetail> {
  const intervalMs = options?.intervalMs ?? 2500;
  const timeoutMs = options?.timeoutMs ?? 300000;
  const started = Date.now();

  while (Date.now() - started < timeoutMs) {
    const run = await getRun(runId);
    if (run.status === "completed" || run.status === "failed") {
      return run;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error("Analysis timed out while processing");
}

export async function listRuns(projectId?: string): Promise<AnalysisRunSummary[]> {
  const params = new URLSearchParams({ limit: "50" });
  if (projectId) {
    params.set("project_id", projectId);
  }
  return fetchJson<AnalysisRunSummary[]>(apiUrl(`/analysis/runs?${params.toString()}`));
}
