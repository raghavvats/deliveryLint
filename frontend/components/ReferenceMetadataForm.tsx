import {
  EMPTY_REFERENCE_HINTS,
  REFERENCE_DOC_TYPES,
  ReferenceProfileHints,
  SOURCE_ORIGINS,
  SOURCE_STATUSES,
} from "../lib/constants";

type ReferenceMetadataFormProps = {
  filename: string;
  hints: ReferenceProfileHints;
  onChange: (hints: ReferenceProfileHints) => void;
};

export function ReferenceMetadataForm({
  filename,
  hints,
  onChange,
}: ReferenceMetadataFormProps) {
  const update = (field: keyof ReferenceProfileHints, value: string) => {
    onChange({ ...hints, [field]: value });
  };

  return (
    <div className="reference-metadata">
      <p className="reference-metadata-title">{filename}</p>
      <div className="reference-metadata-grid">
        <div className="upload-field">
          <label>Document type</label>
          <select
            value={hints.user_provided_doc_type}
            onChange={(e) => update("user_provided_doc_type", e.target.value)}
          >
            {REFERENCE_DOC_TYPES.map((option) => (
              <option key={option.value || "infer"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="upload-field">
          <label>Origin</label>
          <select
            value={hints.user_provided_origin}
            onChange={(e) => update("user_provided_origin", e.target.value)}
          >
            {SOURCE_ORIGINS.map((option) => (
              <option key={option.value || "infer"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="upload-field">
          <label>Status</label>
          <select
            value={hints.user_provided_status}
            onChange={(e) => update("user_provided_status", e.target.value)}
          >
            {SOURCE_STATUSES.map((option) => (
              <option key={option.value || "infer"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="upload-field">
          <label>Recency date (optional)</label>
          <input
            type="date"
            value={hints.user_provided_recency_date}
            onChange={(e) => update("user_provided_recency_date", e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}

export function createReferenceUploadState(file: File) {
  return {
    key: `${file.name}:${file.size}:${file.lastModified}`,
    file,
    hints: { ...EMPTY_REFERENCE_HINTS },
  };
}
