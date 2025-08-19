import logging
from LLMs.factory import get_llm_client
from rag.queryprep import QueryPreprocessor

logging.basicConfig(level=logging.INFO)


def test_queryprep():
    """Тестирование обработки запросов"""
    print("=== Testing QueryPreprocessor ===")
    prep = QueryPreprocessor()

    # Тестовые запросы для кибербезопасности
    test_queries = [
        "Как защититься от malware на 192.168.1.1?"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i} ---")
        print(f"Original: {query}")

        result = prep.run(query)
        print(f"Language: {result.language}")
        print(f"Entities: {result.entities}")
        print(f"Rewritten: {result.rewritten}")


def test_embeddings():
    """Тестирование эмбеддингов"""
    print("\n=== Testing Embeddings ===")
    gc = get_llm_client("gigachat")

    # Тестовые тексты для кибербезопасности
    test_texts = [
        "Как защититься от malware?",
        "SQL injection vulnerability",
        "Настройка firewall для блокировки атак"
    ]

    print("Testing batch embeddings...")
    embeddings = gc.embed_texts(test_texts)
    for i, (text, emb) in enumerate(zip(test_texts, embeddings)):
        print(f"Text {i + 1}: {text}")
        print(f"Embedding dim: {len(emb)}, first 5 values: {emb[:5]}")

    print("\nTesting single embedding...")
    single_emb = gc.embed_single("CVE-2023-1234 exploit")
    print(f"Single embedding dim: {len(single_emb)}, first 5 values: {single_emb[:5]}")


if __name__ == "__main__":
    # Прямое обращение к модели
    gc = get_llm_client("gigachat")
    messages = "Привет, представься"
    print(gc.chat_one(messages))

    # Тест queryprep
    # test_queryprep()

    # Тест эмбеддингов
    # test_embeddings()

