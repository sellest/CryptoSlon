# -*- coding: utf-8 -*-
"""
Тестирование инструментов и ToolManager
"""

import sys
import os
import logging

# Добавляем корневую папку проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.tool_manager import ToolManager, ToolResult
from agents.tools.security_tool import PasswordAnalyzerTool, HashGeneratorTool, VulnerabilityCheckerTool
from agents.tools.search_tool import WebSearchTool

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

def test_password_analyzer():
    """Тестирование анализатора паролей"""
    print("\n🔍 ТЕСТ: Анализатор паролей")
    print("=" * 40)
    
    try:
        tool = PasswordAnalyzerTool()
        
        print(f"Имя инструмента: {tool.name}")
        print(f"Описание: {tool.description}")
        print(f"Параметры: {tool.parameters}")
        
        # Тестовые пароли
        test_passwords = [
            "123456",           # Очень слабый
            "password123",      # Слабый  
            "MyP@ssw0rd123",   # Средний/хороший
            "Tr0ub4dor&3"      # Хороший
        ]
        
        for password in test_passwords:
            print(f"\n🧪 Тестирую пароль: '{password}'")
            result = tool.execute(password=password)
            
            if result["success"]:
                print("✅ Анализ выполнен успешно")
                print(f"📊 Результат:\n{result['analysis'][:200]}...")
            else:
                print(f"❌ Ошибка: {result['error']}")
                
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

def test_hash_generator():
    """Тестирование генератора хешей"""
    print("\n🔐 ТЕСТ: Генератор хешей")
    print("=" * 40)
    
    try:
        tool = HashGeneratorTool()
        
        print(f"Имя инструмента: {tool.name}")
        print(f"Описание: {tool.description}")
        print(f"Параметры: {tool.parameters}")
        
        # Тестовые данные
        test_cases = [
            {"text": "Hello World", "algorithm": "sha256"},
            {"text": "Sensitive data", "algorithm": "md5"},
            {"text": "Test string", "algorithm": "sha1"},
            {"text": "Русский текст"}  # Без алгоритма (по умолчанию)
        ]
        
        for case in test_cases:
            text = case["text"]
            algo = case.get("algorithm", "sha256")
            
            print(f"\n🧪 Хеширую: '{text}' алгоритмом {algo}")
            
            if "algorithm" in case:
                result = tool.execute(text=text, algorithm=algo)
            else:
                result = tool.execute(text=text)
            
            if result["success"]:
                print("✅ Хеш сгенерирован успешно")
                print(f"🔑 Алгоритм: {result['algorithm']}")
                print(f"📝 Хеш: {result['hash']}")
                print(f"📏 Длина: {result['length']} символов")
            else:
                print(f"❌ Ошибка: {result['error']}")
                
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")

def test_vulnerability_checker():
    """Тестирование проверки уязвимостей"""
    print("\n🛡️  ТЕСТ: Проверка уязвимостей")
    print("=" * 40)
    
    try:
        tool = VulnerabilityCheckerTool()
        
        print(f"Имя инструмента: {tool.name}")
        print(f"Описание: {tool.description}")
        
        # Тестовые фрагменты кода с уязвимостями
        test_codes = [
            {
                "code": "cursor.execute('SELECT * FROM users WHERE id = ' + user_id)",
                "language": "python",
                "expected_vuln": "SQL injection"
            },
            {
                "code": "eval(user_input)",
                "language": "python", 
                "expected_vuln": "Code injection"
            },
            {
                "code": "document.innerHTML = user_data",
                "language": "javascript",
                "expected_vuln": "XSS"
            },
            {
                "code": "print('Hello world')",
                "language": "python",
                "expected_vuln": None  # Безопасный код
            }
        ]
        
        for i, test_case in enumerate(test_codes, 1):
            code = test_case["code"]
            lang = test_case["language"]
            expected = test_case["expected_vuln"]
            
            print(f"\n🧪 Тест {i}: {lang.upper()} код")
            print(f"Код: {code}")
            
            result = tool.execute(code=code, language=lang)
            
            if result["success"]:
                vulns = result["vulnerabilities_found"]
                risk = result["risk_level"]
                
                print(f"✅ Анализ завершен: {vulns} уязвимостей, риск: {risk}")
                
                if expected and vulns > 0:
                    print(f"🎯 Ожидаемая уязвимость найдена: {expected}")
                elif expected and vulns == 0:
                    print(f"⚠️  Ожидаемая уязвимость НЕ найдена: {expected}")
                elif not expected and vulns == 0:
                    print("🎯 Безопасный код правильно определен")
                
                if result["vulnerabilities"]:
                    for vuln in result["vulnerabilities"]:
                        print(f"  🚨 {vuln['description']} (риск: {vuln['severity']})")
            else:
                print(f"❌ Ошибка: {result['error']}")
                
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")

