# -*- coding: utf-8 -*-
# vectorize_documents.py - Simple document vectorization tool

from pathlib import Path
from typing import List
from VectorDB.base_chroma_db import BaseChromaDB
from VectorDB.document_ingestion import DocumentIngestion

class SimpleVectorizer:
    """Simple vectorizer that processes .txt and .pdf files and reports metrics"""
    
    def __init__(self, collection_name: str, model_name: str = "intfloat/multilingual-e5-base",
                 chroma_db_path: str = "../chroma_db"):
        self.db = BaseChromaDB(collection_name, model_name, chroma_db_path)
        self.ingestion = DocumentIngestion(self.db, chunk_size=1000, overlap=200)
        
    def vectorize_files(self, file_paths: List[str]) -> dict:
        """Vectorize list of .txt and .pdf files and return metrics"""
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
    
    def vectorize_directory(self, directory_path: str, recursive: bool = True) -> dict:
        """Process all supported files from a directory"""
        print(f"Processing directory: {directory_path} (recursive: {recursive})")
        
        try:
            result = self.ingestion.ingest_directory(directory_path, recursive)
            metrics = {
                "files_scanned": result["processed_files"] + result["errors"],
                "files_processed": result["processed_files"],
                "total_chunks": result["total_chunks"],
                "errors": result["errors"],
                "success": result["errors"] == 0
            }
            return metrics
        except Exception as e:
            print(f"Failed to process directory: {e}")
            return {"success": False, "error": str(e)}


# Example usage
if __name__ == "__main__":
    # Example 1: Create new collection for PDF documents
    pdf_vectorizer = SimpleVectorizer(
        collection_name="cybersecurity_pdfs",
        chroma_db_path="../chroma_db"
    )
    
    # Process PDF files
    pdf_files = [
        "/Users/izelikson/python/CryptoSlon/VectorDB/data/test_data.pdf",
    ]
    
    print("Processing PDF documents...")
    pdf_metrics = pdf_vectorizer.vectorize_files(pdf_files)
    pdf_vectorizer.print_report(pdf_metrics)

    # # Example 3: Process entire directory
    # directory_vectorizer = SimpleVectorizer(
    #     collection_name="documents_from_dir",
    #     chroma_db_path="./custom_chroma_path"
    # )
    #
    # print("\nProcessing entire directory...")
    # dir_metrics = directory_vectorizer.vectorize_directory("VectorDB/data/", recursive=True)
    # directory_vectorizer.print_report(dir_metrics)
