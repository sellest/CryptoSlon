from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from .BaseLLMClient import BaseLLMClient
import os


class GeminiClient(BaseLLMClient):
    def __init__(self, model_name: str = "gemini-2.5-flash", embed_model: str = "models/embedding-001"):
        super().__init__()
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")

        self.chat_client = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7
        )
        self.embed_client = GoogleGenerativeAIEmbeddings(
            model=embed_model,
            google_api_key=api_key
        )

    def _invoke(self, prompt: list) -> str:
        return self.chat_client.invoke(prompt).content

    def embed(self, text: str) -> list[float]:
        return self.embed_client.embed_query(text)
