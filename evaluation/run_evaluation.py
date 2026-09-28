from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

from app.config import GROQ_MODEL  # noqa: E402
from app.graph import get_graph  # noqa: E402
from app.observability import observe_workflow, reset_observability  # noqa: E402


def load_cases(path: Path) -> list[Dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def compare_expected(expected: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[list[Dict[str, Any]], int]:
    comparisons = []
    matched = 0
    for field, expected_value in expected.items():
        actual_value = actual.get(field)
        is_match = actual_value == expected_value
        if is_match:
            matched += 1
        comparisons.append(
            {
                "field": field,
                "expected": expected_value,
                "actual": actual_value,
                "match": is_match,
            }
        )
    return comparisons, matched


def run_case(case: Dict[str, Any]) -> Dict[str, Any]:
    input_path = (Path(__file__).resolve().parent / case["input_path"]).resolve()
    text = input_path.read_text(encoding="utf-8")
    workflow_type = case.get("workflow_type", "document_upload")
    graph = get_graph()
    trace = None
    try:
        with observe_workflow(f"evaluation:{workflow_type}") as trace:
            state = graph.invoke(
                {
                    "user_message": "" if workflow_type == "document_upload" else text,
                    "document_text": text if workflow_type == "document_upload" else None,
                    "current_form": {},
                    "current_risk": {},
                }
            )
        form = state["result_form"]
        risk = state["result_risk"]
        form_comparisons, form_matches = compare_expected(case.get("expected_form", {}), form)
        risk_comparisons, risk_matches = compare_expected(case.get("expected_risk", {}), risk)
        total_expected = len(form_comparisons) + len(risk_comparisons)
        total_matches = form_matches + risk_matches
        return {
            "id": case["id"],
            "description": case.get("description"),
            "status": "passed" if total_expected == total_matches else "completed_with_mismatches",
            "input_path": str(input_path.relative_to(ROOT)),
            "model": GROQ_MODEL,
            "observability": trace.to_dict() if trace else None,
            "field_comparisons": {
                "form": form_comparisons,
                "risk_assessment": risk_comparisons,
            },
            "summary": {
                "expected_fields": total_expected,
                "matched_fields": total_matches,
                "mismatched_fields": total_expected - total_matches,
            },
        }
    except Exception as exc:
        return {
            "id": case["id"],
            "description": case.get("description"),
            "status": "failed",
            "input_path": str(input_path.relative_to(ROOT)),
            "model": GROQ_MODEL,
            "observability": trace.to_dict() if trace else None,
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
            },
            "summary": {
                "expected_fields": len(case.get("expected_form", {})) + len(case.get("expected_risk", {})),
                "matched_fields": 0,
                "mismatched_fields": None,
            },
        }


def summarize(results: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    results = list(results)
    successful = [item for item in results if item["status"] in {"passed", "completed_with_mismatches"}]
    failed = [item for item in results if item["status"] == "failed"]
    expected_fields = sum(item["summary"]["expected_fields"] for item in results)
    matched_fields = sum(item["summary"]["matched_fields"] for item in results)
    measured_workflows = [item["observability"] for item in results if item.get("observability")]
    return {
        "case_count": len(results),
        "completed_cases": len(successful),
        "failed_cases": len(failed),
        "expected_fields": expected_fields,
        "matched_fields": matched_fields,
        "mismatched_fields": expected_fields - matched_fields if not failed else "not measured for failed cases",
        "workflow_durations_ms": [
            workflow.get("total_duration_ms") for workflow in measured_workflows if workflow.get("total_duration_ms") is not None
        ],
    }


def write_markdown(output: Dict[str, Any], path: Path) -> None:
    lines = [
        "# DeviationIQ Evaluation Results",
        "",
        f"- Generated at: `{output['generated_at']}`",
        f"- Model: `{output['model']}`",
        f"- Cases: `{output['summary']['case_count']}`",
        f"- Completed cases: `{output['summary']['completed_cases']}`",
        f"- Failed cases: `{output['summary']['failed_cases']}`",
        f"- Expected fields: `{output['summary']['expected_fields']}`",
        f"- Matched fields: `{output['summary']['matched_fields']}`",
        f"- Mismatched fields: `{output['summary']['mismatched_fields']}`",
        "",
        "No accuracy, throughput, or reliability claims are inferred from this run.",
        "",
        "## Cases",
        "",
    ]
    for case in output["cases"]:
        lines.extend(
            [
                f"### {case['id']}",
                "",
                f"- Status: `{case['status']}`",
                f"- Input: `{case['input_path']}`",
            ]
        )
        if case.get("observability"):
            obs = case["observability"]
            lines.extend(
                [
                    f"- Workflow duration: `{obs.get('total_duration_ms')}` ms",
                    f"- Executed nodes: `{obs.get('executed_node_count')}`",
                    f"- LLM calls: `{obs.get('summary', {}).get('llm_call_count')}`",
                    f"- Validation failures: `{obs.get('summary', {}).get('validation_failures')}`",
                    f"- Retry attempts: `{obs.get('retry_attempts')}`",
                ]
            )
        else:
            lines.append("- Workflow observability: `not measured`")
        if case.get("error"):
            lines.append(f"- Error: `{case['error']['type']}: {case['error']['message']}`")
        lines.append("")
        if case.get("field_comparisons"):
            lines.extend(["| Area | Field | Match |", "| ---- | ----- | ----- |"])
            for area, comparisons in case["field_comparisons"].items():
                for comparison in comparisons:
                    lines.append(f"| {area} | `{comparison['field']}` | `{comparison['match']}` |")
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run DeviationIQ extraction evaluation cases.")
    parser.add_argument("--cases", default=str(Path(__file__).resolve().parent / "cases.json"))
    parser.add_argument("--results-json", default=str(Path(__file__).resolve().parent / "results.json"))
    parser.add_argument("--results-md", default=str(Path(__file__).resolve().parent / "results.md"))
    args = parser.parse_args()

    reset_observability()
    cases = load_cases(Path(args.cases))
    case_results = [run_case(case) for case in cases]
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": GROQ_MODEL,
        "summary": summarize(case_results),
        "cases": case_results,
        "notes": {
            "token_usage": "included only when returned by Groq",
            "retry_attempts": "the current application has no retry loop, so successful runs report 0",
            "failed_cases": "failed cases keep the real error message and do not fabricate metrics",
        },
    }
    results_json = Path(args.results_json)
    results_md = Path(args.results_md)
    results_json.write_text(json.dumps(output, indent=2), encoding="utf-8")
    write_markdown(output, results_md)
    print(f"Wrote {results_json}")
    print(f"Wrote {results_md}")
    return 0 if output["summary"]["failed_cases"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
