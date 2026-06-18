# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_dev_distractor_v1.json
- Mode: mock
- Records: 100
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.78 | 0.98 | 0.2 |
| Avg attempts | 1 | 1.24 | 0.24 |
| Avg token estimate | 1778.32 | 2387.8 | 609.48 |
| Avg latency (ms) | 2458.36 | 3574.52 | 1116.16 |

## Failure modes
```json
{
  "react": {
    "none": 39,
    "wrong_final_answer": 11
  },
  "reflexion": {
    "none": 49,
    "wrong_final_answer": 1
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
