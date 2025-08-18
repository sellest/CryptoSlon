import os
import requests
from dotenv import load_dotenv


class InternetSearchTool:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("SERPER_API_KEY")
        self.endpoint = "https://google.serper.dev/search"

        if not self.api_key:
            raise ValueError("SERPER_API_KEY not найден в .env")

    def search(self, query: str) -> str:
        """Выполняет поиск и возвращает краткий фрагмент первого найденного результата"""
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        data = {"q": query}

        response = requests.post(self.endpoint, headers=headers, json=data)
        response.raise_for_status()
        results = response.json()

        organic = results.get("organic", [])
        if organic:
            first = organic[0]
            snippet = first.get("snippet", "")
            link = first.get("link", "")
            return f"{snippet}\nИсточник: {link}"

        return "Ничего не найдено."
