from typing import Optional, Dict, Any
from .BaseLLMClient import BaseLLMClient
from .GigaChatClient import GigaChatClient
from .GroqClient import GroqClient
from .OpenAIClient import OpenAIClient
from .GeminiClient import GeminiClient

# Предустановленные конфигурации для популярных моделей
PROVIDER_MODELS = {
    "gigachat": {
        "default": "GigaChat-2",
        "base": "GigaChat-2", 
        "pro": "GigaChat-2-Pro",
        "max": "GigaChat-2-Max"
    },
    "openai": {
        "default": "gpt-5-mini",
        "gpt-5": "gpt-5",
        "gpt-5-nano": "gpt-5-nano",
    }
}

def get_llm_client(
    provider: str, 
    model: Optional[str] = None, 
    **kwargs
) -> BaseLLMClient:
    """
    Создает клиент LLM с поддержкой выбора конкретной модели
    
    Args:
        provider: Провайдер ("gigachat", "openai", "google", "groq")
        model: Конкретная модель или алиас (например, "pro", "max", "gpt4")
        **kwargs: Дополнительные параметры для клиента
        
    Returns:
        Экземпляр BaseLLMClient
    """
    provider = provider.lower()
    
    # Обработка модели и алиасов
    if model and provider in PROVIDER_MODELS:
        # Если модель - это алиас, заменяем на полное имя
        if model.lower() in PROVIDER_MODELS[provider]:
            model = PROVIDER_MODELS[provider][model.lower()]
        # Если модель не указана, используем default
    elif provider in PROVIDER_MODELS:
        model = PROVIDER_MODELS[provider]["default"]

    # Вызов Gigachat
    if provider == "gigachat":
        if model:
            kwargs["model"] = model
        return GigaChatClient(**kwargs)

    # Вызов ChatGPT
    elif provider == "openai":
        if model:
            kwargs["model_name"] = model
        return OpenAIClient(**kwargs)
        
    # elif provider == "google":
    #     if model:
    #         kwargs["model_name"] = model
    #     return GeminiClient(**kwargs)
    #
    # elif provider == "groq":
    #     if model:
    #         kwargs["model_name"] = model
    #     return GroqClient(**kwargs)
    #
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

def list_available_models(provider: Optional[str] = None) -> Dict[str, Any]:
    """
    Возвращает доступные модели
    
    Args:
        provider: Конкретный провайдер или None для всех
        
    Returns:
        Словарь с доступными моделями
    """
    if provider:
        provider = provider.lower()
        if provider in PROVIDER_MODELS:
            return {provider: PROVIDER_MODELS[provider]}
        else:
            return {}
    
    return PROVIDER_MODELS.copy()