def test_tool_manager():
    """Тестирование ToolManager"""
    print("\n🛠️  ТЕСТ: ToolManager")
    print("=" * 40)
    
    try:
        # Создание менеджера
        manager = ToolManager()
        
        # Регистрация инструментов
        tools = [
            PasswordAnalyzerTool(),
            HashGeneratorTool(),
            VulnerabilityCheckerTool()
        ]
        
        for tool in tools:
            manager.register_tool(tool)
            print(f"✅ Зарегистрирован: {tool.name}")
        
        # Получение описания инструментов
        print(f"\n📋 Описание инструментов:")
        print(manager.get_tools_description())
        
        # Тестирование парсинга вызовов
        print(f"\n🔍 Тестирование парсинга вызовов:")
        
        test_responses = [
            '{"tool": "password_analyzer", "parameters": {"password": "test123"}}',
            '{"tool": "hash_generator", "parameters": {"text": "hello", "algorithm": "sha256"}}',
            'Анализирую пароль: {"tool": "password_analyzer", "parameters": {"password": "secure123"}}',
            '```json\n{"tool": "hash_generator", "parameters": {"text": "test"}}\n```'
        ]
        
        for i, response in enumerate(test_responses, 1):
            print(f"\nТест парсинга {i}:")
            print(f"Ответ: {response}")
            
            parsed = manager.parse_tool_call(response)
            if parsed:
                print(f"✅ Распознан вызов: {parsed['tool']} с параметрами {list(parsed['parameters'].keys())}")
            else:
                print("❌ Вызов не распознан")
        
        # Тестирование выполнения инструментов
        print(f"\n🚀 Тестирование выполнения через менеджер:")
        
        # Тест 1: Анализ пароля
        result = manager.execute_tool(
            "password_analyzer", 
            {"password": "TestPass123!"}
        )
        print(f"Анализ пароля: {'✅ Успех' if result.success else '❌ Ошибка'}")
        
        # Тест 2: Генерация хеша
        result = manager.execute_tool(
            "hash_generator",
            {"text": "Hello ToolManager", "algorithm": "sha256"}
        )
        print(f"Генерация хеша: {'✅ Успех' if result.success else '❌ Ошибка'}")
        if result.success:
            print(f"  Хеш: {result.result['hash'][:20]}...")
        
        # Тест 3: Несуществующий инструмент
        result = manager.execute_tool("nonexistent_tool", {})
        print(f"Несуществующий инструмент: {'❌ Правильная ошибка' if not result.success else '⚠️  Неожиданный успех'}")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

def test_web_search_tool():
    """Тестирование веб-поиска (если API ключ доступен)"""
    print("\n🌐 ТЕСТ: Веб-поиск (опционально)")
    print("=" * 40)
    
    try:
        tool = WebSearchTool()
        
        print(f"Имя инструмента: {tool.name}")
        print(f"Описание: {tool.description}")
        
        # Простой тестовый поиск
        result = tool.execute(query="Курс доллара", num_results=3)
        
        if result["success"]:
            print("✅ Поиск выполнен успешно")
            print(f"📊 Найдено результатов: {result['total_found']}")
            
            for i, res in enumerate(result["results"][:2], 1):
                print(f"\n{i}. {res['title']}")
                print(f"   {res['snippet'][:100]}...")
        else:
            print(f"❌ Поиск не удался: {result['error']}")
            print("💡 Убедитесь, что SERPER_API_KEY настроен в .env")
        
    except Exception as e:
        print(f"❌ Веб-поиск недоступен: {e}")

def main():
    """Запуск всех тестов"""
    print("🧪 ТЕСТИРОВАНИЕ ИНСТРУМЕНТОВ")
    print("=" * 50)
    
    # Тестируем каждый инструмент отдельно
    test_password_analyzer()
    test_hash_generator()
    test_vulnerability_checker()

    # Тестируем ToolManager
    test_tool_manager()
    
    # Тестируем веб-поиск (опционально)
    test_web_search_tool()
    
    print("\n🏁 Все тесты завершены!")
    print("=" * 50)


if __name__ == "__main__":
    main()
