export type ReviewPriority = "needs_fix" | "needs_review" | "quality_suggestion" | "info";

export type CorrectionSourceSummary = {
  source_profile_id: string;
  document_id: string;
  doc_type: string;
  authority_level: number;
  status: string;
  summary: string;
};

export type CorrectionFindingView = {
  id: string;
  priority: ReviewPriority;
  finding_type: string;
  severity: string;
  confidence: number;
  title: string;
  message: string;
  recommendation?: string | null;
  target_quote?: string | null;
  reference_quotes?: string[];
  related_source_summaries?: CorrectionSourceSummary[];
  rule_id: string;
};

export type CorrectionSummary = {
  total_findings: number;
  needs_fix_count: number;
  needs_review_count: number;
  quality_suggestion_count: number;
  info_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  average_confidence?: number | null;
  has_blocking_issues: boolean;
};

export type CorrectionUIResponse = {
  project_id: string;
  target_document: {
    id: string;
    filename?: string | null;
    doc_type: string;
  };
  summary: CorrectionSummary;
  findings: CorrectionFindingView[];
  lint_warnings: { code: string; message: string }[];
};

export type PipelineResult = {
  correction_ui_response: CorrectionUIResponse;
  analysis_run_id?: number | null;
};

export type AnalysisRunSummary = {
  id: number;
  project_id: string;
  created_at: string;
};

export const PRIORITY_LABELS: Record<ReviewPriority, string> = {
  needs_fix: "Needs Fix",
  needs_review: "Needs Review",
  quality_suggestion: "Quality Suggestions",
  info: "Info / Coverage",
};

export const PRIORITY_ORDER: ReviewPriority[] = [
  "needs_fix",
  "needs_review",
  "quality_suggestion",
  "info",
];
