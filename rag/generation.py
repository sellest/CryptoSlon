from typing import Dict

class Generator:
    def __init__(self, llm_client):
        self.llm = llm_client

    def run(self, prompt) -> str:
        try:
            return self.llm.chat(prompt)
        except TypeError:
            return self.llm.chat([{"role":"user","content":prompt}])
