from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseVectorDB(ABC):
    """
    Abstract base class for vector database implementations in RAG systems.

    This class defines the interface for storing, retrieving, and managing
    document embeddings and their associated metadata. Implementations should
    handle the conversion of text to vectors internally.
    """

    @abstractmethod
    def add_documents(self, documents: List[str], metadata: List[Dict] = None) -> None:
        """
        Add documents to the vector database.

        This method should:
        1. Convert documents to embeddings using the configured model
        2. Store embeddings along with original text and metadata
        3. Generate unique IDs for each document if not provided

        Args:
            documents: List of text documents to add to the database
            metadata: Optional list of metadata dictionaries for each document.
                     Should be same length as documents list. Common metadata
                     includes: source, timestamp, document_type, etc.

        Raises:
            ValueError: If documents and metadata lists have different lengths
        """
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for most semantically similar documents to the query.

        This method should:
        1. Convert query text to embedding using the same model as documents
        2. Perform similarity search (cosine similarity, dot product, etc.)
        3. Return top-k most similar documents with their metadata and scores

        Args:
            query: Text query to search for
            top_k: Maximum number of results to return

        Returns:
            List of dictionaries containing:
            - 'document': Original document text
            - 'metadata': Associated metadata dictionary
            - 'distance' or 'score': Similarity score/distance from query

        Example return:
            [
                {
                    'document': 'Bitcoin is a cryptocurrency...',
                    'metadata': {'source': 'crypto_wiki.pdf', 'page': 1},
                    'distance': 0.23
                },
                ...
            ]
        """
        pass

    @abstractmethod
    def delete_documents(self, ids: List[str]) -> None:
        """
        Remove documents from the vector database by their IDs.

        Args:
            ids: List of document IDs to remove from the database

        Raises:
            ValueError: If any of the provided IDs don't exist
        """
        pass

    @abstractmethod
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get metadata and statistics about the current collection/database.

        Returns:
            Dictionary containing collection information such as:
            - 'total_documents': Number of documents stored
            - 'embedding_dimension': Size of embedding vectors
            - 'model_name': Name of the embedding model used
            - 'collection_name': Name/identifier of the collection

        Example return:
            {
                'total_documents': 1500,
                'embedding_dimension': 384,
                'model_name': 'all-MiniLM-L6-v2',
                'collection_name': 'crypto_knowledge'
            }
        """
        pass
    