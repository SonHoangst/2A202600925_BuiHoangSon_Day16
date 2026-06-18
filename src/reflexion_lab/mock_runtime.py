import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI

from .schemas import QAExample, JudgeResult, ReflectionEntry
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM

# Load environment variables
load_dotenv()

# Khởi tạo OpenAI client trỏ tới Deepseek API
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# Sử dụng deepseek-chat. Model này đủ tốt nhưng nếu gặp câu hỏi phức tạp (multi-hop) mà không có Reflection thì vẫn có thể sai.
MODEL_NAME = "deepseek-chat"

def actor_answer(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> tuple[str, int]:
    """Gọi LLM để trả lời câu hỏi dựa trên ngữ cảnh."""
    
    # 1. Ghép context lại thành văn bản
    context_text = "\n\n".join([f"[{chunk.title}]: {chunk.text}" for chunk in example.context])
    
    # 2. Xây dựng câu hỏi cho LLM
    user_prompt = f"Context:\n{context_text}\n\nQuestion: {example.question}"
    
    # 3. Nếu có rút kinh nghiệm từ lần chạy trước, đưa luôn vào để LLM học hỏi
    if reflection_memory:
        memories = "\n".join(reflection_memory)
        user_prompt += f"\n\nReflection Memory (DO NOT REPEAT PREVIOUS MISTAKES):\n{memories}"
    
    # 4. Gửi request tới Groq
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": ACTOR_SYSTEM},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.4, # Để thấp một chút cho câu trả lời ổn định
        max_tokens=256
    )
    
    return response.choices[0].message.content.strip(), response.usage.total_tokens if response.usage else 0

def evaluator(example: QAExample, answer: str) -> JudgeResult:
    """Gọi LLM để chấm điểm câu trả lời."""
    
    user_prompt = f"Question: {example.question}\nGold Answer: {example.gold_answer}\nPredicted Answer: {answer}"
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": EVALUATOR_SYSTEM},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0, # Chấm điểm cần sự chính xác tuyệt đối
        response_format={"type": "json_object"} # Bắt buộc LLM trả về JSON
    )
    
    json_response = response.choices[0].message.content
    # Parse chuỗi JSON thành object JudgeResult (tự động validate)
    return JudgeResult.model_validate_json(json_response), response.usage.total_tokens if response.usage else 0

def reflector(example: QAExample, attempt_id: int, judge: JudgeResult) -> ReflectionEntry:
    """Gọi LLM để phân tích lý do sai và đề xuất chiến thuật."""
    
    # Đưa vào câu trả lời sai và lý do sai mà giám khảo vừa chấm
    user_prompt = f"Question: {example.question}\nWrong Answer: {judge.spurious_claims}\nEvaluator's Reason for Failure: {judge.reason}"
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": REFLECTOR_SYSTEM},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5, # Để hơi cao tí cho model suy nghĩ linh hoạt hơn
        response_format={"type": "json_object"}
    )
    
    json_response = response.choices[0].message.content
    
    # Parse chuỗi JSON thành đối tượng ReflectionEntry. 
    # Mẹo nhỏ: LLM có thể quên trả về attempt_id, ta có thể tự gán đè lên cho an toàn.
    entry = ReflectionEntry.model_validate_json(json_response)
    entry.attempt_id = attempt_id
    return entry, response.usage.total_tokens if response.usage else 0
