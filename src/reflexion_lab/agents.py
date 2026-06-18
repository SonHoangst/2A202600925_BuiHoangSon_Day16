from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Literal
from .mock_runtime import actor_answer, evaluator, reflector
from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord

@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    max_attempts: int = 1
    def run(self, example: QAExample) -> RunRecord:
        reflection_memory: list[str] = []
        reflections: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0
        for attempt_id in range(1, self.max_attempts + 1):
            start_time = time.time()
            answer, actor_tokens = actor_answer(example, attempt_id, self.agent_type, reflection_memory)
            judge, eval_tokens = evaluator(example, answer)
            latency_ms = int((time.time() - start_time) * 1000)
            token_estimate = actor_tokens + eval_tokens
            trace = AttemptTrace(attempt_id=attempt_id, answer=answer, score=judge.score, reason=judge.reason, token_estimate=token_estimate, latency_ms=latency_ms)
            final_answer = answer
            final_score = judge.score
            if judge.score == 1:
                traces.append(trace)
                break
            
            if self.agent_type == "reflexion" and attempt_id < self.max_attempts:
                # 2. Gọi hàm reflector để lấy nội dung reflection
                ref_start = time.time()
                reflection_entry, ref_tokens = reflector(example, attempt_id, judge)
                ref_latency = int((time.time() - ref_start) * 1000)
                
                trace.token_estimate += ref_tokens
                trace.latency_ms += ref_latency
                
                reflections.append(reflection_entry)
                trace.reflection = reflection_entry
                
                # 3. Cập nhật reflection_memory để Actor dùng cho lần sau
                memory_text = f"Failure: {reflection_entry.failure_reason} | Lesson: {reflection_entry.lesson} | Strategy: {reflection_entry.next_strategy}"
                reflection_memory.append(memory_text)
            
            traces.append(trace)
        total_tokens = sum(t.token_estimate for t in traces)
        total_latency = sum(t.latency_ms for t in traces)
        failure_mode = "none"
        if final_score == 0:
            failure_mode = "wrong_final_answer"
            if traces:
                last_reason = traces[-1].reason.lower()
                if "missing" in last_reason or "hop" in last_reason:
                    failure_mode = "incomplete_multi_hop"
                elif "hallucinat" in last_reason or "drift" in last_reason:
                    failure_mode = "entity_drift"
                if len(traces) >= 2 and traces[-1].answer == traces[-2].answer:
                    failure_mode = "looping"
        return RunRecord(qid=example.qid, question=example.question, gold_answer=example.gold_answer, agent_type=self.agent_type, predicted_answer=final_answer, is_correct=bool(final_score), attempts=len(traces), token_estimate=total_tokens, latency_ms=total_latency, failure_mode=failure_mode, reflections=reflections, traces=traces)

class ReActAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_type="react", max_attempts=1)

class ReflexionAgent(BaseAgent):
    def __init__(self, max_attempts: int = 3) -> None:
        super().__init__(agent_type="reflexion", max_attempts=max_attempts)
