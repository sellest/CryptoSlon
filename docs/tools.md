# Руководство по созданию и использованию инструментов

## Обзор архитектуры инструментов

Система инструментов построена по тому же принципу абстракция → реализация → менеджер:
- **BaseTool** - абстрактный базовый класс для всех инструментов
- **SecurityTool, SearchTool, etc.** - конкретные реализации инструментов
- **ToolManager** - менеджер для регистрации, поиска и выполнения инструментов

Работающие тесты с тулзами можно найти в [test_tools](../tests/test_tools.py).

## BaseTool - базовая абстракция

[BaseTool](../agents/base_tool.py) определяет контракт, который должен выполнять любой инструмент:

### Обязательные свойства:
```python
@property
@abstractmethod
def name(self) -> str:
    """Уникальное имя инструмента (используется для вызова)"""
    pass

@property
@abstractmethod  
def description(self) -> str:
    """Описание инструмента для LLM (что он делает)"""
    pass

@property
@abstractmethod
def parameters(self) -> Dict[str, Any]:
    """Схема параметров в формате JSON Schema"""
    pass
```

### Обязательный метод:
```python
@abstractmethod
def execute(self, **kwargs) -> Any:
    """Выполнение инструмента с переданными параметрами"""
    pass
```

## Создание собственного инструмента

### Шаг 1: Наследование от BaseTool

```python
from agents.base_tool import BaseTool
from typing import Dict, Any
import logging

class MyCustomTool(BaseTool):
    """Описание вашего инструмента"""
    
    @property
    def name(self) -> str:
        return "my_custom_tool"  # Имя должно быть уникальным
    
    @property
    def description(self) -> str:
        return "Описание того, что делает ваш инструмент"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "input_text": {
                "type": "string",
                "description": "Текст для обработки"
            },
            "mode": {
                "type": "string", 
                "description": "Режим обработки (fast/detailed)",
                "default": "fast"
            }
        }
    
    def execute(self, input_text: str, mode: str = "fast") -> Dict[str, Any]:
        """Выполнение инструмента"""
        logger = logging.getLogger(f"tool.{self.name}")
        logger.info(f"Tool {self.name} called with text length: {len(input_text)}")
        
        try:
            # Ваша логика обработки
            if mode == "fast":
                result = self._fast_processing(input_text)
            else:
                result = self._detailed_processing(input_text)
            
            return {
                "success": True,
                "result": result,
                "mode_used": mode
            }
            
        except Exception as e:
            logger.error(f"Tool {self.name} failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _fast_processing(self, text: str) -> str:
        # Быстрая обработка
        return f"Fast: {text.upper()}"
    
    def _detailed_processing(self, text: str) -> str:
        # Детальная обработка
        return f"Detailed: {text.lower()}"
```

### Шаг 2: Рекомендации по параметрам

Параметры должны следовать JSON Schema формату:

```python
@property
def parameters(self) -> Dict[str, Any]:
    return {
        "required_param": {
            "type": "string",  # string, integer, boolean, array, object
            "description": "Обязательный параметр"
        },
        "optional_param": {
            "type": "integer",
            "description": "Необязательный параметр",
            "default": 5,
            "minimum": 1,
            "maximum": 100
        },
        "choice_param": {
            "type": "string",
            "description": "Параметр с ограниченным выбором",
            "enum": ["option1", "option2", "option3"]
        }
    }
```

### Шаг 3: Обработка ошибок и логирование

```python
def execute(self, **kwargs) -> Dict[str, Any]:
    logger = logging.getLogger(f"tool.{self.name}")
    logger.info(f"Tool {self.name} called with params: {list(kwargs.keys())}")
    
    try:
        # Валидация параметров
        required_param = kwargs.get("required_param")
        if not required_param:
            raise ValueError("required_param is missing")
        
        # Основная логика
        result = self._process_data(required_param)
        
        logger.info(f"Tool {self.name} completed successfully")
        return {
            "success": True,
            "result": result
        }
        
    except ValueError as e:
        # Ошибки валидации параметров
        logger.warning(f"Tool {self.name} validation error: {e}")
        return {
            "success": False,
            "error": f"Некорректные параметры: {str(e)}"
        }
    except Exception as e:
        # Все остальные ошибки
        logger.error(f"Tool {self.name} execution error: {e}")
        return {
            "success": False,
            "error": f"Ошибка выполнения: {str(e)}"
        }
```

## Примеры инструментов

### PasswordAnalyzerTool - Анализ паролей

[Полный код](../agents/tools/security_tool.py)

