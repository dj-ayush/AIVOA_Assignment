# DeviationIQ Backend

FastAPI service for deviation extraction, correction, document processing, impact/severity assessment, and persistence.

## Runtime Entry Point

The backend application is created in:

```text
backend/app/main.py
```

It registers FastAPI routes, configures CORS, invokes the LangGraph workflow, extracts uploaded document text, and persists saved deviation records.

## Request Flow

```mermaid
flowchart TD
  Client["React Frontend"] --> Routes["FastAPI Routes"]

  Routes --> Upload{"Document Upload?"}

  Upload -->|Yes| ExtractText["Extract document text"]
  Upload -->|No| Chat["Chat Request"]

  ExtractText --> Graph["LangGraph Workflow"]
  Chat --> Graph

  Graph --> Groq["Groq LLM"]
  Groq --> Schemas["Pydantic Validation"]
  Schemas --> Merge["Merge non-null fields"]
  Merge --> Response["Chat Response"]

  Routes --> Save["POST /api/save"]
  Save --> Persist{"Database Configured?"}

  Persist -->|Yes| MySQL["MySQL Database"]
  Persist -->|No| Ledger["JSON Ledger Fallback"]
```

## FastAPI Routes

| Method | Endpoint | Function | Purpose |
|---|---|---|---|
| `GET` | `/api/health` | `health` | Returns service health |
| `POST` | `/api/chat` | `chat` | Handles pasted text, corrections, and general messages |
| `POST` | `/api/upload` | `upload_document` | Handles PDF/TXT/EML extraction |
| `POST` | `/api/save` | `save` | Persists finalized deviation |
| `POST` | `/api/commit` | `commit` | Compatibility alias for save |
| `GET` | `/api/ledger` | `get_ledger` | Reads saved records |
| `GET` | `/api/observability` | `get_observability` | Returns recent in-memory metrics |

## LangGraph Workflow

Defined in `app/graph.py`.

```mermaid
flowchart TD
  Start([START]) --> Entry{document_text?}
  Entry -->|yes| Document[document_extract_node]
  Entry -->|no| Intent[classify_intent_node]
  Intent -->|new_deviation| Extract[extract_new_node]
  Intent -->|edit_fields| Edit[edit_fields_node]
  Intent -->|general| General[general_chat_node]
  Document --> End([END])
  Extract --> End
  Edit --> End
  General --> End
```

Node behavior:

- `classify_intent_node`: returns `IntentResult`.
- `extract_new_node`: returns a merged `DeviationForm` and `RiskAssessment`.
- `edit_fields_node`: returns patch-only changes from `PatchOutput`.
- `document_extract_node`: extracts from uploaded document text.
- `general_chat_node`: returns text only and preserves current form/risk state.

`_merge_non_null(...)` is the key update rule: fields returned as `null` do not overwrite existing state.

## Groq Integration

Implemented in `app/llm.py`.

- `get_client()` creates a Groq client from `GROQ_API_KEY`.
- `generate_structured(...)` requests JSON schema output and validates it with Pydantic.
- `generate_text(...)` is used only by `general_chat_node`.
- `_strict_json_schema(...)` marks object schemas as strict and disallows additional properties.

The configured model is `GROQ_MODEL`, defaulting to `openai/gpt-oss-20b`.

## Schemas

Implemented in `app/schemas.py`.

### Deviation form

| Field | Type | Notes |
|---|---|---|
| `complaint_source` | `Optional[str]` | Legacy key for source/reporting channel |
| `customer_name` | `Optional[str]` | Legacy key for reporter name/role/site/company |
| `product_name` | `Optional[str]` | Product or API |
| `product_strength` | `Optional[str]` | Strength or grade |
| `batch_lot_number` | `Optional[str]` | Batch or lot identifier |
| `affected_quantity` | `Optional[str]` | Quantity and units from source |
| `manufacturing_date` | `Optional[str]` | Manufacturing date |
| `expiry_date` | `Optional[str]` | Expiry date |
| `originating_site_block` | `Optional[str]` | Explicit site/block/suite/line only |
| `impacted_npm` | `Optional[str]` | Non-product material impact |
| `complaint_category` | `Optional[str]` | Legacy key for deviation category |
| `complaint_description` | `Optional[str]` | Legacy key for deviation summary |

### Impact and severity

| Field | Type | Notes |
|---|---|---|
| `severity` | `Optional[str]` | Minor, Major, or Critical |
| `suggested_next_action` | `Optional[str]` | Recommended QA action |
| `initial_risk_assessment` | `Optional[str]` | Impact, quality risk, containment, investigation status |

### API and graph models

