# DeviationIQ Backend

FastAPI backend for DeviationIQ. It exposes chat, upload, save, health, and ledger APIs, orchestrates the AI workflow with LangGraph, calls Groq for structured outputs, extracts PDF text, and persists records to MySQL when configured.

## Architecture

```text
FastAPI routes
-> LangGraph route: document_extract | classify_intent
-> Groq structured response
-> Pydantic validation
-> save to MySQL or JSON fallback
```

## APIs

- `GET /api/health`: service health
- `POST /api/chat`: text deviation extraction or correction
- `POST /api/upload`: PDF/TXT/EML extraction
- `POST /api/save`: save finalized deviation
- `POST /api/commit`: compatibility alias for save
- `GET /api/ledger`: read saved records

## LangGraph + Groq Workflow

- Documents route directly to `document_extract`.
- Text input is classified as new deviation, edit fields, or general chat.
- New deviations return a full structured form and impact assessment.
- Corrections return patches only, preserving untouched fields.

## MySQL Setup

Create a database and set:

```env
DATABASE_URL=mysql://user:password@localhost:3306/deviationiq
```

The backend creates the `deviations` table automatically. If `DATABASE_URL` is blank, it writes to `sample_data/qms_ledger.json`.

## Environment Variables

```env
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
DATABASE_URL=
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://gracious-enjoyment-production-524c.up.railway.app
```

Blank `CORS_ORIGINS` falls back to local Vite origins plus the Railway frontend origin. Additional comma-separated origins may be supplied with `CORS_ORIGINS`.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## API Usage

Chat:

```bash
curl -X POST http://localhost:8000/api/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Log deviation for discolored Amoxicillin capsules\",\"current_form\":{},\"current_risk\":{}}"
```

Save:

```bash
curl -X POST http://localhost:8000/api/save ^
  -H "Content-Type: application/json" ^
  -d "{\"form\":{\"product_name\":\"Amoxicillin\",\"complaint_description\":\"Discoloration reported\"},\"risk_assessment\":{\"severity\":\"Major\"}}"
```

## Error Handling

- Missing Groq key raises a clear backend error during AI calls.
- Invalid upload state JSON returns `400`.
- Empty extracted document text returns `422`.
- Missing MySQL config uses JSON fallback instead of failing startup.

## Sample Data

Use `sample_data/sample_deviation_report.pdf` or `sample_data/sample_deviation_report.txt` to test document extraction. The sample is a manufacturing deviation for a tablet weight excursion and should populate product, batch, site/process, observed condition, impact, severity, and recommended action fields. Regenerate the PDF with:

```bash
cd sample_data
python generate_sample_pdf.py
```