```python
class PasswordAnalyzerTool(BaseTool):
    @property
    def name(self) -> str:
        return "password_analyzer"
    
    @property 
    def description(self) -> str:
        return "Анализ надежности пароля и рекомендации по его улучшению"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "password": {
                "type": "string",
                "description": "Пароль для анализа (не логируется в целях безопасности)"
            }
        }
    
    def execute(self, password: str) -> Dict[str, Any]:
        # Использует библиотеку zxcvbn для анализа
        result = zxcvbn.zxcvbn(password)
        # Возвращает подробный анализ безопасности
        return {"success": True, "analysis": formatted_analysis}
```

### HashGeneratorTool - Генерация хешей

```python
class HashGeneratorTool(BaseTool):
    @property
    def name(self) -> str:
        return "hash_generator"
    
    @property
    def description(self) -> str:
        return "Генерация безопасных хешей (SHA-256, MD5, etc.) для текста"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "text": {
                "type": "string", 
                "description": "Текст для хеширования"
            },
            "algorithm": {
                "type": "string",
                "description": "Алгоритм хеширования",
                "enum": ["sha256", "sha1", "md5"],
                "default": "sha256"
            }
        }
    
    def execute(self, text: str, algorithm: str = "sha256") -> Dict[str, Any]:
        # Генерирует хеш с использованием hashlib
        hash_obj = getattr(hashlib, algorithm)(text.encode('utf-8'))
        return {
            "success": True,
            "hash": hash_obj.hexdigest(),
            "algorithm": algorithm.upper()
        }
```

## ToolManager - Менеджер инструментов

[ToolManager](../agents/tool_manager.py) управляет регистрацией и выполнением инструментов:

### Основные методы:

```python
class ToolManager:
    def register_tool(self, tool: BaseTool):
        """Регистрация инструмента"""
        
    def get_tools_description(self) -> str:
        """Получение описания всех доступных инструментов"""
        
    def parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """Парсинг вызова инструмента из ответа LLM"""
        
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """Выполнение инструмента по имени"""
```

### ToolResult - Результат выполнения

```python
@dataclass
class ToolResult:
    tool_name: str                    # Имя инструмента
    parameters: Dict[str, Any]        # Переданные параметры
    result: Optional[Any] = None      # Результат (если success=True)
    success: bool = False             # Успешность выполнения
    error_message: Optional[str] = None  # Сообщение об ошибке
```

## Использование ToolManager

### Создание и регистрация инструментов:

```python
from agents.tool_manager import ToolManager
from agents.tools.security_tool import PasswordAnalyzerTool, HashGeneratorTool

# Создание менеджера
tool_manager = ToolManager()

# Регистрация инструментов
tool_manager.register_tool(PasswordAnalyzerTool())
tool_manager.register_tool(HashGeneratorTool())
tool_manager.register_tool(MyCustomTool())

# Получение описания для LLM
description = tool_manager.get_tools_description()
print(description)
# Вывод:
# - password_analyzer: Анализ надежности пароля
# - hash_generator: Генерация безопасных хешей  
# - my_custom_tool: Описание вашего инструмента
```

### Парсинг и выполнение вызовов:

```python
# Ответ от LLM с вызовом инструмента
llm_response = '{"tool": "password_analyzer", "parameters": {"password": "mypass123"}}'

# Парсинг вызова
tool_call = tool_manager.parse_tool_call(llm_response)
if tool_call:
    print(f"Инструмент: {tool_call['tool']}")
    print(f"Параметры: {tool_call['parameters']}")
    
    # Выполнение инструмента
    result = tool_manager.execute_tool(
        tool_call['tool'], 
        tool_call['parameters']
    )
    
    if result.success:
        print(f"Результат: {result.result}")
    else:
        print(f"Ошибка: {result.error_message}")
```

### Прямое выполнение:

```python
# Прямое выполнение инструмента
result = tool_manager.execute_tool(
    "hash_generator", 
    {"text": "Hello World", "algorithm": "sha256"}
)

print(f"Успех: {result.success}")
print(f"Результат: {result.result}")
```

## Интеграция с агентами

Инструменты автоматически интегрируются с агентами через ToolManager:

```python
from agents.base_agent import BaseAgent

# Создание агента
agent = BaseAgent("SecurityBot")

# Регистрация инструментов
agent.register_tool(PasswordAnalyzerTool())
agent.register_tool(HashGeneratorTool())

# Агент автоматически получает доступ к инструментам
response = agent.process_request("Проанализируй пароль 'mypass123'")
# Агент автоматически вызовет password_analyzer
```
