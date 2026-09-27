# DeviationIQ Frontend

React + Vite frontend for DeviationIQ. The UI keeps a two-panel workflow: a read-only Log Deviation form on the left and a Deviation Copilot chat/upload panel on the right.

Deployment: [https://gracious-enjoyment-production-524c.up.railway.app/](https://gracious-enjoyment-production-524c.up.railway.app/)

## Architecture

```text
src/main.jsx
  -> App.jsx
     -> DeviationForm.jsx
     -> CopilotChat.jsx
     -> api.js
```

State is held in `App.jsx` with React state hooks. The frontend does not directly edit form fields; it sends text or files to the backend and renders the returned form/risk state.

## Main Components

| File | Purpose |
|---|---|
| `src/App.jsx` | Top-level state, chat/upload/save/reset orchestration |
| `src/api.js` | Fetch wrappers for backend API routes |
| `src/constants.js` | Empty form/risk state and field layout config |
| `src/components/DeviationForm.jsx` | Read-only deviation form and save/reset actions |
| `src/components/CopilotChat.jsx` | Chat messages, file upload, loading state |
| `src/components/StatusBadge.jsx` | Pending/ready status badge |
| `src/app-layout.css` | Two-panel layout and UI styling |

## User Workflow

```text
Paste text or upload PDF/TXT/EML
-> backend extraction
-> form and impact assessment returned
-> highlighted AI-populated fields
-> optional natural-language correction
-> Save Deviation or Reset Deviation
```

## Backend/API Integration

`src/api.js` reads:

```js
import.meta.env.VITE_API_BASE_URL
```

and calls:

| Function | Route |
|---|---|
| `sendChatMessage(...)` | `POST /api/chat` |
| `uploadDocument(...)` | `POST /api/upload` |
| `saveDeviation(...)` | `POST /api/save` |
| `checkHealth()` | `GET /api/health` |

Network failures are reported as backend URL/CORS/availability issues. Non-2xx backend responses are surfaced from the response body when possible.

## AI-Generated Field Handling

- The form is read-only.
- AI-populated values render with an `AI` indicator.
- Changed fields are temporarily highlighted.
- Empty fields show "Awaiting AI..." placeholders.
- Status changes to `Ready to Save` when the backend marks the response as `ready_to_save`.

## PDF Upload Flow

`CopilotChat.jsx` accepts `.pdf`, `.txt`, and `.eml`. Files are sent as `FormData` to `/api/upload` with the current form and risk state serialized as JSON strings.

## Save, Reset, And Correction Flow

- Correction messages are sent through `/api/chat` with recent chat history and current state.
- Save sends `{ form, risk_assessment }` to `/api/save`.
- Reset clears local form/risk state and adds a confirmation chat message.

## Environment Variables

Local `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Production:

```env
VITE_API_BASE_URL=https://aivoaassignment-production.up.railway.app
```

The production value is present in `frontend/.env.production` for Vite production builds.

## Setup And Run

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Default local URL: `http://localhost:5173`.

## Build And Lint

```bash
npm run lint
npm run build
```

## Sample Demo

Start the backend, then upload or paste:

- `backend/sample_data/sample_deviation_report.pdf`
- `backend/sample_data/sample_deviation_report.txt`

Use a follow-up message such as:

```text
Actually the affected quantity is 16,800 tablets.
```

The backend should return a patch and the updated field should highlight in the form.

## Deployment Notes

The current Railway frontend deployment was reachable during the documentation pass. The deployed frontend must be built with `VITE_API_BASE_URL` pointing to the Railway backend:

```env
VITE_API_BASE_URL=https://aivoaassignment-production.up.railway.app
```

## Current Limitations And Pending Work

- No authentication or per-user sessions.
- Chat history is held in browser state only.
- The form is intentionally AI-populated/read-only; manual field editing is not implemented.
- Browser errors depend on backend availability and CORS configuration.
- No frontend test suite is currently configured beyond `oxlint` and production build checks.
