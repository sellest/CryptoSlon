from typing import List, Dict, Any
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.retrievers import EnsembleRetriever

class HybridRetrieval:
    def __init__(self, faiss_path: str, docs_store: Any, embed_model="sentence-transformers/all-MiniLM-L6-v2"):
        # docs_store: где лежат исходные тексты для BM25 (список Document)
        self.bm25 = BM25Retriever.from_documents(docs_store)    # в памяти
        self.vs = FAISS.load_local(faiss_path, HuggingFaceEmbeddings(model_name=embed_model), allow_dangerous_deserialization=True)
        self.vec = self.vs.as_retriever(search_type="mmr", search_kwargs={"k": 20, "fetch_k": 40, "lambda_mult": 0.6})
        self.hybrid = EnsembleRetriever(retrievers=[self.bm25, self.vec], weights=[0.5, 0.5])

    def run(self, query: str, k: int = 20) -> List[Document]:
        docs = self.hybrid.get_relevant_documents(query)
        return docs[:k]
