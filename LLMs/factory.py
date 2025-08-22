from typing import List
from .BaseLLMClient import BaseLLMClient
from .GigaChatClient import GigaChatClient
from .OpenAIClient import OpenAIClient

# Model names mapped to their providers and client configurations
SUPPORTED_MODELS = {
    # GigaChat models
    "GigaChat": {"provider": "gigachat", "param_name": "model"},
    "GigaChat-Plus": {"provider": "gigachat", "param_name": "model"},
    "GigaChat-Pro": {"provider": "gigachat", "param_name": "model"},
    "GigaChat-Max": {"provider": "gigachat", "param_name": "model"},

    # OpenAI models
    "gpt-4": {"provider": "openai", "param_name": "model_name"},
    "gpt-4-turbo": {"provider": "openai", "param_name": "model_name"},
    "gpt-4o": {"provider": "openai", "param_name": "model_name"},
    "gpt-4o-mini": {"provider": "openai", "param_name": "model_name"},
    "gpt-3.5-turbo": {"provider": "openai", "param_name": "model_name"},
}

# Default model
DEFAULT_MODEL = "GigaChat"

# Create case-insensitive lookup
_MODEL_LOOKUP = {model.lower(): model for model in SUPPORTED_MODELS.keys()}


def normalize_model_name(user_input: str) -> str:
    """
    Normalize user input to correct model name (case-insensitive)
    
    Args:
        user_input: User provided model name (any case)
        
    Returns:
        Correct model name with proper casing
        
    Raises:
        ValueError: If model is not supported
    """
    normalized_input = user_input.lower()
    
    if normalized_input not in _MODEL_LOOKUP:
        available_models = list(SUPPORTED_MODELS.keys())
        raise ValueError(f"Model '{user_input}' is not supported. Available models: {available_models}")
    
    return _MODEL_LOOKUP[normalized_input]


def get_llm_client(model: str = DEFAULT_MODEL, **kwargs) -> BaseLLMClient:
    """
    Creates LLM client based on model name (case-insensitive)

    Args:
        model: Model name (case-insensitive, e.g., "gigachat-pro", "GPT-4O", "GigaChat-Pro")
        **kwargs: Additional parameters for the client

    Returns:
        BaseLLMClient instance

    Raises:
        ValueError: If model is not supported
    """

    # Normalize model name to correct casing
    normalized_model = normalize_model_name(model)
    
    model_config = SUPPORTED_MODELS[normalized_model]
    provider = model_config["provider"]
    param_name = model_config["param_name"]

    # Set model parameter with correct name for the provider
    kwargs[param_name] = normalized_model

    # Create client based on provider
    if provider == "gigachat":
        return GigaChatClient(**kwargs)
    elif provider == "openai":
        return OpenAIClient(**kwargs)
    else:
        raise ValueError(f"Provider '{provider}' is not implemented")
