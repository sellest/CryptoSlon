# -*- coding: utf-8 -*-
# rag/pipeline.py - Complete RAG Pipeline with QueryProcessor integration

import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from VectorDB.base_chroma_db import BaseChromaDB
from rag.queryprep import QueryPreprocessor, QueryResult
from rag.response_generator import ResponseGenerator
from rag.context_builder import ContextBuilder


@dataclass
class RAGResult:
    """Result from RAG pipeline execution"""
    answer: str
    sources: List[Dict[str, Any]]
    query_info: Dict[str, Any]
    processing_time: float
    # success: Optional[bool]
    error_message: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None


class RAGPipeline:
    """
    Complete RAG pipeline that combines query preprocessing with vector search and generation.
    
    Pipeline stages:
    1. Query preprocessing (language detection, entity extraction, query rewriting)
    2. Vector database search with processed query
    3. Context building and filtering
    4. Response generation using LLM
    """
    
    def __init__(
        self,
        vector_db_collection: str,
        llm_provider: str = "gigachat",
        vector_model: str = "intfloat/multilingual-e5-base",
        max_context_length: int = 4000,
        min_relevance_score: float = 0.7,
        max_sources: int = 5,
        enable_debug: bool = False,
        chroma_db_path: str = "../chroma_db",
        query_template: str = "queryprep"
    ):
        # Core components - explicitly pass the ChromaDB path
        self.vector_db = BaseChromaDB(vector_db_collection, vector_model, chroma_db_path)
        self.query_processor = QueryPreprocessor(template_name=query_template)
        self.response_generator = ResponseGenerator(llm_provider)
        self.context_builder = ContextBuilder(max_context_length)
        
        # Configuration
        self.min_relevance_score = min_relevance_score
        self.max_sources = max_sources
        self.enable_debug = enable_debug
        self.chroma_db_path = chroma_db_path
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"RAG Pipeline initialized with collection '{vector_db_collection}' at '{chroma_db_path}' using query template '{query_template}'")
    
    def _search_vector_db(self, query_result: QueryResult, original_query: str) -> List[Dict[str, Any]]:
        """
        Search vector database using processed query with fallback to original
        
        Args:
            query_result: Result from query preprocessing
            original_query: Original user query as fallback
            
        Returns:
            List of search results with relevance filtering
        """
        search_queries = []
        
        # Primary search query (rewritten if available)
        if query_result.rewritten:
            search_queries.append(("rewritten", query_result.rewritten))
        
        # Fallback to original query
        search_queries.append(("original", original_query))
        
        # Additional searches with entities if extracted
        if query_result.entities:
            entity_query = f"{original_query} {' '.join(query_result.entities)}"
            search_queries.append(("entity_enhanced", entity_query))
        
        all_results = []
        seen_documents = set()
        
        for search_type, query in search_queries:
            try:
                results = self.vector_db.search(query, top_k=self.max_sources * 2)

                for result in results:
                    # Calculate relevance score
                    relevance = 1 - result['distance']
                    
                    # Filter by relevance threshold
                    if relevance < self.min_relevance_score:
                        continue
                    
                    # Avoid duplicate documents
                    doc_hash = hash(result['document'][:100])
                    if doc_hash in seen_documents:
                        continue
                    seen_documents.add(doc_hash)
                    
                    # Enhance result with additional info
                    enhanced_result = {
                        'document': result['document'],
                        'metadata': result['metadata'],
                        'relevance_score': relevance,
                        'search_type': search_type,
                        'search_query': query
                    }
                    
                    all_results.append(enhanced_result)
                
                self.logger.debug(f"Search '{search_type}' found {len(results)} results")
                
            except Exception as e:
                self.logger.error(f"Search '{search_type}' failed: {e}")
        
        # Sort by relevance and limit results
        all_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return all_results[:self.max_sources]
    
    def run(
        self, 
        query: str, 
        system_context: Optional[str] = None,
        include_debug: bool = None
    ) -> RAGResult:
        """
        Execute complete RAG pipeline
        
        Args:
            query: User query
            system_context: Additional system context (optional)
            include_debug: Override debug setting for this run
            
        Returns:
            RAGResult with answer, sources, and metadata
        """
        start_time = time.time()
        debug_info = {} if (include_debug or self.enable_debug) else None
        
        try:
            self.logger.info(f"Starting RAG pipeline for query: '{query}'")
            
            # Stage 1: Query preprocessing
            self.logger.info("Stage 1: Query preprocessing")
            query_result = self.query_processor.run(query)
            
            if debug_info is not None:
                debug_info['query_processing'] = {
                    'original_query': query,
                    'detected_language': query_result.language,
                    'rewritten_query': query_result.rewritten,
                    'extracted_entities': query_result.entities
                }
            
            # Stage 2: Vector database search
            self.logger.info("Stage 2: Vector database search")
            search_results = self._search_vector_db(query_result, query)
            
            if not search_results:
                return RAGResult(
                    answer="Извините, я не смог найти релевантную информацию в базе знаний для ответа на ваш вопрос.",
                    sources=[],
                    query_info={
                        'original_query': query,
                        'language': query_result.language,
                        'entities': query_result.entities
                    },
                    processing_time=time.time() - start_time,
                    success=False,
                    error_message="No relevant results found",
                    debug_info=debug_info
                )
            
            if debug_info is not None:
                debug_info['search_results'] = [
                    {
                        'relevance': r['relevance_score'],
                        'search_type': r['search_type'],
                        'filename': r['metadata'].get('filename', 'Unknown'),
                        'snippet': r['document'][:100] + "..."
                    }
                    for r in search_results[:3]
                ]
            
            # Stage 3: Context building
            self.logger.info("Stage 3: Context building")
            context, sources_info = self.context_builder.build_context(search_results)
            
            # Stage 4: Response generation
            self.logger.info("Stage 4: Response generation")
            answer = self.response_generator.generate_response(
                query, context, query_result, 
                domain="cybersecurity",
                additional_context=system_context
            )
            
            processing_time = time.time() - start_time
            self.logger.info(f"RAG pipeline completed in {processing_time:.2f}s")
            
            if debug_info is not None:
                debug_info['context_length'] = len(context)
                debug_info['sources_count'] = len(sources_info)
                debug_info['processing_time'] = processing_time
            
            return RAGResult(
                answer=answer,
                sources=sources_info,
                query_info={
                    'original_query': query,
                    'processed_query': query_result.rewritten,
                    'language': query_result.language,
                    'entities': query_result.entities
                },
                processing_time=processing_time,
                debug_info=debug_info
            )
            
        except Exception as e:
            error_message = f"RAG pipeline error: {e}"
            self.logger.error(error_message)
            
            return RAGResult(
                answer=f"Извините, произошла ошибка при обработке вашего запроса: {e}",
                sources=[],
                query_info={'original_query': query},
                processing_time=time.time() - start_time,
                success=False,
                error_message=error_message,
                debug_info=debug_info
            )
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the vector database collection"""
        return self.vector_db.get_collection_info()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check of RAG pipeline components"""
        health_result = {
            'vector_db': {'status': False, 'details': ''},
            'query_processor': {'status': False, 'details': ''},
            'response_generator': {'status': False, 'details': ''},
            'context_builder': {'status': True, 'details': 'No external dependencies'},
            'overall': False
        }
        
        # Test vector database
        try:
            db_info = self.vector_db.get_collection_info()
            doc_count = db_info['total_documents']
            if doc_count > 0:
                health_result['vector_db']['status'] = True
                health_result['vector_db']['details'] = f"Collection '{db_info['collection_name']}' has {doc_count} documents at '{self.chroma_db_path}'"
            else:
                health_result['vector_db']['details'] = f"Collection '{db_info['collection_name']}' exists but is empty at '{self.chroma_db_path}'"
        except Exception as e:
            health_result['vector_db']['details'] = f"Failed to access collection: {e}"
            self.logger.error(f"Vector DB health check failed: {e}")
        
        # Test query processor
        try:
            test_result = self.query_processor.run("test query")
            if test_result.language in ['ru', 'en']:
                health_result['query_processor']['status'] = True
                health_result['query_processor']['details'] = f"Language detection working (detected: {test_result.language})"
            else:
                health_result['query_processor']['details'] = f"Unexpected language result: {test_result.language}"
        except Exception as e:
            health_result['query_processor']['details'] = f"Query processing failed: {e}"
            self.logger.error(f"Query processor health check failed: {e}")
        
        # Test response generator
        try:
            test_response = self.response_generator.generate_response(
                "test", "test context", 
                QueryResult("en"), domain="general"
            )
            if len(test_response) > 0:
                health_result['response_generator']['status'] = True
                health_result['response_generator']['details'] = f"Response generation working ({len(test_response)} chars)"
            else:
                health_result['response_generator']['details'] = "Response generator returned empty response"
        except Exception as e:
            health_result['response_generator']['details'] = f"Response generation failed: {e}"
            self.logger.error(f"Response generator health check failed: {e}")
        
        # Overall health
        component_statuses = [health_result[comp]['status'] for comp in ['vector_db', 'query_processor', 'response_generator']]
        health_result['overall'] = all(component_statuses)
        
        return health_result


