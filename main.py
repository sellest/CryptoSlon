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


if __name__ == "__main__":
    # Раскомментируйте нужный тест:
    
    # Тест queryprep
    test_queryprep()

    # gc = get_llm_client("gigachat")
    # messages = "Привет, представься"
    # print(gc.chat_one(messages))
