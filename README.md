# DeviationIQ

AI-powered pharmaceutical deviation intake and management system.

## Demo / Deployment

- Repository: [https://github.com/dj-ayush/AIVOA_Assignment](https://github.com/dj-ayush/AIVOA_Assignment)
- Frontend: [https://gracious-enjoyment-production-524c.up.railway.app/](https://gracious-enjoyment-production-524c.up.railway.app/)
- Backend API: [https://aivoaassignment-production.up.railway.app](https://aivoaassignment-production.up.railway.app)
- OpenAPI: [https://aivoaassignment-production.up.railway.app/openapi.json](https://aivoaassignment-production.up.railway.app/openapi.json)

The deployed frontend and backend OpenAPI endpoint were reachable during this documentation pass.

## Overview

DeviationIQ is a two-panel QMS workflow for turning unstructured deviation information into a structured deviation record. A QA user can paste a deviation narrative, upload a PDF/TXT/EML report, review extracted fields in a read-only form, ask the copilot to correct specific values, and save the final record.

The frontend does not perform extraction locally. It sends text, current form state, current impact/severity state, and uploaded documents to FastAPI. The backend routes the request through LangGraph, calls Groq for structured output, validates the response with Pydantic models, and returns the updated deviation state to React.

The application is intentionally scoped to deviation intake. It does not implement authentication, CAPA tracking, dashboards, OCR, or multi-agent workflows. The implemented workflow is: intake -> extraction -> impact/severity assessment -> correction -> persistence.

## Key Capabilities

- Free-text deviation extraction through `/api/chat`
- PDF/TXT/EML document extraction through `/api/upload`
- LangGraph routing for document extraction, new deviation extraction, field edits, and general chat
- Groq structured JSON responses validated against Pydantic schemas
- Read-only React form populated from backend state
- Natural-language corrections using patch semantics
- Impact/severity assessment with recommended QA action
- Save to MySQL when configured, otherwise JSON ledger fallback

## Architecture

```mermaid
flowchart LR
  User[QA user] --> UI[React + Vite UI]
  UI --> API[src/api.js]
  API --> FastAPI[FastAPI app.main]
  FastAPI --> Graph[LangGraph StateGraph]
  Graph --> Router{Route}
  Router --> Doc[document_extract]
  Router --> Intent[classify_intent]
  Intent --> New[extract_new]
  Intent --> Edit[edit_fields]
  Intent --> General[general_chat]
  Doc --> Groq[Groq structured output]
  New --> Groq
  Edit --> Groq
  General --> GroqText[Groq text response]
  Groq --> Schemas[Pydantic schemas]
  GroqText --> Response[ChatResponse]
  Schemas --> Response
  Response --> UIState[React form + copilot state]
  UIState --> Save[/api/save]
  Save --> Persist{Persistence}
  Persist --> MySQL[MySQL deviations table]
  Persist --> Ledger[JSON ledger fallback]
```

## How It Works

1. The user enters a deviation description or uploads a PDF/TXT/EML document in `CopilotChat.jsx`.
2. `frontend/src/api.js` sends the request to FastAPI using `VITE_API_BASE_URL`.
3. `/api/chat` passes text plus current `DeviationForm` and `RiskAssessment` state to LangGraph.
4. `/api/upload` extracts text first, then passes document text and current state to LangGraph.
5. `graph.py` routes document input directly to `document_extract`; chat input goes through `classify_intent`.
6. Groq returns structured data for `ExtractionOutput`, `PatchOutput`, or `IntentResult`.
7. Pydantic validates the model output.
8. The backend merges non-null values into the existing form/risk state.
9. The React form renders returned fields and highlights changed values.
10. Corrections use `edit_fields`, which returns a patch instead of restating the whole form.
11. Save sends `{ form, risk_assessment }` to `/api/save`.
12. The backend writes to MySQL if configured; otherwise it appends to `backend/sample_data/qms_ledger.json`.

## Deviation Processing Pipeline

```text
Text input
-> /api/chat
-> classify_intent
-> extract_new | edit_fields | general_chat
-> Groq structured output
-> Pydantic validation
-> merge non-null fields
-> ChatResponse
-> React state update
```

```text
PDF/TXT/EML input
-> /api/upload
-> pypdf or UTF-8 text decode
-> document_extract
-> Groq structured output
-> Pydantic validation
-> form + impact/severity update
```

```text
Save
-> /api/save
-> build DEV-* record
-> MySQL deviations table, when MYSQL_URL/DATABASE_URL is configured
-> JSON ledger fallback, when no database URL is configured
```

## AI / LangGraph Workflow

The graph is defined in `backend/app/graph.py` with these nodes:

```mermaid
flowchart TD
  Start([START]) --> Entry{document_text?}
  Entry -->|yes| Document[document_extract]
  Entry -->|no| Classify[classify_intent]
  Classify -->|new_deviation| Extract[extract_new]
  Classify -->|edit_fields| Edit[edit_fields]
  Classify -->|general| General[general_chat]
  Document --> End([END])
  Extract --> End
  Edit --> End
  General --> End
```

- `classify_intent_node` asks Groq to classify text as `new_deviation`, `edit_fields`, or `general`.
- `extract_new_node` asks Groq for an `ExtractionOutput`.
- `edit_fields_node` asks Groq for a `PatchOutput`; null fields mean no change.
- `document_extract_node` extracts structured data from uploaded document text.
- `general_chat_node` returns a plain conversational response without changing form state.

Prompts instruct the model to avoid unsupported site/block inference, avoid invented root causes, and preserve existing fields unless the user explicitly changes them.

## Deviation Data Model

### `DeviationForm`

| Field | Type | Purpose |
|---|---|---|
| `complaint_source` | `Optional[str]` | Legacy key for how the deviation was reported |
| `customer_name` | `Optional[str]` | Legacy key for reporter name, role, department, site, or company |
| `product_name` | `Optional[str]` | Product or API name |
| `product_strength` | `Optional[str]` | Product strength or grade |
| `batch_lot_number` | `Optional[str]` | Batch or lot number |
| `affected_quantity` | `Optional[str]` | Quantity affected, preserving source units |
| `manufacturing_date` | `Optional[str]` | Manufacturing date as stated |
| `expiry_date` | `Optional[str]` | Expiry date as stated |
| `originating_site_block` | `Optional[str]` | Explicit site, area, block, suite, or line only |
| `impacted_npm` | `Optional[str]` | Impacted non-product materials, if stated |
| `complaint_category` | `Optional[str]` | Legacy key for deviation category |
| `complaint_description` | `Optional[str]` | Legacy key for structured deviation summary |

The `complaint_*` and `customer_name` names are internal compatibility keys. The UI labels use DeviationIQ terminology.

### `RiskAssessment`

| Field | Type | Purpose |
|---|---|---|
| `severity` | `Optional[str]` | `Minor`, `Major`, or `Critical` |
| `suggested_next_action` | `Optional[str]` | Recommended QA action |
| `initial_risk_assessment` | `Optional[str]` | Impact, product quality risk, containment, and investigation status |

### API Models

| Model | Purpose |
|---|---|
| `ChatRequest` | `/api/chat` input with message, current form, current risk, and history |
| `ChatResponse` | Backend response with reply, form, risk assessment, changed fields, status, and intent |
| `ExtractionOutput` | Full structured extraction result |
| `PatchOutput` | Patch-only edit result |
| `IntentResult` | Intent classification result |

## Prompt / Extraction Behavior

The prompts in `backend/app/prompts.py` constrain Groq to:

- fill fields only when explicitly stated or strongly evidenced
- leave unknown fields as null
- avoid inventing site blocks from dosage form or site name alone
- avoid invented root causes such as equipment wear or operator error
- generate deviation-specific categories
- focus impact assessment on observed risk, quality implications, containment, and investigation status
- return patches for corrections instead of rewriting the whole record
- reassess severity only when the correction changes the risk picture

## Document Extraction

`/api/upload` accepts:

- `.pdf`
- `.txt`
- `.eml`

PDF text is extracted with `pypdf` in `backend/app/pdf_utils.py`. TXT/EML files are decoded as UTF-8 with ignored decode errors. If no text can be extracted, the backend returns `422`.

OCR is not implemented.

## Frontend

The frontend is a React/Vite app under `frontend/src`.

- `App.jsx` owns form state, risk state, status, messages, changed fields, loading state, and save state.
- `api.js` wraps `/api/chat`, `/api/upload`, `/api/save`, and `/api/health`.
- `DeviationForm.jsx` renders the read-only form, impact panel, save button, reset button, and AI indicators.
- `CopilotChat.jsx` renders messages, document upload, typing/loading state, and text input.
- `StatusBadge.jsx` renders `Pending Triage` or `Ready to Save`.
- `constants.js` defines field layout and empty form/risk state.

## Backend

The backend is a FastAPI application under `backend/app`.

- `main.py`: routes, CORS, response construction, upload handling, save/ledger endpoints
- `graph.py`: LangGraph nodes and routing
- `prompts.py`: model instructions for extraction, correction, document processing, and general replies
- `schemas.py`: Pydantic models
- `llm.py`: Groq client and structured JSON response handling
- `database.py`: MySQL connection, table creation, save/read helpers, database error messages
- `config.py`: environment variables and CORS origins

## API Reference

| Method | Endpoint | Purpose | Input | Output |
|---|---|---|---|---|
| `GET` | `/api/health` | Health check | None | `{ "status": "ok" }` |
| `POST` | `/api/chat` | Text extraction, correction, or general reply | `ChatRequest` JSON | `ChatResponse` JSON |
| `POST` | `/api/upload` | Document extraction | Multipart file plus `current_form`, `current_risk` JSON strings | `ChatResponse` JSON |
| `POST` | `/api/save` | Save finalized deviation | `{ form, risk_assessment }` JSON | `{ status, record_id, storage }` |
| `POST` | `/api/commit` | Compatibility alias for save | Same as `/api/save` | Same as `/api/save` |
| `GET` | `/api/ledger` | Read saved records | None | List of saved records |

## Database / Persistence

The backend uses `mysql-connector-python`.

When `MYSQL_URL` or a MySQL `DATABASE_URL` is configured, saves go to a MySQL table:

```sql
CREATE TABLE IF NOT EXISTS deviations (
  id VARCHAR(32) PRIMARY KEY,
  committed_at VARCHAR(40) NOT NULL,
  form JSON NOT NULL,
  risk_assessment JSON NOT NULL
);
```

If no database URL is configured, records are appended to:

```text
backend/sample_data/qms_ledger.json
```

Invalid or unreachable MySQL configuration returns a JSON `503` from `/api/save` and `/api/ledger`.

## Configuration

### Backend

| Variable | Required | Purpose |
|---|---:|---|
| `GROQ_API_KEY` | Yes for AI calls | Groq API key used by `llm.py` |
| `GROQ_MODEL` | No | Model name; defaults to `openai/gpt-oss-20b` |
| `MYSQL_URL` | No | Preferred MySQL connection URL |
| `DATABASE_URL` | No | Compatibility MySQL connection URL |
| `CORS_ORIGINS` | No | Additional comma-separated allowed origins |

Example:

```env
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
MYSQL_URL=mysql://user:password@host:3306/deviationiq
DATABASE_URL=
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://gracious-enjoyment-production-524c.up.railway.app
```

### Frontend

| Variable | Required | Purpose |
|---|---:|---|
| `VITE_API_BASE_URL` | Yes | FastAPI base URL used by `src/api.js` |

Example:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Production value in `frontend/.env.production`:

```env
VITE_API_BASE_URL=https://aivoaassignment-production.up.railway.app
```

## Project Structure

```text
AIVOA-main/
  README.md
  backend/
    README.md
    requirements.txt
    app/
      config.py
      database.py
      graph.py
      llm.py
      main.py
      pdf_utils.py
      prompts.py
      schemas.py
    sample_data/
      generate_sample_pdf.py
      sample_deviation_report.pdf
      sample_deviation_report.txt
  frontend/
    README.md
    package.json
    vite.config.js
    src/
      App.jsx
      api.js
      constants.js
      components/
        CopilotChat.jsx
        DeviationForm.jsx
        StatusBadge.jsx
      app-layout.css
      index.css
```

## Local Development

1. Clone the repository.

```bash
git clone https://github.com/dj-ayush/AIVOA_Assignment.git
cd AIVOA_Assignment
```

2. Configure and run the backend.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

3. Configure and run the frontend.

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

4. Open the Vite URL, usually `http://localhost:5173`.

## Sample / Demo Workflow

Sample files:

- `backend/sample_data/sample_deviation_report.pdf`
- `backend/sample_data/sample_deviation_report.txt`

The sample describes a tablet weight excursion for Losartan Potassium Tablets 50 mg, batch `LST261109A`.

Demo path:

```text
upload sample_deviation_report.pdf
-> PDF text extraction
-> document_extract
-> form population
-> impact/severity assessment
-> natural-language correction
-> Save Deviation
```

Example correction:

```text
Actually the affected quantity is 16,800 tablets.
```

## Testing / Validation

The repository does not include a formal unit/integration test suite. Current validation commands are:

```bash
cd backend
python -m compileall app
python -c "from app.main import app; print(app.title)"
```

```bash
cd frontend
npm run lint
npm run build
```

Optional local save smoke test:

```bash
curl -X POST http://localhost:8000/api/save ^
  -H "Content-Type: application/json" ^
  -d "{\"form\":{},\"risk_assessment\":{}}"
```

## Deployment

The current deployment is on Railway.

Frontend:

```text
https://gracious-enjoyment-production-524c.up.railway.app/
```

Backend:

```text
https://aivoaassignment-production.up.railway.app
```

Railway backend variables should include `GROQ_API_KEY` and, for database persistence, `MYSQL_URL`.

## Current Limitations

- Live AI extraction requires `GROQ_API_KEY`.
- MySQL persistence requires `MYSQL_URL` or a MySQL `DATABASE_URL`.
- JSON fallback is local/demo persistence, not production-grade storage.
- PDF extraction is text-based; OCR is not implemented.
- Authentication, roles, audit trail UI, and CAPA workflows are not implemented.
- Chat state is held in frontend memory during the session.

## Security / Configuration Notes

- Keep provider keys and database URLs in `.env` or Railway variables.
- `GROQ_API_KEY` is used only by the backend.
- Frontend only receives `VITE_API_BASE_URL`.
- CORS is configured through `CORSMiddleware` with local Vite origins and the current Railway frontend origin.
- Upload handling extracts text but does not perform antivirus scanning or OCR.

## Technology Stack

| Area | Technology |
|---|---|
| Frontend | React 19, Vite, CSS |
| Backend | FastAPI, Pydantic, Uvicorn |
| AI/LLM | Groq SDK |
| Workflow | LangGraph `StateGraph` |
| Database | MySQL, `mysql-connector-python` |
| Document processing | `pypdf`, `python-multipart` |
| Sample PDF generation | `reportlab` |
| Deployment | Railway |
