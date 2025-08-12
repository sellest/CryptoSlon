from typing import List
from langchain_core.documents import Document

class Guardrails:
    def __init__(self, min_docs: int = 3, min_avg_score: float = 0.2):
        self.min_docs = min_docs
        self.min_avg_score = min_avg_score

    def check(self, query: str, docs: List[Document], scores: List[float]) -> dict:
        """
        Возвращает dict со статусом ok/insufficient + сообщением для пользователя, если недостаточно контекста.
        """
        ...
