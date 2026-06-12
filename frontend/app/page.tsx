"use client";

import { useCallback, useEffect, useState } from "react";

import {
  AnalysisMode,
  EMPTY_REFERENCE_HINTS,
  ReferenceUploadState,
  TARGET_DOC_TYPES,
  TargetDocType,
  hintsToPayload,
  readFileAsText,
  referenceFileKey,
} from "../lib/constants";
import { ReferenceMetadataForm } from "../components/ReferenceMetadataForm";
import { apiUrl, fetchJson, isRecentRun } from "../lib/api";
import {
  AnalysisRunSummary,
  CorrectionUIResponse,
  PRIORITY_LABELS,
  PRIORITY_ORDER,
  PipelineResult,
  ReviewPriority,
} from "../lib/types";

function FindingCard({
  finding,
}: {
  finding: CorrectionUIResponse["findings"][number];
}) {
  return (
    <article className="finding-card">
      <h3>
        <span className={`badge ${finding.severity}`}>{finding.severity}</span>
        {finding.title}
        <span className="muted" style={{ fontWeight: 400, fontSize: "0.85rem" }}>
          {" "}
          · {(finding.confidence * 100).toFixed(0)}% conf
        </span>
      </h3>
      <p>{finding.message}</p>
      {finding.target_quote && (
        <p className="quote">
          <strong>Target:</strong> {finding.target_quote}
        </p>
      )}
      {finding.reference_quotes?.map((quote) => (
        <p key={quote} className="quote">
          <strong>Reference:</strong> {quote}
        </p>
      ))}
      {finding.related_source_summaries && finding.related_source_summaries.length > 0 && (
        <ul className="muted" style={{ fontSize: "0.88rem", paddingLeft: "1.1rem" }}>
          {finding.related_source_summaries.map((source) => (
            <li key={source.source_profile_id}>
              {source.doc_type} (authority {source.authority_level}) — {source.summary}
            </li>
          ))}
        </ul>
      )}
      {finding.recommendation && (
        <p style={{ fontSize: "0.9rem" }}>
          <strong>Recommendation:</strong> {finding.recommendation}
        </p>
      )}
    </article>
  );
}

