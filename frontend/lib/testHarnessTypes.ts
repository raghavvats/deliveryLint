export interface ExpectedFinding {
  index: number;
  acceptable_types: string[];
  description: string;
}

export interface TestSuiteDefinition {
  id: string;
  name: string;
  directory: string;
  target_filename: string;
  target_doc_type: string;
  expected_findings: ExpectedFinding[];
  reference_count: number;
}

export interface ExpectedFindingResult {
  index: number;
  acceptable_types: string[];
  description: string;
  caught: boolean;
  matched_finding_id?: string | null;
  matched_finding_type?: string | null;
  matched_title?: string | null;
  match_score?: number | null;
}

export interface ActualFindingSnapshot {
  id: string;
  finding_type: string;
  title: string;
  message: string;
}

export interface SuiteRunResult {
  suite_id: string;
  suite_name: string;
  target_filename: string;
  target_doc_type: string;
  status: string;
  error_message?: string | null;
  expected_count: number;
  caught_count: number;
  missed_count: number;
  recall_pct: number;
  actual_finding_count: number;
  extra_finding_count: number;
  expected_results: ExpectedFindingResult[];
  extra_findings: ActualFindingSnapshot[];
  duration_ms?: number | null;
}

export interface HarnessRunSummary {
  id: number;
  created_at: string;
  status: string;
  llm_provider: string;
  suite_count: number;
  total_expected: number;
  total_caught: number;
  recall_pct: number;
  error_message?: string | null;
}

export interface HarnessRunDetail extends HarnessRunSummary {
  missed_count: number;
  suite_results: SuiteRunResult[];
}
