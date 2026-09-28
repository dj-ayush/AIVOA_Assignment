# DeviationIQ Evaluation Results

- Generated at: `2026-09-28T12:47:01.493871+00:00`
- Model: `openai/gpt-oss-20b`
- Cases: `1`
- Completed cases: `1`
- Failed cases: `0`
- Expected fields: `7`
- Matched fields: `7`
- Mismatched fields: `0`

No accuracy, throughput, or reliability claims are inferred from this run.

## Cases

### sample_deviation_report

- Status: `passed`
- Input: `backend\sample_data\sample_deviation_report.txt`
- Workflow duration: `12100.408` ms
- Executed nodes: `1`
- LLM calls: `1`
- Validation failures: `0`
- Retry attempts: `0`

| Area | Field | Match |
| ---- | ----- | ----- |
| form | `product_name` | `True` |
| form | `product_strength` | `True` |
| form | `batch_lot_number` | `True` |
| form | `affected_quantity` | `True` |
| form | `originating_site_block` | `True` |
| form | `complaint_category` | `True` |
| risk_assessment | `severity` | `True` |
