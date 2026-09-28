from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.run_evaluation import compare_expected, summarize


class EvaluationHelperTests(unittest.TestCase):
    def test_compare_expected_counts_exact_matches(self) -> None:
        comparisons, matched = compare_expected(
            {"product_name": "A", "batch_lot_number": "B"},
            {"product_name": "A", "batch_lot_number": "C"},
        )

        self.assertEqual(matched, 1)
        self.assertEqual(len(comparisons), 2)
        self.assertFalse(comparisons[1]["match"])

    def test_summarize_uses_real_case_statuses(self) -> None:
        summary = summarize(
            [
                {
                    "status": "passed",
                    "summary": {"expected_fields": 2, "matched_fields": 2},
                    "observability": {"total_duration_ms": 5.0},
                },
                {
                    "status": "failed",
                    "summary": {"expected_fields": 1, "matched_fields": 0},
                    "observability": None,
                },
            ]
        )

        self.assertEqual(summary["case_count"], 2)
        self.assertEqual(summary["completed_cases"], 1)
        self.assertEqual(summary["failed_cases"], 1)
        self.assertEqual(summary["matched_fields"], 2)
        self.assertEqual(summary["mismatched_fields"], "not measured for failed cases")


if __name__ == "__main__":
    unittest.main()
