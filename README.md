# DeliveryLint

Backend-first pipeline for linting implementation documents (draft SOWs, requirements, UAT plans, etc.) against reference materials.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,db]"
cp .env.example .env
```

### Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `mock` | `mock` (fixtures, no network) or `openai` |
| `OPENAI_API_KEY` | — | Required when `LLM_PROVIDER=openai` |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model for structured extraction |
| `DATABASE_URL` | `sqlite:///deliverylint.db` | SQLite persistence URL |

## Run sample pipeline (in-memory, no LLM)

```bash
python -m backend.app.scripts.run_sample_pipeline
```

With real OpenAI (requires `OPENAI_API_KEY` in `.env`):

```bash
LLM_PROVIDER=openai python -m backend.app.scripts.run_sample_pipeline
```

## Run tests

```bash
pytest
```

## Run API (Phase 6+)

```bash
uvicorn backend.app.main:app --reload
```

POST `http://127.0.0.1:8000/analysis/lint` returns a `PipelineResult` with `CorrectionUIResponse`.

Upload your own documents:

- `POST /analysis/lint/upload` — multipart form: `target_file`, `target_doc_type`, optional `reference_files[]`, optional `reference_metadata` (JSON array of profile hints per reference file)
- `POST /analysis/lint/custom` — JSON body with document text (`CustomLintRequest`); each reference may include `profile_hints` (`doc_type`, `origin`, `status`, `recency_date`)

Optional query params: `include_debug=true`. Every run is saved automatically; use `GET /analysis/runs` to list them or `DELETE /analysis/runs` to clear all.

## Frontend (Phase 8)

```bash
cd frontend && npm install && npm run dev
```

Requires the API running on port 8000. Findings are grouped by `ReviewPriority`.

## Pipeline

Reference documents: `SourceProfiler` → `FactParser` → `FactClusterer`

Target document: `TargetDocumentParser`

Lint: `LintEngine` → `CorrectionUIResponse`
