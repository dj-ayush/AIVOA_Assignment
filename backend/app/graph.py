"""
LangGraph orchestration for DeviationIQ.

                                   ┌─────────────────┐
                     has document  │ document_extract │──┐
                 ┌────────────────▶└─────────────────┘  │
   START ────────┤                                       │
                 │   no document   ┌─────────────────┐   │
                 └────────────────▶│ classify_intent │    │
                                   └────────┬────────┘    │
                                            │              │
                       ┌────────────────────┼───────────┐  │
                       ▼                    ▼           ▼  │
                ┌─────────────┐     ┌──────────────┐  ┌─────────────┐
                │ extract_new │     │ edit_fields  │  │general_chat │
                └──────┬──────┘     └──────┬───────┘  └──────┬──────┘
                       │                   │                 │
                       └───────────────────┴────────┬────────┘
                                                     ▼
                                                    END
"""
from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import END, StateGraph

from . import prompts
from .llm import generate_structured, generate_text
from .observability import observe_node
from .schemas import ExtractionOutput, IntentResult, PatchOutput


class GraphState(TypedDict, total=False):
    user_message: str
    document_text: Optional[str]
    current_form: Dict[str, Any]
    current_risk: Dict[str, Any]
    intent: str
    result_form: Dict[str, Any]
    result_risk: Dict[str, Any]
    reply: str


def _merge_non_null(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if value is not None:
            merged[key] = value
    return merged


def classify_intent_node(state: GraphState) -> GraphState:
    with observe_node("classify_intent"):
        context = (
            f"CURRENT_FORM (json): {state['current_form']}\n"
            f"USER_MESSAGE: {state['user_message']}"
        )
        result: IntentResult = generate_structured(prompts.INTENT_SYSTEM, context, IntentResult)
        return {"intent": result.intent}


def extract_new_node(state: GraphState) -> GraphState:
    with observe_node("extract_new"):
        out: ExtractionOutput = generate_structured(
            prompts.EXTRACT_NEW_SYSTEM, state["user_message"], ExtractionOutput
        )
        return {
            "result_form": _merge_non_null(state["current_form"], out.form.model_dump()),
            "result_risk": _merge_non_null(state["current_risk"], out.risk_assessment.model_dump()),
            "reply": out.reply_message,
        }


def edit_fields_node(state: GraphState) -> GraphState:
    with observe_node("edit_fields"):
        context = (
            f"CURRENT_FORM (json): {state['current_form']}\n"
            f"CURRENT_RISK_ASSESSMENT (json): {state['current_risk']}\n"
            f"USER_CORRECTION: {state['user_message']}"
        )
        out: PatchOutput = generate_structured(prompts.EDIT_SYSTEM, context, PatchOutput)
        return {
            "result_form": _merge_non_null(state["current_form"], out.form_patch.model_dump()),
            "result_risk": _merge_non_null(state["current_risk"], out.risk_patch.model_dump()),
            "reply": out.reply_message,
        }


def document_extract_node(state: GraphState) -> GraphState:
    with observe_node("document_extract"):
        out: ExtractionOutput = generate_structured(
            prompts.DOCUMENT_SYSTEM, state["document_text"] or "", ExtractionOutput
        )
        return {
            "result_form": _merge_non_null(state["current_form"], out.form.model_dump()),
            "result_risk": _merge_non_null(state["current_risk"], out.risk_assessment.model_dump()),
            "reply": out.reply_message,
        }


def general_chat_node(state: GraphState) -> GraphState:
    with observe_node("general_chat"):
        reply = generate_text(prompts.GENERAL_SYSTEM, state["user_message"])
        return {
            "result_form": state["current_form"],
            "result_risk": state["current_risk"],
            "reply": reply,
        }


def _route_entry(state: GraphState) -> str:
    return "document_extract" if state.get("document_text") else "classify_intent"


def _route_after_classification(state: GraphState) -> str:
    return state["intent"]


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("extract_new", extract_new_node)
    graph.add_node("edit_fields", edit_fields_node)
    graph.add_node("document_extract", document_extract_node)
    graph.add_node("general_chat", general_chat_node)

    graph.set_conditional_entry_point(
        _route_entry,
        {
            "document_extract": "document_extract",
            "classify_intent": "classify_intent",
        },
    )

    graph.add_conditional_edges(
        "classify_intent",
        _route_after_classification,
        {
            "new_deviation": "extract_new",
            "edit_fields": "edit_fields",
            "general": "general_chat",
        },
    )

    graph.add_edge("extract_new", END)
    graph.add_edge("edit_fields", END)
    graph.add_edge("document_extract", END)
    graph.add_edge("general_chat", END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
