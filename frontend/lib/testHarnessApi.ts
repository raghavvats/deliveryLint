import type {
  ExpectedFindingResult,
  HarnessRunDetail,
  HarnessRunSummary,
  SuiteRunResult,
  TestSuiteDefinition,
} from "./testHarnessTypes";
import { apiUrl, fetchJson, formatRunTime } from "./api";

export type {
  ExpectedFindingResult,
  HarnessRunDetail,
  HarnessRunSummary,
  SuiteRunResult,
  TestSuiteDefinition,
} from "./testHarnessTypes";
export { formatRunTime };

export async function listTestSuites(): Promise<TestSuiteDefinition[]> {
  return fetchJson<TestSuiteDefinition[]>(apiUrl("/test/suites"));
}

export async function getTestHarnessMeta(): Promise<{
  test_files_root: string;
  suite_count: number;
  exists: boolean;
}> {
  return fetchJson(apiUrl("/test/meta"));
}

export async function runTestHarness(suiteIds?: string[]): Promise<HarnessRunDetail> {
  return fetchJson<HarnessRunDetail>(apiUrl("/test/runs"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ suite_ids: suiteIds ?? null }),
  });
}

export async function pollTestHarnessRunUntilComplete(
  runId: number,
  options?: { intervalMs?: number; timeoutMs?: number },
): Promise<HarnessRunDetail> {
  const intervalMs = options?.intervalMs ?? 3000;
  const timeoutMs = options?.timeoutMs ?? 3_600_000;
  const started = Date.now();

  while (Date.now() - started < timeoutMs) {
    const run = await getTestHarnessRun(runId);
    if (run.status === "completed" || run.status === "failed") {
      return run;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error("Test harness run timed out while processing");
}

export async function listTestHarnessRuns(): Promise<HarnessRunSummary[]> {
  return fetchJson<HarnessRunSummary[]>(apiUrl("/test/runs?limit=100"));
}

export async function getTestHarnessRun(runId: number): Promise<HarnessRunDetail> {
  return fetchJson<HarnessRunDetail>(apiUrl(`/test/runs/${runId}`));
}

export function testHarnessExportUrl(runId: number): string {
  return apiUrl(`/test/runs/${runId}/export.md`);
}

export async function downloadTestHarnessRunMarkdown(runId: number): Promise<void> {
  const response = await fetch(testHarnessExportUrl(runId));
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
    throw new Error(detail || `Export failed (${response.status})`);
  }
  const markdown = await response.text();
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match?.[1] ?? `deliverylint-harness-run-${runId}.md`;
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function deleteTestHarnessRun(runId: number): Promise<void> {
  await fetchJson<{ deleted: number }>(apiUrl(`/test/runs/${runId}`), { method: "DELETE" });
}

export async function clearTestHarnessRuns(): Promise<number> {
  const result = await fetchJson<{ deleted: number }>(apiUrl("/test/runs"), { method: "DELETE" });
  return result.deleted;
}
