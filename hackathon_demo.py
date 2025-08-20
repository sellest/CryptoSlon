# -*- coding: utf-8 -*-
"""
Демонстрационный скрипт для хакатона - агент с предопределенными сценариями
Запускается автономно без пользовательского ввода
"""

import logging
import sys
import os
import time

# Add agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from agents.base_agent import BaseAgent
from agents.tools.search_tool import WebSearchTool
from agents.tools.security_tool import PasswordAnalyzerTool, HashGeneratorTool, VulnerabilityCheckerTool

# Set up logging - less verbose for demo
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(name)s - %(message)s')

# Disable noisy loggers for clean demo output
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

class HackathonDemo:
    """Демонстрационный класс для хакатона"""
    
    def __init__(self):
        self.agent = None
        self.demo_scenarios = []
        
    def setup_agent(self):
        """Настройка агента для демо"""
        print("🤖 Инициализация кибербезопасного AI-агента...")
        
        # Create cybersecurity-focused agent
        self.agent = BaseAgent(
            agent_name="CyberSecurityDemo",
            llm_provider="gigachat",
            max_iterations=3  # Reduced for faster demo
        )
        
        # Register security tools
        tools_registered = 0
        
        security_tools = [
            PasswordAnalyzerTool(),
            HashGeneratorTool(),
            VulnerabilityCheckerTool(),
            WebSearchTool()
        ]
        
        for tool in security_tools:
            self.agent.register_tool(tool)
            tools_registered += 1

        print(f"✅ Агент настроен с {tools_registered} инструментами")
        
    def define_scenarios(self):
        """Определение сценариев для демонстрации"""
        self.demo_scenarios = [
            {
                "title": "Анализ безопасности пароля",
                "description": "Демонстрация анализа надежности пароля",
                "query": "Проанализируй безопасность пароля 'admin123' и дай рекомендации",
                "expected_tool": "password_analyzer"
            },
            {
                "title": "Генерация криптографического хеша",
                "description": "Создание безопасного хеша для данных",
                "query": "Создай SHA-256 хеш для строки 'SecretData2024'",
                "expected_tool": "hash_generator"
            },
            {
                "title": "Поиск уязвимостей в коде",
                "description": "Анализ кода на предмет уязвимостей безопасности",
                "query": "Проверь этот Python код на уязвимости: cursor.execute('SELECT * FROM users WHERE id = ' + user_id)",
                "expected_tool": "vulnerability_checker"
            },
            {
                "title": "Анализ сложного пароля",
                "description": "Проверка более сложного пароля",
                "query": "Оцени надежность пароля 'Tr0ub4dor&3!'",
                "expected_tool": "password_analyzer"
            },
            {
                "title": "Проверка JavaScript на XSS",
                "description": "Анализ JavaScript кода на XSS уязвимости",
                "query": "Найди уязвимости в этом JavaScript коде: document.innerHTML = userInput;",
                "expected_tool": "vulnerability_checker"
            }
        ]
        
        print(f"📋 Подготовлено {len(self.demo_scenarios)} демо-сценариев")
    
    def run_scenario(self, scenario, scenario_num, total_scenarios):
        """Запуск одного сценария"""
        print(f"\n{'='*60}")
        print(f"🎯 СЦЕНАРИЙ {scenario_num}/{total_scenarios}: {scenario['title']}")
        print(f"{'='*60}")
        print(f"📝 Описание: {scenario['description']}")
        print(f"❓ Запрос: {scenario['query']}")
        print(f"🛠️  Ожидаемый инструмент: {scenario['expected_tool']}")
        
        print(f"\n🤔 Агент обрабатывает запрос...")
        
        try:
            # Measure response time
            start_time = time.time()
            response = self.agent.process_request(scenario['query'])
            end_time = time.time()
            
            response_time = round(end_time - start_time, 2)
            
            print(f"\n✅ Ответ получен за {response_time}с:")
            print(f"{'='*50}")
            print(response)
            print(f"{'='*50}")
            
            return True, response_time
            
        except Exception as e:
            print(f"\n❌ Ошибка при выполнении сценария: {e}")
            return False, 0
    
    def run_all_scenarios(self):
        """Запуск всех сценариев подряд"""
        print(f"\n🚀 ЗАПУСК ДЕМОНСТРАЦИИ")
        print(f"Всего сценариев: {len(self.demo_scenarios)}")
        
        successful = 0
        total_time = 0
        
        for i, scenario in enumerate(self.demo_scenarios, 1):
            success, response_time = self.run_scenario(scenario, i, len(self.demo_scenarios))
            
            if success:
                successful += 1
                total_time += response_time
            
            # Small delay between scenarios for better readability
            if i < len(self.demo_scenarios):
                print(f"\n⏳ Пауза перед следующим сценарием...")
                time.sleep(2)
        
        # Summary
        print(f"\n🏁 ИТОГИ ДЕМОНСТРАЦИИ")
        print(f"{'='*40}")
        print(f"✅ Успешных сценариев: {successful}/{len(self.demo_scenarios)}")
        print(f"⏱️  Общее время: {round(total_time, 2)}с")
        print(f"⚡ Среднее время ответа: {round(total_time/max(successful, 1), 2)}с")
        
        if successful == len(self.demo_scenarios):
            print(f"🎉 Все сценарии выполнены успешно!")
        else:
            print(f"⚠️  {len(self.demo_scenarios) - successful} сценариев завершились с ошибками")
    
    def run_interactive_selection(self):
        """Интерактивный выбор сценариев"""
        print(f"\n📋 ДОСТУПНЫЕ СЦЕНАРИИ:")
        for i, scenario in enumerate(self.demo_scenarios, 1):
            print(f"  {i}. {scenario['title']}")
        
        print(f"  0. Запустить все сценарии")
        
        try:
            choice = input(f"\nВыберите сценарий (0-{len(self.demo_scenarios)}): ").strip()
            
            if choice == "0":
                self.run_all_scenarios()
            elif choice.isdigit() and 1 <= int(choice) <= len(self.demo_scenarios):
                scenario_idx = int(choice) - 1
                scenario = self.demo_scenarios[scenario_idx]
                self.run_scenario(scenario, int(choice), len(self.demo_scenarios))
            else:
                print("❌ Неверный выбор")
        except KeyboardInterrupt:
            print(f"\n👋 Демонстрация прервана пользователем")
    
    def run_custom_scenario(self, custom_query):
        """Запуск пользовательского сценария"""
        print(f"\n🎯 ПОЛЬЗОВАТЕЛЬСКИЙ СЦЕНАРИЙ")
        print(f"{'='*40}")
        print(f"❓ Запрос: {custom_query}")
        
        try:
            start_time = time.time()
            response = self.agent.process_request(custom_query)
            end_time = time.time()
            
            response_time = round(end_time - start_time, 2)
            
            print(f"\n✅ Ответ получен за {response_time}с:")
            print(f"{'='*50}")
            print(response)
            print(f"{'='*50}")
            
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")