export default function HomePage() {
  const [mode, setMode] = useState<AnalysisMode>("upload");
  const [data, setData] = useState<CorrectionUIResponse | null>(null);
  const [analysisRunId, setAnalysisRunId] = useState<number | null>(null);
  const [savedRuns, setSavedRuns] = useState<AnalysisRunSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [targetFile, setTargetFile] = useState<File | null>(null);
  const [targetDocType, setTargetDocType] = useState<TargetDocType>(TARGET_DOC_TYPES[0].value);
  const [referenceUploads, setReferenceUploads] = useState<ReferenceUploadState[]>([]);

  const loadSavedRuns = useCallback(async () => {
    const runs = await fetchJson<AnalysisRunSummary[]>(apiUrl("/analysis/runs?limit=10"));
    setSavedRuns(runs);
    return runs;
  }, []);

  useEffect(() => {
    void loadSavedRuns().catch(() => setSavedRuns([]));
  }, [loadSavedRuns]);

  const applyResult = (result: PipelineResult) => {
    setData(result.correction_ui_response);
    setAnalysisRunId(result.analysis_run_id ?? null);
  };

  const tryRecoverLatestRun = async (previousLatestRunId: number | null) => {
    const runs = await loadSavedRuns();
    const newest = runs[0];
    if (!newest || newest.id === previousLatestRunId || !isRecentRun(newest.created_at)) {
      return false;
    }
    const detail = await fetchJson<{
      id: number;
      correction_ui_response: CorrectionUIResponse;
    }>(apiUrl(`/analysis/runs/${newest.id}`));
    setData(detail.correction_ui_response);
    setAnalysisRunId(detail.id);
    setNotice(
      "The connection dropped before results loaded, but your analysis finished and was saved. Showing the latest run.",
    );
    setError(null);
    return true;
  };

  const runSampleAnalysis = async () => {
    const previousLatestRunId = savedRuns[0]?.id ?? null;
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const result = await fetchJson<PipelineResult>(apiUrl("/analysis/lint"), {
        method: "POST",
      });
      applyResult(result);
      await loadSavedRuns();
    } catch (err) {
      const recovered = await tryRecoverLatestRun(previousLatestRunId).catch(() => false);
      if (!recovered) {
        setError(String(err));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReferenceFilesChange = (files: File[]) => {
    setReferenceUploads((previous) => {
      const previousByKey = new Map(previous.map((entry) => [entry.key, entry]));
      return files.map((file) => {
        const key = referenceFileKey(file);
        const existing = previousByKey.get(key);
        return (
          existing ?? {
            key,
            file,
            hints: { ...EMPTY_REFERENCE_HINTS },
          }
        );
      });
    });
  };

  const updateReferenceHints = (key: string, hints: ReferenceUploadState["hints"]) => {
    setReferenceUploads((previous) =>
      previous.map((entry) => (entry.key === key ? { ...entry, hints } : entry)),
    );
  };

  const runUploadedAnalysis = async () => {
    if (!targetFile) {
      setError("Select a target document to upload.");
      return;
    }

    const previousLatestRunId = savedRuns[0]?.id ?? null;
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const [targetText, ...referenceTexts] = await Promise.all([
        readFileAsText(targetFile),
        ...referenceUploads.map((entry) => readFileAsText(entry.file)),
      ]);

      const result = await fetchJson<PipelineResult>(apiUrl("/analysis/lint/custom"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target: {
            filename: targetFile.name,
            text: targetText,
          },
          target_doc_type: targetDocType,
          references: referenceUploads.map((entry, index) => ({
            filename: entry.file.name,
            text: referenceTexts[index],
            profile_hints: hintsToPayload(entry.hints),
          })),
        }),
      });
      applyResult(result);
      await loadSavedRuns();
    } catch (err) {
      const recovered = await tryRecoverLatestRun(previousLatestRunId).catch(() => false);
      if (!recovered) {
        setError(String(err));
      }
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = () => {
    if (mode === "sample") {
      void runSampleAnalysis();
    } else {
      void runUploadedAnalysis();
    }
  };

  const loadRun = async (runId: number) => {
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const detail = await fetchJson<{
        id: number;
        correction_ui_response: CorrectionUIResponse;
      }>(apiUrl(`/analysis/runs/${runId}`));
      setData(detail.correction_ui_response);
      setAnalysisRunId(detail.id);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const clearRuns = async () => {
    if (!window.confirm("Delete all saved analysis runs?")) {
      return;
    }
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      await fetchJson<{ deleted: number }>(apiUrl("/analysis/runs"), { method: "DELETE" });
      setSavedRuns([]);
      setData(null);
      setAnalysisRunId(null);
      setNotice("Cleared all saved runs.");
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const canRunUpload = Boolean(targetFile) && !loading;

  return (
    <main>
      <header className="app-header">
        <h1>DeliveryLint</h1>
        <p>Review implementation documents against reference materials.</p>
      </header>

      <section className="panel">
        <h2>Run analysis</h2>

        <div className="mode-tabs">
          <button
            type="button"
            className={mode === "upload" ? "active" : ""}
            onClick={() => setMode("upload")}
          >
            Upload documents
          </button>
          <button
            type="button"
            className={mode === "sample" ? "active" : ""}
            onClick={() => setMode("sample")}
          >
            Sample demo
          </button>
        </div>

        {mode === "upload" ? (
          <div className="upload-grid">
            <div className="upload-field">
              <label htmlFor="target-file">Target document (.txt, .md)</label>
              <input
                id="target-file"
                type="file"
                accept=".txt,.md,text/plain,text/markdown"
                onChange={(e) => setTargetFile(e.target.files?.[0] ?? null)}
              />
              {targetFile && <p className="muted">{targetFile.name}</p>}
            </div>

            <div className="upload-field">
              <label htmlFor="target-doc-type">Target document type</label>
              <select
                id="target-doc-type"
                value={targetDocType}
                onChange={(e) => setTargetDocType(e.target.value as TargetDocType)}
              >
                {TARGET_DOC_TYPES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="upload-field">
              <label htmlFor="reference-files">Reference documents (optional)</label>
              <input
                id="reference-files"
                type="file"
                accept=".txt,.md,text/plain,text/markdown"
                multiple
                onChange={(e) => handleReferenceFilesChange(Array.from(e.target.files ?? []))}
              />
              <p className="muted" style={{ fontSize: "0.88rem", marginTop: "0.35rem" }}>
                For each reference, you can specify document type, origin, status, and recency date.
                Leave fields blank to let the model infer them.
              </p>
              {referenceUploads.map((entry) => (
                <ReferenceMetadataForm
                  key={entry.key}
                  filename={entry.file.name}
                  hints={entry.hints}
                  onChange={(hints) => updateReferenceHints(entry.key, hints)}
                />
              ))}
            </div>
          </div>
        ) : (
          <p className="muted" style={{ marginTop: 0 }}>
            Runs the built-in NetSuite billing sample scenario (signed SOW + client email vs draft
            SOW).
          </p>
        )}

        <div className="controls" style={{ marginTop: "1rem" }}>
          <button
            className="primary"
            onClick={() => void runAnalysis()}
            disabled={mode === "upload" ? !canRunUpload : loading}
          >
            {loading ? "Running pipeline…" : "Run lint analysis"}
          </button>
        </div>
        <p className="muted" style={{ marginTop: "0.75rem", marginBottom: 0, fontSize: "0.9rem" }}>
          Every run is saved automatically. OpenAI analyses may take a minute.
        </p>
      </section>

      {notice && <p className="notice">{notice}</p>}
      {error && <p className="error">Failed to load analysis: {error}</p>}

      {savedRuns.length > 0 && (
        <section className="panel">
          <div className="controls" style={{ justifyContent: "space-between", marginBottom: "0.75rem" }}>
            <h2 style={{ margin: 0 }}>Saved runs</h2>
            <button className="ghost" onClick={() => void clearRuns()} disabled={loading}>
              Clear all runs
            </button>
          </div>
          <ul className="run-list">
            {savedRuns.map((run) => (
              <li key={run.id}>
                <span>
                  Run #{run.id} · {run.project_id} ·{" "}
                  {new Date(run.created_at).toLocaleString()}
                </span>
                <button
                  className={`ghost${analysisRunId === run.id ? " active" : ""}`}
                  onClick={() => void loadRun(run.id)}
                  disabled={loading}
                >
                  Load
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {!data && !loading && !error && !notice && (
        <p className="muted">
          {mode === "upload"
            ? "Upload a target document and click Run lint analysis."
            : 'Click "Run lint analysis" to start the sample demo.'}
        </p>
      )}

      {data && (
        <>
          <section className="panel">
            <h2>Summary</h2>
            <p>
              Target: {data.target_document.filename ?? "document"} ({data.target_document.doc_type})
              {analysisRunId != null && (
                <span className="muted"> · saved as run #{analysisRunId}</span>
              )}
            </p>
            <div className="summary-grid">
              <div className="stat">
                <strong>{data.summary.total_findings}</strong>
                <span>Total findings</span>
              </div>
              <div className="stat">
                <strong>{data.summary.needs_fix_count}</strong>
                <span>Needs fix</span>
              </div>
              <div className="stat">
                <strong>{data.summary.needs_review_count}</strong>
                <span>Needs review</span>
              </div>
              <div className="stat">
                <strong>{data.summary.quality_suggestion_count}</strong>
                <span>Quality</span>
              </div>
              <div className="stat">
                <strong>{data.summary.info_count}</strong>
                <span>Info</span>
              </div>
              <div className="stat">
                <strong>{data.summary.has_blocking_issues ? "Yes" : "No"}</strong>
                <span>Blocking issues</span>
              </div>
            </div>
          </section>

          {PRIORITY_ORDER.map((priority: ReviewPriority) => {
            const group = data.findings.filter((f) => f.priority === priority);
            if (group.length === 0) return null;
            return (
              <section key={priority} className="priority-section">
                <h2>
                  {PRIORITY_LABELS[priority]} ({group.length})
                </h2>
                {group.map((finding) => (
                  <FindingCard key={finding.id} finding={finding} />
                ))}
              </section>
            );
          })}

          {data.lint_warnings.length > 0 && (
            <section className="panel">
              <h2>Evidence coverage / limitations</h2>
              <ul>
                {data.lint_warnings.map((warning) => (
                  <li key={warning.code}>{warning.message}</li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </main>
  );
}
