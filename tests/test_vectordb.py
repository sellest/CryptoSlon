# -*- coding: utf-8 -*-
# test_vectordb.py - Test script for vector database and document ingestion

import logging
from VectorDB.base_chroma_db import BaseChromaDB
from VectorDB.document_ingestion import DocumentIngestion

logging.basicConfig(level=logging.INFO)

def test_chroma_db():
    """Test ChromaDB functionality"""
    print("=== Testing ChromaDB ===")
    
    # Initialize ChromaDB for cybersecurity documents
    db = BaseChromaDB(
        collection_name="cybersecurity_docs",
        model_name="intfloat/multilingual-e5-base"  # Good for Russian/English
    )
    
    # Test adding documents
    test_docs = [
        "SQL injection - это тип атаки, при которой злоумышленник вводит SQL код в поля ввода веб-приложения",
        "Malware analysis requires understanding of file signatures and behavioral patterns",
        "CVE-2023-1234 представляет собой критическую уязвимость в Apache HTTP Server"
    ]
    
    test_metadata = [
        {"category": "web_security", "language": "ru", "threat_level": "high"},
        {"category": "malware", "language": "en", "threat_level": "medium"}, 
        {"category": "vulnerabilities", "language": "ru", "threat_level": "critical"}
    ]
    
    print("Adding test documents...")
    db.add_documents(test_docs, test_metadata)
    
    # Test search functionality
    print("\nTesting search...")
    queries = [
        "SQL injection attack",
        "анализ вредоносного ПО",
        "Apache vulnerability"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        results = db.search(query, top_k=2)
        for i, result in enumerate(results, 1):
            print(f"  {i}. Distance: {result['distance']:.3f}")
            print(f"     Text: {result['document'][:100]}...")
            print(f"     Category: {result['metadata'].get('category', 'N/A')}")
    
    # Get collection info
    print("\nCollection Info:")
    info = db.get_collection_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

def test_document_ingestion():
    """Test document ingestion from files"""
    print("\n\n=== Testing Document Ingestion ===")
    
    # Initialize vector database
    db = BaseChromaDB(
        collection_name="test_knowledge",
        model_name="intfloat/multilingual-e5-base"
    )
    
    # Initialize ingestion system
    ingestion = DocumentIngestion(
        vector_db=db,
        chunk_size=200,  # Small chunks for the test file
        overlap=50
    )
    
    print("Document ingestion system ready.")
    
    # Test with the sample file
    try:
        print("\nIngesting sample_data.txt...")
        result = ingestion.ingest_single_file("VectorDB/data/sample_data.txt")
        print(f"Ingestion result: {result}")

        # Show collection info
        print(f"\nCollection Info: {db.get_collection_info()}")
    except Exception as e:
        print(f"Ingestion failed: {e}")
        import traceback
        traceback.print_exc()

def inspect_stored_data():
    """Inspect what data is actually stored in ChromaDB"""
    print("\n\n=== Inspecting Stored Data ===")
    
    # Connect to existing collection
    db = BaseChromaDB(
        collection_name="test_knowledge",
        model_name="intfloat/multilingual-e5-base"
    )
    
    # Get collection statistics
    info = db.get_collection_info()
    print("Collection Statistics:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    if info['total_documents'] > 0:
        print(f"SUCCESS: {info['total_documents']} documents stored in ChromaDB!")
        print(f"Embedding dimension: {info['embedding_dimension']}")
        print(f"Database file size: ~237KB")
        
        # Show some sample data (peek function)
        try:
            sample = db.collection.peek(limit=3)
            print(f"\nSample stored documents:")
            for i, (doc, meta) in enumerate(zip(sample['documents'], sample['metadatas'])):
                print(f"  {i+1}. File: {meta.get('filename', 'N/A')}")
                print(f"     Content: {doc[:100]}...")
                print(f"     Chunk: {meta.get('chunk_index', 0)}/{meta.get('total_chunks', 1)}")
        except Exception as e:
            print(f"Could not peek data: {e}")
    
    else:
        print("No documents found in ChromaDB")
    
    # Test search to verify embeddings work
    print(f"\nTesting search functionality:")
    search_results = db.search("Олег Андреевич", top_k=1)
    if search_results:
        result = search_results[0]
        print(f"Search works! Found: {result['document'][:100]}...")
        print(f"Distance: {result['distance']:.3f}")
    else:
        print("Search returned no results")


if __name__ == "__main__":
    # Comment out the basic test to focus on document ingestion
    # test_chroma_db()
    
    # Test document ingestion with your sample file
    # test_document_ingestion()  # Run this first if you haven't ingested yet
    
    # Inspect what's already stored
    inspect_stored_data()
