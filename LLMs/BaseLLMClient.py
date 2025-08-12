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