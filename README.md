# DeliveryLint

Backend-first pipeline for linting implementation documents (draft SOWs, requirements, UAT plans, etc.) against reference materials.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run sample pipeline (in-memory, no LLM)

```bash
python -m backend.app.scripts.run_sample_pipeline
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

Optional query params: `include_debug=true`, `persist=true` (SQLite).

## Frontend (Phase 8)

```bash
cd frontend && npm install && npm run dev
```

Requires the API running on port 8000. Findings are grouped by `ReviewPriority`.

## Pipeline

Reference documents: `SourceProfiler` → `FactParser` → `FactClusterer`

Target document: `TargetDocumentParser`

Lint: `LintEngine` → `CorrectionUIResponse`