# Convenience function for quick RAG usage
def quick_rag_search(
    query: str, 
    collection_name: str = "test_knowledge", 
    query_template: str = "queryprep"
) -> str:
    """
    Quick RAG search function for simple use cases
    
    Args:
        query: User question
        collection_name: Vector DB collection name
        query_template: Template to use for query preprocessing
        
    Returns:
        Answer string
    """
    try:
        pipeline = RAGPipeline(collection_name, query_template=query_template)
        result = pipeline.run(query)
        return result.answer
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.WARNING)
    
    # Initialize pipeline
    rag = RAGPipeline(
        llm_provider="GigaChat-max",
        query_template="queryprep_tests",
        vector_db_collection="cybersecurity_pdfs",
        enable_debug=True,
        min_relevance_score=0.5
    )
    
    # Health check
    health = rag.health_check()
    print(f"Pipeline health: {health}")
    
    # # Test query
    # test_query = "Осґар Рустэмович KPI презы"
    #
    # result = rag.run(test_query)
    #
    # print(f"\nВопрос: {test_query}")
    # print(f"Ответ: {result.answer}")
    # print(f"Источники: {len(result.sources)}")
    # print(f"Время обработки: {result.processing_time:.2f}s")
    #
    # if result.debug_info:
    #     print(f"\nОтладочная информация:")
    #     for key, value in result.debug_info.items():
    #         print(f"  {key}: {value}")

    # Тестирование RAG-системы с запросами разного уровня
    queries = [
        {"q": "чей девиз «доверяй, но проверяй трижды»?", "a": "Найти факт с точной цитатой (Татьяна)."},
        {"q": "кто превращает хаос в проект с дедлайнами за вечер", "a": "Мария Александровна"},
        {"q": "персона, которая: любит UML, спорит об архитектуре и говорит «зависит от архитектуры»", "a": "Артур Евгеньевич"},
        {"q": "дай факты о том, кто не называет Agile методологией", "a": "Олег Андреевич («Agile — стиль танца»)"},
        {"q": "Who keeps a cactus as a “weekly talisman” and posts photos on Fridays?", "a": "Татьяна Олеговна"},
        {"q": "покажи табличные факты про Мария Александровна (Excel/тайминг)", "a": "Достать строку из табличного блока"},
        {"q": "суммаризируй все упоминания об Excel и назови всех людей, к кому это относится", "a": "Олег, Мария"},
        {"q": "верни по каждому человеку ровно один “самый уникальный” факт и объясни, почему он уникален", "a": "Дедупликация и ранжирование"},
        {"q": "сделай таблицу: Имя | 1 факт из “попугаев” | 1 факт из “удавов” | 1 факт из “таблицы”", "a": "Слияние разных источников"},
    ]

    for q in queries:
        result = rag.run(q['q'])

        print(f"\nВопрос: {q['q']}")
        print(f"Ответ: {result.answer}")
        print(f"Ожидаемый ответ: {q['a']}")
        print(f"Источники: {len(result.sources)}")
        print(f"Время обработки: {result.processing_time:.2f}s")
