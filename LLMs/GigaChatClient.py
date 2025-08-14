# giga_client.py
import os
from typing import Any, List, Optional, Dict
import logging
from dotenv import load_dotenv
from LLMs.BaseLLMClient import BaseLLMClient
from langchain_gigachat import GigaChat
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sentence_transformers import SentenceTransformer

RoleMsg = Dict[str, str]  # {"role": "system"|"user"|"assistant", "content": "..."}

ROLE_MAP = {
    "system": SystemMessage,
    "user": HumanMessage,
    "assistant": AIMessage,
}

class GigaChatClient(BaseLLMClient):
    def __init__(
        self,
        scope: str = "GIGACHAT_API_PERS",
        model: str = "GigaChat",
        temperature: float = 0.2,
        verify_ssl_certs: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(logger)
        load_dotenv()
        credentials=os.getenv("GIGACHAT_CREDENTIALS")
        self.chat = GigaChat(
            credentials=credentials,
            scope=scope,
            model=model,
            temperature=temperature,
            verify_ssl_certs=verify_ssl_certs,
        )
        
        # Для эмбеддингов используем multilingual модель от sentence-transformers
        self.embedding_model = None  # Ленивая загрузка

    def _invoke(self, messages: List[RoleMsg]) -> str:
        lc_msgs = []
        for m in messages:
            role = (m.get("role") or "user").lower()
            content = m.get("content") or ""
            constructor = ROLE_MAP.get(role, HumanMessage)
            lc_msgs.append(constructor(content=content))

        resp = self.chat.invoke(lc_msgs)
        return getattr(resp, "content", str(resp))

    def _load_embedding_model(self):
        """Ленивая загрузка модели эмбеддингов"""
        if self.embedding_model is None:
            # Используем multilingual модель для поддержки русского языка
            model_name = "intfloat/multilingual-e5-large"
            self.logger.info(f"Loading embedding model: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
        return self.embedding_model

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Получение эмбеддингов с помощью sentence-transformers"""
        if not texts:
            return []
        try:
            model = self._load_embedding_model()
            # Для multilingual-e5 моделей рекомендуется добавлять префикс
            prefixed_texts = [f"query: {text}" for text in texts]
            embeddings = model.encode(prefixed_texts, normalize_embeddings=True)
            # Конвертируем в список списков float
            return [embedding.tolist() for embedding in embeddings]
        except Exception as e:
            self.logger.error(f"Ошибка при получении эмбеддингов: {e}")
            # Возвращаем пустые векторы в случае ошибки
            return [[0.0] * 1024 for _ in texts]
