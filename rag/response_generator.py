# -*- coding: utf-8 -*-
# rag/response_generator.py - Response generation component

import logging
from typing import Dict, List, Any
from LLMs.factory import get_llm_client
from rag.queryprep import QueryResult


class ResponseGenerator:
    """
    Handles LLM-based response generation with context
    """
    
    def __init__(self, llm_provider: str = "gigachat"):
        self.llm_client = get_llm_client(llm_provider)
        self.logger = logging.getLogger(__name__)
    
    def _build_system_prompt(self, domain: str = "cybersecurity") -> str:
        """Build system prompt based on domain"""
        if domain == "cybersecurity":
            return """Ты — эксперт по кибербезопасности. Отвечай на вопросы, используя предоставленный контекст.

ПРАВИЛА:
1. Используй ТОЛЬКО информацию из предоставленного контекста
2. Если в контексте нет достаточной информации, честно скажи об этом
3. Всегда указывай источники в формате [Источник N]
4. Отвечай на русском языке, если вопрос на русском
5. Будь точным и конкретным
6. Для технических вопросов приводи примеры и детали
7. При обнаружении угроз указывай меры противодействия"""
        
        # Default general domain
        return """Ты — помощник-эксперт. Отвечай на вопросы, используя предоставленный контекст.

ПРАВИЛА:
1. Используй ТОЛЬКО информацию из предоставленного контекста
2. Если в контексте нет достаточной информации, честно скажи об этом
3. Всегда указывай источники в формате [Источник N]
4. Отвечай на том же языке, что и вопрос
5. Будь точным и конкретным"""
    
    def _build_user_prompt(
        self, 
        query: str, 
        context: str, 
        query_result: QueryResult,
        additional_context: str = None
    ) -> str:
        """Build user prompt with all context information"""
        
        prompt_parts = []
        
        # Add additional context if provided
        if additional_context:
            prompt_parts.append(f"ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ:\n{additional_context}")
        
        # Main context from search results
        prompt_parts.append(f"КОНТЕКСТ:\n{context}")
        
        # Extracted entities
        entities_str = ', '.join(query_result.entities) if query_result.entities else 'нет'
        prompt_parts.append(f"ИЗВЛЕЧЕННЫЕ СУЩНОСТИ: {entities_str}")
        
        # Original question
        prompt_parts.append(f"ВОПРОС: {query}")
        
        prompt_parts.append("Ответь на вопрос, используя информацию из контекста. Обязательно укажи источники.")
        
        return "\n\n".join(prompt_parts)
    
    def generate_response(
        self, 
        query: str, 
        context: str, 
        query_result: QueryResult,
        domain: str = "cybersecurity",
        additional_context: str = None
    ) -> str:
        """
        Generate response using LLM with context
        
        Args:
            query: Original user query
            context: Built context from search results  
            query_result: Query preprocessing results
            domain: Domain for system prompt specialization
            additional_context: Extra context to include
            
        Returns:
            Generated response
        """
        try:
            system_prompt = self._build_system_prompt(domain)
            user_prompt = self._build_user_prompt(query, context, query_result, additional_context)
            
            self.logger.debug(f"Generating response with context length: {len(context)}")
            
            response = self.llm_client.chat_one(user_prompt, system_prompt)
            
            self.logger.info(f"Generated response: {len(response)} characters")
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            return f"Извините, произошла ошибка при генерации ответа: {e}"
    
    def generate_summary(self, documents: List[str], topic: str = None) -> str:
        """Generate summary of multiple documents"""
        try:
            combined_text = "\n\n".join(documents)
            
            system_prompt = "Ты — эксперт по анализу и суммаризации. Создай краткое резюме предоставленных документов."
            
            topic_part = f" по теме '{topic}'" if topic else ""
            user_prompt = f"Создай краткое резюме следующих документов{topic_part}:\n\n{combined_text}"
            
            summary = self.llm_client.chat_one(user_prompt, system_prompt)
            return summary.strip()
            
        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}")
            return f"Ошибка при создании резюме: {e}"

