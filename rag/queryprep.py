# -*- coding: utf-8 -*-
# rag/queryprep.py
import re
import json
import os
import logging
from typing import Optional, List, Dict, Any
from LLMs.factory import get_llm_client

class QueryResult:
    """Результат обработки запроса"""
    def __init__(self, language: str, rewritten: Optional[str] = None, entities: List[str] = None):
        self.language = language
        self.rewritten = rewritten
        self.entities = entities or []

class QueryPreprocessor:
    def __init__(self):
        self.llm_client = get_llm_client("gigachat")
        self.template = self._load_template()
        self.logger = logging.getLogger(__name__)
    
    def _load_template(self) -> Dict[str, Any]:
        """Загружает шаблон промпта из JSON файла"""
        template_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "prompts", 
            "templates", 
            "queryprep.json"
        )
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Ошибка загрузки шаблона queryprep: {e}")
            return {"messages": []}
        
    def _detect_language_simple(self, query: str) -> str:
        """Простое определение языка по символам"""
        cyrillic_chars = len(re.findall(r'[а-яё]', query.lower()))
        latin_chars = len(re.findall(r'[a-z]', query.lower()))
        
        if cyrillic_chars > latin_chars:
            return "ru"
        return "en"
    
    def _extract_entities_regex(self, query: str) -> List[str]:
        """Извлечение сущностей с помощью регулярных выражений"""
        entities = []
        
        # IP адреса
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        entities.extend(re.findall(ip_pattern, query))
        
        # CVE номера
        cve_pattern = r'CVE-\d{4}-\d{4,7}'
        entities.extend(re.findall(cve_pattern, query, re.IGNORECASE))
        
        # Домены (простая проверка)
        domain_pattern = r'\b[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+\b'
        potential_domains = re.findall(domain_pattern, query)
        entities.extend([match[0] + match[1] if match[1] else match[0] for match in potential_domains])
        
        # MD5/SHA хеши (32 или 64 символа)
        hash_pattern = r'\b[a-fA-F0-9]{32}\b|\b[a-fA-F0-9]{64}\b'
        entities.extend(re.findall(hash_pattern, query))
        
        return list(set(entities))  # Убираем дубликаты
    
    def _rewrite_query_with_llm(self, query: str, language: str, entities: List[str]) -> Optional[str]:
        """Переписывание запроса с помощью LLM используя шаблон"""
        try:
            # Получаем промпты из шаблона
            messages = self.template.get("messages", [])
            if len(messages) < 2:
                return None
                
            system_prompt = messages[0]["content"]
            user_template = messages[1]["content"]
            
            # Подставляем переменные
            entities_str = ', '.join(entities) if entities else 'нет'
            user_prompt = user_template.replace("{{raw_query}}", query).replace("{{entities}}", entities_str)
            
            rewritten = self.llm_client.chat_one(user_prompt, system_prompt)
            
            # Логируем результат обработки запроса
            self.logger.info(f"Query rewriting - Original: '{query}' | Enhanced: '{rewritten}'")
            self.logger.info(f"Response length: {len(rewritten)} chars (original: {len(query)} chars)")
            
            # Проверка на явные ошибки (не на длину - для RAG длинные запросы полезны)
            if (not rewritten or 
                len(rewritten) > 1000 or
                "не могу" in rewritten.lower() or
                "извините" in rewritten.lower() or
                "не понимаю" in rewritten.lower()):
                self.logger.warning("Query rewrite response rejected by validation")
                return None
                
            return rewritten.strip()
        except Exception as e:
            self.logger.error(f"Ошибка при переписывании запроса: {e}")
            return None
    
    def run(self, raw_query: str) -> QueryResult:
        """Основной метод обработки запроса"""
        self.logger.info(f"Starting query preprocessing for: '{raw_query}'")
        
        # 1. Определяем язык
        language = self._detect_language_simple(raw_query)
        self.logger.info(f"Detected language: {language}")
        
        # 2. Извлекаем сущности
        entities = self._extract_entities_regex(raw_query)
        self.logger.info(f"Extracted entities: {entities}")
        
        # 3. Переписываем запрос с помощью LLM
        rewritten = None
        if len(raw_query.strip()) > 5:  # Только для содержательных запросов
            rewritten = self._rewrite_query_with_llm(raw_query, language, entities)
        else:
            self.logger.info("Skipping query rewriting - query too short")
        
        self.logger.info("Query preprocessing completed")
        return QueryResult(
            language=language,
            rewritten=rewritten,
            entities=entities
        )