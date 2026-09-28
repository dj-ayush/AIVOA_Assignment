from __future__ import annotations

from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Deque, Dict, Iterator, Optional
from uuid import uuid4


MAX_RECENT_EVENTS = 200


def now_ms() -> float:
    return perf_counter() * 1000


def elapsed_ms(start: float) -> float:
    return round(now_ms() - start, 3)


def _error_payload(exc: BaseException) -> Dict[str, str]:
    return {"type": exc.__class__.__name__, "message": str(exc)}


def _clean_none(data: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


@dataclass
class WorkflowTrace:
    workflow_type: str
    trace_id: str = field(default_factory=lambda: uuid4().hex)
    started_at_ms: float = field(default_factory=now_ms)
    total_duration_ms: Optional[float] = None
    success: Optional[bool] = None
    error: Optional[Dict[str, str]] = None
    nodes: list[Dict[str, Any]] = field(default_factory=list)
    llm_calls: list[Dict[str, Any]] = field(default_factory=list)
    validations: list[Dict[str, Any]] = field(default_factory=list)
    retry_attempts: int = 0

    def finish(self, success: bool, error: Optional[BaseException] = None) -> None:
        self.total_duration_ms = elapsed_ms(self.started_at_ms)
        self.success = success
        if error is not None:
            self.error = _error_payload(error)

    def to_dict(self) -> Dict[str, Any]:
        validation_failures = sum(1 for item in self.validations if not item.get("success"))
        llm_failures = sum(1 for item in self.llm_calls if not item.get("success"))
        return {
            "trace_id": self.trace_id,
            "workflow_type": self.workflow_type,
            "total_duration_ms": self.total_duration_ms,
            "executed_node_count": len(self.nodes),
            "success": self.success,
            "error": self.error,
            "retry_attempts": self.retry_attempts,
            "correction_retry_time_ms": None,
            "nodes": self.nodes,
            "llm_calls": self.llm_calls,
            "validations": self.validations,
            "summary": {
                "llm_call_count": len(self.llm_calls),
                "llm_failures": llm_failures,
                "validation_count": len(self.validations),
                "validation_failures": validation_failures,
            },
        }


_current_workflow: ContextVar[Optional[WorkflowTrace]] = ContextVar("current_workflow", default=None)
_recent_api_events: Deque[Dict[str, Any]] = deque(maxlen=MAX_RECENT_EVENTS)
_recent_db_events: Deque[Dict[str, Any]] = deque(maxlen=MAX_RECENT_EVENTS)
_recent_workflows: Deque[Dict[str, Any]] = deque(maxlen=MAX_RECENT_EVENTS)
_recent_llm_calls: Deque[Dict[str, Any]] = deque(maxlen=MAX_RECENT_EVENTS)
_recent_validations: Deque[Dict[str, Any]] = deque(maxlen=MAX_RECENT_EVENTS)


def current_workflow() -> Optional[WorkflowTrace]:
    return _current_workflow.get()


@contextmanager
def observe_workflow(workflow_type: str) -> Iterator[WorkflowTrace]:
    trace = WorkflowTrace(workflow_type=workflow_type)
    token = _current_workflow.set(trace)
    try:
        yield trace
    except BaseException as exc:
        trace.finish(False, exc)
        _recent_workflows.append(trace.to_dict())
        raise
    else:
        trace.finish(True)
        _recent_workflows.append(trace.to_dict())
    finally:
        _current_workflow.reset(token)


@contextmanager
def observe_node(name: str) -> Iterator[None]:
    start = now_ms()
    node_event: Dict[str, Any] = {"name": name}
    try:
        yield
    except BaseException as exc:
        node_event.update(
            {
                "duration_ms": elapsed_ms(start),
                "success": False,
                "error": _error_payload(exc),
            }
        )
        trace = current_workflow()
        if trace is not None:
            trace.nodes.append(node_event)
        raise
    else:
        node_event.update({"duration_ms": elapsed_ms(start), "success": True})
        trace = current_workflow()
        if trace is not None:
            trace.nodes.append(node_event)


def record_llm_call(
    *,
    operation: str,
    model: str,
    duration_ms: float,
    success: bool,
    schema: Optional[str] = None,
    token_usage: Optional[Dict[str, Any]] = None,
    error: Optional[BaseException] = None,
    retry_attempts: int = 0,
) -> None:
    event = _clean_none(
        {
            "operation": operation,
            "model": model,
            "schema": schema,
            "duration_ms": duration_ms,
            "success": success,
            "token_usage": token_usage,
            "error": _error_payload(error) if error else None,
            "retry_attempts": retry_attempts,
        }
    )
    _recent_llm_calls.append(event)
    trace = current_workflow()
    if trace is not None:
        trace.llm_calls.append(event)
        trace.retry_attempts += retry_attempts


def record_validation(
    *,
    schema: str,
    duration_ms: float,
    success: bool,
    error: Optional[BaseException] = None,
) -> None:
    event = _clean_none(
        {
            "schema": schema,
            "duration_ms": duration_ms,
            "success": success,
            "error": _error_payload(error) if error else None,
        }
    )
    _recent_validations.append(event)
    trace = current_workflow()
    if trace is not None:
        trace.validations.append(event)


def record_api_event(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    success: bool,
    error: Optional[BaseException] = None,
) -> None:
    _recent_api_events.append(
        _clean_none(
            {
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "success": success,
                "error": _error_payload(error) if error else None,
            }
        )
    )


def record_db_operation(
    *,
    operation: str,
    duration_ms: float,
    success: bool,
    error: Optional[BaseException] = None,
) -> None:
    _recent_db_events.append(
        _clean_none(
            {
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                "error": _error_payload(error) if error else None,
            }
        )
    )


def observability_snapshot() -> Dict[str, Any]:
    return {
        "workflows": list(_recent_workflows),
        "api_requests": list(_recent_api_events),
        "llm_calls": list(_recent_llm_calls),
        "validations": list(_recent_validations),
        "database_operations": list(_recent_db_events),
        "notes": {
            "token_usage": "reported only when returned by the LLM provider",
            "retry_attempts": "the current application has no LLM retry loop",
            "correction_retry_time_ms": "not measured because no correction retry loop exists",
        },
    }


def reset_observability() -> None:
    _recent_api_events.clear()
    _recent_db_events.clear()
    _recent_workflows.clear()
    _recent_llm_calls.clear()
    _recent_validations.clear()