def main():
    """Main demo function"""
    print("🛡️  КИБЕРБЕЗОПАСНЫЙ AI-АГЕНТ - ДЕМОНСТРАЦИЯ ДЛЯ ХАКАТОНА")
    print("="*60)
    
    try:
        # Initialize demo
        demo = HackathonDemo()
        demo.setup_agent()
        demo.define_scenarios()
        
        # Check command line arguments for automatic mode
        if len(sys.argv) > 1:
            if sys.argv[1] == "--auto":
                print(f"\n🤖 АВТОМАТИЧЕСКИЙ РЕЖИМ")
                demo.run_all_scenarios()
            elif sys.argv[1] == "--scenario" and len(sys.argv) > 2:
                scenario_num = int(sys.argv[2])
                if 1 <= scenario_num <= len(demo.demo_scenarios):
                    scenario = demo.demo_scenarios[scenario_num - 1]
                    demo.run_scenario(scenario, scenario_num, len(demo.demo_scenarios))
                else:
                    print(f"❌ Неверный номер сценария: {scenario_num}")
            elif sys.argv[1] == "--query" and len(sys.argv) > 2:
                custom_query = " ".join(sys.argv[2:])
                demo.run_custom_scenario(custom_query)
            else:
                print(f"❌ Неизвестный аргумент: {sys.argv[1]}")
                print(f"Доступные режимы:")
                print(f"  --auto                    # Запуск всех сценариев")
                print(f"  --scenario <номер>        # Запуск конкретного сценария")
                print(f"  --query <ваш запрос>      # Пользовательский запрос")
        else:
            # Interactive mode
            demo.run_interactive_selection()
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()