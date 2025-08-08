from typing import Optional

from langchain.prompts import ChatPromptTemplate
from pathlib import Path
import json
from langchain.prompts.chat import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

class PromptManager:
    def __init__(self, base_dir: str = "prompts/templates"):
        self.base_dir = Path(base_dir)
        self.cache = {}

    def load_prompt(self, name: str) -> ChatPromptTemplate:
        """
        Загружает шаблон из файла JSON (ключи: system, user, messages).
        Кеширует результат.
        """
        if name in self.cache:
            return self.cache[name]

        path = self.base_dir / f"{name}.json"
        if not path.exists():
            if name != "default":
                print(f"[PromptManager] Шаблон '{name}' не найден. Использую 'default'.")
                return self.load_prompt("default")
            else:
                raise FileNotFoundError(f"[PromptManager] Шаблон 'default.json' не найден.")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        messages = []

        if "system" in data:
            messages.append(("system", data["system"]))
        if "user" in data:
            messages.append(("user", data["user"]))
        if "messages" in data:
            messages.extend(data["messages"])  # список пар (role, content)

        prompt = ChatPromptTemplate.from_messages(messages)
        self.cache[name] = prompt
        return prompt

    def list_prompts(self):
        return [p.stem for p in self.base_dir.glob("*.json")]

    def use_template(
        self,
        name: Optional[str] = None,
        user_input: Optional[str] = None,
        system_input: Optional[str] = None,
    ) -> ChatPromptTemplate:
        """
        Возвращает ChatPromptTemplate, подставляя user_input / system_input.
        Если шаблон name не найден — fallback на default.json
        """
        tpl = self.load_prompt(name or "default")

        # База из шаблона
        base_msgs = tpl.messages

        final: list[tuple[str, str]] = []

        # ---------- system ----------
        if system_input:
            final.append(("system", system_input))
        else:
            for m in base_msgs:
                if isinstance(m, SystemMessagePromptTemplate):
                    final.append(("system", m.prompt.template))
                    break                      # берём первый найденный

        # ---------- user ------------
        if user_input:
            final.append(("user", user_input))
        else:
            for m in base_msgs:
                if isinstance(m, HumanMessagePromptTemplate):
                    final.append(("user", m.prompt.template))
                    break

        if not final:
            raise ValueError("Не удалось собрать ни одного сообщения для промпта")

        return ChatPromptTemplate.from_messages(final)
