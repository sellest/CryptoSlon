import os
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_gigachat.chat_models import GigaChat
from langchain_gigachat.embeddings import GigaChatEmbeddings
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class LLMTools:
    def __init__(self):
        load_dotenv()
        # Получение переменных окружения из .env
        self.credentials = os.getenv("GIGACHAT_CREDENTIALS")

        # Инициализация чата
        self.chat_client = GigaChat(
            credentials=self.credentials,
            verify_ssl_certs=False
        )
        # Инициализация эмбеддинга
        self.embed_client = GigaChatEmbeddings(
            credentials=self.credentials,
            verify_ssl_certs=False
        )

    def chat(self, prompt: str) -> BaseMessage:
        """Отправка простого сообщения"""
        return self.chat_client.invoke(prompt)

    def embed(self, text: str) -> list[float]:
        """Получение эмбеддинга одного текста"""
        return self.embed_client.embed_query(text)

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Эмбеддинг нескольких текстов"""
        return self.embed_client.embed_documents(texts)


if __name__ == '__main__':
    client = GigaChatTools()
    try:
        msg = client.chat("Hello, World!")
    except Exception as err:
        logger.error("Unexpected error during upsert_sales: %s", err, exc_info=True)
        raise

    logger.info(f"server response: %s", msg)

