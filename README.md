# DeviationIQ

Repository: [https://github.com/dj-ayush/AIVOA_Assignment](https://github.com/dj-ayush/AIVOA_Assignment)

DeviationIQ is a pharmaceutical QMS intake tool for logging product deviations from pasted text, emails, or PDF reports. It keeps the existing two-panel workflow: a read-only deviation form on the left and an AI copilot on the right.

## Problem And Solution

Deviation intake often starts with unstructured reports that must be converted into consistent QMS fields, assessed for impact/severity, corrected when details change, and saved without losing traceability. DeviationIQ uses a LangGraph workflow and Groq structured outputs to extract, assess, patch, and save the deviation record.

## Key Features

- Log Deviation form populated by AI only
- Deviation Copilot for text input, PDF/TXT/EML upload, and natural-language corrections
- Impact Assessment with severity and recommended action
- Field highlighting for AI-populated updates
- Save/reset workflow
- MySQL persistence when configured, JSON ledger fallback for local demos

## AI Workflow

```text
User text/PDF
-> FastAPI upload/chat endpoint
-> LangGraph intent/document route
-> Groq structured extraction or patch response
-> form population
-> impact/severity assessment
-> save to MySQL or JSON fallback
```

## Architecture

- `frontend/`: React + Vite UI
- `backend/`: FastAPI API, LangGraph workflow, Groq wrapper, PDF extraction, persistence
- `backend/sample_data/`: demo PDF/email files and local JSON ledger output

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | React 19, Vite, CSS |
| Backend | FastAPI, Pydantic |
| AI orchestration | LangGraph |
| LLM | Groq SDK |
| PDF parsing | pypdf |
| Database | MySQL via `MYSQL_URL` or MySQL `DATABASE_URL`; JSON fallback when unset |

## Project Structure

```text
backend/
  app/
    main.py
    graph.py
    prompts.py
    schemas.py
    llm.py
    database.py
    pdf_utils.py
    config.py
  sample_data/
frontend/
  src/
    App.jsx
    api.js
    constants.js
    components/
```

## Setup

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Frontend:

```bash
cd frontend
npm install
copy .env.example .env
```

## MySQL Configuration

Create a database, then set `MYSQL_URL` in `backend/.env`:

```env
MYSQL_URL=mysql://user:password@host:3306/deviationiq
```

`MYSQL_URL` is preferred. `DATABASE_URL` is accepted for compatibility if it also uses a MySQL URL. If both are blank, the backend saves to `backend/sample_data/qms_ledger.json`.

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

For the Railway production build, `frontend/.env.production` points to `https://aivoaassignment-production.up.railway.app`.

## Run Commands

Backend:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm run dev
```

## Demo Workflow

1. Paste a deviation report into the copilot.
2. Review populated Deviation Details and Impact Assessment.
3. Correct fields using natural language.
4. Upload `backend/sample_data/sample_deviation_report.pdf` or `sample_deviation_report.txt`.
5. Save the finalized deviation.
6. Reset for the next deviation.

The included sample describes a tablet weight excursion for Losartan Potassium Tablets 50 mg, batch `LST261109A`. It can be used to test AI extraction, deviation form population, impact/severity assessment, and follow-up natural-language correction.

## Testing

```bash
cd frontend
npm run build
npm run lint
```

```bash
cd backend
python -m compileall app
python -c "from app.main import app; print(app.title)"
```

## Limitations

- Groq extraction requires a valid `GROQ_API_KEY`.
- MySQL save/read requires a reachable MySQL database and valid `MYSQL_URL` or MySQL `DATABASE_URL`.
- Scanned image-only PDFs need OCR before upload.
- Existing API field keys still use some legacy `complaint_*` names internally for compatibility.
