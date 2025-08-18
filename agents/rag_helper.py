import logging
from typing import Optional
from VectorDB.base_chroma_db import BaseChromaDB
from rag.queryprep import QueryPreprocessor

class RAGHelper:
    """Simple RAG functionality for agents"""
    
    def __init__(self, vector_db_collection: str, vector_model: str = "intfloat/multilingual-e5-base"):
        self.vector_db = BaseChromaDB(vector_db_collection, vector_model)
        self.query_prep = QueryPreprocessor()
        self.logger = logging.getLogger("rag_helper")
    
    def search_knowledge_base(self, query: str, top_k: int = 3) -> Optional[str]:
        """Search vector database for relevant context"""
        try:
            # Use query preprocessing
            prep_result = self.query_prep.run(query)
            search_query = prep_result.rewritten or query
            
            # Search vector database
            results = self.vector_db.search(search_query, top_k=top_k)
            
            if results:
                context_parts = []
                for result in results:
                    if result['distance'] < 0.8:  # Only relevant results
                        filename = result['metadata'].get('filename', 'Unknown')
                        content = result['document']
                        context_parts.append(f"[Source: {filename}] {content}")
                
                if context_parts:
                    return "\n\n".join(context_parts)
            
        except Exception as e:
            self.logger.error(f"Knowledge base search failed: {e}")
        
        return None
