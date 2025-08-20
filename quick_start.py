# -*- coding: utf-8 -*-
"""
Быстрая демонстрация агента - минимальный код для хакатона
"""

import sys
import os
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from agents.base_agent import BaseAgent
from agents.tools.security_tool import PasswordAnalyzerTool, HashGeneratorTool
from agents.tools.search_tool import WebSearchTool

# Уровни логирования
logging.basicConfig(level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.ERROR)

def quick_start():
    """Быстрая демонстрация основных возможностей"""
    
    print("🚀 БЫСТРАЯ ДЕМОНСТРАЦИЯ AI-АГЕНТА")
    print("="*40)
    
    # Setup agent
    agent = BaseAgent("QuickDemo", llm_provider="gigachat", max_iterations=2)
    agent.register_tool(PasswordAnalyzerTool())
    agent.register_tool(WebSearchTool())
    
    print("✅ Агент настроен с инструментами безопасности")
    
    # Predefined test cases
    test_cases = [
        "Проанализируй пароль 'password123'",
        "Какой сейчас курс доллара?"
    ]
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n--- ТЕСТ {i} ---")
        print(f"Запрос: {query}")
        print("Ответ агента:")
        
        try:
            response = agent.process_request(query)
            print(response)
        except Exception as e:
            print(f"Ошибка: {e}")
    
    print(f"\n🏁 Конец!")


if __name__ == "__main__":
    quick_start()
