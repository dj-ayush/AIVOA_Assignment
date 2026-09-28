# DeviationIQ Evaluation And Observability

Lightweight evaluation harness for the current DeviationIQ extraction workflow.

## What Is Measured

The backend records measurements from the actual application flow:

| Area | Metric |
| ---- | ------ |
| Workflow | total duration, executed node count, success/failure |
| LangGraph node | node name, duration, success/failure |
| LLM call | model, operation, duration, success/failure, token usage when Groq returns it |
| Structured validation | Pydantic schema, validation duration, success/failure |
| API request | method, path, status code, request duration, success/failure |
| Database | MySQL table creation, insert, read duration and success/failure |

The current application does not implement an LLM retry loop. Retry attempts are therefore recorded as `0`, and correction retry time is reported as `null`.

## Evaluation Methodology

Evaluation cases live in `evaluation/cases.json`. Each case provides:

- input document path
- workflow type
- expected form fields
- expected risk fields

The runner executes the real LangGraph workflow and compares expected values with actual returned values using exact string equality. It does not infer pharmaceutical correctness or calculate broader accuracy claims.

## Run Evaluation

From the repository root:

```bash
python evaluation/run_evaluation.py
```

Results are written to:

```text
evaluation/results.json
evaluation/results.md
```

Live extraction requires backend dependencies and a valid `GROQ_API_KEY` in the backend environment. If Groq is unavailable, the run records the real failure and does not fabricate metrics.

## Add A Case

Add an object to `evaluation/cases.json`:

```json
{
  "id": "new_case_id",
  "description": "Short case description.",
  "input_path": "../backend/sample_data/sample_deviation_report.txt",
  "workflow_type": "document_upload",
  "expected_form": {
    "product_name": "Expected Product"
  },
  "expected_risk": {
    "severity": "Major"
  }
}
```

Use only fields that exist in `backend/app/schemas.py`.

## API Snapshot

The backend exposes recent in-memory observability data at:

```text
GET /api/observability
```

This endpoint is intended for local/demo inspection. It is not durable monitoring storage.

## Limitations

- Metrics are in-memory and reset when the backend process restarts.
- Token usage is recorded only when Groq returns usage metadata.
- The evaluation dataset is small and representative, not a benchmark.
- Exact-match field comparison is intentionally strict and simple.
- No OCR evaluation is included because OCR is not implemented.
