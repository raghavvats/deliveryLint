export type ReviewPriority = "needs_fix" | "needs_review" | "quality_suggestion" | "info";

export type AnalysisRunStatus = "processing" | "completed" | "failed";

export type TextSpan = {
  quote?: string | null;
  section_title?: string | null;
  page?: number | null;
  line_start?: number | null;
  line_end?: number | null;
  char_start?: number | null;
  char_end?: number | null;
};

export type CorrectionSourceSummary = {
  source_profile_id: string;
  document_id: string;
  doc_type: string;
  authority_level: number;
  status: string;
  summary: string;
};

export type ReferenceEvidenceView = {
  fact_id: string;
  document_id: string;
  source_profile_id: string;
  quote: string;
  location: TextSpan;
};

export type CorrectionFindingView = {
  id: string;
  priority: ReviewPriority;
  finding_type: string;
  severity: string;
  confidence: number;
  title: string;
  message: string;
  target_quote?: string | null;
  reference_quotes?: string[];
  target_location?: TextSpan | null;
  related_source_summaries?: CorrectionSourceSummary[];
  reference_evidence?: ReferenceEvidenceView[];
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

export type CorrectionReferenceDocument = {
  document_id: string;
  filename?: string | null;
  text: string;
  doc_type: string;
  source_profile_id: string;
};

export type CorrectionUIResponse = {
  project_id: string;
  target_document: {
    id: string;
    project_id?: string;
    filename?: string | null;
    text: string;
    doc_type: string;
  };
  target_profile?: Record<string, unknown>;
  reference_documents?: CorrectionReferenceDocument[];
  summary: CorrectionSummary;
  findings: CorrectionFindingView[];
  lint_warnings: { code: string; message: string }[];
};

export type RunFindingsSummary = {
  total_findings: number;
  needs_fix_count: number;
  needs_review_count: number;
  has_blocking_issues: boolean;
};

export type AnalysisRunSummary = {
  id: number;
  project_id: string;
  name: string;
  created_at: string;
  status: AnalysisRunStatus;
  error_message?: string | null;
  findings_summary?: RunFindingsSummary | null;
};

export type AnalysisRunDetail = AnalysisRunSummary & {
  correction_ui_response?: CorrectionUIResponse | null;
};

export type ProjectSummary = {
  id: string;
  name: string;
  created_at: string;
  reference_count: number;
  target_count: number;
  processing_count: number;
};

export type ReferenceDocumentSummary = {
  id: string;
  project_id: string;
  filename: string;
  doc_type: string;
  created_at: string;
  status?: "processing" | "ready" | "failed";
  error_message?: string | null;
};

export type ReferenceDocumentDetail = ReferenceDocumentSummary & {
  text: string;
};

export type ProjectDetail = {
  id: string;
  name: string;
  created_at: string;
  references: ReferenceDocumentSummary[];
  runs: AnalysisRunSummary[];
};

export type TargetUploadResponse = {
  analysis_run_id: number;
  status: AnalysisRunStatus;
  project_id: string;
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
