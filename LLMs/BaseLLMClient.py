from abc import ABC, abstractmethod
from typing import Any, List, Optional, Dict
import logging

RoleMsg = Dict[str, str]

class BaseLLMClient(ABC):
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def _invoke(self, messages: List[Any]) -> str:
        """Низкоуровневый вызов модели."""
        raise NotImplementedError

    @abstractmethod
    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Низкоуровневый вызов для получения эмбеддингов."""
        raise NotImplementedError

    def chat_raw(self, messages: List[Any]) -> str:
        self.logger.info("invoke → %s | %d messages", self.__class__.__name__, len(messages))
        response = self._invoke(messages)
        self.logger.info("response ← %s | %d chars", self.__class__.__name__, len(response or ""))
        return response

    def chat_one(self, user_input: str, system_prompt: Optional[str] = None) -> str:
        """Удобный метод: одна строка пользователя (+ опционально system) → ответ модели."""
        msgs: List[RoleMsg] = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": user_input})
        return self.chat_raw(msgs)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Получение эмбеддингов для списка текстов."""
        if not texts:
            return []
        
        self.logger.info("embed → %s | %d texts", self.__class__.__name__, len(texts))
        embeddings = self._embed(texts)
        
        # Проверяем результат
        if embeddings and len(embeddings) > 0:
            dim = len(embeddings[0])
            self.logger.info("embeddings ← %s | %d vectors, dim=%d", 
                           self.__class__.__name__, len(embeddings), dim)
        else:
            self.logger.warning("embeddings ← %s | empty result", self.__class__.__name__)
        
        return embeddings

    def embed_single(self, text: str) -> List[float]:
        """Получение эмбеддинга для одного текста."""
        embeddings = self.embed_texts([text])
        return embeddings[0] if embeddings else []