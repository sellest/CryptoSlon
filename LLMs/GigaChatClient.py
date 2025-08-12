# giga_client.py
import os
from typing import Any, List, Optional, Dict
import logging
from dotenv import load_dotenv
from LLMs.BaseLLMClient import BaseLLMClient
from langchain_gigachat import GigaChat
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

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

    def _invoke(self, messages: List[RoleMsg]) -> str:
        lc_msgs = []
        for m in messages:
            role = (m.get("role") or "user").lower()
            content = m.get("content") or ""
            constructor = ROLE_MAP.get(role, HumanMessage)
            lc_msgs.append(constructor(content=content))

        resp = self.chat.invoke(lc_msgs)
        return getattr(resp, "content", str(resp))
