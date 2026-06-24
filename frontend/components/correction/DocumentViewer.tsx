"use client";

import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { buildHighlightedSegments, type HighlightSegment } from "@/lib/highlight";
import { cn } from "@/lib/utils";

type DocumentViewerProps = {
  text: string;
  highlights: HighlightSegment[];
  activeHighlightId?: string;
  filename?: string | null;
  className?: string;
  onActiveHighlightRect?: (rect: DOMRect | null) => void;
};

function isMarkdownFilename(filename?: string | null): boolean {
  const lower = filename?.toLowerCase() ?? "";
  return lower.endsWith(".md") || lower.endsWith(".pdf");
}

function MarkdownChunk({ text }: { text: string }) {
  return (
    <div className="markdown-chunk">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ children, ...props }) => (
            <div className="markdown-table-wrapper">
              <table {...props}>{children}</table>
            </div>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}

function HighlightSpan({
  text,
  kind,
  id,
}: {
  text: string;
  kind: "active" | "reference";
  id?: string;
}) {
  const className = kind === "active" ? "active-highlight" : "reference-highlight";
  return (
    <span data-highlight-id={id} className={cn("text-highlight", className)}>
      {text}
    </span>
  );
}

export function DocumentViewer({
  text,
  highlights,
  activeHighlightId,
  filename,
  className,
  onActiveHighlightRect,
}: DocumentViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const segments = buildHighlightedSegments(text, highlights);
  const markdownMode = isMarkdownFilename(filename);

  useEffect(() => {
    if (!activeHighlightId || !containerRef.current) {
      onActiveHighlightRect?.(null);
      return;
    }
    const active = containerRef.current.querySelector(`[data-highlight-id="${activeHighlightId}"]`);
    if (active instanceof HTMLElement) {
      active.scrollIntoView({ behavior: "smooth", block: "center" });
      onActiveHighlightRect?.(active.getBoundingClientRect());
    } else {
      onActiveHighlightRect?.(null);
    }
  }, [activeHighlightId, text, highlights, onActiveHighlightRect]);

  useEffect(() => {
    if (!onActiveHighlightRect) {
      return;
    }
    const update = () => {
      if (!activeHighlightId || !containerRef.current) {
        onActiveHighlightRect(null);
        return;
      }
      const active = containerRef.current.querySelector(`[data-highlight-id="${activeHighlightId}"]`);
      if (active instanceof HTMLElement) {
        onActiveHighlightRect(active.getBoundingClientRect());
      }
    };
    window.addEventListener("scroll", update, true);
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update, true);
      window.removeEventListener("resize", update);
    };
  }, [activeHighlightId, onActiveHighlightRect, text, highlights]);

  return (
    <div
      ref={containerRef}
      className={cn(
        "document-viewer overflow-auto rounded-lg border bg-card p-4",
        markdownMode ? "document-viewer-markdown" : "document-viewer-plain",
        className,
      )}
    >
      {segments.map((segment, index) => {
        if (!segment.highlight) {
          if (markdownMode) {
            return <MarkdownChunk key={index} text={segment.text} />;
          }
          return <span key={index}>{segment.text}</span>;
        }
        return (
          <HighlightSpan
            key={index}
            text={segment.text}
            kind={segment.highlight}
            id={segment.id}
          />
        );
      })}
    </div>
  );
}
