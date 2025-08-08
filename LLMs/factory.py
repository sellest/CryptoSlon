from .BaseLLMClient import BaseLLMClient
from .GigaChatClient import GigaChatClient
from .GroqClient import GroqClient
from .OpenAIClient import OpenAIClient
from .GeminiClient import GeminiClient

def get_llm_client(provider: str) -> BaseLLMClient:
    provider = provider.lower()
    if provider == "gigachat":
        return GigaChatClient()
    elif provider == "openai":
        return OpenAIClient()
    elif provider == "google":
        return GeminiClient()
    elif provider == "groq":
        return GroqClient()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
