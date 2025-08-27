# CryptoSlon - фреймворк агентов для хакатона
CryptoSlon — это минималистичный фреймворк для быстрого прототипирования AI-агентов под задачи хакатона:  
от подключения LLM и векторных БД до полного RAG-пайплайна. Он упрощает интеграцию GigaChat, OpenAI, Google Gemini и Groq, 
поддерживает многоязычный поиск, и даёт готовые классы для добавления своих агентов.

Текущий прогресс: 
- подключение LLM - done
- Векторные БД - done
- Векторизация текстов - done
- RAG - done
- Агенты - done
- Embeddings на Gigachat - in progress

## Установка и настройка

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
Скопируйте `.env.example` в `.env` и добавьте API ключи:
```bash
cp .env.example .env
```

Заполните файл `.env`:
```
GIGACHAT_CREDENTIALS=ваш_ключ_gigachat - необходимо
OPENAI_API_KEY=ваш_ключ_openai - опционально
GOOGLE_API_KEY=ваш_ключ_google - опционально
GROQ_API_KEY=ваш_ключ_groq - опционально
SERPER_API_KEY=ваш_ключ_serper - необходимо (гугл-поиск)
```

### 3. Структура проекта
```
.
├── docs                    # Каталог с расширенной документацией 
├── LLMs                    # Каталог классов с различными LLM 
├── README.md               # Этот файл
├── VectorDB                # Каталог классов для инициализации векторных БД и векторизации документов
├── agents                  # Каталог классов для управления Агентами
├── chroma_db               # Хранилище векторынх данных, создается автоматически
├── example_agent_usage.py  # Пример работающего Агента с набором инструментов
├── prompts                 # Каталог с JSON промптами и менеджером
├── rag                     # Каталог для продвинутых функций RAG-процесса
├── requirements.txt        # Зависимости
├── tests                   # Каталог с готовыми тестами различных функций фреймворка
```

## Использование

### 0. QuickStart
```python
python example_agent_usage.py
```

### 1. Работа с Агентами
[Инструкция по запуску агентов](AGENT_USAGE_GUIDE.md)

### 2. Работа с LLM

#### Базовое использование
```python
from LLMs.factory import get_llm_client

# Создание клиента
llm = get_llm_client("gigachat")  # или "openai", "google", "groq"

# Простой запрос
response = llm.chat_one("Привет, как дела?")
print(response)

# Запрос с системным промптом
system_prompt = "Ты эксперт по кибербезопасности"
response = llm.chat_one("Что такое SQL injection?", system_prompt)
print(response)
```
Пример: [Test LLM](../tests/test_llm_connection.py)


### 3. Создание векторной базы данных
Векторная БД — это хранилище, которое сохраняет тексты, изображения или другие данные в виде числовых векторов (эмбеддингов).
Эти векторы позволяют сравнивать смысловую близость объектов, а не только точное совпадение слов.
Сохраняет данные на локальную машину. Экземпляр БД должен быть построен на основе класса [BaseChromaDB](../VectorDB/base_chroma_db.py).

```python
from VectorDB.base_chroma_db import BaseChromaDB

# Создание базы данных
vector_db = BaseChromaDB(
    collection_name="cybersec_knowledge",
    model_name="intfloat/multilingual-e5-base"  # Поддерживает русский язык
)
```
Пример: [Test VectorDB](../tests/test_vectordb.py)

### 4. Векторизация .txt файлов
_Для запуска векторизации необходима существующая векторная БД_

#### Метод 1: Добавление файлов
Используется для добавления новой информации, а так же для первой записи в БД
```python
from vectorize_documents import SimpleVectorizer

# Инициализация
vectorizer = SimpleVectorizer("my_knowledge_base")

# Список файлов для обработки
files = [
    "data/security_doc1.txt",
    "data/malware_analysis.txt"
]

# Векторизация
metrics = vectorizer.vectorize_files(files)
vectorizer.print_report(metrics)
```

#### Метод 2: Чистое обновление (удаляет старые данные)
Используется, когда требуется обновить базу данных и исключить дупликацию данных, например, в случае, 
когда существующий файл был дополнен новой информацией.
```python
# Полная перезапись базы данных
metrics = vectorizer.clean_and_add(files)
vectorizer.print_report(metrics)
```
Пример: [Test VectorizeDocuments](VectorDB/test_vectorize_documents.py)

### 4. Использование RAG системы
Подробнее смотри в гайд о RAG, который я добавлю в /docs когда-нибудь

Пример: [Test RAG](../tests/test_full_rag.py)

## Поддерживаемые модели
Поддерживается любая модель, входящая в состав библиотеки [langchain](https://python.langchain.com/docs/integrations/chat/)

В проект включены: 
- **GigaChat** - российская LLM с поддержкой русского языка
- **Google Gemini** - модели Gemini
- **Groq** - быстрые модели
