from typing import List
from langchain_core.documents import Document
# варианты: sentence-transformers CrossEncoder, flashrank, CohereRerank, JinaRerank
class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        # инициализируй здесь CrossEncoder, если используешь sbert; или обертку langchain_community
        ...

    def run(self, query: str, docs: List[Document], top_k: int = 7) -> List[Document]:
        """Считает двунаправочные cross‑encoder score и возвращает top_k."""
        ...
