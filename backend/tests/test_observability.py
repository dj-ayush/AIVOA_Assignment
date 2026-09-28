from __future__ import annotations

import unittest

from app.observability import (
    observability_snapshot,
    observe_node,
    observe_workflow,
    record_llm_call,
    record_validation,
    reset_observability,
)


class ObservabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_observability()

    def test_workflow_records_node_llm_and_validation_metrics(self) -> None:
        with observe_workflow("unit_test") as trace:
            with observe_node("sample_node"):
                record_llm_call(
                    operation="structured",
                    model="test-model",
                    schema="ExampleSchema",
                    duration_ms=1.25,
                    success=True,
                    token_usage={"total_tokens": 10},
                )
                record_validation(schema="ExampleSchema", duration_ms=0.5, success=True)

        payload = trace.to_dict()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["executed_node_count"], 1)
        self.assertEqual(payload["summary"]["llm_call_count"], 1)
        self.assertEqual(payload["summary"]["validation_failures"], 0)
        self.assertEqual(payload["retry_attempts"], 0)

    def test_recent_snapshot_exposes_workflow_metrics(self) -> None:
        with observe_workflow("unit_test"):
            pass

        snapshot = observability_snapshot()
        self.assertEqual(len(snapshot["workflows"]), 1)
        self.assertIn("api_requests", snapshot)
        self.assertIn("database_operations", snapshot)


if __name__ == "__main__":
    unittest.main()
