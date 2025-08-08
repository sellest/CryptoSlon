from abc import ABC, abstractmethod
from typing import Optional

from prompts.PromptManager import PromptManager
import logging

logging.basicConfig(
    level=logging.INFO,
    # INFO – «кто вызван»; DEBUG – полный ответ
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler("llm_calls.log"),
              logging.StreamHandler()]
)
for noisy in ("httpx", "httpcore"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

class BaseLLMClient(ABC):
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.prompt_manager = PromptManager()
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def _invoke(self, messages: list) -> str:
        """
        Внутренний вызов модели с отформатированными сообщениями.
        Реализуется в потомках.
        """
        pass

    def chat(self, user_input: str, name: str = None, system_input: str = None, **kwargs) -> str:
        """
        Универсальный чат-метод с поддержкой PromptManager.
        """
        template = self.prompt_manager.use_template(
            name=name,
            user_input=user_input,
            system_input=system_input
        )
        messages = template.format_messages(**kwargs)

        self.logger.info("invoke → %s | %s messages",
                         self.__class__.__name__, len(messages))
        self.logger.debug("prompt: %s", messages)

        response = self._invoke(messages)
        self.logger.info("response ← %s | %s chars",
                         self.__class__.__name__, len(response))
        self.logger.debug("response body: %s", response)

        return response

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        pass
