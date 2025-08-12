from typing import List, Dict
from langchain_core.documents import Document

class ContextPacker:
    def __init__(self, token_limit: int, tokenizer):  # tokenizer = tiktoken или свой
        self.limit = token_limit
        self.tok = tokenizer

    def run(self, docs: List[Document]) -> Dict:
        """
        dedup (по source+hash), smart merge (склейка соседних чанков одного источника),
        сортировка: coverage + recency, жёсткий лимит токенов.
        Возвращает dict со склеенным контекстом + mapping [id]->source.
        """
        ...
