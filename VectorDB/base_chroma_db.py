import chromadb
import uuid
import logging
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from .base_vector_db import BaseVectorDB

class BaseChromaDB(BaseVectorDB):
    def __init__(self, collection_name: str, model_name: str = 'all-MiniLM-L6-v2', 
                 persist_directory: str = "./chroma_db"):
        self.collection_name = collection_name
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        
        try:
            self.client = chromadb.PersistentClient(path=persist_directory)
            self.collection = self.client.get_or_create_collection(collection_name)
            self.model = SentenceTransformer(model_name)
            self.logger.info(f"ChromaDB initialized: collection='{collection_name}', model='{model_name}'")
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def add_documents(self, documents: List[str], metadata: List[Dict] = None) -> None:
        """Add documents to ChromaDB with unique IDs and proper error handling."""
        if not documents:
            self.logger.warning("No documents provided to add")
            return
            
        if metadata and len(documents) != len(metadata):
            raise ValueError(f"Documents ({len(documents)}) and metadata ({len(metadata)}) lists must have same length")
        
        try:
            # Generate unique IDs using UUID
            ids = [str(uuid.uuid4()) for _ in documents]
            
            # Encode documents to embeddings
            embeddings = self.model.encode(documents, normalize_embeddings=True)
            
            # Prepare metadata with document info
            enhanced_metadata = []
            for i, doc in enumerate(documents):
                meta = metadata[i] if metadata else {}
                meta.update({
                    'doc_length': len(doc),
                    'timestamp': str(uuid.uuid1().time),
                    'embedding_model': self.model_name
                })
                enhanced_metadata.append(meta)

            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=documents,
                metadatas=enhanced_metadata,
                ids=ids
            )
            
            self.logger.info(f"Added {len(documents)} documents to collection '{self.collection_name}'")
            
        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            raise

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for most similar documents to the query."""
        try:
            query_embedding = self.model.encode([query], normalize_embeddings=True)
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k
            )

            if not results['documents'] or not results['documents'][0]:
                self.logger.info(f"No results found for query: '{query[:50]}...'")
                return []

            search_results = [
                {
                    "document": doc,
                    "metadata": meta,
                    "distance": dist
                }
                for doc, meta, dist in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )
            ]
            
            self.logger.info(f"Found {len(search_results)} results for query")
            return search_results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []

    def delete_documents(self, ids: List[str]) -> None:
        """Remove documents from the vector database by their IDs."""
        if not ids:
            return
            
        try:
            self.collection.delete(ids=ids)
            self.logger.info(f"Deleted {len(ids)} documents from collection '{self.collection_name}'")
        except Exception as e:
            self.logger.error(f"Failed to delete documents: {e}")
            raise ValueError(f"Failed to delete documents: {e}")

    def get_collection_info(self) -> Dict[str, Any]:
        """Get metadata and statistics about the current collection."""
        try:
            count = self.collection.count()
            
            # Get sample embedding to determine dimension
            embedding_dim = 0
            if count > 0:
                sample_result = self.collection.peek(limit=1)
                if sample_result.get('embeddings') is not None and len(sample_result['embeddings']) > 0:
                    embedding_dim = len(sample_result['embeddings'][0])
            
            return {
                'total_documents': count,
                'embedding_dimension': embedding_dim,
                'model_name': self.model_name,
                'collection_name': self.collection_name
            }
        except Exception as e:
            self.logger.error(f"Failed to get collection info: {e}")
            # Try alternative method to get count
            try:
                # Sometimes collection.count() fails, try getting all IDs
                all_data = self.collection.get()
                actual_count = len(all_data.get('ids', []))
                embedding_dim = 0
                if all_data.get('embeddings') is not None and len(all_data['embeddings']) > 0:
                    embedding_dim = len(all_data['embeddings'][0])
                
                return {
                    'total_documents': actual_count,
                    'embedding_dimension': embedding_dim,
                    'model_name': self.model_name,
                    'collection_name': self.collection_name
                }
            except Exception as e2:
                self.logger.error(f"Alternative count method also failed: {e2}")
                return {
                    'total_documents': 0,
                    'embedding_dimension': 0,
                    'model_name': self.model_name,
                    'collection_name': self.collection_name
                }

    @classmethod
    def list_all_collections(cls, persist_directory: str = "./chroma_db") -> List[Dict[str, Any]]:
        """Static method to list all collections without creating a specific collection."""
        try:
            client = chromadb.PersistentClient(path=persist_directory)
            collections = client.list_collections()
            
            collection_info = []
            for collection in collections:
                try:
                    count = collection.count()
                    collection_info.append({
                        'name': collection.name,
                        'id': collection.id,
                        'total_documents': count
                    })
                except Exception:
                    collection_info.append({
                        'name': collection.name,
                        'id': collection.id,
                        'total_documents': 'unknown'
                    })
            
            return collection_info
            
        except Exception as e:
            logging.error(f"Failed to list all collections: {e}")
            return []
