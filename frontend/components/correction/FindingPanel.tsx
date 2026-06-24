"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { CorrectionFindingView, CorrectionReferenceDocument } from "@/lib/types";
import { PRIORITY_LABELS } from "@/lib/types";

type FindingPanelProps = {
  finding: CorrectionFindingView;
  referenceDocuments: CorrectionReferenceDocument[];
  tracebackDocId: string | null;
  onTraceback: (documentId: string) => void;
  onBackToTarget: () => void;
};

function severityVariant(severity: string): "destructive" | "warning" | "secondary" | "outline" {
  if (severity === "critical" || severity === "high") {
    return "destructive";
  }
  if (severity === "medium") {
    return "warning";
  }
  return "secondary";
}

export function FindingPanel({
  finding,
  referenceDocuments,
  tracebackDocId,
  onTraceback,
  onBackToTarget,
}: FindingPanelProps) {
  const filenameByDocId = Object.fromEntries(
    referenceDocuments.map((doc) => [doc.document_id, doc.filename ?? doc.document_id]),
  );

  const tracebackEntries: Array<{ key: string; documentId: string; label: string; quote?: string }> =
    [];

  for (const evidence of finding.reference_evidence ?? []) {
    tracebackEntries.push({
      key: evidence.fact_id,
      documentId: evidence.document_id,
      label: filenameByDocId[evidence.document_id] ?? evidence.document_id,
      quote: evidence.quote,
    });
  }

  if (tracebackEntries.length === 0) {
    for (const source of finding.related_source_summaries ?? []) {
      tracebackEntries.push({
        key: source.source_profile_id,
        documentId: source.document_id,
        label: filenameByDocId[source.document_id] ?? source.document_id,
        quote: source.summary,
      });
    }
  }

  if (tracebackEntries.length === 0) {
    for (const [index, quote] of (finding.reference_quotes ?? []).entries()) {
      const matchedDoc = referenceDocuments.find((doc) => doc.text.includes(quote));
      if (!matchedDoc) {
        continue;
      }
      tracebackEntries.push({
        key: `quote-${index}`,
        documentId: matchedDoc.document_id,
        label: matchedDoc.filename ?? matchedDoc.document_id,
        quote,
      });
    }
  }

  return (
    <aside className="flex h-full flex-col gap-4 overflow-auto rounded-lg border bg-card p-5">
      

      <div className="flex flex-wrap items-center gap-2">
        <Badge>{PRIORITY_LABELS[finding.priority]}</Badge>
        <Badge variant={severityVariant(finding.severity)}>{finding.severity}</Badge>
        <span className="text-sm text-muted-foreground">
          {(finding.confidence * 100).toFixed(0)}% confidence
        </span>
      </div>

      <div>
        <h2 className="text-lg font-semibold">{finding.title}</h2>
        <p className="mt-2 text-sm text-muted-foreground">{finding.message}</p>
      </div>
      {tracebackDocId ? (
        <div>
          <p className="mb-2 text-sm font-medium text-muted-foreground">
            Viewing reference: {filenameByDocId[tracebackDocId] ?? tracebackDocId}
          </p>
          <Button variant="outline" size="sm" className="w-full" onClick={onBackToTarget}>
            Back to target
          </Button>
        </div>
      ) : (
        tracebackEntries.length > 0 && (
          <div>
            <p className="mb-2 text-sm font-medium">Reference traceback</p>
            <div className="space-y-2">
              {tracebackEntries.map((entry) => (
                <Button
                  key={entry.key}
                  variant="outline"
                  className="h-auto w-full justify-start whitespace-normal px-3 py-2 text-left"
                  onClick={() => onTraceback(entry.documentId)}
                >
                  <div>
                    <p className="font-medium">{entry.label}</p>
                    {entry.quote && (
                      <p className="text-xs text-muted-foreground">{entry.quote}</p>
                    )}
                  </div>
                </Button>
              ))}
            </div>
          </div>
        )
      )}
    </aside>
  );
}
