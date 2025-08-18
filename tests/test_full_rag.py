# -*- coding: utf-8 -*-
# test_full_rag.py - Test complete RAG pipeline

import logging
from LLMs.factory import get_llm_client
from VectorDB.base_chroma_db import BaseChromaDB
from rag.queryprep import QueryPreprocessor

logging.basicConfig(level=logging.WARNING)

def test_full_rag_pipeline():
    """Test complete RAG pipeline: query → queryprep → vectorDB → LLM"""
    
    print("=== FULL RAG PIPELINE TEST ===")
    
    # Initialize components
    print("\n1. Initializing components...")
    llm = get_llm_client("gigachat")
    vector_db = BaseChromaDB("test_knowledge", "intfloat/multilingual-e5-base")
    query_prep = QueryPreprocessor()
    
    # User query
    user_query = "Расскажи про Олега Андреевича"
    use_rag = True  # Boolean flag - your decision point
    
    print(f"\n2. User Query: '{user_query}'")
    print(f"   Use RAG: {use_rag}")
    
    if use_rag:
        print(f"\n3. Running query through RAG pipeline...")
        
        # Step 1: Query preprocessing
        print(f"   → QueryPrep processing...")
        prep_result = query_prep.run(user_query)
        search_query = prep_result.rewritten or user_query
        print(f"   → Enhanced query: '{search_query}'")
        print(f"   → Detected language: {prep_result.language}")
        print(f"   → Found entities: {prep_result.entities}")
        
        # Step 2: Vector search
        print(f"\n   → Searching vectorDB...")
        search_results = vector_db.search(search_query, top_k=3)
        
        if search_results:
            print(f"   → Found {len(search_results)} relevant documents")
            
            # Build context from search results
            context_parts = []
            for i, result in enumerate(search_results):
                distance = result['distance']
                content = result['document']
                filename = result['metadata'].get('filename', 'Unknown')
                
                print(f"     {i+1}. {filename} (distance: {distance:.3f})")
                print(f"        {content[:100]}...")
                
                if distance < 0.8:  # Only use relevant results
                    context_parts.append(f"[Источник: {filename}] {content}")
            
            if context_parts:
                # Step 3: LLM with context
                context = "\n\n".join(context_parts)
                system_prompt = f"""Ты помощник, отвечающий на вопросы пользователя на основе предоставленного контекста.

Контекст:
{context}

Отвечай на основе этого контекста. Если информации недостаточно, скажи об этом."""

                print(f"\n   → Calling LLM with context...")
                print(f"   → Context length: {len(context)} chars")
                
                response = llm.chat_one(user_query, system_prompt)
                
                print(f"\n4. RAG RESPONSE:")
                print(f"   {response}")
                
            else:
                print(f"\n   → No relevant documents found (all distances > 0.8)")
                print(f"   → Falling back to LLM without context...")
                
                response = llm.chat_one(user_query)
                print(f"\n4. FALLBACK RESPONSE:")
                print(f"   {response}")
        
        else:
            print(f"   → No documents found in vectorDB")
            print(f"   → Using LLM without context...")
            
            response = llm.chat_one(user_query)
            print(f"\n4. NO-CONTEXT RESPONSE:")
            print(f"   {response}")
    
    else:
        print(f"\n3. RAG disabled, using LLM directly...")
        response = llm.chat_one(user_query)
        print(f"\n4. DIRECT LLM RESPONSE:")
        print(f"   {response}")

def test_comparison(test_query: str, llm: str = "gigachat"):
    """Test same query with and without RAG for comparison"""
    
    print("\n\n=== RAG vs NO-RAG COMPARISON ===")
    
    # Initialize components
    llm = get_llm_client(llm)
    vector_db = BaseChromaDB("test_knowledge", "intfloat/multilingual-e5-base")
    query_prep = QueryPreprocessor()
    
    test_query = test_query
    
    print(f"\nQuery: '{test_query}'")
    
    # Test WITHOUT RAG
    print(f"\n--- WITHOUT RAG ---")
    no_rag_response = llm.chat_one(test_query)
    print(f"Response: {no_rag_response}")
    
    # Test WITH RAG
    print(f"\n--- WITH RAG ---")
    prep_result = query_prep.run(test_query)
    search_query = prep_result.rewritten or test_query
    search_results = vector_db.search(search_query, top_k=2)
    
    if search_results and search_results[0]['distance'] < 0.8:
        context = search_results[0]['document']
        system_prompt = f"""Отвечай на основе этого контекста:

{context}

Если контекст не помогает ответить на вопрос, скажи об этом."""
        
        rag_response = llm.chat_one(test_query, system_prompt)
        # print(f"Context used: {context[:100]}...")
        print(f"Response: {rag_response}")
    else:
        print(f"No relevant context found, using direct LLM")
        rag_response = llm.chat_one(test_query)
        print(f"Response: {rag_response}")


if __name__ == "__main__":

    # test_full_rag_pipeline()

    # Сравнение ответов модели с использованием и без использования RAG
    user_input = "Что написал Артур Евгеньевич на заднем стекле машины?"
    test_comparison(user_input)
