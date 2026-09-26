from __future__ import annotations

import datetime
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .database import is_database_configured, load_deviation_records, save_deviation_record
from .graph import get_graph
from .pdf_utils import extract_text_from_pdf
from .schemas import ChatRequest, ChatResponse, DeviationForm, RiskAssessment

app = FastAPI(title="DeviationIQ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LEDGER_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "qms_ledger.json"


def _build_response(
    current_form: Dict[str, Any],
    current_risk: Dict[str, Any],
    result_form: Dict[str, Any],
    result_risk: Dict[str, Any],
    reply: str,
    intent: str | None = None,
) -> ChatResponse:
    changed = sorted(
        {k for k in result_form if result_form.get(k) != current_form.get(k)}
        | {k for k in result_risk if result_risk.get(k) != current_risk.get(k)}
    )
    status = "ready_to_save" if result_form.get("product_name") and result_form.get("complaint_description") else "pending_triage"
    return ChatResponse(
        reply=reply,
        form=DeviationForm(**result_form),
        risk_assessment=RiskAssessment(**result_risk),
        changed_fields=changed,
        status=status,
        intent=intent,
    )


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    graph = get_graph()
    state = graph.invoke(
        {
            "user_message": req.message,
            "document_text": None,
            "current_form": req.current_form.model_dump(),
            "current_risk": req.current_risk.model_dump(),
        }
    )
    return _build_response(
        req.current_form.model_dump(),
        req.current_risk.model_dump(),
        state["result_form"],
        state["result_risk"],
        state["reply"],
        state.get("intent"),
    )


@app.post("/api/upload", response_model=ChatResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_form: str = Form("{}"),
    current_risk: str = Form("{}"),
) -> ChatResponse:
    try:
        form_dict = json.loads(current_form or "{}")
        risk_dict = json.loads(current_risk or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Uploaded form state was not valid JSON.") from exc

    raw = await file.read()
    filename = (file.filename or "").lower()

    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(raw)
    else:
        text = raw.decode("utf-8", errors="ignore")

    if not text.strip():
        raise HTTPException(status_code=422, detail="Could not extract any text from the uploaded file.")

    graph = get_graph()
    state = graph.invoke(
        {
            "user_message": "",
            "document_text": text,
            "current_form": form_dict,
            "current_risk": risk_dict,
        }
    )
    return _build_response(
        form_dict,
        risk_dict,
        state["result_form"],
        state["result_risk"],
        state["reply"],
        "document_extraction",
    )


def _build_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    record = {
        "id": f"DEV-{uuid.uuid4().hex[:8].upper()}",
        "committed_at": datetime.datetime.utcnow().isoformat() + "Z",
        "form": payload.get("form", {}),
        "risk_assessment": payload.get("risk_assessment", {}),
    }
    return record


def _append_to_json_ledger(record: Dict[str, Any]) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    ledger: List[Dict[str, Any]] = []
    if LEDGER_PATH.exists():
        try:
            ledger = json.loads(LEDGER_PATH.read_text())
        except json.JSONDecodeError:
            ledger = []
    ledger.append(record)
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2))


@app.post("/api/save")
def save(payload: Dict[str, Any]) -> Dict[str, Any]:
    record = _build_record(payload)
    if is_database_configured():
        save_deviation_record(record)
        storage = "mysql"
    else:
        _append_to_json_ledger(record)
        storage = "json"
    return {"status": "saved", "record_id": record["id"], "storage": storage}


@app.post("/api/commit")
def commit(payload: Dict[str, Any]) -> Dict[str, Any]:
    return save(payload)


@app.get("/api/ledger")
def get_ledger() -> List[Dict[str, Any]]:
    if is_database_configured():
        return load_deviation_records()
    if not LEDGER_PATH.exists():
        return []
    try:
        return json.loads(LEDGER_PATH.read_text())
    except json.JSONDecodeError:
        return []
