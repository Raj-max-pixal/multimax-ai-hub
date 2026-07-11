from typing import List
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "multimax_documents"

class EmbeddingService:
    _client = None
    _collection = None
    _model = None
    
    @classmethod
    def initialize(cls):
        if cls._client is None:
            cls._client = chromadb.PersistentClient(path=CHROMA_DIR)
            sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            cls._collection = cls._client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=sentence_transformer_ef
            )
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
    
    @classmethod
    def add_chunks(cls, document_id: str, chunks: List[dict]):
        cls.initialize()
        ids = [chunk["chunk_id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": chunk["index"]
            }
            for chunk in chunks
        ]
        cls._collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
    
    @classmethod
    def search(cls, query: str, document_ids: List[str] = None, n_results: int = 5):
        cls.initialize()
        where = None
        if document_ids:
            where = {"document_id": {"$in": document_ids}}
        
        results = cls._collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        return results
    
    @classmethod
    def delete_document_chunks(cls, document_id: str):
        cls.initialize()
        where = {"document_id": document_id}
        cls._collection.delete(where=where)
