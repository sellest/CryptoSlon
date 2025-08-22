#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test RAG pipeline with realistic queries based on actual data
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from VectorDB.base_chroma_db import BaseChromaDB
from rag.pipeline import RAGPipeline

def inspect_collection_content():
    """Look at what's actually in the test_knowledge collection"""
    print("🔍 INSPECTING COLLECTION CONTENT")
    print("=" * 50)
    
    try:
        # Use the same model that was used to create the collection
        db = BaseChromaDB("test_knowledge", model_name="intfloat/multilingual-e5-base", persist_directory="./chroma_db")
        
        # Get all documents
        all_data = db.collection.get()
        
        print(f"📊 Collection stats:")
        print(f"   Total documents: {len(all_data['ids'])}")
        print(f"   Sample document IDs: {all_data['ids'][:3] if all_data['ids'] else 'None'}")
        
        if all_data['documents']:
            print(f"\n📝 Sample document content:")
            for i, doc in enumerate(all_data['documents'][:3], 1):
                print(f"\n{i}. Document excerpt:")
                print(f"   {doc[:200]}...")
                if 'metadatas' in all_data and all_data['metadatas'] and i-1 < len(all_data['metadatas']):
                    metadata = all_data['metadatas'][i-1]
                    print(f"   Metadata: {metadata}")
        
        return all_data['documents'][:3] if all_data['documents'] else []
        
    except Exception as e:
        print(f"❌ Failed to inspect collection: {e}")
        return []

def test_rag_with_relevant_queries(sample_docs):
    """Test RAG pipeline with queries relevant to the actual content"""
    print(f"\n\n🧪 TESTING RAG WITH RELEVANT QUERIES")  
    print("=" * 50)
    
    # Create test queries based on document content
    test_queries = []
    
    if sample_docs:
        # Generate queries based on sample content
        for doc in sample_docs:
            # Extract some keywords from the document
            words = doc.lower().split()[:10]  # First 10 words
            if len(words) >= 3:
                query = ' '.join(words[:3])  # Use first 3 words as a query
                test_queries.append(f"{query}")
    
    # Add some generic queries
    test_queries.extend([
        "информация",
        "данные", 
        "текст",
        "содержимое",
        "документ"
    ])
    
    # Remove duplicates and limit to 3 queries
    test_queries = list(set(test_queries))[:3]
    
    try:
        rag = RAGPipeline(
            vector_db_collection="test_knowledge",
            vector_model="intfloat/multilingual-e5-base",  # Use correct model
            chroma_db_path="../chroma_db",
            min_relevance_score=0.5,  # Lower threshold for better matching
            enable_debug=True
        )
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            print("-" * 30)
            
            result = rag.run(query)
            
            print(f"Success: {result.success}")
            print(f"Sources found: {len(result.sources)}")
            print(f"Answer length: {len(result.answer)}")
            
            if result.sources:
                print(f"Source details:")
                for i, source in enumerate(result.sources, 1):
                    print(f"  {i}. {source.get('filename', 'Unknown')} (relevance: {source.get('relevance', 'N/A'):.3f})")
                    print(f"     Snippet: {source.get('snippet', 'N/A')[:100]}...")
            
            if result.debug_info and 'search_results' in result.debug_info:
                search_results = result.debug_info['search_results']
                print(f"Search debug info: {len(search_results)} results")
            
            print(f"Answer: {result.answer[:200]}{'...' if len(result.answer) > 200 else ''}")
            
            if result.success:
                print(f"✅ Query successful!")
                break
            else:
                print(f"❌ Query failed")
            
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        import traceback
        traceback.print_exc()

def test_simple_search():
    """Test simple vector database search without RAG pipeline"""
    print(f"\n\n🔍 TESTING SIMPLE VECTOR SEARCH")
    print("=" * 50)
    
    try:
        # Use the same model that was used to create the collection
        db = BaseChromaDB("test_knowledge", model_name="intfloat/multilingual-e5-base", persist_directory="./chroma_db")
        
        simple_queries = ["Олег", "Илья", "Мария", "Татьяна", "Артур"]
        
        for query in simple_queries:
            print(f"\n🔍 Searching for: '{query}'")
            results = db.search(query, top_k=3)
            
            if results:
                print(f"   Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    distance = result['distance']
                    relevance = 1 - distance
                    print(f"   {i}. Distance: {distance:.3f}, Relevance: {relevance:.3f}")
                    print(f"      Content: {result['document'][:100]}...")
            else:
                print(f"   No results found")
                
    except Exception as e:
        print(f"❌ Simple search failed: {e}")

def main():
    print(f"🏠 Current directory: {os.getcwd()}")
    
    # Step 1: Inspect what's in the collection
    # sample_docs = inspect_collection_content()
    
    # Step 2: Test simple vector search
    test_simple_search()
    
    # Step 3: Test RAG pipeline with relevant queries
    # test_rag_with_relevant_queries(sample_docs)


if __name__ == "__main__":
    main()
