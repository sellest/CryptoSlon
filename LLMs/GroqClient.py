from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from .BaseLLMClient import BaseLLMClient
import os

class GroqClient(BaseLLMClient):
    def __init__(
        self,
        model_name: str = "llama3-70b-8192",
        embed_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        temperature: float = 0.7,
    ):
        super().__init__()
        load_dotenv()

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Переменная среды GROQ_API_KEY не установлена")

        # ---- чат-модель Groq ----
        self.chat_client = ChatGroq(
            model=model_name,
            # api_key=api_key,
            temperature=temperature
        )

        # ---- эмбеддинги (open-source) ----
        self.embed_client = HuggingFaceEmbeddings(model_name=embed_model)

    # BaseLLMClient ждёт эти два метода
    def _invoke(self, messages: list) -> str:
        return self.chat_client.invoke(messages).content

    def embed(self, text: str) -> list[float]:
        return self.embed_client.embed_query(text)