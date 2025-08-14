import os
import logging
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from .base_chroma_db import BaseChromaDB

class DocumentIngestion:
    """
    Handles ingestion of .txt files into ChromaDB vector database.
    
    Features:
    - Automatic text chunking for better retrieval
    - Metadata extraction from file paths
    - Duplicate detection using content hashes
    - Cybersecurity-focused document processing
    """
    
    def __init__(self, vector_db: BaseChromaDB, chunk_size: int = 1000, 
                 overlap: int = 200):
        self.vector_db = vector_db
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.logger = logging.getLogger(__name__)
    
    def chunk_text(self, text: str, preserve_sentences: bool = True) -> List[str]:
        """
        Split text into overlapping chunks for better retrieval.
        
        Args:
            text: Input text to chunk
            preserve_sentences: Try to split on sentence boundaries
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Define chunk end position
            end = start + self.chunk_size
            
            if end >= len(text):
                # Last chunk
                chunks.append(text[start:])
                break
            
            # Try to find sentence boundary if requested
            if preserve_sentences and end < len(text):
                # Look for sentence endings within overlap distance
                search_start = max(end - self.overlap, start + self.chunk_size // 2)
                sentence_end = -1
                
                for i in range(end, search_start - 1, -1):
                    if text[i] in '.!?':
                        # Check if this is likely end of sentence (not abbreviation)
                        if i + 1 < len(text) and text[i + 1].isspace():
                            sentence_end = i + 1
                            break
                
                if sentence_end != -1:
                    end = sentence_end
            
            chunks.append(text[start:end].strip())
            start = end - self.overlap
        
        return chunks
    
    def extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from file path and content."""
        stat = file_path.stat()
        
        metadata = {
            'source': str(file_path),
            'filename': file_path.name,
            'file_size': stat.st_size,
            'created_time': str(stat.st_ctime),
            'modified_time': str(stat.st_mtime),
            'file_extension': file_path.suffix,
        }
        
        # Extract category from directory structure (good for cybersec docs)
        parts = file_path.parts
        if len(parts) > 1:
            metadata['category'] = parts[-2]  # Parent directory as category
        
        # Detect document type based on filename patterns
        filename_lower = file_path.name.lower()
        if any(keyword in filename_lower for keyword in ['cve', 'vulnerability', 'exploit']):
            metadata['doc_type'] = 'vulnerability'
        elif any(keyword in filename_lower for keyword in ['malware', 'virus', 'trojan']):
            metadata['doc_type'] = 'malware'
        elif any(keyword in filename_lower for keyword in ['firewall', 'security', 'policy']):
            metadata['doc_type'] = 'security_policy'
        else:
            metadata['doc_type'] = 'general'
        
        return metadata
    
    def compute_content_hash(self, content: str) -> str:
        """Compute hash of content to detect duplicates."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def process_txt_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Process a single .txt file into document chunks with metadata.
        
        Returns:
            List of dictionaries with 'content' and 'metadata' keys
        """
        try:
            # Read file with proper encoding
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Fallback to other encodings
                with open(file_path, 'r', encoding='cp1251') as f:
                    content = f.read()
            
            if not content.strip():
                self.logger.warning(f"Empty file: {file_path}")
                return []
            
            # Extract base metadata
            base_metadata = self.extract_file_metadata(file_path)
            base_metadata['content_hash'] = self.compute_content_hash(content)
            
            # Chunk the content
            chunks = self.chunk_text(content)
            
            # Prepare document chunks with metadata
            documents = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = base_metadata.copy()
                chunk_metadata.update({
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'chunk_length': len(chunk),
                    'is_first_chunk': i == 0,
                    'is_last_chunk': i == len(chunks) - 1
                })
                
                documents.append({
                    'content': chunk,
                    'metadata': chunk_metadata
                })
            
            self.logger.info(f"Processed {file_path}: {len(chunks)} chunks")
            return documents
            
        except Exception as e:
            self.logger.error(f"Failed to process {file_path}: {e}")
            return []
    
    def ingest_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Ingest all .txt files from a directory into ChromaDB.
        
        Args:
            directory_path: Path to directory containing .txt files
            recursive: Whether to search subdirectories
            
        Returns:
            Summary statistics of ingestion process
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")
        
        # Find all .txt files
        if recursive:
            txt_files = list(directory.rglob("*.txt"))
        else:
            txt_files = list(directory.glob("*.txt"))
        
        if not txt_files:
            self.logger.warning(f"No .txt files found in {directory_path}")
            return {"processed_files": 0, "total_chunks": 0, "errors": 0}
        
        self.logger.info(f"Found {len(txt_files)} .txt files to process")
        
        # Process all files
        all_documents = []
        processed_files = 0
        errors = 0
        
        for file_path in txt_files:
            documents = self.process_txt_file(file_path)
            if documents:
                all_documents.extend(documents)
                processed_files += 1
            else:
                errors += 1
        
        # Add to vector database
        if all_documents:
            texts = [doc['content'] for doc in all_documents]
            metadata = [doc['metadata'] for doc in all_documents]
            
            self.vector_db.add_documents(texts, metadata)
            
            self.logger.info(f"Successfully ingested {len(all_documents)} chunks from {processed_files} files")
        
        return {
            "processed_files": processed_files,
            "total_chunks": len(all_documents),
            "errors": errors,
            "collection_info": self.vector_db.get_collection_info()
        }
    
    def ingest_single_file(self, file_path: str) -> Dict[str, Any]:
        """Ingest a single .txt file into ChromaDB."""
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise ValueError(f"File does not exist: {file_path}")
        
        if file_path_obj.suffix.lower() != '.txt':
            raise ValueError(f"Only .txt files are supported, got: {file_path_obj.suffix}")
        
        documents = self.process_txt_file(file_path_obj)
        
        if documents:
            texts = [doc['content'] for doc in documents]
            metadata = [doc['metadata'] for doc in documents]
            
            self.vector_db.add_documents(texts, metadata)
            
            self.logger.info(f"Successfully ingested {len(documents)} chunks from {file_path}")
        
        return {
            "processed_files": 1 if documents else 0,
            "total_chunks": len(documents),
            "errors": 0 if documents else 1
        }