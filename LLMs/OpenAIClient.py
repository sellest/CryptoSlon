from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
from .BaseLLMClient import BaseLLMClient
import os

class OpenAIClient(BaseLLMClient):
    def __init__(self, model_name: str = "gpt-4o", embed_model: str = "text-embedding-3-small"):
        super().__init__()
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")

        self.chat_client = ChatOpenAI(
            api_key=api_key,
            model=model_name,
            temperature=0.7,
        )
        self.embed_client = OpenAIEmbeddings(
            api_key=api_key,
            model=embed_model,
        )

    def _invoke(self, prompt: str) -> str:
        return self.chat_client.invoke(prompt).content

    def _embed(self, text: str) -> list[float]:
        return self.embed_client.embed_query(text)
