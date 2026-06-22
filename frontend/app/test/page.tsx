"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  clearTestHarnessRuns,
  downloadTestHarnessRunMarkdown,
  formatRunTime,
  getTestHarnessMeta,
  getTestHarnessRun,
  listTestHarnessRuns,
  listTestSuites,
  pollTestHarnessRunUntilComplete,
  runTestHarness,
  type HarnessRunDetail,
  type HarnessRunSummary,
  type TestSuiteDefinition,
} from "@/lib/testHarnessApi";

function pct(value: number): string {
  return `${value.toFixed(1)}%`;
}

function statusColor(status: string): string {
  if (status === "completed") return "#166534";
  if (status === "failed") return "#991b1b";
  if (status === "running") return "#92400e";
  return "#666";
}

export default function TestHarnessPage() {
  const [suites, setSuites] = useState<TestSuiteDefinition[]>([]);
  const [runs, setRuns] = useState<HarnessRunSummary[]>([]);
  const [selectedRun, setSelectedRun] = useState<HarnessRunDetail | null>(null);
  const [selectedSuiteIds, setSelectedSuiteIds] = useState<Set<string>>(new Set());
  const [meta, setMeta] = useState<{ test_files_root: string; suite_count: number; exists: boolean } | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [suiteList, runList, metaInfo] = await Promise.all([
        listTestSuites(),
        listTestHarnessRuns(),
        getTestHarnessMeta(),
      ]);
      setSuites(suiteList);
      setRuns(runList);
      setMeta(metaInfo);
      setSelectedSuiteIds(new Set(suiteList.map((suite) => suite.id)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load test harness data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    try {
      const suiteIds =
        selectedSuiteIds.size === suites.length ? undefined : Array.from(selectedSuiteIds);
      const started = await runTestHarness(suiteIds);
      setSelectedRun(started);
      await refresh();
      const detail = await pollTestHarnessRunUntilComplete(started.id);
      setSelectedRun(detail);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Harness run failed");
    } finally {
      setRunning(false);
    }
  };

  const handleDownload = async () => {
    if (!selectedRun) return;
    setDownloading(true);
    setError(null);
    try {
      await downloadTestHarnessRunMarkdown(selectedRun.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to download report");
    } finally {
      setDownloading(false);
    }
  };

  const handleSelectRun = async (runId: number) => {
    setError(null);
    try {
      const detail = await getTestHarnessRun(runId);
      setSelectedRun(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load run detail");
    }
  };

  const handleClearRuns = async () => {
    if (!window.confirm("Delete all saved harness runs?")) return;
    setError(null);
    try {
      await clearTestHarnessRuns();
      setSelectedRun(null);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to clear runs");
    }
  };

  const aggregateBySuite = useMemo(() => {
    const map = new Map<string, { runs: number; avgRecall: number; lastRecall: number | null }>();
    for (const run of runs) {
      // Summaries don't include per-suite breakdown; keep last overall recall only.
      map.set("__overall__", {
        runs: runs.length,
        avgRecall: runs.length
          ? runs.reduce((sum, item) => sum + item.recall_pct, 0) / runs.length
          : 0,
        lastRecall: runs[0]?.recall_pct ?? null,
      });
    }
    return map;
  }, [runs]);

  const toggleSuite = (suiteId: string) => {
    setSelectedSuiteIds((prev) => {
      const next = new Set(prev);
      if (next.has(suiteId)) {
        next.delete(suiteId);
      } else {
        next.add(suiteId);
      }
      return next;
    });
  };

  return (
    <main style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", padding: "1.5rem", maxWidth: 1200, margin: "0 auto" }}>
      <header style={{ marginBottom: "1.5rem", borderBottom: "1px solid #ccc", paddingBottom: "1rem" }}>
        <h1 style={{ margin: 0, fontSize: "1.25rem" }}>DeliveryLint Test Harness</h1>
        <p style={{ margin: "0.5rem 0 0", color: "#444" }}>
          Benchmark suites from <code>testFiles/</code>. Recall = answer-key findings matched by type + keywords.
          Meaningful scores require <code>LLM_PROVIDER=openai</code> on the API.
        </p>
        {meta && (
          <p style={{ margin: "0.5rem 0 0", color: "#666", fontSize: "0.85rem" }}>
            Root: {meta.test_files_root} · {meta.suite_count} suites · exists={String(meta.exists)}
          </p>
        )}
      </header>

      {error && (
        <div style={{ background: "#fee2e2", border: "1px solid #fca5a5", padding: "0.75rem", marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
        <div style={{ border: "1px solid #ddd", padding: "1rem" }}>
          <h2 style={{ marginTop: 0, fontSize: "1rem" }}>Suites</h2>
          {loading ? (
            <p>Loading…</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {suites.map((suite) => (
                <li key={suite.id} style={{ marginBottom: "0.5rem" }}>
                  <label style={{ display: "flex", gap: "0.5rem", alignItems: "flex-start" }}>
                    <input
                      type="checkbox"
                      checked={selectedSuiteIds.has(suite.id)}
                      onChange={() => toggleSuite(suite.id)}
                    />
                    <span>
                      <strong>{suite.name}</strong>
                      <br />
                      <span style={{ color: "#666", fontSize: "0.8rem" }}>
                        {suite.target_doc_type} · {suite.expected_findings.length} expected · {suite.reference_count} refs
                      </span>
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          )}
          <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}>
            <button type="button" onClick={() => void handleRun()} disabled={running || selectedSuiteIds.size === 0}>
              {running ? "Running (polling)…" : "Run selected suites"}
            </button>
            <button type="button" onClick={() => void refresh()} disabled={running}>
              Refresh
            </button>
          </div>
        </div>

        <div style={{ border: "1px solid #ddd", padding: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ marginTop: 0, fontSize: "1rem" }}>Run history</h2>
            <button type="button" onClick={() => void handleClearRuns()} disabled={runs.length === 0}>
              Clear all
            </button>
          </div>
          {runs.length === 0 ? (
            <p style={{ color: "#666" }}>No saved runs yet.</p>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
              <thead>
                <tr>
                  <th align="left">When</th>
                  <th align="right">Recall</th>
                  <th align="right">Caught</th>
                  <th align="left">LLM</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr
                    key={run.id}
                    style={{
                      cursor: "pointer",
                      background: selectedRun?.id === run.id ? "#f3f4f6" : "transparent",
                    }}
                    onClick={() => void handleSelectRun(run.id)}
                  >
                    <td>{formatRunTime(run.created_at)}</td>
                    <td align="right" style={{ color: statusColor(run.status) }}>
                      {run.status === "running" ? "running…" : pct(run.recall_pct)}
                    </td>
                    <td align="right">
                      {run.total_caught}/{run.total_expected}
                    </td>
                    <td>{run.llm_provider}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {aggregateBySuite.get("__overall__") && runs.length > 1 && (
            <p style={{ marginTop: "0.75rem", color: "#666", fontSize: "0.8rem" }}>
              Avg recall across {runs.length} runs:{" "}
              {pct(aggregateBySuite.get("__overall__")!.avgRecall)}
            </p>
          )}
        </div>
      </section>

      {selectedRun && (
        <section style={{ border: "1px solid #ddd", padding: "1rem" }}>
          <h2 style={{ marginTop: 0, fontSize: "1rem" }}>
            Run #{selectedRun.id} — {pct(selectedRun.recall_pct)} ({selectedRun.total_caught}/
            {selectedRun.total_expected} caught)
          </h2>
          <p style={{ color: "#666", fontSize: "0.85rem" }}>
            {formatRunTime(selectedRun.created_at)} · {selectedRun.llm_provider} · {selectedRun.suite_count} suites ·
            status={selectedRun.status}
          </p>
          <div style={{ marginTop: "0.75rem" }}>
            <button
              type="button"
              onClick={() => void handleDownload()}
              disabled={downloading || selectedRun.status === "running"}
            >
              {downloading ? "Downloading…" : "Download findings (.md)"}
            </button>
            {selectedRun.status === "running" && (
              <span style={{ marginLeft: "0.75rem", color: "#666", fontSize: "0.8rem" }}>
                Available when the run completes.
              </span>
            )}
          </div>

          {selectedRun.suite_results.map((suite) => (
            <details key={suite.suite_id} style={{ marginTop: "1rem", borderTop: "1px solid #eee", paddingTop: "0.75rem" }}>
              <summary style={{ cursor: "pointer" }}>
                <strong>{suite.suite_name}</strong> — {pct(suite.recall_pct)} ({suite.caught_count}/
                {suite.expected_count}) · {suite.actual_finding_count} findings · {suite.extra_finding_count} extra
                {suite.duration_ms != null ? ` · ${suite.duration_ms}ms` : ""}
              </summary>

              {suite.error_message && (
                <p style={{ color: "#991b1b" }}>Error: {suite.error_message}</p>
              )}

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "0.75rem" }}>
                <div>
                  <h3 style={{ fontSize: "0.9rem" }}>Answer key ({suite.expected_count})</h3>
                  <ol style={{ paddingLeft: "1.25rem", fontSize: "0.8rem" }}>
                    {suite.expected_results.map((item) => (
                      <li
                        key={item.index}
                        style={{ marginBottom: "0.5rem", color: item.caught ? "#166534" : "#991b1b" }}
                      >
                        <code>{item.acceptable_types.join(" | ")}</code>
                        <div>{item.description}</div>
                        {item.caught ? (
                          <div style={{ color: "#166534" }}>
                            matched: {item.matched_title} ({item.matched_finding_type}, score{" "}
                            {item.match_score})
                          </div>
                        ) : (
                          <div style={{ color: "#991b1b" }}>missed</div>
                        )}
                      </li>
                    ))}
                  </ol>
                </div>
                <div>
                  <h3 style={{ fontSize: "0.9rem" }}>Extra findings ({suite.extra_finding_count})</h3>
                  {suite.extra_findings.length === 0 ? (
                    <p style={{ color: "#666", fontSize: "0.8rem" }}>None</p>
                  ) : (
                    <ul style={{ paddingLeft: "1.25rem", fontSize: "0.8rem" }}>
                      {suite.extra_findings.map((finding) => (
                        <li key={finding.id} style={{ marginBottom: "0.5rem" }}>
                          <code>{finding.finding_type}</code> — {finding.title}
                          <div style={{ color: "#666" }}>{finding.message}</div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </details>
          ))}
        </section>
      )}
    </main>
  );
}
