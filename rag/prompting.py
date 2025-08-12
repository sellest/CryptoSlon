from typing import Dict

class PromptBuilder:
    def build(self, question: str, ctx: Dict, system_prompt: str, cite: bool = True) -> str:
        """
        ctx: {"text": "...", "citations": [{"id": "[1]", "source": "..."}]}
        Возвращает финальный prompt (или список сообщений), с правилами цитирования [#].
        """
        ...
