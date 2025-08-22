# -*- coding: utf-8 -*-
# rag/context_builder.py - Context building and management

import logging
from typing import Dict, List, Any, Tuple, Optional


class ContextBuilder:
    """
    Handles context building from search results with intelligent formatting and length management
    """
    
    def __init__(self, max_context_length: int = 4000):
        self.max_context_length = max_context_length
        self.logger = logging.getLogger(__name__)
    
    def build_context(
        self, 
        search_results: List[Dict[str, Any]],
        include_metadata: bool = True,
        prioritize_relevance: bool = True
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Build context from search results with intelligent length control
        
        Args:
            search_results: Results from vector database search
            include_metadata: Whether to include metadata in context
            prioritize_relevance: Whether to prioritize high-relevance results
            
        Returns:
            Tuple of (context_string, sources_info)
        """
        if not search_results:
            return "", []
        
        # Sort by relevance if requested
        if prioritize_relevance:
            search_results = sorted(search_results, key=lambda x: x['relevance_score'], reverse=True)
        
        context_parts = []
        sources_info = []
        current_length = 0
        
        for i, result in enumerate(search_results, 1):
            document = result['document']
            metadata = result['metadata']
            
            # Prepare source info
            source_info = self._prepare_source_info(i, result, metadata)
            
            # Build document section
            doc_section = self._build_document_section(i, document, metadata, include_metadata)
            
            # Check if adding this document would exceed length limit
            if current_length + len(doc_section) > self.max_context_length:
                # Try to add truncated version
                remaining_space = self.max_context_length - current_length - 100  # Reserve space for truncation notice
                if remaining_space > 200:  # Only truncate if we have reasonable space left
                    truncated_section = self._truncate_document_section(
                        i, document, metadata, remaining_space, include_metadata
                    )
                    if truncated_section:
                        context_parts.append(truncated_section)
                        sources_info.append(source_info)
                break
            
            context_parts.append(doc_section)
            sources_info.append(source_info)
            current_length += len(doc_section)
        
        context = "".join(context_parts)
        self.logger.info(f"Built context: {len(context)} chars from {len(sources_info)} sources")
        
        return context, sources_info
    
    def _prepare_source_info(self, index: int, result: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare standardized source information"""
        return {
            'id': index,
            'filename': metadata.get('filename', 'Unknown'),
            'source_path': metadata.get('source', 'Unknown'),
            'relevance': result['relevance_score'],
            'search_type': result['search_type'],
            'doc_type': metadata.get('doc_type', 'general'),
            'snippet': result['document'][:200] + "..." if len(result['document']) > 200 else result['document'],
            'chunk_info': {
                'index': metadata.get('chunk_index', 0),
                'total': metadata.get('total_chunks', 1)
            } if 'chunk_index' in metadata else None
        }
    
    def _build_document_section(
        self, 
        index: int, 
        document: str, 
        metadata: Dict[str, Any], 
        include_metadata: bool
    ) -> str:
        """Build formatted document section with optional metadata"""
        
        # Basic source header
        filename = metadata.get('filename', 'Unknown')
        header = f"[Источник {index}: {filename}]"
        
        # Add metadata if requested
        if include_metadata:
            meta_parts = []
            
            # Document type
            if 'doc_type' in metadata:
                meta_parts.append(f"Тип: {metadata['doc_type']}")
            
            # Chunk information
            if 'chunk_index' in metadata and 'total_chunks' in metadata:
                meta_parts.append(f"Фрагмент {metadata['chunk_index']+1}/{metadata['total_chunks']}")
            
            # Relevance score
            meta_parts.append(f"Релевантность: {metadata.get('relevance', 'N/A')}")
            
            if meta_parts:
                header += f" ({', '.join(meta_parts)})"
        
        return f"{header}\n{document}\n\n"
    
    def _truncate_document_section(
        self,
        index: int,
        document: str,
        metadata: Dict[str, Any],
        available_space: int,
        include_metadata: bool
    ) -> Optional[str]:
        """Create truncated version of document section"""
        
        # Calculate header space
        filename = metadata.get('filename', 'Unknown')
        base_header = f"[Источник {index}: {filename}]"
        truncation_notice = "\n[...документ обрезан...]\n\n"
        
        header_space = len(base_header) + len(truncation_notice)
        if include_metadata:
            header_space += 50  # Approximate space for metadata
        
        # Calculate available space for document content
        content_space = available_space - header_space
        if content_space < 100:  # Not enough space for meaningful content
            return None
        
        # Truncate document intelligently (try to break at sentence)
        truncated_doc = document[:content_space]
        
        # Try to find last sentence boundary
        last_sentence = max(
            truncated_doc.rfind('.'),
            truncated_doc.rfind('!'),
            truncated_doc.rfind('?')
        )
        
        if last_sentence > content_space // 2:  # Only use sentence boundary if it's not too early
            truncated_doc = truncated_doc[:last_sentence + 1]
        
        # Build truncated section
        if include_metadata:
            meta_info = f" (Фрагмент, обрезан)"
            header = f"{base_header}{meta_info}"
        else:
            header = base_header
        
        return f"{header}\n{truncated_doc}{truncation_notice}"
    
    def merge_contexts(self, contexts: List[str], separator: str = "\n---\n") -> str:
        """Merge multiple contexts with separator"""
        non_empty = [ctx for ctx in contexts if ctx.strip()]
        merged = separator.join(non_empty)
        
        if len(merged) > self.max_context_length:
            # Truncate merged context
            truncated = merged[:self.max_context_length - 50]
            truncated += "\n[...контекст обрезан...]"
            return truncated
        
        return merged
    
    def analyze_context_quality(self, context: str, sources_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the quality and characteristics of built context"""
        
        analysis = {
            'length': len(context),
            'utilization': len(context) / self.max_context_length,
            'source_count': len(sources_info),
            'avg_relevance': 0.0,
            'source_diversity': {},
            'quality_score': 0.0
        }
        
        if sources_info:
            # Calculate average relevance
            relevance_scores = [src['relevance'] for src in sources_info]
            analysis['avg_relevance'] = sum(relevance_scores) / len(relevance_scores)
            
            # Analyze source diversity
            doc_types = [src.get('doc_type', 'unknown') for src in sources_info]
            analysis['source_diversity'] = {doc_type: doc_types.count(doc_type) for doc_type in set(doc_types)}
            
            # Calculate quality score (0-1)
            quality_factors = [
                min(1.0, analysis['avg_relevance'] * 1.2),  # Relevance factor
                min(1.0, len(sources_info) / 3),  # Source count factor (optimal ~3)
                min(1.0, analysis['utilization'] * 1.5),  # Utilization factor
                min(1.0, len(analysis['source_diversity']) / 2)  # Diversity factor
            ]
            analysis['quality_score'] = sum(quality_factors) / len(quality_factors)
        
        self.logger.debug(f"Context quality analysis: score={analysis['quality_score']:.2f}")
        
        return analysis