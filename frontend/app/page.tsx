"use client";

import { useEffect, useState } from "react";

type ReviewPriority = "needs_fix" | "needs_review" | "quality_suggestion" | "info";

type FindingView = {
  id: string;
  priority: ReviewPriority;
  severity: string;
  confidence: number;
  title: string;
  message: string;
  recommendation?: string | null;
  target_quote?: string | null;
  reference_quotes?: string[];
};

type CorrectionUIResponse = {
  project_id: string;
  target_document: { filename?: string | null; doc_type: string };
  summary: {
    total_findings: number;
    needs_fix_count: number;
    needs_review_count: number;
    quality_suggestion_count: number;
    info_count: number;
    has_blocking_issues: boolean;
  };
  findings: FindingView[];
  lint_warnings: { code: string; message: string }[];
};

const PRIORITY_LABELS: Record<ReviewPriority, string> = {
  needs_fix: "Needs Fix",
  needs_review: "Needs Review",
  quality_suggestion: "Quality Suggestions",
  info: "Info / Coverage",
};

const PRIORITY_ORDER: ReviewPriority[] = [
  "needs_fix",
  "needs_review",
  "quality_suggestion",
  "info",
];

export default function HomePage() {
  const [data, setData] = useState<CorrectionUIResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/analysis/lint", { method: "POST" })
      .then(async (res) => {
        if (!res.ok) throw new Error(`API error ${res.status}`);
        const json = await res.json();
        setData(json.correction_ui_response ?? json);
      })
      .catch((err) => setError(String(err)));
  }, []);

  if (error) {
    return <p style={{ color: "#b00020" }}>Failed to load analysis: {error}</p>;
  }

  if (!data) {
    return <p>Running lint analysis…</p>;
  }

  return (
    <div>
      <section style={{ marginBottom: "1.5rem", padding: "1rem", background: "#f5f5f5" }}>
        <h2 style={{ marginTop: 0 }}>Summary</h2>
        <p>
          Target: {data.target_document.filename ?? "document"} ({data.target_document.doc_type})
        </p>
        <p>
          {data.summary.total_findings} findings · blocking issues:{" "}
          {data.summary.has_blocking_issues ? "yes" : "no"}
        </p>
      </section>

      {PRIORITY_ORDER.map((priority) => {
        const group = data.findings.filter((f) => f.priority === priority);
        if (group.length === 0) return null;
        return (
          <section key={priority} style={{ marginBottom: "2rem" }}>
            <h2>
              {PRIORITY_LABELS[priority]} ({group.length})
            </h2>
            <ul style={{ listStyle: "none", padding: 0 }}>
              {group.map((finding) => (
                <li
                  key={finding.id}
                  style={{
                    border: "1px solid #ddd",
                    borderRadius: 8,
                    padding: "1rem",
                    marginBottom: "0.75rem",
                  }}
                >
                  <strong>[{finding.severity}] {finding.title}</strong>
                  <p>{finding.message}</p>
                  {finding.target_quote && (
                    <p style={{ fontSize: "0.9rem", color: "#333" }}>
                      Target: {finding.target_quote}
                    </p>
                  )}
                  {finding.reference_quotes?.map((q) => (
                    <p key={q} style={{ fontSize: "0.9rem", color: "#555" }}>
                      Reference: {q}
                    </p>
                  ))}
                  {finding.recommendation && (
                    <p style={{ fontSize: "0.9rem" }}>Recommendation: {finding.recommendation}</p>
                  )}
                </li>
              ))}
            </ul>
          </section>
        );
      })}

      {data.lint_warnings.length > 0 && (
        <section>
          <h2>Evidence Coverage / Limitations</h2>
          <ul>
            {data.lint_warnings.map((w) => (
              <li key={w.code}>{w.message}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
