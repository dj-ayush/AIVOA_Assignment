# DeviationIQ

DeviationIQ is a pharmaceutical QMS deviation intake application. It converts unstructured deviation text, emails, and PDFs into a structured read-only deviation form, generates an initial impact/severity assessment, supports natural-language corrections, and saves finalized records.

Links:

- Repository: [https://github.com/dj-ayush/AIVOA_Assignment](https://github.com/dj-ayush/AIVOA_Assignment)
- Frontend deployment: [https://gracious-enjoyment-production-524c.up.railway.app/](https://gracious-enjoyment-production-524c.up.railway.app/)
- Backend API: [https://aivoaassignment-production.up.railway.app](https://aivoaassignment-production.up.railway.app)
- Backend OpenAPI: [https://aivoaassignment-production.up.railway.app/openapi.json](https://aivoaassignment-production.up.railway.app/openapi.json)

## Problem And Solution

Deviation reports often arrive as free text or documents and must be converted into consistent QMS records without losing context. DeviationIQ keeps the user in a simple two-panel workflow: the AI copilot extracts and patches data, while the form stays read-only and traceable.

## Key Features

- Text chat extraction for new deviations
- PDF/TXT/EML upload and extraction
- AI-populated Deviation Details form
- Impact Assessment with severity and recommended QA action
- Natural-language correction flow that patches only mentioned fields
- Highlighting for recently AI-updated fields
- Save/reset workflow
- MySQL persistence when configured, JSON ledger fallback for local demos

## Architecture

```text
frontend/ React + Vite
  -> src/api.js fetch wrappers
  -> FastAPI backend
  -> LangGraph route: document_extract | classify_intent
  -> Groq structured output
  -> Pydantic validation
  -> MySQL save or JSON fallback
```

## End-To-End AI Workflow

```text
Text/PDF input
-> extraction or intent classification
-> DeviationForm population
-> RiskAssessment generation
-> natural-language correction, if needed
-> POST /api/save
-> MySQL deviations table or sample_data/qms_ledger.json fallback
```

## Tech Stack

| Layer | Implementation |
|---|---|
| Frontend | React 19, Vite, plain CSS |
| Backend | FastAPI, Pydantic |
| AI orchestration | LangGraph `StateGraph` |
| LLM | Groq SDK with structured JSON responses |
| PDF parsing | `pypdf` |
| PDF sample generation | `reportlab` |
| Persistence | MySQL via `MYSQL_URL` or MySQL `DATABASE_URL`; JSON fallback |
| Deployment | Railway frontend and backend services |

## Important Schemas And Data Flow

Backend schema names live in `backend/app/schemas.py`:

- `DeviationForm`: structured deviation form fields.
- `RiskAssessment`: severity, recommended action, and impact assessment.
- `ExtractionOutput`: full extraction result for new text/PDF input.
- `PatchOutput`: patch-only correction result.
- `ChatRequest` / `ChatResponse`: API models for `/api/chat`.

Some internal field keys retain legacy names such as `complaint_source`, `customer_name`, `complaint_category`, and `complaint_description` for compatibility with the existing frontend and prompts. The visible UI uses DeviationIQ terminology.

## Project Structure

```text
backend/
  app/
    main.py          FastAPI routes and save/read behavior
    graph.py         LangGraph nodes and routing
    prompts.py       Groq prompt instructions
    schemas.py       Pydantic models
    llm.py           Groq client wrapper
    database.py      MySQL persistence helpers
    pdf_utils.py     PDF text extraction
    config.py        Environment loading and CORS
  sample_data/
    generate_sample_pdf.py
    sample_deviation_report.pdf
    sample_deviation_report.txt
frontend/
  src/
    App.jsx
    api.js
    constants.js
    components/
      DeviationForm.jsx
      CopilotChat.jsx
      StatusBadge.jsx
```

## Local Setup

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

## MySQL Configuration

Set `MYSQL_URL` in `backend/.env` or in Railway backend variables:

```env
MYSQL_URL=mysql://user:password@host:3306/deviationiq
```

`MYSQL_URL` is preferred. `DATABASE_URL` is also accepted only when it is a MySQL URL. If both are blank, `/api/save` writes to `backend/sample_data/qms_ledger.json`.

## Environment Variables

Backend:

```env
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
MYSQL_URL=
DATABASE_URL=
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://gracious-enjoyment-production-524c.up.railway.app
```

Frontend:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Production frontend builds use `frontend/.env.production`, which points to the Railway backend.

## API Overview

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/chat` | Text extraction, correction, or general copilot reply |
| `POST` | `/api/upload` | PDF/TXT/EML extraction |
| `POST` | `/api/save` | Save finalized deviation |
| `POST` | `/api/commit` | Compatibility alias for save |
| `GET` | `/api/ledger` | Read saved records |

## Sample Demo Workflow

Use either sample file:

- `backend/sample_data/sample_deviation_report.pdf`
- `backend/sample_data/sample_deviation_report.txt`

The sample is a tablet weight excursion for Losartan Potassium Tablets 50 mg, batch `LST261109A`.

Demo steps:

1. Start backend and frontend.
2. Upload the PDF or paste the TXT content.
3. Review extracted product, batch, site/process, deviation details, and impact assessment.
4. Send a correction in natural language.
5. Save the finalized deviation.
6. Reset for the next deviation.

## Validation Commands

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

## Deployment Notes

The current Railway frontend and backend URLs above were reachable during this documentation pass. The frontend production build uses `VITE_API_BASE_URL=https://aivoaassignment-production.up.railway.app`.

For backend save/read on Railway, configure:

```env
MYSQL_URL=mysql://USER:PASSWORD@HOST:PORT/DATABASE
```

Do not commit real credentials.

## Current Limitations And Pending Improvements

- `GROQ_API_KEY` is required for `/api/chat` and `/api/upload`.
- MySQL persistence requires a reachable MySQL URL; otherwise local fallback is JSON only.
- JSON fallback is useful for demos but not durable production storage.
- Scanned image-only PDFs are not OCR processed.
- No authentication or role-based access control is implemented.
- Legacy internal `complaint_*` keys remain for compatibility.
