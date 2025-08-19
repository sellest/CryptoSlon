# Руководство по работе с LLM-клиентами

## Обзор архитектуры
Все модели построены с использованием фреймворка langchain.

Система LLM-клиентов построена по принципу абстракция → реализация → фабрика:
- **BaseLLMClient** - абстрактный базовый класс
- **GigaChatClient, OpenAIClient, etc.** - конкретные реализации
- **factory.py** - удобная фабрика для создания клиентов

## BaseLLMClient - базовая абстракция

[BaseLLMClient](../LLMs/BaseLLMClient.py) определяет единый интерфейс для всех LLM-провайдеров:

### Абстрактные методы (требуют реализации в наследниках):
```python
@abstractmethod
def _invoke(self, messages: List[Any]) -> str:
    """Низкоуровневый вызов модели."""
    
@abstractmethod 
def _embed(self, texts: List[str]) -> List[List[float]]:
    """Низкоуровневый вызов для получения эмбеддингов."""
```

### Готовые методы (работают во всех реализациях):
```python
def chat_one(self, user_input: str, system_prompt: Optional[str] = None) -> str:
    """Простой чат: одна строка → ответ модели"""

def chat_raw(self, messages: List[Any]) -> str:
    """Низкоуровневый чат с массивом сообщений"""
    
def embed_texts(self, texts: List[str]) -> List[List[float]]:
    """Получение эмбеддингов для списка текстов"""
    
def embed_single(self, text: str) -> List[float]:
    """Получение эмбеддинга для одного текста"""
```

## Создание собственного LLM-клиента

### Шаг 1: Наследование от BaseLLMClient

```python
from LLMs.BaseLLMClient import BaseLLMClient, RoleMsg
from typing import List, Optional
import logging
from dotenv import load_dotenv

class MyCustomClient(BaseLLMClient):
    def __init__(self, api_key: str, logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        load_dotenv()
        self.api_key = os.getenv("<YOUR CREDITENTIALS>")
        self.client = SomeCustomAPI(api_key=api_key)
```

### Шаг 2: Реализация _invoke

```python
def _invoke(self, messages: List[RoleMsg]) -> str:
    """
    Реализуем логику вызова вашего API
    messages - список словарей вида: {"role": "user/system/assistant", "content": "текст"}
    """
    try:
        # Преобразуем внутренний формат в формат вашего API
        api_messages = []
        for msg in messages:
            api_messages.append({
                "role": msg.get("role", "user"),
                "text": msg.get("content", "")
            })
        
        # Вызов API
        response = self.client.chat(api_messages)
        
        # Возвращаем текст ответа
        return response.get("text", "")
        
    except Exception as e:
        self.logger.error(f"API call failed: {e}")
        raise RuntimeError(f"Ошибка вызова CustomAPI: {str(e)}")
```

### Шаг 3: Реализация _embed

_В настоящий момент эмбеддинги от GigaChat не реализованы, используются OpenSource модели_

```python
def _embed(self, texts: List[str]) -> List[List[float]]:
    """
    Реализуем получение эмбеддингов
    """
    try:
        # Вызов API для эмбеддингов
        response = self.client.embeddings(texts)
        
        # Возвращаем список векторов
        return response.get("embeddings", [])
        
    except Exception as e:
        self.logger.error(f"Embedding call failed: {e}")
        raise RuntimeError(f"Ошибка получения эмбеддингов: {str(e)}")
```

## Пример: GigaChatClient

[GigaChatClient](../LLMs/GigaChatClient.py) - это полная реализация для GigaChat:

Работающий пример представлен в [test_llm_connection](../tests/test_llm_connection.py)

### Инициализация:
```python
class GigaChatClient(BaseLLMClient):
    def __init__(
        self,
        scope: str = "GIGACHAT_API_PERS",
        model: str = "GigaChat-2", 
        temperature: float = 0.2,
        verify_ssl_certs: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(logger)
        load_dotenv()
        credentials = os.getenv("GIGACHAT_CREDENTIALS")
        
        # Инициализация через langchain_gigachat
        self.chat = GigaChat(
            credentials=credentials,
            scope=scope,
            model=model,
            temperature=temperature,
            verify_ssl_certs=verify_ssl_certs,
        )
```

### Реализация _invoke:
```python
def _invoke(self, messages: List[RoleMsg]) -> str:
    # Преобразование в формат langchain
    lc_msgs = []
    for m in messages:
        role = (m.get("role") or "user").lower()
        content = m.get("content") or ""
        constructor = ROLE_MAP.get(role, HumanMessage)
        lc_msgs.append(constructor(content=content))

    # Вызов модели
    resp = self.chat.invoke(lc_msgs)
    return getattr(resp, "content", str(resp))
```

## Использование через Factory

### Настройка переменных окружения
Создайте файл `.env`:
```env
GIGACHAT_CREDENTIALS=ваш_ключ_gigachat
```

### Простое использование:
```python
from LLMs.factory import get_llm_client

# Создание клиента
llm = get_llm_client("gigachat")  # или "openai", "google", "groq"

# Простой запрос
response = llm.chat_one("Привет, как дела?")
print(response)

# С системным промптом
system_prompt = "Ты эксперт по кибербезопасности"
response = llm.chat_one("Что такое SQL injection?", system_prompt)
print(response)
```

### Расширенное использование:
```python
# Многосообщенческий диалог
messages = [
    {"role": "system", "content": "Ты помощник программиста"},
    {"role": "user", "content": "Объясни принцип SOLID"},
    {"role": "assistant", "content": "SOLID - это пять принципов..."},
    {"role": "user", "content": "А теперь пример на Python"}
]

response = llm.chat_raw(messages)
print(response)
```

### Работа с эмбеддингами:
```python
# Получение эмбеддингов
texts = [
    "Это первый документ",
    "А это второй документ", 
    "Третий документ о кибербезопасности"
]

# Для нескольких текстов
embeddings = llm.embed_texts(texts)
print(f"Получено {len(embeddings)} векторов размерности {len(embeddings[0])}")

# Для одного текста
single_embedding = llm.embed_single("Один текст для векторизации")
print(f"Вектор размерности: {len(single_embedding)}")
```

## Добавление нового провайдера

### Шаг 1: Создайте класс клиента
```python
# LLMs/MyProviderClient.py
from LLMs.BaseLLMClient import BaseLLMClient

class MyProviderClient(BaseLLMClient):
    def _invoke(self, messages):
        # Ваша реализация
        pass
        
    def _embed(self, texts):
        # Ваша реализация
        pass
```

### Шаг 2: Добавьте в фабрику
```python
# LLMs/factory.py
from .MyProviderClient import MyProviderClient

def get_llm_client(provider: str) -> BaseLLMClient:
    provider = provider.lower()
    if provider == "myprovider":
        return MyProviderClient()
    # ... остальные провайдеры
```

### Шаг 3: Используйте как обычно
```python
llm = get_llm_client("myprovider")
response = llm.chat_one("Тестовый запрос")
```

## Рекомендации

### Обработка ошибок:
- Используйте try...except и логирование, чтобы избежать непредвиденного завершения программы
- Логируйте детальные ошибки для отладки
- Возвращайте понятные пользователю сообщения

### Логирование:
- Используйте `self.logger` для записи событий
- Логируйте вызовы API и их результаты
- НЕ логируйте API ключи и чувствительные данные
