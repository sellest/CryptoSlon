# -*- coding: utf-8 -*-
# vectorize_documents.py - Simple document vectorization tool

import logging
import hashlib
from pathlib import Path
from typing import List
from VectorDB.base_chroma_db import BaseChromaDB
from VectorDB.document_ingestion import DocumentIngestion

class SimpleVectorizer:
    """Simple vectorizer that processes .txt files and reports metrics"""
    
    def __init__(self, collection_name: str, model_name: str = "intfloat/multilingual-e5-base"):
        self.db = BaseChromaDB(collection_name, model_name)
        self.ingestion = DocumentIngestion(self.db, chunk_size=800, overlap=150)
        
    def vectorize_files(self, file_paths: List[str]) -> dict:
        """Vectorize list of .txt files and return metrics"""
        metrics = {
            "files_scanned": len(file_paths),
            "files_processed": 0,
            "total_chunks": 0,
            "errors": 0,
            "success": True
        }
        
        print(f"Processing {len(file_paths)} files...")
        
        for file_path in file_paths:
            try:
                result = self.ingestion.ingest_single_file(file_path)
                if result["processed_files"] > 0:
                    metrics["files_processed"] += 1
                    metrics["total_chunks"] += result["total_chunks"]
                    print(f"{Path(file_path).name}: {result['total_chunks']} chunks")
                else:
                    metrics["errors"] += 1
                    print(f"{Path(file_path).name}: failed")
            except Exception as e:
                metrics["errors"] += 1
                print(f"{Path(file_path).name}: {e}")
        
        if metrics["errors"] > 0:
            metrics["success"] = False
            
        return metrics
    
    def print_report(self, metrics: dict):
        """Print simple metrics report"""
        print(f"\n--- VECTORIZATION REPORT ---")
        print(f"Files scanned: {metrics['files_scanned']}")
        print(f"Files processed: {metrics['files_processed']}")
        print(f"Total chunks created: {metrics['total_chunks']}")
        print(f"Errors: {metrics['errors']}")
        print(f"Status: {'SUCCESS' if metrics['success'] else 'FAILED'}")

    def clean_and_add(self, file_paths: List[str]) -> dict:
        """Option 2: Delete collection and re-create with new data"""
        print("Using clean_and_add method...")
        print("Deleting existing collection...")
        
        try:
            # Delete the entire collection
            self.db.client.delete_collection(self.db.collection_name)
            print(f"Deleted collection: {self.db.collection_name}")
            
            # Re-create the collection
            self.db.collection = self.db.client.get_or_create_collection(self.db.collection_name)
            print(f"Re-created collection: {self.db.collection_name}")
            
            # Process files into fresh collection
            return self.vectorize_files(file_paths)
            
        except Exception as e:
            print(f"Failed to clean and add: {e}")
            return {"success": False, "error": str(e)}


# Example usage
if __name__ == "__main__":
    # Initialize vectorizer with existing collection
    vectorizer = SimpleVectorizer("test_knowledge")
    
    # List of files to process
    files_to_process = [
        "VectorDB/data/sample_data.txt"
    ]
    
    # Choose your method:
    
    # Option 1: Regular add (might create duplicates)
    # metrics = vectorizer.vectorize_files(files_to_process)
    
    # Option 2: Clean slate - delete and re-create
    metrics = vectorizer.clean_and_add(files_to_process)

    # Print report
    vectorizer.print_report(metrics)