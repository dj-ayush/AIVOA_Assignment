# DeviationIQ Frontend

React + Vite frontend for DeviationIQ. It preserves the two-panel workflow: a read-only Log Deviation form and a Deviation Copilot chat/upload panel.

## UI And Workflow

- Paste deviation text or upload PDF/TXT/EML files.
- AI extraction populates Deviation Details.
- Impact Assessment shows severity, rationale, and recommended action.
- Natural-language corrections update only changed fields.
- Save writes the deviation through the backend.
- Reset clears the current deviation.

## Component Structure

```text
src/
  App.jsx
  api.js
  constants.js
  components/
    DeviationForm.jsx
    CopilotChat.jsx
    StatusBadge.jsx
  app-layout.css
  index.css
```

## Backend/API Integration

`src/api.js` uses `VITE_API_BASE_URL` and calls:

- `POST /api/chat`
- `POST /api/upload`
- `POST /api/save`
- `GET /api/health`

## Environment Variables

```env
VITE_API_BASE_URL=http://localhost:8000
```

`frontend/.env.production` sets the Railway backend URL for production builds.

## Installation

```bash
npm install
copy .env.example .env
```

## Run

```bash
npm run dev
```

## Build And Lint

```bash
npm run build
npm run lint
```

## User Workflow

1. Start the backend.
2. Start the frontend.
3. Paste a deviation or upload a sample file.
4. Review highlighted AI-populated fields.
5. Send corrections in natural language.
6. Save or reset the deviation.

Sample files are available at `backend/sample_data/sample_deviation_report.pdf` and `backend/sample_data/sample_deviation_report.txt`. Use them to exercise AI extraction, form population, impact/severity assessment, and correction flow.
