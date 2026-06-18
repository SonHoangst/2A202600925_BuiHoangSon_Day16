from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Iterable
from .schemas import QAExample, RunRecord

def normalize_answer(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

def load_dataset(path: str | Path) -> list[QAExample]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    examples = []
    for item in raw:
        # Kiểm tra xem đây là data thô của HotpotQA hay data đã được format
        if "_id" in item:
            context_chunks = []
            for title, sentences in item.get("context", []):
                # Nối các câu lại thành một đoạn văn
                text = " ".join(sentences) if isinstance(sentences, list) else sentences
                context_chunks.append({"title": title, "text": text})
            
            converted_item = {
                "qid": item["_id"],
                "difficulty": item.get("level", "medium"),
                "question": item["question"],
                "gold_answer": item["answer"],
                "context": context_chunks
            }
            examples.append(QAExample.model_validate(converted_item))
        else:
            examples.append(QAExample.model_validate(item))
    return examples

def save_jsonl(path: str | Path, records: Iterable[RunRecord]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(record.model_dump_json() + "\n")
