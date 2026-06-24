"use client";

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";

import { DocumentViewer } from "@/components/correction/DocumentViewer";
import { FindingNavigator } from "@/components/correction/FindingNavigator";
import { FindingPanel } from "@/components/correction/FindingPanel";
import { Button } from "@/components/ui/button";
import { getRun } from "@/lib/api";
import type { HighlightSegment } from "@/lib/highlight";
import type { CorrectionUIResponse } from "@/lib/types";

type CorrectionPageProps = {
  runId: number;
};

const PANEL_WIDTH = 360;
const PANEL_GAP = 16;

function panelPosition(anchor: DOMRect | null): CSSProperties {
  if (!anchor) {
    return {
      position: "fixed",
      right: PANEL_GAP,
      top: 96,
      width: PANEL_WIDTH,
      maxHeight: "calc(100vh - 120px)",
    };
  }

  const viewportWidth = typeof window !== "undefined" ? window.innerWidth : 1200;
  const viewportHeight = typeof window !== "undefined" ? window.innerHeight : 800;
  let left = anchor.right + PANEL_GAP;
  if (left + PANEL_WIDTH > viewportWidth - PANEL_GAP) {
    left = Math.max(PANEL_GAP, anchor.left - PANEL_WIDTH - PANEL_GAP);
  }
  if (left + PANEL_WIDTH > viewportWidth - PANEL_GAP) {
    left = PANEL_GAP;
  }

  let top = anchor.top;
  const maxHeight = Math.min(480, viewportHeight - top - 96);
  if (top + maxHeight > viewportHeight - 80) {
    top = Math.max(80, viewportHeight - maxHeight - 96);
  }

  return {
    position: "fixed",
    left,
    top,
    width: PANEL_WIDTH,
    maxHeight,
  };
}

export function CorrectionPage({ runId }: CorrectionPageProps) {
  const [data, setData] = useState<CorrectionUIResponse | null>(null);
  const [status, setStatus] = useState<string>("loading");
  const [error, setError] = useState<string | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [tracebackDocId, setTracebackDocId] = useState<string | null>(null);
  const [highlightRect, setHighlightRect] = useState<DOMRect | null>(null);

  const load = useCallback(async () => {
    const run = await getRun(runId);
    setStatus(run.status);
    if (run.status !== "completed" || !run.correction_ui_response) {
      setError(run.error_message ?? "This run is not ready for review yet.");
      setData(null);
      return;
    }
    setData(run.correction_ui_response);
    setError(null);
  }, [runId]);

  useEffect(() => {
    void load().catch((err) => {
      setError(err instanceof Error ? err.message : "Failed to load run");
      setStatus("failed");
    });
  }, [load]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (!data || data.findings.length === 0) {
        return;
      }
      if (event.key === "ArrowLeft") {
        setActiveIndex((index) => Math.max(0, index - 1));
      }
      if (event.key === "ArrowRight") {
        setActiveIndex((index) => Math.min(data.findings.length - 1, index + 1));
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [data]);

  useEffect(() => {
    setTracebackDocId(null);
  }, [activeIndex]);

  const activeFinding = data?.findings[activeIndex];
  const referenceDocuments = data?.reference_documents ?? [];

  const targetHighlights = useMemo((): HighlightSegment[] => {
    if (!activeFinding?.target_location) {
      return [];
    }
    return [
      {
        ...activeFinding.target_location,
        kind: "active",
        id: activeFinding.id,
      },
    ];
  }, [activeFinding]);

  const referenceHighlights = useMemo((): HighlightSegment[] => {
    if (!activeFinding || !tracebackDocId) {
      return [];
    }
    const fromEvidence = (activeFinding.reference_evidence ?? [])
      .filter((evidence) => evidence.document_id === tracebackDocId)
      .map((evidence) => ({
        ...evidence.location,
        kind: "reference" as const,
        id: evidence.fact_id,
      }));
    if (fromEvidence.length > 0) {
      return fromEvidence;
    }
    return (activeFinding.reference_quotes ?? []).map((quote, index) => ({
      quote,
      kind: "reference" as const,
      id: `reference-quote-${index}`,
    }));
  }, [activeFinding, tracebackDocId]);

  const viewingReference = tracebackDocId
    ? referenceDocuments.find((doc) => doc.document_id === tracebackDocId)
    : null;

  const activeHighlightId = viewingReference
    ? referenceHighlights[0]?.id
    : activeFinding?.id;

  const panelStyle = useMemo(() => panelPosition(highlightRect), [highlightRect]);

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Loading review…
      </div>
    );
  }

  if (!data || !activeFinding) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <Button asChild variant="outline" size="sm">
          <Link href="/">
            <ArrowLeft className="h-4 w-4" />
            Back to dashboard
          </Link>
        </Button>
        <div className="mt-8 rounded-xl border p-8 text-center">
          <p className="text-lg font-medium">
            {status === "processing" ? "Still processing" : "Run unavailable"}
          </p>
          <p className="mt-2 text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-24">
      <header className="border-b bg-card">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4">
          <div className="min-w-0">
            <Button asChild variant="ghost" size="sm" className="mb-2 -ml-2">
              <Link href="/">
                <ArrowLeft className="h-4 w-4" />
                Dashboard
              </Link>
            </Button>
            <h1 className="truncate text-xl font-semibold">
              {data.target_document.filename ?? "Target document"}
            </h1>
            <p className="text-sm text-muted-foreground">
              {data.summary.total_findings} finding
              {data.summary.total_findings === 1 ? "" : "s"} · {data.target_document.doc_type}
            </p>
          </div>
          {viewingReference && (
            <Button variant="outline" size="sm" onClick={() => setTracebackDocId(null)}>
              Back to target
            </Button>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-4 pr-[calc(1rem+380px)]">
        <section className="min-h-[65vh]">
          {viewingReference ? (
            <div>
              <p className="mb-2 text-sm font-medium text-muted-foreground">
                Reference: {viewingReference.filename ?? viewingReference.document_id}
              </p>
              <DocumentViewer
                text={viewingReference.text}
                filename={viewingReference.filename}
                highlights={referenceHighlights}
                activeHighlightId={activeHighlightId}
                onActiveHighlightRect={setHighlightRect}
                className="min-h-[65vh]"
              />
            </div>
          ) : (
            <DocumentViewer
              text={data.target_document.text}
              filename={data.target_document.filename}
              highlights={targetHighlights}
              activeHighlightId={activeHighlightId}
              onActiveHighlightRect={setHighlightRect}
              className="min-h-[65vh]"
            />
          )}
        </section>
      </main>

      <div className="z-30 overflow-auto rounded-lg shadow-lg" style={panelStyle}>
        <FindingPanel
          finding={activeFinding}
          referenceDocuments={referenceDocuments}
          tracebackDocId={tracebackDocId}
          onTraceback={(documentId) => setTracebackDocId(documentId)}
          onBackToTarget={() => setTracebackDocId(null)}
        />
      </div>

      <FindingNavigator
        finding={activeFinding}
        index={activeIndex}
        total={data.findings.length}
        onPrevious={() => setActiveIndex((index) => Math.max(0, index - 1))}
        onNext={() =>
          setActiveIndex((index) => Math.min(data.findings.length - 1, index + 1))
        }
      />
    </div>
  );
}
