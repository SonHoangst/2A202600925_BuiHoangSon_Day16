# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_golden.json
- Mode: mock
- Records: 40
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.95 | 1.0 | 0.05 |
| Avg attempts | 1 | 1.05 | 0.05 |
| Avg token estimate | 477.75 | 530 | 52.25 |
| Avg latency (ms) | 2101.2 | 2407.55 | 306.35 |

## Failure modes
```json
{
  "react": {
    "none": 19,
    "wrong_final_answer": 1
  },
  "reflexion": {
    "none": 20
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding

## Discussion
Reflexion helps when the first attempt stops after the first hop or drifts to a wrong second-hop entity. The tradeoff is higher attempts, token cost, and latency. In a real report, students should explain when the reflection memory was useful, which failure modes remained, and whether evaluator quality limited gains.
