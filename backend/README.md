# DeviationIQ Backend

FastAPI backend for DeviationIQ. It receives text and document inputs, routes them through LangGraph, calls Groq for structured extraction/patching, validates responses with Pydantic, and saves finalized deviations to MySQL or a local JSON fallback.

## Architecture

```text
FastAPI
  /api/chat    -> LangGraph text route
  /api/upload  -> PDF/TXT/EML text extraction -> LangGraph document route
  /api/save    -> MySQL or JSON persistence

LangGraph
  START
  -> document_extract, when uploaded document text exists
  -> classify_intent, for chat text
       -> extract_new
       -> edit_fields
       -> general_chat
  -> END
```

## LangGraph Workflow

Implemented in `app/graph.py`:

| Node | Purpose |
|---|---|
| `classify_intent` | Classifies chat input as `new_deviation`, `edit_fields`, or `general` |
| `extract_new` | Extracts a full `DeviationForm` and `RiskAssessment` from new text |
| `edit_fields` | Produces patch-only updates for corrections |
| `document_extract` | Extracts structured data from uploaded document text |
| `general_chat` | Replies without modifying form state |

## Groq / LLM Integration

Implemented in `app/llm.py`.

- Uses `GROQ_API_KEY` and `GROQ_MODEL`.
- `generate_structured(...)` requests JSON conforming to Pydantic schemas.
- `generate_text(...)` handles general copilot replies.
- Missing `GROQ_API_KEY` raises a clear runtime error during AI calls.

## Pydantic Schemas

Implemented in `app/schemas.py`.

| Schema | Purpose |
|---|---|
| `DeviationForm` | Structured form fields populated by AI |
| `RiskAssessment` | Severity, recommended action, impact assessment |
| `ExtractionOutput` | Full output for new deviations/documents |
| `PatchOutput` | Patch-only output for natural-language corrections |
| `IntentResult` | LangGraph intent route result |
| `ChatRequest` / `ChatResponse` | `/api/chat` request/response models |

Note: some internal field names still use legacy keys such as `complaint_description` for compatibility with existing frontend state and prompts. User-facing labels use deviation terminology.

## PDF And Document Extraction

`app/pdf_utils.py` uses `pypdf` to extract text from uploaded PDF bytes. `/api/upload` also accepts TXT/EML-style text files and sends extracted text into the LangGraph document route.

Image-only scanned PDFs are not OCR processed.

## MySQL Persistence And Fallback

Implemented in `app/database.py` and `app/main.py`.

- Preferred variable: `MYSQL_URL`
- Compatibility variable: MySQL-formatted `DATABASE_URL`
- Table: `deviations`
- Columns: `id`, `committed_at`, `form`, `risk_assessment`
- JSON fallback: `sample_data/qms_ledger.json` when no MySQL URL is configured

Example:

```env
MYSQL_URL=mysql://user:password@host:3306/deviationiq
```

The backend creates the `deviations` table automatically. Invalid or unreachable MySQL configuration returns a JSON `503` instead of an unhandled server error.

## API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/chat` | Text extraction, correction, or general reply |
| `POST` | `/api/upload` | PDF/TXT/EML document extraction |
| `POST` | `/api/save` | Save finalized deviation |
| `POST` | `/api/commit` | Compatibility alias for `/api/save` |
| `GET` | `/api/ledger` | Read saved records |

## Environment Variables

```env
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
MYSQL_URL=
DATABASE_URL=
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://gracious-enjoyment-production-524c.up.railway.app
```

`CORS_ORIGINS` can add comma-separated origins. The backend always includes local Vite origins and the current Railway frontend origin.

## Setup And Run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/health
```

## API Examples

Chat:

```bash
curl -X POST http://localhost:8000/api/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Log deviation for Losartan tablet weight excursion\",\"current_form\":{},\"current_risk\":{}}"
```

Save:

```bash
curl -X POST http://localhost:8000/api/save ^
  -H "Content-Type: application/json" ^
  -d "{\"form\":{\"product_name\":\"Losartan Potassium Tablets\",\"complaint_description\":\"Tablet weight excursion observed\"},\"risk_assessment\":{\"severity\":\"Major\"}}"
```

## Sample Data

Files:

- `sample_data/sample_deviation_report.pdf`
- `sample_data/sample_deviation_report.txt`

Regenerate the PDF:

```bash
cd backend/sample_data
python generate_sample_pdf.py
```

The generator uses `reportlab`; PDF extraction uses `pypdf`.

## Validation

```bash
python -m compileall app
python -c "from app.main import app; print(app.title)"
```

Optional save smoke test:

```bash
curl -X POST http://localhost:8000/api/save ^
  -H "Content-Type: application/json" ^
  -d "{\"form\":{},\"risk_assessment\":{}}"
```

## Current Limitations And Pending Work

- Groq calls require a valid `GROQ_API_KEY`.
- MySQL persistence requires a reachable `MYSQL_URL` or MySQL `DATABASE_URL`.
- JSON fallback is not durable production storage.
- No OCR for scanned PDFs.
- No authentication, authorization, audit trail UI, or user management.
