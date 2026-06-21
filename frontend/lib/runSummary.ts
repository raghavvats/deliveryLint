import type { RunFindingsSummary } from "./types";

export function formatRunFindingsSummary(summary: RunFindingsSummary | null | undefined): string {
  if (!summary) {
    return "No findings yet";
  }
  if (summary.total_findings === 0) {
    return "No issues found";
  }
  const parts: string[] = [];
  if (summary.needs_fix_count > 0) {
    parts.push(`${summary.needs_fix_count} need fix`);
  }
  if (summary.needs_review_count > 0) {
    parts.push(`${summary.needs_review_count} need review`);
  }
  if (parts.length === 0) {
    return `${summary.total_findings} finding${summary.total_findings === 1 ? "" : "s"}`;
  }
  return `${parts.join(" · ")} (${summary.total_findings} total)`;
}
