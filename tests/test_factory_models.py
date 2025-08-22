# -*- coding: utf-8 -*-
"""
Тестирование расширенной factory.py с поддержкой выбора моделей
"""

from LLMs.factory import (
    get_llm_client
)

def test_backwards_compatibility():
    """Тестирование обратной совместимости"""
    print("🔄 Тест обратной совместимости")
    
    try:
        # Старый способ должен работать как раньше
        client = get_llm_client("gigachat")
        print(f"✅ Старый синтаксис работает: {client.__class__.__name__}")
        
        # Проверяем, что используется модель по умолчанию
        if hasattr(client, 'chat') and hasattr(client.chat, 'model'):
            print(f"📋 Модель по умолчанию: {client.chat.model}")
        
    except Exception as e:
        print(f"❌ Ошибка совместимости: {e}")

def test_model_selection():
    """Тестирование выбора конкретных моделей"""
    print(f"\n🎯 Тест выбора моделей")
    
    test_cases = [
        ("gigachat", None, "По умолчанию"),
        ("gigachat", "base", "Базовая через алиас"),
        ("gigachat", "pro", "Pro через алиас"),  
        ("gigachat", "max", "Max через алиас"),
        ("gigachat", "GigaChat-2-Pro", "Pro через полное имя"),
        ("gigachat", "GigaChat-2-Max", "Max через полное имя")
    ]
    
    for provider, model, description in test_cases:
        try:
            if model:
                client = get_llm_client(provider, model)
            else:
                client = get_llm_client(provider)
                
            print(f"✅ {description}: {client.__class__.__name__}")
            
            # Проверяем модель в клиенте
            if hasattr(client, 'chat') and hasattr(client.chat, 'model'):
                print(f"   📋 Установленная модель: {client.chat.model}")
                
        except Exception as e:
            print(f"❌ Ошибка {description}: {e}")

def test_model_listing():
    """Тестирование получения списка моделей"""
    print(f"\n📋 Тест списка доступных моделей")
    
    # Все модели
    all_models = list_available_models()
    print("🌐 Все доступные модели:")
    for provider, models in all_models.items():
        print(f"  {provider.upper()}:")
        for alias, full_name in models.items():
            print(f"    {alias} → {full_name}")
    
    # Модели конкретного провайдера
    gigachat_models = list_available_models("gigachat")
    print(f"\n🤖 Модели GigaChat:")
    for provider, models in gigachat_models.items():
        for alias, full_name in models.items():
            print(f"  {alias} → {full_name}")

def test_real_usage_examples():
    """Примеры реального использования"""
    print(f"\n💼 Примеры реального использования")
    
    examples = [
        ("Базовый GigaChat", lambda: get_llm_client("gigachat")),
        ("GigaChat Pro", lambda: get_llm_client("gigachat-pro")),
        ("GigaChat Max с настройками", lambda: get_llm_client("gigachat-max", temperature=0.7))
    ]
    
    for description, creator in examples:
        try:
            client = creator()
            print(f"✅ {description}: {client.__class__.__name__}")
            query = "Привет, представься!"
            print(f"Запрос: {query}")
            response = client.chat_one(query)
            print(f"   📝 Ответ: {response}")
            
        except Exception as e:
            print(f"❌ {description}: {e}")

def main():
    """Запуск всех тестов"""
    print("🧪 ТЕСТИРОВАНИЕ РАСШИРЕННОЙ FACTORY")
    print("="*50)
    
    # test_backwards_compatibility()
    # test_model_selection()
    # test_model_listing()
    test_real_usage_examples()
    
    print(f"\n🏁 Тестирование завершено!")


if __name__ == "__main__":
    main()
