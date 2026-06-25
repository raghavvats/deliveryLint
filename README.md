# DeliveryLint

DeliveryLint is a structured review assistant for implementation documents—draft SOWs, requirements docs, UAT plans, project plans, change orders, and status reports. It compares a **target** document against **reference** materials (signed SOWs, approved requirements, meeting notes, client emails, etc.) and surfaces contradictions, unsupported claims, completeness gaps, and quality issues with tracebacks to source text.

## Features

- **Project dashboard** (`/`) — Create projects, upload shared reference documents once, then lint multiple target documents against the cached reference set. Supports `.txt`, `.md`, and `.pdf` uploads.
- **Correction triage UI** (`/runs/[runId]`) — Navigate findings by priority, view the target document with highlights, and follow tracebacks to reference excerpts.
- **Lint pipeline** — Profiles references, extracts and clusters facts, parses the target, and runs rule-based checks augmented by LLM extraction.
- **REST API** — Programmatic linting via JSON or multipart upload, plus project and run management.
- **Benchmark harness** (`/test`) — Run curated benchmark suites from `testFiles/` against answer keys, score recall, and export markdown reports. Also available as a CLI.

Finding types include contradictions, unsupported claims, completeness issues, and rubric-quality suggestions. Results are grouped by review priority: `NEEDS_FIX`, `NEEDS_REVIEW`, `QUALITY_SUGGESTION`, and `INFO`.

## Requirements

- Python 3.11+
- Node.js 18+ (for the frontend)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[db]"
cp .env.example .env
```

Install optional dev tools (Ruff linter):

```bash
pip install -e ".[dev,db]"
```

### Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `mock` | `mock` (fixture-backed responses, no network) or `openai` |
| `OPENAI_API_KEY` | — | Required when `LLM_PROVIDER=openai` |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model for structured extraction |
| `DATABASE_URL` | `sqlite:///deliverylint.db` | SQLite persistence URL |

For meaningful lint results and benchmark recall scores, set `LLM_PROVIDER=openai` and provide a valid `OPENAI_API_KEY`.

## Run the application

Start the API (port 8000):

```bash
uvicorn backend.app.main:app --reload
```

Start the frontend (port 3000):

```bash
cd frontend && npm install && npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The Next.js dev server proxies `/api/*` to the backend at `http://127.0.0.1:8000`.

### Typical workflow

1. Create a project on the dashboard.
2. Upload reference documents (signed SOW, requirements, emails, etc.). Optional metadata hints (doc type, origin, status, recency) improve profiling.
3. Upload a target document and choose its doc type. Linting runs in the background.
4. Open the run from the project tile to triage findings in the correction UI.

## Sample pipeline (CLI)

A built-in sample scenario is available for quick pipeline checks without the UI:

```bash
python -m backend.app.scripts.run_sample_pipeline
```

With OpenAI:

```bash
LLM_PROVIDER=openai python -m backend.app.scripts.run_sample_pipeline
```

The same built-in sample is also exposed at `POST /analysis/lint` for API consumers.

## Benchmark test harness

Five benchmark suites live under `testFiles/deliverylint_suite_*`. Each suite has a target document, reference markdown files, and an `answer_key.md` with expected findings.

**Web UI:** [http://localhost:3000/test](http://localhost:3000/test)

**CLI:**

```bash
python -m backend.app.scripts.run_test_harness --list
python -m backend.app.scripts.run_test_harness              # run all suites
python -m backend.app.scripts.run_test_harness --save        # persist results to the database
```

Harness recall scoring requires `LLM_PROVIDER=openai`. With `mock`, suites run but scores are not meaningful.

## API overview

Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

| Area | Endpoints |
|------|-----------|
| **Analysis** | `POST /analysis/lint` (built-in sample), `POST /analysis/lint/custom` (JSON body), `POST /analysis/lint/upload` (multipart) |
| **Runs** | `GET /analysis/runs`, `GET /analysis/runs/{id}`, `PATCH /analysis/runs/{id}`, `DELETE /analysis/runs/{id}`, `DELETE /analysis/runs` |
| **Projects** | `GET/POST /projects`, `GET/DELETE /projects/{id}`, reference and target upload endpoints |
| **Harness** | `GET /test/suites`, `POST /test/runs`, `GET /test/runs`, `GET /test/runs/{id}/export.md` |

Upload endpoints accept `.txt`, `.md`, and `.pdf` files. PDFs are converted to markdown via MarkItDown.

Optional query param on lint endpoints: `include_debug=true`.

## Pipeline

```
Reference documents:  SourceProfiler → FactParser → FactClusterer
Target document:      TargetDocumentParser
Lint:                 LintEngine → CorrectionUIResponse
```

## Project structure

```
backend/app/          FastAPI app, pipeline, services, test harness
frontend/             Next.js dashboard, correction UI, harness page
testFiles/            Benchmark suites for the test harness
```
