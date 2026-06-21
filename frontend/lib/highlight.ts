import type { TextSpan } from "./types";

export type ResolvedSpan = {
  start: number;
  end: number;
};

const WORD_CHAR = /[\p{L}\p{N}_'-]/u;

function isWordChar(char: string): boolean {
  return WORD_CHAR.test(char);
}

function expandToWordBoundaries(text: string, start: number, end: number): ResolvedSpan {
  let expandedStart = start;
  let expandedEnd = end;

  while (expandedStart > 0 && isWordChar(text[expandedStart - 1])) {
    expandedStart -= 1;
  }
  while (expandedEnd < text.length && isWordChar(text[expandedEnd])) {
    expandedEnd += 1;
  }

  return { start: expandedStart, end: expandedEnd };
}

function normalizeQuote(quote: string): string {
  return quote
    .trim()
    .toLowerCase()
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201c\u201d]/g, '"')
    .replace(/\s+/g, " ");
}

function findQuoteSpanLoose(text: string, quote: string): ResolvedSpan | null {
  const trimmed = quote.trim();
  if (!trimmed) {
    return null;
  }
  const words = trimmed.split(/\s+/);
  if (words.length < 2) {
    return null;
  }
  const pattern = words.map((word) => word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("\\s+");
  const match = new RegExp(pattern, "is").exec(text);
  if (!match) {
    return null;
  }
  return expandToWordBoundaries(text, match.index, match.index + match[0].length);
}

function findQuoteSpan(text: string, quote: string): ResolvedSpan | null {
  const trimmed = quote.trim();
  if (!trimmed) {
    return null;
  }
  const index = text.indexOf(trimmed);
  if (index >= 0) {
    return expandToWordBoundaries(text, index, index + trimmed.length);
  }
  const loose = findQuoteSpanLoose(text, trimmed);
  if (loose) {
    return loose;
  }
  const normalizedQuote = normalizeQuote(trimmed);
  if (normalizedQuote.length < 12) {
    return null;
  }
  const normalizedText = normalizeQuote(text);
  const normalizedIndex = normalizedText.indexOf(normalizedQuote);
  if (normalizedIndex < 0) {
    return null;
  }
  return expandToWordBoundaries(text, normalizedIndex, normalizedIndex + trimmed.length);
}

function lineSpan(text: string, lineStart: number, lineEnd?: number | null): ResolvedSpan | null {
  const lines = text.split("\n");
  if (lineStart < 1 || lineStart > lines.length) {
    return null;
  }
  const endLine = lineEnd && lineEnd >= lineStart ? lineEnd : lineStart;
  let start = 0;
  for (let i = 0; i < lineStart - 1; i += 1) {
    start += lines[i].length + 1;
  }
  let end = start;
  for (let i = lineStart - 1; i < endLine; i += 1) {
    end += lines[i].length + (i < lines.length - 1 ? 1 : 0);
  }
  return expandToWordBoundaries(text, start, end);
}

export function resolveSpan(text: string, span: TextSpan | null | undefined): ResolvedSpan | null {
  if (!span) {
    return null;
  }

  if (span.quote?.trim()) {
    const fromQuote = findQuoteSpan(text, span.quote);
    if (fromQuote) {
      return fromQuote;
    }
  }

  let resolved: ResolvedSpan | null = null;
  if (
    span.char_start != null &&
    span.char_end != null &&
    span.char_end > span.char_start &&
    span.char_end <= text.length
  ) {
    resolved = { start: span.char_start, end: span.char_end };
  } else if (span.line_start != null) {
    resolved = lineSpan(text, span.line_start, span.line_end);
  }

  if (resolved) {
    return expandToWordBoundaries(text, resolved.start, resolved.end);
  }

  return null;
}

export type HighlightSegment = {
  start?: number;
  end?: number;
  kind: "active" | "reference";
  id?: string;
  quote?: string | null;
  section_title?: string | null;
  page?: number | null;
  line_start?: number | null;
  line_end?: number | null;
  char_start?: number | null;
  char_end?: number | null;
};

export function buildHighlightedSegments(
  text: string,
  spans: HighlightSegment[],
): Array<{ text: string; highlight?: HighlightSegment["kind"]; id?: string }> {
  const sorted = spans
    .map((span) => {
      const resolved =
        span.start != null && span.end != null
          ? expandToWordBoundaries(text, span.start, span.end)
          : resolveSpan(text, span);
      if (!resolved) {
        return null;
      }
      return { ...span, ...resolved };
    })
    .filter((span): span is HighlightSegment & ResolvedSpan => span !== null && span.start < span.end)
    .sort((a, b) => a.start - b.start || a.end - b.end);

  const segments: Array<{ text: string; highlight?: HighlightSegment["kind"]; id?: string }> = [];
  let cursor = 0;

  for (const span of sorted) {
    if (span.start < cursor) {
      continue;
    }
    if (span.start > cursor) {
      segments.push({ text: text.slice(cursor, span.start) });
    }
    segments.push({
      text: text.slice(span.start, span.end),
      highlight: span.kind,
      id: span.id,
    });
    cursor = span.end;
  }

  if (cursor < text.length) {
    segments.push({ text: text.slice(cursor) });
  }

  return segments;
}
