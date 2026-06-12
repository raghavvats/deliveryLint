export const TARGET_DOC_TYPES = [
  { value: "DRAFT_SOW", label: "Draft SOW" },
  { value: "REQUIREMENTS_DOC", label: "Requirements doc" },
  { value: "UAT_PLAN", label: "UAT plan" },
  { value: "PROJECT_PLAN", label: "Project plan" },
  { value: "CHANGE_ORDER", label: "Change order" },
  { value: "STATUS_REPORT", label: "Status report" },
] as const;

export const REFERENCE_DOC_TYPES = [
  { value: "", label: "Infer from content" },
  { value: "SIGNED_SOW", label: "Signed SOW" },
  { value: "DRAFT_SOW", label: "Draft SOW" },
  { value: "REQUIREMENTS_DOC", label: "Requirements doc" },
  { value: "UAT_PLAN", label: "UAT plan" },
  { value: "MEETING_TRANSCRIPT", label: "Meeting transcript" },
  { value: "CLIENT_EMAIL", label: "Client email" },
  { value: "PROJECT_PLAN", label: "Project plan" },
  { value: "CHANGE_ORDER", label: "Change order" },
  { value: "STATUS_REPORT", label: "Status report" },
  { value: "UNKNOWN", label: "Unknown" },
] as const;

export const SOURCE_ORIGINS = [
  { value: "", label: "Infer from content" },
  { value: "client", label: "Client" },
  { value: "internal", label: "Internal" },
  { value: "joint", label: "Joint" },
  { value: "unknown", label: "Unknown" },
] as const;

export const SOURCE_STATUSES = [
  { value: "", label: "Infer from content" },
  { value: "signed", label: "Signed" },
  { value: "approved", label: "Approved" },
  { value: "draft", label: "Draft" },
  { value: "informal", label: "Informal" },
  { value: "transcript", label: "Transcript" },
  { value: "unknown", label: "Unknown" },
] as const;

export type TargetDocType = (typeof TARGET_DOC_TYPES)[number]["value"];
export type AnalysisMode = "sample" | "upload";

export type ReferenceProfileHints = {
  user_provided_doc_type: string;
  user_provided_origin: string;
  user_provided_status: string;
  user_provided_recency_date: string;
};

export const EMPTY_REFERENCE_HINTS: ReferenceProfileHints = {
  user_provided_doc_type: "",
  user_provided_origin: "",
  user_provided_status: "",
  user_provided_recency_date: "",
};

export type ReferenceUploadState = {
  key: string;
  file: File;
  hints: ReferenceProfileHints;
};

export function referenceFileKey(file: File): string {
  return `${file.name}:${file.size}:${file.lastModified}`;
}

export function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error ?? new Error("Failed to read file"));
    reader.readAsText(file);
  });
}

export function hintsToPayload(hints: ReferenceProfileHints): Record<string, string> {
  const payload: Record<string, string> = {};
  if (hints.user_provided_doc_type) {
    payload.user_provided_doc_type = hints.user_provided_doc_type;
  }
  if (hints.user_provided_origin) {
    payload.user_provided_origin = hints.user_provided_origin;
  }
  if (hints.user_provided_status) {
    payload.user_provided_status = hints.user_provided_status;
  }
  if (hints.user_provided_recency_date) {
    payload.user_provided_recency_date = hints.user_provided_recency_date;
  }
  return payload;
}
