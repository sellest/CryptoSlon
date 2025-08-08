from langchain_gigachat.chat_models import GigaChat
from langchain_gigachat.embeddings import GigaChatEmbeddings
from .BaseLLMClient import BaseLLMClient
from dotenv import load_dotenv
import os


class GigaChatClient(BaseLLMClient):
    def __init__(self, model_name: str = "GigaChat-Pro"):
        super().__init__()
        load_dotenv()
        credentials = os.getenv("GIGACHAT_CREDENTIALS")

        self.chat_client = GigaChat(
            credentials=credentials,
            verify_ssl_certs=False,
            model=model_name,
        )
        self.embed_client = GigaChatEmbeddings(
            credentials=credentials,
            verify_ssl_certs=False,
        )

    def _invoke(self, prompt: list) -> str:
        return self.chat_client.invoke(prompt).content

    def embed(self, text: str) -> list[float]:
        return self.embed_client.embed_query(text)