| Model | Used by |
|---|---|
| `ExtractionOutput` | `extract_new_node`, `document_extract_node` |
| `PatchOutput` | `edit_fields_node` |
| `IntentResult` | `classify_intent_node` |
| `ChatRequest` | `POST /api/chat` |
| `ChatResponse` | `POST /api/chat`, `POST /api/upload` |

## Prompt Behavior

Prompts are in `app/prompts.py`.

The extraction prompts instruct the model to:

- leave unsupported fields as null
- avoid inferring site/block from product type or site name alone
- avoid inventing root causes
- produce deviation-specific categories
- generate impact/severity reasoning from observed quality risk and containment status

The edit prompt instructs the model to return a patch, not a full rewritten form. Risk fields are only re-evaluated when the correction changes the risk picture.

## Document Extraction

`POST /api/upload` accepts multipart uploads.

Supported extensions:

- `.pdf`
- `.txt`
- `.eml`

PDF handling:

```text
UploadFile bytes -> pypdf.PdfReader -> page.extract_text() -> LangGraph document_extract
```

TXT/EML handling:

```text
UploadFile bytes -> UTF-8 decode with ignored errors -> LangGraph document_extract
```

If extracted text is empty, the endpoint returns `422`.

## Persistence

Implemented in `app/database.py`.

Connection source:

```text
MYSQL_URL preferred
DATABASE_URL fallback, only if it is a MySQL URL
```

Driver:

```text
mysql-connector-python
```

Table:

```sql
CREATE TABLE IF NOT EXISTS deviations (
  id VARCHAR(32) PRIMARY KEY,
  committed_at VARCHAR(40) NOT NULL,
  form JSON NOT NULL,
  risk_assessment JSON NOT NULL
);
```

Save flow:

```text
/api/save
-> _build_record()
-> save_deviation_record(), if database configured
-> _append_to_json_ledger(), if not configured
```

Fallback file:

```text
backend/sample_data/qms_ledger.json
```

Database configuration errors and MySQL errors are returned as JSON `503` responses.

## Configuration

`.env.example` contains:

```env
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
MYSQL_URL=
DATABASE_URL=
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://gracious-enjoyment-production-524c.up.railway.app
```

| Variable | Required | Description |
|---|---:|---|
| `GROQ_API_KEY` | Yes for AI calls | Groq provider key |
| `GROQ_MODEL` | No | Groq model name |
| `MYSQL_URL` | No | Preferred MySQL connection string |
| `DATABASE_URL` | No | MySQL-compatible fallback connection string |
| `CORS_ORIGINS` | No | Extra comma-separated CORS origins |

Default CORS origins are defined in `app/config.py` and include local Vite origins plus the current Railway frontend origin.

## Local Run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Observability

Instrumentation is implemented in `app/observability.py` and uses only the Python standard library.

| Area | Where measured | Metrics |
| ---- | -------------- | ------- |
| API | FastAPI middleware in `app/main.py` | method, path, status code, latency, success/failure |
| Workflow | `observe_workflow()` around graph execution | total duration, success/failure, executed node count |
| LangGraph nodes | node wrappers in `app/graph.py` | node name, duration, success/failure |
| LLM calls | `app/llm.py` | model, operation, duration, success/failure, token usage when Groq returns it |
| Validation | `app/llm.py` after JSON parsing | Pydantic schema, duration, success/failure |
| Database | `app/database.py` | table creation, insert, read duration and success/failure |

The current application has no LLM retry loop, so retry attempts are recorded as `0`; correction retry time is not measured.

Inspect recent metrics:

```bash
curl http://localhost:8000/api/observability
```

## Evaluation

The repository-level evaluation runner executes the real graph against cases in `evaluation/cases.json`.

```bash
cd ..
python evaluation/run_evaluation.py
```

Outputs:

```text
evaluation/results.json
evaluation/results.md
```

See `evaluation/README.md` for the case format and metric definitions.

## Validation

```bash
python -m compileall app
python -c "from app.main import app; print(app.title)"
python -m unittest discover tests
```

Optional route check:

```bash
curl http://localhost:8000/api/health
```

Optional save check:

```bash
curl -X POST http://localhost:8000/api/save ^
  -H "Content-Type: application/json" ^
  -d "{\"form\":{},\"risk_assessment\":{}}"
```

## Deployment Notes

Backend deployment target:

```text
https://aivoaassignment-production.up.railway.app
```

Required Railway variables for live AI and database persistence:

```env
GROQ_API_KEY=<secret>
MYSQL_URL=mysql://USER:PASSWORD@HOST:PORT/DATABASE
```

Do not expose provider keys or database credentials to the frontend.

## Current Limitations

- No OCR for scanned PDFs.
- No authentication or authorization.
- JSON ledger fallback is not production persistence.
- No migration framework; table creation is handled directly in `database.py`.
- No backend test suite beyond compile/import/API smoke checks.
